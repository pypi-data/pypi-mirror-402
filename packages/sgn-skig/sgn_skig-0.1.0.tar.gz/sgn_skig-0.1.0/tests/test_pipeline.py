"""Tests for sgneskig.pipeline module."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock, patch

import yaml

from sgneskig.metrics.collector import MetricDeclaration, MetricsCollectorMixin, metrics
from sgneskig.pipeline import MetricsPipeline


@dataclass
class MockMetricsElement(MetricsCollectorMixin):
    """Mock element with metrics for testing."""

    name: str = "mock_element"
    metrics_enabled: bool = True
    metrics_mode: str = "direct"
    track_elapsed_time: bool = False
    elapsed_metric_name: str | None = None

    metrics_schema: ClassVar = metrics(
        [
            ("process_time", "timing", [], "Processing time"),
            ("events_count", "counter", ["type"], "Event count"),
        ]
    )

    source_pad_names: list = None
    sink_pad_names: list = None

    def __post_init__(self):
        self._init_metrics()
        if self.source_pad_names is None:
            self.source_pad_names = ["out"]
        if self.sink_pad_names is None:
            self.sink_pad_names = ["in"]


@dataclass
class MockDynamicMetricsElement(MetricsCollectorMixin):
    """Mock element with dynamic metrics (instance-level schema)."""

    name: str = "dynamic_element"
    metric_name: str = "custom_latency"
    metrics_enabled: bool = True
    metrics_mode: str = "direct"
    track_elapsed_time: bool = False
    elapsed_metric_name: str | None = None

    source_pad_names: list = None
    sink_pad_names: list = None

    def __post_init__(self):
        self._init_metrics()
        # Instance-level schema (dynamic)
        self._metrics_schema = [
            MetricDeclaration(
                name=self.metric_name,
                metric_type="timing",
                tags=["source"],
                description=f"Custom metric: {self.metric_name}",
            )
        ]
        if self.source_pad_names is None:
            self.source_pad_names = ["out"]
        if self.sink_pad_names is None:
            self.sink_pad_names = ["in"]


@dataclass
class MockNonMetricsElement:
    """Mock element without metrics capabilities."""

    name: str = "non_metrics_element"
    source_pad_names: list = None
    sink_pad_names: list = None

    def __post_init__(self):
        if self.source_pad_names is None:
            self.source_pad_names = ["out"]
        if self.sink_pad_names is None:
            self.sink_pad_names = ["in"]


def create_mock_pipeline(**kwargs):
    """Create a MetricsPipeline with mocked MetricsWriter."""
    with patch("sgneskig.metrics.writer.MetricsWriter") as mock_writer_class:
        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer
        pipeline = MetricsPipeline(**kwargs)
        return pipeline, mock_writer


class TestMetricsPipelineInit:
    """Tests for MetricsPipeline initialization."""

    @patch("sgneskig.metrics.writer.MetricsWriter")
    def test_initialization(self, mock_writer_class):
        """Test MetricsPipeline initializes correctly."""
        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer

        pipeline = MetricsPipeline(
            name="test-pipeline",
            influxdb_host="influxdb",
            influxdb_port=8086,
            influxdb_db="test_db",
        )

        assert pipeline.name == "test-pipeline"
        assert pipeline.influxdb_host == "influxdb"
        assert pipeline.influxdb_db == "test_db"
        mock_writer_class.assert_called_once()

    @patch("sgneskig.metrics.writer.MetricsWriter")
    def test_default_values(self, mock_writer_class):
        """Test default configuration values."""
        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer

        pipeline = MetricsPipeline()

        assert pipeline.name == "sgneskig-pipeline"
        assert pipeline.influxdb_host == "localhost"
        assert pipeline.influxdb_port == 8086
        assert pipeline.influxdb_db == "sgneskig_metrics"
        assert pipeline.grafana_influxdb_url == "http://influxdb:8086"
        assert pipeline.metrics_dry_run is False

    @patch("sgneskig.metrics.writer.MetricsWriter")
    def test_dry_run_mode(self, mock_writer_class):
        """Test dry_run mode is passed to MetricsWriter."""
        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer

        MetricsPipeline(metrics_dry_run=True)

        call_kwargs = mock_writer_class.call_args[1]
        assert call_kwargs["dry_run"] is True


class TestMetricsPipelineInsert:
    """Tests for insert method."""

    def test_insert_configures_metrics_writer(self):
        """Test insert configures MetricsWriter for metrics elements."""
        pipeline, mock_writer = create_mock_pipeline()
        element = MockMetricsElement()

        # Mock parent insert to avoid SGN element validation
        with patch("sgn.apps.Pipeline.insert"):
            pipeline.insert(element)

        assert element._metrics_writer is mock_writer

    def test_insert_skips_non_metrics_elements(self):
        """Test insert skips elements without MetricsCollectorMixin."""
        pipeline, mock_writer = create_mock_pipeline()
        element = MockNonMetricsElement()

        # Mock parent insert to avoid SGN element validation
        with patch("sgn.apps.Pipeline.insert"):
            # Should not raise
            pipeline.insert(element)

        # Non-metrics element doesn't have set_metrics_writer
        assert not hasattr(element, "_metrics_writer")


class TestMetricsPipelineClose:
    """Tests for close method."""

    def test_close_flushes_writer(self):
        """Test close flushes and closes MetricsWriter."""
        pipeline, mock_writer = create_mock_pipeline()

        pipeline.close()

        mock_writer.close.assert_called_once()


class TestMetricsPipelineGetMetricsSchema:
    """Tests for get_metrics_schema method."""

    def test_get_metrics_schema_class_level(self):
        """Test get_metrics_schema collects class-level metrics."""
        pipeline, _ = create_mock_pipeline()
        element = MockMetricsElement()
        pipeline.elements.append(element)

        schema = pipeline.get_metrics_schema()

        assert len(schema) == 2
        metric_names = {m.name for m in schema}
        assert "process_time" in metric_names
        assert "events_count" in metric_names

    def test_get_metrics_schema_instance_level(self):
        """Test get_metrics_schema collects instance-level metrics."""
        pipeline, _ = create_mock_pipeline()
        element = MockDynamicMetricsElement(metric_name="my_latency")
        pipeline.elements.append(element)

        schema = pipeline.get_metrics_schema()

        assert len(schema) == 1
        assert schema[0].name == "my_latency"

    def test_get_metrics_schema_deduplicates(self):
        """Test get_metrics_schema deduplicates metrics."""
        pipeline, _ = create_mock_pipeline()
        element1 = MockMetricsElement(name="element1")
        element2 = MockMetricsElement(name="element2")  # Same schema
        pipeline.elements.extend([element1, element2])

        schema = pipeline.get_metrics_schema()

        # Should dedupe by (name, tags)
        assert len(schema) == 2

    def test_get_metrics_schema_skips_non_metrics(self):
        """Test get_metrics_schema skips non-metrics elements."""
        pipeline, _ = create_mock_pipeline()
        element1 = MockMetricsElement()
        element2 = MockNonMetricsElement()
        pipeline.elements.extend([element1, element2])

        schema = pipeline.get_metrics_schema()

        # Only metrics from element1
        assert len(schema) == 2


class TestMetricsPipelineGetMetricsElements:
    """Tests for get_metrics_elements method."""

    def test_get_metrics_elements(self):
        """Test get_metrics_elements returns metrics-capable elements."""
        pipeline, _ = create_mock_pipeline()
        element1 = MockMetricsElement(name="metrics1")
        element2 = MockNonMetricsElement(name="non_metrics")
        element3 = MockMetricsElement(name="metrics2")
        pipeline.elements.extend([element1, element2, element3])

        result = pipeline.get_metrics_elements()

        assert len(result) == 2
        assert element1 in result
        assert element3 in result
        assert element2 not in result


class TestMetricsPipelineGetMetricsByElement:
    """Tests for get_metrics_by_element method."""

    def test_get_metrics_by_element(self):
        """Test get_metrics_by_element groups metrics."""
        pipeline, _ = create_mock_pipeline()
        element1 = MockMetricsElement(name="element1")
        element2 = MockDynamicMetricsElement(name="element2", metric_name="latency")
        pipeline.elements.extend([element1, element2])

        result = pipeline.get_metrics_by_element()

        assert "element1" in result
        assert "element2" in result
        assert len(result["element1"]) == 2
        assert len(result["element2"]) == 1


class TestMetricsPipelineManifest:
    """Tests for manifest generation."""

    def test_metrics_manifest(self):
        """Test metrics_manifest generates correct structure."""
        pipeline, _ = create_mock_pipeline(
            name="test-pipeline",
            influxdb_host="influxdb",
            influxdb_port=8086,
            influxdb_db="test_db",
            grafana_influxdb_url="http://grafana:8086",
        )
        element = MockMetricsElement()
        pipeline.elements.append(element)
        pipeline._registry[element.name] = element

        manifest = pipeline.metrics_manifest()

        assert manifest["version"] == "1.0"
        assert manifest["pipeline"] == "test-pipeline"
        assert manifest["influxdb"]["host"] == "influxdb"
        assert manifest["influxdb"]["database"] == "test_db"
        assert manifest["grafana"]["influxdb_url"] == "http://grafana:8086"
        assert len(manifest["metrics"]) == 2
        assert len(manifest["elements"]) == 1

    def test_write_metrics_manifest(self):
        """Test write_metrics_manifest writes YAML file."""
        pipeline, _ = create_mock_pipeline(name="test")
        element = MockMetricsElement()
        pipeline.elements.append(element)
        pipeline._registry[element.name] = element

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "manifest.yaml"
            pipeline.write_metrics_manifest(str(path))

            assert path.exists()
            with open(path) as f:
                data = yaml.safe_load(f)
            assert data["pipeline"] == "test"


class TestMetricsPipelineGrafana:
    """Tests for Grafana export."""

    def test_get_grafana_exporter(self):
        """Test get_grafana_exporter returns configured exporter."""
        pipeline, _ = create_mock_pipeline(
            name="test-pipeline",
            influxdb_db="test_db",
            grafana_influxdb_url="http://grafana:8086",
        )
        element = MockMetricsElement()
        pipeline.elements.append(element)

        exporter = pipeline.get_grafana_exporter()

        assert exporter.influxdb_db == "test_db"
        assert exporter.influxdb_url == "http://grafana:8086"
        assert len(exporter._metrics) == 2  # process_time and events_count

    def test_get_grafana_exporter_custom_title(self):
        """Test get_grafana_exporter with custom title."""
        pipeline, _ = create_mock_pipeline(name="test-pipeline")

        exporter = pipeline.get_grafana_exporter(dashboard_title="Custom Title")

        assert exporter.dashboard_title == "Custom Title"

    def test_export_grafana_dashboard(self):
        """Test export_grafana_dashboard writes JSON file."""
        pipeline, _ = create_mock_pipeline(name="test")
        element = MockMetricsElement()
        pipeline.elements.append(element)

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "dashboard.json"
            pipeline.export_grafana_dashboard(str(path))

            assert path.exists()

    def test_export_grafana_datasource(self):
        """Test export_grafana_datasource writes YAML file."""
        pipeline, _ = create_mock_pipeline(name="test", influxdb_db="test_db")

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "datasource.yaml"
            pipeline.export_grafana_datasource(str(path))

            assert path.exists()
            content = path.read_text()
            assert "test_db" in content

    def test_dashboard_json(self):
        """Test dashboard_json returns dictionary."""
        pipeline, _ = create_mock_pipeline(name="test")
        element = MockMetricsElement()
        pipeline.elements.append(element)

        dashboard = pipeline.dashboard_json()

        assert "panels" in dashboard
        assert "title" in dashboard


class TestMetricsPipelineTopology:
    """Tests for get_topology method."""

    def test_get_topology_nodes(self):
        """Test get_topology returns nodes for elements."""
        pipeline, _ = create_mock_pipeline()
        element1 = MockMetricsElement(name="element1")
        element2 = MockNonMetricsElement(name="element2")
        pipeline.elements.extend([element1, element2])

        topology = pipeline.get_topology()

        assert len(topology["nodes"]) == 2
        node_names = {n["name"] for n in topology["nodes"]}
        assert "element1" in node_names
        assert "element2" in node_names

        # Check metrics info
        metrics_node = next(n for n in topology["nodes"] if n["name"] == "element1")
        assert metrics_node["has_metrics"] is True
        assert "process_time" in metrics_node["metrics"]

    def test_get_topology_edges(self):
        """Test get_topology returns edges for connections."""
        pipeline, _ = create_mock_pipeline()
        element1 = MockMetricsElement(name="source")
        element2 = MockMetricsElement(name="sink")
        pipeline.elements.extend([element1, element2])

        # Simulate edges from Pipeline by mocking edges method
        with patch.object(
            pipeline, "edges", return_value=[("source:src:out", "sink:snk:in")]
        ):
            topology = pipeline.get_topology()

        assert len(topology["edges"]) == 1
        edge = topology["edges"][0]
        assert edge["source"] == "node_0"
        assert edge["target"] == "node_1"


class TestMetricsPipelineValidateSchema:
    """Tests for _validate_metrics_schema method."""

    def test_validate_warns_on_duplicates(self):
        """Test _validate_metrics_schema warns on duplicate metric names."""
        pipeline, _ = create_mock_pipeline()

        # Create elements with same metric name and no tags
        @dataclass
        class ElementWithDuplicateMetric(MetricsCollectorMixin):
            name: str = "dup_element"
            metrics_enabled: bool = True
            metrics_mode: str = "direct"
            track_elapsed_time: bool = False
            elapsed_metric_name: str | None = None

            metrics_schema: ClassVar = metrics(
                [("shared_metric", "counter", [], "Shared metric")]
            )

            def __post_init__(self):
                self._init_metrics()

        element1 = ElementWithDuplicateMetric(name="element1")
        element2 = ElementWithDuplicateMetric(name="element2")
        pipeline.elements.extend([element1, element2])

        # Should log warning but not raise
        with patch("sgneskig.pipeline.logger") as mock_logger:
            pipeline._validate_metrics_schema()
            # Should have warned about duplicate
            mock_logger.warning.assert_called()

    def test_validate_warns_on_invalid_type(self):
        """Test _validate_metrics_schema warns on invalid metric type."""
        pipeline, _ = create_mock_pipeline()

        @dataclass
        class ElementWithInvalidType(MetricsCollectorMixin):
            name: str = "invalid_element"
            metrics_enabled: bool = True
            metrics_mode: str = "direct"
            track_elapsed_time: bool = False
            elapsed_metric_name: str | None = None

            def __post_init__(self):
                self._init_metrics()
                self._metrics_schema = [
                    MetricDeclaration(
                        name="bad_metric",
                        metric_type="invalid",
                        tags=[],
                        description="Invalid type",
                    )
                ]

        element = ElementWithInvalidType()
        pipeline.elements.append(element)

        with patch("sgneskig.pipeline.logger") as mock_logger:
            pipeline._validate_metrics_schema()
            mock_logger.warning.assert_called()

    def test_validate_skips_non_mixin_elements(self):
        """Test _validate_metrics_schema skips non-MetricsCollectorMixin elements."""
        pipeline, _ = create_mock_pipeline()

        # Add a mock element that is NOT a MetricsCollectorMixin
        non_mixin_element = MagicMock()
        non_mixin_element.name = "plain_element"
        pipeline.elements.append(non_mixin_element)

        # Should not raise when validating
        pipeline._validate_metrics_schema()

    def test_validate_duplicate_metrics_with_same_tags_logs_debug(self):
        """Test _validate_metrics_schema logs debug for duplicates with same tags."""
        pipeline, _ = create_mock_pipeline()

        @dataclass
        class ElementWithTags(MetricsCollectorMixin):
            name: str = "element_with_tags"
            metrics_enabled: bool = True
            metrics_mode: str = "direct"
            track_elapsed_time: bool = False
            elapsed_metric_name: str | None = None

            def __post_init__(self):
                self._init_metrics()
                self._metrics_schema = [
                    MetricDeclaration(
                        name="tagged_metric",
                        metric_type="counter",
                        tags=["env"],  # Has tags
                        description="Tagged metric",
                    )
                ]

        element1 = ElementWithTags(name="element1")
        element2 = ElementWithTags(name="element2")
        pipeline.elements.extend([element1, element2])

        with patch("sgneskig.pipeline.logger") as mock_logger:
            pipeline._validate_metrics_schema()
            # Should log debug (not warning) since tags could differ by value
            mock_logger.debug.assert_called()


class TestMetricsPipelineGaugeMetrics:
    """Tests for gauge metric handling in MetricsPipeline."""

    def test_get_grafana_exporter_adds_gauge_metrics(self):
        """Test get_grafana_exporter adds gauge metrics to exporter."""
        pipeline, _ = create_mock_pipeline()

        @dataclass
        class ElementWithGauge(MetricsCollectorMixin):
            name: str = "gauge_element"
            metrics_enabled: bool = True
            metrics_mode: str = "direct"
            track_elapsed_time: bool = False
            elapsed_metric_name: str | None = None

            metrics_schema: ClassVar = [
                MetricDeclaration(
                    name="buffer_level",
                    metric_type="gauge",
                    tags=["pipeline"],
                    description="Buffer level",
                )
            ]

            def __post_init__(self):
                self._init_metrics()

        element = ElementWithGauge()
        pipeline.elements.append(element)

        exporter = pipeline.get_grafana_exporter(dashboard_title="Test")

        # Verify gauge metric was added
        assert len(exporter._metrics) == 1
        assert exporter._metrics[0].name == "buffer_level"
        assert exporter._metrics[0].metric_type == "gauge"
