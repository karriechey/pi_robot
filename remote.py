"""
PAW Patrol Robot — Remote Control
==================================
Python desktop remote control client for the Pi robot.
Streams live video and sends keyboard commands over HTTP.

Install:  pip install pillow requests
Run:      python3 remote.py

Controls (in Manual mode):
  Arrow keys / WASD  — move
  Space / S          — stop
  M                  — toggle Auto / Manual mode
"""
import io
import threading
import tkinter as tk
from tkinter import ttk
import urllib.request

import requests
from PIL import Image, ImageTk

DEFAULT_HOST = "raspberrypi.local"
PORT = 8080

MOVE_KEYS = {
    "Up": "forward",    "w": "forward",
    "Down": "backward", "s": "backward",
    "Left": "left",     "a": "left",
    "Right": "right",   "d": "right",
    "space": "stop",
}


class RobotRemote(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PAW Patrol Remote Control")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")

        self._host = tk.StringVar(value=DEFAULT_HOST)
        self._base_url = ""
        self._mode = "autonomous"
        self._running = False
        self._stream_thread = None
        self._status_after = None

        self._build_ui()
        self.bind("<KeyPress>",   self._on_key_press)
        self.bind("<KeyRelease>", self._on_key_release)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        PAD = {"padx": 8, "pady": 4}

        # ── Connection bar ──
        conn_frame = tk.Frame(self, bg="#1a1a2e")
        conn_frame.pack(fill="x", **PAD)

        tk.Label(conn_frame, text="Pi address:", bg="#1a1a2e",
                 fg="#f9c74f", font=("Arial", 11)).pack(side="left")
        entry = tk.Entry(conn_frame, textvariable=self._host, width=22,
                         font=("Arial", 11), bg="#16213e", fg="white",
                         insertbackground="white", relief="flat")
        entry.pack(side="left", padx=(4, 8))
        self._connect_btn = tk.Button(
            conn_frame, text="Connect", command=self._connect,
            bg="#f9c74f", fg="#1a1a2e", font=("Arial", 11, "bold"),
            relief="flat", padx=10)
        self._connect_btn.pack(side="left")
        self._conn_label = tk.Label(conn_frame, text="", bg="#1a1a2e",
                                    fg="#aaa", font=("Arial", 10))
        self._conn_label.pack(side="left", padx=8)

        # ── Video stream ──
        self._video_label = tk.Label(self, bg="#000", width=640, height=480)
        self._video_label.pack()

        # ── Status bar ──
        status_frame = tk.Frame(self, bg="#1a1a2e")
        status_frame.pack(fill="x", **PAD)

        tk.Label(status_frame, text="Mode:", bg="#1a1a2e",
                 fg="#aaa", font=("Arial", 10)).pack(side="left")
        self._mode_label = tk.Label(status_frame, text="–", bg="#1a1a2e",
                                    fg="#f9c74f", font=("Arial", 10, "bold"))
        self._mode_label.pack(side="left", padx=(2, 14))

        tk.Label(status_frame, text="Distance:", bg="#1a1a2e",
                 fg="#aaa", font=("Arial", 10)).pack(side="left")
        self._dist_label = tk.Label(status_frame, text="– cm", bg="#1a1a2e",
                                    fg="#f9c74f", font=("Arial", 10, "bold"))
        self._dist_label.pack(side="left", padx=(2, 14))

        self._detected_label = tk.Label(status_frame, text="", bg="#1a1a2e",
                                        fg="#90e0ef", font=("Arial", 10))
        self._detected_label.pack(side="left")

        # ── Mode toggle + D-pad ──
        ctrl_outer = tk.Frame(self, bg="#1a1a2e")
        ctrl_outer.pack(pady=6)

        mode_frame = tk.Frame(ctrl_outer, bg="#1a1a2e")
        mode_frame.pack(pady=(0, 8))

        self._auto_btn = tk.Button(
            mode_frame, text="🤖 Auto", width=10,
            command=lambda: self._set_mode("auto"),
            bg="#f9c74f", fg="#1a1a2e", font=("Arial", 11, "bold"), relief="flat")
        self._auto_btn.pack(side="left", padx=4)

        self._manual_btn = tk.Button(
            mode_frame, text="🕹️ Manual", width=10,
            command=lambda: self._set_mode("manual"),
            bg="#16213e", fg="#f9c74f", font=("Arial", 11, "bold"),
            relief="flat", bd=2)
        self._manual_btn.pack(side="left", padx=4)

        dpad = tk.Frame(ctrl_outer, bg="#1a1a2e")
        dpad.pack()

        btn_cfg = dict(width=4, height=2, font=("Arial", 18),
                       bg="#16213e", fg="white", relief="flat",
                       activebackground="#0f3460")

        tk.Button(dpad, text="▲", **btn_cfg,
                  command=lambda: self._send("forward")).grid(row=0, column=1, padx=4, pady=4)
        tk.Button(dpad, text="◀", **btn_cfg,
                  command=lambda: self._send("left")).grid(row=1, column=0, padx=4, pady=4)
        tk.Button(dpad, text="■", width=4, height=2, font=("Arial", 18),
                  bg="#e63946", fg="white", relief="flat",
                  activebackground="#c1121f",
                  command=lambda: self._send("stop")).grid(row=1, column=1, padx=4, pady=4)
        tk.Button(dpad, text="▶", **btn_cfg,
                  command=lambda: self._send("right")).grid(row=1, column=2, padx=4, pady=4)
        tk.Button(dpad, text="▼", **btn_cfg,
                  command=lambda: self._send("backward")).grid(row=2, column=1, padx=4, pady=4)

        tk.Label(self, text="Keys: ↑↓←→ / WASD · Space=stop · M=mode toggle",
                 bg="#1a1a2e", fg="#555", font=("Arial", 9)).pack(pady=(0, 6))

    # ── Connection ──────────────────────────────────────────────────────────

    def _connect(self):
        host = self._host.get().strip()
        self._base_url = f"http://{host}:{PORT}"
        self._conn_label.config(text="Connecting…", fg="#aaa")
        self.update_idletasks()

        try:
            r = requests.get(f"{self._base_url}/status", timeout=3)
            r.raise_for_status()
        except Exception as e:
            self._conn_label.config(text=f"Failed: {e}", fg="#e63946")
            return

        self._conn_label.config(text="Connected", fg="#57cc99")
        self._connect_btn.config(text="Reconnect")
        self._running = True
        self._start_stream()
        self._poll_status()

    # ── MJPEG stream reader ─────────────────────────────────────────────────

    def _start_stream(self):
        if self._stream_thread and self._stream_thread.is_alive():
            return
        self._stream_thread = threading.Thread(
            target=self._stream_loop, daemon=True)
        self._stream_thread.start()

    def _stream_loop(self):
        url = f"{self._base_url}/stream"
        while self._running:
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    buf = b""
                    while self._running:
                        chunk = resp.read(4096)
                        if not chunk:
                            break
                        buf += chunk
                        # Find complete JPEG in the multipart stream
                        start = buf.find(b"\xff\xd8")
                        end   = buf.find(b"\xff\xd9")
                        if start != -1 and end != -1 and end > start:
                            jpg = buf[start:end + 2]
                            buf = buf[end + 2:]
                            self._update_frame(jpg)
            except Exception:
                if self._running:
                    import time; import time as _t; _t.sleep(1)

    def _update_frame(self, jpg_bytes: bytes):
        try:
            img = Image.open(io.BytesIO(jpg_bytes))
            img = img.resize((640, 480), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            # Must update label from main thread
            self._video_label.after(0, self._set_photo, photo)
        except Exception:
            pass

    def _set_photo(self, photo):
        self._video_label.config(image=photo)
        self._video_label.image = photo  # keep reference

    # ── Status polling ──────────────────────────────────────────────────────

    def _poll_status(self):
        if not self._running:
            return
        try:
            s = requests.get(f"{self._base_url}/status", timeout=2).json()
            self._mode = s.get("mode", "–")
            dist = s.get("distance")
            detected = s.get("detected", [])

            self._mode_label.config(
                text="Autonomous" if self._mode == "autonomous" else "Manual")
            self._dist_label.config(
                text=f"{dist} cm" if dist is not None else "– cm")
            self._detected_label.config(
                text=("👀 Spotted: " + ", ".join(detected)) if detected else "")
            self._update_mode_buttons()
        except Exception:
            pass

        self._status_after = self.after(1500, self._poll_status)

    # ── Commands ────────────────────────────────────────────────────────────

    def _send(self, action: str):
        if not self._base_url:
            return
        threading.Thread(
            target=lambda: requests.get(
                f"{self._base_url}/{action}", timeout=2),
            daemon=True).start()

    def _set_mode(self, mode: str):
        if not self._base_url:
            return
        try:
            r = requests.get(f"{self._base_url}/mode/{mode}", timeout=2).json()
            self._mode = r.get("mode", self._mode)
            self._update_mode_buttons()
        except Exception:
            pass

    def _update_mode_buttons(self):
        is_auto = self._mode == "autonomous"
        self._auto_btn.config(
            bg="#f9c74f" if is_auto else "#16213e",
            fg="#1a1a2e" if is_auto else "#f9c74f")
        self._manual_btn.config(
            bg="#f9c74f" if not is_auto else "#16213e",
            fg="#1a1a2e" if not is_auto else "#f9c74f")

    # ── Keyboard ────────────────────────────────────────────────────────────

    def _on_key_press(self, event):
        action = MOVE_KEYS.get(event.keysym)
        if action and self._mode == "manual":
            self._send(action)
        elif event.keysym.lower() == "m":
            next_mode = "manual" if self._mode == "autonomous" else "auto"
            self._set_mode(next_mode)

    def _on_key_release(self, event):
        if event.keysym in MOVE_KEYS and event.keysym != "space":
            if self._mode == "manual":
                self._send("stop")

    # ── Cleanup ─────────────────────────────────────────────────────────────

    def _on_close(self):
        self._running = False
        if self._status_after:
            self.after_cancel(self._status_after)
        self.destroy()


if __name__ == "__main__":
    app = RobotRemote()
    app.mainloop()
