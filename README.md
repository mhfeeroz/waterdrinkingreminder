# 💧 Water Drinking Reminder

A lightweight desktop application that plays a video reminder at a configurable interval to keep you hydrated throughout the day.

---

## Features

- **Tkinter GUI** — set reminder intervals with +/− spinners for hours and minutes
- **Optional start time** — choose an exact HH:MM at which reminders begin; if the time has already passed today it schedules for tomorrow automatically
- **Elapsed timer** — a live `HH:MM:SS` counter shows how long it has been since the last reminder fired (or since the scheduler started)
- **VLC-powered video popup** — plays an MP4 file with full audio support
- **Non-intrusive popup** — appears at the bottom-right corner of the screen, always on top, with no close button; auto-closes when the video finishes
- **System tray integration** — minimises to the notification tray instead of closing; restore or exit from the tray icon
- **Clean thread management** — background scheduler thread stops gracefully on exit

---

## Requirements

### Python
Python 3.10 or later (uses the `X | Y` union type hint syntax).

### VLC Media Player
The desktop VLC application must be installed on your system before the Python bindings will work.
Download from: https://www.videolan.org/vlc/

### Python packages

```bash
py -m pip install python-vlc pystray Pillow
```

| Package | Purpose |
|---|---|
| `python-vlc` | VLC Python bindings for audio + video playback |
| `pystray` | System tray icon and context menu |
| `Pillow` | Generates the tray icon image in memory |

`tkinter`, `threading`, and `datetime` ship with the Python standard library and require no separate installation.

---

## Project Structure

```
Drinkwater/
├── water_drinking_reminder.py   # Main application
├── waterdrinkreminder.mp4       # Reminder video (must exist at the configured path)
├── README.md                    # This file
└── USER_GUIDE.md                # End-user usage instructions
```

---

## Configuration

Open [`water_drinking_reminder.py`](water_drinking_reminder.py) and update the constant near the top of the file:

```python
VIDEO_PATH = r"C:\Users\MohammadFeeroz\OneDrive - IBM\Documents\BOB\Drinkwater\waterdrinkreminder.mp4"
```

Change this to the full path of your MP4 reminder video.

---

## Running the Application

```bash
py water_drinking_reminder.py
```

Or double-click the script if your system is configured to open `.py` files with the Python interpreter.

---

## Architecture Overview

The application is composed of five distinct components within a single file:

### `_create_tray_image()` — Tray Icon Factory
Draws a blue water-drop icon at runtime using `Pillow`, so no external image file is needed.

### `Spinner` — Reusable Numeric Spinner Widget
A `tk.Frame` subclass that wraps a `−` button, an `Entry`, and a `+` button. Values are clamped to a configured `[min, max]` range. Used for all four numeric fields (start-time hour, start-time minute, interval hour, interval minute).

### `VideoPopup` — Video Player
| Responsibility | Implementation |
|---|---|
| Borderless window | `overrideredirect(True)` |
| Always on top | `attributes("-topmost", True)` |
| Bottom-right positioning | `winfo_screenwidth/height` |
| Audio + video | `python-vlc` bound to a Tkinter canvas HWND |
| Auto-close | Polls `vlc.State` every 500 ms via `Toplevel.after()` |

### `ReminderScheduler` — Background Thread
1. **Phase 1 — Start-time wait:** if a start time is configured and is in the future, sleeps until that moment.
2. **Phase 2 — Repeat loop:** counts each second of the interval, posting a tick callback to the main thread every second (for the elapsed timer display). Fires `<<ShowReminder>>` at the end of each interval and resets the counter to zero.

All sleeping is done in 1-second increments so `stop()` is always responsive within one second.

### `WaterReminderApp` — Application Orchestrator
Owns the Tkinter root window, wires together the GUI, the scheduler, the tray icon, and the popup. Handles the `WM_DELETE_WINDOW` protocol to redirect the close button to a tray-minimise action rather than an exit.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Zero interval (0h 0m) | Error dialog; Start blocked |
| VLC desktop app not installed | Error dialog at startup; `sys.exit(1)` |
| Video file not found at `VIDEO_PATH` | Error dialog shown at reminder time; popup skipped |

---

## Known Limitations

- The popup size is hardcoded at 400 × 280 px. Adjust `popup_w` / `popup_h` in `VideoPopup.show()` if needed.
- Settings (interval, start time) are not persisted between sessions.
- On macOS the tray icon requires additional setup (the app must run as a proper GUI process, not from a plain terminal).

---

## License

Internal use. Not for redistribution.
