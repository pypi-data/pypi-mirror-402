"""Grafana integration for SGN metrics.

Generates Grafana datasource configs and dashboards from metric schemas.

Usage:
    # From ScaldMetricsSink
    sink.export_grafana_dashboard("my_dashboard.json")
    sink.export_grafana_datasource("datasources/sgneskig.yaml")

    # Standalone
    from sgneskig.metrics.grafana import GrafanaExporter
    exporter = GrafanaExporter(
        datasource_name="sgneskig_metrics",
        influxdb_url="http://influxdb:8086",
        influxdb_db="sgneskig_metrics",
    )
    exporter.add_timing_metric("createEvent_time", tags=["pipeline"])
    exporter.add_counter_metric("events_created", tags=["pipeline"])
    exporter.write_dashboard("dashboard.json")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from sgneskig.metrics.collector import MetricDeclaration

# ─────────────────────────────────────────────────────────────────────────────
# Visualization Defaults
# ─────────────────────────────────────────────────────────────────────────────

# Default configuration for each visualization type
# User-provided values override these defaults
_VIZ_DEFAULTS: dict[str, dict[str, Any]] = {
    "timeseries": {
        "draw_style": "line",
        "line_interpolation": "smooth",
        "line_width": 2,
        "fill_opacity": 15,
        "gradient_mode": "opacity",
        "point_size": 5,
        "show_points": "never",
    },
    "histogram": {
        "bucket_count": 30,
        "fill_opacity": 80,
        "gradient_mode": "hue",
    },
    "stat": {
        "color_mode": "thresholds",
    },
    "bars": {
        "draw_style": "bars",
        "fill_opacity": 80,
        "gradient_mode": "hue",
        "bar_alignment": 0,
        "stacking_mode": "normal",
    },
}

# Default visualization type based on metric type
_METRIC_TYPE_DEFAULTS: dict[str, str] = {
    "timing": "timeseries",
    "counter": "bars",
    "gauge": "timeseries",
}


def _normalize_visualizations(
    panel_config: dict, metric_type: str
) -> list[dict[str, Any]]:
    """Normalize visualizations config to list of dicts.

    Accepts:
    - Omitted/None: uses default for metric type
    - String: single viz with defaults ("histogram")
    - List of strings: multiple viz with defaults (["timeseries", "histogram"])
    - List of dicts: full control ([{"type": "histogram", "bucket_count": 50}])
    - Mixed list: (["timeseries", {"type": "histogram", "bucket_count": 50}])

    Returns:
        List of visualization config dicts, each with at least "type" key
    """
    viz = panel_config.get("visualizations")

    # Default based on metric type
    if viz is None:
        default_type = _METRIC_TYPE_DEFAULTS.get(metric_type, "timeseries")
        return [{"type": default_type}]

    # String shorthand
    if isinstance(viz, str):
        return [{"type": viz}]

    # List - normalize each item
    result = []
    for item in viz:
        if isinstance(item, str):
            result.append({"type": item})
        else:
            result.append(item)
    return result


def _resolve_viz_config(viz: dict[str, Any]) -> dict[str, Any]:
    """Merge user visualization config over defaults.

    Args:
        viz: User-provided visualization config (must have "type" key)

    Returns:
        Complete config with defaults filled in
    """
    viz_type = viz.get("type", "timeseries")
    defaults = _VIZ_DEFAULTS.get(viz_type, {}).copy()
    defaults.update(viz)
    return defaults


def _get_panel_width(panel_config: dict) -> int:
    """Get panel width in grid units from config.

    Accepts:
    - "full" → 24 units
    - "half" → 12 units (default)
    - "third" → 8 units
    - "quarter" → 6 units
    - int → explicit width

    Returns:
        Width in Grafana grid units (max 24)
    """
    width = panel_config.get("width", "half")
    if width == "full":
        return 24
    elif width == "half":
        return 12
    elif width == "third":
        return 8
    elif width == "quarter":
        return 6
    elif isinstance(width, int):
        return min(width, 24)
    return 12  # default


@dataclass
class GrafanaExporter:
    """Generates Grafana configs from metric schemas.

    Aggregation Strategy (two-level):
        1. Scald storage: ligo.scald reduces data to 1s buckets using min/median/max
           (scald doesn't support sum). We use "max" by default for both timing
           and counter metrics. Data is tagged with aggregate='max'.

        2. Grafana queries: Different SELECT aggregations per metric type:
           - Timing/Gauge: SELECT max() - shows true maximum values
           - Counter: SELECT sum() - accumulates counts across time intervals

           All queries filter with WHERE aggregate='max' to match scald's tag.

    Args:
        datasource_name: Name for the Grafana datasource
        influxdb_url: InfluxDB URL (for Grafana to connect to)
        influxdb_db: InfluxDB database name
        dashboard_title: Title for generated dashboards
        scald_aggregate: ligo.scald storage aggregation tag (must match
            MetricsWriter.aggregate). Used for WHERE filter in all queries
            and as default SELECT aggregation for timing metrics.
            Valid values: "min", "median", "max" (default: "max").
    """

    datasource_name: str = "sgneskig_metrics"
    influxdb_url: str = "http://influxdb:8086"
    influxdb_db: str = "sgneskig_metrics"
    dashboard_title: str = "SGN-SKIG Metrics"
    dashboard_uid: str | None = None
    scald_aggregate: str = "max"  # Must match MetricsWriter.aggregate

    def __post_init__(self):
        self._metrics: list[MetricDeclaration] = []
        self._topology: dict | None = None
        if self.dashboard_uid is None:
            # Generate a stable UID from title (slugified)
            slug = self.dashboard_title.lower().replace(" ", "-").replace("_", "-")
            # Remove non-alphanumeric chars except hyphens
            slug = "".join(c for c in slug if c.isalnum() or c == "-")
            self.dashboard_uid = f"sgneskig-{slug}"[:40]

    def add_metric(
        self,
        name: str,
        metric_type: Literal["timing", "counter", "gauge"],
        tags: list[str] | None = None,
        unit: str = "",
        description: str = "",
        panel_config: dict | None = None,
    ) -> None:
        """Add a metric to be included in generated dashboards."""
        self._metrics.append(
            MetricDeclaration(
                name=name,
                metric_type=metric_type,
                tags=tags or [],
                unit=unit,
                description=description,
                panel_config=panel_config or {},
            )
        )

    def add_timing_metric(
        self,
        name: str,
        tags: list[str] | None = None,
        description: str = "",
        panel_config: dict | None = None,
    ) -> None:
        """Add a timing metric (displayed as time series graph)."""
        self.add_metric(
            name,
            "timing",
            tags,
            unit="s",
            description=description,
            panel_config=panel_config,
        )

    def add_counter_metric(
        self,
        name: str,
        tags: list[str] | None = None,
        description: str = "",
        panel_config: dict | None = None,
    ) -> None:
        """Add a counter metric (displayed as stat panel + time series)."""
        self.add_metric(
            name,
            "counter",
            tags,
            unit="",
            description=description,
            panel_config=panel_config,
        )

    def add_gauge_metric(
        self,
        name: str,
        tags: list[str] | None = None,
        description: str = "",
        panel_config: dict | None = None,
    ) -> None:
        """Add a gauge metric (displayed as gauge panel)."""
        self.add_metric(
            name,
            "gauge",
            tags,
            unit="",
            description=description,
            panel_config=panel_config,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Datasource Generation
    # ─────────────────────────────────────────────────────────────────────────

    def datasource_yaml(self) -> str:
        """Generate Grafana provisioning YAML for the datasource.

        Save to: grafana/provisioning/datasources/sgneskig.yaml
        """
        return f"""# Auto-generated by sgneskig.metrics.grafana
# Copy to: grafana/provisioning/datasources/
apiVersion: 1

datasources:
  - name: {self.datasource_name}
    type: influxdb
    access: proxy
    url: {self.influxdb_url}
    database: {self.influxdb_db}
    isDefault: false
    jsonData:
      httpMode: POST
    editable: true
"""

    def datasource_json(self) -> dict:
        """Generate JSON for Grafana API datasource creation."""
        return {
            "name": self.datasource_name,
            "type": "influxdb",
            "access": "proxy",
            "url": self.influxdb_url,
            "database": self.influxdb_db,
            "basicAuth": False,
            "jsonData": {"httpMode": "POST"},
        }

    def datasource_curl_command(
        self, grafana_url: str = "http://localhost:3000", auth: str = "admin:admin"
    ) -> str:
        """Generate curl command to create datasource via API."""
        payload = json.dumps(self.datasource_json())
        return f"""curl -u {auth} -X POST {grafana_url}/api/datasources \\
  -H 'Content-Type: application/json' \\
  -d '{payload}'"""

    # ─────────────────────────────────────────────────────────────────────────
    # Dashboard Generation
    # ─────────────────────────────────────────────────────────────────────────

    def _make_base_panel(
        self,
        metric: MetricDeclaration,
        panel_id: int,
        grid_pos: dict,
        panel_type: str = "timeseries",
        title_suffix: str = "",
        custom_config: dict | None = None,
        options: dict | None = None,
        aggregation: str = "mean",
    ) -> dict:
        """Build common panel structure.

        Args:
            metric: The metric schema
            panel_id: Panel ID
            grid_pos: Grid position dict
            panel_type: Grafana panel type (timeseries, histogram, stat)
            title_suffix: Optional suffix for title (e.g., " (Distribution)")
            custom_config: Custom field config overrides
            options: Panel options overrides
            aggregation: Query aggregation function (mean, sum, etc.)

        Returns:
            Base panel dict that can be further customized
        """
        config = metric.panel_config
        title = metric.get_panel_title()
        if title_suffix:
            title = f"{title}{title_suffix}"

        panel = {
            "id": panel_id,
            "title": title,
            "type": panel_type,
            "gridPos": grid_pos,
            "datasource": {"type": "influxdb", "uid": "${datasource}"},
            "fieldConfig": {
                "defaults": {
                    "unit": metric.get_grafana_unit(),
                    "color": {"mode": config.get("color_mode", "palette-classic")},
                    "custom": custom_config or {},
                },
                "overrides": [],
            },
            "options": options
            or {
                "legend": {"displayMode": "list", "placement": "bottom"},
                "tooltip": {"mode": "multi"},
            },
            "targets": [
                {
                    "refId": "A",
                    "query": self._make_influxql_query(metric, aggregation),
                    "rawQuery": True,
                    "resultFormat": "time_series",
                }
            ],
        }
        return panel

    def _make_influxql_query(
        self,
        metric: MetricDeclaration,
        aggregation: str = "mean",
        retention_policy: str = "1s",
    ) -> str:
        """Generate InfluxQL query for a metric.

        Args:
            metric: The metric schema
            aggregation: Aggregation function (mean, sum, max, etc.)
            retention_policy: InfluxDB retention policy (ligo.scald writes to "1s")

        Note:
            ligo.scald stores data with an `aggregate` tag indicating the
            aggregation used when reducing to 1s. We filter by this tag
            (default: 'max' matching MetricsWriter default) to get the
            correct data.
        """
        # Group by tags if present
        group_by = ", ".join(f'"{tag}"' for tag in metric.tags)
        if group_by:
            group_by = f", {group_by}"

        # InfluxQL query for Grafana dashboard (not user input)
        # ligo.scald writes to retention policies like "1s", "10s", etc.
        # and tags data with 'aggregate' indicating the reduction function used
        measurement = f'"{retention_policy}"."{metric.name}"'
        scald_aggregate = self.scald_aggregate  # Filter to match scald's stored data
        query = (
            f'SELECT {aggregation}("value") FROM {measurement} '  # noqa: S608
            f"WHERE \"aggregate\" = '{scald_aggregate}' AND $timeFilter "
            f"GROUP BY time($__interval){group_by} fill(null)"
        )
        return query

    def _make_histogram_panel(
        self, metric: MetricDeclaration, viz_config: dict, panel_id: int, grid_pos: dict
    ) -> dict:
        """Generate a histogram panel showing value distribution.

        Uses Grafana's built-in histogram transformation to bucket values.
        """
        config = _resolve_viz_config(viz_config)
        custom_config = {
            "fillOpacity": config.get("fill_opacity", 80),
            "gradientMode": config.get("gradient_mode", "hue"),
            "hideFrom": {"legend": False, "tooltip": False, "viz": False},
        }
        options = {
            "legend": {"displayMode": "list", "placement": "bottom"},
            "bucketCount": config.get("bucket_count", 30),
            "combine": False,
        }
        return self._make_base_panel(
            metric,
            panel_id,
            grid_pos,
            panel_type="histogram",
            title_suffix=" (Distribution)",
            custom_config=custom_config,
            options=options,
            aggregation="mean",
        )

    def _make_panel_for_viz(
        self, metric: MetricDeclaration, viz_config: dict, panel_id: int, grid_pos: dict
    ) -> dict:
        """Generate a panel based on visualization type.

        Args:
            metric: The metric schema
            viz_config: Visualization config dict (already normalized, has "type" key)
            panel_id: Panel ID
            grid_pos: Grid position

        Returns:
            Panel configuration dictionary
        """
        config = _resolve_viz_config(viz_config)
        viz_type = config.get("type", "timeseries")

        if viz_type == "histogram":
            return self._make_histogram_panel(metric, viz_config, panel_id, grid_pos)
        elif viz_type == "bars":
            # Use bars visualization (like counter default)
            return self._make_bars_panel(metric, config, panel_id, grid_pos)
        elif viz_type == "stat":
            return self._make_stat_panel(metric, panel_id, grid_pos)
        else:
            # Default: timeseries
            return self._make_timeseries_panel(metric, config, panel_id, grid_pos)

    def _make_timeseries_panel(
        self, metric: MetricDeclaration, config: dict, panel_id: int, grid_pos: dict
    ) -> dict:
        """Generate a time series panel.

        Supports `aggregation` in panel_config or visualization config:
        - "max" - maximum value per interval (default, matches scald_aggregate)
        - "mean" - average value per interval
        - "min" - minimum value per interval
        - "sum" - total per interval (default for counters via bars panel)

        Priority: viz config > metric panel_config > scald_aggregate

        The default aggregation matches scald_aggregate to ensure consistency:
        if scald stores max per 1s, Grafana queries max() to get true maximum.
        """
        custom_config = {
            "drawStyle": config.get("draw_style", "line"),
            "lineInterpolation": config.get("line_interpolation", "smooth"),
            "lineWidth": config.get("line_width", 2),
            "fillOpacity": config.get("fill_opacity", 15),
            "gradientMode": config.get("gradient_mode", "opacity"),
            "pointSize": config.get("point_size", 5),
            "showPoints": config.get("show_points", "never"),
        }
        # Default to scald_aggregate for consistency: if scald stores max,
        # Grafana should query max() to get true maximum values
        aggregation = config.get(
            "aggregation", metric.panel_config.get("aggregation", self.scald_aggregate)
        )
        return self._make_base_panel(
            metric,
            panel_id,
            grid_pos,
            panel_type="timeseries",
            custom_config=custom_config,
            aggregation=aggregation,
        )

    def _make_bars_panel(
        self, metric: MetricDeclaration, config: dict, panel_id: int, grid_pos: dict
    ) -> dict:
        """Generate a bar chart panel (typically for counters).

        Default aggregation is "sum" for counters, but can be overridden.
        """
        stacking_mode = config.get("stacking_mode", "normal")
        custom_config = {
            "drawStyle": config.get("draw_style", "bars"),
            "fillOpacity": config.get("fill_opacity", 80),
            "gradientMode": config.get("gradient_mode", "hue"),
            "barAlignment": config.get("bar_alignment", 0),
        }
        if stacking_mode:
            custom_config["stacking"] = {"mode": stacking_mode}
        # Allow aggregation override: viz > panel_config > default
        aggregation = config.get(
            "aggregation", metric.panel_config.get("aggregation", "sum")
        )
        return self._make_base_panel(
            metric,
            panel_id,
            grid_pos,
            panel_type="timeseries",
            custom_config=custom_config,
            aggregation=aggregation,
        )

    def _make_mermaid_panel(
        self, topology: dict, panel_id: int, grid_pos: dict
    ) -> dict:
        """Generate a Text panel with Mermaid diagram of the pipeline.

        This is a fallback for when Node Graph doesn't work well with InfluxDB.
        Requires the Mermaid plugin or uses text panel with markdown.

        Args:
            topology: Dictionary with 'nodes' and 'edges' keys
            panel_id: Panel ID
            grid_pos: Grid position

        Returns:
            Panel configuration dictionary
        """
        # Build Mermaid flowchart
        lines = ["```mermaid", "flowchart LR"]

        # Add nodes with styling
        for node in topology.get("nodes", []):
            node_id = node["id"]
            name = node["name"]
            node_type = node["type"]
            # Use different shapes for different element types
            if "Source" in node_type:
                lines.append(f"    {node_id}[({name})]")  # Stadium shape
            elif "Sink" in node_type:
                lines.append(f"    {node_id}[/{name}/]")  # Parallelogram
            else:
                lines.append(f"    {node_id}[{name}]")  # Rectangle

        # Add edges
        for edge in topology.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            lines.append(f"    {source} --> {target}")

        # Don't include markdown fences - the diagram plugin takes raw mermaid
        mermaid_content = "\n".join(lines[1:])  # Skip the ```mermaid line

        return {
            "id": panel_id,
            "title": "Pipeline Topology",
            "type": "jdbranham-diagram-panel",
            "gridPos": grid_pos,
            "options": {
                "content": mermaid_content,
            },
        }

    def set_topology(self, topology: dict) -> None:
        """Set pipeline topology for Node Graph panel.

        Args:
            topology: Dictionary with 'nodes' and 'edges' keys from
                     MetricsPipeline.get_topology()
        """
        self._topology = topology

    def _make_stat_panel(
        self, metric: MetricDeclaration, panel_id: int, grid_pos: dict
    ) -> dict:
        """Generate a stat panel showing total count."""
        config = metric.panel_config
        thresholds = config.get(
            "thresholds",
            {
                "mode": "absolute",
                "steps": [{"color": "green", "value": None}],
            },
        )
        return {
            "id": panel_id,
            "title": f"Total {metric.get_panel_title()}",
            "type": "stat",
            "gridPos": grid_pos,
            "datasource": {"type": "influxdb", "uid": "${datasource}"},
            "fieldConfig": {
                "defaults": {
                    "unit": metric.get_grafana_unit(),
                    "color": {"mode": config.get("color_mode", "thresholds")},
                    "thresholds": thresholds,
                },
                "overrides": [],
            },
            "options": {
                "colorMode": "value",
                "graphMode": "area",
                "justifyMode": "auto",
                "textMode": "auto",
                "reduceOptions": {"calcs": ["sum"], "fields": "", "values": False},
            },
            "targets": [
                {
                    "refId": "A",
                    # InfluxQL query for Grafana dashboard (not user input)
                    # ligo.scald writes to "1s" retention policy with aggregate tag
                    "query": (  # noqa: S608
                        f'SELECT sum("value") FROM "1s"."{metric.name}" '
                        f"WHERE \"aggregate\" = '{self.scald_aggregate}' "
                        f"AND $timeFilter"
                    ),
                    "rawQuery": True,
                    "resultFormat": "time_series",
                }
            ],
        }

    def dashboard_json(self) -> dict:
        """Generate complete Grafana dashboard JSON."""
        panels = []
        panel_id = 1
        y_pos = 0

        # Pipeline topology section (if set)
        if self._topology and self._topology.get("nodes"):
            # Section header
            panels.append(
                {
                    "id": panel_id,
                    "title": "Pipeline Topology",
                    "type": "row",
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
                    "collapsed": False,
                }
            )
            panel_id += 1
            y_pos += 1

            # Use Mermaid diagram panel (full width)
            panels.append(
                self._make_mermaid_panel(
                    self._topology,
                    panel_id,
                    {"h": 6, "w": 24, "x": 0, "y": y_pos},
                )
            )
            panel_id += 1
            y_pos += 6

        # Group metrics by type
        timing_metrics = [m for m in self._metrics if m.metric_type == "timing"]
        counter_metrics = [m for m in self._metrics if m.metric_type == "counter"]

        # Timing metrics section
        if timing_metrics:
            # Section header
            panels.append(
                {
                    "id": panel_id,
                    "title": "API Timing",
                    "type": "row",
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
                    "collapsed": False,
                }
            )
            panel_id += 1
            y_pos += 1

            # Generate panels for each metric's visualizations
            # Track x position and wrap when exceeding 24 units
            x_pos = 0
            for metric in timing_metrics:
                width = _get_panel_width(metric.panel_config)
                viz_list = _normalize_visualizations(
                    metric.panel_config, metric.metric_type
                )
                for viz_config in viz_list:
                    # Check if we need to wrap to next row
                    if x_pos + width > 24:
                        x_pos = 0
                        y_pos += 8
                    panels.append(
                        self._make_panel_for_viz(
                            metric,
                            viz_config,
                            panel_id,
                            {"h": 8, "w": width, "x": x_pos, "y": y_pos},
                        )
                    )
                    panel_id += 1
                    x_pos += width

            # Move y_pos past the last row
            y_pos += 8

        # Counter metrics section
        if counter_metrics:
            # Section header
            panels.append(
                {
                    "id": panel_id,
                    "title": "Event Counts",
                    "type": "row",
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
                    "collapsed": False,
                }
            )
            panel_id += 1
            y_pos += 1

            # Stat panels row (4 per row) - always show stat for counters
            stat_row_y = y_pos
            for i, metric in enumerate(counter_metrics):
                x_pos = (i % 4) * 6
                if i > 0 and i % 4 == 0:
                    stat_row_y += 4
                panels.append(
                    self._make_stat_panel(
                        metric,
                        panel_id,
                        {"h": 4, "w": 6, "x": x_pos, "y": stat_row_y},
                    )
                )
                panel_id += 1

            y_pos = stat_row_y + 4

            # Generate panels for each counter's visualizations
            # Track x position and wrap when exceeding 24 units
            x_pos = 0
            for metric in counter_metrics:
                width = _get_panel_width(metric.panel_config)
                viz_list = _normalize_visualizations(
                    metric.panel_config, metric.metric_type
                )
                for viz_config in viz_list:
                    # Check if we need to wrap to next row
                    if x_pos + width > 24:
                        x_pos = 0
                        y_pos += 8
                    panels.append(
                        self._make_panel_for_viz(
                            metric,
                            viz_config,
                            panel_id,
                            {"h": 8, "w": width, "x": x_pos, "y": y_pos},
                        )
                    )
                    panel_id += 1
                    x_pos += width

        return {
            "uid": self.dashboard_uid,
            "title": self.dashboard_title,
            "tags": ["sgneskig", "metrics", "auto-generated"],
            "timezone": "browser",
            "schemaVersion": 38,
            "version": 1,
            "refresh": "10s",
            "time": {"from": "now-15m", "to": "now"},
            "templating": {
                "list": [
                    {
                        "name": "datasource",
                        "type": "datasource",
                        "query": "influxdb",
                        "current": {
                            "text": self.datasource_name,
                            "value": self.datasource_name,
                        },
                        "hide": 0,
                        "includeAll": False,
                        "multi": False,
                        "options": [],
                        "refresh": 1,
                        "regex": "",
                    }
                ]
            },
            "annotations": {"list": []},
            "panels": panels,
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 1,
            "links": [],
            "liveNow": False,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # File Output
    # ─────────────────────────────────────────────────────────────────────────

    def write_datasource(self, path: str) -> None:
        """Write datasource provisioning YAML to file."""
        with open(path, "w") as f:
            f.write(self.datasource_yaml())

    def write_dashboard(self, path: str) -> None:
        """Write dashboard JSON to file."""
        with open(path, "w") as f:
            json.dump(self.dashboard_json(), f, indent=2)

    def print_setup_instructions(self) -> str:
        """Print setup instructions for Grafana integration."""
        return f"""
# SGN-SKIG Grafana Setup
# ======================

## 1. Create Datasource (choose one method):

### Option A: Via curl (quick)
{self.datasource_curl_command()}

### Option B: Via provisioning (persistent)
# Save to: grafana/provisioning/datasources/sgneskig.yaml
{self.datasource_yaml()}

## 2. Import Dashboard

# Save dashboard JSON and import via Grafana UI:
#   Dashboards → Import → Upload JSON file

# Or use the API:
curl -u admin:admin -X POST http://localhost:3000/api/dashboards/db \\
  -H 'Content-Type: application/json' \\
  -d '{{"dashboard": <dashboard_json>, "overwrite": true}}'
"""
