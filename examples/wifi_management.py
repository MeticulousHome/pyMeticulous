"""
Example: WiFi Management

This example demonstrates how to:
- Get WiFi status and configuration
- List available networks
- Connect to a network
- Manage saved networks
"""

from meticulous.api import Api, APIError


def main():
    # Initialize API
    api = Api(base_url="http://localhost:8080/")

    print("=" * 60)
    print("WIFI STATUS")
    print("=" * 60)

    # Get full WiFi status
    wifi_status = api.get_wifi_status()
    if isinstance(wifi_status, APIError):
        print(f"Error fetching WiFi status: {wifi_status.error}")
        return

    print(f"\nConfiguration:")
    print(f"  Mode: {wifi_status.config.mode}")
    print(f"  AP Name: {wifi_status.config.apName}")

    print(f"\nConnection Status:")
    print(f"  Connected: {wifi_status.status.connected}")
    if wifi_status.status.connected:
        print(f"  Network: {wifi_status.status.connection_name}")
        print(f"  IP Addresses: {', '.join(wifi_status.status.ips)}")
        print(f"  Gateway: {wifi_status.status.gateway}")
        print(f"  DNS Servers: {', '.join(wifi_status.status.dns)}")
        print(f"  MAC Address: {wifi_status.status.mac}")
        print(f"  Hostname: {wifi_status.status.hostname}")

    print(f"\nKnown Networks:")
    for ssid in wifi_status.known_wifis.keys():
        print(f"  - {ssid}")

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
