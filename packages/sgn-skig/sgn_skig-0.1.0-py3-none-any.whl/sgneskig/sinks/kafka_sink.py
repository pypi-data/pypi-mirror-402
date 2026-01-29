"""KafkaSink: SGN sink element that publishes to Kafka topics.

Each topic becomes a separate input pad, allowing upstream elements to
route messages to specific topics.

Accepts multiple input formats:
- Frame(data=list[dict]): Batch of events
- Frame(data=dict): Single event (legacy)
- EventFrame: With EventBuffers containing dicts
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import ClassVar, Literal

from confluent_kafka import KafkaException, Producer
from sgn.base import SinkElement, SinkPad
from sgn.frames import Frame
from sgnts.base import EventBuffer, EventFrame

# Use sgn.sgneskig hierarchy for SGNLOGLEVEL control
_logger = logging.getLogger("sgn.sgneskig.kafka_sink")

# Valid delivery modes
DeliveryMode = Literal["log_failures", "strict"]


@dataclass
class KafkaSink(SinkElement):
    """SGN sink element that publishes to Kafka.

    Receives Frame or EventFrame objects and publishes their data to Kafka topics.

    Each topic in the topics list becomes a separate input pad with
    the same name as the topic. Messages received on a pad are published
    to the corresponding topic.

    Supports both:
    - Simple Frame: frame.data is the dict to publish
    - EventFrame: frame.data is list of EventBuffers containing dicts

    Args:
        bootstrap_servers: Kafka bootstrap server addresses
        topics: Kafka topics to publish to. Can be:
            - list[str]: Topic names become pad names
            - dict[str, str]: Pad name → topic name mapping
        key_field: Optional field name to use as Kafka message key
        delivery_mode: How to handle message delivery confirmation:
            - "log_failures": Async with error logging (default)
            - "strict": Sync confirmation, exception on failure (for critical data)
    """

    bootstrap_servers: str = "localhost:9092"
    topics: list[str] | dict[str, str] = field(default_factory=lambda: ["output-topic"])
    key_field: str | None = None
    delivery_mode: DeliveryMode = "log_failures"

    # Dynamic pad configuration - pads are created from topics
    static_sink_pads: ClassVar[list[str]] = []
    allow_dynamic_sink_pads: ClassVar[bool] = True

    def __post_init__(self):
        # Build pad-to-topic mapping from topics config
        # - list: pad names = topic names
        # - dict: pad name → topic name
        if isinstance(self.topics, dict):
            self._pad_to_topic = dict(self.topics)
            self.sink_pad_names = list(self.topics.keys())
        else:
            self._pad_to_topic = {t: t for t in self.topics}
            self.sink_pad_names = list(self.topics)

        super().__post_init__()

        self._producer = Producer(
            {
                "bootstrap.servers": self.bootstrap_servers,
            }
        )
        self._logger = _logger

        # For strict mode: track delivery errors from callbacks
        self._delivery_error: str | None = None

        self._logger.info(
            f"KafkaSink initialized for topics {self.topics} "
            f"on {self.bootstrap_servers} (delivery_mode={self.delivery_mode})"
        )
        self._logger.info(f"Input pads: {self.sink_pad_names}")

    def _extract_events(self, frame: Frame | EventFrame) -> list[dict]:
        """Extract event data from Frame or EventFrame.

        Args:
            frame: Either a simple Frame or an EventFrame

        Returns:
            List of event dicts to publish (may be empty for gaps)
        """
        if frame.is_gap:
            return []

        # Check for EventFrame (has list of EventBuffers in .data)
        if isinstance(frame, EventFrame):
            events = []
            for buffer in frame.data:
                if isinstance(buffer, EventBuffer):
                    events.extend(buffer.data)
            return events

        # Simple Frame
        if frame.data is None:
            return []

        # Batch format: list[dict]
        if isinstance(frame.data, list):
            return frame.data

        # Legacy single event format: dict
        if isinstance(frame.data, dict):
            return [frame.data]

        return []

    def _on_delivery(self, err, msg) -> None:
        """Callback for message delivery confirmation.

        Used in 'log_failures' and 'strict' modes.
        """
        if err is not None:
            error_msg = f"Delivery failed for {msg.topic()}: {err}"
            self._logger.error(error_msg)
            # In strict mode, save error for later exception
            if self.delivery_mode == "strict":
                self._delivery_error = error_msg

    def pull(self, pad: SinkPad, frame: Frame | EventFrame) -> None:
        """Receive frame and publish to the topic corresponding to this pad.

        Handles both simple Frame and EventFrame inputs.
        """
        if frame.EOS:
            self.mark_eos(pad)

        # Extract events from frame (handles both Frame and EventFrame)
        events = self._extract_events(frame)
        if not events:
            return

        # Get topic from pad name (use mapping to support custom pad names)
        pad_name = self.rsnks[pad]
        topic = self._pad_to_topic.get(pad_name, pad_name)

        # Publish each event
        for event_data in events:
            # Serialize data
            value = json.dumps(event_data).encode("utf-8")

            # Extract key if configured
            key = None
            if self.key_field and isinstance(event_data, dict):
                key_value = event_data.get(self.key_field)
                if key_value:
                    key = str(key_value).encode("utf-8")

            # Publish to the topic matching this pad
            # NOTE: produce() raises BufferError if the internal queue is full,
            # which will crash the pipeline. This is intentional - a full buffer
            # indicates Kafka cannot keep up and requires operator intervention.
            self._producer.produce(
                topic=topic,
                key=key,
                value=value,
                callback=self._on_delivery,
            )

            if self.delivery_mode == "strict":
                # Synchronous: flush and check for errors
                self._producer.flush()
                if self._delivery_error:
                    error = self._delivery_error
                    self._delivery_error = None  # Reset for next message
                    raise KafkaException(error)
            else:
                # Async: just trigger callbacks without blocking
                self._producer.poll(0)

            self._logger.debug(f"Published to {topic}: {event_data}")

    def internal(self) -> None:
        """Process delivery callbacks."""
        if self.at_eos:
            # Final flush with timeout to avoid blocking forever
            self._logger.info("KafkaSink: final flush (30s timeout)")
            remaining = self._producer.flush(timeout=30.0)
            if remaining > 0:
                self._logger.warning(
                    f"KafkaSink: {remaining} messages not delivered at shutdown"
                )
        else:
            # Non-blocking: just process any pending delivery callbacks
            self._producer.poll(0)
