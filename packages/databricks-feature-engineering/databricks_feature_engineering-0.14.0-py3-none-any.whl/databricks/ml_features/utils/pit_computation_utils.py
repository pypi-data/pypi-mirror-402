"""
Point-in-Time Feature Computation Utilities
===========================================

This module provides utilities for computing time-windowed features with point-in-time correctness.
It's designed for use with declarative Feature objects that define computations over DataSource objects.

The implementation handles:
- Multiple data sources with different schemas
- Multiple time windows per source (including offset windows)
- Microsecond-precision timestamp handling
- All aggregation function types with correct null handling
- Efficient batching and optimization strategies
"""

import random
import string
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Optional, cast

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from databricks.ml_features.constants import (
    _FEATURE_ENGINEERING_COMPUTATION_PRECISION,
    _PIT_MAX_SLIDING_WINDOW_BOUNDARY_COUNT,
    _PRECISION_FACTOR,
)
from databricks.ml_features.entities.data_source import DataSource
from databricks.ml_features.entities.feature import Feature
from databricks.ml_features.entities.time_window import (
    ContinuousWindow,
    SlidingWindow,
    TimeWindow,
    TumblingWindow,
)
from databricks.ml_features.environment_variables import BROADCAST_JOIN_THRESHOLD


@dataclass(frozen=True)
class FilteredDataSource:
    """
    Represents a data source with an optional filter condition.

    Used as a grouping key to ensure features from the same source with
    different filters are computed separately.
    """

    source: DataSource
    filter_condition: Optional[str] = None

    def generate_alias(self) -> str:
        """Generate unique alias for this filtered source."""
        source_id = abs(hash(str(self.source)))

        if self.filter_condition:
            filter_id = abs(hash(self.filter_condition))
            return f"source_{source_id}_filter_{filter_id}"
        else:
            return f"source_{source_id}"


@dataclass(frozen=True)
class SlidingWindowBoundaries:
    """
    Boundaries for epoch-aligned sliding windows.

    All timestamps are microseconds since the Unix epoch.
    """

    start_boundary_us: Optional[int]  # earliest window *end* boundary
    end_boundary_us: Optional[int]  # latest window *end* boundary
    num_boundaries: int  # total count of boundary instants (inclusive)
    timestamp_col: str  # name of the timestamp column (for error messages)
    time_window: SlidingWindow  # sliding window configuration (for validation error messages)
    precision_factor: int  # microsecond precision factor (for time range calculation)

    def __post_init__(self) -> None:
        """Validate boundary data after initialization."""
        # Check for NULL timestamps
        if self.start_boundary_us is None or self.end_boundary_us is None:
            raise ValueError(
                f"Training DataFrame contains NULL values in timestamp column '{self.timestamp_col}'. "
                "Point-in-time feature computation requires all timestamps to be non-NULL."
            )

        # Validate boundary count doesn't exceed limits
        if self.num_boundaries > _PIT_MAX_SLIDING_WINDOW_BOUNDARY_COUNT:
            # Calculate time range for error message
            time_range_days = (self.end_boundary_us - self.start_boundary_us) / (
                24 * 60 * 60 * self.precision_factor
            )
            raise ValueError(
                f"Sliding window would generate {self.num_boundaries} boundaries, which exceeds the "
                f"maximum limit of {_PIT_MAX_SLIDING_WINDOW_BOUNDARY_COUNT:,}. This typically indicates:\n"
                f"  - Training data spans a very large time range ({time_range_days:.1f} days)\n"
                f"  - Slide duration is very small ({self.time_window.slide_duration})\n"
                f"Consider:\n"
                f"  - Using a larger slide_duration\n"
                f"  - Filtering training data to a smaller time range\n"
                f"  - Using TumblingWindow instead of SlidingWindow for this use case"
            )


def _create_unique_string(prefix: str) -> str:
    """
    Create a unique string with a prefix and random alphanumeric suffix.

    Args:
        prefix: The prefix string to prepend to the unique identifier

    Returns:
        String in format: "{prefix}_{random_10_char_alphanumeric}"
    """
    # Generate 10 random alphanumeric characters
    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"{prefix}_{random_suffix}"


def _get_default_value_for_function(function_name: str) -> F.Column:
    """
    Get the appropriate default value when no records exist in time window.

    Different aggregation functions have different semantics for empty windows:
    - Count functions (count, approx_count_distinct) return 0
    - All other functions (sum, avg, min, max, etc.) return null

    Args:
        function_name: Name of the aggregation function (e.g., "count", "sum", "avg")

    Returns:
        PySpark literal column with appropriate default value
    """
    COUNT_FUNCTIONS = {"count", "approx_count_distinct"}

    if function_name.lower() in COUNT_FUNCTIONS:
        return F.lit(0)
    else:
        return F.lit(None)


def _create_microsecond_precision_time_condition(
    source_ts_col: str,
    train_ts_col: str,
    duration: timedelta,
    offset: timedelta = timedelta(0),
) -> F.Column:
    """
    Create time window condition with microsecond precision.

    This function creates a condition that determines whether a source timestamp
    falls within the specified time window relative to a training timestamp.
    It maintains microsecond precision using the same approach as the existing
    compute_features() implementation.

    Args:
        source_ts_col: Source timestamp column name
        train_ts_col: Training timestamp column name
        duration: Window duration (how far back to look from train_ts)
        offset: Window offset (shift backward from train_ts), defaults to 0

    Returns:
        PySpark condition column for time window membership with microsecond precision

    Example:
        # Standard 7-day window: source_ts in [train_ts - 7 days, train_ts)
        condition = _create_microsecond_precision_time_condition(
            "source_ts", "train_ts", timedelta(days=7)
        )

        # Offset window: source_ts in [train_ts - 7 days - 1 day, train_ts - 1 day)
        condition = _create_microsecond_precision_time_condition(
            "source_ts", "train_ts", timedelta(days=7), timedelta(days=-1)
        )
    """
    # Calculate precision factor for microsecond handling
    # This matches the precision used in existing compute_features() implementation
    precision_factor = (
        int(1 / _FEATURE_ENGINEERING_COMPUTATION_PRECISION)
        if _FEATURE_ENGINEERING_COMPUTATION_PRECISION != 0
        else 1
    )

    # Convert timedeltas to microseconds for precise arithmetic
    duration_microseconds = int(duration.total_seconds() * precision_factor)
    offset_microseconds = int(offset.total_seconds() * precision_factor)

    # Convert timestamps to microseconds since epoch using Spark's native function
    source_ts_long = F.unix_micros(F.col(source_ts_col))
    train_ts_long = F.unix_micros(F.col(train_ts_col))

    # Create time window bounds in microsecond precision
    # Window is [train_ts - duration + offset, train_ts + offset)
    window_start = (
        train_ts_long - F.lit(duration_microseconds) + F.lit(offset_microseconds)
    )
    window_end = train_ts_long + F.lit(offset_microseconds)

    return (source_ts_long >= window_start) & (source_ts_long < window_end)


def _group_features_by_source_filter_and_window(
    features: List[Feature],
) -> Dict[FilteredDataSource, Dict[TimeWindow, List[Feature]]]:
    """
    Group features by data source, filter condition, and time window for efficient batch processing.

    This optimization reduces redundant computations by:
    1. Processing each data source with same filter only once
    2. Minimizing the number of window specifications created

    Args:
        features: List of Feature objects to group

    Returns:
        Nested dictionary mapping:
        {FilteredDataSource: {time_window: [features_with_same_window]}}

    Example:
        Input features:
        - f1 = Feature(source=bookings, filter_condition="status='active'", time_window=TimeWindow(days=7))
        - f2 = Feature(source=bookings, filter_condition="status='active'", time_window=TimeWindow(days=7))
        - f3 = Feature(source=bookings, filter_condition="status='active'", time_window=TimeWindow(days=3))
        - f4 = Feature(source=bookings, filter_condition="status='pending'", time_window=TimeWindow(days=7))
        - f5 = Feature(source=transactions, filter_condition=None, time_window=TimeWindow(days=7))

        Output (grouped by source+filter first, then by time_window):
        {
            FilteredDataSource(bookings, "status='active'"): {
                TimeWindow(days=7): [f1, f2],
                TimeWindow(days=3): [f3]
            },
            FilteredDataSource(bookings, "status='pending'"): {
                TimeWindow(days=7): [f4]
            },
            FilteredDataSource(transactions, None): {
                TimeWindow(days=7): [f5]
            }
        }
    """
    grouped = defaultdict(lambda: defaultdict(list))

    for feature in features:
        key = FilteredDataSource(feature.source, feature.filter_condition)
        grouped[key][feature.time_window].append(feature)

    return grouped


def _extract_train_timestamp_column(train_df: DataFrame, source: DataSource) -> str:
    """
    Extract the training timestamp column name from the training DataFrame.

    The training DataFrame should contain a timestamp column that corresponds to
    the source's timeseries_column. This function identifies that column.

    Args:
        train_df: Training DataFrame
        source: DataSource object with timeseries_column property

    Returns:
        Name of the timestamp column in train_df

    Raises:
        ValueError: If the expected timestamp column is not found
    """
    # The training DataFrame should have the same timeseries column as the source
    expected_ts_col = source.timeseries_column

    if expected_ts_col not in train_df.columns:
        raise ValueError(
            f"Expected timestamp column '{expected_ts_col}' not found in training DataFrame. "
            f"Available columns: {train_df.columns}"
        )

    return expected_ts_col


# ==============================================================================
# Why we don't use Spark's F.window() for time bucketing
# ==============================================================================
#
# Spark provides F.window() to bucket timestamps into fixed-duration windows.
# However, we use manual epoch-aligned bucketing instead for these reasons:
#
# 1. Sliding/Continuous Windows:
#    - Events must belong to MULTIPLE overlapping windows based on training timestamps
#    - F.window() assigns each event to exactly ONE bucket, making it unsuitable
#    - We need cross-join logic to assign source events to all relevant windows
#
# 2. Tumbling Windows:
#    - While F.window() could work for source bucketing, training rows need
#      "most recent complete window" logic: window.start - duration
#    - This requires the same floor arithmetic we already use
#    - F.window() would require timedelta→string conversion ("7 days", "604800 seconds")
#    - No performance or simplicity benefit over direct epoch-aligned bucketing
#
# 3. Consistency & Precision:
#    - Using unix_micros() + floor division maintains uniform microsecond precision
#    - Same bucketing approach across all window types makes the code more maintainable
#
# Our approach: floor(timestamp_micros / duration_micros) * duration_micros
# ==============================================================================


def _duration_to_micros(duration: timedelta) -> int:
    return int(duration.total_seconds() * _PRECISION_FACTOR)


def _tumbling_window_bucket_id(timestamp: F.Column, window_size: timedelta) -> F.Column:
    """
    Calculate the bucket ID (window index) for a tumbling window from epoch.

    Tumbling windows are non-overlapping time intervals aligned to epoch.
    Each window is assigned a sequential bucket ID based on its position from epoch.
    For example, with 1-day windows:
        - Jan 1, 2024 00:00 -> bucket 19723
        - Jan 1, 2024 12:00 -> bucket 19723 (same window)
        - Jan 2, 2024 00:00 -> bucket 19724

    Args:
        timestamp: Timestamp column
        window_size: Tumbling window size (e.g., timedelta(days=1))

    Returns:
        Column containing bucket ID (integer window index from epoch)
    """
    window_size_us = _duration_to_micros(window_size)
    return F.floor(F.unix_micros(timestamp) / F.lit(window_size_us))


def _tumbling_previous_window_bucket_id(
    timestamp: F.Column, window_size: timedelta
) -> F.Column:
    """
    Calculate the bucket ID of the previous tumbling window.

    Returns the bucket ID that occurred immediately before the bucket containing
    the given timestamp. Used for point-in-time correctness to ensure we only
    use data from windows that ended before the training timestamp.

    Args:
        timestamp: Timestamp column
        window_size: Tumbling window size

    Returns:
        Column containing previous window's bucket ID
    """
    return _tumbling_window_bucket_id(timestamp, window_size) - F.lit(1)


def _compute_features_with_tumbling_windows(
    train_df: DataFrame,
    source_df: DataFrame,
    source: DataSource,
    train_ts_col: str,
    source_ts_col: str,
    time_window: TumblingWindow,
    window_features: List[Feature],
    source_collision_renames: Dict[str, str],
    source_alias: str,
) -> DataFrame:
    """
    Compute features for tumbling windows using pre-aggregation at bucket boundaries aligned to epoch. Multiple training rows in the same
    bucket share the same pre-computed aggregation.

    Algorithm:
        1. Bucket source events by start: bucket_id = start of this tumbling window
        2. Pre-aggregate per (entity, bucket_id)
        3. For training rows, find the start of the tumbling window immediately prior to train_ts
        4. Join on (entity, bucket_id)

    Args:
        train_df: Training DataFrame
        source_df: Source DataFrame (timestamp column has original name from source.timeseries_column)
        source: DataSource object
        train_ts_col: Training timestamp column name
        source_ts_col: Target name for source timestamp column (will be renamed internally)
        time_window: TumblingWindow object
        window_features: Features to compute for this window
        source_collision_renames: Dict mapping original column names to temp names for collision avoidance
        source_alias: Unique alias for this source to avoid naming conflicts

    Returns:
        DataFrame with training columns + computed feature columns

    Example:
        >>> # 7-day tumbling windows aligned to epoch
        >>> # Buckets: [0,7), [7,14), [14,21), ...
        >>> # Training at day 3: window_end=0, bucket_id=-7 (no data, uses defaults)
        >>> # Training at day 10: window_end=7, bucket_id=0 (uses bucket [0,7))
        >>> # Training at day 14.0: window_end=14, bucket_id=7 (uses bucket [7,14))
        >>> # This ensures PIT semantics: only events before train_ts are included
    """
    if not isinstance(time_window, TumblingWindow):
        raise ValueError(f"Expected TumblingWindow, got {type(time_window).__name__}")

    # Rename timestamp column to avoid conflicts (similar to continuous windows)
    source_df = source_df.withColumnRenamed(source.timeseries_column, source_ts_col)

    # Add bucket column to source dataframe for grouping
    bucket_col = _create_unique_string("bucket_id")

    source_bucket_id = _tumbling_window_bucket_id(
        F.col(source_ts_col), time_window.duration
    )
    source_with_bucket = source_df.withColumn(bucket_col, source_bucket_id)
    partition_cols = source.entity_columns + [bucket_col]

    # Build aggregation expressions for all features
    agg_exprs = []
    for feature in window_features:
        # Map feature inputs to actual column names (handle collision renames)
        mapped_inputs = []
        for input_col in feature.inputs:
            # Check if this input was renamed due to collision
            if input_col in source_collision_renames:
                actual_col_name = source_collision_renames[input_col]
            else:
                actual_col_name = input_col
            mapped_inputs.append(actual_col_name)

        # Get the Spark aggregation function for this feature using mapped column names
        spark_function = feature.function.spark_function(mapped_inputs)
        agg_exprs.append(spark_function.alias(feature.name))

    # Perform the aggregation
    pre_aggregated = source_with_bucket.groupBy(*partition_cols).agg(*agg_exprs)

    # Assign training rows to buckets: find the most recent window ending at or before train_ts
    train_bucket_id = _tumbling_previous_window_bucket_id(
        F.col(train_ts_col), time_window.duration
    )
    train_with_bucket = train_df.withColumn(bucket_col, train_bucket_id)

    # Join training data to pre-aggregated features
    join_keys = source.entity_columns + [bucket_col]
    result = train_with_bucket.join(pre_aggregated, join_keys, "left")

    # Apply default values for missing aggregations
    for feature in window_features:
        default_value = _get_default_value_for_function(feature.function.name)
        result = result.withColumn(
            feature.name, F.coalesce(F.col(feature.name), default_value)
        )

    # Clean up - remove bucket_id column
    result = result.drop(bucket_col)

    return result


def _sliding_start_boundary_micros(
    timestamp: F.Column,
    window_duration: timedelta,
    slide_duration: timedelta,
) -> F.Column:
    """
    Calculate the start boundary for a sliding window aligned to epoch.

    Args:
        timestamp: Timestamp column (in microseconds)
        window_duration: Duration of the sliding window
        slide_duration: Slide interval between windows

    Returns:
        Column with start boundary: floor((timestamp - duration) / slide) * slide
    """
    window_duration_us = _duration_to_micros(window_duration)
    slide_duration_us = _duration_to_micros(slide_duration)
    return F.floor(
        (timestamp - F.lit(window_duration_us)) / F.lit(slide_duration_us)
    ) * F.lit(slide_duration_us)


def _sliding_end_boundary_micros(
    timestamp: F.Column,
    slide_duration: timedelta,
) -> F.Column:
    """
    Calculate the end boundary for a sliding window aligned to epoch.

    Args:
        timestamp: Timestamp column (in microseconds)
        slide_duration: Slide interval between windows

    Returns:
        Column with end boundary: floor(timestamp / slide + 1) * slide
    """
    slide_duration_us = _duration_to_micros(slide_duration)
    return F.floor(timestamp / F.lit(slide_duration_us) + F.lit(1)) * F.lit(
        slide_duration_us
    )


def _compute_sliding_window_boundaries(
    train_df: DataFrame,
    timestamp_col: str,
    time_window: SlidingWindow,
    precision_factor: int,
) -> SlidingWindowBoundaries:
    """
    Compute the start/end boundaries and count for sliding windows aligned to epoch.

    This calculates the range of window boundaries needed to cover all training timestamps,
    using the sliding window's duration and slide parameters. Validates boundaries during
    construction (NULL checks and count limits).

    Args:
        train_df: Training DataFrame containing timestamps
        timestamp_col: Name of the timestamp column
        time_window: SlidingWindow configuration
        precision_factor: Microsecond precision factor for time range calculation

    Returns:
        SlidingWindowBoundaries: Validated boundary information with:
            - start_boundary_us: Earliest window end boundary (microseconds since epoch)
            - end_boundary_us: Latest window end boundary (microseconds since epoch)
            - num_boundaries: Total number of window boundaries needed

    Raises:
        ValueError: If timestamps contain NULLs or boundary count exceeds limits
    """
    # Create a DataFrame with min/max timestamps in microseconds
    train_ts_micros_col = F.unix_micros(train_df[timestamp_col])
    min_max_df = train_df.select(
        F.min(train_ts_micros_col).alias("min_ts_micros"),
        F.max(train_ts_micros_col).alias("max_ts_micros"),
    )

    # Calculate boundary range using Spark expressions (no collect needed) - aligned to epoch
    # start_boundary = floor((min_ts - duration) / slide) * slide
    # end_boundary = floor(max_ts / slide + 1) * slide
    # num_boundaries = (end_boundary - start_boundary) / slide
    slide_duration_us = _duration_to_micros(time_window.slide_duration)
    boundary_info_df = min_max_df.select(
        _sliding_start_boundary_micros(
            F.col("min_ts_micros"), time_window.duration, time_window.slide_duration
        ).alias("start_boundary"),
        _sliding_end_boundary_micros(
            F.col("max_ts_micros"), time_window.slide_duration
        ).alias("end_boundary"),
    ).withColumn(
        "num_boundaries",
        (
            (F.col("end_boundary") - F.col("start_boundary")) / F.lit(slide_duration_us)
        ).cast("long"),
    )

    # TODO (ML-58626): Centralize dataset validation logic into TrainingSetWithDeclarativeFeatures.validate()
    # This validation (and similar checks like continuous window row count limits) should be moved to an
    # explicit validation method that users can optionally call before load_df(). This would:
    # 1. Make validation explicit rather than surprising users during lazy DataFrame loading
    # 2. Provide early feedback on dataset size/time range issues before long-running computations
    # 3. Allow reuse across window types (sliding, continuous, tumbling)
    # 4. Enable users to decide when to pay the validation cost vs. proceeding with computation
    #
    # Current issue: This .first() call triggers a full table scan of train_df to compute min/max timestamps,
    # which can be expensive for large training datasets. Users may be surprised by this cost when calling
    # load_df(), especially if validation then fails after the scan completes.

    # Fetch the computed boundaries (triggers a single Spark action)
    boundary_row = boundary_info_df.select(
        "start_boundary", "end_boundary", "num_boundaries"
    ).first()

    # Check if training DataFrame is empty
    if boundary_row is None:
        raise ValueError(
            f"Training DataFrame is empty. Cannot compute sliding window boundaries for "
            f"timestamp column '{timestamp_col}'."
        )

    # Extract values (may be None if timestamps contain NULLs)
    start_boundary = boundary_row["start_boundary"]
    end_boundary = boundary_row["end_boundary"]
    num_boundaries = (
        boundary_row["num_boundaries"]
        if boundary_row["num_boundaries"] is not None
        else 0
    )

    return SlidingWindowBoundaries(
        start_boundary_us=start_boundary,
        end_boundary_us=end_boundary,
        num_boundaries=num_boundaries,
        timestamp_col=timestamp_col,
        time_window=time_window,
        precision_factor=precision_factor,
    )


def _compute_features_with_sliding_windows(
    train_df: DataFrame,
    source_df: DataFrame,
    source: DataSource,
    train_ts_col: str,
    source_ts_col: str,
    time_window: SlidingWindow,
    window_features: List[Feature],
    source_collision_renames: Dict[str, str],
    precision_factor: int,
) -> DataFrame:
    """
    Compute features for sliding windows using pre-aggregation at slide boundaries aligned to epoch. Source events are assigned
    to all overlapping windows they belong to.

    Algorithm:
        1. Generate window boundaries from min_train to max_train
        2. Join source with boundaries, filter to overlapping windows
        3. Pre-aggregate per (entity, window_end)
        4. Snap training timestamps to nearest boundary
        5. Join on (entity, window_end)

    Args:
        train_df: Training DataFrame
        source_df: Source DataFrame (timestamp column has original name from source.timeseries_column)
        source: DataSource object
        train_ts_col: Training timestamp column name
        source_ts_col: Target name for source timestamp column (will be renamed internally)
        time_window: SlidingWindow object
        window_features: Features to compute for this window
        source_collision_renames: Dict mapping original column names to temp names for collision avoidance
        precision_factor: Microsecond precision factor

    Returns:
        DataFrame with training columns + computed feature columns

    Example:
        >>> # 7-day window, 1-day slide
        >>> # Event on Jan 5 belongs to windows ending Jan 5, 6, 7, ..., 11
        >>> # Training row on Jan 10 uses window [Jan 3-10]
        >>> # Training row on Jan 11 uses window [Jan 4-11] (different data!)
    """
    if not isinstance(time_window, SlidingWindow):
        raise ValueError(f"Expected SlidingWindow, got {type(time_window).__name__}")

    # Validate slide_duration <= window_duration
    if time_window.slide_duration > time_window.duration:
        raise ValueError(
            f"slide_duration ({time_window.slide_duration}) cannot be greater than "
            f"window_duration ({time_window.duration})"
        )

    # Rename timestamp column to avoid conflicts (consistent with tumbling/continuous windows)
    source_df = source_df.withColumnRenamed(source.timeseries_column, source_ts_col)

    duration_microseconds = int(time_window.duration.total_seconds() * precision_factor)
    slide_microseconds = int(
        time_window.slide_duration.total_seconds() * precision_factor
    )

    # Compute window boundaries (validation happens in dataclass __post_init__)
    boundary_info = _compute_sliding_window_boundaries(
        train_df, train_ts_col, time_window, precision_factor
    )

    # Generate unique column name to avoid collisions with other tumbling windows with different duration
    window_end_col = _create_unique_string("window_end")

    # Generate window boundaries using PySpark functions
    # sequence(start, stop, step) generates array, then explode to rows
    start_boundary = boundary_info.start_boundary_us
    end_boundary = boundary_info.end_boundary_us
    num_boundaries = boundary_info.num_boundaries

    window_boundaries_df = train_df.sparkSession.range(1).select(
        F.explode(
            F.sequence(
                F.lit(start_boundary + duration_microseconds),
                F.lit(end_boundary),
                F.lit(slide_microseconds),
            )
        ).alias(window_end_col)
    )

    # Broadcast window boundaries if small enough to optimize range join
    # Broadcasting avoids shuffling the (typically much larger) source data
    # Each boundary is a long (8 bytes) + overhead, estimate ~16 bytes per row
    estimated_size_bytes = num_boundaries * 16
    if estimated_size_bytes < BROADCAST_JOIN_THRESHOLD.get():
        window_boundaries_df = F.broadcast(window_boundaries_df)

    # Assign source events to ALL windows they belong to
    # A source event at time E belongs to window ending at W if: W - duration < E < W
    # Note: Strict less-than for window_end to maintain point-in-time semantics
    # (events exactly at window_end would be "future" data for training at window_end)
    source_ts_micros = F.unix_micros(F.col(source_ts_col))

    # Use range join optimization with binning to avoid full cross product. Requires Spark 3.0+
    # Bin size = duration ensures events only compared to relevant window boundaries
    # https://docs.databricks.com/aws/en/optimizations/range-join
    source_exploded = source_df.join(
        window_boundaries_df.hint("range_join", duration_microseconds),
        (source_ts_micros > (F.col(window_end_col) - F.lit(duration_microseconds)))
        & (
            source_ts_micros < F.col(window_end_col)
        ),  # Strict < to exclude events at boundary
        "inner",
    )

    # Pre-aggregate features per window per entity
    partition_cols = source.entity_columns + [window_end_col]

    agg_exprs = []
    for feature in window_features:
        # Map feature inputs to actual column names (handle collision renames)
        mapped_inputs = []
        for input_col in feature.inputs:
            # Check if this input was renamed due to collision
            if input_col in source_collision_renames:
                actual_col_name = source_collision_renames[input_col]
            else:
                actual_col_name = input_col
            mapped_inputs.append(actual_col_name)

        # Get the Spark aggregation function for this feature using mapped column names
        spark_function = feature.function.spark_function(mapped_inputs)
        agg_exprs.append(spark_function.alias(feature.name))

    pre_aggregated = source_exploded.groupBy(*partition_cols).agg(*agg_exprs)

    # Assign training rows to nearest slide boundary
    # Find window ending at or before train_ts: floor((train_ts - duration) / slide) * slide + duration
    # This ensures the window end <= train_ts, maintaining point-in-time semantics
    train_ts_micros = F.unix_micros(F.col(train_ts_col))
    train_with_window = train_df.withColumn(
        window_end_col,
        F.floor(
            (train_ts_micros - F.lit(duration_microseconds)) / F.lit(slide_microseconds)
        )
        * F.lit(slide_microseconds)
        + F.lit(duration_microseconds),
    )

    # Join training data to pre-aggregated features
    join_keys = source.entity_columns + [window_end_col]
    result = train_with_window.join(pre_aggregated, join_keys, "left")

    # Apply default values for missing aggregations
    for feature in window_features:
        default_value = _get_default_value_for_function(feature.function.name)
        result = result.withColumn(
            feature.name, F.coalesce(F.col(feature.name), default_value)
        )

    # Clean up - remove window_end column
    result = result.drop(window_end_col)

    return result


def _create_joined_df_for_continuous_windows(
    train_df: DataFrame,
    source_df: DataFrame,
    source: DataSource,
    source_ts_col: str,
    source_alias: str,
) -> DataFrame:
    """
    Join training and source data for continuous window computation.

    This performs an inner join on entity columns, creating a potentially large
    cartesian product of training rows × matching source events. This is necessary
    for continuous windows which apply window functions per training row.

    Note: Tumbling/sliding windows do NOT use this - they use pre-aggregation instead.

    Args:
        train_df: Training DataFrame
        source_df: Source DataFrame (already renamed for collision handling)
        source: DataSource object
        source_ts_col: Unique column name for source timestamp in result
        source_alias: Unique alias for source in join

    Returns:
        Joined DataFrame with training columns + source timestamp + source input columns
    """
    train_df_alias = _create_unique_string("train")
    joined = (
        train_df.alias(train_df_alias)
        .join(
            source_df.alias(source_alias),
            [
                F.col(f"{train_df_alias}.{col}") == F.col(f"{source_alias}.{col}")
                for col in source.entity_columns
            ],
            "inner",
        )
        .select(
            *[F.col(f"{train_df_alias}.{col}").alias(col) for col in train_df.columns],
            # Rename source timestamp during select
            F.col(f"{source_alias}.{source.timeseries_column}").alias(source_ts_col),
            *[
                F.col(f"{source_alias}.{col_name}").alias(col_name)
                for col_name in source_df.columns
                if col_name not in (source.entity_columns + [source.timeseries_column])
            ],
        )
    )

    return joined


def _compute_features_with_continuous_windows(
    train_df: DataFrame,
    joined_df: DataFrame,
    source: DataSource,
    train_ts_col: str,
    source_ts_col: str,
    time_window: ContinuousWindow,
    window_features: List[Feature],
    source_collision_renames: Dict[str, str],
) -> DataFrame:
    """
    Compute features using per-row filtering with window functions.

    This function takes a pre-joined DataFrame (train + source) and applies time-based
    filtering and window aggregations for a specific time window.

    Algorithm:
        1. Filter joined data using time window condition (respects offset parameter)
        2. Apply window functions partitioned by (entity + training timestamp)
        3. Aggregate to ensure one row per training record

    Args:
        train_df: Original training DataFrame (for column reference)
        joined_df: Pre-joined DataFrame (train + source, joined on entity columns)
        source: DataSource object
        train_ts_col: Training timestamp column name
        source_ts_col: Source timestamp column name in joined_df
        time_window: ContinuousWindow object defining the time range
        window_features: Features to compute for this window
        source_collision_renames: Mapping of original column names to renamed ones

    Returns:
        DataFrame with training columns + computed feature columns

    Example:
        >>> # ContinuousWindow: 7-day window with 1-day offset (looks at data from 8 days ago to 1 day ago)
        >>> # Training row on Jan 10 uses window [Jan 2 - Jan 9]
        >>> window = ContinuousWindow(duration=timedelta(days=7), offset=timedelta(days=-1))
    """
    # Create time window condition with microsecond precision
    time_condition = _create_microsecond_precision_time_condition(
        source_ts_col, train_ts_col, time_window.duration, time_window.offset
    )

    # Filter joined data to only include records within the time window
    filtered_df = joined_df.filter(time_condition)

    # Create window specification for this time window
    # Partition by entity columns + training timestamp to ensure each training
    # record gets its own independent feature calculation
    partition_cols = source.entity_columns + [train_ts_col]
    window_spec = (
        Window.partitionBy(*partition_cols)
        .orderBy(source_ts_col)  # Order by source timestamp
        .rowsBetween(
            Window.unboundedPreceding, Window.unboundedFollowing
        )  # Use all rows in partition
    )

    # Batch all features for this window into a single DataFrame
    # Start with the filtered DataFrame for this time window
    windowed_df = filtered_df

    # Add all feature columns to the DataFrame in one pass
    feature_names = []
    for feature in window_features:
        # Map feature inputs to current DataFrame column names (handle renames)
        mapped_inputs = []
        for input_col in feature.inputs:
            # Check if this input was renamed due to collision
            if input_col in source_collision_renames:
                actual_col_name = source_collision_renames[input_col]
            else:
                actual_col_name = input_col
            mapped_inputs.append(actual_col_name)

        # Get the Spark aggregation function for this feature using mapped column names
        spark_function = feature.function.spark_function(mapped_inputs)

        # Add feature column to the DataFrame
        windowed_df = windowed_df.withColumn(
            feature.name, spark_function.over(window_spec)
        )
        feature_names.append(feature.name)

    # Select only necessary columns: training columns + computed features
    # Exclude source timestamp and input columns that are no longer needed
    computed_features = windowed_df.select(*train_df.columns, *feature_names)

    # Group by training record and aggregate features using first()
    # This handles any duplicates created by the joins
    features_df = (
        computed_features.groupBy(*train_df.columns)
        .agg(*[F.first(col).alias(col) for col in feature_names])
        .select(*train_df.columns, *feature_names)
    )

    return features_df


def augment_df_with_pit_computed_features(
    train_df: DataFrame,
    features: List[Feature],
    sources: Dict[DataSource, DataFrame],
) -> DataFrame:
    """
    This is an internal function that augments training DataFrame with point-in-time computed features.

    This function computes time-windowed features with point-in-time correctness using multiple data sources.
    Feature calculations are performed efficiently while maintaining microsecond precision and
    handling default values for empty windows.

    Args:
        train_df: Training DataFrame containing entity columns, timestamps, and labels
        features: List of Feature objects defining the computations to perform
        sources: Dictionary mapping DataSource objects to their loaded DataFrames

    Returns:
        DataFrame with original training data plus all computed feature columns

    Raises:
        ValueError: If features reference DataSources not present in sources dict
        ValueError: If required columns are missing from DataFrames

    Example:
        # Training data
        train_df = spark.createDataFrame([
            (1, datetime(2025, 5, 2), 'a'),
            (1, datetime(2025, 5, 4), 'b')
        ], ["customer_id", "ts", "label"])

        # Source data
        bookings_df = spark.createDataFrame([
            (1, datetime(2025, 5, 1), 123),
            (1, datetime(2025, 5, 3), 456)
        ], ["customer_id", "ts", "booking_id"])

        # Features
        features = [
            # Continuous window: 3-day window computed per training row
            Feature(source=bookings_source, inputs=["booking_id"], function=Count(),
                   time_window=ContinuousWindow(window_duration=timedelta(days=7))),
            # Tumbling window: Non-overlapping 7-day buckets aligned to epoch
            Feature(source=bookings_source, inputs=["booking_id"], function=Count(),
                   time_window=TumblingWindow(window_duration=timedelta(days=7))),
        ]

        # Sources mapping
        sources = {bookings_source: bookings_df}

        # Compute features
        result = augment_df_with_pit_computed_features(train_df, features, sources)

        # Result will have original columns plus computed features:
        # [customer_id, ts, label, booking_id_count_7d]
    """
    if not features:
        return train_df

    # Validate that all feature sources are available in sources dict
    feature_sources = {feature.source for feature in features}
    available_sources = set(sources.keys())
    missing_sources = feature_sources - available_sources
    if missing_sources:
        raise ValueError(
            f"Features reference DataSources not found in sources dict: "
            f"{[source.full_name() for source in missing_sources]}"
        )

    # Group features by data source, filter condition, and time window for efficient batch processing
    features_by_source_filter_and_window = _group_features_by_source_filter_and_window(
        features
    )

    # Process each (source, filter_condition) combination independently and collect results
    all_source_results = []

    for (
        filtered_source,
        windows_to_features,
    ) in features_by_source_filter_and_window.items():
        source = filtered_source.source
        filter_condition = filtered_source.filter_condition

        # Get the pre-loaded source DataFrame
        source_df = sources[source]

        # Apply filter condition if specified
        if filter_condition:
            source_df = source_df.where(filter_condition)

        # Extract the training timestamp column name
        train_ts_col = _extract_train_timestamp_column(train_df, source)

        # Generate a unique column name for the source timestamp
        source_ts_col = _create_unique_string("source_ts")

        # Handle column name collisions by temporarily renaming source columns
        train_columns = set(train_df.columns)
        source_columns = set(source_df.columns)
        collision_columns = (
            train_columns.intersection(source_columns)
            - set(source.entity_columns)
            - {source.timeseries_column}
        )

        # Create mapping for collision resolution specific to this source
        source_collision_renames = {}
        source_df_renamed = source_df

        # Generate source alias using FilteredDataSource
        source_alias = filtered_source.generate_alias()

        if collision_columns:
            # Temporarily rename colliding columns in source DataFrame
            # Use source_alias to avoid cross-source and cross-filter conflicts
            for col_name in collision_columns:
                temp_name = _create_unique_string(f"__temp_{source_alias}_{col_name}")
                source_collision_renames[
                    col_name
                ] = temp_name  # Map original name to temp name
                source_df_renamed = source_df_renamed.withColumnRenamed(
                    col_name, temp_name
                )

        # For continuous windows, perform the join once outside the loop for efficiency
        joined_df = None
        has_continuous_windows = any(
            isinstance(tw, (ContinuousWindow, TimeWindow))
            for tw in windows_to_features.keys()
        )
        if has_continuous_windows:
            joined_df = _create_joined_df_for_continuous_windows(
                train_df=train_df,
                source_df=source_df_renamed,
                source=source,
                source_ts_col=source_ts_col,
                source_alias=source_alias,
            )

        current_df = train_df

        for time_window, window_features in windows_to_features.items():
            match time_window:
                case TumblingWindow():
                    computed_features = _compute_features_with_tumbling_windows(
                        train_df=current_df,
                        source_df=source_df_renamed,
                        source=source,
                        train_ts_col=train_ts_col,
                        source_ts_col=source_ts_col,
                        time_window=time_window,
                        window_features=window_features,
                        source_collision_renames=source_collision_renames,
                        source_alias=source_alias,
                    )
                case SlidingWindow():
                    computed_features = _compute_features_with_sliding_windows(
                        train_df=train_df,
                        source_df=source_df_renamed,
                        source=source,
                        train_ts_col=train_ts_col,
                        source_ts_col=source_ts_col,
                        time_window=time_window,
                        window_features=window_features,
                        source_collision_renames=source_collision_renames,
                        precision_factor=_PRECISION_FACTOR,
                    )
                # Preserve backward compatibility with ContinuousWindow and TimeWindow
                case ContinuousWindow() | TimeWindow():
                    computed_features = _compute_features_with_continuous_windows(
                        train_df=train_df,
                        joined_df=joined_df,
                        source=source,
                        train_ts_col=train_ts_col,
                        source_ts_col=source_ts_col,
                        time_window=cast(ContinuousWindow, time_window),
                        window_features=window_features,
                        source_collision_renames=source_collision_renames,
                    )

            # Create unique aliases for the join to avoid naming conflicts
            current_alias = _create_unique_string("current")
            computed_alias = _create_unique_string("computed")

            # Store current column names before joining
            current_columns = current_df.columns

            current_df = (
                current_df.alias(current_alias)
                .join(computed_features.alias(computed_alias), train_df.columns, "left")
                .select(
                    # Select all existing columns from current_df which includes:
                    #    Columns from the training data
                    #    Computed features from previous windows using this source
                    *[F.col(f"{current_alias}.{col}") for col in current_columns],
                    # Select all computed features with coalesce for default values
                    *[
                        F.coalesce(
                            F.col(f"{computed_alias}.{feature.name}"),
                            _get_default_value_for_function(feature.function.name),
                        ).alias(feature.name)
                        for feature in window_features
                    ],
                )
            )

        # Clean up intermediate columns and prepare final result
        feature_columns = [
            feature.name
            for window_features in windows_to_features.values()
            for feature in window_features
        ]
        columns_to_keep = train_df.columns + feature_columns

        # Group by training record and aggregate features using first()
        # This handles any duplicates created by the joins
        source_result = (
            current_df.groupBy(*train_df.columns)
            .agg(*[F.first(col).alias(col) for col in feature_columns])
            .select(*columns_to_keep)
        )

        all_source_results.append(source_result)

    # Combine results from all data sources
    if len(all_source_results) == 1:
        # Single source - return result directly
        final_result = all_source_results[0]
    else:
        # Multiple sources - join results together
        final_result = train_df

        for source_result in all_source_results:
            # Extract only the new feature columns from this source
            source_feature_cols = [
                col for col in source_result.columns if col not in train_df.columns
            ]

            # Select training columns + new features from this source
            source_features_only = source_result.select(
                *train_df.columns, *source_feature_cols
            )

            # Left join to preserve all training records
            final_result = final_result.join(
                source_features_only,
                train_df.columns,  # Join on all original training columns
                "left",
            )

    return final_result
