import requests
import os
from dotenv import load_dotenv

load_dotenv()

AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")

def get_access_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }

    response = requests.post(url, data=data)
    return response.json()["access_token"]

def get_flights(origin, destination, departure_date, return_date):
    token = get_access_token()

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "returnDate": return_date,
        "adults": 1,
        "max": 3
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()
