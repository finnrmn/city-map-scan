import os
import json
from glob import glob


from app.backend import run_pipeline # ocr_pipeline

city_map = {
    "da": "Darmstadt",
    "ber": "Berlin",
    "ham": "Hamburg",
    "mue": "München",
    "koe": "Köln",
    "fm": "Frankfurt am Main",
    "stu": "Stuttgart",
    "due": "Düsseldorf",
    "do": "Dortmund",
    "es": "Essen",
    "le": "Leipzig",
    "bre": "Bremen",
    "dre": "Dresden",
    "han": "Hannover",
    "nue": "Nürnberg",
    "dui": "Duisburg"
}

def main():
    input_dir = "../app/backend/files"
    output_dir = "../app/backend/output"
    os.makedirs(output_dir, exist_ok=True)

    image_files = sorted(glob(os.path.join(input_dir, "*.png")))

    all_results = []
    summary = {
        "correct": 0,
        "incorrect": 0,
        "unclear": 0,
        "osm_used": 0
    }

    for image_path in image_files:
        filename = os.path.basename(image_path)
        prefix = filename.split("_")[0]

        expected_city = city_map.get(prefix)
        if not expected_city:
            continue  # Datei mit unbekanntem Prefix überspringen

        try:
            guessed_city, _, used_osm = run_pipeline(image_path, debug=False)
        except Exception:
            guessed_city = "Fehler"
            used_osm = False

        # Ergebnis speichern
        result_entry = {
            "image": filename,
            "expected": expected_city,
            "detected": guessed_city,
            "used_osm": used_osm
        }
        all_results.append(result_entry)

        # Statistik aktualisieren
        if used_osm:
            summary["osm_used"] += 1

        if guessed_city in [None, "Unklar", "Fehler"]:
            summary["unclear"] += 1
        elif guessed_city == expected_city:
            summary["correct"] += 1
        else:
            summary["incorrect"] += 1

    # JSON zusammenbauen
    output_data = {
        "results": all_results,
        "summary": summary
    }

    with open(os.path.join(output_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
