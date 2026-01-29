import logging
from typing import Any, Dict, Optional

import mlflow
from mlflow.models import ModelSignature
from mlflow.types import ColSpec
from mlflow.types import DataType as MlflowDataType
from mlflow.types import ParamSchema, Schema

from databricks.ml_features_common.entities.feature_column_info import FeatureColumnInfo
from databricks.ml_features_common.entities.feature_spec import FeatureSpec
from databricks.ml_features_common.entities.feature_spec_declarative import (
    FeatureSpecDeclarative,
)
from databricks.ml_features_common.entities.on_demand_column_info import (
    OnDemandColumnInfo,
)
from databricks.ml_features_common.entities.source_data_column_info import (
    SourceDataColumnInfo,
)

_logger = logging.getLogger(__name__)

# Some types (array, map, decimal, timestamp_ntz) are unsupported due to MLflow signatures
# lacking any equivalent types. We thus cannot construct a ColSpec for any column
# that uses these types.
SUPPORTED_TYPE_MAP = {
    "smallint": MlflowDataType.integer,  # Upcast to integer
    "int": MlflowDataType.integer,
    "bigint": MlflowDataType.long,
    "float": MlflowDataType.float,
    "double": MlflowDataType.double,
    "boolean": MlflowDataType.boolean,
    "date": MlflowDataType.datetime,
    "timestamp": MlflowDataType.datetime,
    "string": MlflowDataType.string,
    "binary": MlflowDataType.binary,
}


def is_unsupported_type(type_str: str):
    return type_str not in SUPPORTED_TYPE_MAP


def convert_spark_data_type_to_mlflow_signature_type(spark_type):
    """
    Maps Databricks SQL types to MLflow signature types.
    docs.databricks.com/sql/language-manual/sql-ref-datatypes.html#language-mappings
    """
    return SUPPORTED_TYPE_MAP.get(spark_type)


def get_input_schema_from_feature_spec_declarative(
    feature_spec: FeatureSpecDeclarative,
) -> Schema:
    """
    Produces an MLflow signature schema from a FeatureSpecDeclarative.

    Only the entity columns from the sources of the declarative features are marked as
    required inputs. All other source data columns are marked as optional inputs.

    :param feature_spec: FeatureSpecDeclarative with datatypes for each column.
    """
    # Note: We currently support serving only models that depend only on declarative features.
    # We do not support serving models trained on additional columns.
    # TO-DO [FS-444]: Support request-time features in model signature.

    # If we're missing any data types for any column, we are likely dealing with a
    # malformed feature spec and should halt signature construction.
    missing_type_cols = [ci for ci in feature_spec.column_infos if ci.data_type is None]
    if missing_type_cols:
        cols_string = ", ".join(ci.info.output_name for ci in missing_type_cols)
        raise Exception(
            f"Training set does not contain column data types for the following columns: {cols_string}."
        )

    source_data_cols = [
        ci
        for ci in feature_spec.column_infos
        if isinstance(ci.info, SourceDataColumnInfo)
    ]

    # Only entity key columns are required inputs.
    required_col_names = set()
    for feature in feature_spec.features:
        required_col_names.update(feature.source.entity_columns)

    input_colspecs = []
    unsupported_source_data_cols = []
    for ci in source_data_cols:
        col_name = ci.info.output_name

        # If any required input has an unsupported type, fail signature construction.
        # If any optional input has an unsupported type, omit it from the signature.
        # TO-DO [FS-443]: Support complex types in signature of model logged with declarative features.
        if is_unsupported_type(ci.data_type):
            if col_name in required_col_names:
                raise Exception(
                    "Input DataFrame contains column data types not supported by "
                    "MLflow model signatures."
                )
            unsupported_source_data_cols.append(ci)
            continue

        input_colspecs.append(
            ColSpec(
                convert_spark_data_type_to_mlflow_signature_type(ci.data_type),
                col_name,
                required=(col_name in required_col_names),
            )
        )

    if unsupported_source_data_cols:
        cols_string = ", ".join(
            f"{ci.info.output_name} ({ci.data_type})"
            for ci in unsupported_source_data_cols
        )
        _logger.warning(
            "The following source data columns will not be included in the input schema "
            "because their data types are not supported by MLflow model signatures: "
            f"{cols_string}. These columns cannot be overridden during model serving."
        )

    return Schema(input_colspecs)


def get_input_schema_from_feature_spec(feature_spec: FeatureSpec) -> Schema:
    """
    Produces an MLflow signature schema from a FeatureSpec.

    Source data columns are marked as required inputs. Feature columns
    (both lookup and on-demand features) are marked as optional inputs.

    :param feature_spec: FeatureSpec with datatypes for each column.
    """
    # If we're missing any data types for any column, we are likely dealing with a
    # malformed feature spec and should halt signature construction.
    if any(ci.data_type is None for ci in feature_spec.column_infos):
        raise Exception("Training set does not contain column data types.")

    source_data_cols = [
        ci
        for ci in feature_spec.column_infos
        if isinstance(ci.info, SourceDataColumnInfo)
    ]
    # Don't create signature if any source data columns (required) are of complex types.
    if any(is_unsupported_type(ci.data_type) for ci in source_data_cols):
        raise Exception(
            "Input DataFrame contains column data types not supported by "
            "MLflow model signatures."
        )
    required_input_colspecs = [
        ColSpec(
            convert_spark_data_type_to_mlflow_signature_type(ci.data_type),
            ci.info.output_name,
            required=True,
        )
        for ci in source_data_cols
    ]
    feature_cols = [
        ci
        for ci in feature_spec.column_infos
        if isinstance(ci.info, (FeatureColumnInfo, OnDemandColumnInfo))
    ]
    unsupported_feature_cols = [
        ci for ci in feature_cols if is_unsupported_type(ci.data_type)
    ]
    optional_input_colspecs = [
        ColSpec(
            convert_spark_data_type_to_mlflow_signature_type(ci.data_type),
            ci.output_name,
            required=False,
        )
        for ci in feature_cols
        if not is_unsupported_type(ci.data_type)
    ]
    if unsupported_feature_cols:
        feat_string = ", ".join(
            f"{ci.output_name} ({ci.data_type})" for ci in unsupported_feature_cols
        )
        _logger.warning(
            f"The following features will not be included in the input schema because their"
            f" data types are not supported by MLflow model signatures: {feat_string}. "
            f"These features cannot be overridden during model serving."
        )
    return Schema(required_input_colspecs + optional_input_colspecs)


def get_output_schema_from_labels(label_type_map: Optional[Dict[str, str]]) -> Schema:
    """
    Produces an MLflow signature schema from the provided label type map.
    :param label_type_map: Map label column name -> data type
    """
    if not label_type_map:
        raise Exception("Training set does not contain a label.")
    if any(is_unsupported_type(dtype) for dtype in label_type_map.values()):
        raise Exception(
            "Labels are of data types not supported by MLflow model signatures."
        )
    else:
        output_colspecs = [
            ColSpec(
                convert_spark_data_type_to_mlflow_signature_type(spark_type),
                col_name,
                required=True,
            )
            for col_name, spark_type in label_type_map.items()
        ]
        return Schema(output_colspecs)


def get_mlflow_signature_from_feature_spec(
    feature_spec: FeatureSpec,
    label_type_map: Optional[Dict[str, str]],
    override_output_schema: Optional[Schema],
    params: Optional[Dict[str, Any]] = None,
) -> Optional[ModelSignature]:
    """
    Produces an MLflow model signature from a feature spec and label type map.

    Input schema is inferred by the feature spec type:

    - FeatureSpecDeclarative:
        Only the entity columns from the sources of the declarative features
        are required inputs. All other source data columns are optional inputs.

    - FeatureSpec:
        Source data columns are required inputs. Feature columns (both lookup
        and on-demand features) are optional inputs.

    Output schema is inferred from the cached label -> datatype map in the training set
    unless an override output schema is provided.

    :param feature_spec: FeatureSpec or FeatureSpecDeclarative with datatypes for each column.
    :param label_type_map: Map of label column name -> datatype
    :param override_output_schema: User-provided output schema to use if provided.
    """
    kwargs = {}
    if isinstance(feature_spec, FeatureSpecDeclarative):
        kwargs["inputs"] = get_input_schema_from_feature_spec_declarative(feature_spec)
    elif isinstance(feature_spec, FeatureSpec):
        kwargs["inputs"] = get_input_schema_from_feature_spec(feature_spec)
    else:
        raise ValueError(f"Unsupported feature spec type: {type(feature_spec)}")

    try:
        output_schema = override_output_schema or get_output_schema_from_labels(
            label_type_map
        )
        kwargs["outputs"] = output_schema
    except Exception as e:
        _logger.warning(f"Could not infer an output schema: {e}")

    if params:
        try:
            from mlflow.types.utils import _infer_param_schema

            kwargs["params"] = _infer_param_schema(params)
        except Exception as e:
            _logger.warning(f"Could not infer params schema: {e}")

    return mlflow.models.ModelSignature(**kwargs)


def drop_signature_inputs_and_invalid_params(signature):
    """
    Drop ModelSignature inputs field and invalid params from params field.
    This is useful for feature store model's raw_model.
    Feature store model's input schema does not apply to raw_model's input,
    so we drop the inputs field of raw_model's signature.
    Feature store model's result_type param enables setting and overriding
    a default result_type for predictions, but this interferes with params
    passed to MLflow's predict function, so we drop result_type from
    the params field of raw_model's signature.

    :param signature: ModelSignature object.
    """
    if signature:
        outputs_schema = signature.outputs
        params_schema = signature.params if hasattr(signature, "params") else None
        try:
            # Only for mlflow>=2.6.0 ModelSignature contains params attribute
            if params_schema:
                # Note: This looks like a potential bug if users intentially add "result_type" in
                # params.
                updated_params_schema = ParamSchema(
                    [param for param in params_schema if param.name != "result_type"]
                )
                return ModelSignature(
                    outputs=outputs_schema, params=updated_params_schema
                )
            if outputs_schema:
                return ModelSignature(outputs=outputs_schema)
        except TypeError:
            _logger.warning(
                "ModelSignature without inputs is not supported, please upgrade "
                "mlflow >= 2.7.0 to use the feature."
            )
