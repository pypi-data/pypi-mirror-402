"""Generic sinks for SGN pipelines."""

from sgneskig.sinks.kafka_sink import KafkaSink
from sgneskig.sinks.scald_metrics_sink import ScaldMetricsSink

__all__ = ["KafkaSink", "ScaldMetricsSink"]
