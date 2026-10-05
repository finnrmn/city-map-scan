import googlemaps
import time
import json
import os
from pathlib import Path

from dotenv import load_dotenv

# API-Key kommt aus app/backend/setups/.env (nicht eingecheckt), siehe .env.example
load_dotenv(Path(__file__).resolve().parent / ".env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY fehlt – bitte in app/backend/setups/.env setzen.")
# Platzhalter für gespeicherte URLs; pois_api.py ersetzt ihn zur Laufzeit durch den echten Key
API_KEY_PLACEHOLDER = "{GOOGLE_API_KEY}"
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

KATEGORIEN = {
    "Sehenswürdigkeit": "tourist_attraction",
    "Museum": "museum",
    "Kino": "movie_theater",
    "Kirche": "church",
    "Theater": "theater",
    "Park": "park",
    "Platz": "square",
    "Restaurants": "restaurant",
}

STADTLISTE = [
    "Darmstadt",
    "Berlin",
    "Hamburg",
    "München",
    "Köln",
    "Frankfurt am Main",
    "Stuttgart",
    "Düsseldorf",
    "Dortmund",
    "Essen",
    "Leipzig",
    "Bremen",
    "Dresden",
    "Hannover",
    "Nürnberg",
    "Duisburg"
]

TOP_N = 10


def get_city_location(city_name):
    """Gibt lat/lon von einer Stadt zurück (mittels Geocoding API)"""
    geocode = gmaps.geocode(f"{city_name}, Deutschland")
    if not geocode:
        raise ValueError(f"Stadt {city_name} nicht gefunden.")
    loc = geocode[0]["geometry"]["location"]
    return loc["lat"], loc["lng"]


def get_places_for_category(city, lat, lon, kategorie_google, top_n=10):
    """Findet Top-N Orte einer Kategorie in einer Stadt, holt Details"""
    # Textsuche nach Kategorie im Stadtgebiet (Radius 20km als Kompromiss)
    if city == "Darmstadt":
        radius = 10000
    else:
        radius = 20000
    results = gmaps.places_nearby(
        location=(lat, lon),
        radius=radius,
        type=kategorie_google,
        language="de"
    )["results"]

    # Sortieren nach rating, review_count
    results.sort(key=lambda x: (x.get("rating", 0), x.get("user_ratings_total", 0)), reverse=True)

    pois = []
    for place in results[:top_n]:
        place_id = place["place_id"]
        details = gmaps.place(place_id=place_id, language="de")["result"]
        poi = {
            "name": details.get("name"),
            "beschreibung": details.get("editorial_summary", {}).get("overview") or details.get("types", [None])[0],
            "bewertung": details.get("rating"),
            "bewertung_count": details.get("user_ratings_total"),
            "foto_url": get_photo_url(details),
            "google_url": details.get("url"),
            "adresse": details.get("formatted_address"),
            "oeffnungszeiten": details.get("opening_hours", {}).get("weekday_text", []),
            "lat": details.get("geometry", {}).get("location", {}).get("lat"),
            "lon": details.get("geometry", {}).get("location", {}).get("lng"),
        }
        pois.append(poi)
        time.sleep(0.5)  # Um nicht geblockt zu werden
    return pois


def get_photo_url(details):
    """Erstellt Google Photo-URL, falls Foto vorhanden"""
    if "photos" in details and len(details["photos"]) > 0:
        ref = details["photos"][0]["photo_reference"]
        # Key nicht in die JSON schreiben, nur den Platzhalter
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=600&photoreference={ref}&key={API_KEY_PLACEHOLDER}"
    return None


def crawl_city(city):
    print(f"Bearbeite {city} ...")
    lat, lon = get_city_location(city)
    result = {"city": city, "category_pois": {}}
    for kat_label, kat_google in KATEGORIEN.items():
        print(f"  Kategorie: {kat_label}")
        pois = get_places_for_category(city, lat, lon, kat_google, top_n=TOP_N)
        result["category_pois"][kat_label] = pois
    # Speichern
    fname = f"data/{city.lower().replace(' ', '_')}.json"
    os.makedirs("input", exist_ok=True)
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  -> Gespeichert in {fname}")


if __name__ == "__main__":
    for city in STADTLISTE:
        try:
            crawl_city(city)
        except Exception as e:
            print(f"Fehler bei {city}: {e}")
            continue
