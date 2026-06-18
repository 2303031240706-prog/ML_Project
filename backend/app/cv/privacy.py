import cv2
import numpy as np


def blur_face_regions(frame: np.ndarray, face_boxes: list[tuple[int, int, int, int]]) -> np.ndarray:
    protected = frame.copy()
    for x, y, width, height in face_boxes:
        region = protected[y : y + height, x : x + width]
        if region.size == 0:
            continue
        protected[y : y + height, x : x + width] = cv2.GaussianBlur(region, (31, 31), 0)
    return protected

