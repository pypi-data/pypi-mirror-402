# This file contains all the environment variables used by the lookup client.


# The provisioner of this model is expected to set an environment variable with the path to a
# feature_tables_for_serving.dat file.
# - Set by serving scheduler
FEATURE_TABLES_FOR_SERVING_FILEPATH_ENV = "FEATURE_TABLES_FOR_SERVING_FILEPATH"
# should match LOOKUP_CLIENT_FEATURE_FUNCTION_EVALUATION_ENABLED_ENV in
# model-serving/model-serving-common/src/main/scala/com/databricks/mlflow/utils/serving/FeatureStoreConstants.scala
# - Set by serving scheduler
LOOKUP_CLIENT_FEATURE_FUNCTION_EVALUATION_ENABLED_ENV = (
    "LOOKUP_CLIENT_FEATURE_FUNCTION_EVALUATION_ENABLED"
)
# Enable metrics recorder for feature lookup.
# should match ENABLE_FEATURE_LOOKUP_METRICS_RECORDER_ENV in
# model-serving/model-serving-common/src/main/scala/com/databricks/mlflow/utils/serving/FeatureStoreConstants.scala
# - Set by serving scheduler
ENABLE_FEATURE_LOOKUP_METRICS_RECORDER_ENV = "ENABLE_FEATURE_LOOKUP_METRICS_RECORDER"
# Enable debug logging. The lookup logic will print info logs in service logs with a break down of the latency numbers
# - Set by customers through environment variables config.
LOOKUP_PERFORMANCE_DEBUG_ENABLED = "LOOKUP_PERFORMANCE_DEBUG_ENABLED"
# Env var to tell if the served entity is a Model or a FeatureSpec
# - Set by serving scheduler
ENV_SERVABLE_TYPE = "SERVABLE_TYPE"
# If set to true, postgres connection is allowed.
# Note that the actual eligibility is determined by the features used.
# - Set by customers through environment variables config.
FEATURE_SERVING_HP = "FEATURE_SERVING_HP"
# FEATURE_SERVING_CONNECTION_POOL_SIZE overrides the default connection pool size
# calculated by the utils in lakebase_utils.py, giving the backend or users the
# opportunity to tune the connection pool size for their use cases.
# - Set by serving scheduler but not used yet in Dec 2025.
FEATURE_SERVING_CONNECTION_POOL_SIZE = "FEATURE_SERVING_CONNECTION_POOL_SIZE"
# Engine configurations
# - Set by serving scheduler but not used yet in Dec 2025.
DISABLE_CONNECTION_POOL = "DISABLE_CONNECTION_POOL"
# Whether to disable autocommit for Lakebase connections.
# This is not expected to be set by users or backend. But we keep it here as a
# kill switch.
DISABLE_AUTOCOMMIT = "FEATURE_SERVING_DISABLE_AUTOCOMMIT"

######## Dynamic environment variables #########
# Some secrets related environment variables names are constructed dynamically in
# feature-store/lookup-client/python/databricks/feature_store/online_lookup_client.py
# with certain suffixes. For example:
# _USER
# _PASSWORD
# _ACCESS_KEY_ID
# _SECRET_ACCESS_KEY
# _AUTHORIZATION_KEY

####### Deprecated environment variables ########

# The following environment variable names are deprecated in previouse versions
# Do not use them in new code because it may conflict with old version lookup
# clients that are still running in production.
# Note: they are env var names, not Python constant variable names.

# 1. LOOKUP_CLIENT_INSTRUMENTATION_ENABLED
# 2. ENABLE_LOOKUP_CLIENT_INSTRUMENTATION
