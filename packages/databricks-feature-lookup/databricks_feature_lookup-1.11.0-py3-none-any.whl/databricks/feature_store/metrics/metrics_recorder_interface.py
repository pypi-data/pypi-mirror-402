"""
Abstract metrics recording interface for feature store lookup client.

This module defines the interface but has ZERO dependencies on any metrics
backend (Prometheus). Implementations are provided by the runtime environment.

TODO: Ideally, this should be a library shared with model serving so there is a 
clear contract. Right now, scoring server just assumes the APIs are provided.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class MetricsRecorder(ABC):
    """
    Abstract interface for metrics recording.

    The lookup client emits metrics by calling methods on this interface.
    The runtime environment (model server, notebook, Lambda) provides
    the concrete implementation.
    """

    @abstractmethod
    def record_counter(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a counter metric (monotonically increasing).

        :param name: Metric name (e.g., "databricks.feature_store.lookup.count")
        :param value: Value to add to counter
        :param labels: Label dimensions (e.g., {"table": "users", "status": "success"})
        """
        pass

    @abstractmethod
    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a histogram metric (for latency, size, etc.).

        Histograms buckets are defined by model server (go/model-serving-metric-buckets).
        The latency metrics are estimated from the buckets with acceptable errors. See
        https://prometheus.io/docs/practices/histograms/#quantiles for how quantiles can
        be estimated.

        :param name: Metric name (e.g., "feature_lookup_client_feature_store_latency_ms")
        :param value: Observed value (e.g., latency in milliseconds)
        :param labels: Label dimensions (e.g., {"table": "users"})
        """
        pass


class _NoOpRecorder(MetricsRecorder):
    """
    No-op implementation used when no recorder is registered.

    This ensures zero overhead when metrics are disabled or in
    environments that don't support metrics (notebooks, local dev).
    """

    def record_counter(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        pass

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        pass
