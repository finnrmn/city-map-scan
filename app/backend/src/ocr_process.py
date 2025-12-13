import cv2
import easyocr
import os

from app.backend.src.visualizer import (draw_results) # visualizer

output_dir = "../../output"

def run_ocr_multi(filename, image, preprocessed_image, lang="de", scale=2.0, tile_size=512, stride=256, debug=False):
    """OCR auf vollständigem Bild + Tiles, optional Speicherung"""

    image = cv2.resize(preprocessed_image, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    vis_base = cv2.resize(image, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    height, width = image.shape
    reader = easyocr.Reader([lang], gpu=False)
    all_results = []

    def run_and_collect(cropped, x_offset, y_offset, tag):
        results = reader.readtext(cropped, paragraph=False)
        for bbox, text, score in results:
            adjusted_box = [[float(pt[0] + x_offset), float(pt[1] + y_offset)] for pt in bbox]
            all_results.append({
                "text": text,
                "score": float(score),
                "box": adjusted_box,
                "source": tag
            })

    run_and_collect(image, 0, 0, "full_image")

    for y in range(0, height - tile_size + 1, stride):
        for x in range(0, width - tile_size + 1, stride):
            tile = image[y:y + tile_size, x:x + tile_size]
            run_and_collect(tile, x, y, f"tile_{x}_{y}")

    vis_out = os.path.join(output_dir, f"{filename}_ocr_visualizer.jpg") if debug else None

    vis_image = draw_results(vis_base, [
        (r["box"], r["text"], r["score"]) for r in all_results
    ], out_path=vis_out, debug=debug)

    debug_line = " | ".join([f"'{r['text']}' ({r['score']:.2f})" for r in all_results])
    print(f"Ocr founded strings: \n {debug_line}")
    #if debug:
     #   print("IN DEBUG")
      #  json_out = os.path.join(output_dir, f"{filename}_detect.json")
       # with open(json_out, "w", encoding="utf-8") as f_json:
        #    json.dump(all_results, f_json, indent=2)
    print("OFF")
    return all_results, vis_image




