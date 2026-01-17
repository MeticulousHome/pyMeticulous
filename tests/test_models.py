"""Unit tests for API type models and validation.

# pyright: reportGeneralTypeIssues=false

Tests all Pydantic models, enums, and validation logic used throughout the API.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from pydantic import ValidationError
from requests.models import Response

from meticulous.api import Api
from meticulous.profile import Profile
from meticulous.api_types import (
    ActionType,
    StatusData,
    SensorsEvent,
    MachineState,
    TimezoneResponse,
    ProfileImportResponse,
    ProfileChange,
    WiFiQRData,
    LogFile,
    HeaterStatus,
    OSUpdateEvent,
    ButtonEvent,
    NotificationData,
    WiFiConfig,
)
from meticulous.api_types import APIError
from tests.mock_responses import MOCK_PROFILE_RESPONSE


class TestActionType(unittest.TestCase):
    """Test ActionType enum."""

    def test_all_action_types(self) -> None:
        """Test that all action types are valid."""
        expected_actions = [
            "start",
            "stop",
            "tare",
            "preheat",
            "abort",
            "home",
            "purge",
        ]
        for action in expected_actions:
            ActionType(action)  # Should not raise

    def test_invalid_action_type(self) -> None:
        """Test that invalid action types raise error."""
        with self.assertRaises(ValueError):
            ActionType("calibration")  # Removed from enum

    def test_action_type_values(self) -> None:
        """Test that action types have correct values."""
        self.assertEqual(ActionType.TARE.value, "tare")
        self.assertEqual(ActionType.PREHEAT.value, "preheat")


class TestSensorsEvent(unittest.TestCase):
    """Test SensorsEvent model."""

    def test_sensors_event_all_fields(self) -> None:
        """Test that SensorsEvent includes all required fields."""
        data = {
            "t_ext_1": 90.0,
            "t_ext_2": 90.5,
            "t_bar_up": 88.0,
            "t_bar_mu": 87.5,
            "t_bar_md": 87.0,
            "t_bar_down": 86.5,
            "t_tube": 85.0,
            "t_motor_temp": 45.0,
            "lam_temp": 88.5,
            "p": 9.0,
            "a_0": 100.0,
            "a_1": 150.0,
            "a_2": 200.0,
            "a_3": 250.0,
            "m_pos": 1000.0,
            "m_spd": 50.0,
            "m_pwr": 30.0,
            "m_cur": 500.0,
            "bh_pwr": 800.0,
            "bh_cur": 3500.0,
            "w_stat": True,
            "motor_temp": 45.0,
            "weight_pred": 41.5,
        }
        sensors = SensorsEvent(**data)
        self.assertEqual(sensors.p, 9.0)
        self.assertEqual(sensors.motor_temp, 45.0)


class TestStatusData(unittest.TestCase):
    """Test StatusData model."""

    def test_status_data_complete(self) -> None:
        """Test StatusData with complete data."""
        data = {
            "name": "test_profile",
            "sensors": {"p": 9.0, "f": 2.5, "w": 42.0, "t": 93.0, "g": 1.0},
            "time": 15000,
            "profile_time": 12000,
            "profile": "test-id",
            "state": "extracting",
            "extracting": True,
            "setpoints": {"pressure": 9.0, "flow": 2.5},
        }
        status = StatusData(**data)
        self.assertEqual(status.state, "extracting")
        self.assertTrue(status.extracting)


class TestMachineStateModels(unittest.TestCase):
    """Test machine state and update models."""

    def test_machine_state(self) -> None:
        state = MachineState(state="idle", status="ready", extracting=False)
        self.assertEqual(state.state, "idle")

    def test_heater_status(self) -> None:
        heater = HeaterStatus(remaining=5)
        self.assertEqual(heater.remaining, 5)

    def test_os_update_event(self) -> None:
        update = OSUpdateEvent(progress=75, status="downloading")
        self.assertEqual(update.progress, 75)


class TestTimezoneModels(unittest.TestCase):
    """Test timezone models."""

    def test_timezone_response(self) -> None:
        tz = TimezoneResponse(timezone="America/New_York")
        self.assertEqual(tz.timezone, "America/New_York")


class TestProfileModels(unittest.TestCase):
    """Test profile-related models."""

    def test_profile_import_response(self) -> None:
        result = ProfileImportResponse(imported=3)
        self.assertEqual(result.imported, 3)

    def test_profile_change(self) -> None:
        change = ProfileChange(type="modified", profile_id="id", change_id="c1")
        self.assertEqual(change.type, "modified")


class TestWiFiModels(unittest.TestCase):
    """Test WiFi models."""

    def test_wifi_config(self) -> None:
        config = WiFiConfig(mode="client", apName="AP", apPassword="pass")
        self.assertEqual(config.mode, "client")

    def test_wifi_qr_data(self) -> None:
        qr = WiFiQRData(ssid="Net", password="pass", encryption="WPA2")
        self.assertEqual(qr.ssid, "Net")


class TestLogModels(unittest.TestCase):
    """Test log models."""

    def test_log_file(self) -> None:
        log = LogFile(name="system.log")
        self.assertEqual(log.name, "system.log")


class TestEventModels(unittest.TestCase):
    """Test event models."""

    def test_button_event(self) -> None:
        event = ButtonEvent(type="single_press", time_since_last_event=1000)
        self.assertEqual(event.type, "single_press")

    def test_notification_data(self) -> None:
        notif = NotificationData(
            id="n1", message="Test", responses=["ok"], timestamp=datetime.now()
        )
        self.assertEqual(notif.id, "n1")


class TestModelValidation(unittest.TestCase):
    """Test model validation."""

    def test_status_data_missing_required(self) -> None:
        with self.assertRaises(ValidationError):
            StatusData(state="idle", extracting=False)


class TestProfile(unittest.TestCase):
    """Test Profile model validation and parsing."""

    def setUp(self) -> None:
        self.api = Api(base_url="http://localhost:8080/")

    @patch("requests.Session.get")
    def test_get_profile(self, mock_get: Mock) -> None:
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_PROFILE_RESPONSE
        mock_get.return_value = mock_response

        profile_id = "05051ed3-9996-43e8-9da6-963f2b31d481"
        result = self.api.get_profile(profile_id)
        self.assertFalse(isinstance(result, APIError))
        profile: Profile = result  # type: ignore[assignment]

        self.assertEqual(profile.name, "Italian limbus")
        self.assertEqual(profile.id, "05051ed3-9996-43e8-9da6-963f2b31d481")
        self.assertEqual(profile.author, "meticulous")
        self.assertEqual(profile.author_id, "d9123a0a-d3d7-40fd-a548-b81376e43f23")
        self.assertIsNotNone(profile.previous_authors)
        authors = profile.previous_authors or []
        self.assertEqual(len(authors), 2)
        self.assertEqual(authors[0].name, "mimoja")
        self.assertEqual(
            authors[1].author_id,
            "ee86a777-fdd6-46d6-8cf7-099a9fb609a1",
        )
        self.assertEqual(profile.temperature, 90.5)
        self.assertEqual(profile.final_weight, 40)
        variables = profile.variables or []
        self.assertEqual(len(variables), 1)
        self.assertEqual(variables[0].name, "Pressure")
        self.assertEqual(variables[0].key, "pressure_1")
        self.assertEqual(variables[0].value, "$pressure_var")
        self.assertEqual(len(profile.stages), 2)
        self.assertEqual(profile.stages[0].name, "Preinfusion")
        self.assertEqual(
            profile.stages[0].dynamics.points,
            [[0, "${flow_start}"], [5, "$flow_mid"]],
        )
        self.assertEqual(profile.stages[0].exit_triggers[0].type, "time")
        self.assertEqual(profile.stages[0].exit_triggers[0].value, "${time_exit}")
        limits = profile.stages[1].limits or []
        self.assertEqual(limits[0].type, "flow")
        self.assertEqual(limits[0].value, "$flow_limit")
        if profile.display is not None:
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
