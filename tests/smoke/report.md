# Smoke Test Report (auto-generated)

This document will be updated after running the smoke tests to summarize:
- Endpoint reachability and status codes
- Model validation outcomes vs `meticulous/api_types.py`
- Socket.IO event reception and counts
- Safe POST action validations (brightness, tare, profile switch)
- URL mismatches and proposed fixes

Run instructions:

```bash
export METICULOUS_BASE_URL="http://192.168.0.115:8080"
python -m pytest -q tests/smoke
```

On Windows PowerShell:

```powershell
$env:METICULOUS_BASE_URL = "http://192.168.0.115:8080"
python -m pytest -q tests/smoke
```

After execution, capture logs and update this report accordingly.
