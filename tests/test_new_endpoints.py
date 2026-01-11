"""Unit tests for new REST API endpoints added during modernization."""

import unittest
from unittest.mock import Mock, patch

from requests.models import Response

from meticulous.api import Api
from meticulous.api_types import (
    APIError,
    MachineState,
    UpdateCheckResponse,
    UpdateStatus,
    TimezoneResponse,
    ProfileImportResponse,
    ProfileChange,
    WifiSystemStatus,
    WiFiQRData,
    LogFile,
)


class TestMachineManagement(unittest.TestCase):
    """Test machine management endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_machine_state(self, mock_get: Mock) -> None:
        """Test getting machine state."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "state": "idle",
            "status": "ready",
            "extracting": False,
        }
        mock_get.return_value = mock_response

        result = self.api.get_machine_state()

        self.assertIsInstance(result, MachineState)
        self.assertEqual(result.state, "idle")
        self.assertEqual(result.status, "ready")
        self.assertFalse(result.extracting)
        self.assertFalse(result.extracting)

    @patch("requests.Session.post")
    def test_check_for_updates(self, mock_post: Mock) -> None:
        """Test checking for OS updates."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "available": True,
            "version": "1.3.0",
            "channel": "stable",
        }
        mock_post.return_value = mock_response

        result = self.api.check_for_updates()

        self.assertIsInstance(result, UpdateCheckResponse)
        self.assertTrue(result.available)
        self.assertEqual(result.version, "1.3.0")

    @patch("requests.Session.post")
    def test_perform_os_update(self, mock_post: Mock) -> None:
        """Test performing OS update."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "updating",
            "progress": 0,
        }
        mock_post.return_value = mock_response

        result = self.api.perform_os_update()

        self.assertIsInstance(result, UpdateStatus)
        self.assertEqual(result.status, "updating")

    @patch("requests.Session.post")
    def test_cancel_update(self, mock_post: Mock) -> None:
        """Test canceling OS update."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "cancelled",
            "progress": 0,
        }
        mock_post.return_value = mock_response

        result = self.api.cancel_update()

        self.assertIsInstance(result, UpdateStatus)
        self.assertEqual(result.status, "cancelled")

    @patch("requests.Session.post")
    def test_reboot_machine(self, mock_post: Mock) -> None:
        """Test rebooting machine."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "rebooting",
            "progress": 0,
        }
        mock_post.return_value = mock_response

        result = self.api.reboot_machine()

        self.assertIsInstance(result, UpdateStatus)
        self.assertEqual(result.status, "rebooting")


class TestTimezoneManagement(unittest.TestCase):
    """Test timezone management endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_timezones(self, mock_get: Mock) -> None:
        """Test getting timezone regions."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "countries": ["US", "CA", "MX"],
            "cities": None,
        }
        mock_get.return_value = mock_response

        result = self.api.get_timezones()

        self.assertFalse(isinstance(result, APIError))
        self.assertIsNotNone(result.countries)

    @patch("requests.Session.get")
    def test_get_timezone(self, mock_get: Mock) -> None:
        """Test getting current timezone."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "timezone": "America/New_York",
            "offset": -18000,
        }
        mock_get.return_value = mock_response

        result = self.api.get_timezone()

        self.assertIsInstance(result, TimezoneResponse)
        self.assertEqual(result.timezone, "America/New_York")

    @patch("requests.Session.post")
    def test_set_timezone(self, mock_post: Mock) -> None:
        """Test setting timezone."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "timezone": "America/Los_Angeles",
            "offset": -28800,
        }
        mock_post.return_value = mock_response

        result = self.api.set_timezone("America/Los_Angeles")

        self.assertIsInstance(result, TimezoneResponse)
        self.assertEqual(result.timezone, "America/Los_Angeles")


class TestProfileManagement(unittest.TestCase):
    """Test profile management endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.post")
    @patch("builtins.open", create=True)
    def test_import_profiles(self, mock_open: Mock, mock_post: Mock) -> None:
        """Test importing profiles from file."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "imported": 3,
            "profiles": ["profile1", "profile2", "profile3"],
        }
        mock_post.return_value = mock_response

        # Mock file reading
        mock_file = Mock()
        mock_file.read.return_value = b"profile data"
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.api.import_profiles("profiles.zip")

        self.assertIsInstance(result, ProfileImportResponse)
        self.assertEqual(result.imported, 3)

    @patch("requests.Session.get")
    def test_get_profile_changes(self, mock_get: Mock) -> None:
        """Test getting profile change history."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "type": "modified",
                "profile_id": "test-id",
                "change_id": "change-001",
                "timestamp": 1704067200,
            }
        ]
        mock_get.return_value = mock_response

        result = self.api.get_profile_changes()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ProfileChange)
        self.assertEqual(result[0].type, "modified")
        self.assertEqual(result[0].change_id, "change-001")

    @patch("requests.Session.post")
    def test_load_legacy_profile(self, mock_post: Mock) -> None:
        """Test loading legacy Decent profile format."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Converted Profile",
            "id": "converted-id",
            "author": "legacy",
            "author_id": "00000000-0000-0000-0000-000000000000",
            "temperature": 93,
            "final_weight": 36,
            "stages": [],
        }
        mock_post.return_value = mock_response

        legacy_data = {"profile_title": "Old Profile", "steps": []}
        result = self.api.load_legacy_profile(legacy_data)

        self.assertFalse(isinstance(result, APIError))

    @patch("requests.Session.post")
    @patch("builtins.open", create=True)
    def test_upload_sound_theme(self, mock_open: Mock, mock_post: Mock) -> None:
        """Test uploading custom sound theme."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Mock file reading
        mock_file = Mock()
        mock_file.read.return_value = b"sound theme data"
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.api.upload_sound_theme("theme.zip")

        self.assertIsNone(result)
        mock_post.assert_called_once()


class TestWiFiManagement(unittest.TestCase):
    """Test WiFi management endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_wifi_status(self, mock_get: Mock) -> None:
        """Test getting WiFi system status."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "connected": True,
            "connection_name": "WiFi",
            "gateway": "192.168.1.1",
            "routes": ["default"],
            "ips": ["192.168.1.100"],
            "dns": ["8.8.8.8"],
            "mac": "aa:bb:cc:dd:ee:ff",
            "hostname": "meticulous",
            "domains": ["local"],
        }
        mock_get.return_value = mock_response

        result = self.api.get_wifi_status()

        self.assertIsInstance(result, WifiSystemStatus)
        self.assertTrue(result.connected)
        self.assertEqual(result.gateway, "192.168.1.1")

    @patch("requests.Session.post")
    def test_scan_wifi(self, mock_post: Mock) -> None:
        """Test scanning for WiFi networks."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "scanning": True,
            "networks": [],
        }
        mock_post.return_value = mock_response

        result = self.api.scan_wifi()

        self.assertFalse(isinstance(result, APIError))
        self.assertTrue(result.get("scanning"))

    @patch("requests.Session.get")
    def test_get_wifi_qr_data(self, mock_get: Mock) -> None:
        """Test getting WiFi QR code data as JSON."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ssid": "MyNetwork",
            "password": "secret123",
            "encryption": "WPA2",
        }
        mock_get.return_value = mock_response

        result = self.api.get_wifi_qr_data()

        self.assertIsInstance(result, WiFiQRData)
        self.assertEqual(result.ssid, "MyNetwork")
        self.assertEqual(result.encryption, "WPA2")


class TestHistoryManagement(unittest.TestCase):
    """Test history management endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.delete")
    def test_delete_history_entry(self, mock_delete: Mock) -> None:
        """Test deleting a history entry."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        result = self.api.delete_history_entry("shot-001")

        self.assertIsNone(result)
        mock_delete.assert_called_once()

    @patch("requests.Session.get")
    def test_export_history(self, mock_get: Mock) -> None:
        """Test exporting history as archive."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = b"exported data"
        mock_get.return_value = mock_response

        result = self.api.export_history()

        self.assertIsInstance(result, bytes)
        self.assertEqual(result, b"exported data")


class TestLogManagement(unittest.TestCase):
    """Test log management endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_debug_log(self, mock_get: Mock) -> None:
        """Test getting debug log."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = "Debug log contents"
        mock_get.return_value = mock_response

        result = self.api.get_debug_log()

        self.assertEqual(result, "Debug log contents")

    @patch("requests.Session.get")
    def test_list_logs(self, mock_get: Mock) -> None:
        """Test listing available log files."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "system.log",
                "size": 1024,
                "modified": 1704067200,
            },
            {
                "name": "error.log",
                "size": 512,
                "modified": 1704153600,
            },
        ]
        mock_get.return_value = mock_response

        result = self.api.list_logs()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], LogFile)
        self.assertEqual(result[0].name, "system.log")

    @patch("requests.Session.get")
    def test_get_log_file(self, mock_get: Mock) -> None:
        """Test getting a specific log file."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = b"log file contents"
        mock_get.return_value = mock_response

        result = self.api.get_log_file("system.log")

        self.assertIsInstance(result, bytes)
        self.assertEqual(result, b"log file contents")


class TestAPIErrorHandling(unittest.TestCase):
    """Test error handling for new endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_machine_state_error(self, mock_get: Mock) -> None:
        """Test error handling for machine state endpoint."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_get.return_value = mock_response

        result = self.api.get_machine_state()

        self.assertIsInstance(result, APIError)
        self.assertEqual(result.error, "Internal server error")

    @patch("requests.Session.get")
    def test_wifi_status_not_available(self, mock_get: Mock) -> None:
        """Test WiFi status when WiFi is not available."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "WiFi not available"}
        mock_get.return_value = mock_response

        result = self.api.get_wifi_status()

        self.assertIsInstance(result, APIError)
        self.assertEqual(result.error, "WiFi not available")

    @patch("requests.Session.post")
    def test_profile_import_invalid_file(self, mock_post: Mock) -> None:
        """Test profile import with invalid file."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid profile file"}
        mock_post.return_value = mock_response

        with patch("builtins.open", create=True) as mock_open:
            mock_file = Mock()
            mock_file.read.return_value = b"invalid data"
            mock_open.return_value.__enter__.return_value = mock_file

            result = self.api.import_profiles("invalid.zip")

        self.assertIsInstance(result, APIError)
        self.assertEqual(result.error, "Invalid profile file")


if __name__ == "__main__":
    unittest.main()
