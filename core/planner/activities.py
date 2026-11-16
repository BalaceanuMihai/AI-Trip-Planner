import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST_TRIPADVISOR = os.getenv(
    "RAPIDAPI_HOST_TRIPADVISOR"
)  # ex: travel-advisor.p.rapidapi.com

headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST_TRIPADVISOR}


# ✅ Obține location_id folosind endpointul corect
def get_location_id(city_name):
    url = f"https://{RAPIDAPI_HOST_TRIPADVISOR}" "/locations/v2/search"

    params = {"lang": "en_US", "currency": "EUR", "units": "km"}

    payload = {"query": city_name, "updateToken": ""}

    response = requests.post(
        url,
        headers={**headers, "Content-Type": "application/json"},
        params=params,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    sections = (
        data.get("data", {})
        .get("AppPresentation_queryAppSearch", {})
        .get("sections", [])
    )

    for section in sections:
        card = section.get("appSearchCardContent") or {}
        title = (card.get("cardTitle") or {}).get("string", "")
        save_id = card.get("saveId") or {}

        route = (card.get("cardLink") or {}).get("route") or {}
        typed_params = route.get("typedParams") or {}

        if (
            title.casefold() == city_name.strip().casefold()
            and save_id.get("type") == "location"
            and typed_params.get("contentType") == "geo"
        ):
            return save_id.get("id")

    return None


# ✅ Obține atracții turistice reale
from datetime import date, timedelta
from html import escape
from urllib.parse import quote_plus
import re


def get_activities(city_name, start_date=None, end_date=None):
    # Date implicite pentru testarea separata a functiei
    if not start_date:
        start_date = (date.today() + timedelta(days=30)).isoformat()

    if not end_date:
        end_date = (date.fromisoformat(start_date) + timedelta(days=5)).isoformat()

    location_id = get_location_id(city_name)

    if not location_id:
        return ["⚠️ Nu s-a găsit această locație."]

    url = f"https://{RAPIDAPI_HOST_TRIPADVISOR}" "/attractions/v2/list"

    payload = {
        "geoId": int(location_id),
        "startDate": start_date,
        "endDate": end_date,
        "pax": [{"ageBand": "ADULT", "count": 1}],
        "sort": "TRAVELER_FAVORITE_V2",
        "sortOrder": "asc",
        "filters": [],
        "updateToken": "",
    }

    params = {"lang": "en_US", "currency": "EUR", "units": "km"}

    try:
        response = requests.post(
            url,
            headers={**headers, "Content-Type": "application/json"},
            params=params,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError) as e:
        print("Eroare Tripadvisor:", e)
        return ["⚠️ Nu am putut încărca atracțiile turistice."]

    groups = data.get("data", {}).get("AppPresentation_queryAppListV2") or []

    results = []

    for group in groups:
        for section in group.get("sections", []):
            card = section.get("listSingleCardContent") or {}

            name = (card.get("cardTitle") or {}).get("string")

            if not name:
                continue

            name = re.sub(r"^\d+\.\s*", "", name)

            category = (card.get("primaryInfo") or {}).get("text") or ""

            rating = (card.get("bubbleRating") or {}).get("rating")

            # Link de cautare: API-ul v2 furnizeaza
            # rute interne, nu neaparat URL-uri web publice.
            search = quote_plus(f"{name} {city_name}")
            link = f"https://www.tripadvisor.com/Search?q={search}"

            text = escape(name)

            if category:
                text += f" — {escape(category)}"

            if rating is not None:
                text += f" (Rating: {rating}/5)"

            text += (
                f'<br>🔗 <a href="{escape(link, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">'
                "Caută pe Tripadvisor</a>"
            )

            results.append(text)

            if len(results) == 5:
                return results

    if not results:
        return ["⚠️ Nu am găsit atracții turistice."]

    return results
