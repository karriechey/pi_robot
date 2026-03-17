"""
PAW Patrol Robot — Mac Demo
===========================
Runs the full web UI on your laptop using the built-in webcam.
No Raspberry Pi hardware required.

Install:  pip install bottle opencv-python
Run:      python3 demo.py
Web:      http://localhost:8080
"""
import math
import random
import subprocess
import threading
import time

import cv2
from bottle import Bottle, run, static_file, response

# ── Simulated motor state ─────────────────────────────────────────────────────
_motor_state = "stop"
_motor_lock = threading.Lock()


class _Motors:
    @staticmethod
    def setup(): pass

    @staticmethod
    def forward(speed=75):
        with _motor_lock:
            global _motor_state
            _motor_state = "forward"

    @staticmethod
    def backward(speed=75):
        with _motor_lock:
            global _motor_state
            _motor_state = "backward"

    @staticmethod
    def turn_left(speed=60):
        with _motor_lock:
            global _motor_state
            _motor_state = "left"

    @staticmethod
    def turn_right(speed=60):
        with _motor_lock:
            global _motor_state
            _motor_state = "right"

    @staticmethod
    def stop():
        with _motor_lock:
            global _motor_state
            _motor_state = "stop"

    @staticmethod
    def cleanup(): pass


motors = _Motors()


# ── Simulated ultrasonic sensor ───────────────────────────────────────────────
_sim_time_start = time.time()


class _Sensors:
    @staticmethod
    def setup(): pass

    @staticmethod
    def get_distance():
        """Oscillates between ~10 cm and ~120 cm to simulate driving around."""
        t = time.time() - _sim_time_start
        return round(60 + 50 * math.sin(t / 4), 1)


sensors = _Sensors()


# ── No-op OLED display ────────────────────────────────────────────────────────
class _Display:
    @staticmethod
    def setup(): pass

    @staticmethod
    def show_face(state="patrol"):
        print(f"[DISPLAY] face: {state}")


display = _Display()


# ── TTS using macOS `say` (falls back silently) ───────────────────────────────
PHRASES = {
    "startup":   "PAW Patrol is on a roll!",
    "obstacle":  "Ryder! Obstacle ahead! No job too big, no pup too small!",
    "patrol":    "Everest is on the case, patrolling the area!",
    "searching": "Skye here, scanning from above!",
    "shutdown":  "This pup has got to go! PAW Patrol out!",
}
ITEM_PHRASES = {
    "laptop":     "Chase is on the case! I found your laptop!",
    "backpack":   "Rubble on the double! I found a backpack!",
    "suitcase":   "Marshall here! I found a suitcase!",
    "handbag":    "Zuma here! I spotted a bag!",
    "remote":     "Rocky here, don't lose it! I found a remote!",
    "cell phone": "Chase is on the case! I found your phone!",
}
_tts_lock = threading.Lock()


def _speak(text):
    print(f"[TTS] {text}")
    try:
        subprocess.run(["say", text], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass  # not on macOS


class _TTS:
    @staticmethod
    def say(text):
        with _tts_lock:
            threading.Thread(target=_speak, args=(text,), daemon=True).start()

    @staticmethod
    def say_phrase(key):
        _TTS.say(PHRASES.get(key, f"PAW Patrol reporting: {key}"))

    @staticmethod
    def alert_item(items):
        for item in items:
            _TTS.say(ITEM_PHRASES.get(item, f"Chase is on the case! I found your {item}!"))


tts = _TTS()


# ── Camera (Mac webcam via OpenCV) ────────────────────────────────────────────
TRACKED_LABELS = {"remote", "laptop", "cell phone", "backpack", "handbag", "suitcase"}

_frame_lock = threading.Lock()
_latest_frame: bytes = b""
_detected_items: list = []
_cam_running = False

# Demo: randomly surface a detected item every ~10 s so the UI shows something
_DEMO_ITEMS = list(TRACKED_LABELS)


def _camera_loop():
    global _latest_frame, _detected_items, _cam_running

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[CAMERA] Could not open webcam — stream will be blank.")
        cap = None

    frame_count = 0
    next_detection_at = time.time() + 8

    while _cam_running:
        if cap is not None:
            ret, frame = cap.read()
            if ret:
                _, jpeg = cv2.imencode(".jpg", frame)
                with _frame_lock:
                    _latest_frame = jpeg.tobytes()

        frame_count += 1

        # Simulate a detection appearing briefly every ~10 s
        now = time.time()
        if now >= next_detection_at:
            item = random.choice(_DEMO_ITEMS)
            with _frame_lock:
                _detected_items = [item]
            print(f"[DEMO] Simulated detection: {item}")
            next_detection_at = now + random.uniform(8, 14)
        elif now >= next_detection_at - 3:
            with _frame_lock:
                _detected_items = []

        time.sleep(0.033)  # ~30 fps

    if cap is not None:
        cap.release()


def _start_camera():
    global _cam_running
    _cam_running = True
    threading.Thread(target=_camera_loop, daemon=True).start()


def _stop_camera():
    global _cam_running
    _cam_running = False


def get_frame() -> bytes:
    with _frame_lock:
        return _latest_frame


def get_detected_items() -> list:
    with _frame_lock:
        return list(_detected_items)


def mjpeg_generator():
    while True:
        frame = get_frame()
        if frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
        time.sleep(0.05)


# ── Robot mode ────────────────────────────────────────────────────────────────
_mode = "autonomous"
_mode_lock = threading.Lock()

OBSTACLE_DISTANCE_CM = 20


def get_mode():
    with _mode_lock:
        return _mode


def set_mode(new_mode):
    global _mode
    with _mode_lock:
        _mode = new_mode


def autonomous_loop():
    tts.say_phrase("startup")
    display.show_face("patrol")
    _alerted = set()

    while True:
        if get_mode() == "autonomous":
            dist = sensors.get_distance()
            if dist is not None and dist < OBSTACLE_DISTANCE_CM:
                motors.stop()
                display.show_face("alert")
                tts.say_phrase("obstacle")
                time.sleep(0.5)
                motors.turn_right()
                time.sleep(0.6)
                motors.stop()
                display.show_face("patrol")
            else:
                motors.forward()
                display.show_face("patrol")

            detected = get_detected_items()
            new_items = [i for i in detected if i not in _alerted]
            if new_items:
                tts.alert_item(new_items)
                _alerted.update(new_items)
            if not detected:
                _alerted.clear()
        else:
            time.sleep(0.05)

        time.sleep(0.1)


# ── Bottle web app ────────────────────────────────────────────────────────────
app = Bottle()


@app.route("/")
def index():
    return static_file("index.html", root="templates")


@app.route("/stream")
def stream():
    response.content_type = "multipart/x-mixed-replace; boundary=frame"
    return mjpeg_generator()


@app.route("/forward")
def web_forward():
    if get_mode() == "manual":
        motors.forward()
    return {"ok": True}


@app.route("/backward")
def web_backward():
    if get_mode() == "manual":
        motors.backward()
    return {"ok": True}


@app.route("/left")
def web_left():
    if get_mode() == "manual":
        motors.turn_left()
    return {"ok": True}


@app.route("/right")
def web_right():
    if get_mode() == "manual":
        motors.turn_right()
    return {"ok": True}


@app.route("/stop")
def web_stop():
    motors.stop()
    return {"ok": True}


@app.route("/mode/<new_mode>")
def web_set_mode(new_mode):
    if new_mode in ("auto", "manual"):
        set_mode("autonomous" if new_mode == "auto" else "manual")
        if new_mode == "manual":
            motors.stop()
            display.show_face("searching")
        else:
            display.show_face("patrol")
    return {"mode": get_mode()}


@app.route("/status")
def web_status():
    with _motor_lock:
        mstate = _motor_state
    return {
        "mode": get_mode(),
        "distance": sensors.get_distance(),
        "detected": get_detected_items(),
        "motors": mstate,
    }


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("PAW Patrol Demo — http://localhost:8080")
    print("Press Ctrl-C to stop.\n")

    _start_camera()
    threading.Thread(target=autonomous_loop, daemon=True).start()

    try:
        run(app, host="localhost", port=8080, quiet=True)
    except KeyboardInterrupt:
        pass
    finally:
        tts.say_phrase("shutdown")
        _stop_camera()
