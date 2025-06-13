import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load env vars
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "kiwi-com-cheap-flights.p.rapidapi.com"

# Load airport data
airports_df = pd.read_csv("core/planner/data/airports_cleaned.csv")

def get_airports_from_city_and_country(city_name, country_name):
    matches = airports_df[
        (airports_df["City"].str.lower() == city_name.lower()) &
        (airports_df["Country"].str.lower() == country_name.lower())
    ]
    return [
        (row["IATA"], row["Name"], row["Country"], row["City"])
        for _, row in matches.iterrows()
        if pd.notna(row["IATA"])
    ]

def search_all_flight_combinations(origin_city, origin_country, destination_city, destination_country, date=None):
    origin_airports = get_airports_from_city_and_country(origin_city, origin_country)
    destination_airports = get_airports_from_city_and_country(destination_city, destination_country)

    if not origin_airports:
        print(f"❌ Niciun aeroport găsit pentru orașul de plecare: {origin_city}")
        return [f"❌ Niciun aeroport găsit pentru {origin_city}"]
    if not destination_airports:
        print(f"❌ Niciun aeroport găsit pentru orașul de destinație: {destination_city}")
        return [f"❌ Niciun aeroport găsit pentru {destination_city}"]

    results = []  

    for origin_iata, origin_name, origin_country, origin_city in origin_airports:
        for dest_iata, dest_name, dest_country, dest_city in destination_airports:
            print(f"\n🔍 Caut zboruri din {origin_name} ({origin_iata}) către {dest_name} ({dest_iata})...")

            querystring = {
                "source": origin_iata,
                "destination": dest_iata,
                "currency": "usd",
                "locale": "en",
                "adults": "1",
                "children": "0",
                "infants": "0",
                "handbags": "1",
                "holdbags": "0",
                "cabinClass": "ECONOMY",
                "sortBy": "QUALITY",
                "sortOrder": "ASCENDING",
                "applyMixedClasses": "true",
                "allowReturnFromDifferentCity": "true",
                "allowChangeInboundDestination": "true",
                "allowChangeInboundSource": "true",
                "allowDifferentStationConnection": "true",
                "enableSelfTransfer": "true",
                "enableOvernightStopover": "true",
                "enableTrueHiddenCity": "true",
                "enableThrowAwayTicketing": "true",
                "outbound": "SUNDAY,MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY",
                "transportTypes": "FLIGHT",
                "contentProviders": "KIWI",
                "limit": "5"
            }

            if date:
                querystring["date"] = date

            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            }

            url = f"https://{RAPIDAPI_HOST}/round-trip"
            try:
                response = requests.get(url, headers=headers, params=querystring)
                response.raise_for_status()
                data = response.json()
                itineraries = data.get("itineraries", [])

                for idx, itinerary in enumerate(itineraries, 1):
                    try:
                        out_seg = itinerary["outbound"]["sectorSegments"][0]["segment"]
                        in_seg = itinerary["inbound"]["sectorSegments"][0]["segment"]

                        airline = out_seg["carrier"]["name"]
                        departure = out_seg["source"]["localTime"]
                        arrival = out_seg["destination"]["localTime"]
                        return_dep = in_seg["source"]["localTime"]
                        return_arr = in_seg["destination"]["localTime"]

                        price = float(itinerary["price"]["amount"])
                        currency = "USD"
                        booking_url = itinerary["bookingOptions"]["edges"][0]["node"]["bookingUrl"]
                        full_url = f"https://www.kiwi.com{booking_url}"

                        formatted = (
                            f"✈ {airline}\n"
                            f"📤 Plecare: {departure} → Sosire: {arrival}\n"
                            f"🔁 Întoarcere: {return_dep} → Sosire: {return_arr}\n"
                            f"💵 Preț: {price:.2f} {currency}\n"
                            f"🔗 [Rezervă]({full_url})"
                        )

                        results.append(formatted)

                    except Exception as e:
                        print(f"⚠ Eroare la parsarea itinerariului #{idx}: {e}")

            except Exception as e:
                print(f"⚠ Eroare la request: {e}")

    if not results:
        return ["🚫 Nu au fost găsite zboruri pentru această combinație."]
    
    return results


# Exemplu rulare locală
if _name_ == "_main_":
    search_all_flight_combinations("Barcelona", "Spain", "Rome", "Italy", date="2025-08-05")