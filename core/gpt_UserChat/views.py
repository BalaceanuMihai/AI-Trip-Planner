import json, os
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from dotenv import load_dotenv
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
                "Ask users if they have specific travel periods in mind, how long they wish to stay (trip length in days or nights), "
                "and from where they will depart for the trip (departure_location), but separate questions for different topics. "
                "Store vague periods like 'summer' as travel_window and trip duration as trip_length. "
                "Collect departure_location, budget, trip type, crowd preference, and activities. "
                "Once enough preferences are gathered, suggest 3-5 destinations with short descriptions. "
                "When user chooses a destination, remember it for final summary."
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
    chosen = data.get("destination")
    user_id = "demo_user"

    if user_id in conversation_store:
        conversation_store[user_id].append({
            "role": "user",
            "content": f"I choose {chosen} as my destination."
        })
        return JsonResponse({"status": "ok", "message": f"{chosen} selected."})

    return JsonResponse({"status": "error", "message": "No active conversation."})

@csrf_exempt
def end_conversation(request):
    user_id = "demo_user"
    conversation = conversation_store.get(user_id, [])

    conversation.append({
        "role": "system",
        "content": (
            "Now summarize the user's confirmed travel preferences. "
            "Include departure_location (where the user will leave from), travel_window, trip_length, activities, budget, crowd_level, trip_type, and country. "
            "Format output as JSON with: country, departure_location, climate, season, travel_window, trip_length, activities, budget, crowd_level, trip_type."
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
                "departure_location": prefs_json.get("departure_location"),
                "travel_window": prefs_json.get("travel_window"),
                "trip_length": prefs_json.get("trip_length"),
                "activities": prefs_json.get("activities"),
                "budget": prefs_json.get("budget"),
                "crowd_level": prefs_json.get("crowd_level"),
                "trip_type": prefs_json.get("trip_type")
            }
            save_travel_plan(plan_to_save)

            return JsonResponse({"status": "saved", "preferences": prefs_json, "travel_plan": plan_to_save})
        else:
            return JsonResponse({"status": "skipped", "message": "Destination not confirmed by user."})
    except:
        return JsonResponse({"status": "error", "message": "Could not extract preferences."})

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
