from __future__ import annotations

from typing import Any, Dict, List, Optional

from pyspark.sql import Column

from databricks.ml_features.entities.aggregation import TimeWindow
from databricks.ml_features.entities.data_source import DataSource
from databricks.ml_features.entities.function import Function
from databricks.ml_features_common.entities._feature_store_object import (
    _FeatureStoreObject,
)
from databricks.sdk.service.ml import DataSource as SDKDataSource
from databricks.sdk.service.ml import Feature as SDKFeature
from databricks.sdk.service.ml import Function as SDKFunction
from databricks.sdk.service.ml import TimeWindow as SDKTimeWindow


class Feature(_FeatureStoreObject):
    """
    Represents a feature definition that combines a data source with aggregation logic.

    :param catalog_name: The catalog name for the feature (required)
    :param schema_name: The schema name for the feature (required)
    :param name: The name of the feature. Leading and trailing whitespace will be stripped.
                 If not provided or empty after stripping, a name will be auto-generated
                 based on the input columns, function, and time window.
    :param source: The data source for this feature
    :param inputs: List of column names from the source to use as input
    :param function: The aggregation function to apply to the input columns
    :param time_window: The time window for the aggregation
    :param description: Optional description of the feature
    :param filter_condition: Optional SQL filter condition to apply on the source data before aggregation
    """

    INPUTS_FIELD_NAME = "inputs"
    DATA_SOURCE_FIELD_NAME = "data_source"
    FUNCTION_FIELD_NAME = "function"
    TIME_WINDOW_FIELD_NAME = "time_window"
    FILTER_CONDITION_FIELD_NAME = "filter_condition"

    def __init__(
        self,
        *,
        source: DataSource,
        inputs: List[str],
        function: Function,
        time_window: TimeWindow,
        catalog_name: str,
        schema_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        filter_condition: Optional[str] = None,
    ):
        """Initialize a Feature object. See class documentation.
        Should not be invoked directly, use `FeatureEngineeringClient.create_feature` instead.
        `create_feature` ensures the Feature is registered in Unity Catalog and properly validated.
        """
        # Validate and store mandatory catalog and schema names
        if not isinstance(catalog_name, str) or not catalog_name.strip():
            raise ValueError("'catalog_name' must be a non-empty string")
        if not isinstance(schema_name, str) or not schema_name.strip():
            raise ValueError("'schema_name' must be a non-empty string")

        self._catalog_name = catalog_name.strip()
        self._schema_name = schema_name.strip()

        # Strip whitespace from name if provided
        if name is not None and isinstance(name, str):
            name = name.strip()

        # Handle name construction based on whether name is provided and qualified
        if name:
            if "." in name:
                # If name is already qualified, validate it has the correct prefix and strip it
                expected_prefix = f"{self._catalog_name}.{self._schema_name}."
                if not name.startswith(expected_prefix):
                    raise ValueError(
                        f"Qualified name '{name}' must start with '{expected_prefix}'"
                    )
                # Strip the catalog.schema prefix to get the base name
                self._name = name[len(expected_prefix) :]
            else:
                # If name is unqualified, use it as is
                self._name = name
        else:
            # Generate base name
            self._name = self._generate_name(source, inputs, function, time_window)
        self._source = source
        self._inputs = inputs
        self._function = function
        self._time_window = time_window
        self._description = description
        self._filter_condition = filter_condition

    @property
    def name(self) -> str:
        """The leaf name of the feature."""
        return self._name

    @property
    def full_name(self) -> str:
        """The fully qualified Unity Catalog name of the feature."""
        return f"{self._catalog_name}.{self._schema_name}.{self._name}"

    @property
    def catalog_name(self) -> str:
        """The catalog name of the feature."""
        return self._catalog_name

    @property
    def schema_name(self) -> str:
        """The schema name of the feature."""
        return self._schema_name

    @property
    def source(self) -> DataSource:
        """The data source for this feature."""
        return self._source

    @property
    def inputs(self) -> List[str]:
        """List of column names from the source to use as input."""
        return self._inputs

    @property
    def function(self) -> Function:
        """The aggregation function to apply to the input columns."""
        return self._function

    @property
    def time_window(self) -> TimeWindow:
        """The time window for the aggregation."""
        return self._time_window

    @property
    def description(self) -> Optional[str]:
        """Optional description of the feature."""
        return self._description

    @property
    def filter_condition(self) -> Optional[str]:
        """Optional SQL filter condition to apply on the source data before aggregation."""
        return self._filter_condition

    @staticmethod
    def _generate_name(
        source: DataSource,
        inputs: List[str],
        function: Function,
        time_window: TimeWindow,
    ) -> str:
        # ToDo: move this to backend as a part of CreateFeature API
        """Generate a feature name from the provided parameters."""
        return f"{inputs[0]}_{function.name}_{str(time_window)}"

    def computation_function(
        self, filter_condition: Optional[str] = None, output_alias: Optional[str] = None
    ) -> Column:
        func = self.function.spark_function(self.inputs, filter_condition)
        if self.time_window:
            func = func.over(
                self.time_window.spark_window(
                    self.source.entity_columns, self.source.order_column
                )
            )
        return func.alias(output_alias or self.name)

    def _to_yaml_dict(self) -> Dict[str, Any]:
        """Convert the feature to a dictionary that can be used to generate a YAML file."""
        yaml_dict = {
            self.INPUTS_FIELD_NAME: self.inputs,
            self.DATA_SOURCE_FIELD_NAME: self.source.full_name(),
            self.FUNCTION_FIELD_NAME: self.function._to_yaml_dict(),
            self.TIME_WINDOW_FIELD_NAME: self.time_window._to_yaml_dict(),
        }
        if self._filter_condition is not None:
            yaml_dict[self.FILTER_CONDITION_FIELD_NAME] = self._filter_condition
        return yaml_dict

    @classmethod
    def _from_yaml_dict(
        cls,
        feature_name: str,
        feature_dict: Dict[str, Any],
        data_source: DataSource,
    ) -> "Feature":
        """Create a Feature from a dictionary loaded from YAML."""
        # Parse the function
        func_dict = feature_dict[cls.FUNCTION_FIELD_NAME]
        function = Function._from_yaml_dict(
            func_dict["operator"], func_dict.get("extra_parameters")
        )

        # Parse the time window
        time_window = TimeWindow._from_yaml_dict(
            feature_dict[cls.TIME_WINDOW_FIELD_NAME]
        )

        # Extract catalog and schema from feature_name if it's qualified
        # For backward compatibility, assume default catalog/schema if not qualified
        if "." in feature_name:
            parts = feature_name.split(".")
            if len(parts) == 3:
                catalog_name, schema_name, base_name = parts
            elif len(parts) == 2:
                # Assume default catalog for 2-level names
                catalog_name = "main"  # Default catalog
                schema_name, base_name = parts
            else:
                raise ValueError(f"Invalid feature name format: {feature_name}")
        else:
            # Unqualified name, use defaults
            catalog_name = "main"  # Default catalog
            schema_name = "default"  # Default schema
            base_name = feature_name

        return cls(
            name=base_name,
            catalog_name=catalog_name,
            schema_name=schema_name,
            source=data_source,
            inputs=feature_dict[cls.INPUTS_FIELD_NAME],
            function=function,
            time_window=time_window,
            filter_condition=feature_dict.get(cls.FILTER_CONDITION_FIELD_NAME),
        )

    def _to_sdk_feature(self) -> SDKFeature:
        return SDKFeature(
            full_name=self.full_name,
            source=self.source._to_sdk_data_source(),
            inputs=self.inputs,
            function=self.function._to_sdk_function(),
            time_window=self.time_window._to_sdk_time_window(),
            description=self.description,
            filter_condition=self.filter_condition,
        )

    @classmethod
    def _from_sdk_feature(cls, sdk_feature: SDKFeature) -> "Feature":
        if not isinstance(sdk_feature, SDKFeature):
            raise TypeError(
                f"Expected databricks.sdk.service.ml.Feature, got {type(sdk_feature).__name__}"
            )
        if sdk_feature.full_name is None:
            raise ValueError("SDK Feature must include 'full_name'")
        catalog_name, schema_name, name = cls._parse_full_name(sdk_feature.full_name)
        return cls(
            source=cls._from_sdk_data_source(sdk_feature.source),
            inputs=list(sdk_feature.inputs) if sdk_feature.inputs else [],
            function=cls._from_sdk_function(sdk_feature.function),
            time_window=cls._from_sdk_time_window(sdk_feature.time_window),
            catalog_name=catalog_name,
            schema_name=schema_name,
            name=name,
            description=sdk_feature.description,
            filter_condition=sdk_feature.filter_condition,
        )

    @staticmethod
    def _parse_full_name(full_name: str) -> tuple[str, str, str]:
        parts = full_name.split(".")
        if len(parts) != 3:
            raise ValueError(
                f"Expected fully qualified feature name '<catalog>.<schema>.<name>', got '{full_name}'"
            )
        return parts[0], parts[1], parts[2]

    @staticmethod
    def _from_sdk_data_source(sdk_source: SDKDataSource) -> DataSource:
        return DataSource._from_sdk_data_source(sdk_source)

    @staticmethod
    def _from_sdk_function(sdk_function: SDKFunction) -> Function:
        return Function._from_sdk_function(sdk_function)

    @staticmethod
    def _from_sdk_time_window(sdk_time_window: SDKTimeWindow) -> TimeWindow:
        return TimeWindow._from_sdk_time_window(sdk_time_window)

    def __str__(self) -> str:
        """Return a concise string representation of the feature."""
        inputs_str = ", ".join(self._inputs)
        filter_str = (
            f" [filter={self._filter_condition}]" if self._filter_condition else ""
        )
        return f"{self.name}: {self._function}({inputs_str}) OVER {self._time_window}{filter_str}"

    def __repr__(self) -> str:
        """Return a detailed string representation of the feature."""
        return (
            f"Feature(name={self.full_name!r}, "
            f"source={self._source!r}, "
            f"inputs={self._inputs!r}, "
            f"function={self._function!r}, "
            f"time_window={self._time_window!r}, "
            f"filter_condition={self._filter_condition!r})"
        )
