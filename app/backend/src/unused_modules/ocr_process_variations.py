import cv2
import easyocr
import os

from ..preprocess import run_preprocessing # preprocess
from ..visualizer import draw_results # visualizer

output_dir = "../../output"

def run_ocr(image_path, lang="de", clahe_variant="soft", scale=2.0, debug=False):
    """OCR auf vollständigem Bild mit optionalem Debug-Save"""
    filename = os.path.splitext(os.path.basename(image_path))[0]
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Bild konnte nicht geladen werden: {image_path}")

    clahe_img = run_preprocessing(image_path, clahe_variant=clahe_variant, debug=debug)

    resized = cv2.resize(clahe_img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    vis_base = cv2.resize(image, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    reader = easyocr.Reader([lang], gpu=False)
    results = reader.readtext(resized, paragraph=False)

    if debug:
        os.makedirs(output_dir, exist_ok=True)
        img_out = os.path.join(output_dir, f"visualizer_{filename}_run_ocr_scale{int(scale)}.jpg")
        txt_out = os.path.join(output_dir, f"detect_{filename}_run_ocr_scale{int(scale)}.txt")

        draw_results(vis_base, results, img_out)

        with open(txt_out, "w", encoding="utf-8") as f:
            for i, (_, text, score) in enumerate(results):
                line = f"{i+1:02d}. '{text}'  ({score:.2f})"
                print(line)
                f.write(line + "\n")

        print(f"✅ OCR abgeschlossen (Debug-Mode): {txt_out}")

    structured = []
    for bbox, text, score in results:
        structured.append({
            "text": text,
            "score": float(score),
            "box": [[float(x), float(y)] for (x, y) in bbox],
            "source": "full_image"
        })

    return structured

def run_ocr_fast(filename, original_img, clahe_img, lang="de", scale=2.0, debug=False):
    """Schnelle OCR-Variante, zugeschnitten auf Straßenschilder."""

    image = cv2.resize(clahe_img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    vis_base = cv2.resize(original_img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Kanten hervorheben und Regionen mit hoher Dichte extrahieren
    grad = cv2.morphologyEx(image, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    reader = easyocr.Reader([lang], gpu=False)
    results = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < 20 or h < 10:
            continue
        cropped = image[y:y + h, x:x + w]
        for bbox, text, score in reader.readtext(cropped, paragraph=False):
            adjusted_box = [[float(pt[0] + x), float(pt[1] + y)] for pt in bbox]
            results.append({
                "text": text,
                "score": float(score),
                "box": adjusted_box,
                "source": "fast"
            })

    if debug:
        os.makedirs(output_dir, exist_ok=True)
        vis_out = os.path.join(output_dir, f"{filename}_fast_visualizer.jpg")
        draw_results(vis_base, [
            (r["box"], r["text"], r["score"]) for r in results
        ], vis_out)

        debug_line = " | ".join([f"'{r['text']}' ({r['score']:.2f})" for r in results])
        print(f"\n    2.1    Fast-OCR words: {debug_line}")

    return results





