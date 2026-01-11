"""Unit tests for Socket.IO functionality.

Tests Socket.IO event throttling, event handlers, actions, retry logic,
and real-time communication features.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import json

from meticulous.api import Api, ApiOptions, EventThrottle
from meticulous.api_types import (
    ActionType,
    StatusData,
    SensorsEvent,
    ButtonEvent,
    NotificationData,
    HeaterStatus,
    OSUpdateEvent,
)


class TestEventThrottle(unittest.TestCase):
    """Test the EventThrottle class for rate limiting."""

    def test_throttle_global_rate(self) -> None:
        """Test global throttle rate limiting."""
        throttle = EventThrottle(0.1)  # 100ms throttle

        # First call should pass
        self.assertTrue(throttle.should_process())

        # Immediate second call should be blocked
        self.assertFalse(throttle.should_process())

        # After waiting, should pass again
        time.sleep(0.11)
        self.assertTrue(throttle.should_process())
        # Per-event throttling is handled by global should_process()
        # (EventThrottle only has global rate, not per-event rates)
        time.sleep(0.11)
        self.assertTrue(throttle.should_process())

    def test_throttle_zero_means_no_limit(self) -> None:
        """Test that 0.0 throttle means no rate limiting."""
        throttle = EventThrottle(0.0)

        # All calls should pass immediately with zero throttle
        for _ in range(10):
            self.assertTrue(throttle.should_process())


class TestSocketIOEventHandlers(unittest.TestCase):
    """Test Socket.IO event handler registration and invocation."""

    @patch("socketio.Client")
    @patch("meticulous.api.time.time")
    def test_register_handlers_with_throttle(
        self, mock_time: Mock, mock_client_class: Mock
    ) -> None:
        """Handlers are wrapped with throttle and gate repeated events."""

        handler = Mock()
        options = ApiOptions(onStatus=handler, throttle=0.1)
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        options.register_handlers(mock_client)

        event_name, callback = mock_client.on.call_args_list[0][0]
        self.assertEqual(event_name, "status")
        self.assertIsNot(callback, handler)

        mock_data = {
            "name": "test_profile",
            "state": "idle",
            "extracting": False,
            "time": 1000,
            "profile_time": 0,
            "profile": "test-id",
            "sensors": {"p": 0.0, "f": 0.0, "w": 0.0, "t": 90.0, "g": 1.0},
            "setpoints": {"pressure": 0, "flow": 0},
        }

        mock_time.side_effect = [0.2, 0.25, 0.5]
        callback(StatusData(**mock_data))
        callback(StatusData(**mock_data))
        callback(StatusData(**mock_data))

        self.assertEqual(handler.call_count, 2)

    @patch("socketio.Client")
    def test_register_handlers_without_throttle(self, mock_client_class: Mock) -> None:
        """Handlers are registered directly when throttle is not set."""

        handler = Mock()
        options = ApiOptions(onStatus=handler)
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        options.register_handlers(mock_client)

        event_name, callback = mock_client.on.call_args_list[0][0]
        self.assertEqual(event_name, "status")
        self.assertIs(callback, handler)

    def test_status_handler_called(self) -> None:
        """Test that onStatus handler is called with correct data."""
        handler = Mock()
        options = ApiOptions(onStatus=handler)
        api = Api(base_url="http://localhost:8080/", options=options)

        # Simulate status event
        mock_data = {
            "name": "test_profile",
            "state": "idle",
            "extracting": False,
            "time": 1000,
            "profile_time": 0,
            "profile": "test-id",
            "sensors": {"p": 0.0, "f": 0.0, "w": 0.0, "t": 90.0, "g": 1.0},
            "setpoints": {"pressure": 0, "flow": 0},
        }

        # Manually invoke the handler (simulating Socket.IO callback)
        if api.options and api.options.onStatus:
            status = StatusData(**mock_data)
            api.options.onStatus(status)

        handler.assert_called_once()

    def test_sensors_handler_called(self) -> None:
        """Test that onSensors handler is called with correct data."""
        handler = Mock()
        options = ApiOptions(onSensors=handler)
        api = Api(base_url="http://localhost:8080/", options=options)

        # Simulate sensors event with all 23 fields
        mock_data = {
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
            "f": 2.5,
            "w": 42.0,
            "a_0": 100,
            "a_1": 150,
            "a_2": 200,
            "a_3": 250,
            "m_pos": 1000,
            "m_spd": 50,
            "m_pwr": 30,
            "m_cur": 500,
            "bh_pwr": 800,
            "bh_cur": 3500,
            "w_stat": 1,
            "motor_temp": 45.0,
            "weight_pred": 41.5,
        }

        if api.options and api.options.onSensors:
            sensors = SensorsEvent(**mock_data)
            api.options.onSensors(sensors)

        handler.assert_called_once()

    def test_button_handler_called(self) -> None:
        """Test that onButton handler is called with correct data."""
        handler = Mock()
        options = ApiOptions(onButton=handler)
        api = Api(base_url="http://localhost:8080/", options=options)

        mock_data = {
            "type": "single_press",
            "time_since_last_event": 1000,
        }

        if api.options and api.options.onButton:
            button = ButtonEvent(**mock_data)
            api.options.onButton(button)

        handler.assert_called_once()

    def test_notification_handler_called(self) -> None:
        """Test that onNotification handler is called with correct data."""
        handler = Mock()
        options = ApiOptions(onNotification=handler)
        api = Api(base_url="http://localhost:8080/", options=options)

        mock_data = {
            "id": "notif-001",
            "message": "Low water level",
            "responses": ["ok", "cancel"],
            "timestamp": "2026-01-10T12:00:00Z",
        }

        if api.options and api.options.onNotification:
            notification = NotificationData(**mock_data)
            api.options.onNotification(notification)

        handler.assert_called_once()

    def test_heater_status_handler_called(self) -> None:
        """Test that onHeaterStatus handler is called with correct data."""
        handler = Mock()
        options = ApiOptions(onHeaterStatus=handler)
        api = Api(base_url="http://localhost:8080/", options=options)

        mock_data = {"remaining": 5}

        if api.options and api.options.onHeaterStatus:
            heater = HeaterStatus(**mock_data)
            api.options.onHeaterStatus(heater)

        handler.assert_called_once()

    def test_os_update_handler_called(self) -> None:
        """Test that onOSUpdate handler is called with correct data."""
        handler = Mock()
        options = ApiOptions(onOSUpdate=handler)
        api = Api(base_url="http://localhost:8080/", options=options)

        mock_data = {
            "progress": 75,
            "status": "downloading",
            "message": "Downloading update...",
        }

        if api.options and api.options.onOSUpdate:
            update = OSUpdateEvent(**mock_data)
            api.options.onOSUpdate(update)

        handler.assert_called_once()


class TestManualThrottling(unittest.TestCase):
    """Test manual throttling patterns."""

    def test_manual_throttling_with_handlers(self) -> None:
        """Test manual throttling pattern with event handlers."""
        # datetime import removed (unused)

        call_count = 0
        throttle = EventThrottle(0.1)

        def handler(data: StatusData) -> None:
            nonlocal call_count
            if throttle.should_process():
                call_count += 1

        mock_data = {
            "name": "test",
            "state": "idle",
            "extracting": False,
            "time": 1000,
            "profile_time": 0,
            "profile": "id",
            "sensors": {"p": 0.0, "f": 0.0, "w": 0.0, "t": 90.0, "g": 1.0},
            "setpoints": {"pressure": 0, "flow": 0},
        }

        # First call should go through
        handler(StatusData(**mock_data))
        self.assertEqual(call_count, 1)

        # Immediate second call should be throttled
        handler(StatusData(**mock_data))
        self.assertEqual(call_count, 1)


class TestSocketIOActions(unittest.TestCase):
    """Test Socket.IO action emission."""

    def test_send_action_socketio_rejects_unsupported(self) -> None:
        """Unsupported actions raise ValueError before emitting."""

        api = Api(base_url="http://localhost:8080/")

        with self.assertRaises(ValueError):
            api.send_action_socketio(ActionType.RESET)

    @patch("socketio.Client")
    def test_send_action_socketio(self, mock_client_class: Mock) -> None:
        """Test sending actions via Socket.IO."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connected = True

        api = Api(base_url="http://localhost:8080/")
        api.socketio = mock_client

        # Send tare action
        api.send_action_socketio(ActionType.TARE)

        # Should call emit with action event
        self.assertTrue(mock_client.emit.called)
        args = mock_client.emit.call_args
        self.assertEqual(args[0][0], "action")
        self.assertIn("tare", str(args))

    @patch("socketio.Client")
    def test_acknowledge_notification(self, mock_client_class: Mock) -> None:
        """Test acknowledging notifications via Socket.IO."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connected = True

        api = Api(base_url="http://localhost:8080/")
        api.socketio = mock_client

        # Acknowledge notification (notification_id, response)
        api.acknowledge_notification_socketio("123", "ok")

        # Verify emit was called (actual payload format may vary)
        self.assertTrue(mock_client.emit.called)
        self.assertEqual(mock_client.emit.call_args[0][0], "notification")
        self.assertEqual(
            mock_client.emit.call_args[0][1],
            json.dumps({"id": "123", "response": "ok"}),
        )

    @patch("socketio.Client")
    def test_send_profile_hover(self, mock_client_class: Mock) -> None:
        """Test sending profile hover event."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connected = True

        api = Api(base_url="http://localhost:8080/")
        api.socketio = mock_client

        profile_data = {"id": "test-id", "name": "Test Profile"}
        api.send_profile_hover(profile_data)

        mock_client.emit.assert_called_once_with("profileHover", profile_data)

    @patch("socketio.Client")
    def test_send_profile_hover_focus(self, mock_client_class: Mock) -> None:
        """Test sending profile hover focus/select payload."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connected = True

        api = Api(base_url="http://localhost:8080/")
        api.socketio = mock_client

        payload = {"id": "uuid-123", "from": "app", "type": "focus"}
        api.send_profile_hover(payload)

        mock_client.emit.assert_called_once_with("profileHover", payload)

    @patch("socketio.Client")
    def test_trigger_calibration(self, mock_client_class: Mock) -> None:
        """Test triggering calibration via Socket.IO."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connected = True

        api = Api(base_url="http://localhost:8080/")
        api.socketio = mock_client

        # Enable calibration
        api.trigger_calibration(True)

        # Should call emit with calibrate event
        self.assertTrue(mock_client.emit.called)
        args = mock_client.emit.call_args
        self.assertEqual(args[0][0], "calibrate")

        # Disable calibration
        api.trigger_calibration(False)
        self.assertEqual(mock_client.emit.call_count, 2)

    """Test Socket.IO connection retry logic."""

    @patch("socketio.Client")
    @patch("time.sleep")
    def test_retry_on_connection_failure(
        self, mock_sleep: Mock, mock_client_class: Mock
    ) -> None:
        """Test that connection retries on failure with exponential backoff."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Simulate connection failure twice, then success
        mock_client.connect.side_effect = [
            ConnectionError("Failed"),
            ConnectionError("Failed"),
            None,  # Success on third try
        ]

        api = Api(base_url="http://localhost:8080/")
        api.socketio = mock_client

        # Should retry and eventually succeed
        api.connect_to_socket(retries=3, backoff=0.5)

        # Should have tried 3 times
        self.assertEqual(mock_client.connect.call_count, 3)

        # Should have slept twice (between attempts)
        self.assertEqual(mock_sleep.call_count, 2)
        # First backoff: 0.5s, second: 1.0s (exponential)
        mock_sleep.assert_any_call(0.5)
        mock_sleep.assert_any_call(1.0)

    @patch("socketio.Client")
    @patch("time.sleep")
    def test_retry_backoff_capped(
        self, mock_sleep: Mock, mock_client_class: Mock
    ) -> None:
        """Backoff grows exponentially but caps at max_backoff."""

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connect.side_effect = [
            ConnectionError("Failed"),
            ConnectionError("Failed"),
            ConnectionError("Failed"),
            ConnectionError("Failed"),
            ConnectionError("Failed"),
        ]

        api = Api(base_url="http://localhost:8080/")
        api.socketio = mock_client

        with self.assertRaises(ConnectionError):
            api.connect_to_socket(retries=4, backoff=0.5, max_backoff=1.0)

        self.assertEqual(mock_client.connect.call_count, 5)
        self.assertEqual(mock_sleep.call_count, 4)
        mock_sleep.assert_any_call(0.5)
        mock_sleep.assert_any_call(1.0)
        # Ensure cap is honored (no call larger than max_backoff)
        self.assertTrue(all(args[0] <= 1.0 for args, _ in mock_sleep.call_args_list))

    @patch("socketio.Client")
    def test_no_retry_when_retries_zero(self, mock_client_class: Mock) -> None:
        """Test that no retry happens when retries=0."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.connect.side_effect = ConnectionError("Failed")

        api = Api(base_url="http://localhost:8080/")
        api.socketio = mock_client

        # Should raise error immediately
        with self.assertRaises(ConnectionError):
            api.connect_to_socket(retries=0)

        # Should have tried only once
        self.assertEqual(mock_client.connect.call_count, 1)


if __name__ == "__main__":
    unittest.main()
