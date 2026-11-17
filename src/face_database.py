from __future__ import annotations

import argparse
import pickle
from dataclasses import dataclass
from pathlib import Path

import cv2
import face_recognition

from src.config import ENCODINGS_PATH, FACE_DETECTION_MODEL, KNOWN_FACES_DIR, ensure_directories


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class KnownFace:
    student_id: str
    name: str
    image_path: str
    encoding: list[float]


def parse_student_folder(folder_name: str) -> tuple[str, str]:
    if "_" not in folder_name:
        return folder_name, folder_name.replace("-", " ").title()

    student_id, raw_name = folder_name.split("_", 1)
    return student_id, raw_name.replace("_", " ").replace("-", " ").title()


def iter_face_images(known_faces_dir: Path = KNOWN_FACES_DIR) -> list[Path]:
    if not known_faces_dir.exists():
        return []

    return sorted(
        path
        for path in known_faces_dir.glob("*/*")
        if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )


def build_face_database() -> list[KnownFace]:
    ensure_directories()
    known_faces: list[KnownFace] = []
    image_paths = iter_face_images()

    if not image_paths:
        raise RuntimeError(
            f"No face images found in {KNOWN_FACES_DIR}. "
            "Run python -m src.enroll first."
        )

    for image_path in image_paths:
        student_id, name = parse_student_folder(image_path.parent.name)
        image_bgr = cv2.imread(str(image_path))

        if image_bgr is None:
            print(f"Skipped unreadable image: {image_path}")
            continue

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(image_rgb, model=FACE_DETECTION_MODEL)

        if not locations:
            print(f"Skipped image with no detected face: {image_path}")
            continue

        encodings = face_recognition.face_encodings(image_rgb, known_face_locations=locations)
        if not encodings:
            print(f"Skipped image with no usable face encoding: {image_path}")
            continue

        known_faces.append(
            KnownFace(
                student_id=student_id,
                name=name,
                image_path=str(image_path),
                encoding=encodings[0].tolist(),
            )
        )

    if not known_faces:
        raise RuntimeError("No valid face encodings could be generated.")

    with ENCODINGS_PATH.open("wb") as file:
        pickle.dump(known_faces, file)

    return known_faces


def load_face_database() -> list[KnownFace]:
    if not ENCODINGS_PATH.exists():
        raise RuntimeError(
            f"Face database not found at {ENCODINGS_PATH}. "
            "Run python -m src.face_database first."
        )

    with ENCODINGS_PATH.open("rb") as file:
        return pickle.load(file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build face encodings from enrolled images.")
    parser.parse_args()

    known_faces = build_face_database()
    unique_students = {face.student_id for face in known_faces}
    print(f"Created {len(known_faces)} encodings for {len(unique_students)} students.")
    print(f"Saved database to {ENCODINGS_PATH}")


if __name__ == "__main__":
    main()
