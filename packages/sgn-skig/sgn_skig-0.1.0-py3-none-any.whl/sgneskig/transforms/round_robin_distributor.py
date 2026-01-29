"""RoundRobinDistributor: Distributes frames across N worker pads using round-robin.

Non-target workers receive gap frames for each cycle, ensuring proper SGN frame
flow while distributing work evenly across parallel processors.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from sgn.base import SinkPad, SourcePad, TransformElement
from sgn.frames import Frame

from sgneskig.metrics.collector import MetricsCollectorMixin, metrics

_logger = logging.getLogger("sgn.sgneskig.round_robin_distributor")


@dataclass
class RoundRobinDistributor(TransformElement, MetricsCollectorMixin):
    """Distributes superevent frames across N worker pads using round-robin.

    Each event in the input batch goes to one worker; other workers receive
    gap frames. This enables N parallel Bayestar processors to share the
    workload evenly.

    Pads:
    - Sink: configurable (default "in")
    - Sources: "worker_0", "worker_1", ..., "worker_{N-1}"
    """

    # Declarative metrics schema
    metrics_schema: ClassVar = metrics(
        [
            ("events_distributed", "counter", ["worker"], "Events sent to each worker"),
        ]
    )

    # Configuration
    num_workers: int = 4
    input_pad_name: str = "in"
    worker_pad_prefix: str = "worker"

    # Metrics settings (from MetricsCollectorMixin)
    metrics_enabled: bool = True

    def __post_init__(self):
        # Set up pad names before super().__post_init__()
        self.sink_pad_names = [self.input_pad_name]

        # Generate worker pad names: worker_0, worker_1, ..., worker_{N-1}
        worker_pads = tuple(
            f"{self.worker_pad_prefix}_{i}" for i in range(self.num_workers)
        )
        self.source_pad_names = worker_pads
        # metrics written directly via MetricsWriter (no metrics pad)

        super().__post_init__()
        self._logger = _logger

        # Initialize metrics collection
        self._init_metrics()

        # Round-robin counter
        self._next_worker = 0

        # Output frames for current cycle (pad_name → Frame)
        self._output_frames: dict[str, Frame] = {}

        # Current input state
        self._current_frame: Frame | None = None

        self._logger.info(
            f"RoundRobinDistributor initialized with {self.num_workers} workers"
        )

    def pull(self, pad: SinkPad, frame: Frame) -> None:
        """Receive frame from upstream."""
        self._current_frame = frame

    def internal(self) -> None:
        """Distribute input events across workers using round-robin."""
        frame = self._current_frame
        eos = frame.EOS if frame else False

        # Initialize all worker pads to gap frames
        for i in range(self.num_workers):
            pad_name = f"{self.worker_pad_prefix}_{i}"
            self._output_frames[pad_name] = Frame(data=None, is_gap=True, EOS=eos)

        # Handle gap or empty input
        if frame is None or frame.is_gap or not frame.data:
            return

        # Distribute events from input batch
        # Each event goes to one worker
        events = frame.data if isinstance(frame.data, list) else [frame.data]

        for event in events:
            worker_idx = self._next_worker
            pad_name = f"{self.worker_pad_prefix}_{worker_idx}"

            # Get current output frame for this worker
            current_frame = self._output_frames[pad_name]

            # Add event to this worker's batch
            if current_frame.is_gap:
                # First event for this worker - create new frame
                self._output_frames[pad_name] = Frame(
                    data=[event], is_gap=False, EOS=eos
                )
            else:
                # Append to existing batch
                current_frame.data.append(event)

            # Track metrics
            self.increment_counter(
                "events_distributed", tags={"worker": str(worker_idx)}
            )

            # Advance to next worker
            self._next_worker = (self._next_worker + 1) % self.num_workers

            self._logger.debug(f"Distributed event to worker_{worker_idx}")

    def new(self, pad: SourcePad) -> Frame:
        """Return output frame for the requested pad."""
        pad_name = self.rsrcs[pad]
        eos = self._current_frame.EOS if self._current_frame else False

        return self._output_frames.get(pad_name, Frame(data=None, is_gap=True, EOS=eos))
