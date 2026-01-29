"""SGN-SKIG: SGN infrastructure for Scald, Kafka, InfluxDB, and Grafana.

Provides reusable metrics collection, pipeline infrastructure, and
generic transforms/sinks/sources for SGN pipelines.
"""

from sgneskig.pipeline import MetricsPipeline

try:
    from sgneskig._version import __version__
except ModuleNotFoundError:
    __version__ = "0.0.0"

__all__ = ["MetricsPipeline", "__version__"]
