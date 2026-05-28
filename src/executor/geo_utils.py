import os
from pathlib import Path

import requests
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


def _location_candidates(location):
    cleaned = " ".join(str(location or "").replace("\n", " ").split())
    cleaned = cleaned.replace("Neppal", "Nepal").replace("neppal", "Nepal")
    if not cleaned:
        return ["Kathmandu, Nepal"]

    candidates = [cleaned]
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]

    for index in range(1, len(parts)):
        candidate = ", ".join(parts[index:])
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    if "nepal" not in cleaned.lower():
        candidates.append(f"{cleaned}, Nepal")

    if "Kathmandu, Nepal" not in candidates:
        candidates.append("Kathmandu, Nepal")

    return candidates


def _geocode_with_geoapify(location, api_key):
    if not api_key:
        return None

    response = requests.get(
        "https://api.geoapify.com/v1/geocode/search",
        params={
            "text": location,
            "format": "json",
            "limit": 1,
            "apiKey": api_key,
        },
        timeout=8,
    )
    response.raise_for_status()

    results = response.json().get("results", [])
    if not results:
        return None

    result = results[0]
    lat = result.get("lat")
    lon = result.get("lon")

    if lat is None or lon is None:
        return None

    return {
        "latitude": lat,
        "longitude": lon,
        "formatted": result.get("formatted") or location,
        "source": "geoapify",
    }


def _geocode_with_open_meteo(location):
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1},
        timeout=5,
    )
    response.raise_for_status()

    results = response.json().get("results", [])
    if not results:
        return None

    result = results[0]
    lat = result.get("latitude")
    lon = result.get("longitude")

    if lat is None or lon is None:
        return None

    name_parts = [
        result.get("name"),
        result.get("admin1"),
        result.get("country"),
    ]

    return {
        "latitude": lat,
        "longitude": lon,
        "formatted": ", ".join(part for part in name_parts if part),
        "source": "open-meteo",
    }


def geocode_location(location, api_key=None):
    api_key = api_key or os.getenv("GEOAPIFY_API_KEY")
    errors = []

    for candidate in _location_candidates(location):
        for geocoder in (
            lambda value: _geocode_with_geoapify(value, api_key),
            _geocode_with_open_meteo,
        ):
            try:
                result = geocoder(candidate)
            except Exception as exc:
                errors.append(f"{candidate}: {type(exc).__name__}")
                continue

            if result:
                result["query"] = location
                result["matched_query"] = candidate
                return result

    print(f"[Geocoding ERROR] Could not resolve {location!r}. Attempts: {errors}")
    return None
