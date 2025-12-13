import asyncio
import re
import math
from typing import Dict, Iterable, List, Optional

import aiohttp
import requests
from geopy.distance import geodesic

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = {"User-Agent": "stadtplan-context-unused_modules/1.0"}


def build_query(city, streets):
    escaped = [re.escape(s) for s in streets if len(s) > 3]
    pattern = "|".join(escaped)
    query = f'''
    [out:json][timeout:25];
    area["name"="{city}"]["boundary"="administrative"]["admin_level"="8"]->.a;
    area["name"="{city}"]["boundary"="administrative"]["admin_level"="6"]->.b;
    area["name"="{city}"]["place"="city"]->.c;
    (.a;.b;.c;)->.searchArea;
    (
      node["name"~"{pattern}", i](area.searchArea);
      way["name"~"{pattern}", i](area.searchArea);
    );
    out center;
    '''
    print(f"\n      📤 Query für {city}:")
    print(query)
    return query


def query_overpass(query):
    try:
        print("\n      🌐 Sende Anfrage an Overpass...")
        response = requests.post(OVERPASS_URL, data={"input": query}, headers=USER_AGENT)
        response.raise_for_status()
        json_data = response.json()
        print(f"      ✅ Overpass-Antwort erhalten: {len(json_data.get('elements', []))} Elemente")
        return json_data.get("elements", [])
    except Exception as e:
        print(f"❌ Overpass-Fehler: {e}")
        return []


async def query_overpass_async(session: aiohttp.ClientSession, query: str) -> List[dict]:
    try:
        print("\n      🌐 Sende Anfrage an Overpass...")
        async with session.post(OVERPASS_URL, data={"input": query}, headers=USER_AGENT) as response:
            response.raise_for_status()
            json_data = await response.json()
            print(
                f"      ✅ Overpass-Antwort erhalten: {len(json_data.get('elements', []))} Elemente"
            )
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
    print(f"      🗺️ Extrahierte Koordinaten: {len(coords)}")
    return coords


def score_cluster(coords):
    if len(coords) < 2:
        return float("inf")

    total = 0
    count = 0
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            total += geodesic(coords[i], coords[j]).meters
            count += 1

    avg_dist = total / count
    bonus = math.log(len(coords) + 1)
    return avg_dist / bonus


async def _process_city(session: aiohttp.ClientSession, city: str, streets: Iterable[str], fuzzy_scores: Optional[Dict[str, int]]):
    query = build_query(city, streets)
    elements = await query_overpass_async(session, query)
    coords = extract_coordinates(elements)

    if len(coords) < 2:
        return city, None

    cluster_score = score_cluster(coords)
    fuzzy_score = fuzzy_scores.get(city, 0) if fuzzy_scores else len(streets)
    weighted_score = cluster_score / (fuzzy_score + 1) ** 0.5

    return city, {
        "cluster": cluster_score,
        "fuzzy": fuzzy_score,
        "points": len(coords),
        "weighted": weighted_score,
    }


async def guess_city_from_osm_context_async(match_dict: Dict[str, Iterable[str]], fuzzy_scores: Optional[Dict[str, int]] = None, debug: bool = False) -> Optional[str]:
    scores: Dict[str, float] = {}
    city_debug: Dict[str, Dict[str, float]] = {}
    if debug:
        print(f"\n    3.4     OSM API Anfragen:")

    async with aiohttp.ClientSession() as session:
        tasks = [
            _process_city(session, city, streets, fuzzy_scores)
            for city, streets in match_dict.items()
            if streets
        ]
        results = await asyncio.gather(*tasks)

    for city, stats in results:
        if stats is None:
            continue
        scores[city] = stats["weighted"]
        city_debug[city] = stats

    if not scores:
        return None

    best_city = min(scores.items(), key=lambda x: x[1])[0]

    if debug:
        print("\n    3.5     Stadtvergleich:")
        for city, stats in sorted(city_debug.items(), key=lambda x: x[1]["weighted"]):
            print(
                f"      - {city}: cluster={stats['cluster']:.1f}, fuzzy={stats['fuzzy']}, coords={stats['points']}, score={stats['weighted']:.2f}")

    return best_city


def guess_city_from_osm_context(match_dict, fuzzy_scores=None, debug=False):
    return asyncio.run(guess_city_from_osm_context_async(match_dict, fuzzy_scores, debug))
