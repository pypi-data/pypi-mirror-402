"""EventLatency: Pass-through transform that measures event latency.

Computes the time difference between the current GPS time and a timestamp
field in each event, emitting a timing metric. Useful for monitoring
end-to-end pipeline delays.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, ClassVar

from sgn.base import SinkPad, SourcePad, TransformElement
from sgn.frames import Frame

from sgneskig.metrics.collector import (
    MetricDeclaration,
    MetricsCollectorMixin,
    _gps_now,
)

# Use sgn.sgneskig hierarchy for SGNLOGLEVEL control
_logger = logging.getLogger("sgn.sgneskig.event_latency")


@dataclass
class EventLatency(TransformElement, MetricsCollectorMixin):
    """Pass-through transform that measures event latency.

    Computes the time difference between the current GPS time and a timestamp
    field in each event, emitting a timing metric for each event processed.

    The element passes data through unchanged - it only observes and measures.

    Args:
        metric_name: Name for the latency metric (default: "event_latency")
        time_field: Field name containing the event timestamp (default: "gpstime")
        tag_field: Optional field name to use as a metric tag (e.g., "pipeline")
        input_pad_name: Name of the input pad (default: "in")
        output_pad_name: Name of the output pad (default: "out")
        metrics_enabled: Whether to collect and emit metrics (default: True)
    """

    # Latency measurement configuration
    metric_name: str = "event_latency"
    time_field: str = "gpstime"
    tag_field: str | None = None
    description: str | None = None  # Custom description for Grafana panel title
    panel_config: dict | None = None  # Grafana panel customization

    # Pad names (configurable for pipeline integration)
    input_pad_name: str = "in"
    output_pad_name: str = "out"

    # Metrics settings (from MetricsCollectorMixin)
    metrics_enabled: bool = True

    # Declare metrics schema for discovery (empty at class level, set per-instance)
    metrics_schema: ClassVar[list[MetricDeclaration]] = []

    def __post_init__(self):
        # Set up pad names before super().__post_init__()
        self.sink_pad_names = [self.input_pad_name]
        self.source_pad_names = [self.output_pad_name]

        super().__post_init__()

        # Initialize metrics collection (from MetricsCollectorMixin)
        self._init_metrics()

        # Build metrics schema dynamically based on configuration
        # Store on instance (_metrics_schema) to avoid class-level sharing issues
        # Default to points style since latency data is per-event (sparse)
        tags = [self.tag_field] if self.tag_field else []
        default_config = {"draw_style": "points", "show_points": "always"}
        config = self.panel_config if self.panel_config is not None else default_config
        desc = self.description or f"Event latency ({self.time_field} to now)"
        self._metrics_schema = [
            MetricDeclaration(
                name=self.metric_name,
                metric_type="timing",
                tags=tags,
                description=desc,
                panel_config=config,
            ),
        ]

        # Current frame state
        self._current_frame: Frame | None = None

        _logger.info(
            f"EventLatency initialized: metric={self.metric_name}, "
            f"time_field={self.time_field}, tag_field={self.tag_field}"
        )

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive frame and measure latency for each event."""
        self._current_frame = frame

        if frame.is_gap or frame.data is None:
            return

        # Get current GPS time once for the batch
        now = _gps_now()

        # Handle both single events and batches
        events = frame.data if isinstance(frame.data, list) else [frame.data]

        for event in events:
            self._measure_latency(event, now)

    def _measure_latency(self, event: Any, now: float) -> None:
        """Measure and record latency for a single event."""
        # Extract timestamp from event
        event_time = self._get_timestamp(event)
        if event_time is None:
            return

        # Compute latency (current time - event time)
        latency = now - event_time

        # Build tags if configured
        tags = {}
        if self.tag_field:
            tag_value = self._get_field(event, self.tag_field)
            if tag_value is not None:
                tags[self.tag_field] = str(tag_value)

        # Record the latency metric
        self.record_timing(self.metric_name, latency, tags=tags)

    def _get_timestamp(self, event: Any) -> float | None:
        """Extract timestamp from event data."""
        timestamp = self._get_field(event, self.time_field)
        if timestamp is None:
            _logger.debug(f"Event missing time field '{self.time_field}'")
            return None
        try:
            return float(timestamp)
        except (TypeError, ValueError):
            _logger.warning(f"Invalid timestamp value: {timestamp}")
            return None

    def _get_field(self, event: Any, field: str) -> Any:
        """Extract a field from event data (supports dict and object access)."""
        if isinstance(event, dict):
            return event.get(field)
        return getattr(event, field, None)

    def new(self, pad: SourcePad) -> Frame:
        """Emit data on appropriate pad."""
        eos = self._current_frame.EOS if self._current_frame else False

        # Pass through the original frame unchanged
        if self._current_frame is not None:
            return self._current_frame

        return Frame(data=None, is_gap=True, EOS=eos)
