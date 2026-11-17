# Project Explanation Guide

## One-Minute Introduction

"This is an automated attendance system built with Python, OpenCV, and face_recognition. The system captures student face data using a laptop webcam or mobile camera stream, converts the face images into numerical encodings, and uses those encodings to recognize students in real time. When a known student is detected, the system automatically marks attendance in a daily CSV file and can generate a daily report in CSV or Excel format."

## Problem Statement

Manual attendance is time-consuming and can be inaccurate. This project solves that problem by using face recognition to identify students automatically and maintain daily attendance records.

## Main Modules

### 1. Enrollment Module

File: `src/enroll.py`

This module captures face samples for a student. The user provides a student ID and name, and the system stores multiple face images in a student-specific folder.

Example:

```powershell
python -m src.enroll --id CSE001 --name "Amit Kumar" --source 0
```

What it does:

- Opens the camera.
- Detects the face in the live frame.
- Saves multiple face samples.
- Stores samples in `data/known_faces/`.

### 2. Face Database Module

File: `src/face_database.py`

This module reads enrolled face images and generates encodings. A face encoding is a numerical representation of a face. The encodings are saved in a pickle file so they can be reused during attendance.

Example:

```powershell
python -m src.face_database
```

What it does:

- Reads all enrolled student images.
- Detects the face in each image.
- Converts each face into a 128-dimensional encoding.
- Stores encodings in `data/face_encodings.pkl`.

### 3. Attendance Module

File: `src/attendance.py`

This module runs real-time face recognition. It opens the camera, detects faces, compares live face encodings with stored encodings, and marks attendance.

Example:

```powershell
python -m src.attendance --source 0
```

What it does:

- Opens laptop or mobile camera.
- Detects faces in real time.
- Compares live faces with known face encodings.
- Marks attendance only once per student per day.
- Displays recognized names on the camera window.

### 4. Attendance Storage Module

File: `src/attendance_store.py`

This module handles attendance records. It writes records to a daily CSV file and prevents duplicate attendance entries.

Example output file:

```text
data/attendance/attendance_2026-07-08.csv
```

Stored fields:

- student_id
- name
- date
- time
- status

### 5. Report Module

File: `src/report.py`

This module generates a daily attendance report. It copies the daily attendance CSV into the reports folder and also creates an Excel report if `openpyxl` is installed.

Example:

```powershell
python -m src.report --date 2026-07-08
```

## Algorithm Flow

```text
Start
  |
  v
Enroll student faces
  |
  v
Generate face encodings
  |
  v
Open live camera feed
  |
  v
Detect face in each frame
  |
  v
Generate encoding for detected face
  |
  v
Compare live encoding with stored encodings
  |
  v
If match found, mark attendance
  |
  v
Generate daily report
  |
  v
End
```

## How Face Recognition Works

The `face_recognition` library converts each face into a 128-dimensional vector. This vector represents important facial features. During recognition, the system calculates the distance between the live face vector and stored face vectors.

If the distance is below the tolerance value, the face is considered a match.

In this project, the default tolerance is:

```text
0.50
```

Lower tolerance means stricter matching. Higher tolerance means more flexible matching.

## Why OpenCV Is Used

OpenCV is used for:

- Opening webcam or mobile camera stream.
- Reading video frames.
- Drawing rectangles around detected faces.
- Showing recognized names on screen.
- Displaying the live attendance window.

## Laptop and Mobile Camera Support

Laptop camera uses a device index:

```powershell
python -m src.attendance --source 0
```

Mobile camera uses a stream URL:

```powershell
python -m src.attendance --source "http://PHONE_IP:8080/video"
```

This works because OpenCV's `VideoCapture` can read both local camera indexes and network stream URLs.

## Duplicate Attendance Prevention

The system reads the current day's attendance CSV before marking a student. If the student ID already exists in today's file, attendance is not added again.

This avoids duplicate records when the same student remains in front of the camera.

## Why Multiple Samples Are Captured

Multiple samples improve recognition quality because faces may appear with slight changes in:

- Angle
- Lighting
- Distance from camera
- Expression

The system stores multiple encodings for the same student, which increases the chance of correct recognition.

## Limitations

- It needs good lighting for better accuracy.
- Recognition accuracy depends on the quality of enrolled face samples.
- The basic version does not include liveness detection.
- The file-based storage is suitable for a demo or small system; a production system should use a database.

## Possible Improvements

- Add Flask or FastAPI web dashboard.
- Add SQLite or PostgreSQL database.
- Add login system for admin access.
- Add liveness detection to prevent photo spoofing.
- Add email or WhatsApp report sharing.
- Add class-wise and subject-wise attendance.

## Common Interview Questions

### What is the main objective of the project?

The objective is to automate attendance marking using face recognition so that manual attendance becomes faster and more reliable.

### Why did you use OpenCV?

I used OpenCV for real-time camera handling, frame processing, drawing face boxes, and displaying the live video feed.

### What is face encoding?

Face encoding is a numerical representation of a face. The system compares these numerical vectors to identify whether two faces belong to the same person.

### How do you prevent duplicate attendance?

Before marking attendance, the system checks the current day's CSV file. If the student ID is already present, it does not add another entry.

### Can it work with a mobile camera?

Yes. If the mobile phone provides an IP camera stream, OpenCV can read that stream URL using `VideoCapture`.

### What happens if an unknown face appears?

The system labels the face as Unknown and does not mark attendance.

### What is the role of tolerance?

Tolerance controls how strict the face matching is. A lower value reduces false matches but may reject valid faces. A higher value accepts more matches but can increase false positives.

### How would you improve this project for production?

I would add a database, web dashboard, authentication, liveness detection, cloud backup, and better reporting analytics.
