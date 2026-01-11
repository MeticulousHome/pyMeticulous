"""Integration tests for REST API endpoints.

These tests require a real meticulous machine to be available.
Set METICULOUS_HOST environment variable to specify the machine address.

Run integration tests:
    pytest -m integration

Skip integration tests:
    pytest -m "not integration"
"""

import pytest
import unittest
from typing import Optional

from meticulous.api import Api
from meticulous.api_types import (
    APIError,
    DeviceInfo,
    DefaultProfiles,
    HistoryListingResponse,
    HistoryStats,
    OSStatusResponse,
    Settings,
    ShotRatingResponse,
)
from tests.integration.utils import get_base_url, server_reachable


@pytest.mark.integration
class TestApiEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.base_url = get_base_url()
        self.api = Api(base_url=self.base_url)

    def _assert_ok(self, result: object, expected_type: type) -> None:
        self.assertIsInstance(
            result,
            expected_type,
            msg=f"Expected {expected_type}, got {type(result)}: {result}",
        )

    def _skip_if_unreachable(self) -> Optional[bool]:
        if not server_reachable(self.base_url):
            self.skipTest(f"Server not reachable at {self.base_url}")
            return True
        return None

    def test_device_info(self) -> None:
        if self._skip_if_unreachable():
            return
        result = self.api.get_device_info()
        self._assert_ok(result, DeviceInfo)

    def test_settings(self) -> None:
        if self._skip_if_unreachable():
            return
        result = self.api.get_settings()
        self._assert_ok(result, Settings)

    def test_sounds(self) -> None:
        if self._skip_if_unreachable():
            return
        result = self.api.list_sounds()
        self.assertFalse(isinstance(result, APIError))
        result = self.api.list_sound_themes()
        self.assertFalse(isinstance(result, APIError))
        result = self.api.get_sound_theme()
        self.assertFalse(isinstance(result, APIError))

    def test_wifi(self) -> None:
        if self._skip_if_unreachable():
            return
        result = self.api.get_wifi_config()
        self.assertFalse(isinstance(result, APIError))
        # Test WiFi status endpoint
        status = self.api.get_wifi_status()
        if isinstance(status, APIError):
            self.skipTest("WiFi status endpoint not available")
        # QR endpoint returns bytes; validate quickly
        qr = self.api.get_wifi_qr()
        if not isinstance(qr, APIError):
            self.assertTrue(isinstance(qr, (bytes, bytearray)))
        # Test WiFi QR data endpoint
        qr_data = self.api.get_wifi_qr_data()
        if isinstance(qr_data, APIError):
            self.skipTest("WiFi QR data endpoint not available")

    def test_profiles(self) -> None:
        if self._skip_if_unreachable():
            return
        partial = self.api.list_profiles()
        self.assertFalse(isinstance(partial, APIError))
        full = self.api.fetch_all_profiles()
        self.assertFalse(isinstance(full, APIError))
        defaults = self.api.get_default_profiles()
        self.assertTrue(isinstance(defaults, (list, DefaultProfiles)))

    def test_history(self) -> None:
        if self._skip_if_unreachable():
            return
        # Short listing
        listing = self.api.get_history_short_listing()
        if not isinstance(listing, APIError):
            self._assert_ok(listing, HistoryListingResponse)

        # Statistics
        stats = self.api.get_history_statistics()
        if not isinstance(stats, APIError):
            self._assert_ok(stats, HistoryStats)

        # Rating endpoint shape
        rating = self.api.get_shot_rating(1)
        self.assertTrue(isinstance(rating, (ShotRatingResponse, APIError)))

        # OS status
        status = self.api.get_os_status()
        if not isinstance(status, APIError):
            self._assert_ok(status, OSStatusResponse)

        # Machine state
        state = self.api.get_machine_state()
        if not isinstance(state, APIError):
            from meticulous.api_types import MachineState

            self._assert_ok(state, MachineState)

    def test_timezone_endpoints(self) -> None:
        """Test timezone read operations (safe)."""
        if self._skip_if_unreachable():
            return
        from meticulous.api_types import TimezoneResponse, Regions, APIError

        # Get current timezone
        current_tz = self.api.get_timezone()
        if not isinstance(current_tz, APIError):
            self._assert_ok(current_tz, TimezoneResponse)
            print(f"Current timezone: {current_tz.timezone}")

        # Get timezone regions (countries)
        regions = self.api.get_timezones()
        if not isinstance(regions, APIError):
            self._assert_ok(regions, Regions)

    def test_profile_changes(self) -> None:
        """Test profile change history (safe read-only)."""
        if self._skip_if_unreachable():
            return
        # APIError imported at top; ProfileChange import not needed

        changes = self.api.get_profile_changes()
        if isinstance(changes, APIError):
            # Endpoint might not exist on all firmware versions
            self.skipTest("Profile changes endpoint not available")
        self.assertIsInstance(changes, list)
        print(f"Profile changes: {len(changes)} entries")

    def test_logs_endpoints(self) -> None:
        """Test log retrieval (safe read-only)."""
        if self._skip_if_unreachable():
            return
        from meticulous.api_types import LogFile, APIError

        # List available logs
        logs = self.api.list_logs()
        if isinstance(logs, APIError):
            self.skipTest("Logs endpoint not available")
        self.assertIsInstance(logs, list)
        if logs:
            self.assertIsInstance(logs[0], LogFile)
            print(f"Available logs: {len(logs)}")

        # Get debug log
        debug_log = self.api.get_debug_log()
        if not isinstance(debug_log, APIError):
            self.assertIsInstance(debug_log, str)
            print(f"Debug log size: {len(debug_log)} chars")

    def test_update_check(self) -> None:
        """Test update check (safe read-only, doesn't install)."""
        if self._skip_if_unreachable():
            return
        from meticulous.api_types import UpdateCheckResponse, APIError

        result = self.api.check_for_updates()
        if isinstance(result, APIError):
            self.skipTest("Update check endpoint not available")
        self._assert_ok(result, UpdateCheckResponse)
        print(f"Updates available: {result.available}")


if __name__ == "__main__":
    unittest.main()
