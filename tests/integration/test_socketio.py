"""Integration tests for Socket.IO real-time events.

These tests require a real meticulous machine to be available.

Setup: See tests/integration/test_api_endpoints.py for configuration options.
Use local_config.py file or METICULOUS_HOST environment variable.
"""

import pytest
import unittest

from tests.integration.utils import (
    make_api_with_events,
    wait_for_events,
    get_base_url,
    server_reachable,
)


@pytest.mark.integration
class TestSocketIO(unittest.TestCase):
    def setUp(self) -> None:
        base_url = get_base_url()
        if not server_reachable(base_url):
            self.skipTest(f"Server not reachable at {base_url}")
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

        # Expect at least some status or sensor events in normal operation
        self.assertTrue(
            counts["status"] > 0 or counts["sensors"] > 0,
            msg=f"No events received: {counts}",
        )


if __name__ == "__main__":
    unittest.main()
