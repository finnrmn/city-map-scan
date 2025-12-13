import json
from collections import defaultdict, Counter

from rapidfuzz import process, fuzz
import os
import re
from app.backend.src.unused_modules import guess_city_from_osm_context # osm_resolver_async_every_street

# Optional: Lade Referenzdaten einmal global
REFERENCE_PATH = os.path.join(os.path.dirname(__file__), "files", "de_streets.json")

# Minimaler Ähnlichkeitsscore für akzeptierte Matches
FUZZY_THRESHOLD = 85
def load_reference_data(path=REFERENCE_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Referenzdatei fehlt: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def pre_fuzzy(ocr_results):
    def preserve_highway_labels(results):
        HIGHWAY_PATTERN = re.compile(r"^[ABLK][\s\-]?\d{1,4}$", re.IGNORECASE)
        preserved = []

        for r in results:
            txt = r.get("text", "")
            txt_norm = txt.replace(" ", "").replace("-", "").upper()
            if HIGHWAY_PATTERN.match(txt):
                preserved.append(txt_norm)  # z. B. "B26"
        return preserved

    def str_abbreviation_fix(word):
        # z. B. "Berliner Str" → "Berliner Straße"
        word = re.sub(r"[\s\-\.]?(str)[\s\-\.]?$", "straße", word, flags=re.IGNORECASE)
        word = re.sub(r"[\s\-\.]?(st)[\s\-\.]?$", "straße", word, flags=re.IGNORECASE)
        return word

    def early_ocr_fixes(word):
        # Häufige OCR-Fehler korrigieren
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

    def filter(words):
        # Einfache Heuristik zur Reinigung
        words = list(set(w.lower() for w in words))

        EXCLUDE_SINGLE_WORDS = {
            "stadt", "straße", "städte", "tadt", "traße", "platz", "plotz", "pla", "latz", "plat", "weg", "eg"
        }

        words = [w for w in words if w not in EXCLUDE_SINGLE_WORDS and len(w) > 3]
        return words

    # 1. Sammle Wörter mit Score ≥ 0.6
    raw_words = [r["text"] for r in ocr_results if r.get("score", 0) >= 0.6]

    # 2. Label: B26, L312, A5, ...
    highway_labels = preserve_highway_labels(ocr_results)

    # 3. OCR-Fixes & Abkürzungsfixes anwenden
    cleaned_words = []
    for w in raw_words:
        w = str_abbreviation_fix(w)
        w = early_ocr_fixes(w)
        cleaned_words.append(w)

    # 4. Filter + Cleanup
    final_words = filter(cleaned_words)

    # 5. Highways am Ende wieder hinzufügen
    final_words.extend(highway_labels)

    return final_words



def fuzzy_match(word, street_dict):
    results = []
    norm_word = word

    for city, street_list in street_dict.items():
        if not street_list:
            continue

        # Exakter Match?
        if norm_word.lower() in (s.lower() for s in street_list):
            results.append((city, norm_word, 100))
            continue

        # Fuzzy Top-N Matches durchgehen
        matches = process.extract(norm_word, street_list, scorer=fuzz.ratio, limit=5)
        for match, score, _ in matches:
            if score >= FUZZY_THRESHOLD:
                results.append((city, match, score))

    return results



def run_postprocessing(ocr_results, debug=False):
    # Lade Referenzdaten
    reference = load_reference_data()
    words = pre_fuzzy(ocr_results)
    if debug:
        print(f"\n    3.1    OCR words (gefiltert): {words}")

    # Stadt-Match zählen
    city_hits = {}
    match_dict = {}

    if debug:
        print(f"\n    3.2    Run fuzzy match:\n")
    for word in words:
        matches = fuzzy_match(word, reference)
        for city, matched_name, score in matches:
            city_hits[city] = city_hits.get(city, 0) + 1
            match_dict.setdefault(city, []).append(matched_name)
            if debug:
                print(f"      '{word}' ➝ '{matched_name}' ({score}%) in {city}")

    if debug:
        print("\n    3.3     Stadtzählung:\n")
        for city, count in sorted(city_hits.items(), key=lambda x: -x[1]):
            print(f"      {city}: {count} Treffer")
    print(f"[DEBUG] match_dict: {match_dict}")
    print(f"[DEBUG] city_hits: {city_hits}")

    guessed_city = guess_city_from_osm_context(match_dict, city_hits, debug=debug)
    if guessed_city:
        print(f" => Stadt laut OSM-CLuster: {guessed_city}")

    if guessed_city is None:
        return None
    return guessed_city, city_hits

