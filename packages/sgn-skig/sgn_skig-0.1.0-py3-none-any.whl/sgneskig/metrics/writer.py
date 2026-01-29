"""MetricsWriter: Direct InfluxDB writer for metrics.

Provides a shared writer that elements can use to write metrics directly
to InfluxDB without going through pipeline pads. This enables metrics
collection from sinks (which have no output pads) and simplifies pipeline
topology by eliminating metrics pad wiring.

Example usage:
    # Create shared writer (typically in MetricsPipeline)
    writer = MetricsWriter(
        hostname="localhost",
        port=8086,
        db="sgneskig_metrics",
    )

    # Elements use it directly
    class MySink(SinkElement, MetricsCollectorMixin):
        def __post_init__(self):
            super().__post_init__()
            self._init_metrics()

        def pull(self, pad, frame):
            with self.time_operation("process_time"):
                self._process(frame)
            # Metrics written automatically on flush
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from sgneskig.metrics.collector import MetricPoint

_logger = logging.getLogger("sgn.sgneskig.metrics.writer")


@dataclass
class MetricsWriter:
    """Direct InfluxDB writer for metrics using ligo.scald Aggregator.

    Thread-safe writer that can be shared across multiple elements.
    Handles buffering, schema registration, and periodic flushing.

    Args:
        hostname: InfluxDB host (default: localhost)
        port: InfluxDB port (default: 8086)
        db: InfluxDB database name (default: sgneskig_metrics)
        auth: Whether to use authentication (default: False)
        https: Whether to use HTTPS (default: False)
        check_certs: Whether to verify SSL certificates (default: True)
        reduce_dt: Seconds between reductions (default: 300)
        reduce_across_tags: Aggregate across tag values (default: True)
        aggregate: Aggregation function (default: max)
        flush_interval: Seconds between auto-flushes (default: 2.0)
        dry_run: Log metrics without writing to InfluxDB (default: False)
    """

    hostname: str = "localhost"
    port: int = 8086
    db: str = "sgneskig_metrics"
    auth: bool = False
    https: bool = False
    check_certs: bool = True
    reduce_dt: int = 300
    reduce_across_tags: bool = True
    aggregate: Literal["min", "median", "max"] = "max"
    flush_interval: float = 2.0
    dry_run: bool = False

    # Internal state (initialized in __post_init__)
    _aggregator: object | None = field(default=None, repr=False)
    _registered_schemas: set = field(default_factory=set, repr=False)
    _buffers: dict = field(default_factory=dict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _last_flush_time: float = field(default=0.0, repr=False)

    # Failure counters for observability
    _schema_failures: int = field(default=0, repr=False)
    _write_failures: int = field(default=0, repr=False)
    _points_dropped: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        # Initialize buffers
        self._buffers = defaultdict(
            lambda: defaultdict(lambda: {"time": [], "value": []})
        )
        self._last_flush_time = time.time()

        if not self.dry_run:
            self._connect()
        else:
            _logger.info("MetricsWriter running in dry-run mode")

    def _connect(self) -> None:
        """Connect to InfluxDB and initialize Aggregator.

        Raises:
            RuntimeError: If connection fails and dry_run was not explicitly set.
                This ensures infrastructure problems are caught early rather than
                silently degrading to dry-run mode.
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
            _logger.info(
                f"MetricsWriter connected to InfluxDB at "
                f"{self.hostname}:{self.port}/{self.db}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to InfluxDB at {self.hostname}:{self.port}: {e}"
            ) from e

    def _ensure_database(self) -> None:
        """Create InfluxDB database if it doesn't exist.

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
                    _logger.debug(f"Ensured database '{self.db}' exists")
        except Exception as e:
            raise RuntimeError(
                f"Cannot reach InfluxDB at {self.hostname}:{self.port} to create "
                f"database '{self.db}': {e}"
            ) from e

    def _ensure_schema(self, metric: MetricPoint) -> None:
        """Auto-register schema on first encounter of a metric name."""
        if metric.name in self._registered_schemas:
            return

        if self._aggregator is None:
            self._registered_schemas.add(metric.name)
            return

        # ligo.scald requires at least one tag
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
            _logger.debug(f"Registered schema for {metric.name} with tags={tag_names}")
        except Exception as e:
            self._schema_failures += 1
            _logger.error(
                f"Failed to register schema for {metric.name}: {e} "
                f"(total schema failures: {self._schema_failures})"
            )

    def write(self, metrics: list[MetricPoint]) -> None:
        """Write metrics to buffer (thread-safe).

        Metrics are buffered and periodically flushed to InfluxDB.

        Args:
            metrics: List of MetricPoint objects to write
        """
        if not metrics:
            return

        with self._lock:
            for metric in metrics:
                self._buffer_metric(metric)

            # Check if we should auto-flush
            current_time = time.time()
            if (current_time - self._last_flush_time) >= self.flush_interval:
                self._flush_buffers_locked()
                self._last_flush_time = current_time

    def _buffer_metric(self, metric: MetricPoint) -> None:
        """Add a metric to the buffer (must hold lock)."""
        self._ensure_schema(metric)

        # Create tag tuple for grouping
        tag_tuple = tuple(sorted(metric.tags.items())) if metric.tags else ()

        buffer = self._buffers[metric.name][tag_tuple]
        buffer["time"].append(metric.timestamp)
        buffer["value"].append(metric.value)

    def flush(self) -> None:
        """Force flush all buffered metrics to InfluxDB."""
        with self._lock:
            self._flush_buffers_locked()
            self._last_flush_time = time.time()

    def _flush_buffers_locked(self) -> None:
        """Write buffered metrics to InfluxDB (must hold lock)."""
        for measurement, tag_buffers in self._buffers.items():
            if not tag_buffers:
                continue

            # Convert to store_columns format
            data: dict[str | tuple[str, ...], dict] = {}
            total_points = 0

            for tag_tuple, buffer in tag_buffers.items():
                if not buffer["time"]:
                    continue

                # Extract tag values for the key
                tag_key: str | tuple[str, ...]
                if tag_tuple:
                    tag_values = tuple(v for k, v in tag_tuple)
                    if len(tag_values) == 1:
                        tag_key = tag_values[0]
                    else:
                        tag_key = tag_values
                else:
                    tag_key = "sgneskig"

                data[tag_key] = {
                    "time": buffer["time"].copy(),
                    "fields": {"value": buffer["value"].copy()},
                }
                total_points += len(buffer["time"])

                buffer["time"].clear()
                buffer["value"].clear()

            if not data:
                continue

            if self.dry_run or self._aggregator is None:
                _logger.info(
                    f"[DRY-RUN] Would write {total_points} points to {measurement}"
                )
                continue

            try:
                self._aggregator.store_columns(
                    measurement, data, aggregate=self.aggregate
                )
                _logger.debug(f"Wrote {total_points} points to {measurement}")
            except Exception as e:
                self._write_failures += 1
                self._points_dropped += total_points
                _logger.error(
                    f"Failed to write {total_points} points to {measurement}: {e} "
                    f"(total write failures: {self._write_failures}, "
                    f"points dropped: {self._points_dropped})"
                )

    def get_buffered_count(self) -> int:
        """Get total number of buffered metric points."""
        with self._lock:
            total = 0
            for tag_buffers in self._buffers.values():
                for buffer in tag_buffers.values():
                    total += len(buffer["time"])
            return total

    def get_failure_stats(self) -> dict[str, int]:
        """Get failure statistics for observability.

        Returns:
            Dictionary with schema_failures, write_failures, and points_dropped
        """
        return {
            "schema_failures": self._schema_failures,
            "write_failures": self._write_failures,
            "points_dropped": self._points_dropped,
        }

    def close(self) -> None:
        """Flush remaining metrics and close connection."""
        self.flush()

        # Report any failures on close
        if self._write_failures > 0 or self._schema_failures > 0:
            _logger.warning(
                f"MetricsWriter closed with failures: "
                f"{self._write_failures} write failures, "
                f"{self._schema_failures} schema failures, "
                f"{self._points_dropped} points dropped"
            )
        else:
            _logger.info("MetricsWriter closed")
