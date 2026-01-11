"""
Example: Socket.IO Event Throttling

This example demonstrates how to control Socket.IO event rates.
The backend streams status/sensors at 10Hz (every 100ms), which can be
overwhelming. Use throttling to reduce update frequency.
"""

import time
from meticulous.api import Api, ApiOptions
from meticulous.api_types import StatusData, SensorsEvent


class ThrottleDemo:
    def __init__(self, name: str) -> None:
        self.name = name
        self.status_count = 0
        self.sensors_count = 0
        self.start_time = time.time()

    def on_status(self, data: StatusData) -> None:
        self.status_count += 1

    def on_sensors(self, data: SensorsEvent) -> None:
        self.sensors_count += 1

    def report(self) -> None:
        elapsed = time.time() - self.start_time
        print(f"\n{self.name}:")
        print(f"  Duration: {elapsed:.1f}s")
        print(
            f"  Status events: {self.status_count} ({self.status_count / elapsed:.1f}/s)"
        )
        print(
            f"  Sensors events: {self.sensors_count} ({self.sensors_count / elapsed:.1f}/s)"
        )


def demo_no_throttle() -> ThrottleDemo:
    """No throttling - receive all events at 10Hz"""
    print("\n" + "=" * 60)
    print("DEMO 1: No Throttling (10Hz)")
    print("=" * 60)

    demo = ThrottleDemo("No Throttling")
    options = ApiOptions(
        onStatus=demo.on_status,
        onSensors=demo.on_sensors,
        throttle=0.0,  # No throttling
    )

    api = Api(base_url="http://localhost:8080/", options=options)

    try:
        api.connect_to_socket()
        print("Connected! Collecting events for 10 seconds...")
        time.sleep(10)
    finally:
        api.disconnect_socket()

    demo.report()
    return demo


def demo_global_throttle() -> ThrottleDemo:
    """Global throttle - all events at 1Hz"""
    print("\n" + "=" * 60)
    print("DEMO 2: Global Throttling (1Hz)")
    print("=" * 60)

    demo = ThrottleDemo("Global Throttle 1Hz")
    options = ApiOptions(
        onStatus=demo.on_status,
        onSensors=demo.on_sensors,
        throttle=1.0,  # 1 second between events
    )

    api = Api(base_url="http://localhost:8080/", options=options)

    try:
        api.connect_to_socket()
        print("Connected! Collecting events for 10 seconds...")
        time.sleep(10)
    finally:
        api.disconnect_socket()

    demo.report()
    return demo


def demo_per_event_throttle() -> ThrottleDemo:
    """Per-event throttle - status at 4Hz, sensors at 2Hz"""
    print("\n" + "=" * 60)
    print("DEMO 3: Per-Event Throttling (status=4Hz, sensors=2Hz)")
    print("=" * 60)

    demo = ThrottleDemo("Per-Event Throttle")
    options = ApiOptions(
        onStatus=demo.on_status,
        onSensors=demo.on_sensors,
        throttle={
            "status": 0.25,  # 4 per second
            "sensors": 0.5,  # 2 per second
        },
    )

    api = Api(base_url="http://localhost:8080/", options=options)

    try:
        api.connect_to_socket()
        print("Connected! Collecting events for 10 seconds...")
        time.sleep(10)
    finally:
        api.disconnect_socket()

    demo.report()
    return demo


def main() -> None:
    print("\n" + "=" * 60)
    print("EVENT THROTTLING COMPARISON")
    print("=" * 60)
    print("\nThe Meticulous backend streams events at 10Hz (100ms interval).")
    print("This demo shows how throttling reduces CPU usage and handler load.\n")

    # Run all three demos
    demo1 = demo_no_throttle()
    time.sleep(2)  # Pause between demos

    demo2 = demo_global_throttle()
    time.sleep(2)

    demo3 = demo_per_event_throttle()

    # Summary comparison
    print("\n" + "=" * 60)
    print("SUMMARY COMPARISON")
    print("=" * 60)

    print(f"\nNo throttling: {demo1.status_count + demo1.sensors_count} total events")
    print(f"Global 1Hz: {demo2.status_count + demo2.sensors_count} total events")
    print(f"Per-event: {demo3.status_count + demo3.sensors_count} total events")

    total1 = demo1.status_count + demo1.sensors_count
    total2 = demo2.status_count + demo2.sensors_count
    total3 = demo3.status_count + demo3.sensors_count

    reduction_global = 100 * (1 - (total2 / total1))
    reduction_per = 100 * (1 - (total3 / total1))
    print(f"\nGlobal throttling: {reduction_global:.0f}% reduction")
    print(f"Per-event throttling: {reduction_per:.0f}% reduction")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print("\n• UI updates: 2-4 Hz (0.25-0.5s throttle)")
    print("• Logging: 1 Hz (1.0s throttle)")
    print("• Critical events (button): 0.0s throttle (no delay)")
    print("• Background monitoring: 0.1 Hz (10s throttle)")


if __name__ == "__main__":
    main()
