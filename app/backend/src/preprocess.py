# ocr/preprocess.py
import cv2
import os

output_dir = "../../output"


def to_grayscale(image):
    """Konvertiert ein Farbbild in Graustufen"""
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def apply_clahe(image, variant="medium"):
    """
    Wendet adaptive Histogramm-Equalisierung (CLAHE) an.

    * "soft": schwacher Kontrast
    * "medium": Standard (clipLimit=2.0, tileGridSize=(4,4))
    * "strong": starker Kontrast
    """
    if variant == "soft":
        clip = 1.2
        grid = (8, 8)
    elif variant == "strong":
        clip = 3.0
        grid = (2, 2)
    else:
        clip = 2.0
        grid = (4, 4)

    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=grid)
    return clahe.apply(image)


def adaptive_threshold(image, variant="medium"):
    """
    Adaptive Thresholding mit vordefinierten Presets:

    * "soft": blockSize=25, C=7
    * "medium": blockSize=21, C=9
    * "sharp": blockSize=15, C=11
    """
    if variant == "soft":
        bs, c = 25, 7
    elif variant == "sharp":
        bs, c = 15, 11
    else:
        bs, c = 21, 9

    return cv2.adaptiveThreshold(
        image, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        bs, c
    )


def run_preprocessing(filename, image, clahe_variant="soft", debug=False):
    """Wendet Grayscale + CLAHE an und speichert Zwischenbilder"""
    gray = to_grayscale(image)
    print(f"gray scaling")

    clahe_img = apply_clahe(gray, variant=clahe_variant)
    print(f"apply clahe")

    if debug:
        os.makedirs(output_dir, exist_ok=True)
        gray_path = os.path.join(output_dir, f"{filename}_preprocess_gray.png")
        cv2.imwrite(gray_path, gray)
        clahe_path = os.path.join(output_dir, f"{filename}_preprocess_clahe.png")
        cv2.imwrite(clahe_path, clahe_img)
    return clahe_img
