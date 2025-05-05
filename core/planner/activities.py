import requests
import os
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

def get_activities(city):
    url = "https://travel-advisor.p.rapidapi.com/locations/search"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "travel-advisor.p.rapidapi.com"
    }

    query = {"query": city, "limit": "5"}

    response = requests.get(url, headers=headers, params=query)
    return response.json()
