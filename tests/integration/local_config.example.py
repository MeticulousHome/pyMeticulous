"""Example local configuration for integration tests.

Copy this file to local_config.py and set your machine's IP address.
The local_config.py file is gitignored and won't be committed.

Usage:
    1. Copy this file: cp local_config.example.py local_config.py
    2. Edit local_config.py and set your machine's IP address
    3. Run integration tests: pytest -m integration
"""

# Set this to your meticulous machine's IP address and port
# Examples:
#   METICULOUS_HOST = "192.168.1.100:8080"
#   METICULOUS_HOST = "http://192.168.1.100:8080"
#   METICULOUS_HOST = "meticulous.local:8080"
METICULOUS_HOST = "localhost:8080"
