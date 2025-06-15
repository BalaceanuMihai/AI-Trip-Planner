import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST_BOOKING")  # trebuie să fie apidojo-booking-v1.p.rapidapi.com

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

# ✅ Obține dest_id pe baza numelui orașului
def get_location_id(city_name):
    url = "https://apidojo-booking-v1.p.rapidapi.com/locations/auto-complete"
    params = {
        "text": city_name,
        "languagecode": "en-us"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    locations = response.json()

    if not locations:
        print("⚠️ Locație negăsită pentru:", city_name)
        return None
    
    return locations[0]["dest_id"]


# ✅ Obține hoteluri reale folosind endpointul apidojo
def get_hotels(city, arrival_date, departure_date):
    dest_id = get_location_id(city)
    if not dest_id:
        return ["⚠️ Locația nu a fost găsită."]

    url = "https://apidojo-booking-v1.p.rapidapi.com/properties/list"
    params = {
        "offset": "0",
        "arrival_date": arrival_date,
        "departure_date": departure_date,
        "guest_qty": "1",
        "children_qty": "0",
        "dest_ids": dest_id,
        "room_qty": "1",
        "search_type": "city",
        "search_id": "none",
        "price_filter_currencycode": "EUR",
        "order_by": "popularity",
        "languagecode": "en-us",
        "travel_purpose": "leisure"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    hotels = data.get("result", [])
    if not hotels:
        return ["⚠️ Niciun hotel găsit."]

    # ✅ Filtrare doar cazările disponibile
    available_hotels = [
        hotel for hotel in hotels
        if hotel.get("soldout") == 0 and hotel.get("min_total_price") and hotel.get("block_ids")
    ]

    if not available_hotels:
        return ["⚠️ Nu există cazări disponibile în perioada selectată."]
    
    # print("\n\n\n")
    # print(json.dumps(hotels[0], indent=2))  # vezi structura exactă
    # print("\n\n\n")

    # 📅 Preluare componente pentru linkul cu date
    checkin = datetime.strptime(arrival_date, "%Y-%m-%d")
    checkout = datetime.strptime(departure_date, "%Y-%m-%d")

    results = []
    for hotel in available_hotels[:3]:
        try:
            name = hotel.get("hotel_name", "Unknown")
            price = hotel.get("min_total_price", "N/A")
            address = hotel.get("address", "No address")

            # 🔗 Link de căutare cu date și nume hotel
            query = f"{name} {city}".replace(" ", "+")
            booking_url = (
                f"https://www.booking.com/searchresults.html?"
                f"ss={query}"
                f"&checkin_year={checkin.year}"
                f"&checkin_month={checkin.month}"
                f"&checkin_monthday={checkin.day}"
                f"&checkout_year={checkout.year}"
                f"&checkout_month={checkout.month}"
                f"&checkout_monthday={checkout.day}"
            )

            results.append(
                f"{name} — {price} {hotel.get('currencycode')}, {address}<br>"
                f'🔗 <a href="{booking_url}" target="_blank">Vezi pe Booking</a>'
            )
            
        except Exception as e:
            print("⚠️ Eroare la extragerea hotelului:", e)
    
    return results
