"""Tests for sgneskig.transforms module."""

import time
from unittest.mock import MagicMock

from sgn.frames import Frame

from sgneskig.transforms.delay_buffer import DelayBuffer
from sgneskig.transforms.event_latency import EventLatency
from sgneskig.transforms.round_robin_distributor import RoundRobinDistributor


class TestDelayBuffer:
    """Tests for DelayBuffer transform."""

    def test_initialization(self):
        """Test DelayBuffer initializes correctly."""
        buffer = DelayBuffer(delay_seconds=10.0)
        assert buffer.delay_seconds == 10.0
        assert buffer.input_pad_name == "in"
        assert buffer.output_pad_name == "out"
        assert len(buffer._buffer) == 0

    def test_custom_pad_names(self):
        """Test custom pad names."""
        buffer = DelayBuffer(input_pad_name="input", output_pad_name="output")
        assert buffer.sink_pad_names == ["input"]
        assert buffer.source_pad_names == ["output"]

    def test_pull_buffers_events(self):
        """Test pull buffers incoming events."""
        buffer = DelayBuffer(delay_seconds=30.0)
        frame = Frame(data=[{"id": 1}, {"id": 2}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        buffer.pull(mock_pad, frame)

        assert len(buffer._buffer) == 2

    def test_pull_gap_frame(self):
        """Test pull ignores gap frames."""
        buffer = DelayBuffer(delay_seconds=30.0)
        frame = Frame(data=None, is_gap=True, EOS=False)
        mock_pad = MagicMock()

        buffer.pull(mock_pad, frame)

        assert len(buffer._buffer) == 0

    def test_pull_single_event(self):
        """Test pull handles single event (not list)."""
        buffer = DelayBuffer(delay_seconds=30.0)
        frame = Frame(data={"id": 1}, is_gap=False, EOS=False)
        mock_pad = MagicMock()

        buffer.pull(mock_pad, frame)

        assert len(buffer._buffer) == 1

    def test_internal_releases_aged_events(self):
        """Test internal releases events after delay expires."""
        buffer = DelayBuffer(delay_seconds=0.01)  # 10ms delay
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        buffer.pull(mock_pad, frame)
        time.sleep(0.02)  # Wait for delay to expire
        buffer.internal()

        assert len(buffer._output_events) == 1
        assert len(buffer._buffer) == 0

    def test_internal_holds_recent_events(self):
        """Test internal holds events within delay window."""
        buffer = DelayBuffer(delay_seconds=30.0)  # Long delay
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        buffer.pull(mock_pad, frame)
        buffer.internal()

        assert len(buffer._output_events) == 0
        assert len(buffer._buffer) == 1

    def test_internal_eos_flushes_all(self):
        """Test EOS flushes all buffered events."""
        buffer = DelayBuffer(delay_seconds=30.0)
        frame1 = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        frame2 = Frame(data=[{"id": 2}], is_gap=False, EOS=True)
        mock_pad = MagicMock()

        buffer.pull(mock_pad, frame1)
        buffer.pull(mock_pad, frame2)
        buffer.internal()

        assert len(buffer._output_events) == 2
        assert len(buffer._buffer) == 0

    def test_new_returns_output_frame(self):
        """Test new returns frame with released events."""
        buffer = DelayBuffer(delay_seconds=0.001)
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_sink_pad = MagicMock()
        mock_source_pad = MagicMock()

        buffer.pull(mock_sink_pad, frame)
        time.sleep(0.005)
        buffer.internal()
        output = buffer.new(mock_source_pad)

        assert output.data == [{"id": 1}]
        assert output.is_gap is False

    def test_new_returns_gap_when_empty(self):
        """Test new returns gap frame when no events released."""
        buffer = DelayBuffer(delay_seconds=30.0)
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_sink_pad = MagicMock()
        mock_source_pad = MagicMock()

        buffer.pull(mock_sink_pad, frame)
        buffer.internal()
        output = buffer.new(mock_source_pad)

        assert output.is_gap is True
        assert output.data is None

    def test_metrics_buffered(self):
        """Test metrics are recorded."""
        buffer = DelayBuffer(delay_seconds=30.0, metrics_enabled=True)
        frame = Frame(data=[{"id": 1}, {"id": 2}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        buffer.pull(mock_pad, frame)

        # Check counter incremented for events_buffered
        assert len(buffer._counters) > 0


class TestEventLatency:
    """Tests for EventLatency transform."""

    def test_initialization(self):
        """Test EventLatency initializes correctly."""
        latency = EventLatency(metric_name="my_latency", time_field="timestamp")
        assert latency.metric_name == "my_latency"
        assert latency.time_field == "timestamp"
        assert latency.tag_field is None

    def test_custom_pad_names(self):
        """Test custom pad names."""
        latency = EventLatency(input_pad_name="input", output_pad_name="output")
        assert latency.sink_pad_names == ["input"]
        assert latency.source_pad_names == ["output"]

    def test_pull_measures_latency(self):
        """Test pull measures latency for events."""
        latency = EventLatency(time_field="gpstime", metrics_enabled=True)
        # Use a GPS time about 1 second ago
        now = time.time() + 315964800  # Approx GPS time (UTC -> GPS offset)
        event_time = now - 1.0  # 1 second ago

        frame = Frame(data=[{"gpstime": event_time}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        latency.pull(mock_pad, frame)

        # Should have recorded a latency metric
        assert len(latency._metrics_buffer) == 1

    def test_pull_gap_frame(self):
        """Test pull ignores gap frames."""
        latency = EventLatency(metrics_enabled=True)
        frame = Frame(data=None, is_gap=True, EOS=False)
        mock_pad = MagicMock()

        latency.pull(mock_pad, frame)

        assert len(latency._metrics_buffer) == 0

    def test_pull_missing_time_field(self):
        """Test pull handles events missing time field."""
        latency = EventLatency(time_field="gpstime", metrics_enabled=True)
        frame = Frame(data=[{"other_field": 123}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        latency.pull(mock_pad, frame)

        # No metric recorded for events without timestamp
        assert len(latency._metrics_buffer) == 0

    def test_pull_invalid_timestamp(self):
        """Test pull handles invalid timestamp values."""
        latency = EventLatency(time_field="gpstime", metrics_enabled=True)
        frame = Frame(data=[{"gpstime": "not-a-number"}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        latency.pull(mock_pad, frame)

        # No metric recorded for invalid timestamp
        assert len(latency._metrics_buffer) == 0

    def test_pull_with_tag_field(self):
        """Test pull records metrics with tag."""
        latency = EventLatency(
            time_field="gpstime", tag_field="pipeline", metrics_enabled=True
        )
        now = time.time() + 315964800
        frame = Frame(
            data=[{"gpstime": now - 1.0, "pipeline": "test"}], is_gap=False, EOS=False
        )
        mock_pad = MagicMock()

        latency.pull(mock_pad, frame)

        # Metric should have tag
        assert len(latency._metrics_buffer) == 1
        assert latency._metrics_buffer[0].tags == {"pipeline": "test"}

    def test_pull_single_event(self):
        """Test pull handles single event (not list)."""
        latency = EventLatency(time_field="gpstime", metrics_enabled=True)
        now = time.time() + 315964800
        frame = Frame(data={"gpstime": now - 1.0}, is_gap=False, EOS=False)
        mock_pad = MagicMock()

        latency.pull(mock_pad, frame)

        assert len(latency._metrics_buffer) == 1

    def test_new_passes_through_frame(self):
        """Test new passes through original frame unchanged."""
        latency = EventLatency()
        input_frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_sink_pad = MagicMock()
        mock_source_pad = MagicMock()

        latency.pull(mock_sink_pad, input_frame)
        output = latency.new(mock_source_pad)

        assert output is input_frame

    def test_new_returns_gap_when_no_input(self):
        """Test new returns gap when no input received."""
        latency = EventLatency()
        mock_source_pad = MagicMock()

        output = latency.new(mock_source_pad)

        assert output.is_gap is True

    def test_get_field_dict(self):
        """Test _get_field extracts from dict."""
        latency = EventLatency()
        event = {"field": "value"}

        result = latency._get_field(event, "field")

        assert result == "value"

    def test_get_field_object(self):
        """Test _get_field extracts from object."""
        latency = EventLatency()

        class Event:
            field = "value"

        result = latency._get_field(Event(), "field")

        assert result == "value"

    def test_metrics_schema_built(self):
        """Test metrics schema is built from config."""
        latency = EventLatency(
            metric_name="custom_latency",
            time_field="ts",
            tag_field="source",
            description="Custom description",
        )

        assert len(latency._metrics_schema) == 1
        schema = latency._metrics_schema[0]
        assert schema.name == "custom_latency"
        assert schema.metric_type == "timing"
        assert schema.tags == ["source"]
        assert schema.description == "Custom description"


class TestRoundRobinDistributor:
    """Tests for RoundRobinDistributor transform."""

    def test_initialization(self):
        """Test RoundRobinDistributor initializes correctly."""
        distributor = RoundRobinDistributor(num_workers=3)
        assert distributor.num_workers == 3
        assert distributor._next_worker == 0
        assert len(distributor.source_pad_names) == 3

    def test_worker_pad_names(self):
        """Test worker pad names are generated correctly."""
        distributor = RoundRobinDistributor(num_workers=4, worker_pad_prefix="worker")
        assert list(distributor.source_pad_names) == [
            "worker_0",
            "worker_1",
            "worker_2",
            "worker_3",
        ]

    def test_custom_input_pad(self):
        """Test custom input pad name."""
        distributor = RoundRobinDistributor(input_pad_name="events")
        assert distributor.sink_pad_names == ["events"]

    def test_pull_stores_frame(self):
        """Test pull stores incoming frame."""
        distributor = RoundRobinDistributor(num_workers=2)
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame)

        assert distributor._current_frame is frame

    def test_internal_distributes_single_event(self):
        """Test internal distributes single event to one worker."""
        distributor = RoundRobinDistributor(num_workers=4)
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame)
        distributor.internal()

        # First worker should have the event
        assert distributor._output_frames["worker_0"].data == [{"id": 1}]
        assert distributor._output_frames["worker_0"].is_gap is False

        # Other workers should have gap frames
        assert distributor._output_frames["worker_1"].is_gap is True
        assert distributor._output_frames["worker_2"].is_gap is True
        assert distributor._output_frames["worker_3"].is_gap is True

    def test_internal_round_robin_distribution(self):
        """Test events are distributed round-robin."""
        distributor = RoundRobinDistributor(num_workers=2)
        frame = Frame(data=[{"id": 1}, {"id": 2}, {"id": 3}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame)
        distributor.internal()

        # Events should be distributed: 1->worker_0, 2->worker_1, 3->worker_0
        assert distributor._output_frames["worker_0"].data == [{"id": 1}, {"id": 3}]
        assert distributor._output_frames["worker_1"].data == [{"id": 2}]

    def test_internal_gap_frame(self):
        """Test internal handles gap frames."""
        distributor = RoundRobinDistributor(num_workers=2)
        frame = Frame(data=None, is_gap=True, EOS=False)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame)
        distributor.internal()

        # All workers should get gap frames
        assert distributor._output_frames["worker_0"].is_gap is True
        assert distributor._output_frames["worker_1"].is_gap is True

    def test_internal_empty_data(self):
        """Test internal handles empty data."""
        distributor = RoundRobinDistributor(num_workers=2)
        frame = Frame(data=[], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame)
        distributor.internal()

        # All workers should get gap frames
        assert distributor._output_frames["worker_0"].is_gap is True
        assert distributor._output_frames["worker_1"].is_gap is True

    def test_internal_single_item_not_list(self):
        """Test internal handles single item (not list)."""
        distributor = RoundRobinDistributor(num_workers=2)
        frame = Frame(data={"id": 1}, is_gap=False, EOS=False)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame)
        distributor.internal()

        # First worker should have the event
        assert distributor._output_frames["worker_0"].data == [{"id": 1}]

    def test_new_returns_correct_frame(self):
        """Test new returns frame for correct worker pad."""
        distributor = RoundRobinDistributor(num_workers=2)
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_sink_pad = MagicMock()

        distributor.pull(mock_sink_pad, frame)
        distributor.internal()

        # Create mock source pads
        mock_worker0_pad = MagicMock()
        mock_worker1_pad = MagicMock()
        distributor.rsrcs = {mock_worker0_pad: "worker_0", mock_worker1_pad: "worker_1"}

        worker0_frame = distributor.new(mock_worker0_pad)
        worker1_frame = distributor.new(mock_worker1_pad)

        assert worker0_frame.data == [{"id": 1}]
        assert worker1_frame.is_gap is True

    def test_new_returns_gap_for_unknown_pad(self):
        """Test new returns gap for unknown pad."""
        distributor = RoundRobinDistributor(num_workers=2)
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=False)
        mock_sink_pad = MagicMock()

        distributor.pull(mock_sink_pad, frame)
        distributor.internal()

        # Unknown pad
        mock_unknown_pad = MagicMock()
        distributor.rsrcs = {mock_unknown_pad: "unknown_pad"}

        result = distributor.new(mock_unknown_pad)

        assert result.is_gap is True

    def test_internal_eos_propagated(self):
        """Test EOS flag is propagated to all workers."""
        distributor = RoundRobinDistributor(num_workers=2)
        frame = Frame(data=[{"id": 1}], is_gap=False, EOS=True)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame)
        distributor.internal()

        assert distributor._output_frames["worker_0"].EOS is True
        assert distributor._output_frames["worker_1"].EOS is True

    def test_metrics_recorded(self):
        """Test metrics are recorded for distributed events."""
        distributor = RoundRobinDistributor(num_workers=2, metrics_enabled=True)
        frame = Frame(data=[{"id": 1}, {"id": 2}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame)
        distributor.internal()

        # Should have counter increments
        assert len(distributor._counters) > 0

    def test_worker_counter_advances(self):
        """Test worker counter advances correctly."""
        distributor = RoundRobinDistributor(num_workers=3)

        # Distribute 5 events across 2 frames
        frame1 = Frame(data=[{"id": 1}, {"id": 2}], is_gap=False, EOS=False)
        frame2 = Frame(data=[{"id": 3}, {"id": 4}, {"id": 5}], is_gap=False, EOS=False)
        mock_pad = MagicMock()

        distributor.pull(mock_pad, frame1)
        distributor.internal()
        assert distributor._next_worker == 2  # After 2 events

        distributor.pull(mock_pad, frame2)
        distributor.internal()
        assert distributor._next_worker == 2  # After 5 events total (5 % 3 = 2)
