# 💧 Water Drinking Reminder — User Guide

This guide explains how to install, configure, and use the Water Drinking Reminder application on a day-to-day basis.

---

## Table of Contents

1. [Before You Start — One-Time Setup](#1-before-you-start--one-time-setup)
2. [Starting the Application](#2-starting-the-application)
3. [Using the Main Window](#3-using-the-main-window)
4. [Setting an Optional Start Time](#4-setting-an-optional-start-time)
5. [Setting Your Reminder Interval](#5-setting-your-reminder-interval)
6. [The Elapsed Timer](#6-the-elapsed-timer)
7. [Starting and Stopping Reminders](#7-starting-and-stopping-reminders)
8. [The Reminder Video Popup](#8-the-reminder-video-popup)
9. [Minimising to the System Tray](#9-minimising-to-the-system-tray)
10. [Restoring the Window from the Tray](#10-restoring-the-window-from-the-tray)
11. [Exiting the Application](#11-exiting-the-application)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Before You Start — One-Time Setup

These steps only need to be done once on your computer.

### Step 1 — Install VLC Media Player

Download and install the free VLC media player from:

> https://www.videolan.org/vlc/

VLC handles the video and audio playback inside the reminder popup. The application will not work without it.

### Step 2 — Install Python packages

Open a Command Prompt or PowerShell window and run:

```
py -m pip install python-vlc pystray Pillow
```

Wait for all three packages to finish installing.

### Step 3 — Confirm your video file exists

The reminder video must be present at the following location:

```
C:\Users\MohammadFeeroz\OneDrive - IBM\Documents\BOB\Drinkwater\waterdrinkreminder.mp4
```

If the file has moved, open `water_drinking_reminder.py` in any text editor and update the `VIDEO_PATH` line near the top:

```python
VIDEO_PATH = r"C:\path\to\your\waterdrinkreminder.mp4"
```

---

## 2. Starting the Application

Double-click `water_drinking_reminder.py`, or open a terminal in the project folder and run:

```
py water_drinking_reminder.py
```

The main window will appear with four sections:

```
┌──────────────────────────────────────────────┐
│         💧 Water Drinking Reminder           │
│  ┌────────────────────────────────────────┐  │
│  │  Start Time  (optional)                │  │
│  │  Start at: [−][09][+] : [−][00][+]     │  │
│  │  ☐ Enable start time                   │  │
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │  Reminder Interval                     │  │
│  │  Hours: [−][0][+]  Minutes: [−][30][+] │  │
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │  Elapsed Since Last Reminder           │  │
│  │            --:--:--                    │  │
│  └────────────────────────────────────────┘  │
│              Status: Stopped                 │
│          [ ▶ Start ]  [ ■ Stop ]             │
└──────────────────────────────────────────────┘
```

---

## 3. Using the Main Window

| Element | Description |
|---|---|
| **Start Time** section | Optional HH:MM from which reminders begin (disabled by default) |
| **Reminder Interval** section | How often a reminder fires — set with +/− spinner buttons |
| **Elapsed Timer** | Live `HH:MM:SS` counter showing time since the last reminder |
| **Status** label | Current state and active configuration |
| **▶ Start** button | Begins the reminder countdown |
| **■ Stop** button | Cancels all pending reminders |

---

## 4. Setting an Optional Start Time

By default reminders start immediately when you press **▶ Start**. If you want them to begin at a specific time of day, use the Start Time section.

### How to enable

1. Tick the **Enable start time** checkbox.
2. The hour and minute spinners become active.
3. Use **−** and **+** to set the desired hour (0–23) and minute (0–59).

### Behaviour

| Situation | What happens |
|---|---|
| Chosen time is **in the future today** | App waits until that time, then begins the interval loop. Status shows *"Waiting — starts at HH:MM"* |
| Chosen time has **already passed today** | App schedules it for **tomorrow** at that time |
| Checkbox is **not ticked** | Reminders start immediately; start-time spinners are ignored |

> **Example:** It is 08:45 and you set start time to 09:00. Press Start — the app waits 15 minutes, then fires the first reminder and repeats at your set interval.

### How to disable

Untick the **Enable start time** checkbox. The spinners grey out and are ignored.

---

## 5. Setting Your Reminder Interval

Use the **−** and **+** buttons next to **Hours** and **Minutes** to set how often a reminder fires.

- Click **+** to increase the value by 1.
- Click **−** to decrease the value by 1 (cannot go below 0).
- You can also click inside the number field and type a value directly.

**Examples:**

| Goal | Hours | Minutes |
|---|---|---|
| Remind every 30 minutes | `0` | `30` |
| Remind every hour | `1` | `0` |
| Remind every 1.5 hours | `1` | `30` |
| Remind every 2 hours | `2` | `0` |

> **Rule:** The combined interval must be at least **1 minute** (both cannot be `0`). An error dialog will appear if you try to start with a zero interval.

> **Tip:** All spinners lock while the reminder is running. Stop the reminder first to change any value.

---

## 6. The Elapsed Timer

The **Elapsed Since Last Reminder** display counts up in `HH:MM:SS` format from the moment the scheduler starts (or from immediately after each reminder fires).

| Timer state | Meaning |
|---|---|
| `--:--:--` | Reminder is stopped |
| `00:00:00` | Just started or a reminder just fired |
| `00:14:32` | 14 minutes and 32 seconds since the last reminder |

The timer **resets to `00:00:00`** automatically each time a reminder popup appears, so you always know how long ago you last drank water.

---

## 7. Starting and Stopping Reminders

### Starting

1. Optionally enable and set a **Start Time**.
2. Set your desired **Hours** and **Minutes** interval.
3. Click **▶ Start**.
4. The status label confirms the configuration:
   - *"Status: Running — every 0h 30m"* (no start time)
   - *"Status: Waiting — starts at 09:00, then every 0h 30m"* (start time in future)
5. The elapsed timer resets to `00:00:00` and begins counting.
6. All spinners lock — settings cannot be changed while running.

### Stopping

1. Click **■ Stop** at any time.
2. Status returns to *"Status: Stopped"*, timer shows `--:--:--`.
3. All spinners unlock so you can adjust settings.
4. Any popup currently playing will finish on its own.

---

## 8. The Reminder Video Popup

When a reminder fires:

- A **400 × 280 px video window** appears in the **bottom-right corner** of your screen, just above the taskbar.
- It sits **on top of all other windows** so you cannot miss it.
- There is **no close button** — the window cannot be dismissed manually.
- The video plays with **sound** (ensure your system volume is not muted).
- Once the video finishes, the popup **closes automatically** and the elapsed timer resets.

You do not need to do anything — just watch, drink your water, and get back to work!

---

## 9. Minimising to the System Tray

Click the **✕ (Close/X) button** on the main window title bar.

The window disappears but the application **keeps running** in the background. A 💧 water-drop icon appears in your Windows notification tray (bottom-right of the taskbar, near the clock).

> Any active reminder continues to fire on schedule even while the window is hidden.

---

## 10. Restoring the Window from the Tray

1. Locate the 💧 icon in the system tray.
2. **Double-click** it, or **right-click** and choose **Show**.
3. The main window reappears.

---

## 11. Exiting the Application

To fully close the application and stop all reminders:

1. Right-click the 💧 tray icon.
2. Select **Exit**.

The reminder thread stops, the tray icon disappears, and the application closes completely.

> **Important:** Pressing ✕ on the main window does **not** exit the application — it only hides the window to the tray. You must use the tray **Exit** option to fully close it.

---

## 12. Troubleshooting

### The app opens but no popup appears

- Confirm you pressed **▶ Start** and the status label shows "Running" (not "Waiting").
- If the status shows "Waiting", a start time has been set that is still in the future — the first reminder fires after that time.
- Wait for the full interval to elapse — the first popup appears only after the complete countdown.

### The status shows "Waiting" but I don't want a start time

- Click **■ Stop**, untick the **Enable start time** checkbox, then click **▶ Start** again.

### "Video Not Found" error dialog

- The MP4 file is missing or has been moved.
- Check that `waterdrinkreminder.mp4` exists at the configured path (see [Step 3](#step-3--confirm-your-video-file-exists) above).

### Video popup appears but there is no sound

- Check that your system volume is not muted.
- Make sure VLC media player is installed and can play the MP4 file on its own.

### "VLC Not Found" error dialog on startup

- VLC Media Player is not installed on this computer.
- Download and install it from https://www.videolan.org/vlc/ then restart the application.

### `ModuleNotFoundError: No module named 'vlc'`

Run the installation command again:
```
py -m pip install python-vlc
```
Also confirm that the VLC desktop application itself is installed.

### `ModuleNotFoundError: No module named 'pystray'` or `'PIL'`

```
py -m pip install pystray Pillow
```

### The tray icon does not appear after pressing ✕

Some Windows versions hide new tray icons by default. Click the **˄ (Show hidden icons)** arrow in the taskbar notification area to find the 💧 icon.

### The application crashes on start

- Confirm you are running **Python 3.10 or later**: `py --version`
- Confirm all three packages are installed: `py -m pip show python-vlc pystray Pillow`
- Confirm VLC is installed and working independently.

---

*Water Drinking Reminder — stay hydrated! 💧*
