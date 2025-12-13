import requests
import time

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OSM_POI_QUERIES = [
    ('tourism', 'attraction'),
    ('tourism', 'museum'),
    ('amenity', 'cinema'),
    ('amenity', 'theatre'),
    ('leisure', 'park'),
    ('place', 'square'),
]
CATEGORY_MAP = {
    'attraction': 'Sehenswürdigkeit',
    'museum': 'Museum',
    'cinema': 'Kino',
    'theatre': 'Theater',
    'park': 'Park',
    'square': 'Platz',
}

BAD_NAMES = {"F", "A", "1", "2", "3", "X", "?"}

def is_good_name(name):
    return name and len(name.strip()) > 2 and name.strip() not in BAD_NAMES

def get_city_bbox(city_name, country="Deutschland"):
    params = {
        'q': f'{city_name}, {country}',
        'format': 'json',
        'limit': 1,
        'addressdetails': 1,
        'countrycodes': 'de',
    }
    r = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": "MeinProjekt-OSM-Abfrage"})
    r.raise_for_status()
    results = r.json()
    if not results:
        raise ValueError(f"Stadt '{city_name}' nicht gefunden!")
    bbox = [float(x) for x in results[0]['boundingbox']]
    display_name = results[0]['display_name']
    center = (float(results[0]['lat']), float(results[0]['lon']))
    return bbox, display_name, center

def build_overpass_query(bbox):
    bbox_str = f"{bbox[0]},{bbox[2]},{bbox[1]},{bbox[3]}"  # minlat,minlon,maxlat,maxlon
    query = "[out:json][timeout:30];(\n"
    for key, value in OSM_POI_QUERIES:
        query += f'  node["{key}"="{value}"]({bbox_str});\n'
        query += f'  way["{key}"="{value}"]({bbox_str});\n'
        query += f'  relation["{key}"="{value}"]({bbox_str});\n'
    query += ");\nout center tags;"
    return query

def query_overpass(query):
    for attempt in range(3):
        resp = requests.post(OVERPASS_URL, data=query, headers={"User-Agent": "MeinProjekt-OSM-Abfrage"})
        if resp.status_code == 429:
            time.sleep(5)
            continue
        resp.raise_for_status()
        return resp.json()
    raise Exception("Overpass API nicht erreichbar.")

def extract_pois(overpass_json):
    pois = []
    seen = set()
    for el in overpass_json.get('elements', []):
        tags = el.get('tags', {})
        name = tags.get('name')
        if not is_good_name(name):
            continue
        if el['type'] == 'node':
            lat, lon = el['lat'], el['lon']
        else:
            lat, lon = el.get('center', {}).get('lat'), el.get('center', {}).get('lon')
        if lat is None or lon is None:
            continue
        key = (name.strip().lower(), round(lat, 5), round(lon, 5))
        if key in seen:
            continue
        seen.add(key)
        category = None
        for k, v in OSM_POI_QUERIES:
            if tags.get(k) == v:
                category = CATEGORY_MAP.get(v, v)
                break
        if not category:
            category = 'Sonstiges'
        pois.append({
            'name': name.strip(),
            'category': category,
            'lat': lat,
            'lon': lon,
            'tags': tags,
        })
    return pois

def group_pois_by_category(pois):
    from collections import defaultdict
    grouped = defaultdict(list)
    for poi in pois:
        grouped[poi['category']].append(poi)
    return dict(grouped)

def get_city_pois(city_name, country="Deutschland", group_by_category=True):
    bbox, display_name, center = get_city_bbox(city_name, country)
    query = build_overpass_query(bbox)
    data = query_overpass(query)
    pois = extract_pois(data)
    if group_by_category:
        return group_pois_by_category(pois), display_name, center
    else:
        return pois, display_name, center

if __name__ == "__main__":
    city = "Darmstadt"
    result, display_name, center = get_city_pois(city)
    print(f"Sehenswürdigkeiten für: {display_name}")
    for category, items in result.items():
        print(f"  {category} ({len(items)})")
        for poi in items[:3]:
            print(f"   - {poi['name']} @ ({poi['lat']}, {poi['lon']})")
        if len(items) > 3:
            print("    ...")

