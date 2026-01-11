# Integration Tests

This folder contains optional integration tests that exercise a real Meticulous machine via REST and Socket.IO. These tests are safe, skip gracefully when the machine or endpoints are unavailable, and avoid destructive operations.

## Prerequisites

1. Meticulous machine reachable on your network
2. Set `METICULOUS_HOST` to `<host>:<port>` (e.g., `192.168.1.100:8080`)
3. Activate your venv and install test deps:

```bash
pip install -e ".[test]"
```

## Run

```bash
# Run only integration tests
pytest -m integration

# Run a specific file
pytest tests/integration/test_api_endpoints.py -m integration
pytest tests/integration/test_socketio.py -m integration
```

## Behavior

- Endpoints that return non-JSON are handled robustly
- Wi‑Fi endpoints may be unavailable; tests skip in that case
- Socket.IO handlers support optional throttling via `ApiOptions.throttle`
- No factory reset or firmware flashing is performed

For a quick overview and links, see the root [README.md](../../README.md#running-tests).
