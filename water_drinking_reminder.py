# =============================================================================
# Water Drinking Reminder
# =============================================================================
# Required installations:
#   py -m pip install python-vlc
#   py -m pip install pystray
#   py -m pip install Pillow
#
# Note: VLC media player must also be installed on your system:
#   https://www.videolan.org/vlc/
# =============================================================================

import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
import sys
from datetime import datetime, timedelta

# =============================================================================
# VLC DLL resolver
# python-vlc needs libvlc.dll to be loadable. If VLC is installed in a
# standard location we set PYTHON_VLC_LIB before importing vlc.
# =============================================================================
_VLC_SEARCH_PATHS = [
    r"C:\Program Files\VideoLAN\VLC\libvlc.dll",
    r"C:\Program Files (x86)\VideoLAN\VLC\libvlc.dll",
]

def _resolve_vlc_dll():
    """
    Try each known VLC install location. If found, tell python-vlc where
    the DLL lives via the PYTHON_VLC_LIB environment variable.
    Returns the path if found, None otherwise.
    """
    if os.environ.get("PYTHON_VLC_LIB"):
        return os.environ["PYTHON_VLC_LIB"]
    for path in _VLC_SEARCH_PATHS:
        if os.path.isfile(path):
            os.environ["PYTHON_VLC_LIB"] = path
            return path
    return None

_vlc_dll_path = _resolve_vlc_dll()

if _vlc_dll_path is None:
    import tkinter as _tk
    import tkinter.messagebox as _mb
    _r = _tk.Tk(); _r.withdraw()
    _mb.showerror(
        "VLC Not Found",
        "VLC Media Player is required but was not found on this computer.\n\n"
        "Please install it from:\n  https://www.videolan.org/vlc/\n\n"
        "After installing VLC, restart this application.",
    )
    sys.exit(1)

import vlc
import pystray
from PIL import Image, ImageDraw

# =============================================================================
# CONFIGURATION — update the path below if your video is in a different location
# =============================================================================
VIDEO_PATH = r"C:\Users\MohammadFeeroz\OneDrive - IBM\Documents\BOB\Drinkwater\waterdrinkreminder.mp4"


# =============================================================================
# Tray icon helper — draws a simple blue water-drop icon in memory
# =============================================================================
def _create_tray_image() -> Image.Image:
    """Create a simple water-drop PIL image for the system tray icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([16, 24, 48, 56], fill=(30, 144, 255, 255))
    draw.polygon([(32, 4), (16, 28), (48, 28)], fill=(30, 144, 255, 255))
    draw.ellipse([20, 30, 28, 38], fill=(173, 216, 230, 180))
    return img


# =============================================================================
# Spinner widget — an Entry flanked by − and + buttons
# =============================================================================
class Spinner(tk.Frame):
    """
    A compact numeric spinner: [ − ][ value ][ + ]
    Value is clamped between min_val and max_val.
    """

    def __init__(self, parent, min_val: int, max_val: int,
                 initial: int = 0, width: int = 4, **kwargs):
        super().__init__(parent, **kwargs)
        self._min = min_val
        self._max = max_val
        self._var = tk.StringVar(value=str(initial))

        btn_cfg = dict(width=2, relief=tk.FLAT, bg="#e0e0e0",
                       font=("Segoe UI", 10, "bold"), cursor="hand2")

        tk.Button(self, text="−", command=self._decrement, **btn_cfg).pack(side=tk.LEFT)
        tk.Entry(self, textvariable=self._var, width=width,
                 justify="center", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=2)
        tk.Button(self, text="+", command=self._increment, **btn_cfg).pack(side=tk.LEFT)

    # --- public API ---
    def get(self) -> int:
        """Return the current integer value, clamped to [min, max]."""
        try:
            return max(self._min, min(self._max, int(self._var.get())))
        except ValueError:
            return self._min

    def set(self, value: int):
        self._var.set(str(max(self._min, min(self._max, value))))

    def disable(self):
        for child in self.winfo_children():
            child.configure(state=tk.DISABLED)

    def enable(self):
        for child in self.winfo_children():
            child.configure(state=tk.NORMAL)

    # --- internal ---
    def _increment(self):
        self.set(self.get() + 1)

    def _decrement(self):
        self.set(self.get() - 1)


# =============================================================================
# Video Player — opens a borderless, always-on-top window at bottom-right
# =============================================================================
class VideoPopup:
    """
    Plays the reminder video in a Tkinter Toplevel window.
    - Positioned at the bottom-right corner of the screen.
    - Always on top of other windows.
    - No close button (overrideredirect).
    - Automatically closes when VLC reports the video has ended.
    """

    def __init__(self, parent: tk.Tk, video_path: str):
        self._parent = parent
        self._video_path = video_path
        self._instance: vlc.Instance | None = None
        self._player: vlc.MediaPlayer | None = None
        self._window: tk.Toplevel | None = None

    def show(self):
        """Build the popup window and start video playback."""
        if not os.path.isfile(self._video_path):
            messagebox.showerror(
                "Video Not Found",
                f"Cannot find the reminder video at:\n{self._video_path}",
            )
            return

        # --- Toplevel window setup ---
        self._window = tk.Toplevel(self._parent)
        self._window.overrideredirect(True)        # no title bar / close button
        self._window.attributes("-topmost", True)

        popup_w, popup_h = 400, 280
        screen_w = self._parent.winfo_screenwidth()
        screen_h = self._parent.winfo_screenheight()
        x = screen_w - popup_w - 20
        y = screen_h - popup_h - 60               # above taskbar
        self._window.geometry(f"{popup_w}x{popup_h}+{x}+{y}")
        self._window.configure(bg="black")

        # Canvas that VLC renders into
        canvas = tk.Canvas(self._window, bg="black", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self._window.update()

        # --- VLC setup ---
        self._instance = vlc.Instance("--no-xlib")
        self._player = self._instance.media_player_new()
        media = self._instance.media_new(self._video_path)
        self._player.set_media(media)

        hwnd = canvas.winfo_id()
        if sys.platform == "win32":
            self._player.set_hwnd(hwnd)
        elif sys.platform == "darwin":
            self._player.set_nsobject(hwnd)
        else:
            self._player.set_xwindow(hwnd)

        self._player.play()
        self._window.after(500, self._check_finished)

    def _check_finished(self):
        """Close the popup once VLC reports the video has ended."""
        if self._player is None or self._window is None:
            return
        state = self._player.get_state()
        if state in (vlc.State.Ended, vlc.State.Error, vlc.State.Stopped):
            self._close()
        else:
            self._window.after(500, self._check_finished)

    def _close(self):
        """Stop the player and destroy the popup window."""
        if self._player:
            self._player.stop()
            self._player.release()
            self._player = None
        if self._instance:
            self._instance.release()
            self._instance = None
        if self._window:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
            self._window = None


# =============================================================================
# Reminder Scheduler — runs in a background thread
# =============================================================================
class ReminderScheduler:
    """
    Optionally waits until a configured start time, then fires a reminder
    popup every <interval> seconds.  All timing runs in a daemon thread;
    UI updates are posted back via root.after().
    """

    def __init__(self, root: tk.Tk, get_interval_seconds,
                 get_start_time, on_tick):
        """
        Parameters
        ----------
        root               : Tkinter root window
        get_interval_seconds : callable → float  (reminder interval)
        get_start_time     : callable → datetime | None
                             Returns the next datetime when reminders should
                             begin, or None to start immediately.
        on_tick            : callable(elapsed_seconds: int)
                             Called every second on the main thread so the
                             GUI can update the elapsed-time display.
        """
        self._root = root
        self._get_interval = get_interval_seconds
        self._get_start_time = get_start_time
        self._on_tick = on_tick
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        """Start the background reminder thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the background thread to stop."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    def _sleep_chunked(self, seconds: float) -> bool:
        """
        Sleep for `seconds` in 1-second increments.
        Returns True if the sleep completed, False if stop was requested.
        """
        elapsed = 0.0
        while elapsed < seconds:
            if self._stop_event.is_set():
                return False
            time.sleep(1)
            elapsed += 1
        return True

    def _run(self):
        """Thread body: honour start time → repeat interval loop."""
        # --- Phase 1: wait until start time (if configured) ---
        start_dt = self._get_start_time()
        if start_dt is not None:
            delay = (start_dt - datetime.now()).total_seconds()
            if delay > 0:
                if not self._sleep_chunked(delay):
                    return   # stopped during wait

        # --- Phase 2: repeat reminder loop ---
        session_elapsed = 0   # seconds since scheduler started (after start-time wait)
        while not self._stop_event.is_set():
            interval = self._get_interval()
            # Count down the interval, ticking the elapsed timer every second
            for _ in range(int(interval)):
                if self._stop_event.is_set():
                    return
                time.sleep(1)
                session_elapsed += 1
                # Post tick to main thread
                se = session_elapsed
                self._root.after(0, self._on_tick, se)

            if not self._stop_event.is_set():
                # Fire the reminder and reset the per-interval elapsed counter
                self._root.after(0, self._root.event_generate, "<<ShowReminder>>")
                session_elapsed = 0
                self._root.after(0, self._on_tick, 0)


# =============================================================================
# Main Application
# =============================================================================
class WaterReminderApp:
    """
    Orchestrates the Tkinter GUI, system-tray icon, video popups, and
    the background reminder scheduler.

    New in this version
    -------------------
    * Start Time — optional HH:MM from which reminders begin.
    * Interval spinners — +/- buttons on hours and minutes.
    * Elapsed timer — shows time since the last reminder (or since start).
    """

    def __init__(self):
        self._root = tk.Tk()
        self._root.title("💧 Water Drinking Reminder")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)

        # Custom event fired by the scheduler thread
        self._root.bind("<<ShowReminder>>", self._on_reminder)

        self._scheduler = ReminderScheduler(
            self._root,
            self._get_interval_seconds,
            self._get_start_datetime,
            self._on_scheduler_tick,
        )
        self._tray_icon: pystray.Icon | None = None
        self._tray_thread: threading.Thread | None = None

        self._build_gui()

    # ------------------------------------------------------------------
    # GUI construction
    # ------------------------------------------------------------------
    def _build_gui(self):
        root = self._root
        pad = {"padx": 14, "pady": 6}

        # ── Title ──────────────────────────────────────────────────────
        tk.Label(
            root,
            text="💧 Water Drinking Reminder",
            font=("Segoe UI", 14, "bold"),
            fg="#1e90ff",
        ).grid(row=0, column=0, columnspan=2, pady=(16, 6))

        # ── Start Time ─────────────────────────────────────────────────
        st_frame = tk.LabelFrame(root, text="Start Time  (optional)", padx=10, pady=8)
        st_frame.grid(row=1, column=0, columnspan=2, **pad, sticky="ew")

        tk.Label(st_frame, text="Start at:").grid(row=0, column=0, sticky="e", padx=4)

        # Use today's wall-clock time as the default
        now = datetime.now()
        self._start_hour_spin = Spinner(st_frame, 0, 23, initial=now.hour)
        self._start_hour_spin.grid(row=0, column=1, padx=2)

        tk.Label(st_frame, text=":", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=2)

        self._start_min_spin = Spinner(st_frame, 0, 59, initial=now.minute)
        self._start_min_spin.grid(row=0, column=3, padx=2)

        self._use_start_time = tk.BooleanVar(value=False)
        tk.Checkbutton(
            st_frame,
            text="Enable start time",
            variable=self._use_start_time,
            command=self._toggle_start_time,
        ).grid(row=0, column=4, padx=(12, 0))

        # Spinners start disabled until checkbox is ticked
        self._start_hour_spin.disable()
        self._start_min_spin.disable()

        # ── Reminder Interval ──────────────────────────────────────────
        iv_frame = tk.LabelFrame(root, text="Reminder Interval", padx=10, pady=8)
        iv_frame.grid(row=2, column=0, columnspan=2, **pad, sticky="ew")

        tk.Label(iv_frame, text="Hours:").grid(row=0, column=0, sticky="e", padx=4)
        self._hours_spin = Spinner(iv_frame, 0, 23, initial=0)
        self._hours_spin.grid(row=0, column=1, padx=2)

        tk.Label(iv_frame, text="Minutes:").grid(row=0, column=2, sticky="e", padx=(12, 4))
        self._minutes_spin = Spinner(iv_frame, 0, 59, initial=30)
        self._minutes_spin.grid(row=0, column=3, padx=2)

        # ── Elapsed Timer ──────────────────────────────────────────────
        timer_frame = tk.LabelFrame(root, text="Elapsed Since Last Reminder", padx=10, pady=8)
        timer_frame.grid(row=3, column=0, columnspan=2, **pad, sticky="ew")

        self._timer_var = tk.StringVar(value="--:--:--")
        tk.Label(
            timer_frame,
            textvariable=self._timer_var,
            font=("Segoe UI", 18, "bold"),
            fg="#1e90ff",
            width=10,
        ).pack()

        # ── Status ─────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Status: Stopped")
        tk.Label(root, textvariable=self._status_var, fg="#57606a").grid(
            row=4, column=0, columnspan=2, pady=4
        )

        # ── Start / Stop buttons ───────────────────────────────────────
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(4, 18))

        self._start_btn = tk.Button(
            btn_frame,
            text="▶  Start",
            width=10,
            bg="#1e90ff",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._start_reminder,
        )
        self._start_btn.pack(side=tk.LEFT, padx=8)

        self._stop_btn = tk.Button(
            btn_frame,
            text="■  Stop",
            width=10,
            bg="#dc3545",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            state=tk.DISABLED,
            command=self._stop_reminder,
        )
        self._stop_btn.pack(side=tk.LEFT, padx=8)

    # ------------------------------------------------------------------
    # Start-time checkbox toggle
    # ------------------------------------------------------------------
    def _toggle_start_time(self):
        """Enable or disable the start-time spinners based on the checkbox."""
        if self._use_start_time.get():
            self._start_hour_spin.enable()
            self._start_min_spin.enable()
        else:
            self._start_hour_spin.disable()
            self._start_min_spin.disable()

    # ------------------------------------------------------------------
    # Interval / start-time helpers
    # ------------------------------------------------------------------
    def _get_interval_seconds(self) -> float:
        """Return the configured interval in seconds (min 60 s)."""
        try:
            h = max(0, self._hours_spin.get())
            m = max(0, self._minutes_spin.get())
        except Exception:
            h, m = 0, 30
        total = h * 3600 + m * 60
        return float(max(60, total))

    def _get_start_datetime(self) -> "datetime | None":
        """
        Return the next wall-clock datetime at which reminders should begin,
        or None if start-time is disabled (start immediately).
        """
        if not self._use_start_time.get():
            return None
        h = self._start_hour_spin.get()
        m = self._start_min_spin.get()
        now = datetime.now()
        candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
        # If the chosen time is already past for today, schedule for tomorrow
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    def _validate_interval(self) -> bool:
        """Return False (and show an error) if the interval is 0."""
        h = self._hours_spin.get()
        m = self._minutes_spin.get()
        if h == 0 and m == 0:
            messagebox.showerror(
                "Invalid Interval",
                "The reminder interval must be at least 1 minute.\n"
                "Please set Hours or Minutes to a value above 0.",
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Elapsed timer tick (called from scheduler thread via root.after)
    # ------------------------------------------------------------------
    def _on_scheduler_tick(self, elapsed_seconds: int):
        """Update the elapsed-time display."""
        h = elapsed_seconds // 3600
        m = (elapsed_seconds % 3600) // 60
        s = elapsed_seconds % 60
        self._timer_var.set(f"{h:02d}:{m:02d}:{s:02d}")

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------
    def _start_reminder(self):
        if not self._validate_interval():
            return

        # Build a human-readable status string
        h = self._hours_spin.get()
        m = self._minutes_spin.get()
        interval_str = f"{h}h {m}m"

        if self._use_start_time.get():
            start_dt = self._get_start_datetime()
            start_str = start_dt.strftime("%H:%M") if start_dt else "now"
            # If start time is in the future, warn the user
            if start_dt and start_dt > datetime.now():
                self._status_var.set(
                    f"Status: Waiting — starts at {start_str}, then every {interval_str}"
                )
            else:
                self._status_var.set(f"Status: Running — every {interval_str}")
        else:
            self._status_var.set(f"Status: Running — every {interval_str}")

        self._timer_var.set("00:00:00")
        self._scheduler.start()
        self._start_btn.config(state=tk.DISABLED)
        self._stop_btn.config(state=tk.NORMAL)

        # Lock controls while running
        self._hours_spin.disable()
        self._minutes_spin.disable()
        self._start_hour_spin.disable()
        self._start_min_spin.disable()

    def _stop_reminder(self):
        self._scheduler.stop()
        self._status_var.set("Status: Stopped")
        self._timer_var.set("--:--:--")
        self._start_btn.config(state=tk.NORMAL)
        self._stop_btn.config(state=tk.DISABLED)

        # Re-enable controls
        self._hours_spin.enable()
        self._minutes_spin.enable()
        if self._use_start_time.get():
            self._start_hour_spin.enable()
            self._start_min_spin.enable()

    # ------------------------------------------------------------------
    # Reminder event (fired from scheduler via root.after)
    # ------------------------------------------------------------------
    def _on_reminder(self, _event=None):
        """Called on the main thread when it's time to show the video."""
        popup = VideoPopup(self._root, VIDEO_PATH)
        popup.show()

    # ------------------------------------------------------------------
    # System tray
    # ------------------------------------------------------------------
    def _build_tray_icon(self) -> pystray.Icon:
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._show_from_tray, default=True),
            pystray.MenuItem("Exit", self._exit_app),
        )
        return pystray.Icon(
            "WaterReminder",
            _create_tray_image(),
            "Water Drinking Reminder",
            menu,
        )

    def _minimize_to_tray(self):
        """Hide the main window and park the app in the system tray."""
        self._root.withdraw()
        if self._tray_icon is None:
            self._tray_icon = self._build_tray_icon()
            self._tray_thread = threading.Thread(
                target=self._tray_icon.run, daemon=True
            )
            self._tray_thread.start()

    def _show_from_tray(self, icon=None, item=None):
        """Restore the main window from the tray."""
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self._root.after(0, self._root.deiconify)

    def _exit_app(self, icon=None, item=None):
        """Stop everything and exit cleanly."""
        self._scheduler.stop()
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self._root.after(0, self._root.destroy)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def run(self):
        self._root.mainloop()


# =============================================================================
# Script entry point
# =============================================================================
if __name__ == "__main__":
    app = WaterReminderApp()
    app.run()
