import cv2
import mediapipe as mp
import time
import os
import requests

# ============== CONFIG ==============
RTSP_URL = "rtsp://username:password@ip:port/stream"
RECORD_FOLDER = "api_recordings"
os.makedirs(RECORD_FOLDER, exist_ok=True)

FRAME_SKIP = 2            # process 1 of every 2 frames
GESTURE_COUNTDOWN = 3.0   # seconds
LAST_DETECTION_HOLD = 0.5 # keep landmarks for 0.5s after lost
PROC_WIDTH = 640

START_API = "http://127.0.0.1:5001/start-recording"
STOP_API = "http://127.0.0.1:5001/stop-recording"

# ============== MEDIAPIPE SETUP ==============
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

# ============== FUNCTIONS ==============
def call_api(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print("API Error:", e)
        return False

def fingers_up(hand_landmarks, handedness="Right"):
    lm = hand_landmarks.landmark
    fingers = []

    # Thumb logic depends on hand orientation
    if handedness == "Right":
        fingers.append(1 if lm[4].x < lm[3].x else 0)
    else:
        fingers.append(1 if lm[4].x > lm[3].x else 0)

    for tip in [8, 12, 16, 20]:
        fingers.append(1 if lm[tip].y < lm[tip - 2].y else 0)
    return fingers

# ============== STATE MACHINE ==============
STATE_IDLE = "IDLE"
STATE_WAIT_FIST_START = "WAIT_FIST_START"
STATE_RECORDING = "RECORDING"
STATE_WAIT_FIST_STOP = "WAIT_FIST_STOP"

state = STATE_IDLE
countdown_start = None
is_recording = False
last_label = "Waiting for gesture..."
last_detection_time = 0
last_hand = None
last_handedness = "Right"

# ============== VIDEO CAPTURE ==============
cap = cv2.VideoCapture(0)
try:
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
except:
    pass

if not cap.isOpened():
    print("❌ Cannot open RTSP stream.")
    exit(1)

frame_idx = 0

# ============== MAIN LOOP ==============
while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("⚠️ Frame read failed, retrying...")
        time.sleep(0.2)
        continue

    frame_idx += 1
    h, w = frame.shape[:2]

    # Resize for faster mediapipe processing
    scale = PROC_WIDTH / float(w)
    small_frame = cv2.resize(frame, (PROC_WIDTH, int(h * scale)))
    img_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Skip some frames for speed
    detected_gesture = None
    if frame_idx % FRAME_SKIP == 0:
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            handLms = results.multi_hand_landmarks[0]
            handedness = results.multi_handedness[0].classification[0].label
            last_hand = handLms
            last_handedness = handedness
            last_detection_time = time.time()
        else:
            # keep previous detection for short time to avoid flicker
            if time.time() - last_detection_time > LAST_DETECTION_HOLD:
                last_hand = None

    # Draw landmarks (use last known if available)
    if last_hand is not None:
        mp_draw.draw_landmarks(frame, last_hand, mp_hands.HAND_CONNECTIONS)

        finger_state = fingers_up(last_hand, last_handedness)
        if finger_state == [1, 1, 1, 1, 1]:
            detected_gesture = "OPEN_PALM"
        elif finger_state == [0, 0, 0, 0, 0]:
            detected_gesture = "FIST"

    now = time.time()

    # ======= STATE LOGIC =======
    if state == STATE_IDLE:
        last_label = "Show OPEN PALM to start recording..."
        if detected_gesture == "OPEN_PALM":
            countdown_start = now
            state = STATE_WAIT_FIST_START
            last_label = "OPEN PALM detected — make FIST within 3s to START"

    elif state == STATE_WAIT_FIST_START:
        remaining = GESTURE_COUNTDOWN - (now - countdown_start)
        if remaining <= 0:
            state = STATE_IDLE
            last_label = "⏳ Timeout. Show OPEN PALM again."
        elif detected_gesture == "FIST":
            last_label = "🎥 Recording STARTED"
            print(last_label)
            if call_api(START_API):
                is_recording = True
                state = STATE_RECORDING
            else:
                last_label = "⚠️ Start API failed"
                state = STATE_IDLE
        else:
            last_label = f"Make FIST to START ({remaining:.1f}s)"

    elif state == STATE_RECORDING:
        last_label = "Recording... Show OPEN PALM to stop."
        if detected_gesture == "OPEN_PALM":
            countdown_start = now
            state = STATE_WAIT_FIST_STOP
            last_label = "OPEN PALM detected — make FIST within 3s to STOP"

    elif state == STATE_WAIT_FIST_STOP:
        remaining = GESTURE_COUNTDOWN - (now - countdown_start)
        if remaining <= 0:
            state = STATE_RECORDING
            last_label = "⏳ Timeout. Continue recording."
        elif detected_gesture == "FIST":
            last_label = "🛑 Recording STOPPED"
            print(last_label)
            if call_api(STOP_API):
                is_recording = False
                state = STATE_IDLE
            else:
                last_label = "⚠️ Stop API failed"
                state = STATE_RECORDING
        else:
            last_label = f"Make FIST to STOP ({remaining:.1f}s)"

    # ======= DISPLAY =======
    color = (0, 255, 0) if is_recording else (0, 0, 255)
    cv2.putText(frame, last_label, (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    if is_recording:
        cv2.circle(frame, (25, 40), 10, (0, 0, 255), -1)
        cv2.putText(frame, "REC", (45, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    cv2.imshow("Gesture-Based Recorder", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

# ============== CLEANUP ==============
cap.release()
cv2.destroyAllWindows()
hands.close()
print("✅ Clean exit.")
