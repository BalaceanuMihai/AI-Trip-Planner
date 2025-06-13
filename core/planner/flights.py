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

def get_airports_from_city(city_name):
    matches = airports_df[airports_df["City"].str.lower() == city_name.lower()]
    return [(row["IATA"], row["Name"]) for _, row in matches.iterrows() if pd.notna(row["IATA"])]

def search_all_flight_combinations(origin_city, destination_city, date=None):
    origin_airports = get_airports_from_city(origin_city)
    destination_airports = get_airports_from_city(destination_city)

    if not origin_airports:
        print(f"❌ Niciun aeroport găsit pentru orașul de plecare: {origin_city}")
        return
    if not destination_airports:
        print(f"❌ Niciun aeroport găsit pentru orașul de destinație: {destination_city}")
        return

    found_any = False
    for origin_iata in origin_airports:
        for dest_iata in destination_airports:
            print(f"\n🔍 Caut zboruri din {origin_city} ({origin_iata}) către {destination_city} ({dest_iata})...")

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
            response = requests.get(url, headers=headers, params=querystring)

            try:
                response.raise_for_status()
                data = response.json()
                itineraries = data.get("itineraries", [])

                if itineraries:
                    found_any = True
                    for idx, itinerary in enumerate(itineraries, 1):

                        try:
                            # Extragem segmentul dus (outbound)
                            out_seg = itinerary["outbound"]["sectorSegments"][0]["segment"]
                            in_seg = itinerary["inbound"]["sectorSegments"][0]["segment"]

                            airline = out_seg["carrier"]["name"]
                            departure = out_seg["source"]["localTime"]
                            arrival = out_seg["destination"]["localTime"]
                            return_dep = in_seg["source"]["localTime"]
                            return_arr = in_seg["destination"]["localTime"]

                            price = float(itinerary["price"]["amount"])
                            currency = "USD"  # sau itinerary["price"].get("currency", "USD")

                            booking_url = itinerary["bookingOptions"]["edges"][0]["node"]["bookingUrl"]
                            full_url = f"https://www.kiwi.com{booking_url}"

                            print(f"✅ Zbor #{idx}:")
                            print(f"   ✈️ {airline}")
                            print(f"   📤 Plecare: {departure} → Sosire: {arrival}")
                            print(f"   🔁 Întoarcere: {return_dep} → Sosire: {return_arr}")
                            print(f"   💵 Preț: {price:.2f} {currency}")
                            print(f"   🔗 Rezervă: {full_url}\n")

                        except Exception as e:
                            print(f"⚠️ Eroare la parsarea itinerariului #{idx}: {e}")

                else:
                    print("❌ Niciun zbor găsit pentru această combinație.")

            except Exception as e:
                print(f"⚠️ Eroare la request: {e}")

    if not found_any:
        print("\n🚫 Nu au fost găsite zboruri pentru nicio combinație.")

# Exemplu rulare locală
if __name__ == "__main__":
    search_all_flight_combinations("Barcelona", "Rome", date="2025-08-05")
