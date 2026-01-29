import io
import logging
import os
import time
from collections import defaultdict
from typing import Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from databricks.ml_features._spark_client._spark_client import SparkClient
from databricks.ml_features.constants import _FEATURE_ENGINEERING_COMPUTATION_PRECISION
from databricks.ml_features.entities.cron_schedule import CronSchedule
from databricks.ml_features.entities.data_source import DataSource
from databricks.ml_features.entities.feature import Feature
from databricks.ml_features.entities.feature_aggregations import FeatureAggregations
from databricks.ml_features.entities.materialized_view_info import MaterializedViewInfo
from databricks.ml_features.utils.aggregation.generate_query import (
    generate_aggregation_query,
    generate_dlt_notebook,
    get_aggregated_view_schema,
)
from databricks.ml_features.utils.utils import get_workspace_url
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs, pipelines, workspace

JOB_TASK_KEY = "update_materialized_view"

_logger = logging.getLogger(__name__)


class MaterializationClient:
    def __init__(self, spark_client: SparkClient):
        self._spark_client = spark_client

    def _generate_materialization_id(self) -> str:
        return time.strftime("%Y%m%d_%H%M%S")

    def _generate_notebook_path(self, materialization_id: str, table: str) -> str:
        return f"databricks_feature_materialization/{materialization_id}_{table}.py"

    def _generate_pipeline_name(self, materialization_id: str, table: str) -> str:
        return f"databricks_feature_materialization_{materialization_id}_{table}"

    def _generate_job_name(self, materialization_id: str, table: str) -> str:
        return f"databricks_feature_materialization_{materialization_id}_{table}"

    def _validate_feature_aggregations(self, features: FeatureAggregations):
        assert self._spark_client.table_exists(
            features.source_table
        ), f"Source table {features.source_table} does not exist"

    def _validate_output_table(self, output_table: str):
        assert not self._spark_client.table_exists(
            output_table
        ), f"Output materialized view {output_table} already exists"

    def aggregate_features(self, features: FeatureAggregations) -> DataFrame:
        return self._spark_client._spark.sql(
            generate_aggregation_query(features, self._spark_client)
        )

    def compute_features(
        self,
        features: List[Feature],
        allow_multiple_sources: bool = False,
    ) -> Dict[DataSource, DataFrame]:
        # Validate input
        if not features:
            raise RuntimeError("features argument cannot be None or empty")

        # Group features by their data source and granularity
        # Features with the same source and granularity are processed together
        # Supports SlidingWindow, TumblingWindow, and ContinuousWindow
        feature_groups = defaultdict(list)
        for feature in features:
            # Group by (source, granularity) tuple
            # Extract granularity: slide_duration for SlidingWindow, duration for others
            if hasattr(feature.time_window, "slide_duration"):
                granularity = feature.time_window.slide_duration
            elif hasattr(feature.time_window, "duration"):
                granularity = feature.time_window.duration
            else:
                raise ValueError(
                    f"Feature {feature.name} has unsupported time_window type: {type(feature.time_window).__name__}"
                )
            key = (feature.source, granularity)
            feature_groups[key].append(feature)

        # Check for multiple sources if not allowed
        unique_sources = set(source for source, _ in feature_groups.keys())
        if not allow_multiple_sources and len(unique_sources) > 1:
            source_names = ", ".join(
                [f"'{source.full_name()}'" for source in unique_sources]
            )
            raise ValueError(
                f"Multiple sources are not allowed in this operation. Provided features has these sources: {source_names}"
            )

        # Check if feature names are unique - if not, we need to use full_name with "__" separator
        use_full_names = len(set(feature.name for feature in features)) != len(features)

        # This will be the final result of the computation, a dictionary of source to dataframe with features joined
        sources_joined_with_features = {}

        for (
            source,
            granularity,
        ), source_features in feature_groups.items():
            aggregations = [
                feature.computation_function(
                    filter_condition=feature.filter_condition,
                    output_alias=feature.full_name.replace(".", "__")
                    if use_full_names
                    else None,
                )
                for feature in source_features
            ]

            # Calculate precision factor, handling the case where precision could be 0
            precision_factor = (
                1 / _FEATURE_ENGINEERING_COMPUTATION_PRECISION
                if _FEATURE_ENGINEERING_COMPUTATION_PRECISION != 0
                else 1
            )

            # Load source data and pre-seed the result dataframe with the original source data
            source_df = source.load_df(self._spark_client)
            if not source in sources_joined_with_features:
                sources_joined_with_features[source] = source_df

            # Add timestamp ordering column and select required columns
            feature_df = source_df.withColumn(
                source.order_column,
                F.col(source.timeseries_column).cast("timestamp").cast("long")
                * int(precision_factor)
                + (
                    F.col(source.timeseries_column).cast("timestamp").cast("double")
                    * precision_factor
                    % precision_factor
                ).cast("long"),
            ).select(
                *(source.entity_columns + [source.timeseries_column] + aggregations)
            )

            # Left join to preserve all rows from base DataFrame
            # Filter conditions may result in NULL values for filtered-out rows
            join_keys = source.entity_columns + [source.timeseries_column]
            merged_df = sources_joined_with_features[source].join(
                feature_df, on=join_keys, how="left"
            )
            sources_joined_with_features[source] = merged_df

        return sources_joined_with_features

    def create_materialized_view(
        self,
        *,
        features: FeatureAggregations,
        output_table: str,
        schedule: Optional[CronSchedule],
    ) -> MaterializedViewInfo:
        """
        Note:
        - output_table must be a validated full UC table name in the form of <catalog_name>.<schema_name>.<table_name>
        """
        w = WorkspaceClient()
        materialization_id = self._generate_materialization_id()
        catalog, schema, table = output_table.split(".")
        notebook_path = f"/Users/{w.current_user.me().user_name}/{self._generate_notebook_path(materialization_id, table)}"

        self._validate_feature_aggregations(features)
        self._validate_output_table(output_table)

        aggregated_view_df = self.aggregate_features(features)
        aggregated_view_schema = get_aggregated_view_schema(
            features, aggregated_view_df
        )
        formatted_notebook_source = generate_dlt_notebook(
            features, table, aggregated_view_schema, self._spark_client
        )

        w.workspace.mkdirs(os.path.dirname(notebook_path))
        w.workspace.upload(
            notebook_path,
            io.BytesIO(formatted_notebook_source.encode()),
            format=workspace.ImportFormat.SOURCE,
            language=workspace.Language.SQL,
        )

        pipeline_name = self._generate_pipeline_name(materialization_id, table)
        pipeline_create_response = w.pipelines.create(
            continuous=False,
            name=pipeline_name,
            libraries=[
                pipelines.PipelineLibrary(
                    notebook=pipelines.NotebookLibrary(path=notebook_path)
                )
            ],
            catalog=catalog,
            target=schema,
            serverless=True,
        )
        _logger.info(
            f"Created pipeline: name = {pipeline_name}, id = {pipeline_create_response.pipeline_id}"
        )

        workspace_url = get_workspace_url()
        if isinstance(workspace_url, str):
            if workspace_url.endswith("/"):
                workspace_url = workspace_url[:-1]

            pipeline_url = (
                f"{workspace_url}/pipelines/{pipeline_create_response.pipeline_id}"
            )
            _logger.info(f"Pipeline URL: {pipeline_url}")

        if schedule is not None:
            job_name = self._generate_job_name(materialization_id, table)
            job_create_response = w.jobs.create(
                name=job_name,
                tasks=[
                    jobs.Task(
                        task_key=JOB_TASK_KEY,
                        pipeline_task=jobs.PipelineTask(
                            pipeline_id=pipeline_create_response.pipeline_id
                        ),
                    )
                ],
                schedule=jobs.CronSchedule(
                    quartz_cron_expression=schedule.quartz_cron_expression,
                    timezone_id=schedule.timezone_id,
                ),
                max_concurrent_runs=1,
            )
            _logger.info(
                f"Created schedule job: name = {job_name}, id = {job_create_response.job_id}"
            )

            w.jobs.run_now(job_id=job_create_response.job_id)

        else:
            w.pipelines.start_update(pipeline_id=pipeline_create_response.pipeline_id)

        return MaterializedViewInfo(
            pipeline_id=pipeline_create_response.pipeline_id,
            pipeline_name=pipeline_name,
        )
