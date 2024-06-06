import requests
from meticulous.api import Api, ApiOptions
from meticulous.api_types import StatusData


def on_status_message(data: StatusData) -> None:
    print(f"Received sensor data: {data}")


def main() -> None:
    options = ApiOptions(onStatus=on_status_message)
    api = Api(base_url="http://localhost:8080/", options=options)

    try:
        # Connect to the socket
        api.connect_to_socket()

        # Keep the application running to listen to messages
        input("Listening for sensor messages. Press Enter to exit...\n")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Disconnect the socket
        api.disconnect_socket()


if __name__ == "__main__":
    main()
