import unittest
from typing import Optional

from meticulous.api import Api
from meticulous.api_types import (
    APIError,
    DeviceInfo,
    DefaultProfiles,
    HistoryListingResponse,
    HistoryResponse,
    HistoryStats,
    OSStatusResponse,
    Settings,
    ShotRatingResponse,
    WiFiConfig,
)
from tests.smoke.utils import get_base_url, server_reachable


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
        # QR endpoint returns bytes; validate quickly
        qr = self.api.get_wifi_qr()
        if not isinstance(qr, APIError):
            self.assertTrue(isinstance(qr, (bytes, bytearray)))

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
        listing = self.api.get_history_short_listing()
        self._assert_ok(listing, HistoryListingResponse)

        stats = self.api.get_history_statistics()
        self._assert_ok(stats, HistoryStats)

        # Optional rating read: may not exist for arbitrary ids
        # This ensures URL shape is valid without destructive calls
        # If server returns APIError, it's acceptable.
        rating = self.api.get_shot_rating(1)
        self.assertTrue(isinstance(rating, (ShotRatingResponse, APIError)))

    def test_os_status(self) -> None:
        if self._skip_if_unreachable():
            return
        status = self.api.get_os_status()
        self._assert_ok(status, OSStatusResponse)


if __name__ == "__main__":
    unittest.main()
