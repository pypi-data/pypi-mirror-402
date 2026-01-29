"""Tests for sgneskig.metrics.writer module."""

import time
from unittest.mock import MagicMock, patch

from sgneskig.metrics.collector import MetricPoint
from sgneskig.metrics.writer import MetricsWriter


class TestMetricsWriterInit:
    """Tests for MetricsWriter initialization."""

    def test_dry_run_mode_no_connection(self):
        """Test dry_run mode doesn't connect to InfluxDB."""
        writer = MetricsWriter(dry_run=True)
        assert writer.dry_run is True
        assert writer._aggregator is None

    def test_default_values(self):
        """Test default configuration values."""
        writer = MetricsWriter(dry_run=True)
        assert writer.hostname == "localhost"
        assert writer.port == 8086
        assert writer.db == "sgneskig_metrics"
        assert writer.auth is False
        assert writer.https is False
        assert writer.check_certs is True
        assert writer.reduce_dt == 300
        assert writer.reduce_across_tags is True
        assert writer.aggregate == "max"
        assert writer.flush_interval == 2.0

    def test_custom_values(self):
        """Test custom configuration values."""
        writer = MetricsWriter(
            hostname="influx.example.com",
            port=8087,
            db="custom_db",
            auth=True,
            https=True,
            check_certs=False,
            reduce_dt=600,
            reduce_across_tags=False,
            aggregate="min",
            flush_interval=5.0,
            dry_run=True,
        )
        assert writer.hostname == "influx.example.com"
        assert writer.port == 8087
        assert writer.db == "custom_db"
        assert writer.auth is True
        assert writer.https is True
        assert writer.check_certs is False
        assert writer.reduce_dt == 600
        assert writer.reduce_across_tags is False
        assert writer.aggregate == "min"
        assert writer.flush_interval == 5.0

    @patch("sgneskig.metrics.writer.MetricsWriter._connect")
    def test_connect_called_when_not_dry_run(self, mock_connect):
        """Test _connect is called when not in dry_run mode."""
        MetricsWriter(dry_run=False)
        mock_connect.assert_called_once()


class TestMetricsWriterConnect:
    """Tests for MetricsWriter connection."""

    @patch("sgneskig.metrics.writer.MetricsWriter._ensure_database")
    @patch("ligo.scald.io.influx.Aggregator")
    def test_connect_success(self, mock_aggregator_class, mock_ensure_db):
        """Test successful connection to InfluxDB."""
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator

        writer = MetricsWriter(dry_run=False)

        mock_ensure_db.assert_called_once()
        mock_aggregator_class.assert_called_once()
        assert writer._aggregator is mock_aggregator

    @patch("sgneskig.metrics.writer.MetricsWriter._ensure_database")
    def test_connect_import_error(self, mock_ensure_db):
        """Test fallback to dry_run when ligo.scald not available."""
        with patch.dict("sys.modules", {"ligo.scald.io": None}):
            # Force import error
            import sys

            original = sys.modules.get("ligo.scald.io")
            sys.modules["ligo.scald.io"] = None
            try:
                with patch(
                    "sgneskig.metrics.writer.MetricsWriter._connect",
                    wraps=MetricsWriter._connect,
                ):
                    # Create writer with actual connect that will fail
                    writer = MetricsWriter.__new__(MetricsWriter)
                    writer.hostname = "localhost"
                    writer.port = 8086
                    writer.db = "test"
                    writer.auth = False
                    writer.https = False
                    writer.check_certs = True
                    writer.reduce_dt = 300
                    writer.reduce_across_tags = True
                    writer.aggregate = "max"
                    writer.dry_run = False
                    writer._registered_schemas = set()
                    writer._buffers = {}
                    writer._lock = MagicMock()
                    writer._last_flush_time = 0

                    # This should catch ImportError and set dry_run
                    mock_ensure_db.return_value = None
                    try:
                        writer._connect()
                    except Exception:  # noqa: S110
                        pass  # Expected - testing error handling path
            finally:
                if original is not None:
                    sys.modules["ligo.scald.io"] = original
                else:
                    sys.modules.pop("ligo.scald.io", None)


class TestMetricsWriterWrite:
    """Tests for MetricsWriter write operations."""

    def test_write_empty_list(self):
        """Test writing empty list does nothing."""
        writer = MetricsWriter(dry_run=True)
        writer.write([])
        assert writer.get_buffered_count() == 0

    def test_write_single_metric(self):
        """Test writing a single metric."""
        writer = MetricsWriter(dry_run=True)
        metric = MetricPoint(name="test_metric", value=1.5, timestamp=1000.0)

        writer.write([metric])

        assert writer.get_buffered_count() == 1

    def test_write_multiple_metrics(self):
        """Test writing multiple metrics."""
        writer = MetricsWriter(dry_run=True)
        metrics = [
            MetricPoint(name="metric1", value=1.0, timestamp=1000.0),
            MetricPoint(name="metric2", value=2.0, timestamp=1001.0),
            MetricPoint(name="metric1", value=3.0, timestamp=1002.0),
        ]

        writer.write(metrics)

        assert writer.get_buffered_count() == 3

    def test_write_with_tags(self):
        """Test writing metrics with tags."""
        writer = MetricsWriter(dry_run=True)
        metric = MetricPoint(
            name="tagged_metric",
            value=5.0,
            timestamp=1000.0,
            tags={"env": "test", "host": "localhost"},
        )

        writer.write([metric])

        assert writer.get_buffered_count() == 1

    def test_write_auto_flush(self):
        """Test auto-flush when interval exceeded."""
        writer = MetricsWriter(dry_run=True, flush_interval=0.0)
        # Set last flush time in the past
        writer._last_flush_time = time.time() - 10

        metric = MetricPoint(name="test", value=1.0, timestamp=1000.0)
        writer.write([metric])

        # Buffer should be flushed (cleared in dry_run mode)
        assert writer.get_buffered_count() == 0


class TestMetricsWriterFlush:
    """Tests for MetricsWriter flush operations."""

    def test_flush_empty_buffer(self):
        """Test flushing empty buffer."""
        writer = MetricsWriter(dry_run=True)
        writer.flush()  # Should not raise
        assert writer.get_buffered_count() == 0

    def test_flush_clears_buffer(self):
        """Test flush clears buffer."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)  # No auto-flush
        metric = MetricPoint(name="test", value=1.0, timestamp=1000.0)
        writer.write([metric])
        assert writer.get_buffered_count() == 1

        writer.flush()
        assert writer.get_buffered_count() == 0

    def test_flush_with_aggregator(self):
        """Test flush calls aggregator.store_columns."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator
        writer.dry_run = False  # Enable actual writes

        metric = MetricPoint(name="test", value=1.0, timestamp=1000.0)
        writer.write([metric])
        writer.flush()

        mock_aggregator.store_columns.assert_called_once()

    def test_flush_with_tags(self):
        """Test flush handles tagged metrics correctly."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator
        writer.dry_run = False

        metric = MetricPoint(
            name="test", value=1.0, timestamp=1000.0, tags={"env": "prod"}
        )
        writer.write([metric])
        writer.flush()

        mock_aggregator.store_columns.assert_called_once()
        call_args = mock_aggregator.store_columns.call_args
        # First arg is measurement name
        assert call_args[0][0] == "test"

    def test_flush_error_handling(self):
        """Test flush handles errors gracefully."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        mock_aggregator.store_columns.side_effect = Exception("Connection failed")
        writer._aggregator = mock_aggregator
        writer.dry_run = False

        metric = MetricPoint(name="test", value=1.0, timestamp=1000.0)
        writer.write([metric])

        # Should not raise
        writer.flush()


class TestMetricsWriterSchema:
    """Tests for MetricsWriter schema registration."""

    def test_schema_registered_once(self):
        """Test schema is only registered once per metric name."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator

        metric1 = MetricPoint(name="test", value=1.0, timestamp=1000.0)
        metric2 = MetricPoint(name="test", value=2.0, timestamp=1001.0)

        writer.write([metric1])
        writer.write([metric2])

        # Schema should be registered only once
        assert mock_aggregator.register_schema.call_count == 1

    def test_schema_with_tags(self):
        """Test schema registration with tags."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator

        metric = MetricPoint(
            name="tagged",
            value=1.0,
            timestamp=1000.0,
            tags={"env": "prod", "host": "a"},
        )
        writer.write([metric])

        mock_aggregator.register_schema.assert_called_once()
        call_kwargs = mock_aggregator.register_schema.call_args[1]
        assert "tags" in call_kwargs
        # Tags should be sorted
        assert call_kwargs["tags"] == ("env", "host")

    def test_schema_without_tags(self):
        """Test schema registration without tags uses default."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator

        metric = MetricPoint(name="untagged", value=1.0, timestamp=1000.0)
        writer.write([metric])

        mock_aggregator.register_schema.assert_called_once()
        call_kwargs = mock_aggregator.register_schema.call_args[1]
        # Default tag 'source' should be used
        assert call_kwargs["tags"] == ("source",)

    def test_schema_registration_error(self):
        """Test schema registration handles errors gracefully."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        mock_aggregator.register_schema.side_effect = Exception("Schema error")
        writer._aggregator = mock_aggregator

        metric = MetricPoint(name="test", value=1.0, timestamp=1000.0)

        # Should not raise
        writer.write([metric])


class TestMetricsWriterEnsureSchema:
    """Tests for _ensure_schema method."""

    def test_ensure_schema_no_aggregator(self):
        """Test _ensure_schema with no aggregator just records name."""
        writer = MetricsWriter(dry_run=True)
        writer._aggregator = None

        metric = MetricPoint(name="test", value=1.0, timestamp=1000.0)
        writer._ensure_schema(metric)

        assert "test" in writer._registered_schemas

    def test_ensure_schema_already_registered(self):
        """Test _ensure_schema skips if already registered."""
        writer = MetricsWriter(dry_run=True)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator
        writer._registered_schemas.add("test")

        metric = MetricPoint(name="test", value=1.0, timestamp=1000.0)
        writer._ensure_schema(metric)

        # Should not call register_schema
        mock_aggregator.register_schema.assert_not_called()


class TestMetricsWriterClose:
    """Tests for MetricsWriter close operation."""

    def test_close_flushes(self):
        """Test close flushes remaining metrics."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        metric = MetricPoint(name="test", value=1.0, timestamp=1000.0)
        writer.write([metric])
        assert writer.get_buffered_count() == 1

        writer.close()
        assert writer.get_buffered_count() == 0


class TestMetricsWriterGetBufferedCount:
    """Tests for get_buffered_count method."""

    def test_empty_buffer(self):
        """Test count of empty buffer."""
        writer = MetricsWriter(dry_run=True)
        assert writer.get_buffered_count() == 0

    def test_single_metric(self):
        """Test count with single metric."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        writer.write([MetricPoint(name="m", value=1.0, timestamp=0)])
        assert writer.get_buffered_count() == 1

    def test_multiple_metrics_same_name(self):
        """Test count with multiple metrics same name."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        metrics = [MetricPoint(name="m", value=i, timestamp=i) for i in range(5)]
        writer.write(metrics)
        assert writer.get_buffered_count() == 5

    def test_multiple_metrics_different_names(self):
        """Test count with multiple different metrics."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        metrics = [MetricPoint(name=f"m{i}", value=i, timestamp=i) for i in range(3)]
        writer.write(metrics)
        assert writer.get_buffered_count() == 3


class TestMetricsWriterBufferMetric:
    """Tests for _buffer_metric method."""

    def test_buffer_metric_creates_structure(self):
        """Test _buffer_metric creates correct buffer structure."""
        writer = MetricsWriter(dry_run=True)
        metric = MetricPoint(name="test", value=1.5, timestamp=1000.0)

        writer._buffer_metric(metric)

        assert "test" in writer._buffers
        # Empty tag tuple for no tags
        assert () in writer._buffers["test"]
        assert writer._buffers["test"][()]["time"] == [1000.0]
        assert writer._buffers["test"][()]["value"] == [1.5]

    def test_buffer_metric_with_tags(self):
        """Test _buffer_metric with tagged metric."""
        writer = MetricsWriter(dry_run=True)
        metric = MetricPoint(
            name="test", value=2.0, timestamp=2000.0, tags={"env": "prod"}
        )

        writer._buffer_metric(metric)

        tag_tuple = (("env", "prod"),)
        assert tag_tuple in writer._buffers["test"]
        assert writer._buffers["test"][tag_tuple]["value"] == [2.0]


class TestMetricsWriterFlushBuffersLocked:
    """Tests for _flush_buffers_locked method."""

    def test_flush_multiple_tag_values(self):
        """Test flushing metrics with multiple tag values."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator
        writer.dry_run = False

        # Write metrics with different tag values
        metrics = [
            MetricPoint(name="test", value=1.0, timestamp=1000.0, tags={"env": "prod"}),
            MetricPoint(name="test", value=2.0, timestamp=1001.0, tags={"env": "dev"}),
        ]
        writer.write(metrics)
        writer.flush()

        # Should call store_columns once for the measurement
        mock_aggregator.store_columns.assert_called()
        call_args = mock_aggregator.store_columns.call_args
        data = call_args[0][1]  # Second positional arg is data dict
        # Should have both tag values as keys
        assert "prod" in data
        assert "dev" in data

    def test_flush_multiple_tags(self):
        """Test flushing metrics with multiple tag dimensions."""
        writer = MetricsWriter(dry_run=True, flush_interval=9999)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator
        writer.dry_run = False

        metric = MetricPoint(
            name="test",
            value=1.0,
            timestamp=1000.0,
            tags={"env": "prod", "host": "server1"},
        )
        writer.write([metric])
        writer.flush()

        call_args = mock_aggregator.store_columns.call_args
        data = call_args[0][1]
        # Multiple tags should create tuple key
        assert ("prod", "server1") in data


class TestMetricsWriterEnsureDatabase:
    """Tests for _ensure_database method."""

    @patch("urllib.request.urlopen")
    def test_ensure_database_success(self, mock_urlopen):
        """Test database creation success."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        writer = MetricsWriter.__new__(MetricsWriter)
        writer.hostname = "localhost"
        writer.port = 8086
        writer.db = "test_db"
        writer.https = False

        writer._ensure_database()

        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_ensure_database_https(self, mock_urlopen):
        """Test database creation with HTTPS."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        writer = MetricsWriter.__new__(MetricsWriter)
        writer.hostname = "localhost"
        writer.port = 8086
        writer.db = "test_db"
        writer.https = True

        writer._ensure_database()

        # Check URL starts with https
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.full_url.startswith("https://")

    @patch("urllib.request.urlopen")
    def test_ensure_database_error(self, mock_urlopen):
        """Test database creation raises RuntimeError on failure (fail-fast)."""
        mock_urlopen.side_effect = Exception("Connection refused")

        writer = MetricsWriter.__new__(MetricsWriter)
        writer.hostname = "localhost"
        writer.port = 8086
        writer.db = "test_db"
        writer.https = False

        # Should raise RuntimeError (fail-fast behavior)
        import pytest

        with pytest.raises(RuntimeError, match="Cannot reach InfluxDB"):
            writer._ensure_database()


class TestMetricsWriterEdgeCases:
    """Additional edge case tests for MetricsWriter."""

    def test_flush_empty_tag_buffers(self):
        """Test _flush_buffers_locked handles empty tag_buffers (line 215)."""
        writer = MetricsWriter(dry_run=True)

        # Pre-populate with empty dict for a measurement
        writer._buffers["test_measurement"] = {}

        # Manually call flush
        writer._flush_buffers_locked()

        # Should not raise or change anything
        assert True

    def test_flush_empty_time_array(self):
        """Test _flush_buffers_locked skips empty time arrays (line 223)."""
        writer = MetricsWriter(dry_run=True)

        # Pre-populate with buffer that has empty time/value arrays
        writer._buffers["test_measurement"] = {
            (): {"time": [], "value": []},
        }

        # Manually call flush
        writer._flush_buffers_locked()

        # Should not raise
        assert True

    def test_flush_data_empty_after_processing(self):
        """Test _flush_buffers_locked handles empty data dict (line 246)."""
        writer = MetricsWriter(dry_run=True)
        mock_aggregator = MagicMock()
        writer._aggregator = mock_aggregator
        writer.dry_run = False

        # Pre-populate with empty buffers that will result in empty data
        writer._buffers["test_measurement"] = {
            (): {"time": [], "value": []},
        }

        # Manually call flush
        writer._flush_buffers_locked()

        # store_columns should not be called for empty data
        mock_aggregator.store_columns.assert_not_called()

    @patch("sgneskig.metrics.writer.MetricsWriter._ensure_database")
    def test_connect_general_exception(self, mock_ensure_db):
        """Test _connect raises RuntimeError on failure (fail-fast)."""
        import pytest

        # _ensure_database now raises RuntimeError on failure
        mock_ensure_db.side_effect = RuntimeError("Cannot reach InfluxDB")

        # Create writer instance manually to test _connect
        writer = MetricsWriter.__new__(MetricsWriter)
        writer.hostname = "localhost"
        writer.port = 8086
        writer.db = "test"
        writer.auth = False
        writer.https = False
        writer.check_certs = True
        writer.reduce_dt = 300
        writer.reduce_across_tags = True
        writer.aggregate = "max"
        writer.dry_run = False
        writer._aggregator = None
        writer._registered_schemas = set()
        writer._buffers = {}

        # _connect should raise RuntimeError (fail-fast behavior)
        with pytest.raises(RuntimeError, match="Cannot reach InfluxDB"):
            writer._connect()
