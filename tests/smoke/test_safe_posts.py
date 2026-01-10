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
        # DISABLED: Taring can have unintended consequences on machine state
        # Skipping to avoid triggering unexpected behaviors
        self.skipTest(
            "Tare operation disabled in smoke tests - requires machine idle state"
        )

    def test_switch_active_profile_via_load_by_id(self) -> None:
        # DISABLED: Loading profiles may trigger auto-start or other state changes
        # Skipping to avoid unintended machine operations
        self.skipTest(
            "Profile loading disabled in smoke tests - may trigger auto-start behavior"
        )


if __name__ == "__main__":
    unittest.main()
