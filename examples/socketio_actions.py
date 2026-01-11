"""
Example: Socket.IO Actions and Notifications

This example demonstrates how to:
- Send actions via Socket.IO (instead of REST)
- Listen for machine state changes
- Acknowledge notifications
- Handle button events
"""

import time
from meticulous.api import Api, ApiOptions
from meticulous.api_types import (
    ActionType,
    StatusData,
    ButtonEvent,
    NotificationData,
    HeaterStatus,
)


class MachineMonitor:
    def __init__(self) -> None:
        self.last_state = None
        self.last_extracting = None

    def on_status(self, data: StatusData) -> None:
        # Track state changes
        if data.state != self.last_state:
            print(f"\n[STATE CHANGE] {self.last_state} → {data.state}")
            self.last_state = data.state

        if data.extracting != self.last_extracting:
            status = "STARTED" if data.extracting else "STOPPED"
            print(f"[EXTRACTION] {status}")
            self.last_extracting = data.extracting

        # Show current shot metrics when extracting
        if data.extracting:
            print(
                f"  Shot: {data.time / 1000:.1f}s | "
                f"P: {data.sensors.p:.1f} bar | "
                f"F: {data.sensors.f:.1f} ml/s | "
                f"W: {data.sensors.w:.1f}g"
            )

    def on_button(self, data: ButtonEvent) -> None:
        print(f"\n[BUTTON] {data.type} (after {data.time_since_last_event}ms)")

    def on_notification(self, data: NotificationData) -> None:
        print(f"\n[NOTIFICATION] {data.message}")
        print(f"  Options: {', '.join(data.responses)}")

    def on_heater_status(self, data: HeaterStatus) -> None:
        if data.remaining > 0:
            print(f"\n[HEATER] Preheat remaining: {data.remaining} minutes")


def main() -> None:
    # Initialize monitor and API
    monitor = MachineMonitor()

    options = ApiOptions(
        onStatus=monitor.on_status,
        onButton=monitor.on_button,
        onNotification=monitor.on_notification,
        onHeaterStatus=monitor.on_heater_status,
        throttle={"status": 0.5, "button": 0.0},  # Throttle status, not buttons
    )

    api = Api(base_url="http://localhost:8080/", options=options)

    try:
        # Connect with retries
        print("Connecting to machine...")
        api.connect_to_socket(retries=3, backoff=0.5)
        print("Connected!\n")

        # Example: Send tare action via Socket.IO
        print("=" * 60)
        print("SOCKET.IO ACTION EXAMPLE")
        print("=" * 60)

        print("\nSending TARE action via Socket.IO...")
        api.send_action_socketio(ActionType.TARE)
        print("Tare action sent!")

        # Wait a bit for the action to process
        time.sleep(2)

        # Example: Start preheat
        print("\nSending PREHEAT action via Socket.IO...")
        api.send_action_socketio(ActionType.PREHEAT)
        print("Preheat action sent!")

        print("\n" + "=" * 60)
        print("MONITORING MACHINE STATE")
        print("=" * 60)
        print("\nPress Ctrl+C to stop monitoring...\n")

        # Keep monitoring
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        api.disconnect_socket()
        print("Disconnected.")


if __name__ == "__main__":
    main()
