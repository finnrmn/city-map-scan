import sys

import cv2
import os

from app.backend.setups.download_streets_from_osm import cities

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.backend.src import run_ocr_multi  # ocr_process
from app.backend.src import run_preprocessing  # preprocess
from app.backend.src import run_postprocessing  # post_safe

output_dir = "output"


def run_pipeline(image_path, debug=False):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ Bild nicht gefunden: {image_path}")

    filename = os.path.splitext(os.path.basename(image_path))[0]
    image = cv2.imread(image_path)

    print(f"\nStarte ocr pipeline")

    print(f"\n▶️ Run preprocessing ")
    preprocessed_image = run_preprocessing(filename, image, debug=debug)
    print(f"✅ finished preprocessing ")

    print(f"\n▶️ Run ocr detection")
    ocr_results, ocr_results_vis_img = run_ocr_multi(filename, image, preprocessed_image, debug=debug)
    print(f"✅ Finished ocr detection")

    print(f"\n▶️ Run post processing")
    result = run_postprocessing(ocr_results, debug=debug)

    if result is None:
        raise ValueError("❌ Postprocessing failed")

    guessed_city, city_hits, used_osm = result
    city_backup = None
    if guessed_city:
        print(f"\n Detected city: {guessed_city}")
    else:
        print(f"\n No city detected, possible results: {city_hits}")
        city_backup = no_city_backup(city_hits)


    return {
        "city": guessed_city or "Unklar",
        "city_backup": city_backup,
        "city_hits": city_hits,
        "visualizer_image": ocr_results_vis_img,
        "used_osm": used_osm
    }

def no_city_backup(city_hits):
    max_unique = max(city['unique_count'] for city in city_hits.values())

    cities_with_max_unique = {
        city: data for city, data in city_hits.items()
        if data['unique_count'] == max_unique
    }

    max_count = max(data["count"] for data in cities_with_max_unique.values())

    top_cities = [
        city for city, data in cities_with_max_unique.items()
        if data['count'] == max_count
    ]

    return top_cities


