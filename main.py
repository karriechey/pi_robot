"""
Paw Patrol Home Surveillance Robot
===================================
Main control loop + Bottle web server.

Run:  python3 main.py
Web:  http://<pi-ip>:8080
"""
import time
import threading
import RPi.GPIO as GPIO
from bottle import Bottle, run, template, response, request, static_file

import motors
import sensors
import display
import camera
import tts

# ── Config ──────────────────────────────────────────────────────────────
OBSTACLE_DISTANCE_CM = 20   # stop and turn if closer than this
WEB_HOST = "0.0.0.0"
WEB_PORT = 8080

# ── State ────────────────────────────────────────────────────────────────
mode = "autonomous"   # "autonomous" | "manual"
_mode_lock = threading.Lock()


def get_mode():
    with _mode_lock:
        return mode


def set_mode(new_mode):
    global mode
    with _mode_lock:
        mode = new_mode


# ── Autonomous control loop ───────────────────────────────────────────────
def autonomous_loop():
    tts.say_phrase("startup")
    display.show_face("patrol")

    _alerted_items = set()

    while True:
        current_mode = get_mode()

        if current_mode == "autonomous":
            distance = sensors.get_distance()

            if distance is not None and distance < OBSTACLE_DISTANCE_CM:
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

            # Alert on newly detected items (don't spam)
            detected = camera.get_detected_items()
            new_items = [i for i in detected if i not in _alerted_items]
            if new_items:
                tts.alert_item(new_items)
                _alerted_items.update(new_items)

            # Clear alert set when no items visible
            if not detected:
                _alerted_items.clear()

        else:
            # Manual mode — motors driven by web requests
            time.sleep(0.05)

        time.sleep(0.1)


# ── Bottle web app ────────────────────────────────────────────────────────
app = Bottle()


@app.route("/")
def index():
    return static_file("index.html", root="templates")


@app.route("/stream")
def stream():
    response.content_type = "multipart/x-mixed-replace; boundary=frame"
    return camera.mjpeg_generator()


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
    return {
        "mode": get_mode(),
        "distance": sensors.get_distance(),
        "detected": camera.get_detected_items(),
    }


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        motors.setup()
        sensors.setup()
        display.setup()
        camera.setup()
        camera.start()

        # Autonomous loop in background thread
        control_thread = threading.Thread(target=autonomous_loop, daemon=True)
        control_thread.start()

        # Web server — blocks main thread
        run(app, host=WEB_HOST, port=WEB_PORT, quiet=True)

    except KeyboardInterrupt:
        pass
    finally:
        tts.say_phrase("shutdown")
        camera.stop()
        motors.cleanup()
