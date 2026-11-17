from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path

from src.config import ATTENDANCE_DIR, REPORTS_DIR, ensure_directories


def attendance_file_for(date_text: str) -> Path:
    return ATTENDANCE_DIR / f"attendance_{date_text}.csv"


def generate_csv_report(date_text: str) -> Path:
    ensure_directories()
    source_file = attendance_file_for(date_text)
    if not source_file.exists():
        raise RuntimeError(f"No attendance file found for {date_text}: {source_file}")

    report_file = REPORTS_DIR / f"daily_report_{date_text}.csv"
    shutil.copyfile(source_file, report_file)
    return report_file


def generate_excel_report(date_text: str) -> Path | None:
    source_file = attendance_file_for(date_text)
    excel_file = REPORTS_DIR / f"daily_report_{date_text}.xlsx"

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        return None

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Daily Attendance"

    with source_file.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row_index, row in enumerate(reader, start=1):
            sheet.append(row)
            if row_index == 1:
                for cell in sheet[row_index]:
                    cell.font = Font(bold=True)

    for column_cells in sheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = max_length + 2

    workbook.save(excel_file)
    return excel_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily attendance report.")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Report date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()

    csv_report = generate_csv_report(args.date)
    excel_report = generate_excel_report(args.date)

    print(f"CSV report generated: {csv_report}")
    if excel_report:
        print(f"Excel report generated: {excel_report}")
    else:
        print("Excel report skipped because openpyxl is not installed.")


if __name__ == "__main__":
    main()
