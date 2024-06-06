# pyMeticulous

Meticulous API wrapper in python

## Installation

You can install the `pyMeticulous` package using pip:

```bash
pip install pyMeticulous
```

## Usage

Here is a guide on how to use the pyMeticulous package with example code snippets.

### Example 1: Fetch Profiles, Modify and Save

This example demonstrates how to fetch all profiles, check out the examples folder for more complex logic

```python

import requests
from meticulous.api import Api, APIError, Profile, ProfileIdent, ActionResponse

def main():
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
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
```

### Execute Profile without saving

A profile doesn't need to be saved to be executed. It can be executed in-place and will then be available until another profile was loaded with the get_last_profile() function


```python
profile = Profile(**profile_json)

# Load the profile from JSON into the realtime core (not threadsafe, any other API consumer can overwrite!)
load_response = api.load_profile_from_json(profile)

# Start the profile
action_response = api.execute_action('start')
```

## Error Handling

- APIError: Each method call that interacts with the API can return an APIError object, which contains error details. Check for APIError and handle it accordingly.
- Requests Exceptions: Network-related exceptions are caught using requests.exceptions.RequestException.
- General Exceptions: All other exceptions are caught and handled in a generic manner.