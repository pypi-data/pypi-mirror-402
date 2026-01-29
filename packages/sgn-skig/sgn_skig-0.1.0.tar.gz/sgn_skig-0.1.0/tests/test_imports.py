"""Basic import tests for sgneskig package."""


def test_imports():
    """Verify all main components can be imported."""
    from sgneskig import MetricsPipeline
    from sgneskig.metrics import (
        GrafanaExporter,
        MetricDeclaration,
        MetricsCollectorMixin,
        MetricsWriter,
        metrics,
    )
    from sgneskig.sinks import KafkaSink
    from sgneskig.sources import KafkaSource
    from sgneskig.transforms import DelayBuffer, EventLatency, RoundRobinDistributor

    # Verify they're not None
    assert MetricsPipeline is not None
    assert MetricsCollectorMixin is not None
    assert MetricsWriter is not None
    assert GrafanaExporter is not None
    assert MetricDeclaration is not None
    assert metrics is not None
    assert KafkaSource is not None
    assert KafkaSink is not None
    assert DelayBuffer is not None
    assert EventLatency is not None
    assert RoundRobinDistributor is not None
