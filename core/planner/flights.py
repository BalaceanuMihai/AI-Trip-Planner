"""Kiwi flight search integration via the official Kiwi.com MCP server.

This module replaces the retired third-party RapidAPI Kiwi integration.
It retains the synchronous search_all_flight_combinations() interface used
by core/planner/vacation_planner.py and returns up to three HTML-ready strings.
"""

import asyncio
import json
import logging
from datetime import datetime
from html import escape
from urllib.parse import urlparse

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

KIWI_MCP_URL = "https://mcp.kiwi.com"
logger = logging.getLogger(__name__)


def _kiwi_date(iso_date):
    """Convert YYYY-MM-DD (Django plan format) to DD/MM/YYYY (Kiwi MCP)."""
    return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d/%m/%Y")


def _display_datetime(value):
    if not value:
        return "necunoscută"

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
            "%H:%M %d-%m-%Y"
        )
    except (TypeError, ValueError):
        return escape(str(value))


def _airline_names(leg):
    names = [
        segment.get("carrierName") or segment.get("carrier")
        for segment in (leg.get("segments") or [])
        if isinstance(segment, dict)
    ]

    return (
        ", ".join(dict.fromkeys(str(name) for name in names if name))
        or "Companie necunoscută"
    )


def _booking_url(itinerary):
    """Accept only HTTPS links hosted by Kiwi, since the template uses |safe."""
    raw_url = itinerary.get("bookingUrl") or ""
    parsed = urlparse(raw_url)

    if parsed.scheme == "https" and parsed.hostname in ("kiwi.com", "www.kiwi.com"):
        return raw_url

    return None


def _format_itinerary(itinerary, currency):
    outbound = itinerary.get("outbound") or {}
    inbound = itinerary.get("inbound") or {}

    if not outbound or not inbound:
        return None

    price = itinerary.get("price")

    try:
        price_label = f"{float(price):.2f} {currency}"
    except (TypeError, ValueError):
        price_label = itinerary.get("priceFormatted") or "indisponibil"

    baggage = itinerary.get("baggage") or {}

    baggage_label = (
        f"obiect personal: {baggage.get('personalItem', '?')}, "
        f"cabină: {baggage.get('cabinBag', '?')}, "
        f"cală: {baggage.get('checkedBag', '?')}"
    )

    lines = [
        f"✈ Dus: {escape(_airline_names(outbound))} "
        f"({escape(str(outbound.get('from', '?')))} → "
        f"{escape(str(outbound.get('to', '?')))})",
        f"📤 Plecare: {_display_datetime(outbound.get('departureTime'))} "
        f"→ Sosire: {_display_datetime(outbound.get('arrivalTime'))}",
        f"🔁 Întors: {escape(_airline_names(inbound))} "
        f"({escape(str(inbound.get('from', '?')))} → "
        f"{escape(str(inbound.get('to', '?')))})",
        f"📥 Plecare: {_display_datetime(inbound.get('departureTime'))} "
        f"→ Sosire: {_display_datetime(inbound.get('arrivalTime'))}",
        f"🛬 Escale: dus {escape(str(outbound.get('stops', '?')))}, "
        f"întors {escape(str(inbound.get('stops', '?')))}",
        f"🧳 Bagaje: {escape(baggage_label)}",
        f"💶 Preț total: {escape(price_label)}",
    ]

    link = _booking_url(itinerary)

    if link:
        lines.append(
            f'🔗 <a href="{escape(link, quote=True)}" target="_blank" '
            'rel="noopener noreferrer">Rezervă aici</a>'
        )

    return "\n".join(lines)


async def _search_flights(origin_city, destination_city, departure_date, return_date):
    arguments = {
        "flyFrom": origin_city,
        "flyTo": destination_city,
        "departureDate": _kiwi_date(departure_date),
        "returnDate": _kiwi_date(return_date),
        "adults": 1,
        "currency": "EUR",
        "sort": "price",
    }

    async with streamable_http_client(KIWI_MCP_URL) as (read, write):

        async with ClientSession(read, write) as session:
            await session.initialize()

            response = await session.call_tool("search-flight", arguments=arguments)

            if getattr(response, "is_error", False):
                details = " ".join(
                    getattr(item, "text", "") for item in response.content
                )

                raise RuntimeError(f"Kiwi MCP a returnat o eroare: {details[:500]}")

            for item in response.content:
                if getattr(item, "type", None) != "text":
                    continue

                payload = json.loads(item.text)

                if isinstance(payload, dict) and "itineraries" in payload:
                    return payload

    raise ValueError("Răspunsul Kiwi MCP nu conține lista 'itineraries'.")


def search_all_flight_combinations(
    origin_city,
    origin_country,
    destination_city,
    destination_country,
    departure_date=None,
    return_date=None,
):
    """
    Synchronous API preserved for vacation_planner.py.

    Kiwi MCP accepts city names directly and searches the airports serving
    them, so origin_country and destination_country remain for compatibility.
    """

    if not departure_date or not return_date:
        return [
            "🚫 Lipsesc datele de plecare sau întoarcere " "pentru căutarea zborurilor."
        ]

    try:
        _kiwi_date(departure_date)
        _kiwi_date(return_date)

        if return_date < departure_date:
            return ["🚫 Data întoarcerii trebuie să fie " "după data plecării."]

        data = asyncio.run(
            _search_flights(origin_city, destination_city, departure_date, return_date)
        )

    except Exception as exc:
        logger.exception("Kiwi MCP flight search failed")

        return [f"🚫 Căutarea zborurilor a eșuat: " f"{escape(str(exc))[:200]}"]

    itineraries = data.get("itineraries") or []

    if not isinstance(itineraries, list):
        return ["🚫 Kiwi MCP a returnat un format " "neașteptat pentru zboruri."]

    # Order by total price and ignore malformed entries.
    def price_key(item):
        try:
            return float(item.get("price", float("inf")))
        except (ValueError, TypeError, AttributeError):
            return float("inf")

    results = []

    for itinerary in sorted(itineraries, key=price_key):
        if not isinstance(itinerary, dict):
            continue

        formatted = _format_itinerary(itinerary, data.get("currency") or "EUR")

        if formatted:
            results.append(formatted)

        if len(results) == 3:
            break

    return results or ["🚫 Nu au fost găsite zboruri pentru această combinație."]
