"""
Global registry for metrics recorder implementations.

This module manages the Feature Store metrics recorder lifecycle:
1. During initialization, model server/serving scheduler registers their metrics
   implementation (e.g., PrometheusMetricsRecorder) via register_metrics_recorder()
2. The lookup client retrieves the recorder via get_metrics_recorder() to emit metrics
3. The recorder wraps the implementation with a Feature Store-specific prefix

Thread safety: The global recorder is shared across all greenlets in the same process.
This is initialized once during worker startup (post_fork hook in model server) and
remains constant for the worker's lifetime.

No-op fallback: If no recorder is registered, a _NoOpRecorder is used to ensure
zero overhead in environments without metrics support (notebooks, local dev).
"""

import os
from typing import Dict, Optional

from databricks.feature_store.feature_lookup_version import VERSION
from databricks.feature_store.metrics.metrics_recorder_interface import (
    MetricsRecorder,
    _NoOpRecorder,
)
from databricks.feature_store.utils.lookup_client_envvars import (
    ENABLE_FEATURE_LOOKUP_METRICS_RECORDER_ENV,
)

# Singleton no-op recorder instance used as the default when no metrics are configured.
# Ensures zero overhead in environments without metrics support (notebooks, local dev).
_NOOP_RECORDER = _NoOpRecorder()

# Global metrics recorder shared across all greenlets in the same process.
# Initialized once during worker startup (via register_metrics_recorder) and remains
# constant for the worker's lifetime. Defaults to _NOOP_RECORDER until explicitly set.
# Thread safety: This is set once at initialization and then only read, avoiding race conditions.
_GLOBAL_RECORDER: MetricsRecorder = _NOOP_RECORDER


# Metric prefix. All metric names will be prefixed with this.
METRICS_PREFIX = "feature_lookup_client_"

# ==== Metrics definitions ====
# Latency added by lookup client. It doesn't include the latency of the raw model's prediction.
# This is measured from the time when lookup client logic receives the request to the time
# BEFORE calling the raw model predict method.
METRIC_FEATURE_STORE_LATENCY = METRICS_PREFIX + "feature_store_latency_ms"
# Latency measured for the raw model predict.
# feature_store_latency_ms + raw_model_predict_latency_ms = prediction_latency measured
# by the scoring server.
METRIC_RAW_MODEL_PREDICT_LATENCY = METRICS_PREFIX + "raw_model_predict_latency_ms"
# Postgres query latency. This is a histogram of latency for each individual query to the Postgres
# database. It does not include the acquisition of a connection to the database. Each request may
# involve multiple Postgres queries.
METRIC_POSTGRES_QUERY_LATENCY = METRICS_PREFIX + "postgres_query_latency_ms"
# Connection latency. This is the latency of acquiring a connection to the Postgres database.
METRIC_POSTGRES_CONNECTION_ACQUISITION_LATENCY = (
    METRICS_PREFIX + "postgres_connection_acquisition_latency_ms"
)
# Errors in Feature Store.
METRIC_FEATURE_STORE_ERROR_COUNT = METRICS_PREFIX + "feature_store_error_count"

# === Label definitions ====
# Lookup client version
METRIC_LABEL_LOOKUP_CLIENT_VERSION = "lookup_client_version"
# Online store type. Values are defined in databricks.ml_features_common.entities.store_type
METRIC_LABEL_ONLINE_STORE_TYPE = "online_store_type"
# Label indicating the source of the error. Values are "raw_model" or "feature_lookup".
METRIC_LABEL_ERROR_SOURCE = "error_source"


class FeatureStoreMetricsRecorder:
    """
    Wrapper around a MetricsRecorder that adds Feature Store-specific prefixes.

    This class wraps the runtime-provided metrics recorder (e.g., PrometheusMetricsRecorder)
    and guards the recording of metrics by the ENABLE_FEATURE_LOOKUP_METRICS_RECORDER_ENV
    environment variable.
    """

    def __init__(self, metrics_recorder: MetricsRecorder):
        """
        Initialize the Feature Store metrics recorder wrapper.

        :param metrics_recorder: The underlying MetricsRecorder implementation to wrap
        """
        self.base_labels = {
            METRIC_LABEL_LOOKUP_CLIENT_VERSION: VERSION,
        }
        self._metrics_recorder = metrics_recorder
        self._metrics_recorder_flag_enabled = (
            os.getenv(ENABLE_FEATURE_LOOKUP_METRICS_RECORDER_ENV) == "true"
        )

    def record_counter(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a counter metric (monotonically increasing value).

        :param name: Metric name without prefix (e.g., "function_execution_count")
        :param value: Value to add to the counter (typically 1)
        :param labels: Optional label dimensions (e.g., {"table": "users", "status": "success"})
        """
        if not self._metrics_recorder_flag_enabled:
            return
        all_labels = {**self.base_labels, **(labels or {})}
        self._metrics_recorder.record_counter(name, value, all_labels)

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram metric (for distributions of values).

        :param name: Metric name without prefix (e.g., "postgres_query_latency_ms")
        :param value: Observed value (e.g., latency in milliseconds, payload size in bytes)
        :param labels: Optional label dimensions (e.g., {"table": "users", "source": "online_store"})
        """
        if not self._metrics_recorder_flag_enabled:
            return
        all_labels = {**self.base_labels, **(labels or {})}
        self._metrics_recorder.record_histogram(name, value, all_labels)


def register_metrics_recorder(recorder: MetricsRecorder):
    """
    Register a metrics recorder implementation.

    Model scoring server detects the existence of this method and uses it to register the recorder.
    This is called during worker initialization (post_fork hook) after the Feature Store wrapper
    model is initialized. The recorder is stored in a global variable.

    :param recorder: Implementation of MetricsRecorder (e.g., PrometheusMetricsRecorder)
    """
    global _GLOBAL_RECORDER
    wrapped_recorder = FeatureStoreMetricsRecorder(recorder)
    _GLOBAL_RECORDER = wrapped_recorder


def get_metrics_recorder() -> MetricsRecorder:
    """
    Get the current metrics recorder.

    Returns no-op recorder if none registered.

    :return: MetricsRecorder implementation or _NoOpRecorder
    """
    return _GLOBAL_RECORDER
