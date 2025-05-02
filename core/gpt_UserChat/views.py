import json, os
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
import re
from dotenv import load_dotenv

load_dotenv()

# ✅ Set OpenAI API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PREF_FILE = os.path.join(os.path.dirname(__file__), "user_preferences.json")
conversation_store = {}  # Temporary user memory

def chat_ui(request):
    return render(request, "chat.html")

@csrf_exempt
def chat_api(request):
    data = json.loads(request.body)
    user_input = data.get("message", "")
    user_id = "demo_user"  # Replace with session or login ID

    if user_id not in conversation_store:
        conversation_store[user_id] = [
            {"role": "system", "content": (
                "You are a helpful AI travel assistant. "
                "When the user gives vague trip preferences, first ask 2-3 follow-up questions "
                "to better understand their desired type of trip, budget, activities, or travel season. "
                "However, if the user says they have no restrictions or are open to anything, "
                "skip the questions and directly suggest 3 to 5 suitable destinations. "
                "After the user selects a destination, remember it for the final summary."
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
    conversation = conversation_store.get(user_id, [])

    conversation.append({
        "role": "system",
        "content": (
            "Now summarize the user's confirmed travel preferences based on the full conversation. "
            "Include the chosen destination if the user confirmed one. "
            "Only summarize confirmed or clearly implied preferences. "
            "Format the output as JSON with fields like: destination, climate, budget, season, crowd_level, activity_type."
        )
    })

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation
    )

    summary = response.choices[0].message.content
    try:
        prefs_json = extract_json(summary)
        if prefs_json.get("destination"):
            save_preferences(prefs_json)
            return JsonResponse({"status": "saved", "preferences": prefs_json})
        else:
            return JsonResponse({"status": "skipped", "message": "Destination not confirmed by user."})
    except:
        return JsonResponse({"status": "error", "message": "Could not extract preferences."})

def extract_destinations(text):
    lines = text.strip().split('\n')
    destinations = []
    for line in lines:
        match = re.match(r"\d+\.\s+(.+)", line)
        if match:
            destinations.append(match.group(1).strip())
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
