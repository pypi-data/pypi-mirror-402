ENABLE_EXPERIMENTAL_MATERIALIZATION_API = False

# Feature flag to enable optimized aggregation query generation
# When True, generates a single CTE with conditional aggregations (1 table scan)
# When False, generates N separate CTEs with N table scans (legacy behavior)
ENABLE_OPTIMIZED_FEATURE_AGGREGATION_PIPELINES = False
