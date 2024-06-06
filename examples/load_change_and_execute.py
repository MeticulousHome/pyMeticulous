import requests
from meticulous.api import Api, APIError
import traceback


def main() -> None:
    api = Api(base_url="http://localhost:8080/")

    try:
        # Fetch all profiles
        profiles = api.list_profiles()
        if isinstance(profiles, APIError):
            print(f"Error fetching profiles: {profiles.error}")
            return

        if not profiles:
            print("No profiles found.")
            return

        print("------")
        print("Profiles:")
        print(profiles)

        # Select the first profile
        first_profile_id = profiles[0].id

        # Get the full profile details
        profile = api.get_profile(first_profile_id)
        if isinstance(profile, APIError):
            print(f"Error fetching profile: {profile.error}")
            return

        print("------")
        print("Full Profile:")
        print(profile)

        # Modify an entry in the variables array
        if profile.variables:
            print("------")
            print("Profile variables:")
            for var in profile.variables:
                print(var)

            profile.variables[0].value += 1

        # Save the profile
        save_response = api.save_profile(profile)
        if isinstance(save_response, APIError):
            print(f"Error saving profile: {save_response.error}")
            return

        print("------")
        print(f"Profile saved successfully: change_id={save_response.change_id}")

        # Load the profile by ID
        loaded_profile = api.load_profile_by_id(save_response.profile.id)
        if isinstance(loaded_profile, APIError):
            print(f"Error loading profile: {loaded_profile.error}")
            return

        print("------")
        print(f"Profile loaded successfully: {loaded_profile.id}")

        # Execute action (start)
        action_response = api.execute_action("start")
        if isinstance(action_response, APIError):
            print(f"Error executing action: {action_response.error}")
            return

        print(f"Action executed successfully: {action_response.action}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:

        print(f"An error occurred: {e}")
        print(traceback.format_exc(e))


if __name__ == "__main__":
    main()
