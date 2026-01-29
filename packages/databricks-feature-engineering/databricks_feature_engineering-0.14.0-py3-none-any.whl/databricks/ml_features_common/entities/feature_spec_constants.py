# Field names from feature_spec.proto.
SOURCE_DATA_COLUMN_INFO = "source_data_column_info"
FEATURE_COLUMN_INFO = "feature_column_info"
ON_DEMAND_COLUMN_INFO = "on_demand_column_info"
INPUT_COLUMNS = "input_columns"
NAME = "name"
OUTPUT_NAME = "output_name"
INPUT_TABLES = "input_tables"
TABLE_NAME = "table_name"
TABLE_ID = "table_id"
SERIALIZATION_VERSION = "serialization_version"
FEATURE_STORE_CLIENT_VERSION_FIELD_NAME = "feature_store_client_version"
INPUT_FUNCTIONS = "input_functions"
INCLUDE = "include"
DATA_TYPE = "data_type"
TOPOLOGICAL_ORDERING = "topological_ordering"
UDF_NAME = "udf_name"
INPUT_BINDINGS = "input_bindings"
PARAMETER = "parameter"
BOUND_TO = "bound_to"
WORKSPACE_ID_FIELD_NAME = "workspace_id"
FEATURES_FIELD_NAME = "features"

# FeatureSpec YAML fields not defined in the proto file:
# These fields do not exist in the proto file because they only exist in
# the python logic and are not serialized.
SOURCE = "source"
TRAINING_DATA = "training_data"
FEATURE_STORE = "feature_store"
ON_DEMAND_FEATURE = "on_demand_feature"

# FeatureSpec YAML field for data sources
DATA_SOURCES_FIELD_NAME = "data_sources"
