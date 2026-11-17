from __future__ import annotations

import hmac
import os
import re
import sqlite3
from datetime import datetime
from html import escape

import cv2
import face_recognition
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from src.attendance import best_match
from src.config import FACE_DETECTION_MODEL, KNOWN_FACES_DIR, ensure_directories
from src.database import add_student, all_students, initialize_database, mark_present, today_attendance
from src.face_database import build_face_database, load_face_database
from src.supabase_store import SupabaseStore, is_configured


APP_TITLE = "Attendly"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SESSION_SECRET = os.getenv("SESSION_SECRET", "local-development-secret-change-me")

app = FastAPI(title=APP_TITLE, version="2.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true",
)

supabase_store: SupabaseStore | None = None


@app.on_event("startup")
def startup() -> None:
    ensure_directories()
    if is_configured():
        global supabase_store
        supabase_store = SupabaseStore()
    else:
        initialize_database()


def use_supabase() -> bool:
    return supabase_store is not None


def is_admin(request: Request) -> bool:
    return request.session.get("admin") is True


def admin_required(request: Request) -> RedirectResponse | None:
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    return None


def page(title: str, body: str, admin: bool = False) -> HTMLResponse:
    links = '<a href="/">Scan face</a><a href="/attendance">Attendance</a>'
    if admin:
        links += '<a href="/admin">Admin panel</a><form action="/admin/logout" method="post"><button class="nav-button">Logout</button></form>'
    else:
        links += '<a href="/admin/login">Admin login</a>'
    return HTMLResponse(
        f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>{escape(title)} | {APP_TITLE}</title>
        <style>
        :root{{--ink:#14213d;--muted:#60708a;--blue:#1c65d8;--line:#d9e1ec;--wash:#f4f7fb;--green:#0f8756;--red:#b73535}}
        *{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:15px Arial,sans-serif}}
        nav{{background:#fff;border-bottom:1px solid var(--line);min-height:64px;display:flex;align-items:center;gap:19px;padding:0 max(18px,calc((100vw - 1100px)/2))}}
        nav strong{{font-size:20px;color:var(--blue);margin-right:auto}}nav a,.nav-button{{border:0;background:none;color:#3f4d64;font:inherit;padding:0;text-decoration:none;cursor:pointer}}nav form{{margin:0}}
        main{{max-width:1100px;margin:auto;padding:36px 20px}}h1{{font-size:30px;margin:0 0 8px}}h2{{margin-top:0}}.sub{{color:var(--muted);margin:0 0 26px;line-height:1.5}}
        .grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:22px}}
        label{{display:block;font-weight:700;margin:14px 0 6px}}input{{width:100%;padding:11px;border:1px solid #bac6d7;border-radius:5px;font:inherit}}
        button{{background:var(--blue);border:0;border-radius:5px;color:#fff;font-weight:700;padding:11px 16px;cursor:pointer;margin-top:18px}}button.secondary{{background:#e6edf8;color:#26364d}}button:disabled{{opacity:.65;cursor:wait}}
        video{{width:100%;max-height:490px;object-fit:cover;background:#111827;border-radius:6px}}#result,.status{{padding:14px;background:#fff;border:1px solid var(--line);border-radius:6px}}.ok{{color:var(--green)}}.error{{color:var(--red)}}.empty{{color:var(--muted)}}
        table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line)}}th,td{{padding:12px;text-align:left;border-bottom:1px solid var(--line)}}th{{background:#f0f4fa;color:#536075;font-size:13px}}
        @media(max-width:680px){{nav{{padding:0 14px;gap:12px}}nav a{{font-size:13px}}main{{padding:24px 14px}}.grid{{grid-template-columns:1fr}}th:nth-child(3),td:nth-child(3){{display:none}}}}
        </style></head><body><nav><strong>Attendly</strong>{links}</nav><main>{body}</main></body></html>"""
    )


def student_table(students: list) -> str:
    if not students:
        return '<p class="empty">No students have been registered.</p>'
    rows = "".join(
        f"<tr><td>{escape(row['roll_number'])}</td><td>{escape(row['full_name'])}</td>"
        f"<td>{escape(row['branch'])}</td><td>{escape(row['section'])}</td></tr>"
        for row in students
    )
    return f"<table><thead><tr><th>Roll number</th><th>Name</th><th>Branch</th><th>Section</th></tr></thead><tbody>{rows}</tbody></table>"


@app.get("/", response_class=HTMLResponse)
def scanner_page(request: Request) -> HTMLResponse:
    body = """<h1>Mark attendance</h1><p class="sub">Position one face clearly in the camera, then scan.</p>
    <div class="grid"><section class="card"><video id="video" autoplay playsinline></video><canvas id="canvas" hidden></canvas>
    <button id="scan">Scan face</button><button id="restart" class="secondary">Restart camera</button></section>
    <aside class="card"><h2>Live status</h2><div id="result">Starting camera...</div><p class="sub" style="margin-top:18px">The image is used only to identify the student and mark today's attendance.</p></aside></div>
    <script>
    const v=document.querySelector('#video'),c=document.querySelector('#canvas'),b=document.querySelector('#scan'),r=document.querySelector('#result');
    async function start(){try{const s=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});v.srcObject=s;r.textContent='Camera ready. Scan when you are ready.';r.className=''}catch(e){r.textContent='Camera access was denied. Allow camera access in your browser settings.';r.className='error';b.disabled=true}}
    document.querySelector('#restart').onclick=start;start();
    b.onclick=async()=>{b.disabled=true;r.textContent='Recognizing face...';c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);const blob=await new Promise(x=>c.toBlob(x,'image/jpeg',.9));const form=new FormData();form.append('image',blob,'face.jpg');try{const res=await fetch('/api/recognize',{method:'POST',body:form}),data=await res.json();r.textContent=data.message;r.className=data.recognized?'ok':'error'}catch(e){r.textContent='Service error. Please try again.';r.className='error'}finally{b.disabled=false}};
    </script>"""
    return page("Scan attendance", body, is_admin(request))


@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request, error: str | None = None) -> HTMLResponse:
    if is_admin(request):
        return RedirectResponse("/admin", status_code=303)
    notice = '<p class="error">Invalid username or password.</p>' if error else ""
    body = f"""<div class="card" style="max-width:440px;margin:auto"><h1>Admin login</h1><p class="sub">Use the credentials configured for this application.</p>{notice}
    <form method="post" action="/admin/login"><label>Username</label><input name="username" required autofocus><label>Password</label><input name="password" type="password" required><button>Login</button></form></div>"""
    return page("Admin login", body)


@app.post("/admin/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)) -> RedirectResponse:
    if hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD):
        request.session["admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/admin/login?error=invalid", status_code=303)


@app.post("/admin/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    redirect = admin_required(request)
    if redirect:
        return redirect
    students = supabase_store.all_students() if use_supabase() else all_students()
    body = f"""<h1>Admin dashboard</h1><p class="sub">Manage student face IDs and review attendance.</p>
    <div class="grid"><section class="card"><h2>{len(students)} registered students</h2><p class="sub">Add a roll number, academic data, and clear face images.</p><a href="/admin/students/new"><button>Add student</button></a></section>
    <section class="card"><h2>Attendance records</h2><p class="sub">View the current or previous daily register.</p><a href="/attendance"><button class="secondary">View attendance</button></a></section></div>
    <section class="card" style="margin-top:18px"><h2>Students</h2>{student_table(students)}</section>"""
    return page("Admin dashboard", body, True)


@app.get("/admin/students/new", response_class=HTMLResponse)
def add_student_page(request: Request) -> HTMLResponse:
    redirect = admin_required(request)
    if redirect:
        return redirect
    body = """<h1>Add student</h1><p class="sub">Upload one or more clear face images containing exactly one face.</p>
    <section class="card" style="max-width:720px"><form action="/admin/students" method="post" enctype="multipart/form-data"><div class="grid">
    <div><label>Roll number</label><input name="roll_number" placeholder="CSE001" required></div><div><label>Full name</label><input name="full_name" placeholder="Student name" required></div>
    <div><label>Branch</label><input name="branch" placeholder="CSE" required></div><div><label>Section</label><input name="section" placeholder="A" required></div></div>
    <label>Face images</label><input name="photos" type="file" accept="image/jpeg,image/png" multiple required><button>Save student and generate face ID</button></form></section>"""
    return page("Add student", body, True)


def safe_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")


@app.post("/admin/students")
async def create_student(
    request: Request,
    roll_number: str = Form(...),
    full_name: str = Form(...),
    branch: str = Form(...),
    section: str = Form(...),
    photos: list[UploadFile] = File(...),
) -> RedirectResponse:
    redirect = admin_required(request)
    if redirect:
        return redirect
    roll_number = safe_component(roll_number)
    if not all((roll_number, full_name.strip(), branch.strip(), section.strip())):
        raise HTTPException(status_code=400, detail="All student details are required.")
    uploaded_photos: list[tuple[str, bytes, str]] = []
    encodings: list[list[float]] = []
    folder = KNOWN_FACES_DIR / f"{roll_number}_{safe_component(full_name)}"
    if not use_supabase():
        folder.mkdir(parents=True, exist_ok=True)
    saved = 0
    for index, photo in enumerate(photos, 1):
        contents = await photo.read()
        image = cv2.imdecode(np.frombuffer(contents, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is not None:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(image_rgb, model=FACE_DETECTION_MODEL)
            image_encodings = face_recognition.face_encodings(image_rgb, known_face_locations=locations)
            if len(locations) != 1 or not image_encodings:
                continue
            if use_supabase():
                uploaded_photos.append(
                    (photo.filename or f"sample_{index:03d}.jpg", contents, photo.content_type or "image/jpeg")
                )
                encodings.append(image_encodings[0].tolist())
            else:
                cv2.imwrite(str(folder / f"sample_{index:03d}.jpg"), image)
            saved += 1
    if not saved:
        raise HTTPException(status_code=400, detail="Upload at least one image with exactly one clear face.")
    try:
        if use_supabase():
            supabase_store.add_student(
                roll_number,
                full_name.strip(),
                branch.strip(),
                section.strip(),
                encodings,
                uploaded_photos,
            )
        else:
            add_student(roll_number, full_name.strip(), branch.strip(), section.strip())
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=400, detail="This roll number already exists.") from error
    try:
        if not use_supabase():
            build_face_database()
    except RuntimeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return RedirectResponse("/admin", status_code=303)


@app.get("/attendance", response_class=HTMLResponse)
def attendance_page(request: Request, date: str | None = None) -> HTMLResponse:
    selected = date or datetime.now().strftime("%Y-%m-%d")
    records = supabase_store.attendance_for_date(selected) if use_supabase() else today_attendance(selected)
    if records:
        if use_supabase():
            rows = "".join(
                f"<tr><td>{escape(row['roll_number'])}</td><td>{escape(row['students']['full_name'])}</td><td>{escape(row['students']['branch'])}</td><td>{escape(row['students']['section'])}</td><td>{escape(row['attendance_time'])}</td><td>{escape(row['status'])}</td></tr>"
                for row in records
            )
        else:
            rows = "".join(
                f"<tr><td>{escape(row['roll_number'])}</td><td>{escape(row['full_name'])}</td><td>{escape(row['branch'])}</td><td>{escape(row['section'])}</td><td>{escape(row['attendance_time'])}</td><td>{escape(row['status'])}</td></tr>"
                for row in records
            )
        table = f"<table><thead><tr><th>Roll number</th><th>Name</th><th>Branch</th><th>Section</th><th>Time</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>"
    else:
        table = '<p class="empty">No attendance records for this date.</p>'
    body = f"""<h1>Attendance register</h1><p class="sub">{len(records)} student(s) marked present.</p>
    <form method="get" class="card" style="margin-bottom:18px"><label>Attendance date</label><input type="date" name="date" value="{escape(selected)}"><button>View records</button></form>{table}"""
    return page("Attendance", body, is_admin(request))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/recognize")
async def recognize(image: UploadFile = File(...)) -> dict[str, str | bool | float]:
    frame = cv2.imdecode(np.frombuffer(await image.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Please send a valid image.")
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb, model=FACE_DETECTION_MODEL)
    if len(locations) != 1:
        return {"recognized": False, "message": "Show exactly one face to the camera."}
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    if not encodings:
        return {"recognized": False, "message": "Face encoding could not be generated."}
    try:
        known_faces = supabase_store.known_faces() if use_supabase() else load_face_database()
        if not known_faces:
            return {"recognized": False, "message": "No enrolled students are available yet."}
        match, distance = best_match(encodings[0], known_faces)
    except RuntimeError:
        return {"recognized": False, "message": "No enrolled students are available yet."}
    if match is None:
        return {"recognized": False, "message": "Face not recognized.", "distance": round(distance, 3)}
    now = datetime.now()
    marked = (
        supabase_store.mark_present(match.student_id, now)
        if use_supabase()
        else mark_present(match.student_id, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
    )
    message = "Attendance marked successfully" if marked else "Attendance was already marked today"
    return {"recognized": True, "marked": marked, "student_id": match.student_id, "name": match.name, "message": f"{match.name}: {message}.", "distance": round(distance, 3)}
