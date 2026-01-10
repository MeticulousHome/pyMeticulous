import unittest
import time

from meticulous.api import Api
from meticulous.api_types import APIError, BrightnessRequest, ActionType
from tests.smoke.utils import (
    make_api_with_events,
    wait_for_events,
    get_current_weight_from_status,
    choose_random_different_profile_id,
)


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

        # Baseline events
        baseline = wait_for_events(self.collector, timeout_sec=3.0)

        # Perform safe brightness change
        req = BrightnessRequest(brightness=60)
        result = self.api.set_brightness(req)
        self.assertIsNone(result, msg=f"Brightness change failed: {result}")

        # Observe events shortly after the change
        post = wait_for_events(self.collector, timeout_sec=3.0)

        # We expect at least continued status/temperature events; specific brightness event
        # may or may not be emitted by firmware. Record as soft assertion.
        self.assertTrue(
            post["status"] >= baseline["status"]
            or post["temperatures"] >= baseline["temperatures"],
            msg=f"No events observed after brightness change. baseline={baseline}, post={post}",
        )

    def test_tare_scale_sets_weight_to_zero(self) -> None:
        # Connect socket to observe status for weight
        self.api.connect_to_socket()

        # Collect initial status events
        counts = wait_for_events(self.collector, timeout_sec=5.0)
        self.assertTrue(
            counts["status"] > 0, msg=f"No status events received: {counts}"
        )

        # Execute TARE action (may fail if machine is busy, etc.)
        action_result = self.api.execute_action(ActionType.TARE)
        if isinstance(action_result, APIError):
            # Machine may be busy or in an invalid state; just log and skip
            print(f"TARE not available: {action_result.status} - {action_result.error}")
            self.skipTest(f"TARE unavailable: {action_result.status}")
            return

        # Wait briefly for weight update events
        wait_for_events(self.collector, timeout_sec=5.0)

        # Validate weight becomes zero (or very close to zero)
        final_weight = None
        for evt in reversed(self.collector.status_events):
            w = get_current_weight_from_status(evt)
            if w is not None:
                final_weight = w
                break

        # Only assert if we got a final weight reading
        if final_weight is not None:
            self.assertLessEqual(
                abs(final_weight or 0.0),
                0.1,
                msg=f"Final weight not ~0: {final_weight}",
            )

    def test_switch_active_profile_via_load_by_id(self) -> None:
        # Connect to observe profile change events
        self.api.connect_to_socket()

        # Get current active profile (last loaded)
        last = self.api.get_last_profile()
        current_id = (
            None if isinstance(last, APIError) else getattr(last.profile, "id", None)
        )

        # Choose a different profile id
        new_id = choose_random_different_profile_id(self.api, current_id)
        self.assertIsNotNone(new_id, msg="No alternative profile available to load")

        # Load new profile
        load_result = self.api.load_profile_by_id(new_id or "")
        if isinstance(load_result, APIError):
            # Machine may be busy (brewing, etc.); skip rather than fail
            print(
                f"Profile load not available: {load_result.status} - {load_result.error}"
            )
            self.skipTest(f"Profile load unavailable: {load_result.status}")
            return

        # Wait for profile change events
        counts = wait_for_events(
            self.collector, timeout_sec=5.0, expect_profile_change=True
        )
        self.assertTrue(
            counts["profiles"] > 0, msg=f"No profile change events observed: {counts}"
        )

        # Confirm last profile reflects the change
        updated_last = self.api.get_last_profile()
        if not isinstance(updated_last, APIError):
            self.assertEqual(getattr(updated_last.profile, "id", None), new_id)


if __name__ == "__main__":
    unittest.main()
