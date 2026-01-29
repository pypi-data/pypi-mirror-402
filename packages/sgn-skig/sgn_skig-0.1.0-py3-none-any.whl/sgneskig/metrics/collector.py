"""MetricsCollectorMixin: Reusable mixin for collecting metrics from SGN elements.

This mixin can be added to any SGN element (Source, Transform, or Sink) to enable
metric collection with timing, counts, and custom metrics.

Metrics Modes
=============

The mixin supports two modes for emitting metrics:

**Direct Mode (default, recommended)**
    metrics_mode="direct"

    Metrics are written directly to InfluxDB via a shared MetricsWriter.
    This is the recommended mode because:
    - Works for ALL element types including sinks (which have no output pads)
    - Simpler pipeline topology (no metrics pad wiring needed)
    - MetricsPipeline automatically configures the shared writer

    Use direct mode unless you have a specific need for pad mode.

**Pad Mode (legacy/advanced)**
    metrics_mode="pad"

    Metrics are emitted through a dedicated "metrics" output pad as Frame data.
    Use this mode when you need to:
    - Transform or filter metrics before writing (e.g., aggregation, sampling)
    - Route metrics to multiple destinations
    - Use a custom metrics sink (not InfluxDB)

    Pad mode requires manual wiring in your pipeline:
    1. Add metrics_pad_name to source_pad_names
    2. Connect the metrics pad to a downstream sink
    3. Handle the metrics pad in your new() method

Features
========
- Manual timing via context manager: time_operation()
- Automatic cycle elapsed time tracking via track_elapsed_time=True
- Counter accumulation with increment_counter()
- Generic metric recording with record_metric()
- Direct InfluxDB write or pad-based emission

Example usage (direct mode - default):
    @dataclass
    class MySink(SinkElement, MetricsCollectorMixin):
        def __post_init__(self):
            super().__post_init__()
            self._init_metrics()

        def pull(self, pad, frame):
            with self.time_operation("process_time"):
                self._process(frame)
            self.emit_metrics()  # Write to InfluxDB directly

Example usage (pad mode - advanced):
    @dataclass
    class MyTransform(TransformElement, MetricsCollectorMixin):
        metrics_mode: str = "pad"  # Use pad-based emission
        metrics_pad_name: str = "metrics"

        def __post_init__(self):
            # Include metrics pad in source pads
            self.source_pad_names = ["out", self.metrics_pad_name]
            super().__post_init__()
            self._init_metrics()

        def new(self, pad: SourcePad) -> Frame:
            pad_name = self.rsrcs.get(pad, pad.pad_name)
            if pad_name == self.metrics_pad_name:
                return self.new_metrics_frame(eos=eos)
            # ... handle other pads

Automatic elapsed time tracking:
    When track_elapsed_time=True, the mixin automatically measures cycle time:
    - For transforms: pull() -> internal() -> new() cycle
    - For sinks: Use emit_metrics() at the end of pull() to record elapsed time

    @dataclass
    class MyTransform(TransformElement, MetricsCollectorMixin):
        track_elapsed_time: bool = True
        elapsed_metric_name: str = "my_transform_elapsed"
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Literal

if TYPE_CHECKING:
    from sgn.frames import Frame

    from sgneskig.metrics.writer import MetricsWriter


def _gps_now() -> float:
    """Get current GPS time with sub-second precision.

    ligo.scald expects GPS timestamps, not Unix timestamps. This function
    converts the current wall clock time to GPS time.

    Note: lal.GPSTimeNow() returns integer seconds only (gpsNanoSeconds=0).
    To preserve sub-second precision for accurate latency measurements, we
    use time.time() for high-precision timing and compute the GPS-Unix offset
    from lal to correctly handle leap seconds.

    Returns:
        Current GPS time as float with sub-second precision
    """
    unix_time = time.time()
    try:
        from lal import GPSTimeNow

        # Compute GPS-Unix offset using lal (handles leap seconds correctly)
        # Then apply to high-precision Unix time
        gps_int = int(GPSTimeNow())
        unix_int = int(unix_time)
        offset = gps_int - unix_int
        return unix_time + offset
    except ImportError:
        # Fallback if lal not available - use approximate offset
        # GPS epoch is 1980-01-06, Unix epoch is 1970-01-01
        # Offset is ~315964800 seconds plus leap seconds (~18 as of 2024)
        GPS_UNIX_OFFSET = 315964818
        return unix_time - GPS_UNIX_OFFSET


@dataclass
class MetricDeclaration:
    """Declarative schema for a metric collected by an element.

    Elements declare their metrics upfront using this schema. The MetricsPipeline
    can then discover all metrics in the pipeline and generate manifests,
    Grafana dashboards, etc.

    Attributes:
        name: Metric name (e.g., "events_created")
        metric_type: One of "timing", "counter", or "gauge"
        tags: List of tag names this metric uses (e.g., ["pipeline"])
        description: Human-readable description for dashboards
        unit: Unit of measurement (e.g., "s" for seconds, "" for counts)
        panel_config: Optional Grafana panel overrides (unit, draw_style, etc.)
    """

    name: str
    metric_type: Literal["timing", "counter", "gauge"]
    tags: list[str] = field(default_factory=list)
    description: str = ""
    unit: str = ""
    panel_config: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Set default unit based on type
        if not self.unit and self.metric_type == "timing":
            self.unit = "s"

    def get_grafana_unit(self) -> str:
        """Get Grafana unit with fallback to type defaults."""
        if self.panel_config.get("unit"):
            return self.panel_config["unit"]
        if self.unit:
            return self.unit
        return {"timing": "s", "counter": "short", "gauge": "short"}.get(
            self.metric_type, "short"
        )

    def get_panel_title(self) -> str:
        """Get panel title with fallbacks.

        Priority:
        1. panel_config["title"] - explicit override
        2. description - from metrics schema
        3. Auto-derived from metric name (snake_case → Title Case)
        """
        if self.panel_config.get("title"):
            return self.panel_config["title"]
        if self.description:
            return self.description
        # Auto-derive from metric name: "foo_bar_time" → "Foo Bar Time"
        return self.name.replace("_", " ").title()


# Type alias for tuple shorthand: (name, type, tags, description) or with panel_config
MetricTuple = tuple[str, Literal["timing", "counter", "gauge"], list[str], str]
MetricTupleWithConfig = tuple[
    str, Literal["timing", "counter", "gauge"], list[str], str, dict
]


def metrics(
    specs: list[MetricTuple | MetricTupleWithConfig | MetricDeclaration],
) -> list[MetricDeclaration]:
    """Convert tuple shorthand to MetricDeclaration list.

    Supports three input formats:
    1. 4-tuple: (name, type, tags, description)
    2. 5-tuple: (name, type, tags, description, panel_config)
    3. MetricDeclaration objects (passed through unchanged)

    Example:
        metrics_schema = metrics([
            ("events_created", "counter", ["pipeline"], "G events uploaded"),
            ("api_time", "timing", [], "API latency", {"unit": "ms"}),
        ])
    """
    result = []
    for spec in specs:
        if isinstance(spec, MetricDeclaration):
            result.append(spec)
        elif len(spec) == 5:
            name, mtype, tags, desc, config = spec
            result.append(
                MetricDeclaration(
                    name=name,
                    metric_type=mtype,
                    tags=tags,
                    description=desc,
                    panel_config=config,
                )
            )
        else:
            name, mtype, tags, desc = spec
            result.append(
                MetricDeclaration(
                    name=name, metric_type=mtype, tags=tags, description=desc
                )
            )
    return result


@dataclass
class MetricPoint:
    """A single metric observation with optional tags.

    Attributes:
        name: Metric name (e.g., "createEvent_time")
        value: Numeric value (e.g., 0.245 for timing in seconds)
        timestamp: GPS time of the observation
        tags: Dimensional tags for grouping/filtering (e.g., {"pipeline": "SGNL"})
    """

    name: str
    value: float
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Elapsed Time Tracking Wrappers
# ─────────────────────────────────────────────────────────────────────────────


def _wrap_pull_for_elapsed(original_pull: Callable) -> Callable:
    """Wrap a pull() method to call _on_pull_start() before the original."""

    @functools.wraps(original_pull)
    def wrapped_pull(self: Any, pad: Any, frame: Any) -> Any:
        # Call the elapsed time hook (no-op if track_elapsed_time=False)
        if hasattr(self, "_on_pull_start"):
            self._on_pull_start()
        return original_pull(self, pad, frame)

    return wrapped_pull


def _wrap_new_for_elapsed(original_new: Callable) -> Callable:
    """Wrap a new() method to call _on_new_end() after the original."""

    @functools.wraps(original_new)
    def wrapped_new(self: Any, pad: Any) -> Any:
        result = original_new(self, pad)
        # Call the elapsed time hook (no-op if track_elapsed_time=False)
        if hasattr(self, "_on_new_end"):
            self._on_new_end()
        return result

    return wrapped_new


class MetricsCollectorMixin:
    """Mixin for SGN elements to collect and emit metrics.

    Provides methods for:
    - Timing operations with context manager
    - Recording generic metrics
    - Incrementing counters
    - Flushing buffered metrics for emission
    - Automatic elapsed time tracking for pipeline cycles
    - Direct InfluxDB write or pad-based emission

    The mixin supports two modes:
    - "direct" (default): Write to InfluxDB via shared MetricsWriter
    - "pad": Emit through output pad for downstream processing

    Subclasses should declare their metrics schema for discovery by MetricsPipeline:

        class MyTransform(TransformElement, MetricsCollectorMixin):
            metrics_schema: ClassVar[list[MetricDeclaration]] = [
                MetricDeclaration(
                    name="events_processed",
                    metric_type="counter",
                    tags=["pipeline"],
                    description="Total events processed",
                ),
            ]

    Automatic Elapsed Time Tracking:
        When track_elapsed_time=True, the mixin automatically measures the time
        spent in each pipeline cycle. For transforms this uses pull/new wrapping.
        For sinks, call emit_metrics() at the end of pull() to record and flush.

    Attributes:
        metrics_enabled: Whether metric collection is active (default: True)
        metrics_mode: "direct" for InfluxDB write, "pad" for pad emission
        metrics_pad_name: Name of the output pad for pad mode
        track_elapsed_time: Whether to auto-track cycle elapsed time
        elapsed_metric_name: Name for the elapsed time metric
        metrics_schema: Class variable declaring metrics this element emits
    """

    # These can be overridden in the dataclass that uses this mixin
    metrics_enabled: bool = True
    metrics_mode: Literal["direct", "pad"] = "direct"  # Default to direct write
    metrics_pad_name: str = "metrics"

    # Elapsed time tracking configuration
    track_elapsed_time: bool = False
    elapsed_metric_name: str | None = None  # Defaults to "{element.name}_elapsed"

    # Subclasses declare their metrics schema for discovery
    metrics_schema: ClassVar[list[MetricDeclaration]] = []

    # Track which classes have been wrapped to avoid double-wrapping
    _elapsed_time_wrapped: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Automatically wrap pull() and new() methods for elapsed time tracking.

        This is called when a class inherits from MetricsCollectorMixin. It wraps
        the pull() and new() methods to automatically track elapsed time when
        track_elapsed_time=True on the instance.

        The wrapping is idempotent - if a class is already wrapped (e.g., via
        an intermediate parent class), it won't be wrapped again.
        """
        super().__init_subclass__(**kwargs)

        # Avoid double-wrapping if parent already wrapped these methods
        if getattr(cls, "_elapsed_time_wrapped", False):
            return

        # Wrap pull() if defined directly on this class
        if "pull" in cls.__dict__:
            original_pull = cls.__dict__["pull"]
            cls.pull = _wrap_pull_for_elapsed(original_pull)

        # Wrap new() if defined directly on this class
        if "new" in cls.__dict__:
            original_new = cls.__dict__["new"]
            cls.new = _wrap_new_for_elapsed(original_new)

        # Mark as wrapped to prevent double-wrapping in subclasses
        cls._elapsed_time_wrapped = True

    def _init_metrics(self) -> None:
        """Initialize metrics collection state.

        Call this in __post_init__ of the element using this mixin.
        """
        self._metrics_buffer: list[MetricPoint] = []
        self._counters: dict[tuple[str, tuple], int] = {}  # (name, tags_tuple) -> count

        # Elapsed time tracking state
        self._cycle_start_time: float | None = None
        self._new_call_count: int = 0

        # Direct write mode: reference to shared MetricsWriter (set by MetricsPipeline)
        self._metrics_writer: MetricsWriter | None = None

    def set_metrics_writer(self, writer: MetricsWriter) -> None:
        """Set the shared MetricsWriter for direct mode.

        Called by MetricsPipeline to configure elements with the shared writer.

        Args:
            writer: MetricsWriter instance for direct InfluxDB writes
        """
        self._metrics_writer = writer

    def _on_pull_start(self) -> None:
        """Called at the start of each pull() to track cycle elapsed time.

        Starts the timer on the first pull() of a cycle.
        """
        if not getattr(self, "track_elapsed_time", False):
            return
        if not getattr(self, "metrics_enabled", True):
            return

        # Start timer on first pull of the cycle
        if self._cycle_start_time is None:
            self._cycle_start_time = time.perf_counter()
            self._new_call_count = 0

    def _on_new_end(self) -> None:
        """Called at the end of each new() to track cycle elapsed time.

        Emits the elapsed time metric after the last new() of a cycle.
        In direct mode, also flushes metrics to InfluxDB.
        """
        if not getattr(self, "metrics_enabled", True):
            return

        self._new_call_count += 1

        # Check if we've served all source pads (cycle complete)
        # source_pads is provided by the SGN element base class
        num_source_pads = len(getattr(self, "source_pads", []))
        if self._new_call_count >= num_source_pads:
            # Record elapsed time if tracking is enabled
            if (
                getattr(self, "track_elapsed_time", False)
                and self._cycle_start_time is not None
            ):
                elapsed = time.perf_counter() - self._cycle_start_time

                # Determine metric name (default to "{element.name}_elapsed")
                metric_name = self.elapsed_metric_name
                if metric_name is None:
                    element_name = getattr(self, "name", "element")
                    metric_name = f"{element_name}_elapsed"

                # Record the elapsed time metric
                self.record_timing(metric_name, elapsed)

            # In direct mode, flush and write metrics now
            # (In pad mode, metrics are emitted via new_metrics_frame in new())
            if self.metrics_mode == "direct" and self._metrics_writer is not None:
                metrics = self.flush_metrics()
                self._metrics_writer.write(metrics)

            # Reset for next cycle
            self._cycle_start_time = None
            self._new_call_count = 0

    @contextmanager
    def time_operation(
        self, name: str, tags: dict[str, str] | None = None
    ) -> Generator[None, None, None]:
        """Context manager to time an operation and record as a metric.

        Args:
            name: Metric name (e.g., "createEvent_time")
            tags: Optional dimensional tags

        Example:
            with self.time_operation("gracedb_create", tags={"pipeline": "SGNL"}):
                result = gracedb.createEvent(...)
        """
        if not self.metrics_enabled:
            yield
            return

        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.record_timing(name, elapsed, tags=tags)

    def record_timing(
        self, name: str, elapsed: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record a timing metric.

        Args:
            name: Metric name
            elapsed: Duration in seconds
            tags: Optional dimensional tags
        """
        self.record_metric(name, elapsed, tags=tags)

    def record_metric(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
        timestamp: float | None = None,
    ) -> None:
        """Record a generic metric value.

        Args:
            name: Metric name
            value: Numeric value
            tags: Optional dimensional tags
            timestamp: Optional GPS timestamp (defaults to current GPS time)
        """
        if not self.metrics_enabled:
            return

        point = MetricPoint(
            name=name,
            value=value,
            timestamp=timestamp if timestamp is not None else _gps_now(),
            tags=tags or {},
        )
        self._metrics_buffer.append(point)

    def increment_counter(
        self, name: str, amount: int = 1, tags: dict[str, str] | None = None
    ) -> None:
        """Increment a counter metric.

        Counters are accumulated and emitted as a single metric per flush.

        Args:
            name: Counter name
            amount: Amount to increment (default: 1)
            tags: Optional dimensional tags
        """
        if not self.metrics_enabled:
            return

        # Use sorted tuple of tags as part of the key for consistent grouping
        tags_tuple = tuple(sorted((tags or {}).items()))
        key = (name, tags_tuple)
        self._counters[key] = self._counters.get(key, 0) + amount

    def flush_metrics(self) -> list[MetricPoint]:
        """Get all buffered metrics and clear the buffer.

        This converts accumulated counters to MetricPoints and returns
        all metrics collected since the last flush.

        Returns:
            List of MetricPoint objects ready for emission
        """
        if not self.metrics_enabled:
            return []

        # Convert counters to metric points (use GPS time for ligo.scald)
        now = _gps_now()
        for (name, tags_tuple), count in self._counters.items():
            tags = dict(tags_tuple)
            self._metrics_buffer.append(
                MetricPoint(name=name, value=float(count), timestamp=now, tags=tags)
            )
        self._counters.clear()

        # Return and clear buffer
        metrics = self._metrics_buffer
        self._metrics_buffer = []
        return metrics

    def get_buffered_metric_count(self) -> int:
        """Get the number of metrics currently buffered.

        Returns:
            Number of buffered metrics (not including pending counters)
        """
        return len(self._metrics_buffer)

    def new_metrics_frame(self, eos: bool = False) -> Frame:
        """Create a Frame containing buffered metrics for emission.

        Use this in your new() method to handle the metrics pad:

            def new(self, pad: SourcePad) -> Frame:
                pad_name = self.rsrcs.get(pad, pad.pad_name)

                if pad_name == self.metrics_pad_name:
                    return self.new_metrics_frame(eos=self._current_eos)

                # ... handle other pads

        Args:
            eos: Whether this is an end-of-stream frame

        Returns:
            Frame containing metrics (or gap frame if no metrics buffered)
        """
        from sgn.frames import Frame

        metrics = self.flush_metrics()
        if metrics:
            return Frame(data=metrics, is_gap=False, EOS=eos)
        return Frame(data=None, is_gap=True, EOS=eos)

    def emit_metrics(self) -> None:
        """Flush and emit metrics (for sinks and direct mode).

        This method should be called by sink elements at the end of pull()
        to flush buffered metrics and write them to InfluxDB (in direct mode).

        For transforms in direct mode, this is called automatically by
        _on_new_end(). For sinks (which have no new()), call this explicitly.

        This also handles elapsed time recording for sinks when
        track_elapsed_time=True.

        Example usage in a sink:
            def pull(self, pad, frame):
                # Process the frame
                with self.time_operation("process_time"):
                    self._process(frame)

                # Flush metrics (records elapsed time + writes to InfluxDB)
                self.emit_metrics()
        """
        if not self.metrics_enabled:
            return

        # Record elapsed time if tracking is enabled (for sinks without new())
        if (
            getattr(self, "track_elapsed_time", False)
            and self._cycle_start_time is not None
        ):
            elapsed = time.perf_counter() - self._cycle_start_time

            metric_name = self.elapsed_metric_name
            if metric_name is None:
                element_name = getattr(self, "name", "element")
                metric_name = f"{element_name}_elapsed"

            self.record_timing(metric_name, elapsed)
            self._cycle_start_time = None

        # Flush metrics
        metrics = self.flush_metrics()

        # Write directly if in direct mode and writer is available
        if self.metrics_mode == "direct" and self._metrics_writer is not None:
            self._metrics_writer.write(metrics)
