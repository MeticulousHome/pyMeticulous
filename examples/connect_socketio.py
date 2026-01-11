import requests
from meticulous.api import Api, ApiOptions
from meticulous.api_types import StatusData, SensorsEvent, ButtonEvent


def on_status_message(data: StatusData) -> None:
    print(f"\n[STATUS] State: {data.state}, Extracting: {data.extracting}")
    print(
        f"  Sensors: p={data.sensors.p:.2f} bar, f={data.sensors.f:.2f} ml/s, w={data.sensors.w:.1f}g"
    )
    print(f"  Profile: {data.profile} (time: {data.time / 1000:.1f}s)")


def on_sensors_message(data: SensorsEvent) -> None:
    print(
        f"\n[SENSORS] Temps: bar_up={data.t_bar_up:.1f}°C, motor={data.motor_temp:.1f}°C"
    )
    print(
        f"  Motor: pos={data.m_pos:.1f}, speed={data.m_spd:.1f}, power={data.m_pwr:.1f}W"
    )


def on_button_event(data: ButtonEvent) -> None:
    print(
        f"\n[BUTTON] Type: {data.type}, Time since last: {data.time_since_last_event}ms"
    )


def main() -> None:
    # Throttle Socket.IO events to reduce chatter:
    # - Global interval (e.g., 0.25 for all events at 250ms)
    # - Per-event dict like {"status": 0.25, "sensors": 0.5, "button": 0.1}
    options = ApiOptions(
        onStatus=on_status_message,
        onSensors=on_sensors_message,
        onButton=on_button_event,
        throttle={
            "status": 0.25,
            "sensors": 0.5,
            "button": 0.0,
        },  # No throttle for buttons
    )
    api = Api(base_url="http://localhost:8080/", options=options)

    try:
        # Connect with retry logic (3 retries, exponential backoff)
        api.connect_to_socket(retries=3, backoff=0.5)

        print("Connected to Socket.IO! Listening for events...\n")
        print("Example: Send an action via Socket.IO:")
        print("  from meticulous.api_types import ActionType")
        print("  api.send_action_socketio(ActionType.TARE)\n")

        # Keep the application running to listen to messages
        input("Press Enter to exit...\n")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Disconnect the socket
        api.disconnect_socket()


if __name__ == "__main__":
    main()
