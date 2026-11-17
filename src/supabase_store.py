from __future__ import annotations

import os
from datetime import datetime

from supabase import Client, create_client

from src.face_database import KnownFace


BUCKET_NAME = "student-faces"


def is_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SECRET_KEY"))


class SupabaseStore:
    def __init__(self) -> None:
        url = os.getenv("SUPABASE_URL")
        secret_key = os.getenv("SUPABASE_SECRET_KEY")
        if not url or not secret_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY must be configured.")
        self.client: Client = create_client(url, secret_key)

    def all_students(self) -> list[dict]:
        return self.client.table("students").select("*").order("roll_number").execute().data

    def add_student(
        self,
        roll_number: str,
        full_name: str,
        branch: str,
        section: str,
        encodings: list[list[float]],
        photos: list[tuple[str, bytes, str]],
    ) -> None:
        self.client.table("students").insert(
            {
                "roll_number": roll_number,
                "full_name": full_name,
                "branch": branch,
                "section": section,
            }
        ).execute()

        for index, (filename, contents, content_type) in enumerate(photos, start=1):
            extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
            object_path = f"{roll_number}/sample_{index:03d}.{extension}"
            self.client.storage.from_(BUCKET_NAME).upload(
                object_path,
                contents,
                file_options={"content-type": content_type, "upsert": "false"},
            )

        rows = [
            {"roll_number": roll_number, "encoding": encoding}
            for encoding in encodings
        ]
        self.client.table("face_encodings").insert(rows).execute()

    def known_faces(self) -> list[KnownFace]:
        rows = (
            self.client.table("face_encodings")
            .select("roll_number, encoding, students(full_name)")
            .execute()
            .data
        )
        return [
            KnownFace(
                student_id=row["roll_number"],
                name=row["students"]["full_name"],
                image_path="supabase-storage",
                encoding=row["encoding"],
            )
            for row in rows
        ]

    def mark_present(self, roll_number: str, when: datetime) -> bool:
        response = (
            self.client.table("attendance")
            .upsert(
                {
                    "roll_number": roll_number,
                    "attendance_date": when.strftime("%Y-%m-%d"),
                    "attendance_time": when.strftime("%H:%M:%S"),
                    "status": "Present",
                },
                on_conflict="roll_number,attendance_date",
                ignore_duplicates=True,
            )
            .execute()
        )
        return bool(response.data)

    def attendance_for_date(self, date_text: str) -> list[dict]:
        return (
            self.client.table("attendance")
            .select("roll_number, attendance_date, attendance_time, status, students(full_name, branch, section)")
            .eq("attendance_date", date_text)
            .order("attendance_time", desc=True)
            .execute()
            .data
        )
