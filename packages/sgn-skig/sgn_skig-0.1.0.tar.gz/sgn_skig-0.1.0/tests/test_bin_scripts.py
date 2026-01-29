"""Tests for sgneskig.bin scripts."""

import io
import json
import sys
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sgneskig.bin import grafana_datasource, grafana_import


class TestGrafanaDatasource:
    """Tests for grafana_datasource script."""

    @patch("urllib.request.urlopen")
    def test_create_datasource_success(self, mock_urlopen, capsys):
        """Test successful datasource creation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"name": "test_db"}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with patch.object(sys, "argv", ["grafana-datasource", "--database", "test_db"]):
            grafana_datasource.main()

        captured = capsys.readouterr()
        assert "Created datasource: test_db" in captured.out

    @patch("urllib.request.urlopen")
    def test_custom_arguments(self, mock_urlopen, capsys):
        """Test with custom arguments."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"name": "custom_name"}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with patch.object(
            sys,
            "argv",
            [
                "grafana-datasource",
                "--grafana-url",
                "http://grafana:3000",
                "--grafana-auth",
                "admin:password",
                "--influxdb-url",
                "http://influxdb:8086",
                "--database",
                "my_db",
                "--name",
                "custom_name",
            ],
        ):
            grafana_datasource.main()

        captured = capsys.readouterr()
        assert "Created datasource: custom_name" in captured.out

        # Verify URL was correct
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.full_url == "http://grafana:3000/api/datasources"

    @patch("urllib.request.urlopen")
    def test_datasource_already_exists(self, mock_urlopen, capsys):
        """Test handling of already existing datasource."""
        # Create HTTPError with "already exists" message
        error_response = json.dumps(
            {"message": "data source with the same name already exists"}
        ).encode()
        http_error = urllib.error.HTTPError(
            url="http://localhost:3000/api/datasources",
            code=409,
            msg="Conflict",
            hdrs={},
            fp=io.BytesIO(error_response),
        )
        mock_urlopen.side_effect = http_error

        with patch.object(sys, "argv", ["grafana-datasource", "--database", "test_db"]):
            grafana_datasource.main()

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    @patch("urllib.request.urlopen")
    def test_http_error_other(self, mock_urlopen, capsys):
        """Test handling of other HTTP errors."""
        error_response = json.dumps({"message": "Unauthorized"}).encode()
        http_error = urllib.error.HTTPError(
            url="http://localhost:3000/api/datasources",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(error_response),
        )
        mock_urlopen.side_effect = http_error

        with patch.object(sys, "argv", ["grafana-datasource", "--database", "test_db"]):
            with pytest.raises(SystemExit) as exc_info:
                grafana_datasource.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    @patch("urllib.request.urlopen")
    def test_http_error_non_json_response(self, mock_urlopen, capsys):
        """Test handling of HTTP error with non-JSON response."""
        error_response = b"Internal Server Error"
        http_error = urllib.error.HTTPError(
            url="http://localhost:3000/api/datasources",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=io.BytesIO(error_response),
        )
        mock_urlopen.side_effect = http_error

        with patch.object(sys, "argv", ["grafana-datasource", "--database", "test_db"]):
            with pytest.raises(SystemExit) as exc_info:
                grafana_datasource.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Internal Server Error" in captured.err

    @patch("urllib.request.urlopen")
    def test_default_datasource_name(self, mock_urlopen, capsys):
        """Test that datasource name defaults to database name."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"name": "sgneskig_metrics"}
        ).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with patch.object(sys, "argv", ["grafana-datasource"]):
            grafana_datasource.main()

        # Check the payload sent
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        payload = json.loads(request.data)
        assert payload["name"] == "sgneskig_metrics"
        assert payload["database"] == "sgneskig_metrics"


class TestGrafanaImport:
    """Tests for grafana_import script."""

    @patch("urllib.request.urlopen")
    def test_import_dashboard_success(self, mock_urlopen, capsys):
        """Test successful dashboard import."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"url": "/d/abc123/my-dashboard"}
        ).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_file = Path(tmp_dir) / "dashboard.json"
            dashboard_file.write_text(json.dumps({"title": "Test Dashboard"}))

            with patch.object(sys, "argv", ["grafana-import", str(dashboard_file)]):
                grafana_import.main()

        captured = capsys.readouterr()
        assert "Imported:" in captured.out
        assert "/d/abc123/my-dashboard" in captured.out

    @patch("urllib.request.urlopen")
    def test_import_dashboard_with_slug(self, mock_urlopen, capsys):
        """Test dashboard import response with slug instead of url."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"slug": "my-dashboard"}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_file = Path(tmp_dir) / "dashboard.json"
            dashboard_file.write_text(json.dumps({"title": "Test Dashboard"}))

            with patch.object(sys, "argv", ["grafana-import", str(dashboard_file)]):
                grafana_import.main()

        captured = capsys.readouterr()
        assert "Imported: my-dashboard" in captured.out

    @patch("urllib.request.urlopen")
    def test_custom_arguments(self, mock_urlopen, capsys):
        """Test with custom arguments."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"url": "/d/test"}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_file = Path(tmp_dir) / "dashboard.json"
            dashboard_file.write_text(json.dumps({"title": "Test"}))

            with patch.object(
                sys,
                "argv",
                [
                    "grafana-import",
                    str(dashboard_file),
                    "--grafana-url",
                    "http://grafana:3000",
                    "--grafana-auth",
                    "admin:password",
                    "--folder-id",
                    "5",
                    "--no-overwrite",
                ],
            ):
                grafana_import.main()

        # Verify URL was correct
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.full_url == "http://grafana:3000/api/dashboards/db"

        # Verify payload
        payload = json.loads(request.data)
        assert payload["folderId"] == 5
        assert payload["overwrite"] is False

    def test_file_not_found(self, capsys):
        """Test handling of missing dashboard file."""
        with patch.object(
            sys, "argv", ["grafana-import", "/nonexistent/dashboard.json"]
        ):
            with pytest.raises(SystemExit) as exc_info:
                grafana_import.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err

    def test_invalid_json(self, capsys):
        """Test handling of invalid JSON in dashboard file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_file = Path(tmp_dir) / "dashboard.json"
            dashboard_file.write_text("not valid json {")

            with patch.object(sys, "argv", ["grafana-import", str(dashboard_file)]):
                with pytest.raises(SystemExit) as exc_info:
                    grafana_import.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err

    @patch("urllib.request.urlopen")
    def test_http_error_json_response(self, mock_urlopen, capsys):
        """Test handling of HTTP error with JSON response."""
        error_response = json.dumps({"message": "Dashboard not found"}).encode()
        http_error = urllib.error.HTTPError(
            url="http://localhost:3000/api/dashboards/db",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(error_response),
        )
        mock_urlopen.side_effect = http_error

        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_file = Path(tmp_dir) / "dashboard.json"
            dashboard_file.write_text(json.dumps({"title": "Test"}))

            with patch.object(sys, "argv", ["grafana-import", str(dashboard_file)]):
                with pytest.raises(SystemExit) as exc_info:
                    grafana_import.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Dashboard not found" in captured.err

    @patch("urllib.request.urlopen")
    def test_http_error_non_json_response(self, mock_urlopen, capsys):
        """Test handling of HTTP error with non-JSON response."""
        error_response = b"Internal Server Error"
        http_error = urllib.error.HTTPError(
            url="http://localhost:3000/api/dashboards/db",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=io.BytesIO(error_response),
        )
        mock_urlopen.side_effect = http_error

        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_file = Path(tmp_dir) / "dashboard.json"
            dashboard_file.write_text(json.dumps({"title": "Test"}))

            with patch.object(sys, "argv", ["grafana-import", str(dashboard_file)]):
                with pytest.raises(SystemExit) as exc_info:
                    grafana_import.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Internal Server Error" in captured.err

    @patch("urllib.request.urlopen")
    def test_overwrite_default_true(self, mock_urlopen):
        """Test that overwrite defaults to True."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"url": "/d/test"}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_file = Path(tmp_dir) / "dashboard.json"
            dashboard_file.write_text(json.dumps({"title": "Test"}))

            with patch.object(sys, "argv", ["grafana-import", str(dashboard_file)]):
                grafana_import.main()

        # Verify overwrite is True by default
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        payload = json.loads(request.data)
        assert payload["overwrite"] is True

    @patch("urllib.request.urlopen")
    def test_authorization_header(self, mock_urlopen):
        """Test that authorization header is correctly set."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"url": "/d/test"}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_file = Path(tmp_dir) / "dashboard.json"
            dashboard_file.write_text(json.dumps({"title": "Test"}))

            with patch.object(
                sys,
                "argv",
                [
                    "grafana-import",
                    str(dashboard_file),
                    "--grafana-auth",
                    "user:secret",
                ],
            ):
                grafana_import.main()

        # Verify authorization header
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        auth_header = request.get_header("Authorization")
        assert auth_header is not None
        assert auth_header.startswith("Basic ")
