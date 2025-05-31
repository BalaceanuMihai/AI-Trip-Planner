import os
import requests
from dotenv import load_dotenv

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "sky-scrapper.p.rapidapi.com"


def get_location_info(city_name):
    url = f"https://{RAPIDAPI_HOST}/api/v1/flights/searchAirport"
    params = {"query": city_name}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    # 🔍 Adaugă această linie pentru a vedea ce returnează API-ul
    print(f"\n🔎 Răspuns brut pentru '{city_name}':\n{data}\n")

    airports = data.get("data", [])
    if not airports:
        raise ValueError(f"❌ Niciun aeroport găsit pentru orașul: {city_name}")

    airport = airports[0]
    name = airport.get("name", city_name)
    return airport["skyId"], airport["entityId"], name




def search_flights_v2(origin_sky_id, destination_sky_id, origin_entity_id, destination_entity_id, date):
    """
    Folosește v2/searchFlights pentru a căuta zboruri între două orașe.
    """
    url = f"https://{RAPIDAPI_HOST}/api/v2/flights/searchFlights"
    params = {
        "originSkyId": origin_sky_id,
        "destinationSkyId": destination_sky_id,
        "originEntityId": origin_entity_id,
        "destinationEntityId": destination_entity_id,
        "cabinClass": "economy",
        "adults": "1",
        "sortBy": "best",
        "currency": "USD",
        "market": "en-US",
        "countryCode": "US",
        "date": date
    }
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def generate_skyscanner_link(origin_iata, destination_iata, date):
    """
    Generează link direct către pagina Skyscanner pentru o rută și dată dată.
    """
    date_formatted = date.replace("-", "")[2:]  # ex: 2025-08-01 -> 250801
    return f"https://www.skyscanner.net/transport/flights/{origin_iata.lower()}/{destination_iata.lower()}/{date_formatted}/"


def display_flights(data, max_results=5):
    """
    Afișează cele mai bune zboruri găsite.
    """
    itineraries = data.get("data", {}).get("itineraries", [])
    if not itineraries:
        print("❌ Nu au fost găsite zboruri.")
        return

    print(f"\n🛫 Top {min(max_results, len(itineraries))} zboruri găsite:\n")
    for i, flight in enumerate(itineraries[:max_results], 1):
        leg = flight["legs"][0]
        departure = leg.get("departure")
        arrival = leg.get("arrival")
        duration = leg.get("durationInMinutes", 0)
        carrier = leg.get("carriers", {}).get("marketing", [{}])[0].get("name", "N/A")
        price = flight.get("price", {}).get("formatted", "N/A")

        print(f"{i}. {carrier} | {departure} → {arrival} | Durată: {duration} min | Preț: {price}")


def search_flights_between_cities(origin_city, destination_city, date):
    """
    Proces complet: de la orașe la afișarea zborurilor.
    """
    print(f"🔎 Caut zboruri din {origin_city} către {destination_city} pentru data {date}...")

    origin_sky_id, origin_entity_id, _ = get_location_info(origin_city)
    destination_sky_id, destination_entity_id, _ = get_location_info(destination_city)

    data = search_flights_v2(origin_sky_id, destination_sky_id, origin_entity_id, destination_entity_id, date)
    display_flights(data)


# Exemplu de rulare
if __name__ == "__main__":
    search_flights_between_cities("London", "New York", "2025-08-01")
