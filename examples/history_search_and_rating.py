"""
Example: History Search and Shot Rating

This example demonstrates how to:
- Search shot history
- Filter and sort results
- Rate shots
- Display detailed shot information
"""

from datetime import datetime, timedelta
from meticulous.api import Api, APIError
from meticulous.api_types import HistoryQueryParams


def main() -> None:
    # Initialize API
    api = Api(base_url="http://localhost:8080/")

    print("=" * 60)
    print("SHOT HISTORY SEARCH")
    print("=" * 60)

    # Search for shots from the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)

    query = HistoryQueryParams(
        start_date=seven_days_ago.isoformat(),
        end_date=datetime.now().isoformat(),
        max_results=10,
        sort="desc",
        order_by=["date"],
        dump_data=False,  # Set to True if you need full data points
    )

    history = api.search_history(query)
    if isinstance(history, APIError):
        print(f"Error fetching history: {history.error}")
        return

    print(f"\nFound {len(history.history)} shots in the last 7 days:\n")

    for shot in history.history:
        shot_time = datetime.fromtimestamp(shot.time)
        print(f"Shot: {shot.name} (ID: {shot.db_key})")
        print(f"  Date: {shot_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Profile: {shot.profile.name}")
        print(f"  Temperature: {shot.profile.temperature}°C")
        print(f"  Target Weight: {shot.profile.final_weight}g")

        # Show rating if available
        if shot.rating:
            emoji = "👍" if shot.rating == "like" else "👎"
            print(f"  Rating: {emoji} {shot.rating}")
        else:
            print("  Rating: Not rated")

        print()

    # Example: Rate the most recent shot
    if history.history and history.history[0].db_key is not None:
        latest_shot = history.history[0]
        assert latest_shot.db_key is not None
        shot_id = latest_shot.db_key

        print("=" * 60)
        print("RATING EXAMPLE")
        print("=" * 60)

        print(f"\nRating shot: {latest_shot.name}")

        # Rate as "like"
        rating_response = api.rate_shot(shot_id, "like")
        if isinstance(rating_response, APIError):
            print(f"Error rating shot: {rating_response.error}")
        else:
            print(
                f"Successfully rated shot {rating_response.shot_id}: {rating_response.rating}"
            )

        # Get the rating back
        rating = api.get_shot_rating(shot_id)
        if not isinstance(rating, APIError):
            print(f"Current rating: {rating.rating}")

    # Search for shots by profile name
    print("\n" + "=" * 60)
    print("SEARCH BY PROFILE")
    print("=" * 60)

    profile_search = api.search_historical_profiles("Italian")
    if isinstance(profile_search, APIError):
        print(f"Error searching profiles: {profile_search.error}")
    else:
        print(
            f"\nFound {len(profile_search.history)} shots with 'Italian' in profile name"
        )
        for shot in profile_search.history[:5]:  # Show first 5
            print(f"  - {shot.name} ({shot.profile.name})")


if __name__ == "__main__":
    main()
