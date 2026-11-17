# Deploy To Google Cloud Run

## What Changes In The Cloud Version

Cloud Run cannot access a laptop webcam with `--source 0`. The included web application keeps the camera in the user's browser and sends a single captured image to the service for recognition. It uses Firestore for daily attendance records when deployed to Google Cloud.

## Before Deploying

1. Use Python 3.10 or 3.11 locally to enroll at least one student.
2. Run `python -m src.face_database`.
3. Confirm `data/face_encodings.pkl` exists. This file is included in the container image and is required for recognition.
4. Install and authenticate the Google Cloud CLI:

```powershell
gcloud auth login
gcloud auth application-default login
```

5. Create or select a Google Cloud project with billing enabled.

## Deploy

From the project root, run:

```powershell
.\deploy-cloud-run.ps1 -ProjectId "YOUR_GOOGLE_CLOUD_PROJECT_ID"
```

The script enables Cloud Run, Cloud Build, and Firestore APIs; creates a Firestore database in `asia-south1` only when one does not already exist; grants the Cloud Run default service account permission to write attendance data; builds the container; and deploys it.

When `gcloud run deploy` finishes, it prints the public service URL. Open that URL in Chrome or Edge, allow camera access, and select **Mark attendance**.

## Important Security Notes

- The example deploys a public demo endpoint so the browser can access it. Before collecting real attendance, restrict access with Identity-Aware Proxy, Firebase Authentication, or another authentication layer.
- Use the service only with informed consent. Face data is biometric data.
- Each Cloud Run revision contains `data/face_encodings.pkl`. Enrollments made after deployment require you to rebuild the database and redeploy.
- Firestore is used to prevent duplicate attendance records across Cloud Run instances. The local CSV fallback is only for local development.

## Update Enrolled Faces

```powershell
python -m src.enroll --id CSE002 --name "Student Name" --source 0
python -m src.face_database
.\deploy-cloud-run.ps1 -ProjectId "YOUR_GOOGLE_CLOUD_PROJECT_ID"
```
