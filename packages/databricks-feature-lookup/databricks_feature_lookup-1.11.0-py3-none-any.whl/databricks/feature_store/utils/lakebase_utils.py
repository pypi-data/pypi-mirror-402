import os

from databricks.feature_store.utils.lookup_client_envvars import (
    FEATURE_SERVING_CONNECTION_POOL_SIZE,
)

# Setting a max connection pool size to avoid exhasusting all the connections on Lakebase.
# quickly. Each lakebase replica has a limit of 1000 connections. The maximum number of
# model serving concurrency supported is:
# (1000 * {number of Lakebase read replicas}) / ({connection pool size} * {number of logical databases})
# If provisioning concurrency higher than this, new pods cannot not start because of the connection limit.
DEFAULT_MAX_CONNECTION_POOL_SIZE = 10
# The minimum connection pool size 3 is tested with single table lookup use cases with
# for high throughput use cases for best availability.
DEFAULT_MIN_CONNECTION_POOL_SIZE = 3


def get_lakebase_connection_pool_size(number_of_tables: int) -> int:
    """
    Get the connection pool size for Lakebase PgSql.

    :param number_of_tables: The number of tables to lookup. This should be the
        number of tables that are looked up in parallel. In case of a DAG execution,
        this should be the biggest number of tables in one execution group.
    """
    if number_of_tables is None:
        raise Exception("number_of_tables is required for Lakebase PgSql connections.")
    if FEATURE_SERVING_CONNECTION_POOL_SIZE in os.environ:
        return int(os.environ[FEATURE_SERVING_CONNECTION_POOL_SIZE])
    else:
        return max(
            DEFAULT_MIN_CONNECTION_POOL_SIZE,
            min(DEFAULT_MAX_CONNECTION_POOL_SIZE, number_of_tables),
        )
