"""DelayBuffer: Delays events by a configurable time before releasing them.

A transform element that holds incoming events in an internal buffer and
releases them only after a configurable wall-clock delay has elapsed.
Useful for providing a "look-back" window before committing to downstream
processing.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import ClassVar

from sgn.base import SinkPad, SourcePad, TransformElement
from sgn.frames import Frame

from sgneskig.metrics.collector import MetricsCollectorMixin, metrics

_logger = logging.getLogger("sgn.sgneskig.delay_buffer")


@dataclass
class DelayBuffer(TransformElement, MetricsCollectorMixin):
    """Delays events by a configurable time before releasing them.

    Events are buffered upon arrival and only released when their
    wall-clock "age" exceeds delay_seconds. On EOS, all buffered
    events are flushed immediately.

    Args:
        delay_seconds: Time to hold events before releasing (default: 30.0)
        input_pad_name: Name of the input pad (default: "in")
        output_pad_name: Name of the output pad (default: "out")
        metrics_enabled: Whether to collect metrics (default: True)

    Pads:
        Sink: "in" (configurable)
        Sources: "out" (delayed events)
    """

    # Declarative metrics schema
    # NOTE: The elapsed metric name must match elapsed_metric_name below.
    # This allows auto-tracking to record the metric while the schema
    # provides the description for Grafana dashboard titles.
    _quarter = {"width": "quarter"}
    _quarter_both = {
        "width": "quarter",
        "visualizations": [
            {"type": "timeseries", "draw_style": "points", "show_points": "always"},
            {"type": "histogram", "bucket_count": 20},
        ],
    }
    metrics_schema: ClassVar = metrics(
        [
            (
                "events_buffered",
                "counter",
                [],
                "Events added to delay buffer",
                _quarter,
            ),
            ("events_released", "counter", [], "Events released after delay", _quarter),
            ("events_flushed_eos", "counter", [], "Events flushed on EOS", _quarter),
            ("buffer_size", "gauge", [], "Current buffer size", _quarter),
            (
                "delay_buffer_elapsed",
                "timing",
                [],
                "DelayBuffer cycle time",
                _quarter_both,
            ),
        ]
    )

    # Configuration
    delay_seconds: float = 30.0

    # Pad names
    input_pad_name: str = "in"
    output_pad_name: str = "out"

    # Metrics settings
    metrics_enabled: bool = True
    track_elapsed_time: bool = True
    # NOTE: Must match the name in metrics_schema above for proper Grafana titles
    elapsed_metric_name: str = "delay_buffer_elapsed"

    def __post_init__(self):
        # Set up pad names before super().__post_init__()
        self.sink_pad_names = [self.input_pad_name]
        self.source_pad_names = [self.output_pad_name]
        # metrics written directly via MetricsWriter (no metrics pad)

        super().__post_init__()
        self._logger = _logger

        # Initialize metrics collection
        self._init_metrics()

        # Buffer: deque of (arrival_time, event) tuples
        # arrival_time is wall-clock time when event was received
        self._buffer: deque[tuple[float, dict]] = deque()

        # Output buffer for current cycle
        self._output_events: list[dict] = []

        # Current frame state
        self._current_frame: Frame | None = None

        self._logger.info(f"DelayBuffer initialized with {self.delay_seconds}s delay")

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive frame and buffer events with arrival timestamp."""
        self._current_frame = frame

        if frame.is_gap or frame.data is None:
            return

        # Get current wall-clock time for arrival timestamp
        arrival_time = time.time()

        # Handle both single events and batches
        events = frame.data if isinstance(frame.data, list) else [frame.data]

        for event in events:
            self._buffer.append((arrival_time, event))
            self.increment_counter("events_buffered")

    def internal(self) -> None:
        """Release events that have aged past the delay threshold."""
        self._output_events = []

        now = time.time()
        cutoff_time = now - self.delay_seconds

        # Check if EOS - flush all events immediately
        if self._current_frame and self._current_frame.EOS:
            self._flush_all_events()
        else:
            # Release events older than delay_seconds
            while self._buffer:
                arrival_time, event = self._buffer[0]  # peek at oldest

                if arrival_time <= cutoff_time:
                    self._buffer.popleft()
                    self._output_events.append(event)
                    self.increment_counter("events_released")
                else:
                    # Buffer is ordered, so no more events are ready
                    break

        # Update buffer size gauge
        self.record_metric("buffer_size", float(len(self._buffer)))

    def _flush_all_events(self) -> None:
        """Flush all buffered events on EOS."""
        flush_count = 0
        while self._buffer:
            _, event = self._buffer.popleft()
            self._output_events.append(event)
            flush_count += 1

        if flush_count > 0:
            self._logger.info(f"EOS: Flushed {flush_count} buffered events")
            for _ in range(flush_count):
                self.increment_counter("events_flushed_eos")

    def new(self, pad: SourcePad) -> Frame:
        """Return output frame for the requested pad."""
        eos = self._current_frame.EOS if self._current_frame else False

        # Return released events
        return Frame(
            data=self._output_events if self._output_events else None,
            is_gap=not self._output_events,
            EOS=eos,
        )
