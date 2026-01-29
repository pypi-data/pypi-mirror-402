"""ScaldMetricsSink: SGN sink element that writes metrics directly to InfluxDB.

Uses ligo.scald.io.influx.Aggregator for multi-resolution time series storage
with built-in aggregation (1s, 10s, 100s, 1000s, 10000s, 100000s).

No YAML configuration required - schemas are auto-registered from metric structure.

Example usage:
    metrics_sink = ScaldMetricsSink(
        name="metrics_sink",
        hostname="localhost",
        port=8086,
        db="sgneskig_metrics",
    )
    pipeline.connect(creator, metrics_sink)  # Links "metrics" pad automatically
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal

if TYPE_CHECKING:
    from sgneskig.metrics.grafana import GrafanaExporter

import logging

from sgn.base import SinkElement, SinkPad
from sgn.frames import Frame

from sgneskig.metrics.collector import MetricPoint

# Use sgn.sgneskig hierarchy for SGNLOGLEVEL control
_logger = logging.getLogger("sgn.sgneskig.scald_metrics_sink")


@dataclass
class ScaldMetricsSink(SinkElement):
    """SGN sink that writes metrics to InfluxDB with multi-resolution aggregation.

    Wraps ligo.scald.io.influx.Aggregator to handle time series aggregation
    directly to InfluxDB. Schemas are auto-registered from metric structure -
    no YAML configuration file is required.

    Multi-resolution aggregation creates data at:
    - 1s, 10s, 100s, 1000s, 10000s, 100000s resolution

    Args:
        hostname: InfluxDB host (default: localhost)
        port: InfluxDB port (default: 8086)
        db: InfluxDB database name (default: sgneskig_metrics)
        auth: Whether to use authentication (default: False)
        https: Whether to use HTTPS (default: False)
        check_certs: Whether to verify SSL certificates (default: True)
        reduce_dt: Seconds between reductions (default: 300)
        reduce_across_tags: Aggregate across tag values (default: True)
        aggregate: Aggregation function - min, median, max (default: max)
        flush_interval: Seconds between writes to InfluxDB (default: 2.0)
        dry_run: If True, log metrics but don't write to InfluxDB (default: False)
    """

    # InfluxDB connection settings
    hostname: str = "localhost"
    port: int = 8086
    db: str = "sgneskig_metrics"
    auth: bool = False
    https: bool = False
    check_certs: bool = True

    # Aggregation settings
    reduce_dt: int = 300
    reduce_across_tags: bool = True
    aggregate: Literal["min", "median", "max"] = "max"

    # Buffering settings
    flush_interval: float = 2.0

    # Dry-run mode (for testing without InfluxDB)
    dry_run: bool = False

    # Support multiple metrics sources - dynamic pads allow multiple connections
    static_sink_pads: ClassVar[list[str]] = ["metrics"]
    allow_dynamic_sink_pads: ClassVar[bool] = True

    def __post_init__(self):
        super().__post_init__()
        self._logger = _logger

        # Initialize Aggregator (or None in dry-run mode)
        self._aggregator = None

        # Failure counters for observability
        self._schema_failures: int = 0
        self._write_failures: int = 0
        self._points_dropped: int = 0
        self._parse_failures: int = 0

        # Track registered schemas
        self._registered_schemas: set[str] = set()

        # Track metric metadata for Grafana export: name -> {tags: set, type: str}
        self._metric_metadata: dict[str, dict] = {}

        # Metric buffers: measurement -> tag_tuple -> {time: [], value: []}
        self._buffers: dict[str, dict[tuple, dict]] = defaultdict(
            lambda: defaultdict(lambda: {"time": [], "value": []})
        )

        self._last_flush_time: float = time.time()
        self._current_eos: bool = False

        if not self.dry_run:
            self._connect()
        else:
            self._logger.info("ScaldMetricsSink running in dry-run mode")

    def _connect(self) -> None:
        """Connect to InfluxDB and initialize Aggregator.

        Raises:
            RuntimeError: If connection fails and dry_run was not explicitly set.
        """
        try:
            from ligo.scald.io import influx
        except ImportError as e:
            raise RuntimeError(
                "ligo-scald not installed but metrics required. "
                "Install ligo-scald or use dry_run=True"
            ) from e

        # Ensure database exists before connecting
        self._ensure_database()

        try:
            self._aggregator = influx.Aggregator(
                hostname=self.hostname,
                port=self.port,
                db=self.db,
                auth=self.auth,
                https=self.https,
                check_certs=self.check_certs,
                reduce_dt=self.reduce_dt,
                reduce_across_tags=self.reduce_across_tags,
            )
            self._logger.info(
                f"ScaldMetricsSink connected to InfluxDB at "
                f"{self.hostname}:{self.port}/{self.db}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to InfluxDB at {self.hostname}:{self.port}: {e}"
            ) from e

    def _ensure_database(self) -> None:
        """Create InfluxDB database if it doesn't exist.

        Uses InfluxDB's HTTP API directly. CREATE DATABASE is idempotent,
        so this is safe to call even if the database already exists.

        Raises:
            RuntimeError: If InfluxDB is unreachable. This catches connection
                issues early before the pipeline starts processing data.
        """
        import urllib.parse
        import urllib.request

        protocol = "https" if self.https else "http"
        url = f"{protocol}://{self.hostname}:{self.port}/query"
        query = f"CREATE DATABASE {self.db}"
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:  # noqa: S310
                if response.status == 200:
                    self._logger.debug(f"Ensured database '{self.db}' exists")
        except Exception as e:
            raise RuntimeError(
                f"Cannot reach InfluxDB at {self.hostname}:{self.port} to create "
                f"database '{self.db}': {e}"
            ) from e

    def _ensure_schema(self, metric: MetricPoint) -> None:
        """Auto-register schema on first encounter of a metric name.

        Derives schema structure from the metric itself:
        - columns: ("value",) for all metrics
        - tags: extracted from metric.tags keys (with synthetic tag for tagless)
        - aggregate: from self.aggregate setting

        Note: ligo.scald doesn't support tagless metrics, so we add a synthetic
        "source" tag for metrics without tags.
        """
        if metric.name in self._registered_schemas:
            return

        if self._aggregator is None:
            self._registered_schemas.add(metric.name)
            return

        # Derive tag structure from metric
        # ligo.scald requires at least one tag, so add synthetic "source" tag
        if metric.tags:
            tag_names = tuple(sorted(metric.tags.keys()))
        else:
            tag_names = ("source",)
        tag_key = tag_names[0]

        try:
            self._aggregator.register_schema(
                measurement=metric.name,
                columns=("value",),
                column_key="value",
                tags=tag_names,
                tag_key=tag_key,
                aggregate=self.aggregate,
            )
            self._registered_schemas.add(metric.name)
            self._logger.debug(
                f"Registered schema for {metric.name} with tags={tag_names}"
            )
        except Exception as e:
            self._schema_failures += 1
            self._logger.error(
                f"Failed to register schema for {metric.name}: {e} "
                f"(total schema failures: {self._schema_failures})"
            )

    def _buffer_metric(self, metric: MetricPoint) -> None:
        """Add a metric to the buffer for batch writing."""
        # Ensure schema exists
        self._ensure_schema(metric)

        # Track metric metadata for Grafana export
        self._track_metric_metadata(metric)

        # Create tag tuple for grouping (sorted for consistency)
        tag_tuple = tuple(sorted(metric.tags.items())) if metric.tags else ()

        # Buffer the metric (timestamp is GPS time from MetricsCollectorMixin)
        buffer = self._buffers[metric.name][tag_tuple]
        buffer["time"].append(metric.timestamp)
        buffer["value"].append(metric.value)

    def _track_metric_metadata(self, metric: MetricPoint) -> None:
        """Track metric metadata for Grafana dashboard generation."""
        if metric.name not in self._metric_metadata:
            # Infer type from metric name
            if metric.name.endswith("_time"):
                metric_type = "timing"
            elif any(
                keyword in metric.name
                for keyword in ["count", "created", "skipped", "total"]
            ):
                metric_type = "counter"
            else:
                metric_type = "gauge"

            self._metric_metadata[metric.name] = {
                "tags": set(),
                "type": metric_type,
            }

        # Accumulate all tag keys we've seen
        if metric.tags:
            self._metric_metadata[metric.name]["tags"].update(metric.tags.keys())

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive metrics frame and buffer for aggregation.

        Expected frame format:
        - frame.data: list[MetricPoint] or list[dict]
        """
        if frame.EOS:
            self._current_eos = True
            self.mark_eos(pad)

        if frame.is_gap or frame.data is None:
            return

        # Handle both list of MetricPoints and list of dicts
        metrics = frame.data if isinstance(frame.data, list) else [frame.data]

        for item in metrics:
            if isinstance(item, MetricPoint):
                self._buffer_metric(item)
            elif isinstance(item, dict):
                # Convert dict to MetricPoint
                try:
                    metric = MetricPoint(
                        name=item.get("name", item.get("metric", "unknown")),
                        value=item.get("value", 0.0),
                        timestamp=item.get("timestamp", time.time()),
                        tags=item.get("tags", {}),
                    )
                    self._buffer_metric(metric)
                except Exception as e:
                    self._parse_failures += 1
                    self._logger.error(
                        f"Failed to parse metric dict: {e} "
                        f"(total parse failures: {self._parse_failures})"
                    )

    def internal(self) -> None:
        """Flush buffers periodically or when full."""
        current_time = time.time()

        # Check if we should flush
        should_flush = False

        # Flush on EOS
        if self.at_eos:
            should_flush = True

        # Flush on interval
        elif (current_time - self._last_flush_time) >= self.flush_interval:
            should_flush = True

        if should_flush:
            self._flush_buffers()
            self._last_flush_time = current_time

    def _flush_buffers(self) -> None:
        """Write buffered metrics to InfluxDB via Aggregator.

        Note: ligo.scald requires at least one tag for store_columns, so
        metrics without tags use a synthetic "source=sgneskig" tag.
        """
        for measurement, tag_buffers in self._buffers.items():
            if not tag_buffers:
                continue

            # Convert to store_columns format:
            # {tag_vals: {'time': [...], 'fields': {'value': [...]}}}
            data: dict[str | tuple[str, ...], dict] = {}
            total_points = 0

            for tag_tuple, buffer in tag_buffers.items():
                if not buffer["time"]:
                    continue

                # Extract tag values for the key
                # ligo.scald requires at least one tag, so use "sgneskig" for tagless
                tag_key: str | tuple[str, ...]
                if tag_tuple:
                    tag_values = tuple(v for k, v in tag_tuple)
                    if len(tag_values) == 1:
                        tag_key = tag_values[0]
                    else:
                        tag_key = tag_values
                else:
                    # Synthetic tag for tagless metrics (matches schema registration)
                    tag_key = "sgneskig"

                data[tag_key] = {
                    "time": buffer["time"].copy(),
                    "fields": {"value": buffer["value"].copy()},
                }
                total_points += len(buffer["time"])

                # Clear buffer
                buffer["time"].clear()
                buffer["value"].clear()

            if not data:
                continue

            if self.dry_run or self._aggregator is None:
                self._logger.info(
                    f"[DRY-RUN] Would write {total_points} points to {measurement}"
                )
                continue

            try:
                self._aggregator.store_columns(
                    measurement, data, aggregate=self.aggregate
                )
                self._logger.debug(f"Wrote {total_points} points to {measurement}")
            except Exception as e:
                self._write_failures += 1
                self._points_dropped += total_points
                self._logger.error(
                    f"Failed to write {total_points} points to {measurement}: {e} "
                    f"(total write failures: {self._write_failures}, "
                    f"points dropped: {self._points_dropped})"
                )

    def get_buffered_count(self) -> int:
        """Get total number of buffered metric points."""
        total = 0
        for tag_buffers in self._buffers.values():
            for buffer in tag_buffers.values():
                total += len(buffer["time"])
        return total

    def get_failure_stats(self) -> dict[str, int]:
        """Get failure statistics for observability.

        Returns:
            Dictionary with schema_failures, write_failures, points_dropped,
            and parse_failures.
        """
        return {
            "schema_failures": self._schema_failures,
            "write_failures": self._write_failures,
            "points_dropped": self._points_dropped,
            "parse_failures": self._parse_failures,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Grafana Integration
    # ─────────────────────────────────────────────────────────────────────────

    def get_grafana_exporter(
        self,
        dashboard_title: str = "SGN-SKIG Metrics",
        grafana_influxdb_url: str | None = None,
    ) -> GrafanaExporter:
        """Get a GrafanaExporter configured with observed metrics.

        The exporter is pre-populated with all metrics that have flowed
        through this sink, with types and tags inferred from the data.

        Args:
            dashboard_title: Title for the generated dashboard
            grafana_influxdb_url: InfluxDB URL as seen from Grafana
                                  (default: http://influxdb:8086 for Docker)

        Returns:
            GrafanaExporter configured with this sink's metrics
        """
        from sgneskig.metrics.grafana import GrafanaExporter

        # Default to Docker network URL
        if grafana_influxdb_url is None:
            grafana_influxdb_url = "http://influxdb:8086"

        exporter = GrafanaExporter(
            datasource_name=self.db,
            influxdb_url=grafana_influxdb_url,
            influxdb_db=self.db,
            dashboard_title=dashboard_title,
        )

        # Add all observed metrics
        for name, metadata in self._metric_metadata.items():
            tags = sorted(metadata["tags"])
            metric_type = metadata["type"]

            if metric_type == "timing":
                exporter.add_timing_metric(name, tags=tags)
            elif metric_type == "counter":
                exporter.add_counter_metric(name, tags=tags)
            else:
                exporter.add_gauge_metric(name, tags=tags)

        return exporter

    def export_grafana_dashboard(
        self,
        path: str,
        dashboard_title: str = "SGN-SKIG Metrics",
        grafana_influxdb_url: str | None = None,
    ) -> None:
        """Export a Grafana dashboard JSON file based on observed metrics.

        Call this after the pipeline has processed some data to generate
        a dashboard with panels for all observed metrics.

        Args:
            path: Output path for dashboard JSON
            dashboard_title: Title for the dashboard
            grafana_influxdb_url: InfluxDB URL as seen from Grafana
        """
        exporter = self.get_grafana_exporter(dashboard_title, grafana_influxdb_url)
        exporter.write_dashboard(path)
        self._logger.info(f"Exported Grafana dashboard to {path}")

    def export_grafana_datasource(self, path: str) -> None:
        """Export a Grafana datasource provisioning YAML file.

        Args:
            path: Output path for datasource YAML
        """
        exporter = self.get_grafana_exporter()
        exporter.write_datasource(path)
        self._logger.info(f"Exported Grafana datasource to {path}")
