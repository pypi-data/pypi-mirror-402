"""Tests for sgneskig.sources module."""

import queue
from unittest.mock import MagicMock, patch

import pytest
from sgn.frames import Frame
from sgnts.base import EventBuffer, EventFrame

from sgneskig.sources.kafka_source import KAFKA_TIMESTAMP, KafkaSource


class TestKafkaSourceInit:
    """Tests for KafkaSource initialization."""

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_initialization(self, mock_super):
        """Test KafkaSource initializes correctly."""
        source = KafkaSource(
            bootstrap_servers="kafka:9092",
            topics=["topic1", "topic2"],
            group_id="test-group",
        )

        assert source.bootstrap_servers == "kafka:9092"
        assert source.topics == ["topic1", "topic2"]
        assert source.group_id == "test-group"
        assert source.source_pad_names == ["topic1", "topic2"]

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_default_values(self, mock_super):
        """Test default configuration values."""
        source = KafkaSource()

        assert source.bootstrap_servers == "localhost:9092"
        assert source.topics == ["event-topic"]
        assert source.group_id == "sgn-consumer"
        assert source.poll_timeout == 1.0
        assert source.auto_offset_reset == "latest"
        assert source.timestamp_field is None

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_topic_buffers_created(self, mock_super):
        """Test per-topic buffers are created."""
        source = KafkaSource(topics=["a", "b", "c"])

        assert "a" in source._topic_buffers
        assert "b" in source._topic_buffers
        assert "c" in source._topic_buffers


class TestKafkaSourceCreateBatchFrame:
    """Tests for _create_batch_frame method."""

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_empty_events_returns_gap(self, mock_super):
        """Test empty events list returns gap frame."""
        source = KafkaSource(timestamp_field=None)
        frame = source._create_batch_frame([], eos=False)

        assert frame.is_gap is True
        assert frame.EOS is False

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_simple_mode_returns_frame(self, mock_super):
        """Test simple mode returns Frame with list of dicts."""
        source = KafkaSource(timestamp_field=None)
        events = [({"id": 1}, None), ({"id": 2}, None)]

        frame = source._create_batch_frame(events, eos=False)

        assert isinstance(frame, Frame)
        assert frame.data == [{"id": 1}, {"id": 2}]
        assert frame.is_gap is False

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_eventframe_mode_with_timestamp_field(self, mock_super):
        """Test EventFrame mode with timestamp field."""
        source = KafkaSource(timestamp_field="gpstime")
        events = [({"gpstime": 1000.5, "data": "test"}, None)]

        frame = source._create_batch_frame(events, eos=False)

        assert isinstance(frame, EventFrame)
        assert len(frame.data) == 1
        assert isinstance(frame.data[0], EventBuffer)

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_eventframe_mode_missing_timestamp(self, mock_super):
        """Test EventFrame mode raises on missing timestamp."""
        source = KafkaSource(timestamp_field="gpstime")
        events = [({"data": "test"}, None)]  # Missing gpstime

        with pytest.raises(ValueError, match="not found in data"):
            source._create_batch_frame(events, eos=False)

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_kafka_timestamp_mode(self, mock_super):
        """Test using Kafka message timestamp."""
        source = KafkaSource(timestamp_field=KAFKA_TIMESTAMP)
        events = [({"data": "test"}, 1000000)]  # 1000000ms Kafka timestamp

        frame = source._create_batch_frame(events, eos=False)

        assert isinstance(frame, EventFrame)
        assert len(frame.data) == 1

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_kafka_timestamp_mode_missing(self, mock_super):
        """Test Kafka timestamp mode raises when timestamp not available."""
        source = KafkaSource(timestamp_field=KAFKA_TIMESTAMP)
        events = [({"data": "test"}, None)]  # No Kafka timestamp

        with pytest.raises(ValueError, match="not available"):
            source._create_batch_frame(events, eos=False)

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_eos_flag_propagated(self, mock_super):
        """Test EOS flag is propagated to frame."""
        source = KafkaSource(timestamp_field=None)
        events = [({"id": 1}, None)]

        frame = source._create_batch_frame(events, eos=True)

        assert frame.EOS is True


class TestKafkaSourceCreateGapFrame:
    """Tests for _create_gap_frame method."""

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_simple_mode_gap(self, mock_super):
        """Test gap frame in simple mode."""
        source = KafkaSource(timestamp_field=None)
        frame = source._create_gap_frame(eos=False)

        assert isinstance(frame, Frame)
        assert frame.is_gap is True
        assert frame.data is None

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_eventframe_mode_gap(self, mock_super):
        """Test gap frame in EventFrame mode."""
        source = KafkaSource(timestamp_field="ts")
        frame = source._create_gap_frame(eos=False)

        assert isinstance(frame, EventFrame)
        assert frame.data == []

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_gap_with_eos(self, mock_super):
        """Test gap frame with EOS."""
        source = KafkaSource(timestamp_field=None)
        frame = source._create_gap_frame(eos=True)

        assert frame.EOS is True


class TestKafkaSourceNew:
    """Tests for new method."""

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_new_returns_buffered_events(self, mock_super):
        """Test new returns all buffered events."""
        source = KafkaSource(topics=["test-topic"], timestamp_field=None)
        source.rsrcs = {MagicMock(): "test-topic"}

        # Buffer some events
        source._topic_buffers["test-topic"].append(({"id": 1}, None))
        source._topic_buffers["test-topic"].append(({"id": 2}, None))

        mock_pad = list(source.rsrcs.keys())[0]
        with patch.object(source, "signaled_eos", return_value=False):
            frame = source.new(mock_pad)

        assert frame.data == [{"id": 1}, {"id": 2}]
        assert len(source._topic_buffers["test-topic"]) == 0  # Buffer cleared

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_new_returns_gap_when_empty(self, mock_super):
        """Test new returns gap when buffer empty."""
        source = KafkaSource(topics=["test-topic"], timestamp_field=None)
        source.rsrcs = {MagicMock(): "test-topic"}

        mock_pad = list(source.rsrcs.keys())[0]
        with patch.object(source, "signaled_eos", return_value=False):
            frame = source.new(mock_pad)

        assert frame.is_gap is True

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_new_returns_eos_on_signal(self, mock_super):
        """Test new returns EOS frame on signal."""
        source = KafkaSource(topics=["test-topic"], timestamp_field=None)
        source.rsrcs = {MagicMock(): "test-topic"}

        mock_pad = list(source.rsrcs.keys())[0]
        with patch.object(source, "signaled_eos", return_value=True):
            frame = source.new(mock_pad)

        assert frame.EOS is True


class TestKafkaSourceInternal:
    """Tests for internal method."""

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.internal")
    def test_internal_drains_queue(self, mock_super_internal, mock_super):
        """Test internal drains output queue."""
        source = KafkaSource(topics=["topic1", "topic2"], timestamp_field=None)

        # Create mock queue with data
        mock_queue = MagicMock()
        mock_queue.get.side_effect = [
            ("topic1", {"id": 1}, None),  # First call succeeds
            queue.Empty(),  # Second call raises Empty
        ]
        mock_queue.get_nowait.side_effect = queue.Empty()
        source.out_queue = mock_queue

        source.internal()

        # Event should be in topic1 buffer
        assert len(source._topic_buffers["topic1"]) == 1
        assert source._topic_buffers["topic1"][0] == ({"id": 1}, None)

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.internal")
    def test_internal_handles_empty_queue(self, mock_super_internal, mock_super):
        """Test internal handles empty queue gracefully."""
        source = KafkaSource(topics=["topic1"], timestamp_field=None)

        mock_queue = MagicMock()
        mock_queue.get.side_effect = queue.Empty()
        source.out_queue = mock_queue

        # Should not raise
        source.internal()

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.internal")
    def test_internal_routes_to_correct_topic(self, mock_super_internal, mock_super):
        """Test internal routes messages to correct topic buffer."""
        source = KafkaSource(topics=["topic1", "topic2"], timestamp_field=None)

        # Create real queue for this test
        source.out_queue = queue.Queue()
        source.out_queue.put(("topic1", {"t1": 1}, None))
        source.out_queue.put(("topic2", {"t2": 2}, None))
        source.out_queue.put(("topic1", {"t1": 3}, None))

        # Set short timeout for test
        source.queue_timeout = 0.001

        source.internal()

        assert len(source._topic_buffers["topic1"]) == 2
        assert len(source._topic_buffers["topic2"]) == 1


class TestKafkaSourceWorkerProcess:
    """Tests for worker_process method."""

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    @patch("sgneskig.sources.kafka_source.Consumer")
    def test_worker_initializes_consumer(self, mock_consumer_class, mock_super):
        """Test worker initializes consumer on first call."""
        source = KafkaSource(
            topics=["test"],
            bootstrap_servers="kafka:9092",
            group_id="test-group",
            auto_offset_reset="earliest",
        )

        mock_consumer = MagicMock()
        mock_consumer.poll.return_value = None
        mock_consumer_class.return_value = mock_consumer

        context = MagicMock()
        context.state = {}
        context.should_shutdown.return_value = False
        context.should_stop.return_value = False

        source.worker_process(
            context,
            "kafka:9092",
            ["test"],
            "test-group",
            1.0,
            "earliest",
            None,
        )

        assert "consumer" in context.state
        mock_consumer.subscribe.assert_called_once_with(["test"])

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_worker_handles_shutdown(self, mock_super):
        """Test worker handles shutdown signal."""
        source = KafkaSource(topics=["test"])

        mock_consumer = MagicMock()
        context = MagicMock()
        context.state = {"consumer": mock_consumer, "logger": MagicMock()}
        context.should_shutdown.return_value = True

        source.worker_process(
            context,
            "kafka:9092",
            ["test"],
            "test-group",
            1.0,
            "earliest",
            None,
        )

        mock_consumer.close.assert_called_once()

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_worker_handles_message(self, mock_super):
        """Test worker processes message correctly."""
        source = KafkaSource(topics=["test"])

        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b'{"id": 123}'
        mock_msg.topic.return_value = "test"
        mock_msg.timestamp.return_value = (1, 1000000)  # Type 1, 1000000ms

        mock_consumer = MagicMock()
        mock_consumer.poll.return_value = mock_msg

        mock_queue = MagicMock()

        context = MagicMock()
        context.state = {"consumer": mock_consumer, "logger": MagicMock()}
        context.should_shutdown.return_value = False
        context.should_stop.return_value = False
        context.output_queue = mock_queue

        source.worker_process(
            context,
            "kafka:9092",
            ["test"],
            "test-group",
            1.0,
            "earliest",
            None,
        )

        mock_queue.put.assert_called_once_with(("test", {"id": 123}, 1000000))

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_worker_handles_null_message(self, mock_super):
        """Test worker handles null message (no data available)."""
        source = KafkaSource(topics=["test"])

        mock_consumer = MagicMock()
        mock_consumer.poll.return_value = None

        mock_queue = MagicMock()

        context = MagicMock()
        context.state = {"consumer": mock_consumer, "logger": MagicMock()}
        context.should_shutdown.return_value = False
        context.should_stop.return_value = False
        context.output_queue = mock_queue

        source.worker_process(
            context,
            "kafka:9092",
            ["test"],
            "test-group",
            1.0,
            "earliest",
            None,
        )

        mock_queue.put.assert_not_called()

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    @patch("sgneskig.sources.kafka_source.KafkaError")
    def test_worker_handles_kafka_error(self, mock_kafka_error, mock_super):
        """Test worker handles Kafka error."""
        source = KafkaSource(topics=["test"])

        mock_error = MagicMock()
        mock_error.code.return_value = -1  # Some error code

        mock_msg = MagicMock()
        mock_msg.error.return_value = mock_error

        mock_consumer = MagicMock()
        mock_consumer.poll.return_value = mock_msg

        mock_queue = MagicMock()

        context = MagicMock()
        context.state = {"consumer": mock_consumer, "logger": MagicMock()}
        context.should_shutdown.return_value = False
        context.should_stop.return_value = False
        context.output_queue = mock_queue

        source.worker_process(
            context,
            "kafka:9092",
            ["test"],
            "test-group",
            1.0,
            "earliest",
            None,
        )

        mock_queue.put.assert_not_called()

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_worker_handles_tombstone(self, mock_super):
        """Test worker handles tombstone message (null value)."""
        source = KafkaSource(topics=["test"])

        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = None  # Tombstone

        mock_consumer = MagicMock()
        mock_consumer.poll.return_value = mock_msg

        mock_queue = MagicMock()

        context = MagicMock()
        context.state = {"consumer": mock_consumer, "logger": MagicMock()}
        context.should_shutdown.return_value = False
        context.should_stop.return_value = False
        context.output_queue = mock_queue

        source.worker_process(
            context,
            "kafka:9092",
            ["test"],
            "test-group",
            1.0,
            "earliest",
            None,
        )

        mock_queue.put.assert_not_called()

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_worker_handles_json_decode_error(self, mock_super):
        """Test worker handles invalid JSON."""
        source = KafkaSource(topics=["test"])

        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b"not valid json"
        mock_msg.topic.return_value = "test"

        mock_consumer = MagicMock()
        mock_consumer.poll.return_value = mock_msg

        mock_queue = MagicMock()

        context = MagicMock()
        context.state = {"consumer": mock_consumer, "logger": MagicMock()}
        context.should_shutdown.return_value = False
        context.should_stop.return_value = False
        context.output_queue = mock_queue

        # Should not raise
        source.worker_process(
            context,
            "kafka:9092",
            ["test"],
            "test-group",
            1.0,
            "earliest",
            None,
        )

        mock_queue.put.assert_not_called()

    @patch("sgneskig.sources.kafka_source.ParallelizeSourceElement.__post_init__")
    def test_worker_handles_timestamp_type_zero(self, mock_super):
        """Test worker handles timestamp type 0 (not available)."""
        source = KafkaSource(topics=["test"])

        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b'{"id": 123}'
        mock_msg.topic.return_value = "test"
        # Timestamp type 0 means timestamp is not available
        mock_msg.timestamp.return_value = (0, -1)

        mock_consumer = MagicMock()
        mock_consumer.poll.return_value = mock_msg

        mock_queue = MagicMock()

        context = MagicMock()
        context.state = {"consumer": mock_consumer, "logger": MagicMock()}
        context.should_shutdown.return_value = False
        context.should_stop.return_value = False
        context.output_queue = mock_queue

        source.worker_process(
            context,
            "kafka:9092",
            ["test"],
            "test-group",
            1.0,
            "earliest",
            None,
        )

        # Should have put the message with None timestamp
        mock_queue.put.assert_called_once()
        call_args = mock_queue.put.call_args[0][0]
        # Third element is kafka_ts_ms, should be None for type 0
        assert call_args[2] is None
