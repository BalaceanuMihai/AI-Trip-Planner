import requests
import os
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

def get_hotels(city, checkin_date, checkout_date):
    url = "https://booking-com.p.rapidapi.com/v1/hotels/search"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }

    query = {
        "city": city,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "adults_number": 1,
        "order_by": "price",
        "units": "metric",
        "room_number": 1
    }

    response = requests.get(url, headers=headers, params=query)
    return response.json()
