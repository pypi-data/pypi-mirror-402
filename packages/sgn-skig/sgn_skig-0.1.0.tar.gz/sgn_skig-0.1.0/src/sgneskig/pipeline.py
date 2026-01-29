"""MetricsPipeline: Pipeline subclass with integrated metrics infrastructure.

Provides automatic discovery of metrics from elements using MetricsCollectorMixin,
manifest generation, and Grafana dashboard export.

Example:
    from sgneskig.pipeline import MetricsPipeline

    pipeline = MetricsPipeline(
        name="superevent-pipeline",
        influxdb_db="sgneskig_metrics",
    )
    pipeline.insert(source, creator, output_sink)
    pipeline.connect(source, creator)
    pipeline.connect(creator, output_sink)

    # Export metrics manifest (single source of truth)
    pipeline.write_metrics_manifest("metrics.yaml")

    # Generate Grafana dashboard from discovered metrics
    pipeline.export_grafana_dashboard("grafana/dashboard.json")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import yaml
from sgn.apps import Pipeline

from sgneskig.metrics.collector import MetricDeclaration, MetricsCollectorMixin

if TYPE_CHECKING:
    from sgn.base import Element

    from sgneskig.metrics.grafana import GrafanaExporter
    from sgneskig.metrics.writer import MetricsWriter

# Use sgn.sgneskig hierarchy for SGNLOGLEVEL control
logger = logging.getLogger("sgn.sgneskig.pipeline")


@dataclass
class MetricsPipeline(Pipeline):
    """Pipeline with integrated metrics infrastructure.

    Extends SGN Pipeline to provide:
    - Automatic discovery of metrics from elements using MetricsCollectorMixin
    - Direct InfluxDB write via shared MetricsWriter (no metrics pad wiring needed)
    - Metrics manifest generation (YAML) for CI/CD and tooling
    - Grafana dashboard and datasource export

    Attributes:
        name: Pipeline name for manifest and dashboard titles
        influxdb_host: InfluxDB hostname (default: localhost)
        influxdb_port: InfluxDB port (default: 8086)
        influxdb_db: InfluxDB database name (default: sgneskig_metrics)
        grafana_influxdb_url: URL for Grafana to reach InfluxDB
            (default: http://influxdb:8086)
        metrics_dry_run: If True, log metrics but don't write to InfluxDB
    """

    name: str = "sgneskig-pipeline"
    influxdb_host: str = "localhost"
    influxdb_port: int = 8086
    influxdb_db: str = "sgneskig_metrics"
    grafana_influxdb_url: str = "http://influxdb:8086"
    metrics_dry_run: bool = False

    # Internal state
    _metrics_elements: list[Element] = field(default_factory=list, repr=False)
    _metrics_writer: MetricsWriter | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        # Call Pipeline.__init__ since it's not a dataclass
        Pipeline.__init__(self)

        # Create shared MetricsWriter for direct InfluxDB writes
        from sgneskig.metrics.writer import MetricsWriter

        self._metrics_writer = MetricsWriter(
            hostname=self.influxdb_host,
            port=self.influxdb_port,
            db=self.influxdb_db,
            dry_run=self.metrics_dry_run,
        )
        logger.info(
            f"MetricsPipeline created with MetricsWriter for "
            f"{self.influxdb_host}:{self.influxdb_port}/{self.influxdb_db}"
        )

    def insert(self, *elements: Element) -> None:
        """Insert elements into the pipeline and configure metrics writer.

        Overrides Pipeline.insert() to automatically configure elements
        that use MetricsCollectorMixin with the shared MetricsWriter.

        Also validates metrics schemas to catch duplicates and issues early.

        Args:
            *elements: Elements to insert into the pipeline
        """
        # Call parent insert
        super().insert(*elements)

        # Configure metrics writer for elements that use MetricsCollectorMixin
        for element in elements:
            if isinstance(element, MetricsCollectorMixin):
                element.set_metrics_writer(self._metrics_writer)
                logger.debug(f"Configured MetricsWriter for element '{element.name}'")

        # Validate schema after all elements are inserted
        self._validate_metrics_schema()

    def close(self) -> None:
        """Flush metrics and close the pipeline.

        Should be called when shutting down to ensure all buffered
        metrics are written to InfluxDB.
        """
        if self._metrics_writer:
            self._metrics_writer.close()
            logger.info("MetricsPipeline closed, metrics flushed")

    def _validate_metrics_schema(self) -> None:
        """Validate metrics schema across all pipeline elements.

        Checks for:
        - Duplicate metric names (without tags) that would merge data
        - Invalid metric types

        Logs warnings for issues but does not raise errors to maintain
        backwards compatibility. Call during insert() to catch issues early.
        """
        # Track metrics by name to detect duplicates
        # Key: metric name, Value: list of (element_name, metric) tuples
        metrics_by_name: dict[str, list[tuple[str, MetricDeclaration]]] = {}

        for element in self.elements:
            if not isinstance(element, MetricsCollectorMixin):
                continue

            # Get element's metrics schema
            metrics = getattr(element, "_metrics_schema", None)
            if metrics is None:
                metrics = getattr(element.__class__, "metrics_schema", [])

            for metric in metrics:
                # Validate metric type
                if metric.metric_type not in ("timing", "counter", "gauge"):
                    logger.warning(
                        f"Element '{element.name}': Metric '{metric.name}' has "
                        f"invalid type '{metric.metric_type}'. "
                        f"Valid types: timing, counter, gauge"
                    )

                # Track for duplicate detection
                if metric.name not in metrics_by_name:
                    metrics_by_name[metric.name] = []
                metrics_by_name[metric.name].append((element.name, metric))

        # Check for problematic duplicates
        for name, occurrences in metrics_by_name.items():
            if len(occurrences) <= 1:
                continue

            # Group by tags to see if data is distinguishable
            tags_variants = set()
            for _element_name, metric in occurrences:
                tags_variants.add(tuple(sorted(metric.tags)))

            # If all occurrences have the same tags (or no tags), data is merged
            if len(tags_variants) == 1:
                tags = occurrences[0][1].tags
                element_names = [e for e, _ in occurrences]

                if not tags:
                    # No tags - truly indistinguishable
                    logger.warning(
                        f"Metric '{name}' defined in multiple elements "
                        f"({', '.join(element_names)}) with no tags. "
                        f"Data will be merged and indistinguishable by source. "
                        f"Consider adding unique tags or renaming."
                    )
                else:
                    # Same tags - could still be distinguishable by tag values
                    logger.debug(
                        f"Metric '{name}' defined in multiple elements "
                        f"({', '.join(element_names)}) with tags {tags}. "
                        f"Data is distinguishable if tag values differ."
                    )

    # ─────────────────────────────────────────────────────────────────────────
    # Schema Discovery
    # ─────────────────────────────────────────────────────────────────────────

    def get_metrics_schema(self) -> list[MetricDeclaration]:
        """Collect all declared metrics from pipeline elements.

        Discovers metrics by iterating through all elements and collecting
        their metrics schema. Checks both instance-level `_metrics_schema`
        (for dynamically-named metrics) and class-level `metrics_schema`.

        Returns:
            List of all MetricDeclaration objects from the pipeline
        """
        schema: list[MetricDeclaration] = []
        # Key by (name, tags) - same name with different tags are different metrics
        seen_keys: set[tuple[str, tuple[str, ...]]] = set()

        for element in self.elements:
            if isinstance(element, MetricsCollectorMixin):
                # Check instance-level first (for dynamically-named metrics)
                # then fall back to class-level
                metrics = getattr(element, "_metrics_schema", None)
                if metrics is None:
                    metrics = getattr(element.__class__, "metrics_schema", [])

                for metric in metrics:
                    # Key by (name, tags) for different tag dimensions
                    key = (metric.name, tuple(metric.tags))
                    if key not in seen_keys:
                        schema.append(metric)
                        seen_keys.add(key)
                    elif not metric.tags:
                        # Same name with NO tags - data truly indistinguishable
                        logger.warning(
                            f"Metric '{metric.name}' (no tags) from {element.name} "
                            f"duplicates an existing metric. Data will be merged "
                            f"and indistinguishable by source."
                        )
                    # If tags exist, data is likely distinguishable by tag values
                    # (e.g., worker_id=0 vs worker_id=1) - no warning needed

        return schema

    def get_metrics_elements(self) -> list[Element]:
        """Get all elements that use MetricsCollectorMixin.

        Returns:
            List of elements that have metrics capabilities
        """
        return [e for e in self.elements if isinstance(e, MetricsCollectorMixin)]

    def get_metrics_by_element(self) -> dict[str, list[MetricDeclaration]]:
        """Get metrics grouped by element name.

        Returns:
            Dictionary mapping element names to their metric declarations
        """
        result: dict[str, list[MetricDeclaration]] = {}

        for element in self.elements:
            if isinstance(element, MetricsCollectorMixin):
                # Check instance-level first (for dynamically-named metrics)
                # then fall back to class-level
                metrics = getattr(element, "_metrics_schema", None)
                if metrics is None:
                    metrics = getattr(element.__class__, "metrics_schema", [])
                if metrics:
                    result[element.name] = list(metrics)

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Manifest Export
    # ─────────────────────────────────────────────────────────────────────────

    def metrics_manifest(self) -> dict:
        """Generate metrics manifest as a dictionary.

        The manifest is a portable description of all metrics in the pipeline,
        suitable for consumption by CLI tools, CI/CD pipelines, etc.

        Returns:
            Dictionary containing the full metrics manifest
        """
        metrics_by_element = self.get_metrics_by_element()

        # Build metrics list with element sources
        metrics_list = []
        for element_name, metrics in metrics_by_element.items():
            for metric in metrics:
                metrics_list.append(
                    {
                        "name": metric.name,
                        "type": metric.metric_type,
                        "tags": metric.tags,
                        "description": metric.description,
                        "unit": metric.unit,
                        "source_element": element_name,
                    }
                )

        # Build elements list
        elements_list = []
        for element_name, metrics in metrics_by_element.items():
            element = self._registry.get(element_name)
            elements_list.append(
                {
                    "name": element_name,
                    "type": element.__class__.__name__ if element else "Unknown",
                    "metrics": [m.name for m in metrics],
                }
            )

        return {
            "version": "1.0",
            "pipeline": self.name,
            "influxdb": {
                "host": self.influxdb_host,
                "port": self.influxdb_port,
                "database": self.influxdb_db,
            },
            "grafana": {
                "influxdb_url": self.grafana_influxdb_url,
            },
            "metrics": metrics_list,
            "elements": elements_list,
        }

    def write_metrics_manifest(self, path: str) -> None:
        """Write metrics manifest to a YAML file.

        Args:
            path: Output file path for the YAML manifest
        """
        manifest = self.metrics_manifest()

        with open(path, "w") as f:
            yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Wrote metrics manifest to {path}")

    # ─────────────────────────────────────────────────────────────────────────
    # Grafana Export
    # ─────────────────────────────────────────────────────────────────────────

    def get_grafana_exporter(
        self, dashboard_title: str | None = None
    ) -> GrafanaExporter:
        """Get a GrafanaExporter configured with discovered metrics.

        Args:
            dashboard_title: Optional custom title for the dashboard

        Returns:
            GrafanaExporter instance with all discovered metrics added
        """
        from sgneskig.metrics.grafana import GrafanaExporter

        exporter = GrafanaExporter(
            datasource_name=self.influxdb_db,
            influxdb_url=self.grafana_influxdb_url,
            influxdb_db=self.influxdb_db,
            dashboard_title=dashboard_title or f"{self.name} Metrics",
        )

        # Add all discovered metrics
        for metric in self.get_metrics_schema():
            if metric.metric_type == "timing":
                exporter.add_timing_metric(
                    metric.name,
                    tags=metric.tags,
                    description=metric.description,
                    panel_config=metric.panel_config,
                )
            elif metric.metric_type == "counter":
                exporter.add_counter_metric(
                    metric.name,
                    tags=metric.tags,
                    description=metric.description,
                    panel_config=metric.panel_config,
                )
            elif metric.metric_type == "gauge":
                exporter.add_gauge_metric(
                    metric.name,
                    tags=metric.tags,
                    description=metric.description,
                    panel_config=metric.panel_config,
                )

        # Add pipeline topology for visualization
        topology = self.get_topology()
        if topology.get("nodes"):
            exporter.set_topology(topology)

        return exporter

    def export_grafana_dashboard(
        self, path: str, dashboard_title: str | None = None
    ) -> None:
        """Generate and write Grafana dashboard JSON.

        Args:
            path: Output file path for the dashboard JSON
            dashboard_title: Optional custom title for the dashboard
        """
        exporter = self.get_grafana_exporter(dashboard_title)
        exporter.write_dashboard(path)
        logger.info(f"Wrote Grafana dashboard to {path}")

    def export_grafana_datasource(self, path: str) -> None:
        """Generate and write Grafana datasource provisioning YAML.

        Args:
            path: Output file path for the datasource YAML
        """
        exporter = self.get_grafana_exporter()
        exporter.write_datasource(path)
        logger.info(f"Wrote Grafana datasource to {path}")

    def dashboard_json(self, dashboard_title: str | None = None) -> dict:
        """Get Grafana dashboard as a dictionary.

        Args:
            dashboard_title: Optional custom title for the dashboard

        Returns:
            Dashboard configuration dictionary
        """
        exporter = self.get_grafana_exporter(dashboard_title)
        return exporter.dashboard_json()

    # ─────────────────────────────────────────────────────────────────────────
    # Topology / Graph Visualization
    # ─────────────────────────────────────────────────────────────────────────

    def get_topology(self) -> dict:
        """Get pipeline topology as nodes and edges for visualization.

        Returns a dictionary with:
        - nodes: List of element nodes with id, name, type, and metrics info
        - edges: List of connections between elements

        This format is suitable for Grafana's Node Graph panel or other
        graph visualization tools.

        Returns:
            Dictionary with 'nodes' and 'edges' keys
        """
        # Build nodes from elements
        nodes = []
        element_to_id = {}  # element name -> node id

        for i, element in enumerate(self.elements):
            node_id = f"node_{i}"
            element_to_id[element.name] = node_id

            # Check if element has metrics
            has_metrics = isinstance(element, MetricsCollectorMixin)
            if has_metrics:
                # Check instance-level first (for dynamically-named metrics)
                metrics_schema = getattr(element, "_metrics_schema", None)
                if metrics_schema is None:
                    metrics_schema = getattr(element.__class__, "metrics_schema", [])
            else:
                metrics_schema = []

            # Get pad names from element
            source_pad_names = list(getattr(element, "source_pad_names", []))
            sink_pad_names = list(getattr(element, "sink_pad_names", []))

            nodes.append(
                {
                    "id": node_id,
                    "name": element.name,
                    "type": element.__class__.__name__,
                    "has_metrics": has_metrics,
                    "metrics": [m.name for m in metrics_schema],
                    "source_pads": source_pad_names,
                    "sink_pads": sink_pad_names,
                    # For Grafana Node Graph arc coloring
                    "mainStat": element.__class__.__name__,
                    "secondaryStat": f"{len(metrics_schema)} metrics"
                    if metrics_schema
                    else "",
                }
            )

        # Build edges from pipeline connections
        edges = []
        for source_pad, sink_pad in self.edges():
            # Parse pad names: "element_name:src|snk:pad_name"
            # Element names may contain colons, so split from the right
            # to get the last two parts (direction and pad_name)
            source_parts = source_pad.rsplit(":", 2)
            sink_parts = sink_pad.rsplit(":", 2)

            # source_parts = ["element_name", "src", "pad_name"]
            source_element = source_parts[0] if len(source_parts) >= 3 else source_pad
            sink_element = sink_parts[0] if len(sink_parts) >= 3 else sink_pad

            source_id = element_to_id.get(source_element)
            sink_id = element_to_id.get(sink_element)

            if source_id and sink_id:
                edges.append(
                    {
                        "id": f"{source_id}_{sink_id}",
                        "source": source_id,
                        "target": sink_id,
                        "source_pad": source_parts[2]
                        if len(source_parts) > 2
                        else "out",
                        "target_pad": sink_parts[2] if len(sink_parts) > 2 else "in",
                    }
                )

        return {"nodes": nodes, "edges": edges}
