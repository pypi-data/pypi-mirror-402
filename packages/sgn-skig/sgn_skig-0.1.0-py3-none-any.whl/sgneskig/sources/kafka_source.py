"""KafkaSource: SGN source element that reads from Kafka topics.

Uses ParallelizeSourceElement to run Kafka polling in a background thread,
avoiding blocking the main SGN event loop.

Each topic becomes a separate output pad, allowing downstream elements to
connect to specific topics.

Output format:
- Frame(data=list[dict]) containing all events available this cycle
- Empty list or None with is_gap=True indicates no data available
- With timestamp_field set, outputs EventFrame instead for latency tracking
"""

from __future__ import annotations

import json
import logging
import queue
from collections import deque
from dataclasses import dataclass, field
from typing import Any, ClassVar

from confluent_kafka import Consumer, KafkaError
from sgn.base import SourcePad
from sgn.frames import Frame
from sgn.sources import SignalEOS
from sgn.subprocess import ParallelizeSourceElement, WorkerContext
from sgnts.base import EventBuffer, EventFrame

# Use sgn.sgneskig hierarchy for SGNLOGLEVEL control
_logger = logging.getLogger("sgn.sgneskig.kafka_source")

# Sentinel value for using Kafka's message timestamp instead of a JSON field
KAFKA_TIMESTAMP = "__kafka_timestamp__"


@dataclass
class KafkaSource(ParallelizeSourceElement, SignalEOS):
    """SGN source element that reads from Kafka topics.

    Uses a background thread to poll Kafka, avoiding blocking the main
    SGN async event loop. Messages are passed through a queue to the
    main thread.

    Each topic in the topics list becomes a separate output pad with
    the same name as the topic. This allows downstream elements to
    connect to specific topics.

    Args:
        bootstrap_servers: Kafka bootstrap server addresses
        topics: List of Kafka topics to subscribe to (each becomes an output pad)
        group_id: Consumer group ID
        poll_timeout: Timeout in seconds for polling Kafka
        auto_offset_reset: Where to start reading ('earliest' or 'latest')
        timestamp_field: Field name containing timestamp (seconds) for EventFrame
            output. Use KAFKA_TIMESTAMP to use Kafka's message timestamp.
            If None (default), outputs simple Frame objects.
    """

    bootstrap_servers: str = "localhost:9092"
    topics: list[str] = field(default_factory=lambda: ["event-topic"])
    group_id: str = "sgn-consumer"
    poll_timeout: float = 1.0  # Longer timeout OK since it's in background thread
    auto_offset_reset: str = "latest"
    timestamp_field: str | None = None  # None = simple Frame, else EventFrame

    # Dynamic pad configuration - pads are created from topics list
    static_source_pads: ClassVar[list[str]] = []
    allow_dynamic_source_pads: ClassVar[bool] = True

    # Use threading (not multiprocessing) - Kafka consumer isn't picklable
    _use_threading_override: bool = True

    # Queue settings
    queue_maxsize: int = 1000
    queue_timeout: float = 1.0  # Timeout for blocking get in main thread

    def __post_init__(self):
        # Create output pads from topics list (must be set before super().__post_init__)
        self.source_pad_names = list(self.topics)

        # Per-topic buffers for routing messages from the shared queue
        self._topic_buffers: dict[str, deque] = {
            topic: deque() for topic in self.topics
        }

        super().__post_init__()

        self._logger = _logger
        mode = "EventFrame" if self.timestamp_field else "Frame"
        self._logger.info(
            f"KafkaSource will subscribe to topics {self.topics} "
            f"on {self.bootstrap_servers} (output_mode={mode})"
        )
        if self.timestamp_field:
            self._logger.info(f"Timestamp source: {self.timestamp_field}")
        self._logger.info(f"Output pads: {self.source_pad_names}")

    def _create_batch_frame(
        self, events: list[tuple[dict, int | None]], eos: bool = False
    ) -> Frame | EventFrame:
        """Create a frame containing a batch of events.

        Args:
            events: List of (data, kafka_ts_ms) tuples
            eos: Whether this is an end-of-stream frame

        Returns:
            Frame(data=list[dict]) or EventFrame depending on configuration

        Raises:
            ValueError: If timestamp_field is set but timestamp is not available
        """
        if not events:
            return self._create_gap_frame(eos=eos)

        if self.timestamp_field is None:
            # Simple mode - return Frame with list of dicts
            return Frame(data=[e[0] for e in events], is_gap=False, EOS=eos)

        # EventFrame mode - create EventBuffer for each event
        buffers = []
        for data, kafka_ts_ms in events:
            if self.timestamp_field == KAFKA_TIMESTAMP:
                if kafka_ts_ms is None:
                    raise ValueError(
                        "Kafka timestamp requested but not available in message"
                    )
                gps_ns = kafka_ts_ms * 1_000_000  # ms -> ns
            else:
                timestamp = data.get(self.timestamp_field)
                if timestamp is None:
                    raise ValueError(
                        f"Required timestamp field '{self.timestamp_field}' "
                        f"not found in data. Available fields: {list(data.keys())}"
                    )
                gps_ns = int(float(timestamp) * 1_000_000_000)  # seconds -> ns

            buffer = EventBuffer.from_span(start=gps_ns, end=gps_ns + 1, data=[data])
            buffers.append(buffer)

        return EventFrame(data=buffers, EOS=eos)

    def _create_gap_frame(self, eos: bool = False) -> Frame | EventFrame:
        """Create a gap frame of the appropriate type.

        Args:
            eos: Whether this is an end-of-stream frame

        Returns:
            Gap Frame or empty EventFrame depending on configuration
        """
        if self.timestamp_field is None:
            return Frame(data=None, is_gap=True, EOS=eos)
        else:
            # EventFrame with empty data list represents a gap
            return EventFrame(data=[], EOS=eos)

    def worker_process(
        self,
        context: WorkerContext,
        bootstrap_servers: str,
        topics: list[str],
        group_id: str,
        poll_timeout: float,
        auto_offset_reset: str,
        timestamp_field: str | None,
    ) -> None:
        """Background worker that polls Kafka and puts parsed messages in queue.

        This runs in a separate thread, so blocking on poll() doesn't affect
        the main SGN event loop.

        Messages are put in the queue as (topic, data, kafka_ts_ms) tuples.
        Frame creation happens in the main thread via internal().
        """
        # Initialize consumer in worker thread (first call only)
        if "consumer" not in context.state:
            config = {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": auto_offset_reset,
                "enable.auto.commit": True,
            }
            consumer = Consumer(config)
            consumer.subscribe(topics)
            context.state["consumer"] = consumer
            context.state["logger"] = _logger
            context.state["logger"].info(
                f"KafkaSource worker subscribed to {topics} on {bootstrap_servers}"
            )

        consumer = context.state["consumer"]
        logger = context.state["logger"]

        # Check for shutdown signal and close consumer cleanly
        if context.should_shutdown() or context.should_stop():
            if not context.state.get("consumer_closed"):
                logger.info("KafkaSource worker shutting down, closing consumer")
                consumer.close()
                context.state["consumer_closed"] = True
            return

        # Poll for message (blocking is OK here - we're in background thread)
        msg = consumer.poll(timeout=poll_timeout)

        if msg is None:
            # No message available - don't put anything in queue
            # (gaps will be generated by new() when buffer is empty)
            return

        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                logger.warning(f"Kafka error: {msg.error()}")
            return

        # Skip tombstone messages (None value used in compacted topics)
        if msg.value() is None:
            return

        try:
            topic = msg.topic()
            data = json.loads(msg.value().decode("utf-8"))

            # Get Kafka timestamp (type 0 = not available)
            ts_type, kafka_ts_ms = msg.timestamp()
            if ts_type == 0:
                kafka_ts_ms = None

            logger.debug(
                f"Received event from {topic}: {data.get('graceid', 'unknown')}"
            )

            # Put raw data + kafka timestamp for frame creation in main thread
            context.output_queue.put((topic, data, kafka_ts_ms))

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse message: {e}")

    # Ignore: SGN subprocess.py:975 uses class variable assignment for `internal`.
    # TODO: Fix in SGN by using proper method override instead.
    def internal(self) -> Any:  # type: ignore[override]
        """Drain the shared queue and route messages to per-topic buffers.

        Stores raw (data, kafka_ts_ms) tuples for batching in new().
        """
        super().internal()

        # Wait for data with timeout (prevents spinning)
        try:
            topic, data, kafka_ts_ms = self.out_queue.get(timeout=self.queue_timeout)
            self._topic_buffers[topic].append((data, kafka_ts_ms))

            # Drain any additional available items
            while True:
                try:
                    topic, data, kafka_ts_ms = self.out_queue.get_nowait()
                    self._topic_buffers[topic].append((data, kafka_ts_ms))
                except queue.Empty:
                    break
        except queue.Empty:
            pass  # No data available this cycle

    def new(self, pad: SourcePad) -> Frame | EventFrame:
        """Get next frame for the specified pad (topic).

        Returns all buffered events as a single batch frame.
        """
        # Check for signal (Ctrl+C or SIGTERM)
        eos = self.signaled_eos()
        if eos:
            self._logger.info("Signal received, setting EOS for graceful shutdown")
            return self._create_gap_frame(eos=True)

        # Get topic name for this pad
        topic = self.rsrcs[pad]

        # Collect all buffered events for this topic
        events = list(self._topic_buffers[topic])
        self._topic_buffers[topic].clear()

        # Return batch frame (handles empty case as gap)
        return self._create_batch_frame(events, eos=False)
