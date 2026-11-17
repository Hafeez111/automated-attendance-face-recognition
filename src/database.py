from __future__ import annotations

import sqlite3
from datetime import datetime

from src.config import DATA_DIR, ensure_directories


DATABASE_PATH = DATA_DIR / "attendance.db"


def connection() -> sqlite3.Connection:
    ensure_directories()
    database = sqlite3.connect(DATABASE_PATH)
    database.row_factory = sqlite3.Row
    return database


def initialize_database() -> None:
    with connection() as database:
        database.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                roll_number TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                branch TEXT NOT NULL,
                section TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_number TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                attendance_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Present',
                UNIQUE(roll_number, attendance_date),
                FOREIGN KEY(roll_number) REFERENCES students(roll_number)
            );
            """
        )


def add_student(roll_number: str, full_name: str, branch: str, section: str) -> None:
    with connection() as database:
        database.execute(
            "INSERT INTO students (roll_number, full_name, branch, section, created_at) VALUES (?, ?, ?, ?, ?)",
            (roll_number, full_name, branch, section, datetime.now().isoformat()),
        )


def all_students() -> list[sqlite3.Row]:
    with connection() as database:
        return database.execute("SELECT * FROM students ORDER BY roll_number").fetchall()


def today_attendance(date_text: str) -> list[sqlite3.Row]:
    with connection() as database:
        return database.execute(
            """SELECT attendance.roll_number, students.full_name, students.branch, students.section,
                      attendance.attendance_date, attendance.attendance_time, attendance.status
               FROM attendance JOIN students ON students.roll_number = attendance.roll_number
               WHERE attendance.attendance_date = ? ORDER BY attendance.attendance_time DESC""",
            (date_text,),
        ).fetchall()


def mark_present(roll_number: str, date_text: str, time_text: str) -> bool:
    try:
        with connection() as database:
            database.execute(
                "INSERT INTO attendance (roll_number, attendance_date, attendance_time) VALUES (?, ?, ?)",
                (roll_number, date_text, time_text),
            )
        return True
    except sqlite3.IntegrityError:
        return False
