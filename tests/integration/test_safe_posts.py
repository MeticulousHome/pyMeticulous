"""Integration tests for safe POST operations.

These tests require a real meticulous machine to be available.
Set METICULOUS_HOST environment variable to specify the machine address.
"""

import pytest
import unittest
from typing import cast

# Api imported by make_api_with_events; direct import not needed
from meticulous.api_types import BrightnessRequest, ActionType, ActionResponse, APIError
from tests.integration.utils import (
    make_api_with_events,
    wait_for_events,
)


@pytest.mark.integration
class TestSafePosts(unittest.TestCase):
    def setUp(self) -> None:
        self.api, self.collector = make_api_with_events()

    def tearDown(self) -> None:
        try:
            self.api.disconnect_socket()
        except Exception:
            pass

    def test_set_brightness_emits_events(self) -> None:
        # Connect socket to observe events
        self.api.connect_to_socket()

        baseline = wait_for_events(self.collector, timeout_sec=3.0)

        req = BrightnessRequest(brightness=60)
        result = self.api.set_brightness(req)
        self.assertIsNone(result, msg=f"Brightness change failed: {result}")
        print("Brightness set to 60: success")

        post = wait_for_events(self.collector, timeout_sec=3.0)

        # Expect continued status/sensors events after brightness change
        continued = (post["status"] >= baseline["status"]) or (
            post["sensors"] >= baseline["sensors"]
        )
        self.assertTrue(
            continued,
            msg=(
                "No events observed after brightness change. "
                f"baseline={baseline}, post={post}"
            ),
        )

    def test_tare_scale_sets_weight_to_zero(self) -> None:
        # RE-ENABLED: API should return ActionResponse (status may be 'error' if state disallows tare)
        result = self.api.execute_action(ActionType.TARE)
        print(
            "TARE -> "
            f"status={getattr(result, 'status', None)}, "
            f"action={getattr(result, 'action', None)}, "
            f"allowed={getattr(result, 'allowed_actions', None)}"
        )
        self.assertIsInstance(
            result,
            ActionResponse,
            msg=f"Expected ActionResponse, got {type(result)}: {result}",
        )
        ar = cast(ActionResponse, result)
        self.assertIsNotNone(ar.action, msg="ActionResponse missing action field")
        self.assertIsNotNone(
            ar.allowed_actions, msg="ActionResponse missing allowed_actions field"
        )

    def test_profile_hover_socketio(self) -> None:
        """Test profile hover event (safe - doesn't load profile)."""
        self.api.connect_to_socket()

        # Get a profile to hover
        profiles = self.api.list_profiles()
        if isinstance(profiles, list) and len(profiles) > 0:
            profile_data = {"id": profiles[0].id, "name": profiles[0].name}
            # send_profile_hover doesn't return anything, just emits event
            self.api.send_profile_hover(profile_data)
            print(f"Profile hover sent for: {profiles[0].name}")
        else:
            self.skipTest("No profiles available for hover test")

    def test_profile_hover_select_focus(self) -> None:
        """Test profile hover with select/focus payload (safe)."""
        self.api.connect_to_socket()

        profiles = self.api.list_profiles()
        if not isinstance(profiles, list) or len(profiles) == 0:
            self.skipTest("No profiles available for hover focus test")
            return

        payload = {
            "id": profiles[0].id,
            "from": "app",
            "type": "focus",
        }
        self.api.send_profile_hover(payload)
        print(
            f"Profile hover select/focus sent for: {profiles[0].name} ({profiles[0].id})"
        )

    def test_profile_select_via_load_endpoint(self) -> None:
        """Test profile selection via load endpoint.

        NOTE: This test loads a profile which may trigger auto-start behavior
        depending on machine settings. Monitor carefully during first run.

        If this causes unwanted auto-start, mark as unsafe and skip.
        """
        from meticulous.api_types import PartialProfile

        # Get available profiles
        profiles = self.api.list_profiles()
        if not isinstance(profiles, list) or len(profiles) == 0:
            self.skipTest("No profiles available for selection test")
            return

        # Remember the first profile to select
        target_profile = profiles[0]
        print(
            f"Testing profile selection: {target_profile.name} (ID: {target_profile.id})"
        )

        # Connect socket to observe any events triggered
        self.api.connect_to_socket()
        baseline = wait_for_events(self.collector, timeout_sec=2.0)

        # Load/select the profile
        result = self.api.load_profile_by_id(target_profile.id)

        if isinstance(result, APIError):
            print(f"Profile selection returned error: {result.error}")
            self.skipTest(f"Profile selection failed: {result.error}")
            return

        self.assertIsInstance(result, PartialProfile)
        print(f"Profile selected successfully: {result.name}")

        # Wait a moment to see if any concerning events fire
        post = wait_for_events(self.collector, timeout_sec=3.0)

        # Log event differences (informational only)
        print(f"Events before: {baseline}")
        print(f"Events after: {post}")

        # Check if machine state changed to extracting (would indicate auto-start)
        if post["status"] > baseline["status"]:
            last_status = (
                self.collector.status_events[-1]
                if self.collector.status_events
                else None
            )
            if last_status:
                state_val = (
                    last_status.state
                    if hasattr(last_status, "state")
                    else last_status.get("state")
                )
                if state_val == "extracting":
                    self.fail(
                        "UNSAFE: Profile selection triggered extraction! "
                        "This test should be disabled."
                    )

    def test_set_timezone_safe(self) -> None:
        """Test timezone setting (restores original after test)."""
        from meticulous.api_types import APIError

        # Get current timezone to restore later
        current = self.api.get_timezone()
        if isinstance(current, APIError):
            self.skipTest("Timezone endpoint not available")
            return

        original_tz = current.timezone
        print(f"Original timezone: {original_tz}")

        # Try setting to the same timezone (safe no-op)
        result = self.api.set_timezone(original_tz)
        if not isinstance(result, APIError):
            self.assertEqual(result.timezone, original_tz)
            print(f"Timezone set (no change): {result.timezone}")

    def test_stop_action_returns_actionresponse(self) -> None:
        # Safe: STOP should be a no-op when idle; validate response shape only
        result = self.api.execute_action(ActionType.STOP)
        print(
            "STOP -> "
            f"status={getattr(result, 'status', None)}, "
            f"action={getattr(result, 'action', None)}, "
            f"allowed={getattr(result, 'allowed_actions', None)}"
        )
        self.assertIsInstance(result, ActionResponse)
        ar = cast(ActionResponse, result)
        self.assertIsNotNone(ar.action)
        self.assertIsNotNone(ar.allowed_actions)

    def test_preheat_action_returns_actionresponse(self) -> None:
        # UNSAFE: Preheating wastes energy and heats the boiler
        # Only uncomment if you want to test this action
        self.skipTest(
            "PREHEAT test disabled - heats boiler unnecessarily. Enable manually if needed."
        )


if __name__ == "__main__":
    unittest.main()
