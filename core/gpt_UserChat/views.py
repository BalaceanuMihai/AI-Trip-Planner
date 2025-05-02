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
conversation_store = {}  # Temporary user memory

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
                "When the user gives vague trip preferences, do not suggest destinations right away. "
                "Ask for information step-by-step, one question at a time, waiting for answers. "
                "Ask about these in order: travel period (dates or season), budget/restrictions, trip type, crowd preference. "
                "Accept vague answers like 'summer' or 'next week' as valid. "
                "If the user says they have no restrictions or preferences, skip to the next question. "
                "Only after all answers, suggest 3-5 destinations that match with a short description for each. "
                "Once the user selects a destination, remember it for the final summary."
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
    data = json.loads(request.body)
    user_id = "demo_user"
    travel_dates = data.get("travel_dates")
    trip_length = data.get("trip_length")
    activities = data.get("activities")

    conversation = conversation_store.get(user_id, [])

    conversation.append({
        "role": "system",
        "content": (
            "Now summarize the user's confirmed travel preferences based on the full conversation. "
            "Include the chosen destination if the user confirmed one. "
            "Only summarize confirmed or clearly implied preferences. "
            "If the user mentioned a season like spring, summer, autumn, or winter, store that under 'season'. "
            "If they mentioned specific travel periods or vague date ranges (like 'next week', 'July 5-20'), ignore that for preferences but use for travel plan if given. "
            "Climate should only describe weather preferences (like warm, tropical, cool, cold). "
            "Format the output as JSON with fields: country, climate, season, budget, crowd_level, trip_type."
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
            fields_to_save = ["country", "climate", "season", "budget", "crowd_level", "trip_type"]
            prefs_to_save = {k: prefs_json.get(k) for k in fields_to_save}
            save_preferences(prefs_to_save)

            # Save user travel plan (destination, travel dates, trip length, activities, budget)
            plan_to_save = {
                "country": prefs_json.get("country"),
                "travel_window": travel_dates,
                "trip_length": trip_length,
                "activities": activities,
                "budget": prefs_json.get("budget")
            }
            save_travel_plan(plan_to_save)

            return JsonResponse({"status": "saved", "preferences": prefs_to_save, "travel_plan": plan_to_save})
        else:
            return JsonResponse({"status": "skipped", "message": "Destination not confirmed by user."})
    except:
        return JsonResponse({"status": "error", "message": "Could not extract preferences."})

def extract_destinations(text):
    lines = text.strip().split('\n')
    destinations = []
    current_destination = None

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
    entry = {
        "timestamp": datetime.now().isoformat(),
        "preferences": prefs
    }

    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)
    with open(PREF_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_travel_plan(plan):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "plan": plan
    }

    if os.path.exists(TRAVEL_PLAN_FILE):
        with open(TRAVEL_PLAN_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)
    with open(TRAVEL_PLAN_FILE, "w") as f:
        json.dump(data, f, indent=2)
