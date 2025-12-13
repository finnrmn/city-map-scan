import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.backend import run_pipeline # ocr_pipeline

BASE_DIR = os.path.dirname(__file__)
IMAGE_PATH = os.path.join(BASE_DIR, os.pardir,"app","backend", "files", "da_2.png")

def main():
    result = run_pipeline(IMAGE_PATH)

if __name__ == "__main__":
    main()
