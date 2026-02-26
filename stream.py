from flask import Flask, Response
import subprocess
import sys
import os
import cv2
import numpy as np

app = Flask(__name__)

if len(sys.argv) < 2:
    print("Usage: python stream.py <video_path>")
    sys.exit()

video_path = os.path.expanduser(sys.argv[1])

if not os.path.exists(video_path):
    print("Video not found")
    sys.exit()

print(f"Serving video: {video_path}")

# Get video size
cap = cv2.VideoCapture(video_path)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
cap.release()

# Start FFmpeg process
ffmpeg = subprocess.Popen(
    [
        "ffmpeg",
        "-re",
        "-stream_loop",
        "-1",
        "-i",
        video_path,
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)


def generate():
    while True:
        raw_frame = ffmpeg.stdout.read(width * height * 3)
        if not raw_frame:
            continue

        frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
        ret, buffer = cv2.imencode(".jpg", frame)

        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@app.route("/")
def home():
    return '<h2>TN_IMPACT Live Stream</h2><img src="/video">'


@app.route("/video")
def video():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
