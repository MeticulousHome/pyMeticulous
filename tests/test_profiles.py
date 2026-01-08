import unittest
from unittest.mock import Mock, patch

from requests.models import Response

from meticulous.api import Api
from meticulous.profile import Profile
from tests.mock_responses import MOCK_PROFILE_RESPONSE


class TestProfile(unittest.TestCase):
    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_profile(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_PROFILE_RESPONSE
        mock_get.return_value = mock_response

        profile_id = "05051ed3-9996-43e8-9da6-963f2b31d481"
        profile: Profile = self.api.get_profile(profile_id)

        self.assertEqual(profile.name, "Italian limbus")
        self.assertEqual(profile.id, "05051ed3-9996-43e8-9da6-963f2b31d481")
        self.assertEqual(profile.author, "meticulous")
        self.assertEqual(profile.author_id, "d9123a0a-d3d7-40fd-a548-b81376e43f23")
        self.assertEqual(len(profile.previous_authors), 2)
        self.assertEqual(profile.previous_authors[0].name, "mimoja")
        self.assertEqual(
            profile.previous_authors[1].author_id,
            "ee86a777-fdd6-46d6-8cf7-099a9fb609a1",
        )
        self.assertEqual(profile.temperature, 90.5)
        self.assertEqual(profile.final_weight, 40)
        self.assertEqual(len(profile.variables), 1)
        self.assertEqual(profile.variables[0].name, "Pressure")
        self.assertEqual(profile.variables[0].key, "pressure_1")
        self.assertEqual(profile.variables[0].value, "$pressure_var")
        self.assertEqual(len(profile.stages), 2)
        self.assertEqual(profile.stages[0].name, "Preinfusion")
        self.assertEqual(
            profile.stages[0].dynamics.points,
            [[0, "${flow_start}"], [5, "$flow_mid"]],
        )
        self.assertEqual(profile.stages[0].exit_triggers[0].type, "time")
        self.assertEqual(profile.stages[0].exit_triggers[0].value, "${time_exit}")
        self.assertEqual(profile.stages[1].limits[0].type, "flow")
        self.assertEqual(profile.stages[1].limits[0].value, "$flow_limit")
        self.assertEqual(
            profile.display.image,
            "/api/v1/profile/image/ed03e12bb34fc419c5adfd7d993b50e7.png",
        )
        self.assertEqual(profile.last_changed, 1716585650.3912911)

    @patch("requests.Session.get")
    def test_get_profile_invalid_json(self, mock_get: Mock) -> None:
        # Set up the mock to return invalid JSON
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        profile_id = "05051ed3-9996-43e8-9da6-963f2b31d481"
        with self.assertRaises(ValueError) as context:
            self.api.get_profile(profile_id)

        self.assertTrue("Invalid JSON" in str(context.exception))

    @patch("requests.Session.get")
    def test_get_profile_invalid_format(self, mock_get: Mock) -> None:
        # Set up the mock to return JSON not adhering to the format
        invalid_profile_response = {
            "name": "Invalid Profile",
            "id": 12345,  # ID should be a string (UUID format)
            "author": "author_name",
            # Missing required fields such as author_id, temperature, final_weight, stages
        }
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = invalid_profile_response
        mock_get.return_value = mock_response

        profile_id = "invalid-profile-id"
        with self.assertRaises(Exception) as context:
            self.api.get_profile(profile_id)

        self.assertTrue("validation error" in str(context.exception).lower())


if __name__ == "__main__":
    unittest.main()
