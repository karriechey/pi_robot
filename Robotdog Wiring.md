# Paw Patrol Robot — Complete Wiring Reference

## L293D Chip 1 — Breadboard Layout
Pin 1 at f30, Pin 9 at e30 (notch facing left, straddling center gap)

```
Row 30  f30 = Pin 1  (EN1)   e30 = Pin 9  (EN2)
Row 29  f29 = Pin 2  (IN1)   e29 = Pin 10 (IN3)
Row 28  f28 = Pin 3  (OUT1)  e28 = Pin 11 (OUT3)
Row 27  f27 = Pin 4  (GND)   e27 = Pin 12 (GND)
Row 26  f26 = Pin 5  (GND)   e26 = Pin 13 (GND)
Row 25  f25 = Pin 6  (OUT2)  e25 = Pin 14 (OUT4)
Row 24  f24 = Pin 7  (IN2)   e24 = Pin 15 (IN4)
Row 23  f23 = Pin 8  (VMOT)  e23 = Pin 16 (VCC)
```

---

## Power & Ground

| Connection | Breadboard Location |
|---|---|
| Pi Pin 2 (5V) | e23 (L293D VCC) |
| Pi Pin 6 (GND) | GND rail (blue) |
| 9V battery red (+) | f23 (L293D VMOT) |
| 9V battery black (-) | GND rail (blue) |
| GND rail top ↔ bottom | Link with jumper wire |

---

## Motor Control — Pi GPIO → L293D

| Pi Physical Pin | GPIO | Breadboard Row | L293D Function |
|---|---|---|---|
| Pin 22 | GPIO 25 | f30 | EN1 (left speed) |
| Pin 18 | GPIO 24 | e30 | EN2 (right speed) |
| Pin 11 | GPIO 17 | f29 | IN1 |
| Pin 15 | GPIO 22 | e29 | IN3 |
| Pin 16 | GPIO 23 | e24 | IN4 |
| Pin 12 | GPIO 18 | f24 | IN2 |

---

## Motor Wires → L293D Outputs

| Motor | Wire | Breadboard Row | L293D Pin |
|---|---|---|---|
| Left motors red (+) | OUT1 | f28 | Pin 3 |
| Left motors black (-) | OUT2 | f25 | Pin 6 |
| Right motors red (+) | OUT3 | e28 | Pin 11 |
| Right motors black (-) | OUT4 | e25 | Pin 14 |

---

## L293D GND Connections

| L293D Pin | Breadboard Row | Goes To |
|---|---|---|
| Pin 4 | f27 | GND rail |
| Pin 5 | f26 | GND rail |
| Pin 12 | e27 | GND rail |
| Pin 13 | e26 | GND rail |

---

## HC-SR04 Ultrasonic Sensor

| HC-SR04 Pin | Goes To |
|---|---|
| VCC | Pi Pin 2 (5V) |
| GND | GND rail |
| TRIG | Pi Pin 13 (GPIO 27) |
| ECHO | Breadboard e5 (into voltage divider) |

---

## Voltage Divider (ECHO pin protection — 5V → 3.3V)

```
HC-SR04 ECHO → e5 → [470Ω] → e6 → [10kΩ] → GND rail
                               │
                          jumper wire
                               │
                          Pi Pin 7 (GPIO 4)
```

| Component | Breadboard Location |
|---|---|
| 470Ω leg 1 | e5 (ECHO wire connects here too) |
| 470Ω leg 2 | e6 (shared junction) |
| 10kΩ leg 1 | d6 (shared junction) |
| 10kΩ leg 2 | GND rail |
| Jumper to Pi | c6 → Pi Pin 7 (GPIO 4) |

---

## OLED Display

| OLED Pin | Pi Physical Pin | GPIO |
|---|---|---|
| VCC | Pin 1 | 3.3V |
| GND | Pin 9 | GND |
| SDA | Pin 3 | GPIO 2 |
| SCL | Pin 5 | GPIO 3 |

---

## Camera Module

| Component | Connection |
|---|---|
| Camera module | CSI ribbon port on Pi |
| Blue side of ribbon | Faces toward HDMI ports |

---

## Pi GPIO Quick Reference

```
3.3V  · [1]  [2] · 5V
SDA   · [3]  [4] · 5V
SCL   · [5]  [6] · GND
GPIO4 · [7]  [8] · GPIO14
GND   · [9] [10] · GPIO15
GPIO17· [11][12] · GPIO18
GPIO27· [13][14] · GND
GPIO22· [15][16] · GPIO23
3.3V  · [17][18] · GPIO24
      · [19][20] · GND
      · [21][22] · GPIO25
      · [23][24] · GPIO8
GND   · [25][26] · GPIO7
```

---

## Power On/Off Order

### Power ON order
1. Plug USB power bank → Pi USB-C
2. Wait 30-40 seconds for boot
3. SSH in and confirm working
4. **Then** plug in 9V battery

### Power OFF order
1. Unplug 9V battery **first**
2. Then unplug power bank

---

## ⚠️ Safety Rules

1. **ALWAYS power off before touching any wire — every single time, no exceptions**
2. 9V battery connects **last**, disconnects **first**
3. Never reconnect or adjust wires while Pi is powered on
4. Common ground — Pi GND and 9V battery GND must share the same GND rail
5. HC-SR04 ECHO is 5V — always use voltage divider before connecting to GPIO
6. If a motor spins the wrong direction, swap its two wires on L293D — no code change needed

---

## Software Test Commands

```bash
# Test ultrasonic sensor
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
import sensors
sensors.setup()
import time
for i in range(5):
    d = sensors.get_distance()
    print('Distance:', d, 'cm')
    time.sleep(0.5)
GPIO.cleanup()
"

# Test OLED
python3 -c "
import display
display.setup()
display.show_face('happy')
import time
time.sleep(2)
display.show_face('alert')
time.sleep(2)
display.show_face('patrol')
"

# Test camera
python3 -c "
import camera
camera.setup()
camera.start()
import time
time.sleep(3)
print('Frame size:', len(camera.get_frame()), 'bytes')
camera.stop()
"

# Test motors (plug in 9V battery first)
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
import motors
motors.setup()
import time
print('Forward...')
motors.forward()
time.sleep(2)
print('Stop.')
motors.stop()
GPIO.cleanup()
"
```

---

## Status Checklist

| Component | Status |
|---|---|
| HC-SR04 sensor | ✅ Tested and working |
| OLED display | ✅ Tested and working |
| Camera stream | ✅ Tested and working |
| Motors |  Pi broke down here |
| YOLOv8 |  Install ultralytics later |
| Systemd autostart |  Last step after everything works |
