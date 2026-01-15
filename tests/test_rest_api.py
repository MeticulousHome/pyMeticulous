"""Unit tests for all REST API endpoints.

# pyright: reportGeneralTypeIssues=false, reportUnknownMemberType=false

Comprehensive tests for all HTTP REST endpoints including profiles, device info,
history, settings, machine management, timezone, WiFi, logs, and error handling.
"""

import json
import unittest
from unittest.mock import Mock, patch

from requests.models import Response

from meticulous import Api, APIError
from typing import cast, List

from meticulous.api_types import (
    BrightnessRequest,
    DeviceInfo,
    HistoryListingResponse,
    HistoryStats,
    HistoryQueryParams,
    Settings,
    OSStatusResponse,
    ShotRatingResponse,
    RateShotResponse,
    DefaultProfiles,
    Regions,
    UpdateCheckResponse,
    UpdateStatus,
    TimezoneResponse,
    ProfileImportResponse,
    ProfileChange,
    WiFiQRData,
    WiFiConfig,
    WiFiConfigResponse,
    LogFile,
)
from .mock_responses import (
    MOCK_PROFILE_LIST_RESPONSE,
    MOCK_DEVICE_INFO_RESPONSE,
    MOCK_HISTORY_LISTING_RESPONSE,
    MOCK_HISTORY_STATS_RESPONSE,
    MOCK_SETTINGS_RESPONSE,
    MOCK_DEFAULT_PROFILES_RESPONSE,
    MOCK_SHOT_RATING_RESPONSE,
    MOCK_RATE_SHOT_RESPONSE,
    MOCK_OS_STATUS_RESPONSE,
    MOCK_REGIONS_RESPONSE,
    MOCK_HISTORY_DATES_RESPONSE,
    MOCK_SHOT_FILES_RESPONSE,
    MOCK_SHOT_LOG_RESPONSE,
    MOCK_SHOT_LOG_ZST,
)


class TestProfileEndpoints(unittest.TestCase):
    """Test profile-related REST endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_list_profiles(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_PROFILE_LIST_RESPONSE
        mock_get.return_value = mock_response
        profiles_res = self.api.list_profiles()
        profiles = cast(list, profiles_res)

        self.assertEqual(len(profiles), 3)
        self.assertEqual(profiles[0].name, "Italian limbus")
        self.assertEqual(profiles[1].display.accentColor, "#FF5733")
        self.assertEqual(profiles[2].id, "06050134-0680-408e-8fe4-60e7d329b136")

    @patch("requests.Session.get")
    def test_get_profile_not_found(self, mock_get: Mock) -> None:
        # Set up the mock to return a 404 response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Profile not found"}
        mock_get.return_value = mock_response

        profile_id = "nonexistent-profile-id"
        result = self.api.get_profile(profile_id)
        self.assertIsInstance(result, APIError)
        err = cast(APIError, result)
        self.assertEqual(err.error, "Profile not found")

    @patch("requests.Session.get")
    def test_get_default_profiles(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_DEFAULT_PROFILES_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_default_profiles()
        self.assertIsInstance(result, DefaultProfiles)
        df = cast(DefaultProfiles, result)
        self.assertEqual(len(df.default), 1)
        self.assertEqual(len(df.community), 1)

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
        imp = cast(ProfileImportResponse, result)
        self.assertEqual(imp.imported, 3)

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
        changes = cast(list, result)
        self.assertEqual(len(changes), 1)
        self.assertIsInstance(changes[0], ProfileChange)
        self.assertEqual(changes[0].type, "modified")
        self.assertEqual(changes[0].change_id, "change-001")

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


class TestDeviceEndpoints(unittest.TestCase):
    """Test device information and settings endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_device_info(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_DEVICE_INFO_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_device_info()
        self.assertIsInstance(result, DeviceInfo)
        info = cast(DeviceInfo, result)
        self.assertEqual(info.name, "meticulous")
        self.assertEqual(info.serial, "MT12345678")
        self.assertEqual(info.mainVoltage, 230.5)
        self.assertEqual(len(info.version_history), 4)

    @patch("requests.Session.post")
    def test_set_brightness(self, mock_post: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        brightness_req = BrightnessRequest(brightness=0.8, interpolation="curve")
        result = self.api.set_brightness(brightness_req)

        self.assertIsNone(result)
        mock_post.assert_called_once()

    def test_set_brightness_out_of_range(self) -> None:
        """Test that BrightnessRequest rejects values outside 0-1 range."""
        # Test too low
        with self.assertRaises(ValueError) as ctx:
            BrightnessRequest(brightness=-0.1)
        self.assertIn("must be between 0 and 1", str(ctx.exception))

        # Test too high
        with self.assertRaises(ValueError) as ctx:
            BrightnessRequest(brightness=1.5)
        self.assertIn("must be between 0 and 1", str(ctx.exception))

        # Test boundary values are valid
        BrightnessRequest(brightness=0.0)  # Should not raise
        BrightnessRequest(brightness=1.0)  # Should not raise

    @patch("requests.Session.get")
    def test_get_settings(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SETTINGS_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_settings()
        self.assertIsNotNone(result)
        settings = cast(Settings, result)
        self.assertEqual(settings.auto_preheat, 5)
        self.assertTrue(settings.enable_sounds)
        self.assertEqual(settings.update_channel, "stable")


class TestHistoryEndpoints(unittest.TestCase):
    """Test history-related REST endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_history_short_listing(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_HISTORY_LISTING_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_history_short_listing()
        self.assertIsInstance(result, HistoryListingResponse)
        listing = cast(HistoryListingResponse, result)
        self.assertEqual(len(listing.history), 1)
        self.assertEqual(listing.history[0].name, "Morning espresso")
        self.assertEqual(listing.history[0].rating, "like")

    @patch("requests.Session.post")
    def test_search_history(self, mock_post: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"history": []}
        mock_post.return_value = mock_response

        query = HistoryQueryParams(
            query="espresso", max_results=10, sort="desc", order_by=["date"]
        )
        result = self.api.search_history(query)

        self.assertIsNotNone(result)
        mock_post.assert_called_once()

    @patch("requests.Session.get")
    def test_get_history_statistics(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_HISTORY_STATS_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_history_statistics()
        self.assertIsInstance(result, HistoryStats)
        stats = cast(HistoryStats, result)
        self.assertEqual(stats.totalSavedShots, 150)
        self.assertEqual(len(stats.byProfile), 3)
        self.assertEqual(stats.byProfile[0].name, "Italian limbus")
        self.assertEqual(stats.byProfile[0].count, 75)

    @patch("requests.Session.get")
    def test_get_history_dates(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_HISTORY_DATES_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_history_dates()
        files = cast(list, result)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].name, "2024-01-02")
        self.assertEqual(files[0].url, "2024-01-02")

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


class TestShotEndpoints(unittest.TestCase):
    """Test shot log and rating endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.post")
    def test_rate_shot(self, mock_post: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_RATE_SHOT_RESPONSE
        mock_post.return_value = mock_response

        result = self.api.rate_shot(1, "like")
        self.assertIsInstance(result, RateShotResponse)
        rated = cast(RateShotResponse, result)
        self.assertEqual(rated.shot_id, 1)
        self.assertEqual(rated.rating, "like")
        self.assertEqual(rated.status, "success")

    @patch("requests.Session.get")
    def test_get_shot_rating(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SHOT_RATING_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_shot_rating(1)
        self.assertIsInstance(result, ShotRatingResponse)
        rating = cast(ShotRatingResponse, result)
        self.assertEqual(rating.shot_id, 1)
        self.assertEqual(rating.rating, "like")

    @patch("requests.Session.get")
    def test_get_current_shot_none(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = None
        mock_get.return_value = mock_response

        result = self.api.get_current_shot()

        self.assertIsNone(result)

    @patch("requests.Session.get")
    def test_get_shot_files(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SHOT_FILES_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_shot_files("2024-01-02")
        files = cast(list, result)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].url, "21:04:06.shot.json")

    @patch("requests.Session.get")
    def test_get_shot_log_plain_json(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_SHOT_LOG_RESPONSE).encode()
        mock_get.return_value = mock_response

        result = self.api.get_shot_log("2024-01-02", "21:04:06.shot.json")
        log = cast(dict, result)
        self.assertEqual(log["shot"], "latest")
        self.assertEqual(log["value"], 1)

    @patch("requests.Session.get")
    def test_get_shot_log_zst(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = MOCK_SHOT_LOG_ZST
        mock_get.return_value = mock_response

        result = self.api.get_shot_log("2024-01-02", "20:55:00.shot.json.zst")
        log = cast(dict, result)
        self.assertEqual(log["shot"], "latest")


class TestWiFiConfigParsing(unittest.TestCase):
    """Test WiFi config response parsing shapes."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_wifi_config_wrapped_response(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "config": {
                "mode": "client",
                "apName": "MyAP",
                "apPassword": "secret",
            },
            "status": {
                "connected": True,
                "connection_name": "home",
                "gateway": "192.168.1.1",
                "routes": ["0.0.0.0/0"],
                "ips": ["192.168.1.10"],
                "dns": ["8.8.8.8"],
                "mac": "aa:bb:cc:dd:ee:ff",
                "hostname": "machine",
                "domains": ["local"],
            },
        }
        mock_get.return_value = mock_response

        result = self.api.get_wifi_config()
        self.assertIsInstance(result, WiFiConfigResponse)
        resp = cast(WiFiConfigResponse, result)
        self.assertEqual(resp.config.apName, "MyAP")
        self.assertEqual(resp.status.connection_name, "home")

    @patch("requests.Session.get")
    def test_get_wifi_config_bare_response(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "mode": "client",
            "apName": "Cafe",
            "apPassword": "beans",
        }
        mock_get.return_value = mock_response

        result = self.api.get_wifi_config()
        self.assertIsInstance(result, WiFiConfig)
        cfg = cast(WiFiConfig, result)
        self.assertEqual(cfg.apName, "Cafe")

    @patch("requests.Session.get")
    def test_get_shot_log_error(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "not found", "status": "404"}
        mock_get.return_value = mock_response

        result = self.api.get_shot_log("2024-01-02", "missing.shot.json")
        self.assertIsInstance(result, APIError)
        err = cast(APIError, result)
        self.assertEqual(err.error, "not found")

    @patch("requests.Session.get")
    def test_get_last_shot_log(self, mock_get: Mock) -> None:
        dates_response = Mock(spec=Response)
        dates_response.status_code = 200
        dates_response.json.return_value = MOCK_HISTORY_DATES_RESPONSE

        files_response = Mock(spec=Response)
        files_response.status_code = 200
        files_response.json.return_value = MOCK_SHOT_FILES_RESPONSE

        log_response = Mock(spec=Response)
        log_response.status_code = 200
        log_response.content = json.dumps(MOCK_SHOT_LOG_RESPONSE).encode()

        mock_get.side_effect = [dates_response, files_response, log_response]

        result = self.api.get_last_shot_log()
        log = cast(dict, result)
        self.assertEqual(log["shot"], "latest")


class TestMachineManagement(unittest.TestCase):
    """Test machine state, updates, and system operations."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_os_status(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_OS_STATUS_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_os_status()
        self.assertIsInstance(result, OSStatusResponse)
        osr = cast(OSStatusResponse, result)
        self.assertEqual(osr.progress, 75)
        self.assertEqual(osr.status, "updating")

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
        upd = cast(UpdateCheckResponse, result)
        self.assertTrue(upd.available)
        self.assertEqual(upd.version, "1.3.0")

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
        upds = cast(UpdateStatus, result)
        self.assertEqual(upds.status, "rebooting")


class TestTimezoneManagement(unittest.TestCase):
    """Test timezone configuration endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_timezone_region(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_REGIONS_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_timezone_region("countries", "North America")
        self.assertIsInstance(result, Regions)
        regions = cast(Regions, result)
        self.assertIsNotNone(regions.countries)
        countries = cast(List[str], regions.countries)
        self.assertEqual(len(countries), 3)
        self.assertIn("US", countries)

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
        regions = cast(Regions, result)
        self.assertIsNotNone(regions.countries)

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
        tz = cast(TimezoneResponse, result)
        self.assertEqual(tz.timezone, "America/New_York")

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
        tz = cast(TimezoneResponse, result)
        self.assertEqual(tz.timezone, "America/Los_Angeles")


class TestWiFiManagement(unittest.TestCase):
    """Test WiFi configuration and monitoring endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

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
        qr = cast(WiFiQRData, result)
        self.assertEqual(qr.ssid, "MyNetwork")
        self.assertEqual(qr.encryption, "WPA2")


class TestLogManagement(unittest.TestCase):
    """Test log retrieval and management endpoints."""

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
        logs = cast(List[LogFile], result)
        self.assertEqual(len(logs), 2)
        self.assertIsInstance(logs[0], LogFile)
        self.assertEqual(logs[0].name, "system.log")

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
    """Test error handling across all REST endpoints."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_wifi_status_not_available(self, mock_get: Mock) -> None:
        """Test WiFi config when WiFi is not available."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "WiFi not available"}
        mock_get.return_value = mock_response

        result = self.api.get_wifi_config()

        self.assertIsInstance(result, APIError)
        err = cast(APIError, result)
        self.assertEqual(err.error, "WiFi not available")

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
        err = cast(APIError, result)
        self.assertEqual(err.error, "Invalid profile file")


if __name__ == "__main__":
    unittest.main()
