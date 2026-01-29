from databricks.ml_features.entities.data_type import DataType

OVERWRITE = "overwrite"
MERGE = "merge"
PATH = "path"
TABLE = "table"
CUSTOM = "custom"
PREDICTION_COLUMN_NAME = "prediction"
MODEL_DATA_PATH_ROOT = "feature_store"
UTF8_BYTES_PER_CHAR = 4
MAX_PRIMARY_KEY_STRING_LENGTH_CHARS = 100
MAX_PRIMARY_KEY_STRING_LENGTH_BYTES = (
    MAX_PRIMARY_KEY_STRING_LENGTH_CHARS * UTF8_BYTES_PER_CHAR
)
COMPLEX_DATA_TYPES = [DataType.ARRAY, DataType.MAP, DataType.STRUCT]
DATA_TYPES_REQUIRES_DETAILS = COMPLEX_DATA_TYPES + [DataType.DECIMAL]
STREAMING_TRIGGER_CONTINUOUS = "continuous"
STREAMING_TRIGGER_ONCE = "once"
STREAMING_TRIGGER_PROCESSING_TIME = "processingTime"
_DEFAULT_WRITE_STREAM_TRIGGER = {STREAMING_TRIGGER_PROCESSING_TIME: "5 seconds"}
_DEFAULT_PUBLISH_STREAM_TRIGGER = {STREAMING_TRIGGER_PROCESSING_TIME: "5 minutes"}

_WARN = "WARN"
_ERROR = "ERROR"
_SOURCE_FORMAT_DELTA = "delta"

_USE_SPARK_NATIVE_JOIN = "use_spark_native_join"
_PREBUILT_ENV_URI = "prebuilt_env_uri"

_FEATURE_ENGINEERING_COMPUTATION_PRECISION = 1e-6
_FEATURE_ENGINEERING_COMPUTATION_WINDOW_START_INCLUSIVE = True
_FEATURE_ENGINEERING_COMPUTATION_WINDOW_END_INCLUSIVE = False

# Maximum number of sliding window boundaries to generate for PIT feature computation
# This prevents memory issues when training data spans large time ranges with small slide durations
# Can consider bumping up limit if benchmarking shows it's doable
_PIT_MAX_SLIDING_WINDOW_BOUNDARY_COUNT = 100_000

# Precision factor for microsecond-level time computations
_PRECISION_FACTOR = (
    int(1 / _FEATURE_ENGINEERING_COMPUTATION_PRECISION)
    if _FEATURE_ENGINEERING_COMPUTATION_PRECISION != 0
    else 1
)

# Databricks online store publish modes
PUBLISH_MODE_CONTINUOUS = "CONTINUOUS"
PUBLISH_MODE_SNAPSHOT = "SNAPSHOT"
PUBLISH_MODE_TRIGGERED = "TRIGGERED"
