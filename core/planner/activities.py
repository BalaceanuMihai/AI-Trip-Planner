import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST_TRIPADVISOR = os.getenv("RAPIDAPI_HOST_TRIPADVISOR")  # ex: travel-advisor.p.rapidapi.com

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST_TRIPADVISOR
}

# ✅ Obține location_id folosind endpointul corect
def get_location_id(city_name):
    url = "https://travel-advisor.p.rapidapi.com/locations/search"
    params = {
        "query": city_name,
        "lang": "en_US",
        "units": "km"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    for result in data.get("data", []):
        if result.get("result_type") == "geos":
            return result.get("result_object", {}).get("location_id")
    
    return None

# ✅ Obține atracții turistice reale
def get_activities(city_name):
    location_id = get_location_id(city_name)
    if not location_id:
        return ["⚠️ Nu s-a găsit această locație."]

    url = "https://travel-advisor.p.rapidapi.com/attractions/list"
    params = {
        "location_id": location_id,
        "lang": "en_US",
        "currency": "EUR",
        "sort": "recommended",
        "lunit": "km"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for activity in data.get("data", []):
        name = activity.get("name")
        description = activity.get("description", "")
        link = activity.get("web_url", "")

        if name and "Things to Do" not in name:
            text = f"{name} — {description[:100]}..."
            if link:
                text += f"\n🔗 {link}"
            results.append(text)

    if not results:
        return ["⚠️ Nu am găsit atracții turistice."]

    return results[:5]
