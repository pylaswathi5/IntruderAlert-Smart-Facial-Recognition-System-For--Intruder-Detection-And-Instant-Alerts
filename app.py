from flask import Flask, render_template, request, jsonify, send_from_directory, Response, redirect, url_for, session
import os
import cv2
import uuid
import json
import shutil
import threading
from datetime import datetime
from werkzeug.utils import secure_filename
from face_utils import extract_embedding, recognize_face, load_authorized_faces, get_authorized_users
from email_utils import send_intruder_alert
import logging
from functools import wraps

# Try to load config, fallback to defaults
try:
    from config import DETECTION_SETTINGS
    ALERT_COOLDOWN = DETECTION_SETTINGS.get('ALERT_COOLDOWN', 5)
except ImportError:
    ALERT_COOLDOWN = 5

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")  # Needed for session-based login
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

AUTHORIZED_DIR = "authorized_faces"
INTRUDER_DIR = "intruders"
LOGS_FILE = "detection_logs.json"

# -------- ADMIN AUTH CONFIG --------
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def login_required(view_func):
    """Simple decorator to restrict routes to logged-in admin."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            next_url = request.path
            return redirect(url_for("login", next=next_url))
        return view_func(*args, **kwargs)
    return wrapped_view

# Create necessary directories
os.makedirs(INTRUDER_DIR, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(AUTHORIZED_DIR, exist_ok=True)

# Initialize detection logs
if not os.path.exists(LOGS_FILE):
    with open(LOGS_FILE, 'w') as f:
        json.dump([], f)

# Load authorized faces on startup
load_authorized_faces()

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_logs():
    """Load detection logs from JSON file"""
    try:
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading logs: {str(e)}")
    return []

def save_log(detection_type, name, confidence, image_path=None):
    """Save detection log"""
    try:
        logs = load_logs()
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": detection_type,  # "authorized" or "intruder"
            "name": name,
            "confidence": float(confidence),
            "image_path": image_path
        }
        logs.insert(0, log_entry)  # Add to beginning
        # Keep only last 1000 logs
        logs = logs[:1000]
        with open(LOGS_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving log: {str(e)}")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page (hardcoded credentials)."""
    if session.get("admin_logged_in"):
        next_url = request.args.get("next") or url_for("index")
        return redirect(next_url)

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Log out admin."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    """Dashboard page"""
    users = get_authorized_users()
    logs = load_logs()[:10]  # Latest 10 logs
    stats = {
        "total_users": len(users),
        "total_detections": len(load_logs()),
        "intruders": len([log for log in load_logs() if log.get("type") == "intruder"]),
        "authorized": len([log for log in load_logs() if log.get("type") == "authorized"])
    }
    return render_template("dashboard.html", users=users, logs=logs, stats=stats)


@app.route("/add-user")
@login_required
def add_user_page():
    """Add user page"""
    return render_template("add_user.html")

@app.route("/detect")
def detect_page():
    """Face detection page"""
    return render_template("detect.html")

@app.route("/users")
@login_required
def users_page():
    """Manage users page"""
    users = get_authorized_users()
    return render_template("users.html", users=users)


@app.route("/add-user", methods=["POST"])
@login_required
def add_user():
    """Add authorized user.

    Updated to support multiple webcam-captured images (recommended: 10 color images).
    Frontend should send images as multiple files with field name 'images'.
    """
    try:
        name = request.form.get("name", "").strip()

        if not name:
            # For AJAX requests, return JSON instead of re-rendering template
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": "Name is required"}), 400
            return render_template("add_user.html", error="Name is required")

        # Prefer multi-image input from webcam captures
        images = request.files.getlist("images")
        single_image = request.files.get("image")

        # Determine input mode
        use_multi = images and len(images) > 0

        if not use_multi:
            # Fallback to legacy single image upload if provided
            if not single_image or single_image.filename == "":
                msg = "At least one captured image is required. Please capture 10 photos from the webcam."
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"success": False, "message": msg}), 400
                return render_template("add_user.html", error=msg)

            if not allowed_file(single_image.filename):
                msg = "Invalid file type. Allowed: JPG, JPEG, PNG, GIF"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"success": False, "message": msg}), 400
                return render_template("add_user.html", error=msg)

        # Secure folder name
        name_secure = secure_filename(name)
        user_dir = os.path.join(AUTHORIZED_DIR, name_secure)
        os.makedirs(user_dir, exist_ok=True)

        saved_paths = []
        valid_face_count = 0

        def _process_and_save_image(file_storage, idx: int):
            nonlocal valid_face_count
            if not file_storage:
                return

            # Some webcam blobs might not have a filename; give them a safe default
            original_filename = file_storage.filename or f"capture_{idx}.jpg"
            if not allowed_file(original_filename):
                # Force a jpg extension so allowed_file passes
                original_filename = f"capture_{idx}.jpg"

            filename = f"{uuid.uuid4()}.jpg"
            image_path = os.path.join(user_dir, filename)
            file_storage.save(image_path)
            saved_paths.append(image_path)

            img = cv2.imread(image_path)
            if img is None:
                # Not a valid image
                os.remove(image_path)
                return

            # Extract embedding to ensure there is a clear face
            embedding = extract_embedding(img)
            if embedding is None:
                # No face detected; remove this capture
                os.remove(image_path)
                return

            valid_face_count += 1

        if use_multi:
            # Enforce exactly 10 images for better robustness if possible
            if len(images) != 10:
                msg = f"Exactly 10 captured images are required, but received {len(images)}. Please recapture."
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"success": False, "message": msg}), 400
                return render_template("add_user.html", error=msg)

            for idx, img_file in enumerate(images):
                _process_and_save_image(img_file, idx)
        else:
            _process_and_save_image(single_image, 0)

        # If no valid faces were found, clean up and report error
        if valid_face_count == 0:
            # Remove user directory if empty
            try:
                if os.path.isdir(user_dir) and not os.listdir(user_dir):
                    os.rmdir(user_dir)
            except Exception:
                pass

            msg = "No valid faces detected in the captured images. Please ensure a clear, front-facing, well-lit face."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": msg}), 400
            return render_template("add_user.html", error=msg)

        # Reload authorized faces so new images are used immediately
        load_authorized_faces()
        logger.info(f"Added authorized user: {name_secure} with {valid_face_count} valid face images.")

        success_msg = f"User '{name_secure}' added successfully with {valid_face_count} face images! You can now use face detection."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": True, "message": success_msg})
        return render_template("add_user.html", success=success_msg)
    except Exception as e:
        logger.error(f"Error adding user: {str(e)}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": f"Error adding user: {str(e)}"}), 500
        return render_template("add_user.html", error=f"Error adding user: {str(e)}")

@app.route("/delete-user/<username>", methods=["POST"])
@login_required
def delete_user(username):
    """Delete authorized user (admin only)."""
    try:
        # Support both legacy folder names and secure filenames
        username_raw = username
        username_secure = secure_filename(username)

        candidate_dirs = [
            os.path.join(AUTHORIZED_DIR, username_secure),
            os.path.join(AUTHORIZED_DIR, username_raw),
        ]

        deleted = False
        for user_dir in candidate_dirs:
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir)
                deleted = True

        if deleted:
            load_authorized_faces()
            logger.info(f"Deleted user: {username_raw}")
            return jsonify({"success": True, "message": f"User '{username_raw}' deleted successfully"})

        return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/detect", methods=["POST"])
def predict():
    """Predict/recognize face"""
    try:
        image = request.files.get("image")
        if not image or image.filename == '':
            return render_template("detect.html", error="Image is required")

        if not allowed_file(image.filename):
            return render_template("detect.html", error="Invalid file type. Allowed: JPG, JPEG, PNG, GIF")

        # Save image temporarily
        img_path = os.path.join(INTRUDER_DIR, f"{uuid.uuid4()}.jpg")
        image.save(img_path)

        img = cv2.imread(img_path)
        if img is None:
            if os.path.exists(img_path):
                os.remove(img_path)
            return render_template("detect.html", error="Could not read image file")

        embedding = extract_embedding(img)
        if embedding is None:
            if os.path.exists(img_path):
                os.remove(img_path)
            return render_template("detect.html", error="No face detected in image. Please upload an image with a clear face.")

        name, score = recognize_face(embedding)

        # Save log
        detection_type = "authorized" if name != "INTRUDER" else "intruder"
        save_log(detection_type, name, score, img_path)

        if name == "INTRUDER":
            # Send email alert in background thread
            def send_alert():
                send_intruder_alert(img_path, score)
            threading.Thread(target=send_alert, daemon=True).start()
            
            message = f"🚨 INTRUDER DETECTED! Confidence: {score:.2%}"
            return render_template("detect.html", warning=message, intruder_detected=True)
        else:
            # Remove image if authorized (only keep intruder images)
            if os.path.exists(img_path):
                os.remove(img_path)
            message = f"✅ Authorized: {name} (Confidence: {score:.2%})"
            return render_template("detect.html", success=message)
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        return render_template("detect.html", error=f"Error during prediction: {str(e)}")

@app.route("/logs")
def logs_page():
    """View all detection logs"""
    logs = load_logs()
    stats = {
        "total_detections": len(logs),
        "intruders": len([log for log in logs if log.get("type") == "intruder"]),
        "authorized": len([log for log in logs if log.get("type") == "authorized"])
    }
    return render_template("logs.html", logs=logs, stats=stats)

@app.route("/intruders")
def intruders_page():
    """View all intruder images"""
    try:
        intruder_files = []
        if os.path.exists(INTRUDER_DIR):
            for filename in os.listdir(INTRUDER_DIR):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    filepath = os.path.join(INTRUDER_DIR, filename)
                    # Get file modification time
                    mtime = os.path.getmtime(filepath)
                    intruder_files.append({
                        "filename": filename,
                        "timestamp": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
        # Sort by timestamp (newest first)
        intruder_files.sort(key=lambda x: x["timestamp"], reverse=True)
        return render_template("intruders.html", intruders=intruder_files)
    except Exception as e:
        logger.error(f"Error loading intruders: {str(e)}")
        return render_template("intruders.html", intruders=[], error=str(e))

@app.route("/intruder-image/<filename>")
def intruder_image(filename):
    """Serve intruder image"""
    return send_from_directory(INTRUDER_DIR, filename)

@app.route("/video_feed")
def video_feed():
    """Video streaming route for webcam"""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/webcam")
def webcam_page():
    """Webcam page with live video stream"""
    return render_template("webcam.html")

@app.route("/video")
def video_page():
    """Video page with webcam stream (legacy route)"""
    return render_template("webcam.html")

# Global variable to track last intruder detection time (to avoid spam)
last_intruder_alert_time = {}

# Global state for live webcam detection status (used by /detection_status)
current_detection_status = {
    "status": "none",      # "none", "authorized", "intruder"
    "name": None,
    "confidence": 0.0,
    "timestamp": None,
}

def generate_frames():
    """Generate frames from webcam for video streaming with monitoring"""
    from face_utils import detector
    global last_intruder_alert_time, current_detection_status
    
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        logger.error("Could not open camera")
        return
    
    # Temporal smoothing: require a streak of "INTRUDER" recognitions
    # before firing an alert, to avoid noisy one-off misclassifications.
    intruder_streak = 0
    authorized_streak = 0
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        detected_name = "Scanning..."
        detected_score = 0.0
        intruder_detected = False
        
        # Perform face detection and recognition on every frame
        try:
            embedding = extract_embedding(frame)
            if embedding is not None:
                detected_name, detected_score = recognize_face(embedding)

                if detected_name == "INTRUDER":
                    intruder_streak += 1
                    authorized_streak = 0
                else:
                    authorized_streak += 1
                    intruder_streak = 0

                # Update live detection status for frontend polling
                if detected_name == "INTRUDER":
                    status_label = "intruder" if intruder_streak >= 1 else "none"
                else:
                    status_label = "authorized"

                current_detection_status = {
                    "status": status_label,
                    "name": detected_name if status_label != "none" else None,
                    "confidence": float(detected_score) if status_label != "none" else 0.0,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Only trigger an intruder alert if we have 30 consecutive INTRUDER frames
                if detected_name == "INTRUDER" and intruder_streak >= 1:
                    intruder_detected = True
                    current_time = datetime.now()

                    # Save intruder image and send alert (with cooldown)
                    detection_key = f"{detected_score:.2f}"
                    if (detection_key not in last_intruder_alert_time or 
                        (current_time - last_intruder_alert_time[detection_key]).total_seconds() > ALERT_COOLDOWN):
                        
                        # Save intruder image
                        img_path = os.path.join(INTRUDER_DIR, f"{uuid.uuid4()}.jpg")
                        cv2.imwrite(img_path, frame)
                        
                        # Save log
                        save_log("intruder", detected_name, detected_score, img_path)
                        
                        # Send email alert in background
                        def send_alert():
                            send_intruder_alert(img_path, detected_score)
                        threading.Thread(target=send_alert, daemon=True).start()
                        
                        last_intruder_alert_time[detection_key] = current_time
                        logger.warning(f"INTRUDER DETECTED via webcam! Confidence: {detected_score:.2%}")
            else:
                # No face detected in this frame – reset streaks but keep previous status
                intruder_streak = 0
                authorized_streak = 0
        except Exception as e:
            logger.error(f"Error in video frame processing: {str(e)}")
        
        # Draw detection results on frame
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = detector.detect_faces(rgb)
            
            for face in faces:
                x, y, w, h = face["box"]
                x, y = max(0, x), max(0, y)
                color = (0, 0, 255) if detected_name == "INTRUDER" else (0, 255, 0)
                thickness = 3 if detected_name == "INTRUDER" else 2
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, thickness)
                label = f"{detected_name}: {detected_score:.2%}"
                cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Add warning text for intruders
                if detected_name == "INTRUDER":
                    cv2.putText(frame, "ALERT!", (x, y+h+25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        except Exception as e:
            logger.error(f"Error drawing on frame: {str(e)}")
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    camera.release()

@app.route("/detection_status")
def detection_status():
    """Get current detection status for webcam monitoring"""
    # Return the live, in-memory detection status from the webcam feed,
    # instead of relying on historical logs. This prevents old intruder
    # events from showing up as soon as the webcam is started.
    global current_detection_status
    # Ensure at least a minimal structure for the frontend
    status = current_detection_status or {}
    return jsonify({
        "status": status.get("status", "none"),
        "name": status.get("name"),
        "confidence": status.get("confidence", 0.0),
        "timestamp": status.get("timestamp"),
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
