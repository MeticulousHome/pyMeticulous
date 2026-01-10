import unittest

from tests.smoke.utils import make_api_with_events, wait_for_events


class TestSocketIO(unittest.TestCase):
    def setUp(self) -> None:
        self.api, self.collector = make_api_with_events()

    def tearDown(self) -> None:
        try:
            self.api.disconnect_socket()
        except Exception:
            pass

    def test_connect_and_receive_events(self) -> None:
        # Connect and listen briefly
        self.api.connect_to_socket()
        counts = wait_for_events(self.collector, timeout_sec=5.0)

        # Expect at least some status or temperature events in normal operation
        self.assertTrue(
            counts["status"] > 0 or counts["temperatures"] > 0,
            msg=f"No events received: {counts}",
        )


if __name__ == "__main__":
    unittest.main()
