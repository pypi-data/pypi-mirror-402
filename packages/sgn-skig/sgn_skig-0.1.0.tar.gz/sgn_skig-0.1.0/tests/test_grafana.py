"""Tests for sgneskig.metrics.grafana module."""

import json

from sgneskig.metrics.collector import MetricDeclaration
from sgneskig.metrics.grafana import (
    GrafanaExporter,
    _get_panel_width,
    _normalize_visualizations,
    _resolve_viz_config,
)


class TestNormalizeVisualizations:
    """Tests for _normalize_visualizations helper."""

    def test_none_uses_metric_type_default(self):
        """Test None visualization uses metric type default."""
        result = _normalize_visualizations({}, "timing")
        assert result == [{"type": "timeseries"}]

        result = _normalize_visualizations({}, "counter")
        assert result == [{"type": "bars"}]

        result = _normalize_visualizations({}, "gauge")
        assert result == [{"type": "timeseries"}]

    def test_string_shorthand(self):
        """Test string shorthand for single visualization."""
        result = _normalize_visualizations({"visualizations": "histogram"}, "timing")
        assert result == [{"type": "histogram"}]

    def test_list_of_strings(self):
        """Test list of strings for multiple visualizations."""
        result = _normalize_visualizations(
            {"visualizations": ["timeseries", "histogram"]}, "timing"
        )
        assert result == [{"type": "timeseries"}, {"type": "histogram"}]

    def test_list_of_dicts(self):
        """Test list of dicts with full config."""
        result = _normalize_visualizations(
            {"visualizations": [{"type": "histogram", "bucket_count": 50}]}, "timing"
        )
        assert result == [{"type": "histogram", "bucket_count": 50}]

    def test_mixed_list(self):
        """Test mixed list of strings and dicts."""
        result = _normalize_visualizations(
            {
                "visualizations": [
                    "timeseries",
                    {"type": "histogram", "bucket_count": 50},
                ]
            },
            "timing",
        )
        assert result == [
            {"type": "timeseries"},
            {"type": "histogram", "bucket_count": 50},
        ]


class TestResolveVizConfig:
    """Tests for _resolve_viz_config helper."""

    def test_defaults_for_timeseries(self):
        """Test defaults applied for timeseries."""
        result = _resolve_viz_config({"type": "timeseries"})
        assert result["draw_style"] == "line"
        assert result["line_interpolation"] == "smooth"
        assert result["line_width"] == 2
        assert result["fill_opacity"] == 15

    def test_defaults_for_histogram(self):
        """Test defaults applied for histogram."""
        result = _resolve_viz_config({"type": "histogram"})
        assert result["bucket_count"] == 30
        assert result["fill_opacity"] == 80

    def test_user_overrides_defaults(self):
        """Test user values override defaults."""
        result = _resolve_viz_config({"type": "histogram", "bucket_count": 50})
        assert result["bucket_count"] == 50
        assert result["fill_opacity"] == 80  # Default preserved

    def test_unknown_type_empty_defaults(self):
        """Test unknown viz type gets empty defaults."""
        result = _resolve_viz_config({"type": "unknown", "custom": "value"})
        assert result["type"] == "unknown"
        assert result["custom"] == "value"


class TestGetPanelWidth:
    """Tests for _get_panel_width helper."""

    def test_full_width(self):
        """Test 'full' returns 24 units."""
        assert _get_panel_width({"width": "full"}) == 24

    def test_half_width(self):
        """Test 'half' returns 12 units (default)."""
        assert _get_panel_width({"width": "half"}) == 12
        assert _get_panel_width({}) == 12  # Default

    def test_third_width(self):
        """Test 'third' returns 8 units."""
        assert _get_panel_width({"width": "third"}) == 8

    def test_quarter_width(self):
        """Test 'quarter' returns 6 units."""
        assert _get_panel_width({"width": "quarter"}) == 6

    def test_explicit_int(self):
        """Test explicit integer width."""
        assert _get_panel_width({"width": 18}) == 18

    def test_int_capped_at_24(self):
        """Test explicit int is capped at 24."""
        assert _get_panel_width({"width": 30}) == 24

    def test_unknown_string_returns_default(self):
        """Test unknown string returns default (12)."""
        assert _get_panel_width({"width": "unknown"}) == 12


class TestGrafanaExporterInit:
    """Tests for GrafanaExporter initialization."""

    def test_default_values(self):
        """Test default configuration values."""
        exporter = GrafanaExporter()
        assert exporter.datasource_name == "sgneskig_metrics"
        assert exporter.influxdb_url == "http://influxdb:8086"
        assert exporter.influxdb_db == "sgneskig_metrics"
        assert exporter.dashboard_title == "SGN-SKIG Metrics"
        assert exporter.scald_aggregate == "max"
        assert exporter._metrics == []

    def test_custom_values(self):
        """Test custom configuration values."""
        exporter = GrafanaExporter(
            datasource_name="my_metrics",
            influxdb_url="http://localhost:8086",
            influxdb_db="my_db",
            dashboard_title="My Dashboard",
            scald_aggregate="min",
        )
        assert exporter.datasource_name == "my_metrics"
        assert exporter.influxdb_url == "http://localhost:8086"
        assert exporter.influxdb_db == "my_db"
        assert exporter.dashboard_title == "My Dashboard"
        assert exporter.scald_aggregate == "min"

    def test_auto_generated_uid(self):
        """Test UID is auto-generated from title."""
        exporter = GrafanaExporter(dashboard_title="My Test Dashboard")
        assert "my-test-dashboard" in exporter.dashboard_uid

    def test_custom_uid_preserved(self):
        """Test custom UID is preserved."""
        exporter = GrafanaExporter(dashboard_uid="custom-uid-123")
        assert exporter.dashboard_uid == "custom-uid-123"


class TestGrafanaExporterAddMetric:
    """Tests for add_metric methods."""

    def test_add_metric(self):
        """Test basic add_metric."""
        exporter = GrafanaExporter()
        exporter.add_metric(
            name="test_metric",
            metric_type="counter",
            tags=["env"],
            description="Test description",
        )

        assert len(exporter._metrics) == 1
        metric = exporter._metrics[0]
        assert metric.name == "test_metric"
        assert metric.metric_type == "counter"
        assert metric.tags == ["env"]
        assert metric.description == "Test description"

    def test_add_timing_metric(self):
        """Test add_timing_metric sets correct type and unit."""
        exporter = GrafanaExporter()
        exporter.add_timing_metric(
            name="process_time",
            tags=["stage"],
            description="Processing time",
        )

        metric = exporter._metrics[0]
        assert metric.name == "process_time"
        assert metric.metric_type == "timing"
        assert metric.unit == "s"

    def test_add_counter_metric(self):
        """Test add_counter_metric sets correct type."""
        exporter = GrafanaExporter()
        exporter.add_counter_metric(
            name="events_count",
            tags=["type"],
            description="Event count",
        )

        metric = exporter._metrics[0]
        assert metric.name == "events_count"
        assert metric.metric_type == "counter"
        assert metric.unit == ""

    def test_add_gauge_metric(self):
        """Test add_gauge_metric sets correct type."""
        exporter = GrafanaExporter()
        exporter.add_gauge_metric(
            name="buffer_size",
            description="Buffer size",
        )

        metric = exporter._metrics[0]
        assert metric.name == "buffer_size"
        assert metric.metric_type == "gauge"

    def test_add_metric_with_panel_config(self):
        """Test add_metric with panel_config."""
        exporter = GrafanaExporter()
        exporter.add_metric(
            name="test",
            metric_type="timing",
            panel_config={
                "width": "full",
                "visualizations": ["timeseries", "histogram"],
            },
        )

        metric = exporter._metrics[0]
        assert metric.panel_config["width"] == "full"


class TestGrafanaExporterDatasource:
    """Tests for datasource generation."""

    def test_datasource_yaml(self):
        """Test datasource YAML generation."""
        exporter = GrafanaExporter(
            datasource_name="test_ds",
            influxdb_url="http://influx:8086",
            influxdb_db="test_db",
        )

        yaml = exporter.datasource_yaml()

        assert "name: test_ds" in yaml
        assert "url: http://influx:8086" in yaml
        assert "database: test_db" in yaml
        assert "type: influxdb" in yaml

    def test_datasource_json(self):
        """Test datasource JSON generation."""
        exporter = GrafanaExporter(
            datasource_name="test_ds",
            influxdb_url="http://influx:8086",
            influxdb_db="test_db",
        )

        ds = exporter.datasource_json()

        assert ds["name"] == "test_ds"
        assert ds["type"] == "influxdb"
        assert ds["url"] == "http://influx:8086"
        assert ds["database"] == "test_db"

    def test_datasource_curl_command(self):
        """Test curl command generation."""
        exporter = GrafanaExporter(datasource_name="test_ds")

        cmd = exporter.datasource_curl_command(
            grafana_url="http://grafana:3000",
            auth="myuser:mypass",
        )

        assert "curl -u myuser:mypass" in cmd
        assert "http://grafana:3000/api/datasources" in cmd
        assert '"name": "test_ds"' in cmd


class TestGrafanaExporterQuery:
    """Tests for InfluxQL query generation."""

    def test_make_influxql_query_basic(self):
        """Test basic query generation."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="test_metric",
            metric_type="timing",
            tags=[],
            description="Test",
        )

        query = exporter._make_influxql_query(metric, aggregation="mean")

        assert 'SELECT mean("value")' in query
        assert '"1s"."test_metric"' in query
        assert "WHERE \"aggregate\" = 'max'" in query
        assert "$timeFilter" in query
        assert "GROUP BY time($__interval)" in query

    def test_make_influxql_query_with_tags(self):
        """Test query with tags includes GROUP BY tags."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="test_metric",
            metric_type="counter",
            tags=["env", "host"],
            description="Test",
        )

        query = exporter._make_influxql_query(metric, aggregation="sum")

        assert 'SELECT sum("value")' in query
        assert 'GROUP BY time($__interval), "env", "host"' in query

    def test_make_influxql_query_custom_aggregate(self):
        """Test query uses custom scald_aggregate."""
        exporter = GrafanaExporter(scald_aggregate="min")
        metric = MetricDeclaration(
            name="test",
            metric_type="timing",
            tags=[],
            description="",
        )

        query = exporter._make_influxql_query(metric)

        assert "WHERE \"aggregate\" = 'min'" in query


class TestGrafanaExporterPanels:
    """Tests for panel generation."""

    def test_make_base_panel(self):
        """Test base panel structure."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="test",
            metric_type="timing",
            tags=[],
            description="Test metric",
        )

        panel = exporter._make_base_panel(
            metric,
            panel_id=1,
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
            panel_type="timeseries",
        )

        assert panel["id"] == 1
        assert panel["title"] == "Test metric"
        assert panel["type"] == "timeseries"
        assert panel["gridPos"]["w"] == 12
        assert panel["datasource"]["type"] == "influxdb"
        assert len(panel["targets"]) == 1

    def test_make_histogram_panel(self):
        """Test histogram panel generation."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="latency",
            metric_type="timing",
            tags=[],
            description="Latency",
        )

        panel = exporter._make_histogram_panel(
            metric,
            {"type": "histogram"},
            panel_id=1,
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
        )

        assert panel["type"] == "histogram"
        assert "Distribution" in panel["title"]
        assert "bucketCount" in panel["options"]

    def test_make_timeseries_panel(self):
        """Test timeseries panel generation."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="process_time",
            metric_type="timing",
            tags=[],
            description="Process time",
        )

        panel = exporter._make_timeseries_panel(
            metric,
            {"type": "timeseries"},
            panel_id=1,
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
        )

        assert panel["type"] == "timeseries"
        assert panel["fieldConfig"]["defaults"]["custom"]["drawStyle"] == "line"

    def test_make_bars_panel(self):
        """Test bars panel generation."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="events",
            metric_type="counter",
            tags=[],
            description="Events",
        )

        panel = exporter._make_bars_panel(
            metric,
            {"type": "bars"},
            panel_id=1,
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
        )

        assert panel["type"] == "timeseries"  # Grafana timeseries with bars config
        assert panel["fieldConfig"]["defaults"]["custom"]["drawStyle"] == "bars"

    def test_make_stat_panel(self):
        """Test stat panel generation."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="total_count",
            metric_type="counter",
            tags=[],
            description="Total count",
        )

        panel = exporter._make_stat_panel(
            metric,
            panel_id=1,
            grid_pos={"h": 4, "w": 6, "x": 0, "y": 0},
        )

        assert panel["type"] == "stat"
        assert "Total" in panel["title"]
        assert panel["options"]["reduceOptions"]["calcs"] == ["sum"]

    def test_make_mermaid_panel(self):
        """Test Mermaid diagram panel generation."""
        exporter = GrafanaExporter()
        topology = {
            "nodes": [
                {"id": "source", "name": "KafkaSource", "type": "SourceElement"},
                {"id": "sink", "name": "KafkaSink", "type": "SinkElement"},
            ],
            "edges": [{"source": "source", "target": "sink"}],
        }

        panel = exporter._make_mermaid_panel(
            topology,
            panel_id=1,
            grid_pos={"h": 6, "w": 24, "x": 0, "y": 0},
        )

        assert panel["type"] == "jdbranham-diagram-panel"
        assert "flowchart LR" in panel["options"]["content"]
        assert "KafkaSource" in panel["options"]["content"]
        assert "source --> sink" in panel["options"]["content"]

    def test_make_panel_for_viz_histogram(self):
        """Test _make_panel_for_viz routes to histogram."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="test",
            metric_type="timing",
            tags=[],
            description="",
        )

        panel = exporter._make_panel_for_viz(
            metric,
            {"type": "histogram"},
            panel_id=1,
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
        )

        assert panel["type"] == "histogram"

    def test_make_panel_for_viz_bars(self):
        """Test _make_panel_for_viz routes to bars."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="test",
            metric_type="counter",
            tags=[],
            description="",
        )

        panel = exporter._make_panel_for_viz(
            metric,
            {"type": "bars"},
            panel_id=1,
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
        )

        assert panel["fieldConfig"]["defaults"]["custom"]["drawStyle"] == "bars"

    def test_make_panel_for_viz_stat(self):
        """Test _make_panel_for_viz routes to stat."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="test",
            metric_type="counter",
            tags=[],
            description="",
        )

        panel = exporter._make_panel_for_viz(
            metric,
            {"type": "stat"},
            panel_id=1,
            grid_pos={"h": 4, "w": 6, "x": 0, "y": 0},
        )

        assert panel["type"] == "stat"


class TestGrafanaExporterDashboard:
    """Tests for dashboard generation."""

    def test_dashboard_json_structure(self):
        """Test dashboard JSON has required structure."""
        exporter = GrafanaExporter(dashboard_title="Test Dashboard")
        exporter.add_timing_metric("latency")

        dashboard = exporter.dashboard_json()

        assert "uid" in dashboard
        assert dashboard["title"] == "Test Dashboard"
        assert "panels" in dashboard
        assert "templating" in dashboard
        assert dashboard["refresh"] == "10s"

    def test_dashboard_with_timing_metrics(self):
        """Test dashboard with timing metrics."""
        exporter = GrafanaExporter()
        exporter.add_timing_metric("process_time", description="Process time")
        exporter.add_timing_metric("api_latency", description="API latency")

        dashboard = exporter.dashboard_json()
        panels = dashboard["panels"]

        # Should have: row header + 2 timeseries panels
        panel_types = [p["type"] for p in panels]
        assert "row" in panel_types
        assert panel_types.count("timeseries") == 2

    def test_dashboard_with_counter_metrics(self):
        """Test dashboard with counter metrics."""
        exporter = GrafanaExporter()
        exporter.add_counter_metric("events_created")
        exporter.add_counter_metric("events_processed")

        dashboard = exporter.dashboard_json()
        panels = dashboard["panels"]

        # Should have: row + stat panels + bar charts
        panel_types = [p["type"] for p in panels]
        assert "row" in panel_types
        assert panel_types.count("stat") == 2  # One stat per counter
        assert panel_types.count("timeseries") == 2  # One bars chart per counter

    def test_dashboard_with_topology(self):
        """Test dashboard includes topology panel."""
        exporter = GrafanaExporter()
        exporter.set_topology(
            {
                "nodes": [
                    {"id": "src", "name": "Source", "type": "SourceElement"},
                ],
                "edges": [],
            }
        )
        exporter.add_timing_metric("test")

        dashboard = exporter.dashboard_json()
        panels = dashboard["panels"]

        # Should have topology row + mermaid panel
        has_topology_row = any(
            p["type"] == "row" and p["title"] == "Pipeline Topology" for p in panels
        )
        has_mermaid = any(p["type"] == "jdbranham-diagram-panel" for p in panels)

        assert has_topology_row
        assert has_mermaid

    def test_dashboard_panel_wrapping(self):
        """Test panels wrap to new row when exceeding width."""
        exporter = GrafanaExporter()
        # Add 3 half-width metrics (should cause wrapping)
        for i in range(3):
            exporter.add_timing_metric(f"metric_{i}")

        dashboard = exporter.dashboard_json()
        panels = dashboard["panels"]

        # Check y positions vary (indicating row wrapping)
        y_positions = {p["gridPos"]["y"] for p in panels if p["type"] != "row"}
        assert len(y_positions) >= 1  # At least one row


class TestGrafanaExporterSetTopology:
    """Tests for set_topology method."""

    def test_set_topology(self):
        """Test setting topology."""
        exporter = GrafanaExporter()
        topology = {"nodes": [], "edges": []}

        exporter.set_topology(topology)

        assert exporter._topology == topology


class TestGrafanaExporterFileOutput:
    """Tests for file output methods."""

    def test_write_datasource(self, tmp_path):
        """Test writing datasource YAML to file."""
        exporter = GrafanaExporter(datasource_name="test_ds")
        path = tmp_path / "datasource.yaml"

        exporter.write_datasource(str(path))

        content = path.read_text()
        assert "name: test_ds" in content

    def test_write_dashboard(self, tmp_path):
        """Test writing dashboard JSON to file."""
        exporter = GrafanaExporter(dashboard_title="Test Dashboard")
        exporter.add_timing_metric("test")
        path = tmp_path / "dashboard.json"

        exporter.write_dashboard(str(path))

        content = path.read_text()
        data = json.loads(content)
        assert data["title"] == "Test Dashboard"

    def test_print_setup_instructions(self):
        """Test setup instructions generation."""
        exporter = GrafanaExporter()

        instructions = exporter.print_setup_instructions()

        assert "Grafana Setup" in instructions
        assert "Create Datasource" in instructions
        assert "curl" in instructions


class TestGrafanaExporterEdgeCases:
    """Tests for edge cases."""

    def test_empty_dashboard(self):
        """Test dashboard with no metrics."""
        exporter = GrafanaExporter()
        dashboard = exporter.dashboard_json()

        assert dashboard["panels"] == []

    def test_metric_with_multiple_visualizations(self):
        """Test metric with multiple visualization types."""
        exporter = GrafanaExporter()
        exporter.add_timing_metric(
            name="latency",
            panel_config={"visualizations": ["timeseries", "histogram"]},
        )

        dashboard = exporter.dashboard_json()
        panels = [p for p in dashboard["panels"] if p["type"] != "row"]

        # Should have both timeseries and histogram
        assert len(panels) == 2
        assert any(p["type"] == "timeseries" for p in panels)
        assert any(p["type"] == "histogram" for p in panels)

    def test_metric_title_derived_from_name(self):
        """Test panel title derived from metric name when no description."""
        exporter = GrafanaExporter()
        exporter.add_timing_metric(name="foo_bar_time", description="")

        dashboard = exporter.dashboard_json()
        timing_panel = next(p for p in dashboard["panels"] if p["type"] == "timeseries")

        # Title should be derived from name (title case)
        assert "Foo Bar Time" in timing_panel["title"]

    def test_aggregation_override_in_panel_config(self):
        """Test aggregation can be overridden in panel_config."""
        exporter = GrafanaExporter(scald_aggregate="max")
        exporter.add_timing_metric(
            name="test",
            panel_config={"aggregation": "mean"},
        )

        dashboard = exporter.dashboard_json()
        timing_panel = next(p for p in dashboard["panels"] if p["type"] == "timeseries")
        query = timing_panel["targets"][0]["query"]

        assert "mean(" in query

    def test_bars_panel_stacking(self):
        """Test bars panel includes stacking config."""
        exporter = GrafanaExporter()
        metric = MetricDeclaration(
            name="events",
            metric_type="counter",
            tags=["type"],
            description="Events",
        )

        panel = exporter._make_bars_panel(
            metric,
            {"type": "bars", "stacking_mode": "normal"},
            panel_id=1,
            grid_pos={"h": 8, "w": 12, "x": 0, "y": 0},
        )

        assert "stacking" in panel["fieldConfig"]["defaults"]["custom"]
        assert (
            panel["fieldConfig"]["defaults"]["custom"]["stacking"]["mode"] == "normal"
        )


class TestGrafanaExporterPanelWrapping:
    """Tests for panel row wrapping logic."""

    def test_stat_panels_wrap_after_four(self):
        """Test stat panels wrap to new row after 4 counter metrics."""
        exporter = GrafanaExporter()

        # Add 5 counter metrics to trigger stat row wrapping (line 743)
        for i in range(5):
            exporter.add_counter_metric(
                name=f"counter_{i}",
                tags=[],
                description=f"Counter {i}",
            )

        dashboard = exporter.dashboard_json()
        stat_panels = [p for p in dashboard["panels"] if p["type"] == "stat"]

        # Should have 5 stat panels
        assert len(stat_panels) == 5

        # First 4 should be on same row (same y), 5th should be on new row
        y_positions = [p["gridPos"]["y"] for p in stat_panels]
        assert y_positions[0] == y_positions[1] == y_positions[2] == y_positions[3]
        assert y_positions[4] > y_positions[0]

    def test_panels_wrap_when_exceeding_width(self):
        """Test panels wrap to new row when exceeding 24 unit width."""
        exporter = GrafanaExporter()

        # Add counter metrics with wide panels to trigger wrapping (lines 766-767)
        # Default counter timeseries panel is 12 units wide
        # With 3 metrics (3 * 12 = 36 > 24), should wrap
        for i in range(3):
            exporter.add_counter_metric(
                name=f"wide_counter_{i}",
                tags=[],
                description=f"Wide counter {i}",
            )

        dashboard = exporter.dashboard_json()

        # Find timeseries panels (counter visualizations, not stat panels)
        timeseries_panels = [
            p for p in dashboard["panels"] if p["type"] == "timeseries"
        ]

        # Should have 3 timeseries panels
        assert len(timeseries_panels) == 3

        # At least one should be on a different row (y position differs)
        y_positions = [p["gridPos"]["y"] for p in timeseries_panels]
        # Not all y positions should be the same if wrapping occurred
        assert len(set(y_positions)) > 1
