import abc
import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from databricks.ml_features_common.entities._feature_store_object import (
    _FeatureStoreObject,
)
from databricks.sdk.service.ml import ColumnIdentifier
from databricks.sdk.service.ml import DataSource as SDKDataSource
from databricks.sdk.service.ml import DeltaTableSource as SDKDeltaTableSource
from databricks.sdk.service.ml import KafkaSource as SDKKafkaSource

_logger = logging.getLogger(__name__)


class DataSourceTypes(Enum):
    """Enumeration of supported data source types."""

    DELTA = "delta"
    UNIFORM = "uniform"
    KAFKA = "kafka"
    VOLUME = "volume"
    DATAFRAME = "dataframe"


class DataSource(_FeatureStoreObject, abc.ABC):
    """
    Abstract base class for data sources used in feature computation.

    :param source_type: The type of data source
    :param entity_columns: List of column names that serve as primary keys
    :param timeseries_column: Column name that contains timestamp data
    """

    def __init__(
        self,
        *,
        source_type: DataSourceTypes,
        entity_columns: List[str],
        timeseries_column: str,
    ):
        """Initialize a DataSource object. See class documentation."""
        self._validate_parameters(source_type, entity_columns, timeseries_column)

        self._source_type = source_type
        self._entity_columns = entity_columns
        self._timeseries_column = timeseries_column
        self._order_column = f"___{timeseries_column}_as_long"

    @property
    def source_type(self) -> DataSourceTypes:
        """The type of data source."""
        return self._source_type

    @property
    def entity_columns(self) -> List[str]:
        """List of column names that serve as primary keys."""
        return self._entity_columns

    @property
    def timeseries_column(self) -> str:
        """Column name that contains timestamp data."""
        return self._timeseries_column

    @property
    def order_column(self) -> str:
        """The column name for the order column."""
        return self._order_column

    @abc.abstractmethod
    def full_name(self) -> str:
        """Return the full name/identifier for this data source."""
        raise NotImplementedError()

    @abc.abstractmethod
    def load_df(self, spark_client):
        """Load the data source as a Spark DataFrame. Must be implemented by all derived classes."""
        raise NotImplementedError()

    @abc.abstractmethod
    def __hash__(self):
        """Make DataSource hashable. Must be implemented by all derived classes."""
        raise NotImplementedError()

    def _validate_parameters(
        self,
        source_type: DataSourceTypes,
        entity_columns: List[str],
        timeseries_column: str,
    ):
        """Validates the parameters provided to the DataSource class."""
        if not isinstance(source_type, DataSourceTypes):
            raise ValueError("The 'source_type' must be a DataSourceTypes enum value.")

        if not isinstance(entity_columns, list):
            raise ValueError("The 'entity_columns' must be a list.")

        if not entity_columns:
            raise ValueError(
                "The 'entity_columns' must contain at least one column name."
            )

        for i, column in enumerate(entity_columns):
            if not isinstance(column, str) or not column.strip():
                raise ValueError(
                    f"All entity columns must be non-empty strings. "
                    f"Invalid column at index {i}: {column}"
                )

        if not isinstance(timeseries_column, str) or not timeseries_column.strip():
            raise ValueError("The 'timeseries_column' must be a non-empty string.")

    @classmethod
    def _from_yaml_dict(cls, data_source_dict: Dict[str, Any]) -> "DataSource":
        """Create a DataSource from a dictionary loaded from YAML."""
        if (
            DeltaTableSource.CATALOG_NAME_FIELD_NAME in data_source_dict
            and DeltaTableSource.SCHEMA_NAME_FIELD_NAME in data_source_dict
            and DeltaTableSource.TABLE_NAME_FIELD_NAME in data_source_dict
        ):
            return DeltaTableSource._from_yaml_dict(data_source_dict)
        elif KafkaSource.NAME_FIELD_NAME in data_source_dict:
            return KafkaSource._from_yaml_dict(data_source_dict)
        else:
            raise ValueError(
                f"Unsupported data source type in dictionary: {data_source_dict}"
            )

    def _to_sdk_data_source(self) -> SDKDataSource:
        raise NotImplementedError

    @classmethod
    def _from_sdk_data_source(cls, sdk_source: SDKDataSource) -> "DataSource":
        if not isinstance(sdk_source, SDKDataSource):
            raise TypeError(
                "Expected databricks.sdk.service.ml.DataSource when converting from SDK"
            )

        # Check which source type is present
        if sdk_source.delta_table_source is not None:
            return DeltaTableSource._from_sdk_data_source(sdk_source.delta_table_source)
        elif sdk_source.kafka_source is not None:
            return KafkaSource._from_sdk_data_source(sdk_source.kafka_source)
        else:
            raise ValueError("Unknown or unsupported DataSource type in SDK object")


class DeltaTableSource(DataSource):
    """
    Data source implementation for Delta Lake tables.

    :param catalog_name: The name of the Unity Catalog catalog
    :param schema_name: The name of the schema within the catalog
    :param table_name: The name of the table within the schema
    :param entity_columns: List of column names that serve as primary keys
    :param timeseries_column: Column name that contains timestamp data
    """

    CATALOG_NAME_FIELD_NAME = "catalog"
    SCHEMA_NAME_FIELD_NAME = "schema"
    TABLE_NAME_FIELD_NAME = "table"
    ENTITY_COLUMNS_FIELD_NAME = "entity_columns"
    TIMESERIES_COLUMN_FIELD_NAME = "timeseries_column"

    def __init__(
        self,
        *,
        catalog_name: str,
        schema_name: str,
        table_name: str,
        entity_columns: List[str],
        timeseries_column: str,
    ):
        """Initialize a DeltaTableSource object. See class documentation."""
        self._validate_delta_parameters(catalog_name, schema_name, table_name)

        # Initialize the parent with DELTA type
        super().__init__(
            source_type=DataSourceTypes.DELTA,
            entity_columns=entity_columns,
            timeseries_column=timeseries_column,
        )

        self._catalog_name = catalog_name
        self._schema_name = schema_name
        self._table_name = table_name

    @property
    def catalog_name(self) -> str:
        """The name of the Unity Catalog catalog."""
        return self._catalog_name

    @property
    def schema_name(self) -> str:
        """The name of the schema within the catalog."""
        return self._schema_name

    @property
    def table_name(self) -> str:
        """The name of the table within the schema."""
        return self._table_name

    def full_name(self) -> str:
        """Return the full table name in catalog.schema.table format."""
        return f"{self._catalog_name}.{self._schema_name}.{self._table_name}"

    def load_df(self, spark_client):
        """Load the Delta table as a Spark DataFrame."""
        return spark_client.read_table(self.full_name())

    def __hash__(self):
        """Make DeltaTableSource hashable by using immutable representations of its attributes."""
        # Create a tuple of all the key attributes including Delta-specific ones
        return hash(
            (
                self._source_type,
                tuple(self._entity_columns),
                self._timeseries_column,
                self._catalog_name,
                self._schema_name,
                self._table_name,
            )
        )

    def __str__(self) -> str:
        """Return a concise string representation of the data source."""
        entities_str = ", ".join(self._entity_columns)
        return f"{self.full_name()}[entity_columns=({entities_str}), timeseries_column={self._timeseries_column}]"

    def __repr__(self) -> str:
        """Return a detailed string representation of the data source."""
        return (
            f"DeltaTableSource(catalog_name={self._catalog_name!r}, "
            f"schema_name={self._schema_name!r}, table_name={self._table_name!r}, "
            f"entity_columns={self._entity_columns!r}, "
            f"timeseries_column={self._timeseries_column!r})"
        )

    def _validate_delta_parameters(
        self, catalog_name: str, schema_name: str, table_name: str
    ):
        """Validates Delta-specific parameters."""
        if not catalog_name or not isinstance(catalog_name, str):
            raise ValueError("The 'catalog_name' must be a non-empty string.")

        if not schema_name or not isinstance(schema_name, str):
            raise ValueError("The 'schema_name' must be a non-empty string.")

        if not table_name or not isinstance(table_name, str):
            raise ValueError("The 'table_name' must be a non-empty string.")

    def _to_yaml_dict(self) -> Dict[str, Any]:
        """Convert the DeltaTableSource to a dictionary that can be used to generate a YAML file."""
        return {
            DeltaTableSource.CATALOG_NAME_FIELD_NAME: self._catalog_name,
            DeltaTableSource.SCHEMA_NAME_FIELD_NAME: self._schema_name,
            DeltaTableSource.TABLE_NAME_FIELD_NAME: self._table_name,
            DeltaTableSource.ENTITY_COLUMNS_FIELD_NAME: self._entity_columns,
            DeltaTableSource.TIMESERIES_COLUMN_FIELD_NAME: self._timeseries_column,
        }

    @classmethod
    def _from_yaml_dict(cls, data_source_dict: Dict[str, Any]) -> "DeltaTableSource":
        """Create a DeltaTableSource from a dictionary loaded from YAML."""
        return cls(
            catalog_name=data_source_dict[DeltaTableSource.CATALOG_NAME_FIELD_NAME],
            schema_name=data_source_dict[DeltaTableSource.SCHEMA_NAME_FIELD_NAME],
            table_name=data_source_dict[DeltaTableSource.TABLE_NAME_FIELD_NAME],
            entity_columns=data_source_dict[DeltaTableSource.ENTITY_COLUMNS_FIELD_NAME],
            timeseries_column=data_source_dict[
                DeltaTableSource.TIMESERIES_COLUMN_FIELD_NAME
            ],
        )

    def _to_sdk_data_source(self) -> SDKDataSource:
        return SDKDataSource(
            delta_table_source=SDKDeltaTableSource(
                full_name=self.full_name(),
                entity_columns=list(self.entity_columns),
                timeseries_column=self.timeseries_column,
            )
        )

    @classmethod
    def _from_sdk_data_source(
        cls, sdk_source: SDKDeltaTableSource
    ) -> "DeltaTableSource":
        if sdk_source.full_name is None:
            raise ValueError("SDK DeltaTableSource must include 'full_name'")

        parts = sdk_source.full_name.split(".")
        if len(parts) != 3:
            raise ValueError(
                f"The full_name of DeltaTableSource {sdk_source.full_name} is not in '<catalog>.<schema>.<table>' format"
            )

        return DeltaTableSource(
            catalog_name=parts[0],
            schema_name=parts[1],
            table_name=parts[2],
            entity_columns=list(sdk_source.entity_columns),
            timeseries_column=sdk_source.timeseries_column,
        )


class VolumeSource(DataSource):
    """
    Data source implementation for Unity Catalog Volumes.

    TODO: Implementation to be defined based on volume requirements.
    """

    def __init__(
        self,
        *,
        entity_columns: List[str],
        timeseries_column: str,
    ):
        """Initialize a VolumeSource object. See class documentation."""
        super().__init__(
            source_type=DataSourceTypes.VOLUME,
            entity_columns=entity_columns,
            timeseries_column=timeseries_column,
        )

    def full_name(self) -> str:
        """Return the full volume path identifier."""
        # TODO: Implement volume-specific naming convention
        raise NotImplementedError("VolumeSource.full_name() is not yet implemented.")

    def load_df(self, spark_client):
        """Load the volume data as a Spark DataFrame."""
        # TODO: Implement volume-specific DataFrame loading
        raise NotImplementedError("VolumeSource.load_df() is not yet implemented.")

    def __hash__(self):
        """Make VolumeSource hashable."""
        # TODO: Implement volume-specific hash when volume attributes are defined
        raise NotImplementedError("VolumeSource.__hash__() is not yet implemented.")


class KafkaSource(DataSource):
    """
    Data source implementation for Kafka streams.

    KafkaSource references a KafkaConfig by name. The KafkaConfig contains connection details, authentication, and schemas for the Kafka topics.
    Column names must be prefixed with 'key:' or 'value:' to indicate which schema to use. Examples: 'key:customer_id' or 'value:trip_details.pickup_zip' for nested JSON fields.

    :param name: Name of the KafkaConfig to use (uniquely identifies the KafkaConfig in the metastore)
    :param entity_columns: List of column names with schema prefix (e.g., ['key:customer_id', 'value:trip_details.pickup_zip'])
    :param timeseries_column: Column name with schema prefix (e.g., 'value:event_timestamp')
    """

    class SchemaType:
        """Constants for Kafka schema types."""

        KEY = "key"
        VALUE = "value"

    NAME_FIELD_NAME = "name"
    ENTITY_COLUMNS_FIELD_NAME = "entity_columns"
    TIMESERIES_COLUMN_FIELD_NAME = "timeseries_column"

    def __init__(
        self,
        *,
        name: str,
        entity_columns: List[str],
        timeseries_column: str,
    ):
        """Initialize a KafkaSource object. See class documentation."""
        self._validate_kafka_parameters(name)

        super().__init__(
            source_type=DataSourceTypes.KAFKA,
            entity_columns=entity_columns,
            timeseries_column=timeseries_column,
        )

        self._name = name

    @property
    def name(self) -> str:
        """The name of the KafkaConfig this source references."""
        return self._name

    def full_name(self) -> str:
        """Return the Kafka config name as the full identifier."""
        return self._name

    def load_df(self, spark_client):
        """Load the Kafka stream as a Spark DataFrame."""
        # TODO: Implement Kafka-specific DataFrame loading
        raise NotImplementedError("KafkaSource.load_df() is not yet implemented.")

    def __hash__(self):
        """Make KafkaSource hashable by using immutable representations of its attributes."""
        return hash(
            (
                self._source_type,
                self._name,
                tuple(self._entity_columns),
                self._timeseries_column,
            )
        )

    def __str__(self) -> str:
        """Return a concise string representation of the data source."""
        entities_str = ", ".join(self._entity_columns)
        return (
            f"KafkaSource(name={self.full_name()}, "
            f"entity_columns=[{entities_str}], "
            f"timeseries_column={self._timeseries_column})"
        )

    def __repr__(self) -> str:
        """Return a detailed string representation of the data source."""
        return (
            f"KafkaSource(name={self._name!r}, "
            f"entity_columns={self._entity_columns!r}, "
            f"timeseries_column={self._timeseries_column!r})"
        )

    def _validate_kafka_parameters(self, name: str):
        """Validates Kafka-specific parameters."""
        if not name or not isinstance(name, str):
            raise ValueError("The 'name' must be a non-empty string")

    @staticmethod
    def _validate_column_in_json_schema(
        column_path: str, json_schema_str: Optional[str]
    ) -> bool:
        """Validate that a column path exists in a JSON schema. Supports nested paths like 'trip_details.pickup_zip' by traversing the schema properties. Does not support complex, modular JSON schemas with key words like $ref."""
        if not json_schema_str:
            return False

        try:
            schema = json.loads(json_schema_str)
        except json.JSONDecodeError as ex:
            _logger.warning(
                f"Failed to parse JSON schema, skipping column validation: {ex}"
            )
            return False

        path_parts = column_path.split(".")
        current = schema
        for part in path_parts:
            if not isinstance(current, dict) or "properties" not in current:
                return False
            properties = current["properties"]
            if part not in properties:
                return False
            current = properties[part]

        return True

    @staticmethod
    def validate_columns_exist_in_schemas(columns: List[str], kafka_config) -> None:
        """Validate that columns exist in the Kafka config schemas. All columns must be prefixed with 'key:' or 'value:' and the column must exist in the corresponding schema."""
        key_schema = kafka_config.key_schema
        value_schema = kafka_config.value_schema

        def get_schema_str_and_validator(schema, schema_name: str):
            if schema is None:
                return None, None
            if hasattr(schema, "json_schema") and schema.json_schema:
                return schema.json_schema, KafkaSource._validate_column_in_json_schema
            raise NotImplementedError(
                f"Only JSON schema validation is supported. {schema_name} uses a non-JSON schema type."
            )

        key_schema_str, key_validator = get_schema_str_and_validator(
            key_schema, "key_schema"
        )
        value_schema_str, value_validator = get_schema_str_and_validator(
            value_schema, "value_schema"
        )

        for col in columns:
            if ":" not in col:
                raise ValueError(
                    f"Column '{col}' must be prefixed with '{KafkaSource.SchemaType.KEY}:' or '{KafkaSource.SchemaType.VALUE}:' to indicate which schema to use"
                )

            schema_type, column_path = col.split(":", 1)

            if schema_type not in (
                KafkaSource.SchemaType.KEY,
                KafkaSource.SchemaType.VALUE,
            ):
                raise ValueError(
                    f"Column '{col}' has invalid prefix '{schema_type}'. Must be '{KafkaSource.SchemaType.KEY}:' or '{KafkaSource.SchemaType.VALUE}:'"
                )

            if schema_type == KafkaSource.SchemaType.KEY:
                if not key_schema_str:
                    raise ValueError(
                        f"Column '{col}' references key schema but Kafka config '{kafka_config.name}' has no key_schema defined"
                    )
                if not key_validator(column_path, key_schema_str):
                    raise ValueError(
                        f"Column path '{column_path}' not found in key schema of Kafka config '{kafka_config.name}'"
                    )
            else:
                if not value_schema_str:
                    raise ValueError(
                        f"Column '{col}' references value schema but Kafka config '{kafka_config.name}' has no value_schema defined"
                    )
                if not value_validator(column_path, value_schema_str):
                    raise ValueError(
                        f"Column path '{column_path}' not found in value schema of Kafka config '{kafka_config.name}'"
                    )

    def _to_yaml_dict(self) -> Dict[str, Any]:
        """Convert the KafkaSource to a dictionary that can be used to generate a YAML file."""
        return {
            KafkaSource.NAME_FIELD_NAME: self._name,
            KafkaSource.ENTITY_COLUMNS_FIELD_NAME: self._entity_columns,
            KafkaSource.TIMESERIES_COLUMN_FIELD_NAME: self._timeseries_column,
        }

    @classmethod
    def _from_yaml_dict(cls, data_source_dict: Dict[str, Any]) -> "KafkaSource":
        """Create a KafkaSource from a dictionary loaded from YAML."""
        return cls(
            name=data_source_dict[KafkaSource.NAME_FIELD_NAME],
            entity_columns=data_source_dict[KafkaSource.ENTITY_COLUMNS_FIELD_NAME],
            timeseries_column=data_source_dict[
                KafkaSource.TIMESERIES_COLUMN_FIELD_NAME
            ],
        )

    def _to_sdk_data_source(self) -> SDKDataSource:
        """Convert to SDK DataSource format for proto serialization. Converts string columns to ColumnIdentifier objects as required by proto."""

        # Convert entity columns (strings) to ColumnIdentifier objects
        entity_column_identifiers = [
            ColumnIdentifier(variant_expr_path=col) for col in self.entity_columns
        ]

        # Convert timeseries column to ColumnIdentifier
        timeseries_column_identifier = ColumnIdentifier(
            variant_expr_path=self.timeseries_column
        )

        # Create SDK KafkaSource
        sdk_kafka_source = SDKKafkaSource(
            name=self.name,
            entity_column_identifiers=entity_column_identifiers,
            timeseries_column_identifier=timeseries_column_identifier,
        )

        return SDKDataSource(kafka_source=sdk_kafka_source)

    @classmethod
    def _from_sdk_data_source(cls, sdk_source: SDKKafkaSource) -> "KafkaSource":
        """Create KafkaSource from SDK format. Converts ColumnIdentifier objects back to simple strings."""
        if sdk_source.name is None:
            raise ValueError("SDK KafkaSource must include 'name'")

        entity_columns = [
            col_id.variant_expr_path for col_id in sdk_source.entity_column_identifiers
        ]
        timeseries_column = sdk_source.timeseries_column_identifier.variant_expr_path

        return KafkaSource(
            name=sdk_source.name,
            entity_columns=entity_columns,
            timeseries_column=timeseries_column,
        )


class DataFrameSource(DataSource):
    """
    Data source implementation for Spark DataFrames.

    This allows using an existing Spark DataFrame directly as a data source
    for feature computation, useful for in-memory data processing and testing.

    :param dataframe: The Spark DataFrame to use as the data source
    :param entity_columns: List of column names that serve as primary keys
    :param timeseries_column: Column name that contains timestamp data
    :param source_name: Optional name for the DataFrame source (for identification)
    """

    def __init__(
        self,
        *,
        dataframe,  # Will be validated as Spark DataFrame
        entity_columns: List[str],
        timeseries_column: str,
        source_name: Optional[str] = None,
    ):
        """Initialize a DataFrameSource object. See class documentation."""
        self._validate_dataframe_parameters(dataframe, source_name)

        # Initialize the parent with DATAFRAME type
        super().__init__(
            source_type=DataSourceTypes.DATAFRAME,
            entity_columns=entity_columns,
            timeseries_column=timeseries_column,
        )

        self._dataframe = dataframe
        self._source_name = source_name

    @property
    def dataframe(self):
        """The Spark DataFrame being used as the data source."""
        return self._dataframe

    @property
    def source_name(self) -> str:
        """The name identifier for this DataFrame source."""
        return self._source_name

    def full_name(self) -> str:
        """Return the source name identifier for this DataFrame."""
        return (
            self._source_name
            if self._source_name
            else f"DataFrameSource with schema : {self.dataframe.schema.simpleString()}"
        )

    def load_df(self, spark_client):
        """Return the existing Spark DataFrame."""
        return self._dataframe

    def __hash__(self):
        """Make DataFrameSource hashable by using immutable representations of its attributes."""
        # Get schema information from the DataFrame
        # Convert schema to a hashable representation (sorted tuple of field names and types)
        # Sort by field name to ensure consistent hashing regardless of field order
        schema_fields = tuple(
            sorted(
                (field.name, str(field.dataType))
                for field in self._dataframe.schema.fields
            )
        )

        # Note: We cannot hash the DataFrame itself as it's mutable
        # Use source_name and schema as the identifier for the DataFrame
        return hash(
            (
                self._source_type,
                tuple(self._entity_columns),
                self._timeseries_column,
                self._source_name,
                schema_fields,
            )
        )

    def __str__(self) -> str:
        """Return a concise string representation of the data source."""
        entities_str = ", ".join(self._entity_columns)
        name = self._source_name if self._source_name else "DataFrame"
        return f"{name}[entity_columns=({entities_str}), timeseries_column={self._timeseries_column}]"

    def __repr__(self) -> str:
        """Return a detailed string representation of the data source."""
        return (
            f"DataFrameSource(source_name={self._source_name!r}, "
            f"entity_columns={self._entity_columns!r}, "
            f"timeseries_column={self._timeseries_column!r})"
        )

    def _validate_dataframe_parameters(self, dataframe, source_name: str):
        """Validates DataFrame-specific parameters."""
        if dataframe is None:
            raise ValueError("The 'dataframe' cannot be None.")

        # Import DataFrame locally for isinstance check
        try:
            from pyspark.sql import DataFrame

            if not isinstance(dataframe, DataFrame):
                raise ValueError("The 'dataframe' must be a valid Spark DataFrame.")
        except ImportError:
            raise ImportError("PySpark is required to use DataFrameSource.")

        if source_name is not None and (
            not isinstance(source_name, str) or not source_name.strip()
        ):
            raise ValueError(
                "The 'source_name' must be a non-empty string if provided."
            )
