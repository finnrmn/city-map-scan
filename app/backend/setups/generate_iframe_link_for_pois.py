"""
generate_iframe_links_for_pois.py
===============================

Dieses Skript liest deine POI‑JSON‑Dateien und erzeugt für jeden Eintrag
einen allgemeingültigen Google‑Maps‑Embed‑Link ohne API‑Key.
Die generierten Links verwenden das klassische URL‑Format
`https://www.google.com/maps?q=<lat>,<lon>&z=<zoom>&t=k&hl=de&output=embed`,
wobei `t=k` die Satellitenansicht aktiviert.

im Ausgabeordner gespeichert.

HOW TO RUN:
            python generate_iframe_link_for_pois.py --input-dir ./input --output-dir ./city_pois --zoom 15

"""

import argparse
import json
import os
from typing import Dict, Any


def build_general_iframe_link(lat: float, lon: float, zoom: int = 16) -> str:
    """
    Erzeugt einen Embed‑Link im klassischen Format ohne API‑Key, mit Satellitenansicht.
    Beispiel: https://www.google.com/maps?q=52.520008,13.404954&z=16&t=k&hl=de&output=embed
    """
    return f"https://www.google.com/maps?q={lat},{lon}&z={zoom}&t=k&hl=de&output=embed"


def process_file(input_path: str, output_path: str, zoom: int) -> None:
    """Liest eine JSON‑Datei, fügt jedem POI einen `iframe_link` hinzu und schreibt das Ergebnis."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data: Dict[str, Any] = json.load(f)

    if not isinstance(data, dict) or 'category_pois' not in data:
        print(f"WARNUNG: Datei {input_path} entspricht nicht dem erwarteten Format. Überspringe.")
        return

    for category, pois in data['category_pois'].items():
        for poi in pois:
            lat = poi.get('lat')
            lon = poi.get('lon')
            if lat is None or lon is None:
                continue
            poi['iframe_link'] = build_general_iframe_link(lat, lon, zoom)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"→ {os.path.basename(output_path)} erstellt.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Erzeugt allgemeingültige Google‑Maps‑Embed‑Links ohne API‑Key in der Satellitenansicht.")
    parser.add_argument('--input-dir', required=True, help='Verzeichnis mit Eingabe‑JSON‑Dateien')
    parser.add_argument('--output-dir', required=True, help='Verzeichnis für Ausgabedateien')
    parser.add_argument('--zoom', type=int, default=16, help='Zoom‑Stufe für die Karten (Standard: 16)')
    args = parser.parse_args(argv)

    input_dir = args.input_dir
    output_dir = args.output_dir
    zoom = args.zoom

    if not os.path.isdir(input_dir):
        print(f"Fehler: Eingabeverzeichnis {input_dir} existiert nicht.")
        return 1

    os.makedirs(output_dir, exist_ok=True)

    processed = 0
    for filename in os.listdir(input_dir):
        if not filename.lower().endswith('.json'):
            continue
        input_path = os.path.join(input_dir, filename)
        output_filename = filename
        output_path = os.path.join(output_dir, output_filename)
        process_file(input_path, output_path, zoom)
        processed += 1

    if processed == 0:
        print("Es wurden keine JSON‑Dateien zur Verarbeitung gefunden.")
    else:
        print(f"Fertig: {processed} Datei(en) verarbeitet.")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
