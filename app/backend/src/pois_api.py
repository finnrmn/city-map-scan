import json
import os
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

# Static POI loader; no external API calls.

DATA_DIR = Path(__file__).resolve().parents[1] / "files" / "city_pois"
MAX_ITEMS_PER_CATEGORY = 12

# The static files only contain a placeholder instead of the Google API key;
# the real key is read from app/backend/setups/.env (not committed).
load_dotenv(Path(__file__).resolve().parents[1] / "setups" / ".env")
API_KEY_PLACEHOLDER = "{GOOGLE_API_KEY}"


def _inject_api_key(url: str | None) -> str | None:
    if not url:
        return url
    return url.replace(API_KEY_PLACEHOLDER, os.getenv("GOOGLE_API_KEY", ""))


def _city_to_filename(city: str) -> str:
    """Build the expected filename (lowercase, spaces/hyphens -> underscore)."""
    return city.strip().lower().replace(" ", "_").replace("-", "_")


def _map_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    mapped = []
    for item in entries:
        mapped.append({
            "name": item.get("name"),
            "beschreibung": item.get("beschreibung", ""),
            # Preserve any provided photo URL (static files contain Google photo links)
            "photo_url": _inject_api_key(item.get("photo_url") or item.get("foto_url")),
            "iframe_link": _inject_api_key(item.get("iframe_link") or item.get("embed_url")),
        })
    return mapped


def normalize_static_city_data(
    raw_data: Dict[str, Any],
    fallback_city: str = "",
    max_items: int = MAX_ITEMS_PER_CATEGORY,
) -> Dict[str, Any]:
    """
    Normalize legacy/static POI files to the format expected by the frontend.
    """
    categories = raw_data.get("category_pois", {}) or raw_data.get("pois_category", {})

    def collect(keys):
        merged = []
        for key in keys:
            if key in categories:
                merged.extend(_map_entries(categories.get(key, [])))
        return merged[:max_items]

    pois = collect(["Sehenswürdigkeit", "Museum", "Kirche", "Theater", "Platz"])
    fun = collect(["Park", "Kino"])
    restaurants = collect(["Restaurants", "Restaurant", "restaurants"])

    # Fallback: if categories don't match, flatten everything into pois
    if not (pois or fun or restaurants) and categories:
        for entries in categories.values():
            pois.extend(_map_entries(entries))
        pois = pois[:max_items]

    return {
        "city_name": raw_data.get("city_name") or raw_data.get("city") or fallback_city,
        "city_iframe": raw_data.get("city_iframe"),
        "pois_category": {
            "pois": pois,
            "fun": fun,
            "restaurants": restaurants,
        },
    }


def get_places_by_category(city: str, data_dir: Path | str = DATA_DIR) -> Dict[str, Any]:
    """
    Load POIs for a city from the static backend files.
    """
    base_dir = Path(data_dir)
    file_path = base_dir / f"{_city_to_filename(city)}_pois.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Keine statischen POI-Daten gefunden: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    return normalize_static_city_data(raw_data, fallback_city=city)


if __name__ == "__main__":
    # Quick manual check: python -m app.backend.src.pois_api
    sample = get_places_by_category("Berlin")
    print(json.dumps(sample, ensure_ascii=False, indent=2))
