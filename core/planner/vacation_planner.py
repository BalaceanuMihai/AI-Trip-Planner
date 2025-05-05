from .flights import get_flights
from .hotels import get_hotels
from .activities import get_activities
from .gpt import suggest_destination

import json

def generate_vacation_plans(preferences_file):

    # Load preferences
    with open(preferences_file, "r") as f:
        data = json.load(f)

    preferences = data.get("preferences", {})

    destination = suggest_destination(preferences)

    # Example dates
    departure_date = "2025-06-10"
    return_date = "2025-06-20"

    # Get API data
    flights = get_flights("BUH", "BCN", departure_date, return_date)
    hotels = get_hotels(destination, departure_date, return_date)
    activities = get_activities(destination)

    # Build plan (simplified)
    plan_text = f"Destination: {destination}\n\n"
    plan_text += "Flights:\n" + str(flights) + "\n\n"
    plan_text += "Hotels:\n" + str(hotels) + "\n\n"
    plan_text += "Activities:\n" + str(activities) + "\n"

    return plan_text
