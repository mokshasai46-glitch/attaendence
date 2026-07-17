
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import json, csv, datetime, os
from functools import wraps

try:
    import face_recognition
    import numpy as np
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False


# Optional SQL support using SQLAlchemy
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON as SAJSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# environment variable or default database URL
DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///attendance.db"

# initialize SQLAlchemy using DATABASE_URL (defaults to SQLite)
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    password = Column(String, nullable=False)
    role = Column(String)
    name = Column(String)

class Embedding(Base):
    __tablename__ = 'embeddings'
    student_id = Column(String, primary_key=True)
    embeddings = Column(SAJSON)
    year = Column(String)
    section = Column(String)
    course = Column(String)

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime)
    session_id = Column(String)
    student_id = Column(String)
    status = Column(String)
    confidence = Column(Float)
    location = Column(String)
    course = Column(String)
    year = Column(String)
    section = Column(String)
    photo_path = Column(String)

# create tables if they don't exist
try:
    Base.metadata.create_all(engine)
    # Add photo_path column to attendance table if it doesn't exist (safe migration)
    with engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("PRAGMA table_info(attendance)"))
        columns = [row[1] for row in result.fetchall()]
        if 'photo_path' not in columns:
            conn.execute(text("ALTER TABLE attendance ADD COLUMN photo_path VARCHAR(255) NULL"))
            print("Successfully migrated database to add photo_path column.")
except Exception as e:
    print(f"Database initialization/migration error: {e}")


EMBEDDINGS_FILE = "embeddings.json"
USERS_FILE = "users.json"

# if the attendance table is empty, migrate any existing CSV files
def migrate_csv_attendance():
    import glob
    if not os.path.exists(EMBEDDINGS_FILE) and not glob.glob("attendance_*.csv"):
        return
    session = SessionLocal()
    try:
        count = session.query(Attendance).count()
        if count == 0:
            for file in glob.glob("attendance_*.csv"):
                with open(file, "r") as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    parts = file.replace("attendance_", "").replace(".csv", "").split("_")
                    if len(parts) == 3:
                        course, year, section = parts
                    else:
                        course = year = section = None
                    for record in reader:
                        if len(record) == 5:
                            record.append("")
                        ts = datetime.datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S")
                        rec = Attendance(
                            timestamp=ts,
                            session_id=record[1],
                            student_id=record[2],
                            status=record[3],
                            confidence=float(record[4]) if record[4] else None,
                            location=record[5],
                            course=course,
                            year=year,
                            section=section,
                        )
                        session.add(rec)
            session.commit()
    finally:
        session.close()
migrate_csv_attendance()

# if the embeddings table is empty, migrate existing JSON file
def migrate_json_embeddings():
    if not os.path.exists(EMBEDDINGS_FILE):
        return
    session = SessionLocal()
    try:
        count = session.query(Embedding).count()
        if count == 0:
            with open(EMBEDDINGS_FILE, "r") as f:
                file_data = json.load(f)
            for sid, info in file_data.items():
                rec = Embedding(
                    student_id=sid,
                    embeddings=info.get("embeddings"),
                    year=info.get("year"),
                    section=info.get("section"),
                    course=info.get("course"),
                )
                session.add(rec)
            session.commit()
    finally:
        session.close()
migrate_json_embeddings()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here-change-in-production")  # Change via env var in production

UPLOAD_DIR = os.path.join("static", "uploads", "attendance_pics")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pre-download static face-api JS and models for offline robustness
def download_static_assets():
    import urllib.request
    js_dir = os.path.join("static", "js")
    models_dir = os.path.join("static", "models")
    os.makedirs(js_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    # Download face-api.js
    js_path = os.path.join(js_dir, "face-api.js")
    if not os.path.exists(js_path):
        print("Downloading face-api.js locally for offline support...")
        try:
            urllib.request.urlretrieve(
                "https://cdn.jsdelivr.net/npm/@vladmandic/face-api/dist/face-api.js",
                js_path
            )
            print("Successfully downloaded face-api.js")
        except Exception as e:
            print(f"Non-blocking: Failed to download face-api.js locally: {e}")
            
    # Download models
    models = [
        "tiny_face_detector_model-weights_manifest.json",
        "tiny_face_detector_model-shard1",
        "face_landmark_68_model-weights_manifest.json",
        "face_landmark_68_model-shard1",
        "face_recognition_model-weights_manifest.json",
        "face_recognition_model-shard1",
        "face_recognition_model-shard2"
    ]
    base_url = "https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/"
    for model in models:
        model_path = os.path.join(models_dir, model)
        if not os.path.exists(model_path):
            print(f"Downloading model file locally: {model}...")
            try:
                urllib.request.urlretrieve(base_url + model, model_path)
                print(f"Successfully downloaded {model}")
            except Exception as e:
                print(f"Non-blocking: Failed to download {model} locally: {e}")

try:
    download_static_assets()
except Exception as e:
    print(f"Warning: Failed to execute static assets downloader: {e}")



# Health check endpoint
# Load embeddings

def load_embeddings():
    if DATABASE_URL:
        # fetch from database
        session = SessionLocal()
        try:
            records = session.query(Embedding).all()
            result = {}
            for r in records:
                result[r.student_id] = {
                    "embeddings": r.embeddings,
                    "year": r.year,
                    "section": r.section,
                    "course": r.course,
                }
            return result
        finally:
            session.close()
    # fallback to JSON file
    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_embeddings(data):
    if DATABASE_URL:
        session = SessionLocal()
        try:
            for sid, info in data.items():
                rec = session.get(Embedding, sid)
                if not rec:
                    rec = Embedding(student_id=sid)
                rec.embeddings = info.get("embeddings")
                rec.year = info.get("year")
                rec.section = info.get("section")
                rec.course = info.get("course")
                session.merge(rec)
            session.commit()
        finally:
            session.close()
        # also keep file backup
        with open(EMBEDDINGS_FILE, "w") as f:
            json.dump(data, f)
        return
    # fallback to file
    with open(EMBEDDINGS_FILE, "w") as f:
        json.dump(data, f)

# Load users (file + database support)
def load_users():
    if DATABASE_URL:
        session = SessionLocal()
        try:
            records = session.query(User).all()
            users = {r.username: {"password": r.password, "role": r.role, "name": r.name} for r in records}
            # migrate from json if empty
            if not users and os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r") as f:
                    file_users = json.load(f)
                for uname, info in file_users.items():
                    user = User(username=uname, password=info.get("password"), role=info.get("role"), name=info.get("name"))
                    session.add(user)
                session.commit()
                users = file_users
            return users
        finally:
            session.close()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(data):
    # write file backup
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)
    if DATABASE_URL:
        session = SessionLocal()
        try:
            for uname, info in data.items():
                user = session.get(User, uname)
                if not user:
                    user = User(username=uname)
                user.password = info.get("password")
                user.role = info.get("role")
                user.name = info.get("name")
                session.merge(user)
            session.commit()
        finally:
            session.close()

# Log attendance (writes to CSV and optionally to SQL database)
def log_attendance(session_id, student_id, status, confidence, location=None, photo_path=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get student's course, year and section from embeddings
    data = load_embeddings()
    course = 'unknown'
    year = 'unknown'
    section = 'unknown'
    if student_id in data:
        student_data = data[student_id]
        if isinstance(student_data, dict):
            course = student_data.get('course', 'unknown')
            year = student_data.get('year', 'unknown')
            section = student_data.get('section', 'unknown')
    
    attendance_file = f"attendance_{course}_{year}_{section}.csv"

    # primary storage is database when configured; CSV serves as optional backup
    if not DATABASE_URL:
        file_exists = os.path.exists(attendance_file)
        if file_exists:
            # Check if header has Location column
            with open(attendance_file, "r") as f:
                first_line = f.readline().strip()
                has_location = "Location" in first_line
        else:
            has_location = False
        with open(attendance_file, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists or not has_location:
                writer.writerow(["Timestamp", "Session ID", "Student ID", "Status", "Confidence", "Location", "Photo Path"])
            writer.writerow([timestamp, session_id, student_id, status, confidence, location or "", photo_path or ""])

    # additionally, mirror into database
    if DATABASE_URL:
        session = SessionLocal()
        try:
            # insert actual record
            rec = Attendance(
                timestamp=datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"),
                session_id=session_id,
                student_id=student_id,
                status=status,
                confidence=confidence,
                location=location,
                course=course,
                year=year,
                section=section,
                photo_path=photo_path,
            )
            session.add(rec)
            session.commit()
        finally:
            session.close()


# Initialize default users if file doesn't exist
def init_users():
    users = load_users()
    if not users:
        # Default admin user
        users['admin'] = {
            'password': 'admin123',
            'role': 'admin',
            'name': 'Administrator'
        }
        # Default faculty user
        users['faculty'] = {
            'password': 'faculty123',
            'role': 'faculty',
            'name': 'Faculty Member'
        }
        save_users(users)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/check_student/<student_id>")
def check_student(student_id):
    data = load_embeddings()
    exists = student_id in data
    return jsonify({"exists": exists})

@app.post("/analyze_face")
def analyze_face():
    try:
        file = request.files.get("image")
        if not file:
            return jsonify({"detected": False, "confidence": 0.0, "error": "No image provided"}), 400

        if not HAS_FACE_RECOGNITION:
            # Fallback when dlib/numpy are not available (e.g., local Windows or restricted cloud)
            return jsonify({"detected": True, "confidence": 0.95})

        # Load image and detect faces
        image = face_recognition.load_image_file(file)
        face_locations = face_recognition.face_locations(image)
        
        if not face_locations:
            return jsonify({"detected": False, "confidence": 0.0})
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        if not face_encodings:
            return jsonify({"detected": False, "confidence": 0.0})
        
        # For now, just return that a face was detected with high confidence
        confidence = 0.85  # Default high confidence for detected faces
        
        return jsonify({"detected": True, "confidence": confidence})
        
    except Exception as e:
        print(f"Face analysis error: {e}")
        return jsonify({"detected": False, "confidence": 0.0, "error": str(e)}), 500


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    # may show informational message (e.g. after password reset)
    message = request.args.get('message')
    return render_template("login.html", message=message)

@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username")
    password = request.form.get("password")

    users = load_users()
    if username in users and users[username]['password'] == password:
        session['user'] = username
        session['role'] = users[username]['role']
        session['name'] = users[username]['name']
        return redirect(url_for('enroll_page'))
    else:
        return render_template("login.html", error="Invalid username or password")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/forgot_password", methods=["GET","POST"])
def forgot_password():
    # allow user to reset their own password or admin reset via master key
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        new_pass = request.form.get("new_password")
        master_key = request.form.get("master_key")
        users = load_users()
        if username not in users:
            error = "Username not found"
        else:
            role = users[username].get("role")
            # if user is not logged in, require master key for any reset
            if not session.get('user'):
                expected = os.environ.get("ADMIN_RESET_KEY", "RESET123")
                if master_key != expected:
                    error = "Master key required to reset password when not logged in"
            else:
                # logged in; only allow changing own password or if admin
                if session.get('user') != username and session.get('role') != 'admin':
                    error = "You may only reset your own password unless you are an admin."
                # if resetting admin while logged in as non-admin should be caught above
            # if resetting admin and not already authenticated as admin, master key still required
            if not error and username == "admin" and not (session.get('user') == 'admin' and session.get('role') == 'admin'):
                expected = os.environ.get("ADMIN_RESET_KEY", "RESET123")
                if master_key != expected:
                    error = "Master key required to reset admin password"
            if not error:
                users[username]['password'] = new_pass
                save_users(users)
                return render_template("login.html", message="Password updated. Please log in.")
    return render_template("forgot_password.html", error=error)

@app.route("/manage_users", methods=["GET","POST"])
@login_required
def manage_users():
    # only admins may manage accounts
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    users = load_users()
    if request.method == "POST":
        uname = request.form.get("username")
        pwd = request.form.get("password")
        role = request.form.get("role")
        name = request.form.get("name")
        if uname and pwd and role:
            users[uname] = {"password": pwd, "role": role, "name": name}
            save_users(users)
    return render_template("manage_users.html", users=users)

@app.route("/enroll_page")
@login_required
def enroll_page():
    return render_template("enroll.html")

@app.route("/view_attendance")
def view_attendance():
    import glob
    from datetime import datetime
    
    # Get filter parameters
    selected_course = request.args.get('course', '')
    selected_year = request.args.get('year', '')
    selected_section = request.args.get('section', '')
    selected_from_date = request.args.get('from_date', '')
    selected_to_date = request.args.get('to_date', '')
    
    attendance_records = []
    available_courses = set()
    available_years = set()
    available_sections = set()
    
    if DATABASE_URL:
        # pull all entries from the database
        session = SessionLocal()
        try:
            for rec in session.query(Attendance).all():
                # record attributes: convert timestamp to string
                ts = rec.timestamp.strftime("%Y-%m-%d %H:%M:%S") if rec.timestamp else ""
                row = [ts, rec.session_id, rec.student_id, rec.status, rec.confidence or "", rec.location or ""]
                # class info appended later
                attendance_records.append((row, rec.course or '', rec.year or '', rec.section or ''))
                available_courses.add(rec.course or '')
                available_years.add(rec.year or '')
                available_sections.add(rec.section or '')
        finally:
            session.close()
        # convert attendance_records to unified list with class info
        normalized = []
        for row, course, year, section in attendance_records:
            normalized.append(row + [f"{course} {year}-{section}"])
        attendance_records = normalized
    else:
        files = glob.glob("attendance_*.csv")
        for file in files:
            if os.path.exists(file):
                with open(file, "r") as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    records = list(reader)
                    
                    # Extract class info from filename
                    parts = file.replace("attendance_", "").replace(".csv", "").split("_")
                    if len(parts) == 3:
                        course, year, section = parts
                        available_courses.add(course)
                        available_years.add(year)
                        available_sections.add(section)
                        
                        for record in records:
                            # Normalize record to have location column
                            if len(record) == 5:  # Old format without location
                                record.append("")  # Add empty location
                            # Add class info to record
                            record.append(f"{course} {year}-{section}")
                            attendance_records.append(record)
    
    # Convert sets to sorted lists for template
    available_courses = sorted(list(available_courses))
    available_years = sorted(list(available_years))
    available_sections = sorted(list(available_sections))
    
    # Apply filters
    filtered_records = []
    for record in attendance_records:
        if len(record) < 7:  # Ensure record has class info
            continue
            
        course, year_section = record[6].split(' ', 1) if ' ' in record[6] else ('', record[6])
        year, section = year_section.split('-', 1) if '-' in year_section else ('', '')
        
        # Apply course filter
        if selected_course and course != selected_course:
            continue
            
        # Apply year filter
        if selected_year and year != selected_year:
            continue
            
        # Apply section filter
        if selected_section and section != selected_section:
            continue
            
        # Apply date filters
        record_date = record[0].split(' ')[0] if ' ' in record[0] else record[0]  # Extract date part
        if selected_from_date and record_date < selected_from_date:
            continue
        if selected_to_date and record_date > selected_to_date:
            continue
            
        filtered_records.append(record)
    
    # Sort filtered records by class, then by date
    filtered_records.sort(key=lambda x: (x[6] if len(x) > 6 else '', x[0]))
    
    return render_template("attendance.html", 
                         records=filtered_records,
                         available_courses=available_courses,
                         available_years=available_years,
                         available_sections=available_sections,
                         selected_course=selected_course,
                         selected_year=selected_year,
                         selected_section=selected_section,
                         selected_from_date=selected_from_date,
                         selected_to_date=selected_to_date)

@app.post("/enroll")
def enroll():
    student_id = request.form.get("student_id")
    year = request.form.get("year")
    section = request.form.get("section")
    course = request.form.get("course")
    files = request.files.getlist("image")
    
    # Check if client sent pre-computed embeddings
    client_embeddings_str = request.form.get("embeddings")
    embeddings = []
    if client_embeddings_str:
        try:
            embeddings = json.loads(client_embeddings_str)
        except Exception as e:
            print(f"Error parsing client embeddings: {e}")

    # Fallback to backend calculation if needed
    if not embeddings:
        if not files or len(files) < 3 or not student_id or not year or not section or not course:
            return jsonify({"error": "All fields and 3 images are required"}), 400

        if not HAS_FACE_RECOGNITION:
            return jsonify({"error": "Backend face recognition is not enabled and no client embeddings were sent"}), 400

        for file in files:
            # Load image and encode face
            image = face_recognition.load_image_file(file)
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                return jsonify({"error": "No face detected in one of the images"}), 400
            embeddings.append(encodings[0].tolist())
    else:
        if not student_id or not year or not section or not course:
            return jsonify({"error": "All details are required"}), 400

    data = load_embeddings()
    data[student_id] = {
        "embeddings": embeddings,
        "year": year,
        "section": section,
        "course": course
    }
    save_embeddings(data)

    return jsonify({"status": "enrolled", "student_id": student_id})

@app.post("/attendance")
def attendance():
    if not HAS_FACE_RECOGNITION:
        return jsonify({"status": "error", "message": "Backend face recognition is not enabled. Please use the Real-Time Scanner."}), 400

    session_id = request.form.get("session_id")
    student_id = request.form.get("student_id")
    location = request.form.get("location")
    file = request.files.get("image")
    if not file or not student_id:
        return jsonify({"error": "Session ID, Student ID, and image are required"}), 400

    # Load image and encode face
    image = face_recognition.load_image_file(file)
    face_locations = face_recognition.face_locations(image)

    # Security Check 1: Multiple faces detection
    if len(face_locations) == 0:
        return jsonify({"status": "security_failed", "message": "No face detected. Please ensure your face is clearly visible.", "face_location": None, "match": False})
    elif len(face_locations) > 1:
        return jsonify({"status": "security_failed", "message": "Multiple faces detected. Only one person should be in frame.", "face_location": None, "match": False})

    encodings = face_recognition.face_encodings(image, face_locations)
    if not encodings:
        return jsonify({"status": "security_failed", "message": "Face encoding failed. Please try again.", "face_location": None, "match": False})

    new_encoding = encodings[0]
    data = load_embeddings()
    
    # Get face location (top, right, bottom, left)
    face_location = face_locations[0]

    # Check if student_id exists
    if student_id not in data:
        return jsonify({
            "status": "not_enrolled", 
            "message": "Student ID not found. Please check your ID or contact your faculty member.",
            "face_location": list(face_location),
            "match": False
        })

    student_data = data[student_id]
    embeddings = student_data['embeddings']

    # Compare with the student's embeddings
    best_confidence = 0
    for embedding in embeddings:
        known_encoding = np.array(embedding)
        matches = face_recognition.compare_faces([known_encoding], new_encoding, tolerance=0.4)  # Stricter tolerance
        confidence = 1 - face_recognition.face_distance([known_encoding], new_encoding)[0]

        if matches[0] and confidence > best_confidence:
            best_confidence = confidence

    # Security Check: Minimum confidence threshold
    if best_confidence >= 0.6:  # Require 60% confidence
        # Save photo path for consistency
        photo_web_path = None
        if file:
            timestamp_slug = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_student_id = "".join([c for c in student_id if c.isalnum() or c in ("-", "_")])
            photo_filename = f"{safe_student_id}_{timestamp_slug}.jpg"
            photo_path = os.path.join(UPLOAD_DIR, photo_filename)
            file.seek(0)
            file.save(photo_path)
            photo_web_path = f"/static/uploads/attendance_pics/{photo_filename}"

        log_attendance(session_id, student_id, "present", round(best_confidence, 2), location, photo_web_path)
        return jsonify({
            "status": "logged", 
            "student_id": student_id, 
            "confidence": round(best_confidence, 2),
            "face_location": list(face_location),
            "match": True
        })
    elif best_confidence > 0:
        return jsonify({
            "status": "low_confidence", 
            "message": f"Face recognition confidence too low ({round(best_confidence * 100, 1)}%). Please try again with better lighting and positioning.",
            "face_location": list(face_location),
            "match": False
        })

    return jsonify({
        "status": "not_recognized", 
        "message": "Face does not match the provided Student ID. Please try again or contact your faculty member.",
        "face_location": list(face_location),
        "match": False
    })

@app.route("/get_embeddings/<course>/<year>/<section>")
def get_embeddings(course, year, section):
    # Normalize inputs to match how they are stored
    course = course.lower().strip()
    year = year.lower().strip()
    section = section.lower().strip()
    
    data = load_embeddings()
    filtered = {}
    
    # Also load the display name for each student to send to client
    users = load_users()
    
    for sid, info in data.items():
        c = info.get("course", "").lower().strip()
        y = info.get("year", "").lower().strip()
        s = info.get("section", "").lower().strip()
        if c == course and y == year and s == section:
            # Find display name
            name = sid
            if sid in users:
                name = users[sid].get("name", sid)
            filtered[sid] = {
                "name": name,
                "embeddings": info.get("embeddings")
            }
            
    return jsonify(filtered)

@app.post("/attendance_realtime")
def attendance_realtime():
    try:
        session_id = request.form.get("session_id")
        student_id = request.form.get("student_id")
        confidence_str = request.form.get("confidence")
        location = request.form.get("location")
        file = request.files.get("image")
        
        if not session_id or not student_id:
            return jsonify({"error": "Session ID and Student ID are required"}), 400
            
        confidence = float(confidence_str) if confidence_str else 1.0
        
        # Save photo
        photo_web_path = None
        if file:
            timestamp_slug = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_student_id = "".join([c for c in student_id if c.isalnum() or c in ("-", "_")])
            photo_filename = f"{safe_student_id}_{timestamp_slug}.jpg"
            photo_path = os.path.join(UPLOAD_DIR, photo_filename)
            file.save(photo_path)
            photo_web_path = f"/static/uploads/attendance_pics/{photo_filename}"
            
        # Optional: Backend double-check validation if HAS_FACE_RECOGNITION is True
        backend_flagged = False
        backend_message = ""
        backend_confidence = None
        
        if HAS_FACE_RECOGNITION and file:
            try:
                # Seek back to 0 because save() consumed it
                file.seek(0)
                image = face_recognition.load_image_file(file)
                face_locations = face_recognition.face_locations(image)
                if len(face_locations) == 1:
                    encodings = face_recognition.face_encodings(image, face_locations)
                    if encodings:
                        new_encoding = encodings[0]
                        data = load_embeddings()
                        if student_id in data:
                            student_data = data[student_id]
                            known_embeddings = student_data.get('embeddings', [])
                            best_dist = 1.0
                            for embedding in known_embeddings:
                                known_encoding = np.array(embedding)
                                dist = face_recognition.face_distance([known_encoding], new_encoding)[0]
                                if dist < best_dist:
                                    best_dist = dist
                            
                            backend_confidence = round(1.0 - best_dist, 2)
                            if best_dist > 0.45:  # Tolerance threshold
                                backend_flagged = True
                                backend_message = "Backend double-check failed: face distance too high."
                        else:
                            backend_flagged = True
                            backend_message = "Backend warning: student embeddings not found in database."
                else:
                    backend_flagged = True
                    backend_message = f"Backend warning: {len(face_locations)} faces detected (expected 1)."
            except Exception as ex:
                print(f"Backend double-check error: {ex}")
                backend_message = f"Backend check failed with error: {str(ex)}"
                
        # Status
        status = "present"
        if backend_flagged:
            status = "flagged"
            
        # Log attendance
        log_attendance(session_id, student_id, status, confidence, location, photo_web_path)
        
        # Get student's name
        users = load_users()
        student_name = student_id
        if student_id in users:
            student_name = users[student_id].get("name", student_id)
        else:
            # try finding in embeddings
            data = load_embeddings()
            if student_id in data and "name" in data[student_id]:
                student_name = data[student_id]["name"]
            
        return jsonify({
            "status": "logged",
            "student_id": student_id,
            "student_name": student_name,
            "confidence": confidence,
            "backend_flagged": backend_flagged,
            "backend_message": backend_message,
            "backend_confidence": backend_confidence,
            "photo_path": photo_web_path
        })
    except Exception as e:
        print(f"Real-time attendance logging error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/attendance_live_stream/<session_id>")
def attendance_live_stream(session_id):
    session = SessionLocal()
    try:
        records = session.query(Attendance).filter(Attendance.session_id == session_id).order_by(Attendance.timestamp.desc()).all()
        result = []
        users = load_users()
        for r in records:
            name = r.student_id
            if r.student_id in users:
                name = users[r.student_id].get("name", r.student_id)
            result.append({
                "id": r.id,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "",
                "student_id": r.student_id,
                "student_name": name,
                "status": r.status,
                "confidence": r.confidence,
                "location": r.location,
                "photo_path": r.photo_path
            })
        return jsonify(result)
    finally:
        session.close()

@app.route("/live_scanner")
def live_scanner_page():
    course = request.args.get('course', '')
    year = request.args.get('year', '')
    section = request.args.get('section', '')
    session_id = request.args.get('session_id', '')
    return render_template("live_scanner.html", course=course, year=year, section=section, session_id=session_id)

@app.route("/live_dashboard")
def live_dashboard_page():
    course = request.args.get('course', '')
    year = request.args.get('year', '')
    section = request.args.get('section', '')
    session_id = request.args.get('session_id', '')
    return render_template("live_dashboard.html", course=course, year=year, section=section, session_id=session_id)


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=debug_mode)

