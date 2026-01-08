import json
import unittest
from unittest.mock import Mock, patch

from requests.models import Response

from meticulous import Api, APIError
from meticulous.api_types import (
    BrightnessRequest,
    DeviceInfo,
    HistoryListingResponse,
    HistoryStats,
    HistoryQueryParams,
    OSStatusResponse,
    ShotRatingResponse,
    RateShotResponse,
    DefaultProfiles,
    Regions,
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


class TestApi(unittest.TestCase):
    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_list_profiles(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_PROFILE_LIST_RESPONSE
        mock_get.return_value = mock_response
        profiles = self.api.list_profiles()

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
        self.assertEqual(result.error, "Profile not found")

    @patch("requests.Session.get")
    def test_get_device_info(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_DEVICE_INFO_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_device_info()

        self.assertIsInstance(result, DeviceInfo)
        self.assertEqual(result.name, "meticulous")
        self.assertEqual(result.serial, "MT12345678")
        self.assertEqual(result.mainVoltage, 230.5)
        self.assertEqual(len(result.version_history), 4)

    @patch("requests.Session.post")
    def test_set_brightness(self, mock_post: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        brightness_req = BrightnessRequest(brightness=80, interpolation="curve")
        result = self.api.set_brightness(brightness_req)

        self.assertIsNone(result)
        mock_post.assert_called_once()

    @patch("requests.Session.get")
    def test_get_history_short_listing(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_HISTORY_LISTING_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_history_short_listing()

        self.assertIsInstance(result, HistoryListingResponse)
        self.assertEqual(len(result.history), 1)
        self.assertEqual(result.history[0].name, "Morning espresso")
        self.assertEqual(result.history[0].rating, "like")

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
        self.assertEqual(result.totalSavedShots, 150)
        self.assertEqual(len(result.byProfile), 3)
        self.assertEqual(result.byProfile[0].name, "Italian limbus")
        self.assertEqual(result.byProfile[0].count, 75)

    @patch("requests.Session.get")
    def test_get_settings(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SETTINGS_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_settings()

        self.assertIsNotNone(result)
        self.assertEqual(result.auto_preheat, 5)
        self.assertTrue(result.enable_sounds)
        self.assertEqual(result.update_channel, "stable")

    @patch("requests.Session.get")
    def test_get_default_profiles(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_DEFAULT_PROFILES_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_default_profiles()

        self.assertIsInstance(result, DefaultProfiles)
        self.assertEqual(len(result.default), 1)
        self.assertEqual(len(result.community), 1)

    @patch("requests.Session.post")
    def test_rate_shot(self, mock_post: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_RATE_SHOT_RESPONSE
        mock_post.return_value = mock_response

        result = self.api.rate_shot(1, "like")

        self.assertIsInstance(result, RateShotResponse)
        self.assertEqual(result.shot_id, 1)
        self.assertEqual(result.rating, "like")
        self.assertEqual(result.status, "success")

    @patch("requests.Session.get")
    def test_get_shot_rating(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SHOT_RATING_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_shot_rating(1)

        self.assertIsInstance(result, ShotRatingResponse)
        self.assertEqual(result.shot_id, 1)
        self.assertEqual(result.rating, "like")

    @patch("requests.Session.get")
    def test_get_os_status(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_OS_STATUS_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_os_status()

        self.assertIsInstance(result, OSStatusResponse)
        self.assertEqual(result.progress, 75)
        self.assertEqual(result.status, "updating")

    @patch("requests.Session.get")
    def test_get_timezone_region(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_REGIONS_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_timezone_region("countries", "North America")

        self.assertIsInstance(result, Regions)
        self.assertEqual(len(result.countries), 3)
        self.assertIn("US", result.countries)

    @patch("requests.Session.get")
    def test_get_current_shot_none(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = None
        mock_get.return_value = mock_response

        result = self.api.get_current_shot()

        self.assertIsNone(result)

    @patch("requests.Session.get")
    def test_get_history_dates(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_HISTORY_DATES_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_history_dates()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "2024-01-02")
        self.assertEqual(result[0].url, "2024-01-02")

    @patch("requests.Session.get")
    def test_get_shot_files(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SHOT_FILES_RESPONSE
        mock_get.return_value = mock_response

        result = self.api.get_shot_files("2024-01-02")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].url, "21:04:06.shot.json")

    @patch("requests.Session.get")
    def test_get_shot_log_plain_json(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_SHOT_LOG_RESPONSE).encode()
        mock_get.return_value = mock_response

        result = self.api.get_shot_log("2024-01-02", "21:04:06.shot.json")

        self.assertEqual(result["shot"], "latest")
        self.assertEqual(result["value"], 1)

    @patch("requests.Session.get")
    def test_get_shot_log_zst(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = MOCK_SHOT_LOG_ZST
        mock_get.return_value = mock_response

        result = self.api.get_shot_log("2024-01-02", "20:55:00.shot.json.zst")

        self.assertEqual(result["shot"], "latest")

    @patch("requests.Session.get")
    def test_get_shot_log_error(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "not found", "status": "404"}
        mock_get.return_value = mock_response

        result = self.api.get_shot_log("2024-01-02", "missing.shot.json")

        self.assertIsInstance(result, APIError)
        self.assertEqual(result.error, "not found")

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

        self.assertEqual(result["shot"], "latest")


if __name__ == "__main__":
    unittest.main()
