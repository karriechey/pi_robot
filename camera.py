"""
Camera streaming + YOLOv8 object detection.
Runs in a background thread so it never blocks the motor control loop.

Tracked items: keys, wallet, laptop, cello case (mapped from COCO class names).
"""
import io
import threading
import time
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from ultralytics import YOLO

# ── Items we care about (COCO class names) ──
TRACKED_LABELS = {"remote", "laptop", "cell phone", "backpack", "handbag", "suitcase"}
# "keys" and "wallet" are not in COCO — treat them as custom targets if you fine-tune later

_frame_lock = threading.Lock()
_latest_frame: bytes = b""
_detected_items: list = []
_running = False
_thread = None

_model = None
YOLO_MODEL = "yolov8n.pt"
INFERENCE_EVERY_N_FRAMES = 5


def setup():
    global _model
    _model = YOLO(YOLO_MODEL)


def _camera_loop():
    global _latest_frame, _detected_items, _running

    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()

    frame_count = 0
    try:
        while _running:
            frame = picam2.capture_array()
            frame_count += 1

            # JPEG encode for MJPEG stream
            import cv2
            _, jpeg = cv2.imencode(".jpg", frame)
            with _frame_lock:
                _latest_frame = jpeg.tobytes()

            # Run YOLO every N frames to keep CPU load manageable
            if frame_count % INFERENCE_EVERY_N_FRAMES == 0:
                results = _model(frame, verbose=False)
                found = []
                for r in results:
                    for box in r.boxes:
                        label = r.names[int(box.cls)]
                        if label in TRACKED_LABELS:
                            found.append(label)
                with _frame_lock:
                    _detected_items = found

            time.sleep(0.03)   # ~30 fps cap
    finally:
        picam2.stop()


def start():
    global _running, _thread
    _running = True
    _thread = threading.Thread(target=_camera_loop, daemon=True)
    _thread.start()


def stop():
    global _running
    _running = False


def get_frame() -> bytes:
    with _frame_lock:
        return _latest_frame


def get_detected_items() -> list:
    with _frame_lock:
        return list(_detected_items)


def mjpeg_generator():
    """Generator that yields MJPEG frames for Bottle streaming response."""
    while True:
        frame = get_frame()
        if frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
        time.sleep(0.05)
