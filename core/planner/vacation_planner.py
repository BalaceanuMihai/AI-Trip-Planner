import json
import os
from dotenv import load_dotenv
from flights import search_all_flight_combinations
from hotels import get_hotels
from activities import get_activities

load_dotenv()

def generate_vacation_plans(preferences_file):
    # 1. Încarcă datele din fișierul JSON
    with open(preferences_file, "r") as f:
        data = json.load(f)

    # Suportă ambele formate: listă sau obiect direct
    plan_data = data[-1]["plan"] if isinstance(data, list) else data["plan"]

    # 2. Extrage detalii esențiale
    origin_city = plan_data.get("departure_city", "Bucharest")
    origin_country = plan_data.get("departure_country", "Romania")
    destination_city = plan_data.get("destination_city", "Rome")
    destination_country = plan_data.get("destination_country", "Italy")
    departure_date = plan_data.get("departure_date", "2025-07-15")
    return_date = plan_data.get("return_date", "2025-07-20")

    # 3. Apelează cele 3 servicii
    flights = search_all_flight_combinations(
        origin_city, origin_country, destination_city, destination_country, departure_date, return_date
    )
    hotels = get_hotels(destination_city, departure_date, return_date)
    activities = get_activities(destination_city)

    # 4. Formatează planul final în stil chatbot
    plan_parts = []

    # ✈ Zboruri
    if flights and not flights[0].startswith("❌") and not flights[0].startswith("🚫"):
        plan_parts.append(f"✈ Zboruri din {origin_city} spre {destination_city}:")
        plan_parts += [f"- {f}" for f in flights[:3]]
    else:
        plan_parts.append("❌ Nu am găsit zboruri disponibile.")

    # 🏨 Hoteluri
    if hotels and not hotels[0].startswith("⚠️"):
        plan_parts.append(f"\n🏨 Cazări în {destination_city}:")
        plan_parts += [f"- {h}" for h in hotels[:3]]
    else:
        plan_parts.append("⚠️ Nu am găsit hoteluri disponibile.")

    # 🎯 Activități
    if activities and not activities[0].startswith("⚠️"):
        plan_parts.append(f"\n🎯 Activități populare în {destination_city}:")
        plan_parts += [f"- {a}" for a in activities[:5]]
    else:
        plan_parts.append("⚠️ Nu am găsit activități disponibile.")

    # 5. Concatenează totul într-un singur string
    full_plan = "\n".join(plan_parts)

    return [full_plan]


