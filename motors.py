import RPi.GPIO as GPIO

# ── Pin assignments — verify these match your physical L298N wiring ──
IN1 = 17
IN2 = 18
IN3 = 22
IN4 = 23
ENA = 25   # PWM — left motors
ENB = 24   # PWM — right motors

_pwm_a = None
_pwm_b = None


def setup():
    global _pwm_a, _pwm_b
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in (IN1, IN2, IN3, IN4, ENA, ENB):
        GPIO.setup(pin, GPIO.OUT)
    _pwm_a = GPIO.PWM(ENA, 100)
    _pwm_b = GPIO.PWM(ENB, 100)
    _pwm_a.start(0)
    _pwm_b.start(0)


def _set_speed(speed):
    _pwm_a.ChangeDutyCycle(speed)
    _pwm_b.ChangeDutyCycle(speed)


def forward(speed=75):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    _set_speed(speed)


def backward(speed=75):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    _set_speed(speed)


def turn_left(speed=60):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    _set_speed(speed)


def turn_right(speed=60):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    _set_speed(speed)


def stop():
    for pin in (IN1, IN2, IN3, IN4):
        GPIO.output(pin, GPIO.LOW)
    _set_speed(0)


def cleanup():
    stop()
    GPIO.cleanup()
