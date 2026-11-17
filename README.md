 # Automated Attendance System Using Face Recognition

A portfolio-ready Python project that detects and recognizes faces from a laptop webcam or mobile camera stream, marks attendance automatically, stores attendance in CSV/Excel-friendly format, and generates daily reports.

## Why This Project Is Resume-Worthy

This project demonstrates practical computer vision, file-based data handling, modular Python design, and real-world automation. It is built as a complete mini product rather than a single demo script, so you can explain the full workflow in interviews:

1. Enroll a student by capturing face samples.
2. Generate face encodings from stored images.
3. Open a live camera feed.
4. Detect and recognize faces in real time.
5. Mark attendance once per student per day.
6. Export daily attendance reports.

## Tech Stack

- Python
- OpenCV
- face_recognition
- NumPy
- CSV file storage
- Optional Excel export using openpyxl

## Project Structure

```text
automated-attendance-face-recognition/
  .vscode/
    launch.json
    settings.json
  data/
    attendance/
    known_faces/
    reports/
  src/
    attendance.py
    attendance_store.py
    camera.py
    config.py
    enroll.py
    face_database.py
    report.py
  requirements.txt
  README.md
```

## Setup in VS Code

Open this folder in VS Code:

```powershell
cd outputs\automated-attendance-face-recognition
code .
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Note for Windows: the `face_recognition` package depends on `dlib`. If normal installation fails, install CMake first, or use a prebuilt dlib wheel that matches your Python version.

## Camera Options

Laptop webcam:

```powershell
python -m src.attendance --source 0
```

Mobile camera using an IP camera app:

```powershell
python -m src.attendance --source "http://PHONE_IP:8080/video"
```

Common mobile camera options:

- Android IP Webcam app: `http://PHONE_IP:8080/video`
- DroidCam: use the virtual webcam index, usually `0` or `1`
- Any RTSP camera stream: pass the RTSP URL as `--source`

## How To Run

### 1. Enroll a Student

Run this command and face the camera:

```powershell
python -m src.enroll --id CSE001 --name "Amit Kumar" --source 0
```

This captures multiple face samples and stores them under:

```text
data/known_faces/CSE001_Amit_Kumar/
```

### 2. Generate Face Encodings

```powershell
python -m src.face_database
```

This creates:

```text
data/face_encodings.pkl
```

### 3. Start Automatic Attendance

```powershell
python -m src.attendance --source 0
```

Press `q` to stop the camera window.

Attendance is saved daily as:

```text
data/attendance/attendance_YYYY-MM-DD.csv
```

### 4. Generate Daily Report

```powershell
python -m src.report
```

The report is saved under:

```text
data/reports/
```

If `openpyxl` is installed, an Excel `.xlsx` report is also generated.

## Interview Explanation

You can explain the system like this:

"I built an automated attendance system using Python, OpenCV, and the face_recognition library. First, the system enrolls students by capturing their face samples through a webcam or mobile camera stream. Then it converts those images into numerical face encodings and stores them locally. During attendance, OpenCV reads frames from the live camera feed, detects faces, and compares the live face encoding with stored encodings. If a match is found within the tolerance threshold, the system marks that student's attendance only once per day and stores the record in a CSV file. Finally, a daily report generator creates a summary of present students, which can also be exported to Excel."

## Resume Bullet Points

- Developed an automated face recognition attendance system using Python, OpenCV, and face_recognition.
- Implemented real-time face detection and recognition from laptop webcam and mobile IP camera streams.
- Automated daily attendance marking with duplicate prevention and CSV/Excel-compatible report generation.
- Designed a modular codebase with separate enrollment, encoding, recognition, storage, and reporting components.

## Key Concepts To Know

- OpenCV captures frames from camera devices or stream URLs.
- Face detection finds the location of faces in a frame.
- Face encoding converts a face into a 128-dimensional numerical vector.
- Face matching compares vector distances between known and live faces.
- A tolerance threshold controls how strict recognition should be.
- Attendance is marked once per student per date to avoid duplicates.

## Future Enhancements

- Add a web dashboard using Flask or FastAPI.
- Store users and attendance in SQLite or PostgreSQL.
- Add admin login and role-based access.
- Add email report sharing.
- Add liveness detection to reduce photo spoofing.

## Web Admin And Render Deployment

The project includes a browser-based application with an admin login, student enrollment, live face scanning, and an attendance register. It is ready for deployment to Render with a persistent disk. Follow `docs/RENDER_DEPLOYMENT.md`.
