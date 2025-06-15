import json, os
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from dotenv import load_dotenv
from core.planner.vacation_planner import generate_vacation_plans
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PREF_FILE = os.path.join(os.path.dirname(__file__), "user_preferences.json")
TRAVEL_PLAN_FILE = os.path.join(os.path.dirname(__file__), "user_travel_plan.json")
conversation_store = {}

def chat_ui(request):
    return render(request, "chat.html")

@csrf_exempt
def chat_api(request):
    data = json.loads(request.body)
    user_input = data.get("message", "")
    user_id = "demo_user"

    if user_id not in conversation_store:
        conversation_store[user_id] = [
            {"role": "system", "content": (
                "You are a helpful AI travel assistant. "
                "Keep the conversation casual, without imposing strict formats. "
                "Ask different questions for each topic that will follow. Don't ask multiple questions at once. "
                "Ask users if they have specific travel periods in mind or how long they wish to stay (trip length in days or nights), "
                "and from where they will depart for the trip. Ask for the departure city and based on that find what the country of departure is (store as departure_city and departure_country). "
                "If the user tells you the departure date and the duration of the trip, calculate the return date without asking for it. "
                "If needed, ask users for specific travel dates: exact departure date (departure_date) and return date (return_date). "
                "departure_date and return_date must be real dates provided by the user or inferred close to today. Avoid using past dates like 2022 or 2023. Assume dates are in the future, e.g., 2025."
                "If the user only provides a departure date, assume a default return date 5-7 days later. "
                "Store the dates in ISO format: YYYY-MM-DD. Do not use travel_window anymore, calculate it based on departure_date and return_date."
                "Collect departure_city, departure_country, trip type, crowd preference, and activities."
                "Once enough preferences are gathered, suggest 3-5 destinations with short descriptions. "
                "The destinations should be in this format: City, Country: description. "
                "When user chooses a destination, remember it for final summary."
                "After the user confirms a destination, tell him to end the chat for the full vacation plan."
            )}
        ]

    conversation = conversation_store[user_id]
    conversation.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation
    )

    reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": reply})

    destinations = extract_destinations(reply)

    return JsonResponse({
        "reply": reply,
        "suggested_destinations": destinations
    })

@csrf_exempt
def select_destination(request):
    data = json.loads(request.body)
    destination_text = data.get("destination")  # Ex: "Rome, Italy: beautiful history and food"
    user_id = "demo_user"

    if user_id in conversation_store:
        conversation_store[user_id].append({
            "role": "user",
            "content": f"I choose {destination_text} as my destination."
        })
        save_selected_destination(destination_text)
        return JsonResponse({"status": "ok", "message": f"{destination_text} selected."})

    return JsonResponse({"status": "error", "message": "No active conversation."})

@csrf_exempt
def end_conversation(request):
    user_id = "demo_user"
    conversation = conversation_store.get(user_id, [])

    conversation.append({
        "role": "system",
        "content": (
            "Now summarize the user's confirmed travel preferences. "
            "Include departure_city and departure_country (where the user will leave from), "
            "and also include destination_city and destination_country (where the user is going). "
            "Format output as JSON with: destination_country, destination_city, departure_city, departure_country, country, city, climate, season, departure_date, return_date, trip_length, activities, crowd_level, trip_type."
        )
    })

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation
    )

    summary = response.choices[0].message.content
    try:
        prefs_json = extract_json(summary)

        if prefs_json.get("country"):
            save_preferences(prefs_json)

            plan_to_save = {
                "country": prefs_json.get("country"),
                "city": prefs_json.get("city"),
                "destination_country": prefs_json.get("destination_country"),
                "destination_city": prefs_json.get("destination_city"),
                "departure_city": prefs_json.get("departure_city"),
                "departure_country": prefs_json.get("departure_country"),
                "departure_date": prefs_json.get("departure_date"),
                "return_date": prefs_json.get("return_date"),
                "trip_length": prefs_json.get("trip_length"),
                "activities": prefs_json.get("activities"),
                "crowd_level": prefs_json.get("crowd_level"),
                "trip_type": prefs_json.get("trip_type")
            }


            save_travel_plan(plan_to_save)

            return JsonResponse({"status": "saved", "preferences": prefs_json, "travel_plan": plan_to_save})
        else:
            return JsonResponse({"status": "skipped", "message": "Destination not confirmed by user."})
    except:
        return JsonResponse({"status": "error", "message": "Could not extract preferences."})
    


# === Utility Functions ===

def extract_destinations(text):
    lines = text.strip().split('\n')
    destinations = []

    for line in lines:
        match = re.match(r"\d+\.\s+(.+?)\s*-\s*(.+)", line)
        if match:
            destination = match.group(1).strip()
            description = match.group(2).strip()
            destinations.append(f"{destination}: {description}")
    return destinations if destinations else None

def extract_city_country(destination_text):
    """
    Primește: "Rome, Italy: something..."
    Returnează: ("Rome", "Italy")
    """
    if ":" in destination_text:
        location_part = destination_text.split(":", 1)[0].strip()
    else:
        location_part = destination_text.strip()

    if "," in location_part:
        city, country = [x.strip() for x in location_part.split(",", 1)]
        return city, country
    return location_part, None  # fallback

def extract_json(text):
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])

def save_preferences(prefs):
    entry = {"timestamp": datetime.now().isoformat(), "preferences": prefs}
    data = []
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, "r") as f:
            data = json.load(f)
    data.append(entry)
    with open(PREF_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_travel_plan(plan):
    entry = {"timestamp": datetime.now().isoformat(), "plan": plan}
    data = []
    if os.path.exists(TRAVEL_PLAN_FILE):
        with open(TRAVEL_PLAN_FILE, "r") as f:
            data = json.load(f)
    data.append(entry)
    with open(TRAVEL_PLAN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_selected_destination(destination_text):
    city, country = extract_city_country(destination_text)

    if os.path.exists(TRAVEL_PLAN_FILE):
        with open(TRAVEL_PLAN_FILE, "r+") as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                data[-1]["plan"]["selected_destination"] = destination_text
                data[-1]["plan"]["destination_city"] = city
                data[-1]["plan"]["destination_country"] = country
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
                
def vacation_plan(request):
    plan = generate_vacation_plans()
    return render(request, "vacation_plan.html", {"plan": plan})