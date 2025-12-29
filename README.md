# Gesture Based Lecture Recording

An AI-powered **gesture-controlled lecture recording system** that automatically starts and stops class recordings using **hand gestures**, exclusively recognized for **authorized staff**.

The system eliminates manual recording control by allowing lecturers to manage recording seamlessly during a class using simple hand gestures.

---

## 📌 Project Overview

This project uses **computer vision and hand gesture recognition** to control classroom recording:

- ✋ **Open Palm** → Initiates gesture confirmation
- ✊ **Fist** → Confirms action (Start / Stop recording)

Only **staff gestures** are considered valid, ensuring recordings are not triggered by students or others.

---

## 🧠 How It Works (High Level Flow)

1. Camera captures live video feed
2. MediaPipe detects hand landmarks
3. Gesture state machine validates gesture sequence
4. Flask API triggers FFmpeg recording
5. Recorded lecture is stored automatically

---

## 📁 Project Structure

```
Gesture-Based-Lecture-Recording/
│
├── api_recordings/            # Final recorded lecture videos
│
├── outputs/                   # Gesture detection output / debug recordings
│
├── app.py                     # Flask API to start/stop recording
├── gesture.py                 # Gesture detection & recording trigger logic
│
└── README.md                  # Project documentation
```

---

## ⚙️ Technologies Used

- Python
- OpenCV
- MediaPipe (Hand Tracking)
- Flask (Recording API)
- FFmpeg (Video recording)
- RTSP camera stream

---

## 📦 Python Dependencies

Install required packages using:

```bash
pip install opencv-python mediapipe flask flask-cors requests
```

> ⚠️ **FFmpeg must be installed separately and available in system PATH**.

---

## 🎥 Recording Control Logic

### Gesture Sequence

| Action | Gesture Flow |
|------|--------------|
| Start Recording | Open Palm → Fist (within 3 seconds) |
| Stop Recording | Open Palm → Fist (within 3 seconds) |

This **two-step confirmation** prevents accidental triggers.

---

## ▶️ How to Run

### 1️⃣ Start Recording API Server

```bash
python app.py
```

- Starts a Flask server on **port 5001**
- Controls FFmpeg-based RTSP recording

Available endpoints:
- `/start-recording`
- `/stop-recording`

---

### 2️⃣ Start Gesture Detection

```bash
python gesture.py
```

This will:
- Open camera feed
- Detect hand gestures in real time
- Display gesture state on screen
- Trigger start/stop recording APIs automatically

---

## 📂 Recordings & Outputs

- **Recorded lectures:** stored in `api_recordings/`
- **Gesture visualization/debug outputs:** stored in `outputs/`

Recorded files are saved with **timestamped filenames** for easy organization.

---

## 🖥️ On-Screen Indicators

- 🔴 **REC icon** → Recording in progress
- 🟢 Text prompts → Gesture guidance
- Bounding hand landmarks → Gesture visualization

---

## 🔐 Staff-Only Recognition

- System is designed to respond **only to staff gestures**
- Gesture flow and positioning reduce accidental triggers
- Can be extended with **face recognition or ID validation**

---

## 🚀 Applications

- Smart classrooms
- Lecture halls
- Training centers
- Online & hybrid education systems

---

## 🔮 Future Enhancements

- Staff face authentication
- Cloud storage integration
- Multi-camera classroom support
- Audio-based backup triggers
- Web dashboard for recordings

---

## 📜 License

This project is intended for **educational and research purposes**.

---

## 👤 Author

**Vamsi Tejo**

If you find this project useful, don’t forget to ⭐ the repository!

