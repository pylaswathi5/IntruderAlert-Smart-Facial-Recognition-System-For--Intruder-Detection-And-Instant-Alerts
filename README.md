# Smart Facial Recognition-Based Intruder Detection System

A comprehensive web-based facial recognition system for detecting authorized users and identifying intruders. Built with Flask, MTCNN, FaceNet, and modern web technologies.

## 🎯 Features

### Core Functionality
- **Face Recognition**: Advanced face detection and recognition using MTCNN and FaceNet
- **Intruder Detection**: Automatically identifies unauthorized individuals
- **Authorized User Management**: Add and manage authorized users with face images
- **Detection Logging**: Complete history of all face detections with timestamps
- **Real-time Webcam Monitoring**: Continuous face recognition via webcam with alerts
- **Alarm System**: Audio alerts when intruders are detected
- **Email Notifications**: Automatic email alerts to admin with intruder images

### User Interface
- **Modern Dashboard**: Beautiful, responsive UI with statistics
- **Image Preview**: Preview images before uploading
- **Detection History**: View all detection logs with detailed information
- **Intruder Gallery**: Browse all detected intruder images
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### Technical Features
- **Error Handling**: Robust error handling and validation
- **Image Validation**: Validates image formats and face detection
- **Secure File Handling**: Secure filename handling and file management
- **JSON Logging**: Persistent logging system with JSON storage
- **Performance Optimized**: Efficient face recognition pipeline

## 📋 Requirements

- Python 3.7 or higher
- Webcam (optional, for live detection)
- 4GB+ RAM recommended
- Internet connection (for initial model downloads)

## 🚀 Installation

### Step 1: Clone the Project

```bash
git clone https://github.com/pylaswathi5/IntruderAlert-Smart-Facial-Recognition-System-For--Intruder-Detection-And-Instant-Alerts.git
cd IntruderAlert-Smart-Facial-Recognition-System-For--Intruder-Detection-And-Instant-Alerts
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```


### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: TensorFlow and other ML libraries may take a few minutes to install.

### Step 4: Configure Email Notifications and Admin credentials(Optional)

1. Create a `.env` file in the project root folder (the same folder as `app.py`) by copying `.env.example`.

   **On Windows (PowerShell):**
   ```powershell
   Copy-Item .env.example .env
   ```

   **On Linux/Mac:**
   ```bash
   cp .env.example .env
   ```

2. Open the newly created `.env` file and replace the placeholder values with your own configuration:

   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your-16-character-app-password
   ADMIN_EMAIL=admin@gmail.com
   FLASK_SECRET_KEY=replace_with_a_long_random_secret
   ADMIN_USERNAME=choose_admin_username
   ADMIN_PASSWORD=choose_a_strong_password
   ```
3. **For Gmail:** Use an "App Password" (not your regular password). See `EMAIL_SETUP.md` for details.

### Step 5: Download FaceNet Model

The FaceNet model will be automatically downloaded on first run. Ensure you have an active internet connection.

## 🎮 Usage

### Starting the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

Open your web browser and navigate to:
```
http://localhost:5000
```

### Adding Authorized Users

1. Go to the "Add Authorized User" section
2. Enter the user's name
3. Upload a clear photo of the person's face
4. Click "Add User"

**Tips for best results**:
- Use clear, front-facing photos
- Good lighting conditions
- Face should be clearly visible
- Avoid sunglasses or masks

### Face Detection

1. Go to the "Face Detection" section
2. Upload an image containing a face
3. Click "Detect Face"
4. View the result (Authorized or Intruder)
5. **If intruder detected:** Alarm sound will play and email alert sent (if configured)

### Live Webcam Monitoring

1. Click "Live Webcam" in the sidebar
2. Allow browser/webcam access when prompted
3. The system will continuously monitor for faces
4. **When an intruder is detected:**
   - Alarm sound will play automatically
   - Email alert will be sent to admin (if configured)
   - Red alert banner will appear on screen
   - Intruder image will be saved
5. Green box = Authorized, Red box = Intruder

### Viewing Logs

- **Recent Detections**: Shown on the main dashboard
- **All Logs**: Click "View All Logs" to see complete history
- **Intruders**: Click "View Intruders" to see all detected intruder images

### Managing Users

- View all authorized users in the "Authorized Users" section
- Delete users by clicking the "Delete" button next to their name

## 📁 Project Structure

```
smart facialfacial/
├── app.py                 # Main Flask application
├── face_utils.py          # Face recognition utilities
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── detection_logs.json   # Detection logs (auto-generated)
├── authorized_faces/     # Authorized user images
│   └── [username]/
│       └── [images]
├── intruders/            # Detected intruder images
├── templates/            # HTML templates
│   ├── index.html        # Main page
│   ├── logs.html         # Logs page
│   ├── intruders.html    # Intruders gallery
│   └── video.html        # Webcam page
└── static/               # Static files
    └── style.css         # Stylesheet
```

## ⚙️ Configuration

### Recognition Threshold

The face recognition similarity threshold can be adjusted in `face_utils.py`:

```python
THRESHOLD = 0.7  # Adjust between 0.0 and 1.0
```

- **Lower values** (e.g., 0.6): More lenient, may have false positives
- **Higher values** (e.g., 0.8): Stricter, may miss authorized users

### Server Configuration

In `app.py`, you can modify:

```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size (16MB)
app.run(debug=True, host='0.0.0.0', port=5000)  # Server settings
```

## 🔧 Troubleshooting

### Common Issues

**1. "No face detected" error**
- Ensure the image contains a clear, front-facing face
- Check image quality and lighting
- Try a different image

**2. Camera not working**
- Check if webcam is connected and not used by another application
- Allow browser permissions for camera access
- Try a different browser

**3. Slow performance**
- Reduce image resolution before uploading
- Close other applications using the webcam
- For webcam: recognition runs every 5 frames for performance

**4. Import errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.7+)
- Try reinstalling TensorFlow if needed

**5. Model download issues**
- Ensure internet connection is active on first run
- Check firewall/antivirus settings
- Models are downloaded automatically by keras-facenet

## 🛡️ Security Considerations

- This is a demonstration project and should not be used for critical security applications without additional security measures
- Images are stored locally - ensure proper file system permissions
- Consider implementing authentication for production use
- Regularly backup detection logs and authorized user data

## 📊 Performance

- **Image Detection**: ~1-2 seconds per image (depends on hardware)
- **Webcam Detection**: ~5-10 FPS (processes every 5th frame)
- **Accuracy**: High accuracy with good quality images and proper lighting

## 🔮 Future Enhancements

Potential improvements for future versions:
- Database integration (SQLite/PostgreSQL)
- Email/SMS alerts for intruders
- Multi-face detection in single image
- Face recognition confidence visualization
- Export logs to CSV/Excel
- User authentication system
- API endpoints for integration
- Docker containerization

## 📝 License

This project is for educational and demonstration purposes.

## 👥 Credits

- **MTCNN**: Face detection
- **FaceNet (Keras)**: Face recognition embeddings
- **Flask**: Web framework
- **OpenCV**: Image processing
- **scikit-learn**: Similarity calculations

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📧 Support

For issues or questions, please create an issue in the repository or contact the development team.

---

**Note**: Make sure to test the system thoroughly before deploying in any production environment. The system's accuracy depends on image quality, lighting conditions, and the similarity threshold settings.

