import json
import os
from dotenv import load_dotenv
from core.planner.flights import get_flights
from core.planner.hotels import get_hotels
from core.planner.activities import get_activities

load_dotenv()

def generate_vacation_plans(preferences_file):
    # Load travel preferences and plan
    with open(preferences_file, "r") as f:
        data = json.load(f)

    # Suport pentru formatul cu listă (istoric) sau direct obiect
    plan_data = data[-1]["plan"] if isinstance(data, list) else data["plan"]

    destination = plan_data["country"]
    budget = plan_data["budget"]
    # activities = plan_data.get("activities", [])
    travel_window = plan_data.get("travel_window", "2025-07-10 to 2025-07-20")  # fallback dacă lipsesc datele

    # Extrage datele de plecare și întoarcere
    try:
        departure_date, return_date = [d.strip() for d in travel_window.split("to")]
    except ValueError:
        departure_date, return_date = "2025-07-10", "2025-07-20"

    origin = "BUH"  # Aeroport de plecare (București)

    # Fetch data from real APIs
    flights = get_flights(origin, destination, departure_date, return_date)
    hotels = get_hotels(destination, departure_date, return_date, budget)
    activity_options = get_activities(destination)

    # Format the full vacation plan
    plan_text = f"✈️ Flights to {destination}:\n"
    plan_text += "\n".join(f"- {flight}" for flight in flights) + "\n\n"

    plan_text += f"🏨 Hotel Options in {destination}:\n"
    plan_text += "\n".join(f"- {hotel}" for hotel in hotels) + "\n\n"

    plan_text += f"🎯 Suggested Activities in {destination}:\n"
    plan_text += "\n".join(f"- {act}" for act in activity_options) + "\n"

    return [plan_text]
