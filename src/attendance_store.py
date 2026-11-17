from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.config import ATTENDANCE_DIR, ensure_directories


@dataclass(frozen=True)
class AttendanceRecord:
    student_id: str
    name: str
    date: str
    time: str
    status: str = "Present"


class AttendanceStore:
    def __init__(self, attendance_dir: Path = ATTENDANCE_DIR) -> None:
        ensure_directories()
        self.attendance_dir = attendance_dir

    def file_for_date(self, date_value: str | None = None) -> Path:
        date_text = date_value or datetime.now().strftime("%Y-%m-%d")
        return self.attendance_dir / f"attendance_{date_text}.csv"

    def read_student_ids(self, date_value: str | None = None) -> set[str]:
        attendance_file = self.file_for_date(date_value)
        if not attendance_file.exists():
            return set()

        with attendance_file.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return {row["student_id"] for row in reader if row.get("student_id")}

    def mark_present(self, student_id: str, name: str) -> bool:
        now = datetime.now()
        date_text = now.strftime("%Y-%m-%d")
        time_text = now.strftime("%H:%M:%S")

        if student_id in self.read_student_ids(date_text):
            return False

        attendance_file = self.file_for_date(date_text)
        is_new_file = not attendance_file.exists()
        record = AttendanceRecord(
            student_id=student_id,
            name=name,
            date=date_text,
            time=time_text,
        )

        with attendance_file.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["student_id", "name", "date", "time", "status"],
            )
            if is_new_file:
                writer.writeheader()
            writer.writerow(record.__dict__)

        return True
