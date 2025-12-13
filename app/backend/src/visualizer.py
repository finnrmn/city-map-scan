import cv2

def draw_results(image, results, out_path=None, debug=False):
    # Kopiere das Bild, um das Original nicht zu überschreiben
    output_image = image.copy()

    for bbox, text, score in results:
        top_left = tuple(map(int, bbox[0]))
        bottom_right = tuple(map(int, bbox[2]))
        cv2.rectangle(output_image, top_left, bottom_right, (0, 0, 255), 2)
        cv2.putText(output_image, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # Wenn debug=True und ein Pfad übergeben wurde, speichern
    if debug and out_path:
        cv2.imwrite(out_path, output_image)

    return output_image


