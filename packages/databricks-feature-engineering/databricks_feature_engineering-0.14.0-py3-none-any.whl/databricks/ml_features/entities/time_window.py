import datetime
from typing import Any, Dict, List, Optional

from pyspark import sql
from pyspark.sql.window import WindowSpec

from databricks.ml_features.constants import (
    _FEATURE_ENGINEERING_COMPUTATION_PRECISION,
    _FEATURE_ENGINEERING_COMPUTATION_WINDOW_END_INCLUSIVE,
    _FEATURE_ENGINEERING_COMPUTATION_WINDOW_START_INCLUSIVE,
)
from databricks.ml_features.utils.time_utils import (
    dict_to_timedelta,
    duration_string_to_timedelta,
    format_duration,
    timedelta_to_dict,
    timedelta_to_duration_string,
)
from databricks.ml_features_common.entities._feature_store_object import (
    _FeatureStoreObject,
)
from databricks.sdk.service.ml import TimeWindow as SDKTimeWindow


class TimeWindow(_FeatureStoreObject):
    """
    Defines an aggregation time window.

    :param duration: The length of the time window. This defines how far back in time the window spans from the
        requested time. This must be positive. The interval defined by this window includes the start (earlier in time)
        endpoint, but not the end (later in time) endpoint. That is, the interval is [ts - duration, ts).
    :param offset: Optional offset to adjust the end of the window. This can be used to shift the window by a certain
        duration backwards. This must be non-positive if provided. Defaults to 0.
    """

    DURATION_FIELD_NAME = "duration"
    OFFSET_FIELD_NAME = "offset"

    def __init__(
        self,
        *,
        duration: datetime.timedelta,
        offset: Optional[datetime.timedelta] = None,
        _start_inclusive: bool = _FEATURE_ENGINEERING_COMPUTATION_WINDOW_START_INCLUSIVE,
        _end_inclusive: bool = _FEATURE_ENGINEERING_COMPUTATION_WINDOW_END_INCLUSIVE,
    ):
        """Initialize a TimeWindow object. See class documentation."""
        self._duration = duration
        self._offset = offset if offset is not None else datetime.timedelta(0)
        self._start_inclusive = _start_inclusive
        self._end_inclusive = _end_inclusive

        self._validate_parameters()

    @property
    def duration(self) -> datetime.timedelta:
        """The length of the time window."""
        return self._duration

    @property
    def offset(self) -> datetime.timedelta:
        """The offset to adjust the end of the window."""
        return self._offset

    def __str__(self) -> str:
        """
        Return a string representation of the time window for use in feature names.

        Returns a formatted string like "7d" or "7d_1d" depending on whether
        an offset is present. Offsets are displayed as positive values even though
        they are stored as non-positive.

        Returns:
            str: Formatted time window string (e.g., "7d", "1h", "7d_1d", "2h_30m")
        """
        duration_str = format_duration(self.duration)

        if not self._offset or self._offset == datetime.timedelta(0):
            return duration_str

        # Negate the offset since it's stored as non-positive but displayed as positive
        offset_str = format_duration(-self._offset)
        return f"{duration_str}_{offset_str}"

    def __repr__(self) -> str:
        """Return a detailed string representation of the time window."""
        if self._offset and self._offset != datetime.timedelta(0):
            return f"TimeWindow(duration={self._duration!r}, offset={self._offset!r})"
        return f"TimeWindow(duration={self._duration!r})"

    def __hash__(self) -> int:
        """
        Return hash of the string representation of the time window.

        This makes TimeWindow objects hashable and suitable for use as dictionary keys.
        The hash is based on the same string representation used in __str__.

        Returns:
            int: Hash value based on the string representation
        """
        return hash(str(self))

    def _validate_parameters(self):
        """Validates the parameters provided to the TimeWindow class."""
        if not isinstance(
            self._duration, datetime.timedelta
        ) or self._duration <= datetime.timedelta(0):
            raise ValueError("The 'duration' must be a positive datetime.timedelta.")

        if not isinstance(
            self._offset, datetime.timedelta
        ) or self._offset > datetime.timedelta(0):
            raise ValueError("The 'offset' must be non-positive if provided.")

    def spark_window(
        self, partition_columns: List[str], order_column: str
    ) -> WindowSpec:
        """
        Creates a Spark WindowSpec using rangeBetween with time-based windows.

        Parameters:
            partition_columns (list[str]): Columns to partition by.
            order_column (str): Column to order by (must be one timestamp column).

        Returns:
            pyspark.sql.window.Window: A configured WindowSpec.
        """
        # Apply precision factor to duration and offset (but not to inclusive/exclusive adjustments)
        precision_factor = int(1 / _FEATURE_ENGINEERING_COMPUTATION_PRECISION)

        offset_seconds = int(self.offset.total_seconds()) if self.offset else 0
        duration_seconds = int(self.duration.total_seconds())

        # Calculate base time ranges, then apply precision factor
        # TBD: if `offset` is defined and is negative, should we ignore the end boundary condition, aka always inclusive?
        start = (-duration_seconds + offset_seconds) * precision_factor + (
            0 if self._start_inclusive else 1
        )
        end = (offset_seconds * precision_factor) - (0 if self._end_inclusive else 1)

        return (
            sql.Window.partitionBy(*partition_columns)
            .orderBy(order_column)
            .rangeBetween(start, end)
        )

    def _to_yaml_dict(self) -> Dict[str, Any]:
        """Convert the time window to a dictionary that can be used to generate a YAML file."""
        result = {
            self.DURATION_FIELD_NAME: timedelta_to_dict(self.duration),
        }
        # Only include offset if it's not zero/None.
        if self.offset and self.offset != datetime.timedelta(0):
            result[self.OFFSET_FIELD_NAME] = timedelta_to_dict(self.offset)
        return result

    @classmethod
    def _from_yaml_dict(cls, time_window_dict: Dict[str, Any]) -> "TimeWindow":
        """Create a TimeWindow from a dictionary loaded from YAML."""
        duration = dict_to_timedelta(time_window_dict[cls.DURATION_FIELD_NAME])
        offset = (
            dict_to_timedelta(time_window_dict[cls.OFFSET_FIELD_NAME])
            if cls.OFFSET_FIELD_NAME in time_window_dict
            else None
        )
        return cls(duration=duration, offset=offset)

    def _to_sdk_time_window(self) -> "SDKTimeWindow":
        from databricks.sdk.service.ml import ContinuousWindow as SDKContinuousWindow

        """Convert to SDK TimeWindow with ContinuousWindow oneof."""
        continuous = SDKContinuousWindow(
            window_duration=timedelta_to_duration_string(self.duration),
            offset=(
                timedelta_to_duration_string(self.offset)
                if self.offset and self.offset != datetime.timedelta(0)
                else None
            ),
        )
        return SDKTimeWindow(continuous=continuous)

    @classmethod
    def _from_sdk_time_window(cls, sdk_time_window: "SDKTimeWindow") -> "TimeWindow":
        """Create appropriate TimeWindow subclass from SDK TimeWindow based on oneof field."""
        # Handle the oneof window_type field - delegate to subclass-specific methods
        if sdk_time_window.continuous is not None:
            return ContinuousWindow(
                window_duration=duration_string_to_timedelta(
                    sdk_time_window.continuous.window_duration
                ),
                offset=(
                    duration_string_to_timedelta(sdk_time_window.continuous.offset)
                    if sdk_time_window.continuous.offset
                    else None
                ),
            )
        elif sdk_time_window.tumbling is not None:
            return TumblingWindow(
                window_duration=duration_string_to_timedelta(
                    sdk_time_window.tumbling.window_duration
                )
            )
        elif sdk_time_window.sliding is not None:
            return SlidingWindow(
                window_duration=duration_string_to_timedelta(
                    sdk_time_window.sliding.window_duration
                ),
                slide_duration=duration_string_to_timedelta(
                    sdk_time_window.sliding.slide_duration
                ),
            )
        else:
            raise ValueError(
                "SDK TimeWindow must have one of continuous, tumbling, or sliding set"
            )


class TumblingWindow(TimeWindow):
    """
    Tumbling windows partition a continuous stream of data into non-overlapping,
    fixed-duration windows. Each event belongs to exactly one window.

    Example: 5-day tumbling creates windows [Day1-5], [Day6-10], [Day11-15]

    :param window_duration: The length of each time window. This must be positive.
    """

    def __init__(self, *, window_duration: datetime.timedelta):
        """Initialize a TumblingWindow object. See class documentation."""
        # Tumbling windows don't use offset - each window is fixed duration with no overlap
        super().__init__(duration=window_duration, offset=datetime.timedelta(0))

    def __str__(self) -> str:
        """
        Return a string representation of the tumbling window.

        Returns a formatted string like "tumbling_7d".

        Returns:
            str: Formatted tumbling window string
        """
        duration_str = format_duration(self.duration)
        return f"tumbling_{duration_str}"

    def __repr__(self) -> str:
        """Return a detailed string representation of the tumbling window."""
        return f"TumblingWindow(window_duration={self._duration!r})"

    def _to_sdk_time_window(self) -> SDKTimeWindow:
        from databricks.sdk.service.ml import TumblingWindow as SDKTumblingWindow

        """Convert to SDK TimeWindow with TumblingWindow oneof."""
        tumbling = SDKTumblingWindow(
            window_duration=timedelta_to_duration_string(self.duration)
        )
        return SDKTimeWindow(tumbling=tumbling)


class SlidingWindow(TimeWindow):
    """
    Sliding windows create overlapping, fixed-duration windows that advance by
    a specified slide interval. Data points can belong to multiple windows.

    Example: 5-day window, 1-day slide creates overlapping 5-day periods:
    [Day1-5], [Day2-6], [Day3-7], etc.

    :param window_duration: The length of each time window. This must be positive.
    :param slide_duration: The interval by which windows advance. This must be positive and less than window_duration.
    """

    def __init__(
        self,
        *,
        window_duration: datetime.timedelta,
        slide_duration: datetime.timedelta,
    ):
        """Initialize a SlidingWindow object. See class documentation."""
        self._slide_duration = slide_duration
        super().__init__(duration=window_duration, offset=datetime.timedelta(0))

    def _validate_parameters(self):
        """Validates the parameters provided to the SlidingWindow class."""
        super()._validate_parameters()
        if not isinstance(
            self._slide_duration, datetime.timedelta
        ) or self._slide_duration <= datetime.timedelta(0):
            raise ValueError(
                "The 'slide_duration' must be a positive datetime.timedelta."
            )
        if self._slide_duration >= self._duration:
            raise ValueError(
                "The 'slide_duration' must be less than the 'window_duration'."
            )

    @property
    def slide_duration(self) -> datetime.timedelta:
        """The interval by which windows advance."""
        return self._slide_duration

    def __str__(self) -> str:
        """
        Return a string representation of the sliding window.

        Returns a formatted string like "sliding_7d_1d".

        Returns:
            str: Formatted sliding window string
        """
        duration_str = format_duration(self.duration)
        slide_str = format_duration(self.slide_duration)
        return f"sliding_{duration_str}_{slide_str}"

    def __repr__(self) -> str:
        """Return a detailed string representation of the sliding window."""
        return f"SlidingWindow(window_duration={self._duration!r}, slide_duration={self._slide_duration!r})"

    def _to_sdk_time_window(self) -> SDKTimeWindow:
        """Convert to SDK TimeWindow with SlidingWindow oneof."""
        from databricks.sdk.service.ml import SlidingWindow as SDKSlidingWindow

        sliding = SDKSlidingWindow(
            window_duration=timedelta_to_duration_string(self.duration),
            slide_duration=timedelta_to_duration_string(self.slide_duration),
        )
        return SDKTimeWindow(sliding=sliding)


class ContinuousWindow(TimeWindow):
    """
    Continuous windows are typically used for point-in-time windows, where duration and offset are explicitly defined.
    This provides maximum fidelity for windowing scenarios.

    Timeline:  <── older ─────────────────── evaluation_time ──> newer

    Basic Window (duration=7d):
            [─── 7 days ───]|
            └─ start        └─ evaluation_time (excluded)

    With Offset (duration=7d, offset=-1d):
        [─── 7 days ───]        |
        └─ start       └─ end   └─ evaluation_time
                        (1d ago)

    :param window_duration: The length of the window from the event time. This must be positive.
    :param offset: Adjustment the end of the window backwards from the event time before the window starts.
                   This must be non-positive if provided. Defaults to 0.
    """

    def __init__(
        self,
        *,
        window_duration: datetime.timedelta,
        offset: Optional[datetime.timedelta] = None,
    ):
        """Initialize a ContinuousWindow object. See class documentation."""
        super().__init__(duration=window_duration, offset=offset)

    def __str__(self) -> str:
        """
        Return a string representation of the continuous window.

        Returns a formatted string like "continuous_7d" or "continuous_7d_1d"
        depending on whether an offset is present.

        Returns:
            str: Formatted continuous window string
        """
        duration_str = format_duration(self.duration)
        if not self.offset or self.offset == datetime.timedelta(0):
            return f"continuous_{duration_str}"

        # Negate the offset since it's stored as non-positive but displayed as positive
        offset_str = format_duration(-self.offset)
        return f"continuous_{duration_str}_{offset_str}"

    def __repr__(self) -> str:
        """Return a detailed string representation of the continuous window."""
        if self._offset and self._offset != datetime.timedelta(0):
            return f"ContinuousWindow(window_duration={self._duration!r}, offset={self._offset!r})"
        return f"ContinuousWindow(window_duration={self._duration!r})"


# Backward compatibility alias for existing code
Window = TimeWindow
