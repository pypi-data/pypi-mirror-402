import datetime
import logging
import os
from collections import defaultdict
from dataclasses import replace
from itertools import islice
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple, Union

import mlflow
import yaml
from mlflow.utils import databricks_utils
from mlflow.utils.annotations import experimental
from mlflow.utils.env_manager import LOCAL
from pyspark.sql import DataFrame
from pyspark.sql.streaming import StreamingQuery
from pyspark.sql.types import StructType

from databricks.feature_engineering.entities import (
    DataFrameSource,
    DataSource,
    DeltaTableSource,
    Feature,
    Function,
    KafkaConfig,
    KafkaSource,
    OfflineStoreConfig,
    OnlineStoreConfig,
    SlidingWindow,
    TimeWindow,
    TumblingWindow,
)
from databricks.feature_engineering.entities.cron_schedule import CronSchedule
from databricks.feature_engineering.entities.feature_aggregations import (
    FeatureAggregations,
)
from databricks.feature_engineering.entities.feature_function import FeatureFunction
from databricks.feature_engineering.entities.feature_lookup import FeatureLookup
from databricks.feature_engineering.entities.feature_table import FeatureTable
from databricks.feature_engineering.entities.materialized_view_info import (
    MaterializedViewInfo,
)
from databricks.feature_engineering.online_store_spec import OnlineStoreSpec
from databricks.feature_engineering.training_set import TrainingSet
from databricks.ml_features import flags  # Note: this allows patching flags for testing
from databricks.ml_features._catalog_client._catalog_client import CatalogClient
from databricks.ml_features._catalog_client._catalog_client_helper import (
    CatalogClientHelper,
)
from databricks.ml_features._compute_client._compute_client import ComputeClient
from databricks.ml_features._databricks_client._databricks_client import (
    DatabricksClient,
)
from databricks.ml_features._feature_serving_endpoint_client._feature_serving_endpoint_client import (
    FeatureServingEndpointClient,
)
from databricks.ml_features._materialization_client._materialization_client import (
    MaterializationClient,
)
from databricks.ml_features._online_store_publish_client._online_store_publish_client import (
    NOSQL_SPECS,
    is_rdbms_spec,
)
from databricks.ml_features._publish_client._publish_client import PublishClient
from databricks.ml_features._spark_client._spark_client import SparkClient
from databricks.ml_features._spark_client._spark_client_helper import SparkClientHelper
from databricks.ml_features._training_scoring_client._training_scoring_client import (
    TrainingScoringClient,
)
from databricks.ml_features.api.proto.feature_catalog_pb2 import (
    LogClientEvent,
    ProducerAction,
)
from databricks.ml_features.constants import (
    _DEFAULT_PUBLISH_STREAM_TRIGGER,
    _DEFAULT_WRITE_STREAM_TRIGGER,
    MERGE,
    MODEL_DATA_PATH_ROOT,
    PUBLISH_MODE_CONTINUOUS,
    PUBLISH_MODE_SNAPSHOT,
    PUBLISH_MODE_TRIGGERED,
)
from databricks.ml_features.entities.aggregation import Aggregation
from databricks.ml_features.entities.feature import SDKFeature
from databricks.ml_features.entities.feature_serving_endpoint import (
    EndpointCoreConfig,
    FeatureServingEndpoint,
)
from databricks.ml_features.entities.feature_spec_info import FeatureSpecInfo
from databricks.ml_features.entities.online_store import DatabricksOnlineStore
from databricks.ml_features.entities.published_table import PublishedTable
from databricks.ml_features.entities.training_set import (
    TrainingSetWithDeclarativeFeatures,
)
from databricks.ml_features.utils import request_context
from databricks.ml_features.utils.feature_serving_endpoint_utils import (
    format_endpoint_core_config,
    format_feature_serving_endpoint_name,
)
from databricks.ml_features.utils.feature_utils import (
    format_feature_lookups_and_functions,
)
from databricks.ml_features.utils.request_context import RequestContext
from databricks.ml_features.utils.utils import as_list, enable_if
from databricks.ml_features_common import mlflow_model_constants
from databricks.ml_features_common.utils import uc_utils
from databricks.ml_features_common.utils.uc_utils import validate_qualified_feature_name
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import AlreadyExists, NotFound, ResourceAlreadyExists
from databricks.sdk.service import catalog
from databricks.sdk.service.catalog import (
    DataSourceFormat,
    SecurableKind,
    TableInfo,
    TableType,
)
from databricks.sdk.service.ml import (
    AuthConfig,
    CreateMaterializedFeatureRequest,
    JobContext,
    LineageContext,
    MaterializedFeature,
    MaterializedFeaturePipelineScheduleState,
    OnlineStore,
    SchemaConfig,
    SubscriptionMode,
)

_logger = logging.getLogger(__name__)


class _UnsetType(str):
    def __repr__(self):
        return "<UNSET>"


UNSET = _UnsetType()


class FeatureEngineeringClient:
    """
    Client for interacting with the Databricks Feature Engineering in Unity Catalog.

    .. note::
        Use :class:`Databricks FeatureStoreClient <databricks.feature_store.client.FeatureStoreClient>` for workspace feature tables in hive metastore
    """

    def __init__(
        self,
        *,
        model_registry_uri: Optional[str] = None,
    ):
        """
        Initialize a client to interact with Feature Engineering in Unity Catalog.

        Creates a client to interact with Feature Engineering in Unity Catalog.

        :param model_registry_uri: Address of local or remote model registry server. If not provided,
          defaults to the local server.
        """
        self._catalog_client = CatalogClient(
            databricks_utils.get_databricks_host_creds,
            feature_store_uri=None,  # multi-workspace is not supported in FE client
        )
        # The Databricks client must be local from the context of the notebook
        self._databricks_client = DatabricksClient(
            databricks_utils.get_databricks_host_creds
        )
        self._catalog_client_helper = CatalogClientHelper(
            self._catalog_client, self._databricks_client
        )

        self._spark_client = SparkClient()
        if not self._spark_client._on_spark_driver:
            _logger.warning(
                "Feature Engineering client functionality is limited when running outside of a Spark driver node. Spark operations will fail."
            )

        self._spark_client_helper = SparkClientHelper(self._spark_client)
        self._compute_client = ComputeClient(
            catalog_client=self._catalog_client,
            catalog_client_helper=self._catalog_client_helper,
            spark_client=self._spark_client,
            spark_client_helper=self._spark_client_helper,
            databricks_client=self._databricks_client,
        )
        self._materialization_client = MaterializationClient(self._spark_client)
        self._workspace_client = WorkspaceClient()
        self._training_scoring_client = TrainingScoringClient(
            catalog_client=self._catalog_client,
            catalog_client_helper=self._catalog_client_helper,
            spark_client=self._spark_client,
            spark_client_helper=self._spark_client_helper,
            materialization_client=self._materialization_client,
            databricks_client=self._databricks_client,
            workspace_client=self._workspace_client,
            model_registry_uri=model_registry_uri,
        )
        self._model_registry_uri = model_registry_uri
        self._feature_serving_endpoint_client = FeatureServingEndpointClient(
            get_host_creds=databricks_utils.get_databricks_host_creds, fs_client=self
        )
        self._publish_client = PublishClient(
            catalog_client=self._catalog_client,
            catalog_client_helper=self._catalog_client_helper,
            spark_client=self._spark_client,
            spark_client_helper=self._spark_client_helper,
            workspace_client=self._workspace_client,
        )

    def _validate_is_uc_table_name(self, name: str) -> None:
        full_name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        if not uc_utils.is_uc_entity(full_name):
            raise ValueError(
                "FeatureEngineeringClient only supports feature tables in Unity Catalog. "
                "For feature tables in hive metastore, use databricks.feature_store.FeatureStoreClient."
            )

    def _extract_lineage_info(self) -> Optional[LineageContext]:
        """
        Extract lineage information from the current execution context.

        Returns an LineageContext with notebook_id, job_id, and job_run_id if available.
        Returns None if no lineage information could be extracted.

        :return: LineageContext containing available lineage information, or None.
        """
        notebook_id = None
        job_context = None

        try:
            if databricks_utils.is_in_databricks_notebook():
                notebook_id = int(databricks_utils.get_notebook_id())
        except Exception as e:
            _logger.debug(f"Could not extract notebook_id: {e}")

        try:
            if databricks_utils.is_in_databricks_job():
                job_id = int(databricks_utils.get_job_id())
                job_run_id = int(databricks_utils.get_job_run_id())
                job_context = JobContext(job_id=job_id, job_run_id=job_run_id)
        except Exception as e:
            _logger.debug(f"Could not extract job_id/job_run_id: {e}")

        # Only create LineageContext if we have at least one piece of lineage information
        if notebook_id is not None or job_context is not None:
            return LineageContext(notebook_id=notebook_id, job_context=job_context)

        return None

    @experimental
    def create_feature(
        self,
        *,
        source: DataSource,
        inputs: List[str],
        function: Union[Function, str],
        time_window: Union[TimeWindow, Dict[str, datetime.timedelta]],
        catalog_name: str,
        schema_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ) -> Feature:
        """
        Create a Feature instance with comprehensive validation.

        :param source: Required. The data source for this feature (DeltaTableSource or DataFrameSource)
        :param inputs: Required. List of column names from the source to use as input
        :param function: Required. The aggregation function to apply (Function instance or string name)
        :param time_window: Required. The time window for the aggregation (TimeWindow instance or dict with 'duration' and optional 'offset')
        :param catalog_name: Required. The catalog name for the feature
        :param schema_name: Required. The schema name for the feature
        :param name: Optional name for the feature
        :param description: Optional description of the feature
        :param filter_condition: Optional. SQL WHERE clause to filter source data before aggregation.
                                Example: "amount > 100" or "status = 'completed'"
        :return: A validated Feature instance
        :raises ValueError: If any validation fails
        """
        # Validate mandatory catalog_name and schema_name parameters
        if not isinstance(catalog_name, str) or not catalog_name.strip():
            raise ValueError("'catalog_name' must be a non-empty string")

        if not isinstance(schema_name, str) or not schema_name.strip():
            raise ValueError("'schema_name' must be a non-empty string")

        catalog_name = catalog_name.strip()
        schema_name = schema_name.strip()

        # Validate name parameter constraints
        if name is not None:
            validate_qualified_feature_name(catalog_name, schema_name, name)
            name = name.strip()

        # Validate and convert function parameter
        if isinstance(function, str):
            function = Function.from_string(function)
        elif not isinstance(function, Function):
            raise ValueError(
                f"'function' must be a Function instance or string, got {type(function)}"
            )

        # Validate and convert time_window parameter
        # TODO(ML-59016): Deprecate passing time_window as a dict and use ContinuousWindow, TumblingWindow, or SlidingWindow instead.
        if isinstance(time_window, dict):
            # Validate required 'duration' key
            if "duration" not in time_window:
                raise ValueError(
                    "'time_window' dict must contain a 'duration' key with a datetime.timedelta value"
                )

            duration = time_window["duration"]
            if not isinstance(duration, datetime.timedelta):
                raise ValueError(
                    f"time_window['duration'] must be a datetime.timedelta, got {type(duration)}"
                )

            # Validate optional 'offset' key
            offset = time_window.get("offset")
            if offset is not None and not isinstance(offset, datetime.timedelta):
                raise ValueError(
                    f"time_window['offset'] must be a datetime.timedelta or None, got {type(offset)}"
                )

            # Check for invalid keys
            valid_keys = {"duration", "offset"}
            invalid_keys = set(time_window.keys()) - valid_keys
            if invalid_keys:
                raise ValueError(
                    f"'time_window' dict contains invalid keys: {sorted(invalid_keys)}. "
                    f"Valid keys are: {sorted(valid_keys)}"
                )
            # Create ContinuousWindow instance from dict
            from databricks.ml_features.entities.time_window import ContinuousWindow

            time_window = ContinuousWindow(window_duration=duration, offset=offset)

        elif not isinstance(time_window, TimeWindow):
            raise ValueError(
                f"'time_window' must be a TimeWindow instance or dict, got {type(time_window)}"
            )

        # Validate source type
        if not isinstance(source, DataSource):
            raise ValueError(
                f"'source' must be a DataSource instance, got {type(source)}"
            )

        # Validate inputs
        if not inputs:
            raise ValueError("'inputs' must contain at least one column name")

        if not isinstance(inputs, list):
            raise ValueError(f"'inputs' must be a list, got {type(inputs)}")

        for i, column in enumerate(inputs):
            if not isinstance(column, str) or not column.strip():
                raise ValueError(
                    f"All column names in 'inputs' must be non-empty strings. "
                    f"Invalid column at index {i}: {column}"
                )

        # Validate filter_condition parameter (minimal validation only)
        if filter_condition is not None:
            if not isinstance(filter_condition, str):
                raise ValueError(
                    f"'filter_condition' must be a string or None, got {type(filter_condition)}"
                )

            filter_condition = filter_condition.strip()
            if not filter_condition:
                raise ValueError("'filter_condition' cannot be an empty string")

        # Validation: If source is DeltaTableSource, validate that the table exists
        if isinstance(source, DeltaTableSource):
            table_name = source.full_name()
            if not self._spark_client.table_exists(table_name):
                raise ValueError(f"Delta table '{table_name}' does not exist")

            # Validation: For DeltaTableSource, validate input columns exist in the table
            try:
                table_df = self._spark_client.read_table(table_name)
                table_columns = set(table_df.columns)

                for column in inputs:
                    if column not in table_columns:
                        raise ValueError(
                            f"Column '{column}' does not exist in table '{table_name}'. "
                            f"Available columns: {sorted(table_columns)}"
                        )
            except Exception as e:
                raise ValueError(
                    f"Failed to validate columns in table '{table_name}': {str(e)}"
                )

        # Validation: For DataFrameSource, validate input columns exist in the DataFrame
        elif isinstance(source, DataFrameSource):
            try:
                df_columns = set(source.dataframe.columns)

                for column in inputs:
                    if column not in df_columns:
                        raise ValueError(
                            f"Column '{column}' does not exist in DataFrame. "
                            f"Available columns: {sorted(df_columns)}"
                        )
            except Exception as e:
                raise ValueError(f"Failed to validate columns in DataFrame: {str(e)}")

        # Validation: For KafkaSource, validate relevant columns exist in the Kafka config schemas
        elif isinstance(source, KafkaSource):
            try:
                kafka_config = self.get_kafka_config(name=source.name)
                KafkaSource.validate_columns_exist_in_schemas(
                    source.entity_columns + [source.timeseries_column] + inputs,
                    kafka_config,
                )
            except NotFound:
                raise ValueError(
                    f"Kafka config '{source.name}' does not exist. Create it first using create_kafka_config() before creating features."
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to validate Kafka config '{source.name}': {str(e)}"
                )

        else:
            raise ValueError(
                f"'source' must be a DeltaTableSource, KafkaSource, or DataFrameSource instance, got {type(source)}"
            )

        # Create and return the Feature instance (this will perform additional validations)
        feature = Feature(
            source=source,
            inputs=inputs,
            function=function,
            time_window=time_window,
            description=description,
            catalog_name=catalog_name,
            schema_name=schema_name,
            name=name,
            filter_condition=filter_condition,
        )

        # Persist to Unity Catalog for supported source types
        if isinstance(source, (DeltaTableSource, KafkaSource)):
            sdk_feature = feature._to_sdk_feature()

            lineage_context = self._extract_lineage_info()
            if lineage_context:
                sdk_feature.lineage_context = lineage_context

            sdk_feature_response = (
                self._workspace_client.feature_engineering.create_feature(
                    feature=sdk_feature
                )
            )
            return Feature._from_sdk_feature(sdk_feature_response)
        else:
            _logger.warning(
                "Feature was not saved to Unity Catalog. UC persistence is only supported for DeltaTableSource and KafkaSource."
            )
            return feature

    def get_feature(self, *, full_name: str) -> Feature:
        """Retrieve a feature definition from Unity Catalog."""
        if not isinstance(full_name, str) or not full_name.strip():
            raise ValueError("'full_name' must be a non-empty string")

        sdk_feature = self._workspace_client.feature_engineering.get_feature(
            full_name=full_name.strip()
        )

        return Feature._from_sdk_feature(sdk_feature)

    @experimental
    def delete_feature(self, *, full_name: str) -> None:
        """
        Delete a feature from Unity Catalog.

        :param full_name: The full name of the feature in format
                          '<catalog>.<schema>.<feature_name>'
        """
        self._workspace_client.feature_engineering.delete_feature(full_name=full_name)

    def list_materialized_features(
        self,
        *,
        feature_name: Optional[str] = None,
        max_results: int = 100,
    ) -> List[MaterializedFeature]:
        """
        List materialized features in the user's Unity Catalog metastore.

        :param feature_name: Optional. Filter by feature name. If specified, only materialized features materialized from this feature will be returned.
        :param max_results: The maximum number of features to return across the user's metastore, default is 100. Specifying a high number may result in a long-running operation.
        :return: List of MaterializedFeature instances
        """
        iterator = (
            self._workspace_client.feature_engineering.list_materialized_features(
                feature_name=feature_name
            )
        )

        return list(islice(iterator, max_results))

    def delete_materialized_feature(
        self, *, materialized_feature: MaterializedFeature
    ) -> None:
        """
        Delete a materialized feature

        :param materialized_feature: The materialized feature to delete.
        """
        if (
            materialized_feature is None
            or materialized_feature.materialized_feature_id is None
        ):
            raise ValueError(
                f"Ill-formed object {materialized_feature}. Use `list_materialized_features` API to get the materialized feature for a Unity Catalog feature."
            )

        self._workspace_client.feature_engineering.delete_materialized_feature(
            materialized_feature_id=materialized_feature.materialized_feature_id,
        )

    @experimental
    def grant_feature_serving_permissions(
        self,
        *,
        features: List[Feature],
        users: List[str],
    ) -> None:
        """
        Grant permissions on online tables (materialized feature tables) of the given features to specified users.

        .. note::

            Experimental: This function may change or be removed in
            a future release without warning.

        This function is a temporary solution to address permission gaps when deploying
        models that use materialized features. The person deploying a model may have
        permission on the Feature itself, but not on the online table it is materialized to
        (if they are not the one who materialized the features).

        Eventually calling this API will be unnecessary as the permissions will automatically
        be in place once a long-term permission propagation solution is implemented.

        For each Feature, this method grants:

            - USE_CATALOG on the catalog
            - USE_SCHEMA on the schema
            - SELECT on the online table

        :param features: List of Feature objects to grant online table access for
        :param users: List of user identifiers (e.g., email addresses) to grant permissions to
        :raises Exception: If any validation fails or if any grant fails
        """
        if not features:
            raise ValueError("'features' must be a non-empty list")
        if not users:
            raise ValueError("'users' must be a non-empty list")

        table_name_to_uc_table_info: Dict[str, TableInfo] = {}
        feature_name_to_online_table_name: Dict[str, str] = {}

        # TODO [FS-65]: The current filter implementation in list_materialized_features is inefficient
        # as it does a full scan. We call it once without filter and manually filter
        # to avoid multiple full scans. This will be swapped out when we improve the filter
        # implementation with secondary index.
        feature_names = {feature.full_name for feature in features}
        all_materialized_features = (
            self._workspace_client.feature_engineering.list_materialized_features()
        )

        for mf in all_materialized_features:
            if mf.feature_name not in feature_names:
                continue
            # Safety check: table_name should not be null in normal cases.
            if mf.table_name is None:
                continue

            # fetch UC table info if not already cached
            if mf.table_name not in table_name_to_uc_table_info:
                table_name_to_uc_table_info[
                    mf.table_name
                ] = self._workspace_client.tables.get(full_name=mf.table_name)

            uc_table = table_name_to_uc_table_info[mf.table_name]
            if (
                uc_table.table_type == TableType.FOREIGN
                and uc_table.data_source_format == DataSourceFormat.POSTGRESQL_FORMAT
            ):
                # this is an online materialized feature (Lakebase online table)
                feature_name_to_online_table_name[mf.feature_name] = mf.table_name

        # Validate that we found online materialized tables for every feature
        missing_features = sorted(
            feature_names - set(feature_name_to_online_table_name.keys())
        )
        if missing_features:
            error_msg = (
                "No online materialized feature table found for features: "
                f"{missing_features}"
            )
            _logger.error(error_msg)
            raise ValueError(error_msg)

        # Build reverse maps for permissions
        catalog_name_to_feature_names: Dict[str, List[str]] = {}
        schema_full_name_to_feature_names: Dict[str, List[str]] = {}
        table_name_to_feature_names: Dict[str, List[str]] = {}

        for (
            feature_name,
            online_table_name,
        ) in feature_name_to_online_table_name.items():
            uc_table = table_name_to_uc_table_info[online_table_name]
            catalog_name = uc_table.catalog_name
            schema_name = uc_table.schema_name
            schema_full_name = f"{catalog_name}.{schema_name}"

            if online_table_name not in table_name_to_feature_names:
                table_name_to_feature_names[online_table_name] = []
            table_name_to_feature_names[online_table_name].append(feature_name)

            if catalog_name not in catalog_name_to_feature_names:
                catalog_name_to_feature_names[catalog_name] = []
            catalog_name_to_feature_names[catalog_name].append(feature_name)

            if schema_full_name not in schema_full_name_to_feature_names:
                schema_full_name_to_feature_names[schema_full_name] = []
            schema_full_name_to_feature_names[schema_full_name].append(feature_name)

        _logger.info(
            f"Found {len(table_name_to_feature_names)} online materialized feature table(s) across "
            f"{len(catalog_name_to_feature_names)} catalog(s) and {len(schema_full_name_to_feature_names)} schema(s)"
        )

        # Grant USE CATALOG on each catalog
        for catalog_name in catalog_name_to_feature_names.keys():
            try:
                self._workspace_client.grants.update(
                    securable_type=catalog.SecurableType.CATALOG.value,
                    full_name=catalog_name,
                    changes=[
                        catalog.PermissionsChange(
                            principal=user,
                            add=[catalog.Privilege.USE_CATALOG],
                        )
                        for user in users
                    ],
                )
            except Exception as e:
                catalog_features = catalog_name_to_feature_names.get(catalog_name, [])
                _logger.error(
                    f"Failed to grant USE_CATALOG permission on catalog '{catalog_name}' "
                    f"for features: {catalog_features}: {e}"
                )
                raise

        # Grant USE SCHEMA on each schema
        for schema_full_name in schema_full_name_to_feature_names.keys():
            try:
                self._workspace_client.grants.update(
                    securable_type=catalog.SecurableType.SCHEMA.value,
                    full_name=schema_full_name,
                    changes=[
                        catalog.PermissionsChange(
                            principal=user,
                            add=[catalog.Privilege.USE_SCHEMA],
                        )
                        for user in users
                    ],
                )
            except Exception as e:
                schema_features = schema_full_name_to_feature_names.get(
                    schema_full_name, []
                )
                _logger.error(
                    f"Failed to grant USE_SCHEMA permission on schema '{schema_full_name}' "
                    f"for features: {schema_features}: {e}"
                )
                raise

        # Grant SELECT permission on each online table
        for table_name in table_name_to_feature_names.keys():
            try:
                self._workspace_client.grants.update(
                    securable_type=catalog.SecurableType.TABLE.value,
                    full_name=table_name,
                    changes=[
                        catalog.PermissionsChange(
                            principal=user,
                            add=[catalog.Privilege.SELECT],
                        )
                        for user in users
                    ],
                )
            except Exception as e:
                table_features = table_name_to_feature_names.get(table_name, [])
                _logger.error(
                    f"Failed to grant SELECT permission on table '{table_name}' "
                    f"for features: {table_features}: {e}"
                )
                raise

    def create_feature_serving_endpoint(
        self,
        *,
        name: str = None,
        config: EndpointCoreConfig = None,
        **kwargs,
    ) -> FeatureServingEndpoint:
        """
        Creates a Feature Serving Endpoint

        :param name: The name of the endpoint. Must only contain alphanumerics and dashes.
        :param config: Configuration of the endpoint, including features, workload_size, etc.
        """
        return self._feature_serving_endpoint_client.create_feature_serving_endpoint(
            name=name,
            config=format_endpoint_core_config(config, self._spark_client),
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            **kwargs,
        )

    def create_feature_spec(
        self,
        *,
        name: str,
        features: List[Union[FeatureLookup, FeatureFunction]],
        exclude_columns: Optional[List[str]] = None,
    ) -> FeatureSpecInfo:
        """
        Creates a feature specification in Unity Catalog. The feature spec can be used for serving features & functions.

        :param name: The name of the feature spec.
        :param features: List of FeatureLookups and FeatureFunctions to include in the feature spec.
        :param exclude_columns: List of columns to drop from the final output.
        """
        for feature in features:
            if type(feature) == FeatureLookup:
                self._validate_is_uc_table_name(feature.table_name)

        name = uc_utils.get_full_udf_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )

        if exclude_columns is None:
            exclude_columns = []

        features = format_feature_lookups_and_functions(self._spark_client, features)

        return self._training_scoring_client.create_feature_spec(
            name=name,
            features=features,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            exclude_columns=exclude_columns,
        )

    def update_feature_spec(self, *, name: str, owner: str) -> None:
        """
        Update the owner of a feature spec.

        :param name: The name of the feature spec.
        :param owner: The new owner of the feature spec.
        """
        if not name:
            raise ValueError("FeatureSpec name must be provided.")
        if not owner:
            raise ValueError("owner must be provided.")

        name = uc_utils.get_full_udf_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )

        req_context = RequestContext(
            request_context.UPDATE_FEATURE_SPEC,
            request_context.FEATURE_ENGINEERING_CLIENT,
        )
        self._catalog_client.update_feature_spec(
            name=name, owner=owner, req_context=req_context
        )

    def delete_feature_spec(self, *, name: str) -> None:
        """
        Delete a feature spec.

        :param name: The name of the feature spec.
        """
        if not name:
            raise ValueError("FeatureSpec name must be provided.")
        name = uc_utils.get_full_udf_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        req_context = RequestContext(
            request_context.DELETE_FEATURE_SPEC,
            request_context.FEATURE_ENGINEERING_CLIENT,
        )
        self._catalog_client.delete_feature_spec(name=name, req_context=req_context)

    def create_table(
        self,
        *,
        name: str,
        primary_keys: Union[str, List[str]],
        df: Optional[DataFrame] = None,
        timeseries_column: Optional[str] = None,
        partition_columns: Union[str, List[str], None] = None,
        schema: Optional[StructType] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> FeatureTable:
        """
        Create and return a feature table with the given name and primary keys.

        The returned feature table has the given name and primary keys.
        Uses the provided ``schema`` or the inferred schema
        of the provided ``df``. If ``df`` is provided, this data will be saved in
        a Delta table. Supported data types for features are: ``IntegerType``, ``LongType``,
        ``FloatType``, ``DoubleType``, ``StringType``, ``BooleanType``, ``DateType``,
        ``TimestampType``, ``ShortType``, ``ArrayType``, ``MapType``, and ``BinaryType``,
        ``DecimalType``, and ``StructType``.

        :param name: A feature table name. The format is ``<catalog_name>.<schema_name>.<table_name>``, for example ``ml.dev.user_features``.
        :param primary_keys: The feature table's primary keys. If multiple columns are required,
          specify a list of column names, for example ``['customer_id', 'region']``.
        :param df: Data to insert into this feature table. The schema of
          ``df`` will be used as the feature table schema.
        :param timeseries_column: Column containing the event time associated with feature value.
          Timeseries column should be part of the primary keys.
          Combined, the timeseries column and other primary keys of the feature table uniquely identify the feature value
          for an entity at a point in time.
        :param partition_columns: Columns used to partition the feature table. If a list is
          provided, column ordering in the list will be used for partitioning.

          .. Note:: When choosing partition columns for your feature table, use columns that do
                    not have a high cardinality. An ideal strategy would be such that you
                    expect data in each partition to be at least 1 GB.
                    The most commonly used partition column is a ``date``.

                    Additional info: `Choosing the right partition columns for Delta tables
                    <https://bit.ly/3ueXsjv>`_
        :param schema: Feature table schema. Either ``schema`` or ``df`` must be provided.
        :param description: Description of the feature table.
        :param tags: Tags to associate with the feature table.
        """
        self._validate_is_uc_table_name(name)

        if timeseries_column is None:
            if "timestamp_keys" in kwargs:
                timeseries_column = kwargs.pop("timestamp_keys")
            if "timeseries_columns" in kwargs:
                timeseries_column = kwargs.pop("timeseries_columns")
            if type(timeseries_column) is list:
                if len(timeseries_column) == 1:
                    timeseries_column = timeseries_column[0]
                elif len(timeseries_column) == 0:
                    timeseries_column = None
                else:
                    raise ValueError(
                        "Setting multiple timeseries keys is not supported."
                    )

        primary_keys_as_list = as_list(primary_keys, default=[])
        if (
            timeseries_column is not None
            and timeseries_column not in primary_keys_as_list
        ):
            raise ValueError(
                f"Timeseries column '{timeseries_column}' is not in primary_keys. "
                f"Timeseries columns must be primary keys."
            )

        name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )

        return self._compute_client.create_table(
            name=name,
            primary_keys=primary_keys,
            df=df,
            timestamp_keys=as_list(timeseries_column, default=[]),
            partition_columns=partition_columns,
            schema=schema,
            description=description,
            tags=tags,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            **kwargs,
        )

    def create_training_set(
        self,
        *,
        df: DataFrame,
        feature_lookups: Optional[List[Union[FeatureLookup, FeatureFunction]]] = None,
        feature_spec: Optional[str] = None,
        features: Optional[List[Feature]] = None,
        label: Union[str, List[str], None],
        exclude_columns: Optional[List[str]] = None,
        use_spark_native_join: bool = False,
        **kwargs,
    ) -> TrainingSet:
        """
        Create a :class:`TrainingSet <databricks.ml_features.training_set.TrainingSet>` using feature_lookups, feature_spec, or features.

        :param df: The :class:`DataFrame <pyspark.sql.DataFrame>` used to join features into.
        :param feature_lookups: List of features to use in the :class:`TrainingSet <databricks.ml_features.training_set.TrainingSet>`.
          :class:`FeatureLookups <databricks.ml_features.entities.feature_lookup.FeatureLookup>` are
          joined into the :class:`DataFrame <pyspark.sql.DataFrame>`, and
          :class:`FeatureFunctions <databricks.ml_features.entities.feature_function.FeatureFunction>` are
          computed on-demand. `feature_lookups` cannot be specified if `feature_spec` or `features` is provided.
        :param feature_spec: Full name of the FeatureSpec in Unity Catalog. `feature_spec` cannot be specified if `feature_lookups` or `features` is provided.
        :param features: List of :class:`Feature <databricks.ml_features.entities.feature.Feature>` objects to use in the training set.
          `features` cannot be specified if `feature_lookups` or `feature_spec` is provided.
        :param label: Names of column(s) in :class:`DataFrame <pyspark.sql.DataFrame>` that contain training set labels. To create a training set without a label field, i.e. for unsupervised training set, specify label = None.
        :param exclude_columns: Names of the columns to drop from the :class:`TrainingSet <databricks.ml_features.training_set.TrainingSet>` :class:`DataFrame <pyspark.sql.DataFrame>`.
        :param use_spark_native_join: Use spark to optimize table joining performance. The optimization is only applicable when `Photon <https://docs.databricks.com/en/compute/photon.html>` is enabled.
        :return: A :class:`TrainingSet <databricks.ml_features.training_set.TrainingSet>` object.
        """

        if exclude_columns is None:
            exclude_columns = []

        # Validate that exactly one of the three feature specification methods is provided
        provided_options = [
            feature_lookups is not None,
            feature_spec is not None,
            features is not None,
        ]
        num_provided = sum(provided_options)

        if num_provided == 0:
            raise ValueError(
                "One of 'feature_lookups', 'feature_spec', or 'features' must be provided."
            )
        elif num_provided > 1:
            raise ValueError(
                "Only one of 'feature_lookups', 'feature_spec', or 'features' can be provided."
            )

        # Route to appropriate implementation based on provided parameter
        if feature_spec is not None:
            return self._create_training_set_from_feature_spec(
                df=df,
                feature_spec=feature_spec,
                label=label,
                exclude_columns=exclude_columns,
                use_spark_native_join=use_spark_native_join,
                **kwargs,
            )
        elif feature_lookups is not None:
            return self._create_training_set_from_feature_lookups(
                df=df,
                feature_lookups=feature_lookups,
                label=label,
                exclude_columns=exclude_columns,
                use_spark_native_join=use_spark_native_join,
                **kwargs,
            )
        else:  # features is not None
            # Validates that declarative features are enabled. Throws if not enabled.
            self._catalog_client.validate_declarative_features_enabled(
                feature_spec_yaml=None,
                req_context=RequestContext(
                    request_context.CREATE_TRAINING_SET,
                    request_context.FEATURE_ENGINEERING_CLIENT,
                ),
            )
            return self._create_training_set_from_features(
                df=df,
                features=features,
                label=label,
                exclude_columns=exclude_columns,
                use_spark_native_join=use_spark_native_join,
                **kwargs,
            )

    def _create_training_set_from_feature_spec(
        self,
        *,
        df: DataFrame,
        feature_spec: str,
        label: Union[str, List[str], None],
        exclude_columns: List[str],
        use_spark_native_join: bool,
        **kwargs,
    ) -> TrainingSet:
        """Create training set from a feature spec."""
        if not isinstance(feature_spec, str):
            raise TypeError("'feature_spec' must be a string.")

        feature_spec_name = uc_utils.get_full_table_name(
            feature_spec,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        self._databricks_client.verify_feature_spec_in_uc(feature_spec_name)
        return self._training_scoring_client.create_training_set_from_feature_spec(
            df=df,
            feature_spec_name=feature_spec,
            label=label,
            exclude_columns=exclude_columns,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            use_spark_native_join=use_spark_native_join,
            **kwargs,
        )

    def _create_training_set_from_feature_lookups(
        self,
        *,
        df: DataFrame,
        feature_lookups: List[Union[FeatureLookup, FeatureFunction]],
        label: Union[str, List[str], None],
        exclude_columns: List[str],
        use_spark_native_join: bool,
        **kwargs,
    ) -> TrainingSet:
        """Create training set from feature lookups."""
        if not isinstance(feature_lookups, list):
            raise TypeError("'feature_lookups' must be a list.")

        # Feature_lookups may contain either FeatureLookup or FeatureFunctions.
        # https://docs.google.com/document/d/1cExSgaf6l_U6txWB5Qaf3EjYt2m1PPNciFyhFT3zd5s/edit#heading=h.39s4jy5qc7u
        for i, item in enumerate(feature_lookups):
            if not isinstance(item, (FeatureLookup, FeatureFunction)):
                raise TypeError(
                    f"'feature_lookups[{i}]' must be a FeatureLookup or FeatureFunction."
                )

        for feature_lookup in feature_lookups:
            if type(feature_lookup) == FeatureLookup:
                self._validate_is_uc_table_name(feature_lookup.table_name)

        formatted_features = format_feature_lookups_and_functions(
            self._spark_client, feature_lookups
        )

        return self._training_scoring_client.create_training_set_from_feature_lookups(
            df=df,
            feature_lookups=formatted_features,
            label=label,
            exclude_columns=exclude_columns,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            use_spark_native_join=use_spark_native_join,
            **kwargs,
        )

    def _create_training_set_from_features(
        self,
        *,
        df: DataFrame,
        features: List[Feature],
        label: Union[str, List[str], None],
        exclude_columns: List[str],
        use_spark_native_join: bool,
        **kwargs,
    ) -> TrainingSet:
        """Create training set from Feature objects.

        Performs point-in-time (as-of) joins between the provided labeled
        ``df`` and the computed feature DataFrames for each underlying
        Delta table source referenced by the provided ``features``.
        """
        # Validate features list and element type
        if not isinstance(features, list):
            raise TypeError("'features' must be a list.")
        for i, item in enumerate(features):
            if not isinstance(item, Feature):
                raise TypeError(f"'features[{i}]' must be a Feature.")

        # Validate all feature sources are Delta tables and required keys exist in df
        df_columns = set(df.columns)
        for i, feature in enumerate(features):
            if not isinstance(feature.source, DeltaTableSource):
                raise ValueError(
                    "All features must reference a DeltaTableSource. "
                    f"Found type '{type(feature.source)}' at features[{i}]."
                )
            missing_pk = [
                pk for pk in feature.source.entity_columns if pk not in df_columns
            ]
            if missing_pk:
                raise ValueError(
                    "Training DataFrame is missing primary key columns required "
                    f"for join: {missing_pk}"
                )
            if feature.source.timeseries_column not in df_columns:
                raise ValueError(
                    "Training DataFrame is missing timestamp key required for join: "
                    f"{feature.source.timeseries_column}"
                )

        return self._training_scoring_client.create_training_set_from_features(
            df=df,
            features=features,
            label=label,
            exclude_columns=exclude_columns,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            use_spark_native_join=use_spark_native_join,
            **kwargs,
        )

    def delete_feature_serving_endpoint(self, *, name=None, **kwargs) -> None:
        legacy_endpoint_name = kwargs.get("endpoint_name")
        name = format_feature_serving_endpoint_name(name, legacy_endpoint_name, _logger)
        self._feature_serving_endpoint_client.delete_feature_serving_endpoint(name=name)

    def delete_feature_table_tag(self, *, name: str, key: str) -> None:
        """
        Delete the tag associated with the feature table. Deleting a non-existent tag will emit a warning.

        :param name: the feature table name.
        :param key: the tag key to delete.
        """
        self._validate_is_uc_table_name(name)
        table_name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        self._compute_client.delete_feature_table_tag(
            table_name=table_name,
            key=key,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
        )

    def drop_online_table(
        self,
        name: str,
        online_store: OnlineStoreSpec,
    ) -> None:
        """
        Drop a table in an online store.

        This API first attempts to make a call to the online store provider to drop the table.
        If successful, it then deletes the online store from the feature catalog.

        :param name: Name of feature table associated with online store table to drop.
        :param online_store: Specification of the online store.

        .. note::
            Deleting an online published table can lead to unexpected failures in downstream
            dependencies. Ensure that the online table being dropped is no longer used for
            Model Serving feature lookup or any other use cases.
        """

        # Temporarily block dropping databricks online tables before it's supported.
        if isinstance(online_store, DatabricksOnlineStore):
            raise ValueError("Dropping Databricks online tables is not supported.")

        self._validate_is_uc_table_name(name)
        feature_table_name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )

        return self._publish_client._drop_online_table(
            feature_table_name=feature_table_name,
            online_store=online_store,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
        )

    def drop_table(self, *, name: str) -> None:
        """
        Delete the specified feature table. This API also drops the underlying Delta table.

        :param name: A feature table name. The format is ``<catalog_name>.<schema_name>.<table_name>``, for example ``ml.dev.user_features``.

        .. note::
            Deleting a feature table can lead to unexpected failures in  upstream producers and
            downstream consumers (models, endpoints, and scheduled jobs). You must delete any existing
            published online stores separately.
        """
        self._validate_is_uc_table_name(name)
        name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        self._compute_client.drop_table(
            name=name, client_name=request_context.FEATURE_ENGINEERING_CLIENT
        )

    def get_feature_serving_endpoint(
        self, *, name=None, **kwargs
    ) -> FeatureServingEndpoint:
        legacy_endpoint_name = kwargs.get("endpoint_name")
        name = format_feature_serving_endpoint_name(name, legacy_endpoint_name, _logger)
        return self._feature_serving_endpoint_client.get_feature_serving_endpoint(
            name=name
        )

    def get_table(self, *, name: str) -> FeatureTable:
        """
        Get a feature table's metadata.

        :param name: A feature table name. The format is ``<catalog_name>.<schema_name>.<table_name>``, for example ``ml.dev.user_features``.
        """
        self._validate_is_uc_table_name(name)
        name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        return self._compute_client.get_table(
            name=name,
            req_context=RequestContext(
                request_context.GET_TABLE, request_context.FEATURE_ENGINEERING_CLIENT
            ),
        )

    def log_model(
        self,
        *,
        model: Any,
        artifact_path: str,
        flavor: ModuleType,
        training_set: Optional[TrainingSet] = None,
        registered_model_name: Optional[str] = None,
        await_registration_for: int = mlflow.tracking._model_registry.DEFAULT_AWAIT_MAX_SLEEP_SECONDS,
        infer_input_example: bool = False,
        **kwargs,
    ):
        """
        Log an MLflow model packaged with feature lookup information.

        .. note::

           The :class:`DataFrame <pyspark.sql.DataFrame>` returned
           by :meth:`.TrainingSet.load_df` **must** be used to train the
           model. If it has been modified (for example data normalization, add a column,
           and similar), these modifications will not be applied at inference time,
           leading to training-serving skew.


        :param model: Model to be saved. This model must be capable of being saved by
          ``flavor.save_model``. See the `MLflow Model API
          <https://bit.ly/3yzl1r0>`_.
        :param artifact_path: Run-relative artifact path.
        :param flavor: MLflow module to use to log the model. ``flavor`` should have
          type :obj:`ModuleType <types.ModuleType>`.
          The module must have a method ``save_model``, and must support the ``python_function``
          flavor. For example, :mod:`mlflow.sklearn`, :mod:`mlflow.xgboost`, and similar.
        :param training_set: The :class:`.TrainingSet` used to train this model.
        :param registered_model_name:
          When provided, create a model version under ``registered_model_name``,
          also creating a registered model if one with the given name does not exist.
        :param await_registration_for: Number of seconds to wait for the model version to finish
          being created and is in ``READY`` status. By default, the function waits for five minutes.
          Specify ``0`` or :obj:`None` to skip waiting.
        :param infer_input_example:

          .. note::

             Experimental: This argument may change or be removed in a future release without warning.

          Automatically log an input example along with the model, using supplied training data.
          Defaults to ``False``.
        :kwargs: If other keyword arguments are provided, in most cases, they are passed to the underlying
          MLflow API flavor.save_model() when saving and registering the model.

          .. note::
            - ``signature`` is not recommended and it's preferred to use ``infer_input_example``.
            - ``output_schema``: When logging a model without labels in the training set, you must pass ``output_schema`` to ``log_model`` to suggest the output schema explicitly. For example:

                .. code-block:: python

                    from mlflow.types import ColSpec, DataType, Schema

                    output_schema = Schema([ColSpec(DataType.???)]) # Refer to mlflow signature types for the right choice of type here
                    ...
                    fe.log_model(
                        ...
                        output_schema=output_schema
                    )


        :return: `None`
        """
        if training_set is not None:
            if isinstance(training_set, TrainingSetWithDeclarativeFeatures):
                # Validates that declarative features are enabled. Throws if not enabled.
                self._catalog_client.validate_declarative_features_enabled(
                    feature_spec_yaml=yaml.dump(
                        training_set.feature_spec._to_dict(), sort_keys=False
                    ),
                    req_context=RequestContext(
                        request_context.LOG_MODEL,
                        request_context.FEATURE_ENGINEERING_CLIENT,
                    ),
                )
                # For declarative features, validate the DeltaTableSource table names
                for feature in training_set.features:
                    if not isinstance(feature.source, DeltaTableSource):
                        raise ValueError(
                            f"All features must reference a DeltaTableSource. "
                            f"Found type '{type(feature.source)}' for feature '{feature.name}'."
                        )
                    self._validate_is_uc_table_name(feature.source.full_name())
            else:
                # Regular TrainingSet flow - validate feature_spec table_infos
                feature_spec = training_set.feature_spec
                table_infos = feature_spec.table_infos
                for table_info in table_infos:
                    self._validate_is_uc_table_name(table_info.table_name)

        return self._training_scoring_client.log_model(
            model=model,
            artifact_path=artifact_path,
            flavor=flavor,
            training_set=training_set,
            registered_model_name=registered_model_name,
            await_registration_for=await_registration_for,
            infer_input_example=infer_input_example,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            **kwargs,
        )

    def publish_table(
        self,
        *,
        online_store: Union[OnlineStoreSpec, DatabricksOnlineStore],
        source_table_name: str = None,
        online_table_name: str = None,
        publish_mode: str = PUBLISH_MODE_TRIGGERED,
        filter_condition: Optional[str] = None,
        mode: str = MERGE,
        streaming: bool = False,
        checkpoint_location: Optional[str] = None,
        trigger: Dict[str, Any] = _DEFAULT_PUBLISH_STREAM_TRIGGER,
        features: Union[str, List[str], None] = None,
        **kwargs,
    ) -> Optional[StreamingQuery | PublishedTable]:
        """
        Publish a feature table to an online store.

        :param source_table_name: Name of the feature table. This is a required parameter.
        :param online_table_name: Name of the online table. This is a required parameter when publishing to Databricks Online Store.
        :param online_store: Specification of the online store. This is a required parameter.
        :param publish_mode: supported modes are ``"SNAPSHOT"``, ``"CONTINUOUS"``, and ``"TRIGGERED"``. Default is ``"TRIGGERED"``.

        .. Note:: Change Data Feed (CDF) must be enabled for CONTINUOUS and TRIGGERED modes.

        Legacy parameters. The following parameters are only used by third party online stores.
        ------------------
        :param filter_condition: A SQL expression using feature table columns that filters feature
          rows prior to publishing to the online store. For example, ``"dt > '2020-09-10'"``. This
          is analogous to running ``df.filter`` or a ``WHERE`` condition in SQL on a feature table
          prior to publishing.
        :param mode: Specifies the behavior when data already exists in this feature
          table. The only supported mode is ``"merge"``, with which the new data will be
          merged in, under these conditions:

          * If a key exists in the online table but not the offline table,
            the row in the online table is unmodified.

          * If a key exists in the offline table but not the online table,
            the offline table row is inserted into the online table.

          * If a key exists in both the offline and the online tables,
            the online table row will be updated.

        :param streaming: If ``True``, streams data to the online store.
        :param checkpoint_location: Sets the Structured Streaming ``checkpointLocation`` option.
          By setting a ``checkpoint_location``, Spark Structured Streaming will store
          progress information and intermediate state, enabling recovery after failures.
          This parameter is only supported when ``streaming=True``.
        :param trigger: If ``streaming=True``, ``trigger`` defines the timing of
          stream data processing. The dictionary will be unpacked and passed
          to :meth:`DataStreamWriter.trigger <pyspark.sql.streaming.DataStreamWriter.trigger>` as arguments. For example, ``trigger={'once': True}``
          will result in a call to ``DataStreamWriter.trigger(once=True)``.
        :param features: Specifies the feature column(s) to be published to the online store.
          The selected features must be a superset of existing online store features. Primary key columns
          and timestamp key columns will always be published.

          .. Note:: When ``features`` is not set, the whole feature table will be published.


        :return: If ``streaming=True``, returns a PySpark :class:`StreamingQuery <pyspark.sql.streaming.StreamingQuery>`, :obj:`None` otherwise.
        """

        # prefer argument `source_table_name` over `name`. Continue to support `name` for backwards compatibility.
        if source_table_name is None:
            if "name" in kwargs:
                # ToDo: Add deprecation warning for `name` parameter
                source_table_name = kwargs["name"]
            else:
                raise ValueError("source_table_name is required")

        self._validate_is_uc_table_name(source_table_name)

        if mode != MERGE:
            raise ValueError(
                f"Unsupported mode '{mode}'. '{MERGE}' is the only supported mode."
            )

        source_table_name = uc_utils.get_full_table_name(
            source_table_name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )

        if isinstance(online_store, DatabricksOnlineStore):
            if online_table_name is None:
                raise ValueError(
                    "online_table_name is required for Databricks online store"
                )
            if not uc_utils._is_three_level_name(online_table_name):
                raise ValueError(
                    f"Online table name '{online_table_name}' is not valid. Expected format '<catalog_name>.<schema_name>.<table_name>'"
                )
            if filter_condition is not None:
                raise ValueError(
                    "filter_condition can not be set for Databricks online store"
                )
            if checkpoint_location is not None:
                raise ValueError(
                    "checkpoint_location can not be set for Databricks online store"
                )
            if mode != MERGE:
                raise ValueError(
                    f"only '{MERGE}' mode is supported for Databricks online store"
                )
            if streaming:
                # handle backward compatibility
                if publish_mode == PUBLISH_MODE_TRIGGERED:
                    # TRIGGERED is the default value which should be allowed for backward compatibility
                    _logger.warning(
                        'streaming=True is deprecated, please use publish_mode="CONTINUOUS" instead. Publishing in CONTINUOUS mode.'
                    )
                    publish_mode = PUBLISH_MODE_CONTINUOUS
                elif publish_mode == PUBLISH_MODE_CONTINUOUS:
                    # consistent parameters
                    pass
                else:
                    raise ValueError(
                        f"streaming=True is not supported for publish_mode={publish_mode}"
                    )
            if trigger != _DEFAULT_PUBLISH_STREAM_TRIGGER:
                raise ValueError("trigger can not be set for Databricks online store")
            if features is not None:
                raise ValueError("features can not be set for Databricks online store")
            return self._publish_client._publish_databricks_table(
                source_table_name=source_table_name,
                online_table_name=online_table_name,
                online_store=online_store,
                publish_mode=publish_mode,
            )
        else:
            if is_rdbms_spec(online_store):
                raise ValueError(
                    f"Unsupported online store '{online_store}'. Use one of {NOSQL_SPECS}."
                )
            if online_table_name:
                raise ValueError(
                    f"online_table_name not supported for online store type {online_store.store_type}"
                )

            return self._publish_client._publish_table(
                name=source_table_name,
                online_store=online_store,
                filter_condition=filter_condition,
                mode=mode,
                streaming=streaming,
                checkpoint_location=checkpoint_location,
                trigger=trigger,
                features=features,
                client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            )

    def read_table(self, *, name: str, **kwargs) -> DataFrame:
        """
        Read the contents of a feature table.

        :param name: A feature table name. The format is ``<catalog_name>.<schema_name>.<table_name>``, for example ``ml.dev.user_features``.
        :return: The feature table contents, or an exception will be raised if this feature table does not
          exist.
        """
        self._validate_is_uc_table_name(name)
        name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        return self._compute_client.read_table(
            name=name, client_name=request_context.FEATURE_ENGINEERING_CLIENT, **kwargs
        )

    def score_batch(
        self,
        *,
        model_uri: str,
        df: DataFrame,
        result_type: str = "double",
        env_manager: str = LOCAL,
        params: Optional[dict[str, Any]] = None,
        use_spark_native_join: bool = False,
        **kwargs,
    ) -> DataFrame:
        """
        Evaluate the model on the provided :class:`DataFrame <pyspark.sql.DataFrame>`.

        Additional features required for
        model evaluation will be automatically retrieved from feature tables.

        .. todo::

           [ML-15539]: Replace the bitly URL in doc string

        The model must have been logged with :meth:`.FeatureEngineeringClient.log_model`,
        which packages the model with feature metadata. Unless present in ``df``,
        these features will be looked up from feature tables and joined with ``df``
        prior to scoring the model.

        If a feature is included in ``df``, the provided feature values will be used rather
        than those stored in feature tables.

        For example, if a model is trained on two features ``account_creation_date`` and
        ``num_lifetime_purchases``, as in:

        .. code-block:: python

            feature_lookups = [
                FeatureLookup(
                    table_name = 'trust_and_safety.customer_features',
                    feature_name = 'account_creation_date',
                    lookup_key = 'customer_id',
                ),
                FeatureLookup(
                    table_name = 'trust_and_safety.customer_features',
                    feature_name = 'num_lifetime_purchases',
                    lookup_key = 'customer_id'
                ),
            ]

            with mlflow.start_run():
                training_set = fe.create_training_set(
                    df,
                    feature_lookups = feature_lookups,
                    label = 'is_banned',
                    exclude_columns = ['customer_id']
                )
                ...
                  fe.log_model(
                    model,
                    "model",
                    flavor=mlflow.sklearn,
                    training_set=training_set,
                    registered_model_name="example_model"
                  )

        Then at inference time, the caller of :meth:`FeatureEngineeringClient.score_batch` must pass
        a :class:`DataFrame <pyspark.sql.DataFrame>` that includes ``customer_id``, the ``lookup_key`` specified in the
        ``FeatureLookups`` of the :mod:`training_set <databricks.feature_engineering.training_set>`.
        If the :class:`DataFrame <pyspark.sql.DataFrame>` contains a column
        ``account_creation_date``, the values of this column will be used
        in lieu of those in feature tables. As in:

        .. code-block:: python

            # batch_df has columns ['customer_id', 'account_creation_date']
            predictions = fe.score_batch(
                'models:/example_model/1',
                batch_df
            )

        :param model_uri: The location, in URI format, of the MLflow model logged using
          :meth:`FeatureEngineeringClient.log_model`. One of:

            * ``runs:/<mlflow_run_id>/run-relative/path/to/model``

            * ``models:/<model_name>/<model_version>``

            * ``models:/<model_name>/<stage>``

          For more information about URI schemes, see
          `Referencing Artifacts <https://bit.ly/3wnrseE>`_.
        :param df: The :class:`DataFrame <pyspark.sql.DataFrame>` to score the model on. Features from feature tables will be joined with
          ``df`` prior to scoring the model. ``df`` must:

              1. Contain columns for lookup keys required to join feature data from feature
              tables, as specified in the ``feature_spec.yaml`` artifact.

              2. Contain columns for all source keys required to score the model, as specified in
              the ``feature_spec.yaml`` artifact.

              3. Not contain a column ``prediction``, which is reserved for the model's predictions.
              ``df`` may contain additional columns.

          Streaming DataFrames are not supported.

        :param result_type: The return type of the model.
           See :func:`mlflow.pyfunc.spark_udf` result_type.
        :param env_manager: The environment manager to use in order to create the python environment for model inference.
           See :func:`mlflow.pyfunc.spark_udf` env_manager.
        :param params: Additional parameters to pass to the model for inference.
        :param use_spark_native_join: Use spark to optimize table joining performance. The optimization is only applicable when `Photon <https://docs.databricks.com/en/compute/photon.html>` is enabled.
        :return: A :class:`DataFrame <pyspark.sql.DataFrame>`
           containing:

            1. All columns of ``df``.

            2. All feature values retrieved from feature tables.

            3. A column ``prediction`` containing the output of the model.

        """
        return self._training_scoring_client.score_batch(
            model_uri=model_uri,
            df=df,
            result_type=result_type,
            env_manager=env_manager,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
            params=params,
            use_spark_native_join=use_spark_native_join,
            **kwargs,
        )

    def set_feature_table_tag(self, *, name: str, key: str, value: str) -> None:
        """
        Create or update a tag associated with the feature table. If the tag with the
        corresponding key already exists, its value will be overwritten with the new value.

        :param name: the feature table name
        :param key: tag key
        :param value: tag value
        """
        self._validate_is_uc_table_name(name)
        table_name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        self._compute_client.set_feature_table_tag(
            table_name=table_name,
            key=key,
            value=value,
            client_name=request_context.FEATURE_ENGINEERING_CLIENT,
        )

    def write_table(
        self,
        *,
        name: str,
        df: DataFrame,
        mode: str = MERGE,
        checkpoint_location: Optional[str] = None,
        trigger: Dict[str, Any] = _DEFAULT_WRITE_STREAM_TRIGGER,
    ) -> Optional[StreamingQuery]:
        """
        Writes to a feature table.

        If the input :class:`DataFrame <pyspark.sql.DataFrame>` is streaming, will create a write stream.

        :param name: A feature table name. The format is ``<catalog_name>.<schema_name>.<table_name>``, for example ``ml.dev.user_features``.
        :param df: Spark :class:`DataFrame <pyspark.sql.DataFrame>` with feature data. Raises an exception if the schema does not
          match that of the feature table.
        :param mode: There is only one supported write mode:

          * ``"merge"`` upserts the rows in ``df`` into the feature table. If ``df`` contains
            columns not present in the feature table, these columns will be added as new features.

          If you want to overwrite a table, run SQL ``DELETE FROM <table name>;`` to delete all rows, or drop and recreate the table before calling this method.

        :param checkpoint_location: Sets the Structured Streaming ``checkpointLocation`` option.
          By setting a ``checkpoint_location``, Spark Structured Streaming will store
          progress information and intermediate state, enabling recovery after failures.
          This parameter is only supported when the argument ``df`` is a streaming :class:`DataFrame <pyspark.sql.DataFrame>`.
        :param trigger: If ``df.isStreaming``, ``trigger`` defines the timing of stream data
          processing, the dictionary will be unpacked and passed to :meth:`DataStreamWriter.trigger <pyspark.sql.streaming.DataStreamWriter.trigger>`
          as arguments. For example, ``trigger={'once': True}`` will result in a call to
          ``DataStreamWriter.trigger(once=True)``.
        :return: If ``df.isStreaming``, returns a PySpark :class:`StreamingQuery <pyspark.sql.streaming.StreamingQuery>`. :obj:`None` otherwise.
        """
        self._validate_is_uc_table_name(name)

        if mode != MERGE:
            raise ValueError(
                f"Unsupported mode '{mode}'. '{MERGE}' is the only supported mode. If you want to overwrite a table, run SQL 'DELETE FROM <table name>;' to delete all rows, or drop and recreate the table before calling this method."
            )

        name = uc_utils.get_full_table_name(
            name,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        return self._compute_client.write_table(
            name=name,
            df=df,
            mode=mode,
            checkpoint_location=checkpoint_location,
            trigger=trigger,
            producer_action=ProducerAction.WRITE,
            req_context=RequestContext(
                request_context.WRITE_TABLE, request_context.FEATURE_ENGINEERING_CLIENT
            ),
        )

    def compute_features(
        self,
        features: List[Feature],
    ) -> DataFrame:
        """
        Computes the specified features and returns a DataFrame containing the results.

        Note: This method only supports computing features from a single source.

        :param features: The features to compute.
        """
        # Validate input
        if not features:
            raise ValueError(
                "The 'features' parameter should contain at least 1 feature to be computed."
            )

        # Validates that declarative features are enabled. Throws if not enabled.
        self._catalog_client.validate_declarative_features_enabled(
            feature_spec_yaml=None,
            req_context=RequestContext(
                request_context.COMPUTE_FEATURES,
                request_context.FEATURE_ENGINEERING_CLIENT,
            ),
        )

        source_to_features = self._materialization_client.compute_features(
            features=features,
            allow_multiple_sources=False,
        )
        return next(iter(source_to_features.values()), None)

    @enable_if(lambda: flags.ENABLE_EXPERIMENTAL_MATERIALIZATION_API)
    def aggregate_features(self, *, features: FeatureAggregations) -> DataFrame:
        """
        Computes the specified aggregations and returns a DataFrame containing the results.

        :param features: The aggregation specification to compute.
        """
        self._catalog_client.log_client_event(
            event="aggregate_features",
            payload=LogClientEvent.AggregateFeatures(
                aggregation_info=features.to_aggregation_info(),
            ),
            req_context=RequestContext(
                request_context.LOG_CLIENT_EVENT,
                request_context.FEATURE_ENGINEERING_CLIENT,
            ),
        )
        features = features.copy(
            source_table=uc_utils.get_full_table_name(
                features.source_table,
                self._spark_client.get_current_catalog(),
                self._spark_client.get_current_database(),
            )
        )
        assert uc_utils.is_uc_entity(
            features.source_table
        ), "Source table name must be a Unity Catalog entity."

        return self._materialization_client.aggregate_features(features=features)

    @enable_if(lambda: flags.ENABLE_EXPERIMENTAL_MATERIALIZATION_API)
    def create_materialized_view(
        self,
        *,
        features: FeatureAggregations,
        output_table: str,
        schedule: Optional[CronSchedule],
    ) -> MaterializedViewInfo:
        """
        Creates and runs a pipeline that materializes the given feature aggregation specification into a materialized view.

        :param features: The aggregation specification to materialize.
        :param output_table: The name of the output materialized view.
        :param schedule: The schedule at which to run the materialization pipeline. If not provided, the pipeline can only be run manually.
        """

        # This is a pre-flight check to ensure that the materialized view API is enabled in the backend.
        # Since payload is empty, nothing is logged to the backend.
        self._catalog_client.log_client_event(
            event="create_materialized_view",
            payload=LogClientEvent.CreateMaterializedView(),
            req_context=RequestContext(
                request_context.LOG_CLIENT_EVENT,
                request_context.FEATURE_ENGINEERING_CLIENT,
            ),
        )

        output_table = uc_utils.get_full_table_name(
            output_table,
            self._spark_client.get_current_catalog(),
            self._spark_client.get_current_database(),
        )
        features = features.copy(
            source_table=uc_utils.get_full_table_name(
                features.source_table,
                self._spark_client.get_current_catalog(),
                self._spark_client.get_current_database(),
            )
        )

        assert uc_utils.is_uc_entity(
            features.source_table
        ), "Source table name must be a Unity Catalog entity."
        assert uc_utils.is_uc_entity(
            output_table
        ), "Target materialized view name must be a Unity Catalog entity."

        materialized_view_info = self._materialization_client.create_materialized_view(
            features=features,
            output_table=output_table,
            schedule=schedule,
        )

        self._catalog_client.log_client_event(
            event="create_materialized_view",
            payload=LogClientEvent.CreateMaterializedView(
                pipeline_id=materialized_view_info.pipeline_id,
                aggregation_info=features.to_aggregation_info(),
            ),
            req_context=RequestContext(
                request_context.LOG_CLIENT_EVENT,
                request_context.FEATURE_ENGINEERING_CLIENT,
            ),
        )

        return materialized_view_info

    def create_pipeline(
        self,
        *,
        features: List[Feature],
        offline_store_config: OfflineStoreConfig,
        schedule: Optional[CronSchedule] = None,
        start_time: Optional[datetime.datetime] = None,
    ) -> List[MaterializedViewInfo]:
        """
        Creates and runs a pipeline that materializes the given features into tables.

        Features are grouped by (source, granularity) and each unique combination
        creates a separate materialized view.

        Restrictions:
        - Supports SlidingWindow and TumblingWindow features
        - Features within same (source, granularity) group must have same granularity
          (slide_duration for SlidingWindow, window_duration for TumblingWindow)
        - All features must use a single column for aggregation
        - ContinuousWindow not supported, at this time

        :param features: List of features to materialize
        :param offline_store_config: The offline store configuration containing catalog, schema, and table prefix
        :param schedule: The schedule at which to run the pipeline (applied to all created views)
        :param start_time: The earliest time to generate features from. If not provided,
                          will use the minimum timestamp from the source table's timeseries column
        :return: List of MaterializedViewInfo, one per unique (source, granularity) combination
        """
        # Validate inputs
        if not features:
            raise ValueError("At least one feature is required")

        self._validate_window_features(features)

        # Convert List[Feature] to List[FeatureAggregations] (grouped by source/filter)
        aggregations_list = self._convert_features_to_aggregations(features, start_time)

        # Create materialized view for each group
        materialized_views = []

        for idx, feature_aggregations in enumerate(aggregations_list):
            # Generate unique table name
            if len(aggregations_list) == 1:
                # Single group: use prefix as-is
                output_table = self._generate_unique_table_name(
                    offline_store_config.catalog_name,
                    offline_store_config.schema_name,
                    offline_store_config.table_name_prefix,
                )
            else:
                # Multiple groups: append group suffix
                group_suffix = self._generate_table_suffix(idx)
                output_table = self._generate_unique_table_name(
                    offline_store_config.catalog_name,
                    offline_store_config.schema_name,
                    f"{offline_store_config.table_name_prefix}_{group_suffix}",
                )

            # Validate UC entities
            if not uc_utils.is_uc_entity(feature_aggregations.source_table):
                raise ValueError(
                    f"Source table '{feature_aggregations.source_table}' must be a Unity Catalog entity"
                )
            if not uc_utils.is_uc_entity(output_table):
                raise ValueError(
                    f"Output table '{output_table}' must be a Unity Catalog entity"
                )

            # Create the materialized view using the materialization client
            view_info = self._materialization_client.create_materialized_view(
                features=feature_aggregations,
                output_table=output_table,
                schedule=schedule,
            )
            materialized_views.append(view_info)

        return materialized_views

    def _validate_window_features(self, features: List[Feature]) -> None:
        """Validate that all features have supported time windows.

        Supports SlidingWindow and TumblingWindow. ContinuousWindow and base TimeWindow
        are not supported in create_pipeline.

        Args:
            features: List of features to validate

        Raises:
            ValueError: If features are missing time_window or have unsupported window types
        """
        # Check for missing time windows
        missing_windows = [f.name for f in features if not f.time_window]
        if missing_windows:
            raise ValueError(
                f"Features missing time_window: {', '.join(missing_windows)}"
            )

        # Check for unsupported window types (reject ContinuousWindow and base TimeWindow)
        unsupported_windows = [
            f.name
            for f in features
            if not isinstance(f.time_window, (SlidingWindow, TumblingWindow))
        ]
        if unsupported_windows:
            raise ValueError(
                f"Features must have SlidingWindow or TumblingWindow, but these do not: "
                f"{', '.join(unsupported_windows)}"
            )

    def _get_granularity(self, feature: Feature) -> datetime.timedelta:
        """Extract granularity from a feature, supporting both SlidingWindow and TumblingWindow.

        For SlidingWindow: granularity = slide_duration
        For TumblingWindow: granularity = duration

        Args:
            feature: Feature to extract granularity from

        Returns:
            The granularity as a timedelta

        Raises:
            ValueError: If unsupported window type is encountered
        """
        if isinstance(feature.time_window, SlidingWindow):
            granularity = feature.time_window.slide_duration
        elif isinstance(feature.time_window, TumblingWindow):
            granularity = feature.time_window.duration
        else:
            # Caller should have already validated features only have SlidingWindow or TumblingWindow
            raise ValueError(
                f"Unsupported window type for feature {feature.name}: {type(feature.time_window).__name__}. "
                f"Only SlidingWindow and TumblingWindow are supported."
            )

        # Warn if granularity is less than 1 hour
        if granularity < datetime.timedelta(hours=1):
            _logger.warning(
                f"The specified granularity is less than 1 hour ({granularity}). "
                "Depending on the granularity of event times in the source data and number of rows, "
                "the pipeline execution could take a long time and could create a large materialized table."
            )

        return granularity

    def _generate_unique_table_name(
        self, catalog_name: str, schema_name: str, table_name_prefix: str
    ) -> str:
        """Generate a unique table name by appending a numeric suffix.

        Starts with _001 and increments until finding an available name.

        ToDo: move this closer to OfflineStoreConfig or materialization client rather than the top-level client.

        :param catalog_name: The catalog name
        :param schema_name: The schema name
        :param table_name_prefix: The table name prefix
        :return: A unique table name that doesn't already exist in UC
        """
        suffix = 1
        max_attempts = 999  # Reasonable upper limit

        while suffix <= max_attempts:
            table_name = f"{table_name_prefix}_{suffix:03d}"
            full_table_name = f"{catalog_name}.{schema_name}.{table_name}"

            # Use _spark_client.table_exists to check if table already exists
            if not self._spark_client.table_exists(full_table_name):
                return full_table_name

            suffix += 1

        # If we've exhausted all options, raise an error
        raise ValueError(
            f"Could not generate unique table name for prefix '{table_name_prefix}'. Use a different prefix."
        )

    def _generate_table_suffix(self, index: int) -> str:
        """Generate a suffix for multi-group pipelines.

        :param index: The group index
        :return: A suffix string (e.g., "group_0", "group_1")
        """
        return f"group_{index}"

    def _convert_features_to_aggregations(
        self,
        features: List[Feature],
        start_time: Optional[datetime.datetime] = None,
    ) -> List[FeatureAggregations]:
        """Convert new Feature objects to legacy FeatureAggregations format.

        Groups features by (source, filter_condition) and creates one FeatureAggregations
        object per unique combination.

        :param features: List of features to convert
        :param start_time: Optional start time for all groups
        :return: List of FeatureAggregations, one per unique (source, filter_condition) combination
        """
        if not features:
            raise ValueError("No features provided")

        # Group features by (source, granularity) combination
        # Features with same source and granularity share a materialized view
        feature_groups: Dict[
            Tuple[DataSource, datetime.timedelta], List[Feature]
        ] = defaultdict(list)

        for feature in features:
            # group features by (source, granularity) combination
            feature_granularity = self._get_granularity(feature)
            key = (feature.source, feature_granularity)
            feature_groups[key].append(feature)

        # Convert each group to a FeatureAggregations object
        aggregations_list = []

        for (source, granularity), group_features in feature_groups.items():
            # Convert Feature objects to Aggregation objects for this group
            aggregations = []
            for feature in group_features:
                # Extract column name from inputs (assuming single input for now)
                if not feature.inputs:
                    raise ValueError(f"Feature '{feature.name}' has no input columns")

                column_name = feature.inputs[0]  # Take first input column

                aggregations.append(
                    Aggregation(
                        column=column_name,
                        function=feature.function.name,  # Convert Function to string
                        time_window=feature.time_window,
                        output_column=feature.name,  # Use feature name as output column
                        filter_condition=feature.filter_condition,
                    )
                )

            # Calculate start time for this group
            snapped_start_time = self._snap_to_granularity_boundary(
                start_time or self._infer_start_time(group_features), granularity
            )

            # Create FeatureAggregations object for this group
            feature_agg = FeatureAggregations(
                source_table=source.full_name(),
                lookup_key=source.entity_columns,
                timestamp_key=source.timeseries_column,
                granularity=granularity,
                start_time=snapped_start_time,
                aggregations=aggregations,
            )
            aggregations_list.append(feature_agg)

        return aggregations_list

    def _snap_to_granularity_boundary(
        self, timestamp: datetime.datetime, granularity: datetime.timedelta
    ) -> datetime.datetime:
        """
        Snap a timestamp to the beginning of its granularity period.

        This ensures consistent time boundaries for feature aggregations by aligning
        timestamps to granularity intervals. For timezone-less timestamps, assumes UTC.
        For timezone-aware timestamps, snaps within that timezone.

        TODO(ML-57868): Update this method to snap to the appropriate start-time boundary, based on time window specification.

        :param timestamp: The timestamp to snap
        :param granularity: The granularity period (e.g., 1 hour, 1 day)
        :return: Timestamp snapped to the beginning of its granularity period

        Example:
            If granularity is 1 day and timestamp is 2023-05-15 14:30:00,
            returns 2023-05-15 00:00:00

            If granularity is 6 hours and timestamp is 2023-05-15 14:30:00,
            returns 2023-05-15 12:00:00 (nearest 6-hour boundary)
        """
        # Determine the reference epoch based on timezone
        if timestamp.tzinfo is not None:
            # Use epoch in the same timezone as the timestamp
            epoch = datetime.datetime(1970, 1, 1, tzinfo=timestamp.tzinfo)
        else:
            # For naive timestamps, assume UTC
            epoch = datetime.datetime(1970, 1, 1)

        # Calculate seconds since epoch
        seconds_since_epoch = (timestamp - epoch).total_seconds()

        # Calculate granularity in seconds
        granularity_seconds = granularity.total_seconds()

        # Snap down to the nearest granularity boundary
        snapped_seconds = (
            seconds_since_epoch // granularity_seconds
        ) * granularity_seconds

        # Convert back to datetime, preserving timezone information
        snapped_timestamp = epoch + datetime.timedelta(seconds=snapped_seconds)

        return snapped_timestamp

    def _infer_start_time(self, features: List[Feature]) -> datetime.datetime:
        # Calculate minimum timestamp from source table
        first_feature = features[0]
        source = first_feature.source

        def _raise_start_time_error(reason: str) -> None:
            raise ValueError(
                f"Cannot determine start_time: {reason} from source table '{source.full_name()}' "
                f"column '{source.timeseries_column}'. "
                f"Provide the start time explicitly using start_time argument."
            )

        try:
            # Use Spark to get the minimum timestamp from the source table
            from pyspark.sql import functions as F

            df = source.load_df(self._spark_client)
            min_timestamp_row = df.select(
                F.min(source.timeseries_column).alias("min_ts")
            ).collect()

            if min_timestamp_row and min_timestamp_row[0]["min_ts"] is not None:
                return min_timestamp_row[0]["min_ts"]
            else:
                # Table is empty or has null timestamps
                _raise_start_time_error("no valid timestamps found")

        except ValueError:
            # Re-raise ValueError from _raise_start_time_error
            raise
        except Exception as e:
            # Could not access source table or execute query
            _logger.error(
                f"Failed to determine start_time from source table '{source.full_name()}': {e}"
            )
            _raise_start_time_error("unable to query minimum timestamp")

    def build_model_env(self, model_uri: str, save_path: str) -> str:
        """
        Prebuild the model Python environment required by the given model and generate an archive file saved to the specified ``save_path``.
        The resulting environment can then be used in :meth:`FeatureEngineeringClient.score_batch` as the ``prebuilt_env_uri`` parameter.

        :param model_uri: URI of the model used to build the Python environment.
        :param save_path: Directory path to save the prebuilt model environment archive file.
          This can be a local directory path, a mounted DBFS path (e.g., '/dbfs/...'),
          or a mounted UC volume path (e.g., '/Volumes/...').

        :return: The path of the archive file containing the Python environment data.
        """
        artifact_path = os.path.join(mlflow.pyfunc.DATA, MODEL_DATA_PATH_ROOT)
        model_data_path = os.path.join(model_uri, artifact_path)
        raw_model_path = os.path.join(
            model_data_path, mlflow_model_constants.RAW_MODEL_FOLDER
        )
        return mlflow.pyfunc.build_model_env(raw_model_path, save_path)

    def _grant_permission(
        self, *, endpoint_name: str, endpoint_service_principal: str = None
    ):
        """
        Grant permission to the endpoint.

        Deprecated. This method is no longer needed.

        :param endpoint_name: The name of the endpoint.
        :param endpoint_service_principal: Optional. The service principal of the endpoint.
        """
        _logger.warning(
            "'_grant_permission' API is no longer required. The endpoint's service principal now uses Unity Catalog permissions to query downstream resources. Refer to the endpoint page for details. "
            "This method will be removed in future versions."
        )

    def create_online_store(
        self,
        *,
        name: str,
        capacity: str,
        read_replica_count: Optional[int] = None,
        usage_policy_id: Optional[str] = None,
    ) -> DatabricksOnlineStore:
        """
        Create an Online Feature Store.

        :param name: The name of the online store.
        :param capacity: The capacity of the online store. Valid values are "CU_1", "CU_2", "CU_4", "CU_8".
        :param read_replica_count: Optional. The number of read replicas for the online store.
        :param usage_policy_id: Optional. ID of the usage policy to associate with the online store used for cost tracking.
        :return: The created online store.
        """
        # due to casting in the SDK, we cannot validate the type of 'read_replica_count' in the backend, so we validate it here in the client.
        # we do not validate the type of 'capacity' because validation in the backend already throws an actionable error message.
        if read_replica_count is not None and not isinstance(read_replica_count, int):
            raise TypeError("'read_replica_count' value must be an integer.")

        existing_store = self.get_online_store(name=name)
        if existing_store is not None:
            raise AlreadyExists(f"Online store with name '{name}' already exists")

        online_store = self._workspace_client.feature_store.create_online_store(
            online_store=OnlineStore(
                name=name,
                capacity=capacity,
                read_replica_count=read_replica_count,
                usage_policy_id=usage_policy_id,
            )
        )

        return DatabricksOnlineStore._from_online_store(online_store)

    def get_online_store(self, *, name: str) -> Optional[DatabricksOnlineStore]:
        """
        Get an Online Feature Store.

        Note: this method is experimental and is expected to be removed in version 0.13.0.
        :param name: The name of the online store.
        :return: The retrieved online store, or None if not found.
        """

        try:
            online_store = self._workspace_client.feature_store.get_online_store(
                name=name
            )
            return DatabricksOnlineStore._from_online_store(online_store)
        except NotFound:
            return None

    def update_online_store(
        self,
        *,
        name: str,
        capacity: Union[str, _UnsetType] = UNSET,
        read_replica_count: Union[int, _UnsetType] = UNSET,
        usage_policy_id: Union[str, _UnsetType] = UNSET,
    ) -> DatabricksOnlineStore:
        """
        Update an Online Feature Store. Only the fields specified will be updated. Fields that are not specified will remain unchanged.

        :param name: The name of the online store.
        :param capacity: Optional. The capacity of the online store. Valid values are "CU_1", "CU_2", "CU_4", "CU_8".
        :param read_replica_count: Optional. The number of read replicas for the online store.
        :param usage_policy_id: Optional. ID of the usage policy to associate with the online store used for cost tracking.
        :return: The updated online store.
        """
        # due to casting in the SDK, we cannot validate the type of 'read_replica_count' in the backend, so we validate it here in the client.
        # we do not validate the type of 'capacity' because validation in the backend already throws an actionable error message.
        if read_replica_count is not UNSET and not isinstance(read_replica_count, int):
            raise TypeError("'read_replica_count' value must be an integer.")

        existing_store = self.get_online_store(name=name)
        if existing_store is None:
            raise NotFound(f"Online store with name '{name}' not found")

        # map of all updateable fields to their provided values
        field_to_value = {
            "capacity": capacity,
            "read_replica_count": read_replica_count,
            "usage_policy_id": usage_policy_id,
        }
        update_fields = {
            field: value
            for field, value in field_to_value.items()
            if value is not UNSET
        }

        if all(
            getattr(existing_store, field) == value
            for field, value in update_fields.items()
        ):
            return existing_store

        online_store = replace(existing_store, **update_fields)._to_sdk_online_store()
        update_mask = ",".join(update_fields.keys())
        updated_store = self._workspace_client.feature_store.update_online_store(
            name=name,
            online_store=online_store,
            update_mask=update_mask,
        )

        return DatabricksOnlineStore._from_online_store(updated_store)

    def delete_online_store(self, *, name: str) -> None:
        """
        Delete an Online Feature Store.

        :param name: The name of the online store.
        :return: None.
        """
        try:
            self._workspace_client.feature_store.delete_online_store(name=name)
        except NotFound:
            raise NotFound(f"Online store with name '{name}' not found")

    def list_online_stores(self) -> List[DatabricksOnlineStore]:
        """
        List available Online Feature Stores. These are online stores that are associated with
        a feature store. Note that online stores not associated with a feature store will be excluded
        from the output.

        :return: A list of DatabricksOnlineStore objects.
        """

        # list_online_stores is paginated, so we need to handle pagination here.
        online_stores = self._workspace_client.feature_store.list_online_stores()
        return [
            DatabricksOnlineStore._from_online_store(item) for item in online_stores
        ]

    def materialize_features(
        self,
        *,
        features: List[Feature],
        offline_config: OfflineStoreConfig,
        online_config: Optional[OnlineStoreConfig] = None,
        pipeline_state: Union[MaterializedFeaturePipelineScheduleState, str],
        cron_schedule: Optional[str] = None,
    ) -> List[MaterializedFeature] | None:
        """
        Direct Databricks to materialize a list of feature definitions stored in Unity Catalog
        to an offline (Delta Live Table) store and/or an online store for model serving. Note that
        the features must already exist in Unity Catalog as functions, which can be created using
        :meth:`FeatureEngineeringClient.create_feature`.

        If both offline_config and online_config are provided, there will be two materialized features created
        and returned for each feature provided.

        :param features: The list of features to materialize.
        :param offline_config: The offline store configuration. Required.
        :param online_config: The online store configuration. Optional.
        :param pipeline_state: A supported materialized feature pipeline schedule state, currently only "ACTIVE" is supported.
        :param cron_schedule: The cron schedule for the materialization pipeline. May be omitted in future pipeline states.
        :return: The list of materialized features.
        """
        if isinstance(pipeline_state, str):
            pipeline_state_resolved = MaterializedFeaturePipelineScheduleState(
                pipeline_state
            )
        else:
            pipeline_state_resolved = pipeline_state

        # Build requests for offline and online stores separately due to proto oneof constraint:
        # offline_store_config and online_store_config cannot be set on the same MaterializedFeature
        requests = [
            CreateMaterializedFeatureRequest(
                materialized_feature=MaterializedFeature(
                    feature_name=feature.full_name,
                    offline_store_config=offline_config,
                    pipeline_schedule_state=pipeline_state_resolved,
                    cron_schedule=cron_schedule,
                )
            )
            for feature in features
            if offline_config is not None
        ] + [
            CreateMaterializedFeatureRequest(
                materialized_feature=MaterializedFeature(
                    feature_name=feature.full_name,
                    online_store_config=online_config,
                    pipeline_schedule_state=pipeline_state_resolved,
                    cron_schedule=cron_schedule,
                )
            )
            for feature in features
            if online_config is not None
        ]

        response = self._workspace_client.feature_engineering.batch_create_materialized_features(
            requests=requests
        )
        return response.materialized_features

    @experimental
    def create_kafka_config(
        self,
        *,
        name: str,
        bootstrap_servers: str,
        subscription_mode: SubscriptionMode,
        auth_config: AuthConfig,
        key_schema: Optional[SchemaConfig] = None,
        value_schema: Optional[SchemaConfig] = None,
        extra_options: Optional[Dict[str, str]] = None,
    ) -> KafkaConfig:
        """
        Create a Kafka configuration for streaming feature ingestion.

        :param name: Required. A unique name for the Kafka configuration within the metastore. Can be distinct from the topic name.
        :param bootstrap_servers: Required. A comma-separated list of host/port pairs pointing to the Kafka cluster
          (e.g. "host1:port1,host2:port2"). See https://spark.apache.org/docs/latest/streaming/structured-streaming-kafka-integration.html
          for more details on this parameter.
        :param subscription_mode: Required. A SubscriptionMode instance specifying how to select Kafka topics to consume from.
          Supports three modes: subscribe (comma-separated topic list), subscribe_pattern (regex pattern), or assign
          (JSON with specific topic-partitions). See https://spark.apache.org/docs/latest/streaming/structured-streaming-kafka-integration.html
          for more details on this parameter.
        :param auth_config: Required. An AuthConfig instance containing authentication configuration for connecting to Kafka topics.
          Supports Unity Catalog service credentials. See https://docs.databricks.com/aws/en/connect/unity-catalog/cloud-services
          for more details on UC service credentials.
        :param key_schema: Optional. A SchemaConfig instance defining the schema for extracting message keys from Kafka topics.
          Supports IEFT JSON Schema format (https://json-schema.org/). At least one of key_schema or value_schema must be provided.
        :param value_schema: Optional. A SchemaConfig instance defining the schema for extracting message values from Kafka topics.
          Supports IEFT JSON Schema format (https://json-schema.org/). At least one of key_schema or value_schema must be provided.
        :param extra_options: Optional. A dictionary of additional Kafka consumer configuration options. Keys should be source options
        or Kafka consumer options (e.g. {"kafka.security.protocol": "SASL_SSL"}). See
          https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html
          for more details on optional configurations.
        :return: KafkaConfig instance containing the created configuration.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("'name' must be a non-empty string")
        if not isinstance(bootstrap_servers, str) or not bootstrap_servers.strip():
            raise ValueError("'bootstrap_servers' must be a non-empty string")
        if not isinstance(subscription_mode, SubscriptionMode):
            raise TypeError(
                f"'subscription_mode' must be a SubscriptionMode instance, got {type(subscription_mode)}"
            )
        if not isinstance(auth_config, AuthConfig):
            raise TypeError(
                f"'auth_config' must be an AuthConfig instance, got {type(auth_config)}"
            )
        if key_schema is not None and not isinstance(key_schema, SchemaConfig):
            raise TypeError(
                f"'key_schema' must be a SchemaConfig instance if specified, got {type(key_schema)}"
            )
        if value_schema is not None and not isinstance(value_schema, SchemaConfig):
            raise TypeError(
                f"'value_schema' must be a SchemaConfig instance if specified, got {type(value_schema)}"
            )
        if key_schema is None and value_schema is None:
            raise ValueError(
                "At least one of 'key_schema' or 'value_schema' must be provided"
            )

        kafka_config = KafkaConfig(
            name=name.strip(),
            bootstrap_servers=bootstrap_servers.strip(),
            subscription_mode=subscription_mode,
            auth_config=auth_config,
            key_schema=key_schema,
            value_schema=value_schema,
            extra_options=extra_options,
        )

        return self._workspace_client.feature_engineering.create_kafka_config(
            kafka_config=kafka_config
        )

    @experimental
    def get_kafka_config(self, *, name: str) -> KafkaConfig:
        """
        Retrieve a Kafka configuration by name within the caller's metastore.

        :param name: Required. The name of the Kafka configuration to retrieve.
        :return: KafkaConfig instance containing the configuration.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("'name' must be a non-empty string")

        return self._workspace_client.feature_engineering.get_kafka_config(
            name=name.strip()
        )

    @experimental
    def list_kafka_configs(
        self,
        *,
        max_results: int = 50,
        include_schemas: bool = False,
    ) -> List[KafkaConfig]:
        """
        List Kafka configurations in the current metastore.

        :param max_results: The maximum number of configs to return, default is 50. Specifying a high number may result in a long-running operation.
        :param include_schemas: Whether to include schema information in the response, default is False. Schemas may be large and can be
          retrieved individually instead using :meth:`FeatureEngineeringClient.get_kafka_config`. Specifying True may result in a long-running operation.
        :return: List of KafkaConfig instances.
        """
        iterator = self._workspace_client.feature_engineering.list_kafka_configs()
        configs = list(islice(iterator, max_results))

        if include_schemas:
            # Make individual get_kafka_config calls to retrieve full configs with schemas
            return [self.get_kafka_config(name=config.name) for config in configs]

        return configs

    @experimental
    def delete_kafka_config(self, *, name: str) -> None:
        """
        Delete a Kafka configuration.

        :param name: Required. The name of the Kafka configuration to delete.

        .. note::
            The caller must be the creator of the Kafka configuration in order to delete it.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("'name' must be a non-empty string")

        self._workspace_client.feature_engineering.delete_kafka_config(
            name=name.strip()
        )
