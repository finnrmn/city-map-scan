import os
import json
import re
from collections import defaultdict, Counter

from .osm_resolver import guess_city_from_osm_context # osm_resolver_async_safe_street

BASE_DIR = os.path.dirname(__file__)
REFERENCE_PATH = os.path.join(BASE_DIR, os.pardir, "files", "de_streets.json")

def load_reference_data(path=REFERENCE_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Referenzdatei fehlt: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def early_city_detection(ocr_results, reference):
    safe_words = []

    for word in ocr_results:
        if word.get("score") >= 0.1:
            safe_words.append({
                "text": word["text"],
                "score": word["score"]
            })

    # print(f"Remove low score | {[f'{w['text']} ({w['score']:.2f})' for w in safe_words]}")

    def str_abbreviation_fix(word):
        word = re.sub(r"[\s\-\.]?(str)[\s\-\.]?$", "straße", word, flags=re.IGNORECASE)
        word = re.sub(r"[\s\-\.]?(st)[\s\-\.]?$", "straße", word, flags=re.IGNORECASE)
        return word

    def early_ocr_fixes(word):
        replacements = {
            r"strabe": "straße",
            r"straBe": "straße",
            r"Strabe": "Straße",
            r"plat$": "platz",
            r"plalz$": "platz",
            r"plotz$": "platz",
        }
        for wrong, right in replacements.items():
            word = re.sub(wrong, right, word, flags=re.IGNORECASE)
        return word

    def filter(safe_words):
        cleaned = []
        seen = set()
        EXCLUDE_SINGLE_WORDS = {
            "stadt", "straße", "städte", "tadt", "traße", "platz", "plotz",
            "pla", "latz", "plat", "weg", "eg", "halle"
        }

        for entry in safe_words:
            raw_word = entry["text"]
            word = str_abbreviation_fix(raw_word)
            word = early_ocr_fixes(word)

            # Nur Buchstaben behalten (äöüß auch)
            word = re.sub(r"[^a-zA-ZäöüÄÖÜß\-]", "", word)

            word_lower = word.lower()

            # Länge prüfen nach Bereinigung
            if len(word_lower) >= 4 and word_lower not in EXCLUDE_SINGLE_WORDS:
                if word_lower not in seen:
                    seen.add(word_lower)
                    cleaned.append({
                        "text": word_lower,
                        "score": entry["score"]
                    })

                # Erweiterung für Bindestrich-Ende
                if word_lower.endswith("-"):
                    base = word_lower[:-1]
                    for suffix in ["straße", "platz"]:
                        new_word = base + suffix
                        if new_word not in seen:
                            seen.add(new_word)
                            cleaned.append({
                                "text": new_word,
                                "score": entry["score"]  # Kein Score-Abzug nötig, bleibt gleich
                            })

        return cleaned

    cleaned_safe_words = filter(safe_words)

    print("Apply filter :\n"+[f"{w['text']} ({w['score']:.2f})" for w in cleaned_safe_words].__str__())

    def city_matcher(entries, reference):
        matches = defaultdict(list)
        for entry in entries:
            word = entry["text"]
            for city, streets in reference.items():
                for street in streets:
                    if word == street.strip().lower():
                        matches[city].append(street)
        return matches

    city_dict = city_matcher(cleaned_safe_words, reference)

    def attach_unique_counts(city_dict):
        all_streets = []
        for streets in city_dict.values():
            all_streets.extend(streets)
        street_counter = Counter(all_streets)

        updated = {}
        for city, streets in city_dict.items():
            unique_count = sum(1 for s in streets if street_counter[s] == 1)
            updated[city] = {
                "count": len(streets),
                "unique_count": unique_count,
                "matches": sorted(set(streets))  # optional: Duplikate entfernen + sortieren
            }
        return updated

    city_dict = attach_unique_counts(city_dict)
    print("Count matches (detailliert):")
    for city, stats in city_dict.items():
        print(f"{city}")
        print(f"  Matches total   : {stats['count']}")
        print(f"  Unique matches  : {stats['unique_count']}")
        print(f"  Streets         : {', '.join(stats['matches'])}")
        print("-" * 40)

    def find_best_city(city_dict):
        counts = {city: data["unique_count"] for city, data in city_dict.items()}
        if not counts:
            return None
        max_count = max(counts.values())
        top = [city for city, count in counts.items() if count == max_count]
        if len(top) == 1:
            return top[0]
        return None

    guessed_city = find_best_city(city_dict)

    matched_streets = set()
    for entries in city_dict.values():
        matched_streets.update(entries["matches"])

    return {
        "city_dict": city_dict,
        "guessed_city": guessed_city,
        "streets": matched_streets,
    }



def run_postprocessing(ocr_results, debug=False):
    print(f"Load reference streets | {REFERENCE_PATH}")
    reference = load_reference_data()
    result = early_city_detection(ocr_results, reference)

    city_dict = result["city_dict"]
    guessed_city = result["guessed_city"]
    streets = result["streets"]

    if guessed_city:
        print(f"Clear city detected")
        return guessed_city, city_dict, False
    else:
        print(f"❌ No clear city detected  | Fallback zum OSM Resolver!")
        print(f"▶️ Run OSM Resolver")
        match_dict = {city: data["matches"] for city, data in city_dict.items()}
        guessed_city = guess_city_from_osm_context(match_dict, streets, debug=debug)

        if guessed_city:
            print(f"✅ Clear city detected")
            return guessed_city, city_dict, True

        print(f" ❌ No City detected from OSM Resolver")

        return None, city_dict, True
