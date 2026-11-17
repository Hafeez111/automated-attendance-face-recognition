from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
KNOWN_FACES_DIR = DATA_DIR / "known_faces"
ATTENDANCE_DIR = DATA_DIR / "attendance"
REPORTS_DIR = DATA_DIR / "reports"
ENCODINGS_PATH = DATA_DIR / "face_encodings.pkl"

FRAME_RESIZE_SCALE = float(os.getenv("FRAME_RESIZE_SCALE", "0.25"))
FACE_MATCH_TOLERANCE = float(os.getenv("FACE_MATCH_TOLERANCE", "0.50"))
FACE_DETECTION_MODEL = os.getenv("FACE_DETECTION_MODEL", "hog")
DEFAULT_SAMPLE_COUNT = int(os.getenv("DEFAULT_SAMPLE_COUNT", "20"))


def ensure_directories() -> None:
    for directory in (DATA_DIR, KNOWN_FACES_DIR, ATTENDANCE_DIR, REPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def parse_camera_source(source: str | int) -> str | int:
    if isinstance(source, int):
        return source

    value = str(source).strip()
    if value.isdigit():
        return int(value)
    return value
