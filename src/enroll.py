from __future__ import annotations

import argparse
import re
from pathlib import Path

import cv2
import face_recognition

from src.camera import open_camera
from src.config import DEFAULT_SAMPLE_COUNT, FACE_DETECTION_MODEL, KNOWN_FACES_DIR, ensure_directories


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    return cleaned.strip("_") or "Student"


def student_directory(student_id: str, name: str) -> Path:
    folder = f"{safe_name(student_id)}_{safe_name(name)}"
    return KNOWN_FACES_DIR / folder


def enroll_student(student_id: str, name: str, source: str, samples: int) -> Path:
    ensure_directories()
    output_dir = student_directory(student_id, name)
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = open_camera(source)
    saved_count = 0

    print("Enrollment started.")
    print("Look at the camera. Press q to stop early.")

    try:
        while saved_count < samples:
            success, frame = capture.read()
            if not success:
                raise RuntimeError("Unable to read frame from camera.")

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_frame, model=FACE_DETECTION_MODEL)

            for top, right, bottom, left in locations[:1]:
                face_crop = frame[top:bottom, left:right]
                if face_crop.size == 0:
                    continue

                saved_count += 1
                image_path = output_dir / f"sample_{saved_count:03d}.jpg"
                cv2.imwrite(str(image_path), face_crop)

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 180, 0), 2)
                cv2.putText(
                    frame,
                    f"Saved {saved_count}/{samples}",
                    (left, max(top - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 180, 0),
                    2,
                )

            cv2.imshow("Enroll Student", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()

    print(f"Saved {saved_count} samples to {output_dir}")
    if saved_count == 0:
        raise RuntimeError("No face samples were captured.")

    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture face samples for one student.")
    parser.add_argument("--id", required=True, help="Student roll number or unique ID.")
    parser.add_argument("--name", required=True, help="Student full name.")
    parser.add_argument("--source", default="0", help="Camera index or mobile camera URL.")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLE_COUNT)
    args = parser.parse_args()

    enroll_student(args.id, args.name, args.source, args.samples)
    print("Next step: run python -m src.face_database")


if __name__ == "__main__":
    main()
