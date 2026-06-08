# Face Recognition Attendance System

A modern, colorful college attendance system using face recognition technology with live webcam capture and advanced security features.

**[🚀 Visit the Web App](http://127.0.0.1:5000/)** (after running `python app.py`)

## Features

- **🎨 Modern UI**: Beautiful gradient design with smooth animations
- **🔐 Secure Authentication**: Role-based access control for enrollment
- **📱 Live Webcam Enrollment**: Register students using real-time camera capture (faculty only)
- **🔒 Secure Live Attendance**: Mark attendance with advanced security checks (public access)
- **👤 Face Recognition**: Advanced AI-powered face detection and matching
- **📊 View Attendance Records**: Access complete attendance history
- **🌐 Web-based Interface**: User-friendly browser interface

## 🔐 Authentication System

The system includes role-based authentication to secure enrollment functionality:

### Default Faculty Credentials:
- **Username**: faculty
- **Password**: admin123

### Default Student Credentials:
- **Username**: student
- **Password**: student123

## Installation

1. Install Python 3.8 or higher
2. Clone or download this repository
3. Navigate to the project directory
4. Create a virtual environment: `python -m venv .venv`
5. Activate the virtual environment: `.venv\Scripts\activate` (Windows)
6. Install dependencies: `pip install -r requirements.txt`

### SQL Database Setup
The application uses a SQL database by default via SQLite.
If `DATABASE_URL` is not provided, it will create and use a local
`attendance.db` SQLite database automatically.

For local testing you can explicitly set a file‑based SQLite database:

```
# local SQLite database file
set DATABASE_URL=sqlite:///attendance.db          (Windows PowerShell)
export DATABASE_URL=sqlite:///attendance.db        (bash)
```

Or point to a MySQL/MariaDB server using PyMySQL:

```
mysql+pymysql://username:password@localhost/attendance_db
```

When the database is first opened, any existing `users.json`,
`embeddings.json` or `attendance_*.csv` files will be migrated so your
historical data is preserved. By default the app now uses SQLite
`attendance.db`, so SQL storage is active even without setting
`DATABASE_URL` explicitly.

## Usage

1. **Run the application**: `python app.py`
2. **Access the web interface**: Open http://127.0.0.1:5000/
3. **Faculty Login**: Use credentials to access enrollment
4. **Student Enrollment**: Capture multiple face angles for better recognition
5. **Attendance Marking**: Students can mark attendance using webcam
6. **View Records**: Access attendance history with filtering options

## Dependencies

- Flask: Web framework
- face_recognition: Face recognition library
- numpy: Numerical computations
- opencv-python: Computer vision
- requests: HTTP requests

## 📁 Project Structure

```
attendance-system/
├── app.py                 # Main Flask application
├── capture.py            # Webcam capture script
├── embeddings.json       # Face embeddings storage
├── users.json           # User credentials
├── attendance_*.csv     # Attendance records
├── templates/           # HTML templates
│   ├── index.html
│   ├── login.html
│   ├── enroll.html
│   └── attendance.html
├── static/              # CSS and static files
│   └── style.css
└── requirements.txt     # Python dependencies
```

## 📝 Usage Guide

1. **Faculty Login**: Use credentials to access enrollment
2. **Student Enrollment**: Capture multiple face angles for better recognition
3. **Attendance Marking**: Students can mark attendance using webcam
4. **View Records**: Access attendance history with filtering options

### **User Roles:**
- **👑 Admin**: Full system access
- **👨‍🏫 Faculty**: Enrollment access only

### **Default Credentials:**
- **Admin**: `admin` / `admin123`
- **Faculty**: `faculty` / `faculty123`

### **Access Control:**
- **Public Access**: Attendance marking (no login required)
- **Protected Access**: Student enrollment (login required)
- **Session Management**: Automatic logout on browser close

### **Security Features:**
- Password-based authentication
- Session-based access control
- Role-based permissions
- Secure enrollment restrictions

## Installation

1. Install Python 3.8 or higher
2. Clone or download this repository
3. Navigate to the project directory
4. Create a virtual environment: `python -m venv .venv`
5. Activate the virtual environment: `.venv\Scripts\activate` (Windows)
6. Install dependencies: `pip install -r requirements.txt`

## Usage

### Running the Web App

1. Run the Flask app: `python app.py`
2. Open your browser and go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

### Main Attendance Page
- Use "� Faculty Login" to access enrollment system
- Use "📊 View Attendance Records" to check attendance history
- Mark attendance using the live capture system (no login required)

### Faculty Enrollment (Protected)
1. Click "🔐 Faculty Login" (opens in new tab)
2. Enter username and password
3. Access enrollment system for authorized personnel only
4. Enroll students using live webcam capture
5. Logout when finished

**Note:** Students cannot enroll themselves - enrollment is restricted to faculty and administrators only.

**Enrollment Security:**
- Checks for duplicate Student IDs
- Validates face detection
- Provides clear feedback on enrollment status

### Marking Attendance

1. Enter a Session ID
2. Click "Start Attendance Check"
3. Follow the security prompt (smile, blink, or move as instructed)
4. Click "Capture Now" when ready
5. If your face is recognized, attendance will be marked
6. If your face is not recognized, you'll be directed to contact faculty/admin for enrollment

**Security Checks Include:**
- Face detection and recognition (60%+ confidence required)
- Liveness verification with random actions
- Multiple face detection prevention
- Single face validation

### Using the Capture Script

For webcam capture:

1. Run `python capture.py`
2. Choose 'e' to enroll or 'a' to mark attendance
3. Follow the prompts

## Files

- `app.py`: Main Flask application
- `capture.py`: Script for webcam capture
- `embeddings.json`: Stores face embeddings
- `attendance.csv`: Attendance records
- `templates/`: HTML templates
- `static/`: CSS and static files

## Dependencies

- Flask: Web framework
- face_recognition: Face recognition library
- numpy: Numerical computations
- opencv-python: Computer vision
- requests: HTTP requests

## 🚀 Deploying from GitHub

### Environment variables

Set the following values before deploying or running in production:

- `SECRET_KEY` — Flask session secret key
- `DATABASE_URL` — Database connection string (example: `sqlite:///attendance.db` or `mysql+pymysql://user:pass@host/dbname`)
- `FLASK_DEBUG` — `false` in production
- `PORT` — Web server port (Heroku sets this automatically)
- `ADMIN_RESET_KEY` — Master key for password reset flows

### Deploying on Heroku

1. Create a Heroku app: `heroku create`
2. Push code: `git push heroku main`
3. Set environment variables:
   - `heroku config:set SECRET_KEY=your-secret-key`
   - `heroku config:set FLASK_DEBUG=false`
   - `heroku config:set ADMIN_RESET_KEY=RESET123`
4. Open the app: `heroku open`

> Note: Heroku’s file system is ephemeral, so use a hosted database service with `DATABASE_URL` rather than relying on local `attendance.db`.

### GitHub Actions CI

A lightweight GitHub Actions workflow has been added to validate `app.py` syntax on each push and pull request.

### 2. Deployment support files

This repo now includes:
- `Procfile` for WSGI deployment
- `runtime.txt` for Python version pinning
- `gunicorn` in `requirements.txt`

### 3. Recommended cloud hosts

#### Render

1. Create a new Web Service and connect your GitHub repo.
2. Use the provided `render.yaml` file to pin Python and build settings.
3. If you configure the service manually, set the build command to:
   ```bash
   python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
   ```
4. Set the start command:
   ```bash
   gunicorn app:app --bind 0.0.0.0:$PORT
   ```
5. Set environment variables:
   - `SECRET_KEY`
   - `DATABASE_URL` (optional)
   - `ADMIN_RESET_KEY` (optional)

#### Heroku

1. Install the Heroku CLI and login.
2. Create a new app:
   ```bash
   heroku create your-app-name
   ```
3. Set config vars:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   ```
4. Deploy:
   ```bash
   git push heroku main
   ```

#### Railway

1. Create a Railway project and connect your GitHub repo.
2. Add `SECRET_KEY` and `FLASK_ENV=production`.
3. Railway will auto-deploy on push.

### 4. Notes for production

- Camera access in browsers requires HTTPS.
- Keep `SECRET_KEY` secret.
- For higher reliability, use `DATABASE_URL` instead of JSON/CSV.
- `face_recognition` may need build tools on Linux or Windows.

## 🔧 Troubleshooting Deployment Issues

### "Website Cannot Be Accessed" Error

If you're getting a "website cannot be accessed" error, try these solutions:

#### 1. **Check App Status**
```bash
# For Heroku
heroku ps -a your-app-name
heroku logs --tail -a your-app-name

# For Railway
# Check the deployment logs in the Railway dashboard
```

#### 2. **Test Locally First**
```bash
python test_deployment.py
python app.py
# Visit http://localhost:5000
```

#### 3. **Common Issues & Solutions**

**Issue: App crashes on startup**
- Check if all dependencies are installed
- Verify Python version compatibility
- Look for import errors in logs

**Issue: Face recognition not working**
- Ensure `dlib` and `face_recognition` are properly installed
- Check if system has required libraries (for Linux/Mac)

**Issue: Static files not loading**
- Ensure `static/` folder exists
- Check file permissions
- Verify Flask is configured to serve static files

**Issue: Camera not working in production**
- Camera access requires HTTPS
- Check if your deployment platform provides HTTPS
- Some platforms may not support webcam access

#### 4. **Environment Variables**
Make sure these are set in your deployment platform:

```bash
SECRET_KEY=your-super-secret-random-key-here
FLASK_ENV=production
```

#### 5. **Platform-Specific Issues**

**Heroku:**
```bash
# Check build logs
heroku logs -a your-app-name --source app

# Restart app
heroku restart -a your-app-name

# Check if app is running
heroku ps -a your-app-name
```

**Railway:**
- Check deployment logs in dashboard
- Ensure `Procfile` exists
- Verify Python version in `runtime.txt`

**PythonAnywhere:**
- Check web app logs
- Ensure WSGI file points to correct app
- Verify static files configuration

#### 6. **Health Check**
Visit `https://your-app-url/health` to check if the app is responding.

#### 7. **Manual Testing**
```bash
# Test the health endpoint
curl https://your-app-url/health

# Test the main page
curl https://your-app-url/
```

### Need Help?
1. Check the deployment platform's documentation
2. Review the app logs for error messages
3. Ensure all environment variables are set
4. Test locally before deploying

## 📝 Usage

1. **Faculty Login**: Use credentials to access enrollment
2. **Student Enrollment**: Capture multiple face angles for better recognition
3. **Attendance Marking**: Students can mark attendance using webcam
4. **View Records**: Access attendance history with filtering options