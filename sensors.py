import RPi.GPIO as GPIO
import time

# ── Pin assignments — verify these match your physical HC-SR04 wiring ──
# NOTE: ECHO pin must go through a voltage divider (5V → 3.3V) to protect GPIO
TRIG = 27
ECHO = 4

SPEED_OF_SOUND_CM_PER_S = 34300


def setup():
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.1)   # let sensor settle


def get_distance():
    """Return distance in cm, or None on timeout."""
    # Send 10µs trigger pulse
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    timeout = time.time() + 0.04   # 40 ms max wait

    # Wait for ECHO to go high
    pulse_start = time.time()
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None

    # Wait for ECHO to go low
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None

    duration = pulse_end - pulse_start
    distance = (duration * SPEED_OF_SOUND_CM_PER_S) / 2
    return round(distance, 1)
