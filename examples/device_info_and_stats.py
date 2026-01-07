"""
Example: Device Information and Statistics

This example demonstrates how to:
- Get device information
- Retrieve shot history statistics
- Display brewing statistics by profile
"""

from meticulous.api import Api, APIError


def main():
    # Initialize API
    api = Api(base_url="http://localhost:8080/")

    print("=" * 60)
    print("DEVICE INFORMATION")
    print("=" * 60)

    # Get device info
    device_info = api.get_device_info()
    if isinstance(device_info, APIError):
        print(f"Error fetching device info: {device_info.error}")
        return

    print(f"Device Name: {device_info.name}")
    print(f"Model: {device_info.model_version}")
    print(f"Serial Number: {device_info.serial}")
    print(f"Batch Number: {device_info.batch_number}")
    print(f"Build Date: {device_info.build_date}")
    print(f"Firmware: {device_info.firmware}")
    print(f"Software Version: {device_info.software_version}")
    print(f"Main Voltage: {device_info.mainVoltage}V")
    print(f"Manufacturing Mode: {device_info.manufacturing}")
    print(f"Version History: {', '.join(device_info.version_history[-3:])}")

    print("\n" + "=" * 60)
    print("SHOT HISTORY STATISTICS")
    print("=" * 60)

    # Get history statistics
    stats = api.get_history_statistics()
    if isinstance(stats, APIError):
        print(f"Error fetching statistics: {stats.error}")
        return

    print(f"\nTotal Saved Shots: {stats.totalSavedShots}\n")

    print("Breakdown by Profile:")
    print("-" * 60)

    for profile_stat in stats.byProfile:
        percentage = (
            (profile_stat.count / stats.totalSavedShots * 100)
            if stats.totalSavedShots > 0
            else 0
        )
        print(f"  {profile_stat.name}")
        print(f"    Shots: {profile_stat.count} ({percentage:.1f}%)")
        print(f"    Profile Versions: {profile_stat.profileVersions}")
        print()

    # Get most recent shot
    print("=" * 60)
    print("MOST RECENT SHOT")
    print("=" * 60)

    last_shot = api.get_last_shot()
    if last_shot is None:
        print("No shots recorded yet")
    elif isinstance(last_shot, APIError):
        print(f"Error fetching last shot: {last_shot.error}")
    else:
        print(f"\nShot ID: {last_shot.id}")
        print(f"Name: {last_shot.name}")
        print(f"Profile: {last_shot.profile.name}")
        print(f"Temperature: {last_shot.profile.temperature}°C")
        print(f"Target Weight: {last_shot.profile.final_weight}g")
        if last_shot.rating:
            print(f"Rating: {last_shot.rating}")
        print(f"Data Points: {len(last_shot.data)}")

        # Calculate shot duration
        if last_shot.data:
            duration = last_shot.data[-1].time / 1000.0  # Convert to seconds
            print(f"Duration: {duration:.1f}s")


if __name__ == "__main__":
    main()
