# Deploy To Render

## What You Need

- A GitHub account and a Render account.
- This project pushed to a GitHub repository.
- A Render paid web service with a persistent disk. The disk stores the SQLite database, uploaded face images, and generated face encodings.

## Deploy Using The Render Blueprint

1. Push this repository to GitHub. Do not add face images or student data to a public repository.
2. In Render, choose **New** > **Blueprint** and select the repository.
3. Render reads `render.yaml` and creates the Docker web service with a persistent disk mounted at `/var/data`.
4. Set a strong `ADMIN_PASSWORD` in Render's environment-variable screen. Do not use the local default password in production.
5. Deploy. Render will show a public URL such as `https://face-attendance.onrender.com`.

## First Use

1. Open `https://YOUR-RENDER-URL/admin/login`.
2. Sign in using `ADMIN_USERNAME` and `ADMIN_PASSWORD` from Render.
3. Open **Add student** and enter roll number, name, branch, section, and one or more clear face images.
4. Students open the home page, allow camera access, and select **Scan face**.
5. Anyone can view the attendance register at `/attendance`; use the admin panel to manage students.

## Local Run

```powershell
python -m pip install -r requirements.txt
$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD = "your-strong-password"
python -m uvicorn src.web_app:app --reload
```

Then open `http://127.0.0.1:8000`.

## Production Notes

- Browser camera access requires HTTPS. Render provides HTTPS on its public URL.
- A public attendance page can be viewed by anyone with the URL. Add student login or a QR/session code before a real college deployment.
- Face images are biometric data. Obtain consent, set a retention policy, and restrict admin access.
- The selected Render plan needs a persistent disk. Free instances do not preserve local files after redeploy or restart.
