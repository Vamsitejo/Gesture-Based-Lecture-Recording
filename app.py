from flask import Flask, jsonify
import subprocess
import datetime
import os
import signal
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ===== CONFIG =====
RTSP_URL = "rtsp://username:password@ip:port/stream"
RECORD_FOLDER = "api_recordings"
RTSP_TRANSPORT = "tcp"

os.makedirs(RECORD_FOLDER, exist_ok=True)


def timestamped_filename(prefix="record"):
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(RECORD_FOLDER, f"{prefix}_{now}.mp4")


class Recorder:
    def __init__(self, rtsp):
        self.rtsp = rtsp
        self.proc = None
        self.current_file = None

    def start_recording(self):
        if self.proc is not None:
            print("[WARN] Already recording")
            return None

        fname = timestamped_filename("capture")

        cmd = [
            "ffmpeg",
            "-rtsp_transport", RTSP_TRANSPORT,
            "-i", self.rtsp,
            "-y",
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c:v", "copy",         # keep original video codec
            "-c:a", "aac",          # convert audio to AAC for MP4 compatibility
            "-b:a", "128k",
            "-movflags", "+faststart",
            fname
        ]

        print("[INFO] Starting FFmpeg:\n ", " ".join(cmd))

        # Create a log file to inspect FFmpeg output
        log_file = open(os.path.join(RECORD_FOLDER, "ffmpeg_log.txt"), "a")

        self.proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        self.current_file = fname
        print(f"[INFO] Recording started: {fname}")
        return fname

    def stop_recording(self):
        if self.proc is None:
            print("[WARN] Not recording")
            return None

        print("[INFO] Stopping FFmpeg...")
        try:
            if os.name == "nt":  # Windows
                self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.proc.send_signal(signal.SIGINT)

            # Wait for ffmpeg to finalize file
            try:
                self.proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                print("[WARN] FFmpeg not stopping, forcing terminate...")
                self.proc.terminate()
                self.proc.wait(timeout=3)

        except Exception as e:
            print("[ERROR] While stopping FFmpeg:", e)
            self.proc.kill()

        finished_file = self.current_file
        self.proc = None
        self.current_file = None

        # Check if file was created and has size
        if os.path.exists(finished_file) and os.path.getsize(finished_file) > 0:
            print(f"[INFO] Recording saved successfully: {finished_file}")
        else:
            print(f"[ERROR] Recording failed or empty file: {finished_file}")

        return finished_file


recorder = Recorder(RTSP_URL)


@app.route("/start-recording", methods=["GET"])
def start_recording():
    file = recorder.start_recording()
    if file:
        return jsonify({"status": "started", "file": file})
    else:
        return jsonify({"status": "error", "message": "Already recording"}), 400


@app.route("/stop-recording", methods=["GET"])
def stop_recording():
    file = recorder.stop_recording()
    if file:
        return jsonify({"status": "stopped", "file_saved": file})
    else:
        return jsonify({"status": "error", "message": "No recording in progress"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
