from __future__ import annotations

import argparse
from collections import Counter

import cv2
import face_recognition
import numpy as np

from src.attendance_store import AttendanceStore
from src.camera import open_camera
from src.config import FACE_DETECTION_MODEL, FACE_MATCH_TOLERANCE, FRAME_RESIZE_SCALE
from src.face_database import KnownFace, load_face_database


def best_match(face_encoding: np.ndarray, known_faces: list[KnownFace]) -> tuple[KnownFace | None, float]:
    known_encodings = [np.array(face.encoding) for face in known_faces]
    distances = face_recognition.face_distance(known_encodings, face_encoding)

    if len(distances) == 0:
        return None, 1.0

    best_index = int(np.argmin(distances))
    best_distance = float(distances[best_index])

    if best_distance <= FACE_MATCH_TOLERANCE:
        return known_faces[best_index], best_distance

    return None, best_distance


def run_attendance(source: str) -> None:
    known_faces = load_face_database()
    attendance_store = AttendanceStore()
    capture = open_camera(source)
    already_present = attendance_store.read_student_ids()
    recognition_counter: Counter[str] = Counter()

    print("Attendance started. Press q to stop.")

    try:
        while True:
            success, frame = capture.read()
            if not success:
                raise RuntimeError("Unable to read frame from camera.")

            small_frame = cv2.resize(frame, (0, 0), fx=FRAME_RESIZE_SCALE, fy=FRAME_RESIZE_SCALE)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb_small_frame, model=FACE_DETECTION_MODEL)
            encodings = face_recognition.face_encodings(rgb_small_frame, locations)

            for location, encoding in zip(locations, encodings):
                match, distance = best_match(encoding, known_faces)
                top, right, bottom, left = location
                top = int(top / FRAME_RESIZE_SCALE)
                right = int(right / FRAME_RESIZE_SCALE)
                bottom = int(bottom / FRAME_RESIZE_SCALE)
                left = int(left / FRAME_RESIZE_SCALE)

                if match is None:
                    label = f"Unknown ({distance:.2f})"
                    color = (0, 0, 255)
                else:
                    recognition_counter[match.student_id] += 1
                    stable_match = recognition_counter[match.student_id] >= 3

                    if stable_match and match.student_id not in already_present:
                        marked = attendance_store.mark_present(match.student_id, match.name)
                        if marked:
                            already_present.add(match.student_id)
                            print(f"Marked present: {match.student_id} - {match.name}")

                    status = "Present" if match.student_id in already_present else "Recognizing"
                    label = f"{match.name} - {status}"
                    color = (0, 180, 0)

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(
                    frame,
                    label,
                    (left + 6, bottom - 10),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.6,
                    (255, 255, 255),
                    1,
                )

            cv2.imshow("Automated Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real-time face recognition attendance.")
    parser.add_argument("--source", default="0", help="Camera index or mobile camera URL.")
    args = parser.parse_args()

    run_attendance(args.source)


if __name__ == "__main__":
    main()
