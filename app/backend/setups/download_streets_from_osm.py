import os

import requests
import json
import time

# Liste deutscher Städte mit >150.000 Einwohnern (kann erweitert werden)
cities = [
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


# Overpass Query Template
def build_query(city_name):
    return f"""
    [out:json][timeout:60];
    area["name"="{city_name}"]->.searchArea;
    (
      way["highway"]["name"](area.searchArea);
    );
    out tags;
    """


def fetch_street_names(city):
    url = "https://overpass-api.de/api/interpreter"
    query = build_query(city)
    print(f"📡 Anfrage an Overpass API für: {city}")
    response = requests.post(url, data={"input": query})

    if response.status_code != 200:
        print(f"❌ Fehler bei {city}: {response.status_code}")
        return []

    data = response.json()
    streets = set()

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if name:
            streets.add(name)

    print(f"✅ {city}: {len(streets)} Straßennamen gefunden")
    return list(streets)


def build_street_database():
    street_data = {}

    for city in cities:
        try:
            street_names = fetch_street_names(city)
            street_data[city] = street_names
            time.sleep(1)  # Delay für Fair Use
        except Exception as e:
            print(f"⚠️ Fehler bei {city}: {e}")

    current_file = os.path.abspath(__file__)
    backend_dir = os.path.dirname(os.path.dirname(current_file))
    json_file_path = os.path.join(backend_dir, "files", "de_streets.json")
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(street_data, f, indent=2, ensure_ascii=False)

    print("\n📁 Datei gespeichert als 'de_streets.json'")


if __name__ == "__main__":
    build_street_database()
