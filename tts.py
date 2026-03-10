"""
Text-to-speech using espeak (or pyttsx3 as fallback).
All phrases are Paw Patrol themed.
"""
import subprocess
import threading

_lock = threading.Lock()

# ── Paw Patrol phrases ──
PHRASES = {
    "startup":   "PAW Patrol is on a roll!",
    "obstacle":  "Ryder! Obstacle ahead! No job too big, no pup too small!",
    "patrol":    "Everest is on the case, patrolling the area!",
    "searching": "Skye here, scanning from above!",
    "shutdown":  "This pup has got to go! PAW Patrol out!",
}

ITEM_PHRASES = {
    "laptop":    "Chase is on the case! I found your laptop!",
    "backpack":  "Rubble on the double! I found a backpack!",
    "suitcase":  "Marshall here! I found a suitcase!",
    "handbag":   "Zuma here! I spotted a bag!",
    "remote":    "Rocky here, don't lose it! I found a remote!",
    "cell phone": "Chase is on the case! I found your phone!",
}
DEFAULT_ITEM_PHRASE = "Chase is on the case! I found your {item}!"


def _speak(text: str):
    """Run espeak in a subprocess. Non-blocking — called from a thread."""
    try:
        subprocess.run(
            ["espeak", "-s", "140", "-v", "en", text],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        # espeak not installed — silently skip
        pass


def say(text: str):
    """Speak text without blocking the caller."""
    with _lock:
        t = threading.Thread(target=_speak, args=(text,), daemon=True)
        t.start()


def say_phrase(key: str):
    phrase = PHRASES.get(key, f"PAW Patrol reporting: {key}")
    say(phrase)


def alert_item(items: list):
    for item in items:
        phrase = ITEM_PHRASES.get(item, DEFAULT_ITEM_PHRASE.format(item=item))
        say(phrase)
