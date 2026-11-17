from __future__ import annotations

import cv2

from src.config import parse_camera_source


def open_camera(source: str | int) -> cv2.VideoCapture:
    camera_source = parse_camera_source(source)
    capture = cv2.VideoCapture(camera_source)

    if not capture.isOpened():
        raise RuntimeError(
            "Unable to open camera source. Use 0 for laptop webcam, "
            "or pass a mobile IP camera URL such as http://PHONE_IP:8080/video."
        )

    return capture
