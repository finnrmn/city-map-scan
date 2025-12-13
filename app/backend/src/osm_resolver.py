import asyncio
import re
import aiohttp
from typing import Dict, Iterable, List, Optional
from geopy.distance import geodesic

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = {"User-Agent": "stadtplan-context-unused_modules/1.0"}

def build_query(city, streets):
    escaped = [re.escape(s) for s in streets if len(s) > 3]
    pattern = "|".join(escaped)
    query = f'''
    [out:json][timeout:25];
    area["name"="{city}"]["boundary"="administrative"]->.a;
    (
      node["name"~"{pattern}", i](area.a);
      way["name"~"{pattern}", i](area.a);
    );
    out center;
    '''
    print(f"\n 📤 Query für {city}:")
    print(query)
    return query

async def query_overpass_async(session: aiohttp.ClientSession, query: str) -> List[dict]:
    try:
        print(" 🌐 Sende Anfrage an Overpass...")
        async with session.post(OVERPASS_URL, data={"input": query}, headers=USER_AGENT) as response:
            response.raise_for_status()
            json_data = await response.json()
            return json_data.get("elements", [])
    except Exception as e:
        print(f"❌ Overpass-Fehler: {e}")
        return []

def extract_coordinates(elements):
    coords = []
    for el in elements:
        if el.get("lat") and el.get("lon"):
            coords.append((el["lat"], el["lon"]))
        elif el.get("center"):
            coords.append((el["center"]["lat"], el["center"]["lon"]))
    return coords

def central_density_score(coords, city_name: str, detected_words: List[str]) -> float:
    if len(coords) < 2:
        return float("inf")

    # 1. Berechne geometrisches Zentrum
    lat_avg = sum(c[0] for c in coords) / len(coords)
    lon_avg = sum(c[1] for c in coords) / len(coords)
    center = (lat_avg, lon_avg)

    # 2. Punkte im Radius (500m)
    radius = 500  # Meter
    close_points = sum(1 for c in coords if geodesic(center, c).meters <= radius)

    # 3. Grundscore
    base_score = -close_points

    # 4. Bonus bei erkannter Stadt im OCR
    if city_name.lower() in [w.lower() for w in detected_words]:
        base_score -= 2

    return base_score

async def _process_city(session: aiohttp.ClientSession, city: str, streets: Iterable[str], detected_words: List[str]):
    if len(streets) <= 1:
        return city, None

    query = build_query(city, streets)
    elements = await query_overpass_async(session, query)
    coords = extract_coordinates(elements)

    if len(coords) < 2:
        return city, None

    score = central_density_score(coords, city, detected_words)

    return city, {
        "score": score,
        "points": len(coords),
        "center_coords": coords
    }

async def guess_city_from_osm_context_async(match_dict: Dict[str, Iterable[str]], detected_words: List[str], debug: bool = False) -> Optional[str]:
    valid_cities = {city: streets for city, streets in match_dict.items() if len(streets) > 1}

    if not valid_cities:
        print(f"No valid cities | Amount of streets must be greater then 1")
        return None

    scores: Dict[str, float] = {}
    city_debug: Dict[str, Dict[str, float]] = {}


    async with aiohttp.ClientSession() as session:
        tasks = [_process_city(session, city, streets, detected_words) for city, streets in valid_cities.items()]
        results = await asyncio.gather(*tasks)

    for city, stats in results:
        if stats is None:
            continue
        scores[city] = stats["score"]
        city_debug[city] = stats

    if not scores:
        return None

    best_city = min(scores.items(), key=lambda x: x[1])[0]

    print(f"\nResult OSM Resolver:")
    for city, stats in sorted(city_debug.items(), key=lambda x: x[1]["score"]):
        print(
            f" {city}: coords={stats['points']}, score={stats['score']:.2f}")
    return best_city

def guess_city_from_osm_context(match_dict, detected_words, debug=False):
    return asyncio.run(guess_city_from_osm_context_async(match_dict, detected_words, debug=debug))

