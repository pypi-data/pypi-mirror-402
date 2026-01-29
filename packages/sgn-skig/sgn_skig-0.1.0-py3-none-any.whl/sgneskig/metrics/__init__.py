"""Metrics collection framework for SGN pipelines.

Provides reusable components for collecting timing and count metrics
from SGN pipeline elements and sending them to InfluxDB.

Two modes of metric emission are supported:
- "direct" (default): Write directly to InfluxDB via shared MetricsWriter
- "pad": Emit through output pad for downstream processing (legacy)
"""

from sgneskig.metrics.collector import (
    MetricDeclaration,
    MetricPoint,
    MetricsCollectorMixin,
    metrics,
)
from sgneskig.metrics.grafana import GrafanaExporter
from sgneskig.metrics.writer import MetricsWriter

__all__ = [
    "MetricDeclaration",
    "MetricPoint",
    "MetricsCollectorMixin",
    "MetricsWriter",
    "GrafanaExporter",
    "metrics",
]
