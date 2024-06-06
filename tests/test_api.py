import unittest
from unittest.mock import Mock, patch

from requests.models import Response

from meticulous import Api, APIError
from .mock_responses import MOCK_PROFILE_LIST_RESPONSE


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


if __name__ == "__main__":
    unittest.main()
