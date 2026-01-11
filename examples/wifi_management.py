"""
Example: WiFi Management

This example demonstrates how to:
- Get WiFi configuration
- List available networks
- Connect to a network
- Manage saved networks
"""

from typing import cast

from meticulous.api import Api, APIError
from meticulous.api_types import WiFiConfig, WiFiConfigResponse


def main() -> None:
    # Initialize API
    api = Api(base_url="http://localhost:8080/")

    print("=" * 60)
    print("WIFI CONFIGURATION")
    print("=" * 60)

    # Get WiFi configuration (may include status if available)
    wifi_config = api.get_wifi_config()
    if isinstance(wifi_config, APIError):
        print(f"Error fetching WiFi config: {wifi_config.error}")
        return

    print("\nConfiguration:")
    if isinstance(wifi_config, WiFiConfigResponse):
        response = cast(WiFiConfigResponse, wifi_config)
        print(f"  Mode: {response.config.mode}")
        print(f"  AP Name: {response.config.apName}")
        print("\nConnection Status:")
        print(f"  Connected: {response.status.connected}")
        print(f"  Network: {response.status.connection_name}")
        print(f"  Gateway: {response.status.gateway}")
        print(f"  IPs: {', '.join(response.status.ips)}")
        print(f"  DNS: {', '.join(response.status.dns)}")
        print(f"  MAC: {response.status.mac}")
    elif isinstance(wifi_config, WiFiConfig):
        config = cast(WiFiConfig, wifi_config)
        print(f"  Mode: {config.mode}")
        print(f"  AP Name: {config.apName}")
    else:
        print("Unexpected WiFi config payload")
        return

    print("\n" + "=" * 60)
    print("AVAILABLE NETWORKS")
    print("=" * 60)

    # Scan for available networks
    networks = api.list_available_wifi()
    if isinstance(networks, APIError):
        print(f"Error scanning networks: {networks.error}")
        return

    print(f"\nFound {len(networks)} networks:\n")

    # Sort by signal strength
    sorted_networks = sorted(networks, key=lambda n: n.signal, reverse=True)

    for network in sorted_networks:
        in_use_indicator = "✓" if network.in_use else " "
        security_type = network.type or "UNKNOWN"
        signal_bars = "█" * (network.signal // 20)

        print(
            f"[{in_use_indicator}] {network.ssid:30s} {signal_bars:5s} {network.signal:3d}% {security_type}"
        )

    # Example: Connect to a network (commented out for safety)
    print("\n" + "=" * 60)
    print("CONNECT TO NETWORK (Example)")
    print("=" * 60)
    print("\nTo connect to a network, use:")
    print(
        """
    connect_request = WiFiConnectRequest(
        ssid="YourNetworkName",
        password="YourPassword"
    )
    result = api.connect_to_wifi(connect_request)
    if result is None:
        print("Connected successfully!")
    """
    )

    # Example: Remove a saved network (commented out for safety)
    print("\n" + "=" * 60)
    print("REMOVE SAVED NETWORK (Example)")
    print("=" * 60)
    print("\nTo remove a saved network, use:")
    print(
        """
    result = api.delete_wifi("NetworkToRemove")
    if result is None:
        print("Network removed successfully!")
    """
    )


if __name__ == "__main__":
    main()
