# PAW Patrol Home Surveillance Robot

A Paw Patrol-themed home surveillance robot built on a **Raspberry Pi 4**. It patrols autonomously, avoids obstacles, streams live video, detects personal items via YOLOv8, and displays animated OLED expressions. Manual control is available through a mobile-friendly web interface.

---

## Hardware

| Component | Details |
|---|---|
| Computer | Raspberry Pi 4 |
| OS | Raspberry Pi OS Bullseye (32-bit) |
| Motor Driver | L298N |
| Motors | 2× DC motors (differential drive) |
| Ultrasonic Sensor | HC-SR04 |
| Display | OLED (I2C, 128×64) |
| Camera | Raspberry Pi Camera Module (CSI) |
| Power — Pi | USB power bank via USB-C |
| Power — Motors | 9V battery → L298N VIN terminal |
| TTS | `espeak` |

### Wiring Reference

| Signal | GPIO (BCM) | Notes |
|---|---|---|
| L298N IN1 | 17 | |
| L298N IN2 | 18 | |
| L298N IN3 | 22 | |
| L298N IN4 | 23 | |
| L298N ENA (left PWM) | 25 | |
| L298N ENB (right PWM) | 24 | |
| HC-SR04 TRIG | 27 | |
| HC-SR04 ECHO | 4 | **Must use voltage divider — ECHO is 5V** |
| OLED SDA | 2 | I2C |
| OLED SCL | 3 | I2C |
| Camera | CSI port | ribbon cable |

---

## Project Structure

```
pi_robot/
├── main.py             # Control loop + Bottle web server
├── motors.py           # L298N motor control
├── sensors.py          # HC-SR04 distance reading
├── display.py          # OLED animated faces
├── camera.py           # Camera stream + YOLOv8 detection
├── tts.py              # Paw Patrol text-to-speech phrases
├── templates/
│   └── index.html      # Mobile web control UI
├── robot.service       # systemd autostart service
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
sudo apt update
sudo apt install espeak python3-pip python3-picamera2
pip3 install -r requirements.txt
```

### 2. Download YOLOv8 nano model

```bash
# The model downloads automatically on first run, or manually:
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 3. Run manually

```bash
python3 main.py
# Web UI: http://<pi-ip>:8080
```

### 4. Autostart on boot

```bash
# Edit robot.service — update User= and WorkingDirectory= to match your Pi username/path
sudo cp robot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable robot.service
sudo systemctl start robot.service
```

---

## Web Interface

Open `http://<pi-ip>:8080` on any phone or browser.

- **Live camera stream** (MJPEG)
- **Mode toggle**: Autonomous ↔ Manual
- **D-pad controls** for manual driving
- **Status bar**: current mode, distance reading, detected items

---

## Build Order (Recommended)

1. Motors + HC-SR04 obstacle avoidance
2. OLED face states
3. Bottle web interface (manual control)
4. Camera live stream
5. YOLOv8 object detection
6. TTS phrases
7. systemd autostart

---

## Known Gotchas

- **GPIO pin mismatch** — always verify pin numbers in `motors.py` match physical wiring
- **HC-SR04 ECHO is 5V** — use a voltage divider to protect the Pi's 3.3V GPIO
- **32-bit OS required** — do not upgrade to 64-bit Bullseye (hardware compatibility)
- **Use `yolov8n.pt` only** — larger models are too slow for real-time use on Pi 4
- **Power bank** — do not use a MacBook USB-C charger (Power Delivery issues)
- **Non-printable Unicode** — if copying code from PDFs, watch for hidden characters causing syntax errors
