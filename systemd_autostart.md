# Systemd Autostart — Paw Patrol Robot

Run this **last**, after all components are tested and working.

---

## Step 1 — Create the service file

```bash
sudo nano /etc/systemd/system/robot.service
```

---

## Step 2 — Paste this inside nano

```ini
[Unit]
Description=Paw Patrol Robot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/karrie/pi_robot/main.py
WorkingDirectory=/home/karrie/pi_robot
Restart=on-failure
User=karrie

[Install]
WantedBy=multi-user.target
```

Save with **Ctrl+O → Enter → Ctrl+X**

---

## Step 3 — Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable robot.service
sudo systemctl start robot.service
```

---

## Step 4 — Verify it's running

```bash
sudo systemctl status robot.service
```

You should see `Active: active (running)` in green.

---

## Step 5 — Reboot to confirm autostart

```bash
sudo reboot
```

After reboot, robot starts automatically every time power bank is plugged in. No SSH needed.

---

## Useful Commands

| Command | What it does |
|---|---|
| `sudo systemctl start robot.service` | Start robot now |
| `sudo systemctl stop robot.service` | Stop robot now |
| `sudo systemctl restart robot.service` | Restart robot |
| `sudo systemctl enable robot.service` | Enable autostart on boot |
| `sudo systemctl disable robot.service` | Disable autostart |
| `sudo systemctl status robot.service` | Check if running |
| `journalctl -u robot.service -f` | See live logs |

---

## ⚠️ Notes

- Do this **after** motors, OLED, sensor, and camera are all tested
- If robot crashes on boot, SSH in and check logs with `journalctl`
- To debug, disable autostart temporarily and run `python3 main.py` manually
