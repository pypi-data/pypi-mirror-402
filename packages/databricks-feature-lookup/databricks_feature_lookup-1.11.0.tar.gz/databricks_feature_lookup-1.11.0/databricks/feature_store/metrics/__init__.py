"""
Metrics recording system for Feature Store lookup client.

This module provides a pluggable metrics interface that allows the Feature Store
lookup client to emit operational metrics (latency, count, errors) to model server.

The metrics system uses a global registry pattern:
- Runtime environments (model server, serving scheduler) register their metrics
  implementation via `register_metrics_recorder()`
- The lookup client retrieves the recorder via `get_metrics_recorder()` to emit metrics
- If no recorder is registered, a no-op implementation is used (zero overhead)

Typical usage in model server:
    from databricks.feature_store.metrics import register_metrics_recorder
    register_metrics_recorder(PrometheusMetricsRecorder())

Typical usage in lookup client:
    from databricks.feature_store.metrics import get_metrics_recorder
    recorder = get_metrics_recorder()
    recorder.record_histogram("lookup_latency", latency_ms, {"is_postgres": "true"})
"""

from databricks.feature_store.metrics.feature_store_metrics_recorder import (
    get_metrics_recorder,
    register_metrics_recorder,
)

__all__ = ["register_metrics_recorder", "get_metrics_recorder"]
