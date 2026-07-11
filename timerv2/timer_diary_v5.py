"""
TimerDiary v5 — the old timer's file format, with the bottlenecks removed.

THE BIG IDEA (different from v4): the day file is the app. One text pane =
today's .txt, exactly like the old timer + notepad workflow:

    --- Session start at: 2026-06-02 13:26:33
    Start;2026-06-02;13:26:33;0;0;0
    Stop;2026-06-02;14:04:17;0;20;1229
    --- Break duration: 0:10:3 jt viestei jne      <- you type notes right here
    ...
    --- Session reset, studying duration: 1:29:14

You type freely between/after the lines, the timer inserts its lines at the
end, everything autosaves. No more manually creating a notepad file.

Fixes for the old bottlenecks:
  - launches at Windows startup (asked once on first run, toggle in Tools)
  - today's file auto-created with a date header + yesterday's totals
  - the "day" rolls over at 04:00, not midnight — a 00:30 grind stays in
    the evening's file (configurable in Tools)
  - autosave every 10 s and on every timer event; weekly backups
  - crash recovery: if the app/PC dies mid-session, next launch offers to
    keep it running or log it

New in v5:
  - IDLE DETECTION: walked away without pressing Stop? When you come back
    it offers to log the away time as a break, retroactively. (Tools menu,
    default 10 min.)
  - Every work/break interval is ALSO written to sessions.csv
    (';' delimited -> double-click opens right in Finnish Excel;
    pandas: pd.read_csv(p, sep=';')). Columns:
    date;type;start;end;minutes;task;note  — type is work|break, so
    "where does my time leak" is one pivot table away.
  - Close with timer running -> option to keep it running across a reboot.

New in v5.1:
  - the task box now DOES something visible: starting (or changing) a task
    writes "--- Task: thesis" into the day file, so the notes always say
    what you were doing. Switch button / Ctrl+Enter / plain Enter in the
    task box splits the log mid-session when you change tasks.
  - FLOATING BREAK PILL: on Stop, a small always-on-top "break 12:34"
    appears bottom-right, turns red after 15 min, one click resumes work.
    No more invisible breaks behind the browser. (Tools menu to disable.)
  - GLOBAL HOTKEY: Ctrl+Alt+Space starts/stops from anywhere, no alt-tab
    (beeps high = working, low = break).
  - COPY FOR AI REVIEW (View menu): puts the week's (or day's) totals,
    per-task hours and full diary text on the clipboard — paste into
    Claude on Friday and ask what slipped.
  - DEADLINE COUNTDOWN (Tools menu): "thesis: 18d left · 6.2/10h wk" in
    the totals line. Clear the name to remove it.

New in v5.2:
  - DAY TIMELINE: a thin 00-24 bar under the task row — blue = focus,
    orange = breaks, so you see the shape of your day at a glance.
  - deadline dot: green = currently working on the deadline task,
    orange = on break mid-session, grey = not on it.
  - task dropdown now remembers every task the moment you start it
    (was: only after a 30s+ interval reached the csv).
  - global hotkey is configurable (Tools menu); default Ctrl+Shift+Space.
  - hours shown with two decimals everywhere (0.25 h = 15 min).

New in v5.4:
  - single-instance guard (named mutex), atomic merge-on-save settings,
    diary-folder change carries today's file along (see 2026-07-11 incident).
  - ESTIMATED SLEEP BAND on the day timeline: dark band from ~bed to ~wake,
    derived from last night's imported sleep total + your logging pattern
    (bed ~= last logged event + 1 h, else 00:00; clipped to first activity).
    Labeled "zzz (est.)" — it's an estimate until an export with real
    bed/wake times is available. The incentive: the gap between your last
    evening log and the band start is your doomscroll tax, visible.

New in v5.3:
  - SIGNAL METER: each new day file gets a "SIGNAL: ..." line (carried over
    from yesterday — edit it right in the text, comma-separated keywords,
    e.g. "SIGNAL: thesis, day job"). Work on matching tasks counts as signal;
    the totals line shows today's and the week's signal %, and the timeline
    paints signal work GREEN vs other work blue. 100% signal, 0% noise.
  - HEALTH IMPORT: point File > "Health import folder..." at a folder where
    an Apple Health export app drops CSVs (e.g. Health Auto Export). Each
    day's header gets "(sleep 6h12m, workout 45m)" automatically — so the
    Friday AI review can answer "do I work worse after short sleep?".
    Fallback: any csv with date + sleep/workout columns works, e.g. a
    hand-made health.csv with "date;sleep_h;workout_min".

Kept from v4: weekly/monthly summary, 8-week trend chart, search across all
day files, .ics calendar export, add past session, compact always-on-top
mode, recent-task dropdown, daily target bar, weekly auto-backup.

Data: %APPDATA%\\TimerDiary   (sessions.csv, settings, backups)
Day files: %APPDATA%\\TimerDiary\\diary\\YYYY-MM-DD.txt by default —
File > "Change diary folder..." to point it at OneDrive for sync.

Hotkeys: Ctrl+Space start/stop · Ctrl+R reset session · F5 timestamp
Build the exe: run build_exe.bat (PyInstaller one-file, no console).
"""

import csv
import ctypes
import ctypes.wintypes
import json
import os
import queue
import re
import shutil
import sys
import threading
import time
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

APP_NAME = "TimerDiary"

# ---------------- storage ----------------

def data_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d

SESSIONS_CSV = os.path.join(data_dir(), "sessions.csv")
RUNNING_JSON = os.path.join(data_dir(), "running.json")
SETTINGS_JSON = os.path.join(data_dir(), "settings.json")
CSV_HEADER = ["date", "type", "start", "end", "minutes", "task", "note"]


def load_settings():
    try:
        with open(SETTINGS_JSON, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(s):
    """Merge-and-replace: keys another writer added since our load survive,
    and the write is atomic so a crash can't leave a half-written file."""
    merged = load_settings()
    merged.update(s)
    s.update(merged)
    tmp = SETTINGS_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(merged, f)
    os.replace(tmp, SETTINGS_JSON)


def already_running():
    """Single-instance guard via a named Windows mutex. Two instances
    logging to different folders is how diary text gets lost."""
    try:
        ctypes.windll.kernel32.CreateMutexW(None, False, "TimerDiary_single")
        return ctypes.windll.kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS
    except Exception:
        return False


def read_rows():
    """All csv rows, normalised to 7 columns (v4 files had no 'type')."""
    if not os.path.exists(SESSIONS_CSV):
        return []
    with open(SESSIONS_CSV, newline="", encoding="utf-8") as f:
        raw = list(csv.reader(f, delimiter=";"))
    out = []
    for r in raw[1:]:
        if len(r) == 6:          # v4 format: date;start;end;minutes;task;note
            r = [r[0], "work"] + r[1:]
        if len(r) >= 5:
            out.append(r + [""] * (7 - len(r)))
    return out


def append_row(row):
    new = not os.path.exists(SESSIONS_CSV)
    with open(SESSIONS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if new:
            w.writerow(CSV_HEADER)
        w.writerow(row)


def recent_tasks(limit=12):
    seen, out = set(), []
    for r in reversed(read_rows()):
        t = r[5].strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
        if len(out) >= limit:
            break
    return out


def day_totals(date_iso):
    """(work_min, break_min) for a date string."""
    w = b = 0
    for r in read_rows():
        if r[0] != date_iso:
            continue
        try:
            m = int(r[4])
        except ValueError:
            continue
        if r[1] == "break":
            b += m
        else:
            w += m
    return w, b


def weekly_totals(n_weeks=8):
    today = dt.date.today()
    this_mon = today - dt.timedelta(days=today.weekday())
    weeks = {this_mon - dt.timedelta(weeks=i): 0 for i in range(n_weeks - 1, -1, -1)}
    for r in read_rows():
        if r[1] == "break":
            continue
        try:
            d = dt.date.fromisoformat(r[0])
            m = int(r[4])
        except ValueError:
            continue
        mon = d - dt.timedelta(days=d.weekday())
        if mon in weeks:
            weeks[mon] += m
    return sorted(weeks.items())


def backup_if_due():
    if not os.path.exists(SESSIONS_CSV):
        return
    bdir = os.path.join(data_dir(), "backups")
    os.makedirs(bdir, exist_ok=True)
    today = dt.date.today()
    newest = None
    for fn in os.listdir(bdir):
        try:
            newest = max(newest or dt.date.min, dt.date.fromisoformat(fn[9:19]))
        except (ValueError, IndexError):
            continue
    if newest and (today - newest).days < 7:
        return
    shutil.copy2(SESSIONS_CSV,
                 os.path.join(bdir, f"sessions_{today.isoformat()}.csv"))


# ---------------- health csv import (best effort) ----------------

def _parse_any_date(s):
    s = s.strip()[:10]
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _dur_minutes(s):
    """'7h 54m' / '45m' / '7h' -> minutes, else None."""
    m = re.fullmatch(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?", s.strip())
    if m and (m.group(1) or m.group(2)):
        return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
    return None


def _num(s):
    """Number tolerant of Finnish decimal commas and nbsp thousand
    separators ('2\\xa0152', '24,4'). Ranges like '52-149' -> None."""
    s = s.strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_health_dir(hdir):
    """Scan csv files for date + sleep/workout/steps columns.
    Returns {date_iso: {"sleep_h", "workout_min", "steps"}}.
    Understands Health Auto Export headers ('Sleep Analysis [Asleep] (hr)'),
    Health App Data Export Tool ('Sleep' = '7h 54m', d.m.yyyy dates,
    decimal commas) and a hand-made 'date;sleep_h;workout_min' file.
    Later files/rows overwrite earlier."""
    data = {}
    try:
        names = sorted(os.listdir(hdir))
    except OSError:
        return data
    for fn in names:
        if not fn.lower().endswith(".csv"):
            continue
        try:
            with open(os.path.join(hdir, fn), encoding="utf-8-sig",
                      newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                delim = ";" if sample.count(";") > sample.count(",") else ","
                rows = list(csv.reader(f, delimiter=delim))
        except OSError:
            continue
        if len(rows) < 2:
            continue
        hdr = [h.strip().lower() for h in rows[0]]

        def col(*words):
            for i, h in enumerate(hdr):
                if any(w in h for w in words):
                    return i
            return None

        dcol = col("date", "start")
        scol = col("asleep")
        if scol is None:
            scol = col("sleep")
        wcol = col("exercise", "workout")
        stcol = col("steps")
        if dcol is None or (scol is None and wcol is None):
            continue
        for r in rows[1:]:
            if len(r) <= dcol:
                continue
            diso = _parse_any_date(r[dcol])
            if not diso:
                continue
            rec = data.setdefault(diso, {})
            if scol is not None and scol < len(r):
                dm = _dur_minutes(r[scol])
                if dm is not None:
                    v = dm / 60
                else:
                    v = _num(r[scol])
                    if v is not None and ("min" in hdr[scol] or v > 24):
                        v /= 60
                if v and 0 < v <= 24:
                    rec["sleep_h"] = v
            if wcol is not None and wcol < len(r):
                dm = _dur_minutes(r[wcol])
                v = dm if dm is not None else _num(r[wcol])
                if (dm is None and v is not None
                        and ("hr" in hdr[wcol] or "hour" in hdr[wcol])):
                    v *= 60
                if v and 0 < v <= 1440:
                    rec["workout_min"] = v
            if stcol is not None and stcol < len(r):
                v = _num(r[stcol])
                if v and 0 < v <= 200000:
                    rec["steps"] = int(v)
    return data


def fmt_sleep(h):
    return f"{int(h)}h{round(h % 1 * 60):02}m"


def health_line(rec):
    parts = []
    if rec.get("sleep_h"):
        parts.append(f"sleep {fmt_sleep(rec['sleep_h'])}")
    if rec.get("workout_min"):
        parts.append(f"workout {round(rec['workout_min'])}m")
    if rec.get("steps"):
        parts.append(f"{rec['steps']} steps")
    return f"({', '.join(parts)})" if parts else ""


# ---------------- old-format line builders ----------------

def hms_unpadded(secs):
    return f"{secs // 3600}:{secs % 3600 // 60}:{secs % 60}"


def hms_padded(secs):
    return f"{secs // 3600}:{secs % 3600 // 60:02}:{secs % 60:02}"


def event_line(kind, when, cum_secs):
    # Start;2026-06-02;13:43:42;0;20;1229  (h ; total min ; total sec)
    return (f"{kind};{when:%Y-%m-%d};{when:%H:%M:%S};"
            f"{cum_secs // 3600};{cum_secs // 60};{cum_secs}")


# ---------------- idle detection (Windows) ----------------

class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def idle_seconds():
    try:
        lii = _LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        return (ctypes.windll.kernel32.GetTickCount() - lii.dwTime) / 1000.0
    except Exception:
        return 0.0


# ---------------- global hotkey ----------------

# label -> (modifier flags, virtual-key code); MOD_ALT=1 CTRL=2 SHIFT=4
HOTKEYS = {
    "Ctrl+Shift+Space": (0x0002 | 0x0004, 0x20),
    "Ctrl+Alt+Space": (0x0001 | 0x0002, 0x20),
    "Ctrl+Alt+P": (0x0001 | 0x0002, 0x50),
    "Pause": (0, 0x13),
    "F9": (0, 0x78),
}
DEFAULT_HOTKEY = "Ctrl+Shift+Space"


def hotkey_thread(q, mods, vk, tid_holder):
    """Registers a system-wide hotkey; puts 'toggle' on q when hit.
    Post WM_QUIT to tid_holder[0] to stop and unregister."""
    try:
        user32 = ctypes.windll.user32
        tid_holder[0] = ctypes.windll.kernel32.GetCurrentThreadId()
        ok = False
        for _ in range(10):        # brief retry while an old thread unregisters
            if user32.RegisterHotKey(None, 1, mods, vk):
                ok = True
                break
            time.sleep(0.1)
        if not ok:
            q.put("failed")
            return
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312:          # WM_HOTKEY
                q.put("toggle")
        user32.UnregisterHotKey(None, 1)
    except Exception:
        pass


# ---------------- autostart (Windows registry) ----------------

def app_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    py = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(py):
        py = sys.executable
    return f'"{py}" "{os.path.abspath(__file__)}"'


def get_autostart():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
            winreg.QueryValueEx(k, APP_NAME)
        return True
    except Exception:
        return False


def set_autostart(enable):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE) as k:
            if enable:
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, app_command())
            else:
                try:
                    winreg.DeleteValue(k, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        messagebox.showerror(APP_NAME, f"Couldn't change autostart:\n{e}")
        return False


# ---------------- calendar (.ics) export ----------------

def week_to_ics(monday):
    sunday = monday + dt.timedelta(days=6)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{APP_NAME}//EN"]
    n = 0
    for i, r in enumerate(read_rows()):
        if r[1] == "break":
            continue
        try:
            d = dt.date.fromisoformat(r[0])
            sh, sm = map(int, r[2].split(":"))
            eh, em = map(int, r[3].split(":"))
        except ValueError:
            continue
        if not (monday <= d <= sunday):
            continue
        start = dt.datetime(d.year, d.month, d.day, sh, sm)
        end = dt.datetime(d.year, d.month, d.day, eh, em)
        if end <= start:
            end += dt.timedelta(days=1)
        lines += ["BEGIN:VEVENT",
                  f"UID:timerdiary-{d.isoformat()}-{i}@local",
                  f"DTSTART:{start:%Y%m%dT%H%M%S}",
                  f"DTEND:{end:%Y%m%dT%H%M%S}",
                  f"SUMMARY:{r[5] or 'work'}",
                  f"DESCRIPTION:{r[6].replace(chr(10), ' ')}",
                  "END:VEVENT"]
        n += 1
    lines.append("END:VCALENDAR")
    path = os.path.join(data_dir(), f"TimerDiary_week_{monday.isoformat()}.ics")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path, n


# ---------------- app ----------------

NORMAL_GEO = "780x540"
COMPACT_GEO = "330x92"
MIN_LOG_SECS = 30          # intervals shorter than this skip the csv (not the txt)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry(NORMAL_GEO)
        self.minsize(330, 92)
        try:
            ttk.Style().theme_use("vista")
        except tk.TclError:
            pass

        self.settings = load_settings()
        self.state = "idle"            # idle | working | break
        self.cum_secs = 0              # session work seconds so far
        self.work_start = None
        self.break_start = None
        self.session_started = None
        self.idle_since = None         # datetime when idle gap began
        self.prompting = False
        self.compact = False
        self.active_task = ""          # task the current work interval logs to
        self.logged_task = None        # last task written as a "--- Task:" line
        self.pill = None               # floating break window
        self.today = self.effective_date()

        backup_if_due()
        self._build_menu()
        self._build_ui()
        self._bind_keys()
        self._load_diary(create=True)
        self._refresh_totals()
        self._first_run_autostart()
        self._recover_if_needed()
        self.hotq = queue.Queue()
        self.hot_tid = None
        self._start_hotkey()
        self._poll_hotkey()
        self._tick()
        self._autosave_loop()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def hotkey_name(self):
        hk = self.settings.get("hotkey", DEFAULT_HOTKEY)
        return hk if hk in HOTKEYS else DEFAULT_HOTKEY

    def _start_hotkey(self):
        if self.hot_tid and self.hot_tid[0]:
            # WM_QUIT ends the old thread's message loop -> it unregisters
            ctypes.windll.user32.PostThreadMessageW(self.hot_tid[0], 0x0012, 0, 0)
        self.hot_tid = [None]
        mods, vk = HOTKEYS[self.hotkey_name()]
        threading.Thread(target=hotkey_thread,
                         args=(self.hotq, mods, vk, self.hot_tid),
                         daemon=True).start()

    def _poll_hotkey(self):
        try:
            while True:
                msg = self.hotq.get_nowait()
                if msg == "failed":
                    self.status.config(text=f"Hotkey {self.hotkey_name()} is taken "
                                            "by another app — pick a different one in Tools.")
                else:
                    self._toggle(beep=True)
        except queue.Empty:
            pass
        self.after(150, self._poll_hotkey)

    def _set_hotkey(self):
        win = tk.Toplevel(self)
        win.title("Global hotkey")
        win.resizable(False, False)
        win.grab_set()
        ttk.Label(win, text="Start/stop from any app with:").grid(
            row=0, column=0, padx=8, pady=(8, 3))
        var = tk.StringVar(value=self.hotkey_name())
        box = ttk.Combobox(win, textvariable=var, state="readonly",
                           values=list(HOTKEYS))
        box.grid(row=1, column=0, padx=8, pady=3)

        def save():
            self.settings["hotkey"] = var.get()
            save_settings(self.settings)
            self._start_hotkey()
            self._set_status_hint()
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(
            row=2, column=0, sticky="e", padx=8, pady=8)

    # ----- signal meter -----

    @staticmethod
    def _kws_from_text(text):
        """Comma-separated keywords from the first 'SIGNAL:' line, lowered."""
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("signal:"):
                return [k.strip().lower() for k in s[7:].split(",") if k.strip()]
        return []

    def _signal_kws(self, day=None):
        if day is None or day == self.today:
            return self._kws_from_text(self.diary.get("1.0", "end-1c"))
        try:
            with open(self.diary_path(day), encoding="utf-8") as f:
                return self._kws_from_text(f.read())
        except OSError:
            return []

    @staticmethod
    def _is_signal(task, kws):
        t = (task or "").lower()
        return any(k in t for k in kws)

    def _day_signal(self, day, kws=None):
        """(signal_min, work_min) for one day given its keywords."""
        if kws is None:
            kws = self._signal_kws(day)
        sig = work = 0
        if kws:
            iso = day.isoformat()
            for r in read_rows():
                if r[0] != iso or r[1] == "break":
                    continue
                try:
                    m = int(r[4])
                except ValueError:
                    continue
                work += m
                if self._is_signal(r[5], kws):
                    sig += m
        return sig, work

    # ----- day / paths -----

    def rollover_hour(self):
        return int(self.settings.get("rollover_hour", 4))

    def effective_date(self, now=None):
        now = now or dt.datetime.now()
        return (now - dt.timedelta(hours=self.rollover_hour())).date()

    def diary_dir(self):
        d = self.settings.get("diary_dir") or os.path.join(data_dir(), "diary")
        os.makedirs(d, exist_ok=True)
        return d

    def diary_path(self, day=None):
        return os.path.join(self.diary_dir(),
                            (day or self.today).isoformat() + ".txt")

    # ----- menu -----

    def _build_menu(self):
        m = tk.Menu(self)
        filem = tk.Menu(m, tearoff=0)
        filem.add_command(label="Add past session…", command=self._add_past_session)
        filem.add_command(label="Open a day file…", command=self._open_day_file)
        filem.add_command(label="Export week to calendar (.ics)", command=self._export_ics)
        filem.add_separator()
        filem.add_command(label="Open data folder", command=self._open_folder)
        filem.add_command(label="Change diary folder…", command=self._change_diary_dir)
        filem.add_command(label="Health import folder…", command=self._set_health_dir)
        filem.add_separator()
        filem.add_command(label="Exit", command=self._on_close)
        m.add_cascade(label="File", menu=filem)

        viewm = tk.Menu(m, tearoff=0)
        viewm.add_command(label="Weekly summary", command=lambda: self._summary("week"))
        viewm.add_command(label="Monthly summary", command=lambda: self._summary("month"))
        viewm.add_command(label="Trend (8 weeks)", command=self._trend)
        viewm.add_command(label="Health × focus (14 days)", command=self._health_view)
        viewm.add_command(label="Search all days…", command=self._search_diary)
        viewm.add_separator()
        viewm.add_command(label="Copy week for AI review",
                          command=lambda: self._copy_review("week"))
        viewm.add_command(label="Copy today for AI review",
                          command=lambda: self._copy_review("day"))
        viewm.add_separator()
        viewm.add_command(label="Toggle compact mode", command=self._toggle_compact)
        m.add_cascade(label="View", menu=viewm)

        toolsm = tk.Menu(m, tearoff=0)
        self.autostart_var = tk.BooleanVar(value=get_autostart())
        toolsm.add_checkbutton(label="Launch at Windows startup",
                               variable=self.autostart_var,
                               command=lambda: set_autostart(self.autostart_var.get()))
        self.nudge_var = tk.BooleanVar(value=self.settings.get("nudge", True))
        toolsm.add_checkbutton(label="Nudge in title when not tracking",
                               variable=self.nudge_var, command=self._save_prefs)
        self.float_var = tk.BooleanVar(value=self.settings.get("float_break", True))
        toolsm.add_checkbutton(label="Floating break timer",
                               variable=self.float_var, command=self._save_prefs)
        toolsm.add_separator()
        toolsm.add_command(label="Global hotkey…", command=self._set_hotkey)
        toolsm.add_command(label="Deadline countdown…", command=self._set_deadline)
        toolsm.add_command(label="Idle detection…", command=self._set_idle)
        toolsm.add_command(label="Day rollover hour…", command=self._set_rollover)
        toolsm.add_command(label="Daily target…", command=self._set_target)
        m.add_cascade(label="Tools", menu=toolsm)
        self.menu = m
        self.config(menu=m)

    def _save_prefs(self):
        self.settings["nudge"] = self.nudge_var.get()
        self.settings["float_break"] = self.float_var.get()
        save_settings(self.settings)

    def _set_deadline(self):
        win = tk.Toplevel(self)
        win.title("Deadline countdown")
        win.resizable(False, False)
        win.grab_set()
        fields = {}
        defaults = [("Name (empty = off)", self.settings.get("dl_name", "")),
                    ("Date (YYYY-MM-DD)", self.settings.get("dl_date", "")),
                    ("Count tasks containing", self.settings.get("dl_match", "")),
                    ("Weekly target hours (0 = off)",
                     str(self.settings.get("dl_target_h", 0)))]
        for i, (lbl, dv) in enumerate(defaults):
            ttk.Label(win, text=lbl + ":").grid(row=i, column=0, sticky="e",
                                                padx=6, pady=3)
            e = ttk.Entry(win, width=24)
            e.insert(0, dv)
            e.grid(row=i, column=1, padx=6, pady=3)
            fields[lbl] = e

        def save():
            name = fields["Name (empty = off)"].get().strip()
            if name:
                try:
                    dt.date.fromisoformat(fields["Date (YYYY-MM-DD)"].get().strip())
                    float(fields["Weekly target hours (0 = off)"].get().strip() or 0)
                except ValueError:
                    messagebox.showerror(APP_NAME, "Check the date / target hours.",
                                         parent=win)
                    return
            self.settings["dl_name"] = name
            self.settings["dl_date"] = fields["Date (YYYY-MM-DD)"].get().strip()
            self.settings["dl_match"] = fields["Count tasks containing"].get().strip()
            self.settings["dl_target_h"] = float(
                fields["Weekly target hours (0 = off)"].get().strip() or 0)
            save_settings(self.settings)
            self._refresh_totals()
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(
            row=len(defaults), column=1, sticky="e", padx=6, pady=8)

    def _set_idle(self):
        cur = int(self.settings.get("idle_min", 10))
        v = simpledialog.askinteger(
            APP_NAME, "Offer to log a break after this many minutes\n"
                      "away from the keyboard (0 = off):",
            initialvalue=cur, minvalue=0, maxvalue=240, parent=self)
        if v is not None:
            self.settings["idle_min"] = v
            save_settings(self.settings)

    def _set_rollover(self):
        cur = self.rollover_hour()
        v = simpledialog.askinteger(
            APP_NAME, "New day starts at this hour (0-12).\n"
                      "4 means a 00:30 session still belongs to yesterday's file:",
            initialvalue=cur, minvalue=0, maxvalue=12, parent=self)
        if v is not None:
            self.settings["rollover_hour"] = v
            save_settings(self.settings)

    def _set_target(self):
        cur = self.settings.get("target_min", 0)
        v = simpledialog.askinteger(
            APP_NAME, "Daily target in minutes (0 = off):",
            initialvalue=cur, minvalue=0, maxvalue=1440, parent=self)
        if v is None:
            return
        self.settings["target_min"] = v
        save_settings(self.settings)
        self._refresh_totals()

    def _change_diary_dir(self):
        d = filedialog.askdirectory(parent=self, initialdir=self.diary_dir(),
                                    title="Folder for the daily .txt files")
        if not d:
            return
        self._save_diary()
        old_today = self.diary_path()
        self.settings["diary_dir"] = d
        save_settings(self.settings)
        # bring today's file along, or the morning's text stays behind
        if os.path.exists(old_today) and not os.path.exists(self.diary_path()):
            shutil.copy2(old_today, self.diary_path())
        self._load_diary(create=True)
        self.status.config(text=f"Diary folder: {d}")

    def _first_run_autostart(self):
        if self.settings.get("asked_autostart"):
            return
        # flag saved only after the dialog is answered — if the app dies
        # mid-dialog the question comes back next launch
        if not get_autostart() and messagebox.askyesno(
                APP_NAME, "Start TimerDiary automatically with Windows?\n"
                          "(You can change this later in Tools.)"):
            set_autostart(True)
            self.autostart_var.set(True)
        self.settings["asked_autostart"] = True
        save_settings(self.settings)

    # ----- UI -----

    def _build_ui(self):
        self.top = ttk.Frame(self)
        self.top.pack(fill="x", padx=8, pady=(6, 0))

        self.clock = ttk.Label(self.top, text="0:00:00", font=("Segoe UI", 22))
        self.clock.pack(side="left")

        self.compact_btn = ttk.Button(self.top, text="—", width=3,
                                      command=self._toggle_compact)
        self.compact_btn.pack(side="right")
        self.reset_btn = ttk.Button(self.top, text="Reset", width=7,
                                    command=self._reset, state="disabled")
        self.reset_btn.pack(side="right", padx=(0, 4))
        self.switch_btn = ttk.Button(self.top, text="Switch", width=7,
                                     command=self._switch, state="disabled")
        self.switch_btn.pack(side="right", padx=(0, 4))
        self.btn = ttk.Button(self.top, text="Start", width=8, command=self._toggle)
        self.btn.pack(side="right", padx=(0, 4))

        row = ttk.Frame(self.top)
        row.pack(side="left", fill="x", expand=True, padx=(12, 8))
        ttk.Label(row, text="Task:").pack(side="left")
        self.task_var = tk.StringVar()
        self.task_box = ttk.Combobox(row, textvariable=self.task_var,
                                     values=self._task_values())
        self.task_box.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        self.target_bar = ttk.Progressbar(self.body, maximum=100)
        # packed on demand in _refresh_totals when a target is set

        self.timeline = tk.Canvas(self.body, height=28, highlightthickness=0)
        self.timeline.pack(fill="x", padx=8, pady=(6, 0))
        self.timeline.bind("<Configure>", lambda e: self._draw_timeline())

        info = ttk.Frame(self.body)
        info.pack(fill="x", padx=8, pady=(4, 0))
        self.info_row = info
        self.dl_dot = tk.Label(info, text="●", font=("Segoe UI", 10), fg="#bbbbbb")
        # packed on demand in _refresh_totals when a deadline is set
        self.diary_lbl = ttk.Label(info, text="")
        self.diary_lbl.pack(side="left")
        self.diary = tk.Text(self.body, wrap="word", font=("Consolas", 10),
                             undo=True, relief="sunken", borderwidth=1)
        self.diary.pack(fill="both", expand=True, padx=8, pady=(2, 4))

        self.status = ttk.Label(self, text="", anchor="w")
        self.status.pack(fill="x", side="bottom", padx=8, pady=(0, 4))
        self._set_status_hint()

    def _set_status_hint(self):
        self.status.config(text=f"{self.hotkey_name()} start/stop (works everywhere) · "
                                "Enter in task box = switch · Ctrl+R reset · F5 timestamp")

    def _task_values(self):
        out = list(self.settings.get("recent_tasks", []))
        lower = {x.lower() for x in out}
        for t in recent_tasks():
            if t.lower() not in lower:
                out.append(t)
        return out[:15]

    def _remember_task(self, t):
        """Put a task at the top of the dropdown the moment it is started."""
        lst = [x for x in self.settings.get("recent_tasks", [])
               if x.lower() != t.lower()]
        self.settings["recent_tasks"] = ([t] + lst)[:15]
        save_settings(self.settings)
        self.task_box.config(values=self._task_values())

    def _bind_keys(self):
        self.bind("<Control-space>", lambda e: self._toggle())
        self.bind("<Control-Return>", self._go)
        self.bind("<Control-r>", lambda e: self._reset())
        self.diary.bind("<F5>", self._insert_timestamp)
        self.task_box.bind("<Return>", self._go)
        self.task_box.bind("<<ComboboxSelected>>", self._switch)

    def _insert_timestamp(self, event=None):
        self.diary.insert("insert", f"{dt.datetime.now():%H:%M} ")
        return "break"

    # ----- compact mode -----

    def _toggle_compact(self):
        self.compact = not self.compact
        if self.compact:
            self.body.pack_forget()
            self.status.pack_forget()
            self.config(menu="")
            self.attributes("-topmost", True)
            self.geometry(COMPACT_GEO)
            self.compact_btn.config(text="□")
        else:
            self.attributes("-topmost", False)
            self.config(menu=self.menu)
            self.geometry(NORMAL_GEO)
            self.body.pack(fill="both", expand=True)
            self.status.pack(fill="x", side="bottom", padx=8, pady=(0, 4))
            self.compact_btn.config(text="—")
            self._refresh_totals()

    # ----- text log helpers -----

    def _append_text(self, text, cursor_to_line_end=False):
        """Append at end of the day file text; optionally park the cursor at
        the end of the first appended line (so you can type a break note)."""
        cur = self.diary.get("1.0", "end-1c")
        if cur and not cur.endswith("\n"):
            self.diary.insert("end", "\n")
        index_before = self.diary.index("end-1c")
        self.diary.insert("end", text + "\n")
        if cursor_to_line_end:
            line = index_before.split(".")[0]
            self.diary.mark_set("insert", f"{line}.end")
            self.diary.see("insert")
            self.diary.focus_set()
        else:
            self.diary.see("end")
        self._save_diary()

    def _csv_interval(self, kind, start, end, note=""):
        secs = int((end - start).total_seconds())
        if secs < MIN_LOG_SECS:
            return
        # active_task = task at interval START, so editing the box mid-interval
        # (before pressing Switch) can't relabel time already worked
        append_row([self.effective_date(start).isoformat(), kind,
                    start.strftime("%H:%M"), end.strftime("%H:%M"),
                    max(1, round(secs / 60)),
                    self.active_task, note])

    # ----- timer state machine -----

    def _toggle(self, beep=False):
        self._roll_day_if_needed()
        now = dt.datetime.now()
        self.idle_since = None
        if self.state == "idle":
            self.session_started = now
            self.cum_secs = 0
            self._append_text(f"\n--- Session start at: {now:%Y-%m-%d %H:%M:%S}\n"
                              + event_line("Start", now, 0))
            self._log_task_if_new()
            self.state = "working"
            self.work_start = now
            self.reset_btn.config(state="normal")
            self.switch_btn.config(state="normal")
            self.btn.config(text="Stop")
        elif self.state == "working":
            self._log_work_until(now)
            self.state = "break"
            self.break_start = now
            self.switch_btn.config(state="disabled")
            self.btn.config(text="Start")
        else:  # break -> back to work
            bsecs = int((now - self.break_start).total_seconds())
            self._append_text(f"--- Break duration: {hms_unpadded(bsecs)} ",
                              cursor_to_line_end=True)
            self._append_text(event_line("Start", now, self.cum_secs))
            self._csv_interval("break", self.break_start, now)
            self._log_task_if_new()
            self.state = "working"
            self.work_start = now
            self.switch_btn.config(state="normal")
            self.btn.config(text="Stop")
        self._save_state()
        self._refresh_totals()
        if self.state == "working":
            self._hide_pill()      # snappier than waiting for the next tick
            self.status.config(text=f"Working — {self.active_task or '(no task)'}")
        elif self.settings.get("float_break", True):
            self.status.config(text="On break — the floating clock counts it; "
                                    "click it to get back to work.")
        else:
            self.status.config(text="On break.")
        if beep:
            try:
                import winsound
                winsound.Beep(880 if self.state == "working" else 440, 150)
            except Exception:
                pass

    def _log_task_if_new(self):
        """Remember the task for csv rows and write it into the day file."""
        t = self.task_var.get().strip()
        self.active_task = t
        if t:
            self._remember_task(t)
        if t and t != self.logged_task:
            self._append_text(f"--- Task: {t}")
            self.logged_task = t

    def _go(self, event=None):
        """Enter in the task box: split if working, otherwise just start."""
        if self.state == "working":
            self._switch()
        else:
            self._toggle()

    def _switch(self, event=None):
        """Split the log here: close the work interval under the old task,
        continue immediately under whatever is in the task box now."""
        if self.state != "working":
            return
        now = dt.datetime.now()
        if self.task_var.get().strip() == self.active_task:
            self.status.config(text="Switch splits the log when the task changes — type the new task first.")
            return
        self._log_work_until(now)
        self._append_text(event_line("Start", now, self.cum_secs))
        self._log_task_if_new()
        self.work_start = now
        self._save_state()
        self._refresh_totals()
        self.status.config(text=f"Switched to {self.active_task or '(no task)'}")
        self.diary.focus_set()

    def _log_work_until(self, end):
        """Close the current work interval at `end` (Stop line + csv)."""
        secs = int((end - self.work_start).total_seconds())
        self.cum_secs += secs
        self._append_text(event_line("Stop", end, self.cum_secs))
        self._csv_interval("work", self.work_start, end)

    def _reset(self):
        if self.state == "idle":
            return
        if not messagebox.askyesno(
                APP_NAME, f"End session? ({hms_padded(self._session_secs())} tracked)"):
            return
        now = dt.datetime.now()
        if self.state == "working":
            self._log_work_until(now)
        elif self.state == "break":
            bsecs = int((now - self.break_start).total_seconds())
            self._append_text(f"--- Break duration: {hms_unpadded(bsecs)} ")
            self._csv_interval("break", self.break_start, now)
        self._append_text(f"--- Session reset, studying duration: {hms_padded(self.cum_secs)}\n"
                          + event_line("Reset", now, self.cum_secs) + "\n")
        self.state = "idle"
        self.cum_secs = 0
        self.work_start = self.break_start = self.session_started = None
        self.active_task, self.logged_task = "", None
        self.btn.config(text="Start")
        self.reset_btn.config(state="disabled")
        self.switch_btn.config(state="disabled")
        self._save_state()
        self._refresh_totals()

    def _session_secs(self):
        s = self.cum_secs
        if self.state == "working" and self.work_start:
            s += int((dt.datetime.now() - self.work_start).total_seconds())
        return s

    # ----- clock + idle watch -----

    def _tick(self):
        if self.state == "working":
            secs = self._session_secs()
            self.clock.config(text=hms_padded(secs))
            self.title(f"{secs // 3600}:{secs % 3600 // 60:02} — "
                       f"{self.task_var.get().strip() or APP_NAME}")
            self._watch_idle()
        elif self.state == "break":
            bsecs = int((dt.datetime.now() - self.break_start).total_seconds())
            self.clock.config(text=f"☕ {hms_padded(bsecs)}")
            self.title(f"☕ break {bsecs // 60}:{bsecs % 60:02} — {APP_NAME}")
            self._update_pill(bsecs)
        else:
            self.clock.config(text="0:00:00")
            self.title(("⏸ not tracking — " + APP_NAME)
                       if self.nudge_var.get() else APP_NAME)
        if self.state != "break":
            self._hide_pill()
        self._tl_tick = getattr(self, "_tl_tick", 0) + 1
        if self._tl_tick % 60 == 0 and not self.compact:
            self._draw_timeline()      # keep the live segment growing
        self.after(1000, self._tick)

    # ----- floating break pill -----

    BREAK_WARN_SECS = 15 * 60      # pill turns red after this

    def _update_pill(self, bsecs):
        if not self.settings.get("float_break", True) or self.compact:
            self._hide_pill()
            return
        if self.pill is None:
            p = tk.Toplevel(self)
            p.overrideredirect(True)
            p.attributes("-topmost", True)
            self.pill_lbl = tk.Label(p, text="", font=("Segoe UI", 13, "bold"),
                                     fg="white", bg="#505050", padx=14, pady=7,
                                     cursor="hand2")
            self.pill_lbl.pack()
            self._pill_drag = None

            def press(e):
                self._pill_drag = (e.x_root, e.y_root,
                                   p.winfo_x(), p.winfo_y(), False)

            def motion(e):
                if not self._pill_drag:
                    return
                x0, y0, px, py, _ = self._pill_drag
                dx, dy = e.x_root - x0, e.y_root - y0
                if abs(dx) + abs(dy) > 4:
                    self._pill_drag = (x0, y0, px, py, True)
                    p.geometry(f"+{px + dx}+{py + dy}")

            def release(e):
                if self._pill_drag and self._pill_drag[4]:
                    # dragged: remember the spot for every future break
                    self.settings["pill_pos"] = [p.winfo_x(), p.winfo_y()]
                    save_settings(self.settings)
                elif self._pill_drag:
                    self._toggle()      # plain click = back to work
                self._pill_drag = None

            for seq, fn in (("<ButtonPress-1>", press), ("<B1-Motion>", motion),
                            ("<ButtonRelease-1>", release)):
                self.pill_lbl.bind(seq, fn)
            p.update_idletasks()
            pos = self.settings.get("pill_pos")
            if pos and self._pos_on_screen(pos):
                p.geometry(f"+{int(pos[0])}+{int(pos[1])}")
            else:
                x = self.winfo_screenwidth() - p.winfo_reqwidth() - 24
                y = self.winfo_screenheight() - p.winfo_reqheight() - 90
                p.geometry(f"+{x}+{y}")
            self.pill = p
        self.pill_lbl.config(
            text=f"☕ break {bsecs // 60}:{bsecs % 60:02} — click to work",
            bg="#a03030" if bsecs > self.BREAK_WARN_SECS else "#505050")

    @staticmethod
    def _pos_on_screen(pos):
        """Is a saved pill position still inside the virtual desktop?
        (Covers all monitors — a spot on a detached monitor is rejected.)"""
        try:
            gm = ctypes.windll.user32.GetSystemMetrics
            vx, vy, vw, vh = gm(76), gm(77), gm(78), gm(79)
            return (vx - 50 <= pos[0] <= vx + vw - 40
                    and vy - 20 <= pos[1] <= vy + vh - 30)
        except Exception:
            return True

    def _hide_pill(self):
        if self.pill is not None:
            self.pill.destroy()
            self.pill = None

    def _watch_idle(self):
        thr = int(self.settings.get("idle_min", 10))
        if not thr or self.prompting:
            return
        idle = idle_seconds()
        if idle > thr * 60:
            self.idle_since = dt.datetime.now() - dt.timedelta(seconds=idle)
        elif self.idle_since and idle < 15:
            gone_since, self.idle_since = self.idle_since, None
            self._offer_idle_break(gone_since)

    def _offer_idle_break(self, gone_since):
        self.prompting = True
        try:
            mins = round((dt.datetime.now() - gone_since).total_seconds() / 60)
            if not messagebox.askyesno(
                    APP_NAME, f"You were away ~{mins} min while the timer ran.\n\n"
                              f"Log it as a break (work stops at "
                              f"{gone_since:%H:%M})?"):
                return
            # the global hotkey still works while this dialog is open — if the
            # state changed under us, the retro-split no longer applies
            if self.state != "working" or not self.work_start:
                return
            gone_since = max(gone_since, self.work_start)
            now = dt.datetime.now()
            self._log_work_until(gone_since)
            bsecs = int((now - gone_since).total_seconds())
            self._append_text(f"--- Break duration: {hms_unpadded(bsecs)} (away) ",
                              cursor_to_line_end=True)
            self._append_text(event_line("Start", now, self.cum_secs))
            self._csv_interval("break", gone_since, now, "away")
            self.work_start = now
            self._save_state()
            self._refresh_totals()
        finally:
            self.prompting = False

    # ----- crash recovery / state persistence -----

    def _save_state(self):
        if self.state == "idle":
            try:
                os.remove(RUNNING_JSON)
            except FileNotFoundError:
                pass
            return
        with open(RUNNING_JSON, "w", encoding="utf-8") as f:
            json.dump({"state": self.state,
                       "cum_secs": self.cum_secs,
                       "work_start": self.work_start.isoformat() if self.work_start else None,
                       "break_start": self.break_start.isoformat() if self.break_start else None,
                       "session_started": self.session_started.isoformat(),
                       "task": self.task_var.get()}, f)

    def _recover_if_needed(self):
        try:
            with open(RUNNING_JSON, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            return
        try:
            state = d["state"]
            started = dt.datetime.fromisoformat(d["session_started"])
        except (KeyError, ValueError):
            os.remove(RUNNING_JSON)
            return
        mins = round((dt.datetime.now() - started).total_seconds() / 60)
        ans = messagebox.askyesnocancel(
            APP_NAME,
            f"A session was still open when the app last closed\n"
            f"({d.get('task') or 'no task'} — started {started:%d.%m %H:%M}, "
            f"~{mins} min ago).\n\n"
            f"Yes = keep it running\nNo = log it (until now)\nCancel = discard")
        if ans is None:
            os.remove(RUNNING_JSON)
            return
        self.state = state
        self.cum_secs = int(d.get("cum_secs", 0))
        self.session_started = started
        self.task_var.set(d.get("task", ""))
        self.active_task = d.get("task", "").strip()
        self.logged_task = self.active_task or None
        self.work_start = (dt.datetime.fromisoformat(d["work_start"])
                           if d.get("work_start") else None)
        self.break_start = (dt.datetime.fromisoformat(d["break_start"])
                            if d.get("break_start") else None)
        self.reset_btn.config(state="normal")
        if ans is True:
            self.btn.config(text="Stop" if state == "working" else "Start")
            self.switch_btn.config(state="normal" if state == "working" else "disabled")
            self._save_state()
        else:
            now = dt.datetime.now()
            if state == "working":
                self._log_work_until(now)
            self._append_text("--- Session reset, studying duration: "
                              f"{hms_padded(self.cum_secs)}\n"
                              + event_line("Reset", now, self.cum_secs) + "\n")
            self.state = "idle"
            self.cum_secs = 0
            self.work_start = self.break_start = self.session_started = None
            self.active_task, self.logged_task = "", None
            self.reset_btn.config(state="disabled")
            self.switch_btn.config(state="disabled")
            self._save_state()
        self._refresh_totals()

    # ----- totals / target bar -----

    def _refresh_totals(self):
        today_iso = self.today.isoformat()
        w, b = day_totals(today_iso)
        monday = self.today - dt.timedelta(days=self.today.weekday())
        week = 0
        for r in read_rows():
            if r[1] == "break":
                continue
            try:
                d = dt.date.fromisoformat(r[0])
                if monday <= d <= self.today:
                    week += int(r[4])
            except ValueError:
                continue
        text = (f"{self.today.isoformat()} — today {w / 60:.2f} h work"
                + (f" / {b / 60:.2f} h breaks" if b else "")
                + f"   |   week {week / 60:.2f} h")
        # signal %: today by today's SIGNAL line, week per each day's own line
        kws_today = self._signal_kws()
        if kws_today and w:
            sig_today, _ = self._day_signal(self.today, kws_today)
            wk_sig = wk_work = 0
            d = monday
            while d <= self.today:
                s, tot = self._day_signal(d, kws_today if d == self.today else None)
                wk_sig += s
                wk_work += tot
                d += dt.timedelta(days=1)
            text += f"   |   signal {round(100 * sig_today / w)}%"
            if wk_work and wk_work != w:
                text += f" (wk {round(100 * wk_sig / wk_work)}%)"
        dl_name = self.settings.get("dl_name")
        if dl_name:
            try:
                left = (dt.date.fromisoformat(self.settings["dl_date"])
                        - dt.date.today()).days
                match = self.settings.get("dl_match", "").lower()
                wk_m = 0
                for r in read_rows():
                    if r[1] == "break":
                        continue
                    try:
                        d = dt.date.fromisoformat(r[0])
                    except ValueError:
                        continue
                    if (monday <= d <= self.today
                            and (not match or match in r[5].lower())):
                        wk_m += int(r[4])
                seg = f"   |   {dl_name}: {left}d left"
                target = self.settings.get("dl_target_h", 0)
                if target:
                    seg += f" · {wk_m / 60:.2f}/{target:g}h wk"
                text += seg
            except (ValueError, KeyError):
                pass
        # activity dot: green = working on the deadline task right now
        if dl_name:
            match = self.settings.get("dl_match", "").lower()
            on_it = not match or match in (self.active_task or "").lower()
            if self.state == "working" and on_it:
                c = "#2e8b2e"
            elif self.state == "break" and on_it:
                c = "#d9a24a"
            else:
                c = "#bbbbbb"
            self.dl_dot.config(fg=c)
            if not self.dl_dot.winfo_ismapped():
                self.dl_dot.pack(side="left", padx=(0, 5),
                                 before=self.diary_lbl)
        elif self.dl_dot.winfo_ismapped():
            self.dl_dot.pack_forget()
        self._draw_timeline()
        target = self.settings.get("target_min", 0)
        if target:
            text += f"   |   target {min(100, round(100 * w / target))}%"
            self.target_bar.config(maximum=target, value=min(w, target))
            if not self.target_bar.winfo_ismapped() and not self.compact:
                self.target_bar.pack(fill="x", padx=8, pady=(4, 0),
                                     before=self.timeline)
        elif self.target_bar.winfo_ismapped():
            self.target_bar.pack_forget()
        self.diary_lbl.config(text=text)

    # ----- day timeline (00-24 bar) -----

    TL_WORK, TL_BREAK, TL_SIGNAL = "#4a6fa5", "#e0a44c", "#3a8a3a"
    TL_SLEEP = "#454569"

    def _sleep_band(self):
        """ESTIMATED sleep band for today's 00-24 bar, as clock-minute
        (start, end), or None. We only have last night's sleep TOTAL from
        the health import, so: bed ~= last logged event yesterday + 1 h
        (default 00:00 if the evening wasn't logged late), band length =
        the imported total, clipped so it ends before today's first
        logged activity. Clearly an estimate — labeled as such on the bar."""
        rec = self._health_data().get(self.today.isoformat())
        if not rec or not rec.get("sleep_h"):
            return None
        sleep_min = int(rec["sleep_h"] * 60)
        yday_iso = (self.today - dt.timedelta(days=1)).isoformat()
        today_iso = self.today.isoformat()
        last = first = None      # minutes since yesterday 00:00 / today 00:00
        for r in read_rows():
            try:
                if r[0] == yday_iso:
                    h, m = map(int, r[3].split(":"))
                    t = h * 60 + m + (1440 if h < 12 else 0)
                    last = max(last or 0, t)
                elif r[0] == today_iso:
                    h, m = map(int, r[2].split(":"))
                    if h >= self.rollover_hour():   # skip past-midnight tail
                        first = min(first if first is not None else 9999,
                                    h * 60 + m)
            except ValueError:
                continue
        bed = last + 60 if last and last >= 21 * 60 else 1440   # default 00:00
        wake = bed + sleep_min
        if first is not None and wake > 1440 + first:
            wake = 1440 + first
            bed = wake - sleep_min
        if wake <= 1440:         # entire band before midnight — nothing to draw
            return None
        return max(0, bed - 1440), wake - 1440

    def _draw_timeline(self):
        cv = self.timeline
        cv.delete("all")
        W = cv.winfo_width()
        if W < 50:
            W = cv.winfo_reqwidth() or 600
        H = 14

        def seg(x0, x1, color):
            if x1 < x0:          # crossed midnight -> wrap around the bar
                seg(x0, W, color)
                x0 = 0
            cv.create_rectangle(x0, 1, max(x1, x0 + 1.5), H, fill=color,
                                outline="")

        cv.create_rectangle(0, 1, W, H, fill="#ececec", outline="#cccccc")
        band = self._sleep_band()
        if band:
            x0, x1 = W * band[0] / 1440, W * band[1] / 1440
            cv.create_rectangle(x0, 1, x1, H, fill=self.TL_SLEEP, outline="")
            if x1 - x0 > 55:
                cv.create_text((x0 + x1) / 2, (H + 1) / 2, text="zzz (est.)",
                               fill="#c8c8dc", font=("Segoe UI", 7))
        kws = self._signal_kws()

        def work_color(task):
            return self.TL_SIGNAL if kws and self._is_signal(task, kws) \
                else self.TL_WORK

        today_iso = self.today.isoformat()
        for r in read_rows():
            if r[0] != today_iso:
                continue
            try:
                sh, sm = map(int, r[2].split(":"))
                eh, em = map(int, r[3].split(":"))
            except ValueError:
                continue
            seg(W * (sh * 60 + sm) / 1440, W * (eh * 60 + em) / 1440,
                self.TL_BREAK if r[1] == "break" else work_color(r[5]))
        # the interval currently running
        now = dt.datetime.now()
        live = (("working", self.work_start), ("break", self.break_start))
        for st, t0 in live:
            if self.state == st and t0:
                seg(W * (t0.hour * 60 + t0.minute) / 1440,
                    W * (now.hour * 60 + now.minute) / 1440,
                    work_color(self.active_task) if st == "working"
                    else self.TL_BREAK)
        for hr in range(0, 25, 3):
            x = W * hr / 24
            cv.create_line(x, H, x, H + 3, fill="#999999")
            anchor = "nw" if hr == 0 else ("ne" if hr == 24 else "n")
            cv.create_text(min(max(x, 1), W - 1), H + 4, text=f"{hr:02}",
                           font=("Segoe UI", 7), fill="#888888", anchor=anchor)

    # ----- diary file -----

    def _load_diary(self, create=False):
        p = self.diary_path()
        self.diary.delete("1.0", "end")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                self.diary.insert("1.0", f.read())
        elif create:
            header = f"=== {self.today:%A %d.%m.%Y} ==="
            yw, yb = day_totals((self.today - dt.timedelta(days=1)).isoformat())
            if yw or yb:
                header += (f"\n(yesterday: {yw // 60}h{yw % 60:02}m work"
                           f" / {yb // 60}h{yb % 60:02}m breaks)")
            header += f"\nSIGNAL: {self._carry_signal()}"
            self.diary.insert("1.0", header + "\n\n")
            self._save_diary()
        self.diary.mark_set("insert", "end")
        self.diary.edit_modified(False)
        self._maybe_insert_health()

    def _carry_signal(self):
        """Yesterday's SIGNAL line text (original case), or ''."""
        try:
            with open(self.diary_path(self.today - dt.timedelta(days=1)),
                      encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.lower().startswith("signal:"):
                        return s[7:].strip()
        except OSError:
            pass
        return ""

    # ----- health import -----

    def _health_data(self):
        hdir = self.settings.get("health_dir")
        if not hdir or not os.path.isdir(hdir):
            return {}
        try:
            key = tuple(sorted(
                (fn, os.path.getmtime(os.path.join(hdir, fn)))
                for fn in os.listdir(hdir) if fn.lower().endswith(".csv")))
        except OSError:
            return {}
        cache = getattr(self, "_health_cache", None)
        if cache and cache[0] == (hdir, key):
            return cache[1]
        data = parse_health_dir(hdir)
        self._health_cache = ((hdir, key), data)
        return data

    def _maybe_insert_health(self):
        """Add '(sleep 6h12m, ...)' under today's header once data appears.
        Sleep syncs from the watch after wake-up, so this may run hours
        after the day file was created."""
        rec = self._health_data().get(self.today.isoformat())
        line = health_line(rec) if rec else ""
        if not line:
            return
        text = self.diary.get("1.0", "end-1c")
        if "(sleep " in text or "(workout " in text:
            return
        at = self.diary.search("SIGNAL:", "1.0", stopindex="20.0")
        at = f"{at.split('.')[0]}.end" if at else "1.end"
        self.diary.insert(at, "\n" + line)
        self._save_diary()

    def _set_health_dir(self):
        d = filedialog.askdirectory(
            parent=self, title="Folder where your health app drops csv files")
        if not d:
            return
        self.settings["health_dir"] = d
        save_settings(self.settings)
        self._health_cache = None
        n = len(parse_health_dir(d))
        self._maybe_insert_health()
        self.status.config(text=f"Health folder set — found data for {n} day(s).")

    def _save_diary(self):
        text = self.diary.get("1.0", "end-1c")
        p = self.diary_path()
        if text.strip() or os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
        self.diary.edit_modified(False)

    def _autosave_loop(self):
        self._roll_day_if_needed()
        if self.diary.edit_modified():
            self._save_diary()
        if self.state != "idle":
            self._save_state()
        # sleep data lands on the phone after wake-up: re-check ~every 30 min
        self._hb = getattr(self, "_hb", 0) + 1
        if self._hb % 180 == 0:
            self._maybe_insert_health()
        self.after(10000, self._autosave_loop)

    def _roll_day_if_needed(self):
        now = self.effective_date()
        if now == self.today:
            return
        self._save_diary()
        self.today = now
        self._load_diary(create=True)
        if self.state != "idle" and self.session_started:
            self._append_text(f"--- (session continues, started "
                              f"{self.session_started:%d.%m %H:%M})")
        self._refresh_totals()

    # ----- add past session -----

    def _add_past_session(self):
        win = tk.Toplevel(self)
        win.title("Add past session")
        win.resizable(False, False)
        win.grab_set()
        fields = {}
        defaults = [("Date (YYYY-MM-DD)", self.today.isoformat()),
                    ("Start (HH:MM)", f"{dt.datetime.now():%H:%M}"),
                    ("Minutes", "30"),
                    ("Task", self.task_var.get()),
                    ("Note", "")]
        for i, (lbl, dv) in enumerate(defaults):
            ttk.Label(win, text=lbl + ":").grid(row=i, column=0, sticky="e",
                                                padx=6, pady=3)
            e = ttk.Entry(win, width=28)
            e.insert(0, dv)
            e.grid(row=i, column=1, padx=6, pady=3)
            fields[lbl] = e

        def save():
            try:
                d = dt.date.fromisoformat(fields["Date (YYYY-MM-DD)"].get().strip())
                sh, sm = map(int, fields["Start (HH:MM)"].get().strip().split(":"))
                mins = int(fields["Minutes"].get().strip())
                assert mins >= 1
            except (ValueError, AssertionError):
                messagebox.showerror(APP_NAME, "Check date / start time / minutes.",
                                     parent=win)
                return
            start = dt.datetime(d.year, d.month, d.day, sh, sm)
            end = start + dt.timedelta(minutes=mins)
            task = fields["Task"].get().strip()
            note = fields["Note"].get().strip()
            append_row([d.isoformat(), "work", start.strftime("%H:%M"),
                        end.strftime("%H:%M"), mins, task, note])
            if d == self.today:
                self._append_text(f"{start:%H:%M}-{end:%H:%M}  {task or '(no task)'} "
                                  f"({mins}m, added afterwards)"
                                  + (f" - {note}" if note else ""))
            if task:
                self._remember_task(task)
            self._refresh_totals()
            win.destroy()
            self.status.config(text=f"Added {mins} min — {task or '(no task)'}")

        ttk.Button(win, text="Save", command=save).grid(
            row=len(defaults), column=1, sticky="e", padx=6, pady=8)

    # ----- copy for AI review -----

    def _copy_review(self, mode):
        self._save_diary()
        if mode == "week":
            first = self.today - dt.timedelta(days=self.today.weekday())
            last = first + dt.timedelta(days=6)
        else:
            first = last = self.today

        work = brk = 0
        tasks = {}
        for r in read_rows():
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[4])
            except ValueError:
                continue
            if not (first <= d <= last):
                continue
            if r[1] == "break":
                brk += m
            else:
                work += m
                key = r[5] or "(no task)"
                tasks[key] = tasks.get(key, 0) + m

        parts = [f"TimerDiary export {first} … {last}",
                 f"Total: {work / 60:.2f} h work, {brk / 60:.2f} h breaks"]
        sig_m = work_m = 0
        d = first
        while d <= last:
            s, tot = self._day_signal(d)
            sig_m += s
            work_m += tot
            d += dt.timedelta(days=1)
        if work_m:
            parts.append(f"Signal: {sig_m / 60:.2f} h "
                         f"({round(100 * sig_m / work_m)}% of tracked work; "
                         "per each day's own SIGNAL line)")
        parts.append("")
        if tasks:
            parts.append("Hours per task:")
            for t, m in sorted(tasks.items(), key=lambda x: -x[1]):
                parts.append(f"  {m / 60:6.2f} h  {t}")
            parts.append("")
        d, n_days = first, 0
        while d <= last:
            p = self.diary_path(d)
            if os.path.exists(p):
                dw, db = day_totals(d.isoformat())
                parts.append(f"===== {d:%a %Y-%m-%d} — "
                             f"{dw / 60:.2f}h work / {db / 60:.2f}h breaks =====")
                with open(p, encoding="utf-8") as f:
                    parts.append(f.read().rstrip())
                parts.append("")
                n_days += 1
            d += dt.timedelta(days=1)
        self.clipboard_clear()
        self.clipboard_append("\n".join(parts))
        self.status.config(text=f"Copied {n_days} day(s), {work / 60:.2f} h — "
                                "paste into Claude and ask what slipped.")

    # ----- health x focus view -----

    def _health_view(self):
        hd = self._health_data()
        win = tk.Toplevel(self)
        win.title("Health × focus — last 14 days")
        win.geometry("560x430")
        txt = tk.Text(win, wrap="none", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=8)

        lines = [" day        sleep  workout   steps   work   signal",
                 " " + "-" * 50]
        good, short = [], []      # (work_min, sig_pct) split at 7 h sleep
        for i in range(13, -1, -1):
            d = self.today - dt.timedelta(days=i)
            rec = hd.get(d.isoformat(), {})
            w, _b = day_totals(d.isoformat())
            sig, tot = self._day_signal(d)
            sl = rec.get("sleep_h")
            pct = round(100 * sig / tot) if tot else None
            lines.append(
                f" {d:%a %d.%m}  "
                + (f"{fmt_sleep(sl):>6}" if sl else "     -")
                + (f"  {round(rec['workout_min']):>4}m" if rec.get("workout_min") else "     -")
                + (f"  {rec['steps']:>6}" if rec.get("steps") else "       -")
                + (f"  {w / 60:>5.2f}h" if w else "      -")
                + (f"  {pct:>4}%" if pct is not None else "      -"))
            if sl and w:
                (good if sl >= 7 else short).append((w, pct))
        if len(good) >= 2 and len(short) >= 2:
            def avg(xs, i):
                vals = [x[i] for x in xs if x[i] is not None]
                return sum(vals) / len(vals) if vals else None
            lines += ["",
                      f" sleep ≥7h ({len(good)} days): avg work "
                      f"{avg(good, 0) / 60:.2f} h"
                      + (f", signal {round(avg(good, 1))}%" if avg(good, 1) is not None else ""),
                      f" sleep <7h ({len(short)} days): avg work "
                      f"{avg(short, 0) / 60:.2f} h"
                      + (f", signal {round(avg(short, 1))}%" if avg(short, 1) is not None else "")]
        if not hd:
            lines += ["", " No health data yet — set the folder via",
                      " File > Health import folder…"]
        txt.insert("1.0", "\n".join(lines))
        txt.config(state="disabled")

    # ----- open old day / search -----

    def _open_day_file(self):
        p = filedialog.askopenfilename(parent=self, initialdir=self.diary_dir(),
                                       filetypes=[("Day files", "*.txt")])
        if p:
            os.startfile(p)

    def _search_diary(self):
        win = tk.Toplevel(self)
        win.title("Search all days")
        win.geometry("620x440")
        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=8)
        q = ttk.Entry(bar)
        q.pack(side="left", fill="x", expand=True)
        q.focus_set()
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        def go(event=None):
            txt.config(state="normal")
            txt.delete("1.0", "end")
            query = q.get().strip().lower()
            if not query:
                return
            hits = 0
            for fn in sorted(os.listdir(self.diary_dir()), reverse=True):
                if not fn.endswith(".txt"):
                    continue
                try:
                    with open(os.path.join(self.diary_dir(), fn),
                              encoding="utf-8") as f:
                        for line in f:
                            if query in line.lower():
                                txt.insert("end", f"{fn[:-4]}  {line.rstrip()}\n")
                                hits += 1
                except OSError:
                    continue
            if not hits:
                txt.insert("1.0", "No matches.")
            txt.config(state="disabled")

        ttk.Button(bar, text="Search", command=go).pack(side="left", padx=(6, 0))
        q.bind("<Return>", go)

    # ----- summaries + trend -----

    def _summary(self, mode):
        # effective date, so a 01:30 session still counts into "this week"
        today = self.today
        if mode == "week":
            first = today - dt.timedelta(days=today.weekday())
            last = first + dt.timedelta(days=6)
            title = f"Week {first.isocalendar().week} — {first} … {last}"
        else:
            first = today.replace(day=1)
            nxt = (first.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
            last = nxt - dt.timedelta(days=1)
            title = f"{first:%B %Y}"

        days, breaks, tasks, sig = {}, {}, {}, {}
        kws_by_day = {}
        d = first
        while d <= last:
            days[d] = breaks[d] = sig[d] = 0
            kws_by_day[d] = self._signal_kws(d)
            d += dt.timedelta(days=1)
        for r in read_rows():
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[4])
            except ValueError:
                continue
            if d not in days:
                continue
            if r[1] == "break":
                breaks[d] += m
            else:
                days[d] += m
                key = r[5] or "(no task)"
                tasks[key] = tasks.get(key, 0) + m
                if kws_by_day[d] and self._is_signal(r[5], kws_by_day[d]):
                    sig[d] += m

        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("480x540")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=8)

        lines, total, btotal = ["Per day (work | breaks):"], 0, 0
        for d in days:
            m, b = days[d], breaks[d]
            total += m
            btotal += b
            if mode == "month" and not m and not b:
                continue
            lines.append(f"  {d.strftime('%a %d.%m')}  {m / 60:>6.2f} h  |  {b / 60:>5.2f} h")
        lines.append(f"  {'TOTAL':<10} {total / 60:>6.2f} h  |  {btotal / 60:>5.2f} h")
        sig_work = sum(days[d] for d in days if kws_by_day[d])
        if sig_work:
            stot = sum(sig.values())
            lines.append(f"  {'SIGNAL':<10} {stot / 60:>6.2f} h  "
                         f"({round(100 * stot / sig_work)}% of tracked work)")

        cats, any_cat = {}, False
        for t, m in tasks.items():
            if ":" in t:
                c, any_cat = t.split(":", 1)[0].strip(), True
            else:
                c = "(uncategorised)"
            cats[c] = cats.get(c, 0) + m
        if any_cat:
            lines += ["", "Per category:"]
            for c, m in sorted(cats.items(), key=lambda x: -x[1]):
                lines.append(f"  {m / 60:>6.2f} h  {c}")

        lines += ["", "Per task:"]
        for t, m in sorted(tasks.items(), key=lambda x: -x[1]):
            lines.append(f"  {m / 60:>6.2f} h  {t}")
        txt.insert("1.0", "\n".join(lines))
        txt.config(state="disabled")

    def _trend(self):
        data = weekly_totals(8)
        win = tk.Toplevel(self)
        win.title("Tracked hours — last 8 weeks")
        W, H, PAD = 520, 300, 36
        cv = tk.Canvas(win, width=W, height=H, background="white",
                       highlightthickness=0)
        cv.pack(padx=8, pady=8)
        mx = max((m for _, m in data), default=0) or 1
        bw = (W - 2 * PAD) / len(data)
        for i, (mon, m) in enumerate(data):
            x0 = PAD + i * bw + 6
            x1 = PAD + (i + 1) * bw - 6
            h = (H - 2 * PAD) * m / mx
            y0 = H - PAD - h
            cv.create_rectangle(x0, y0, x1, H - PAD, fill="#4a6fa5", outline="")
            cv.create_text((x0 + x1) / 2, H - PAD + 12,
                           text=f"W{mon.isocalendar().week}", font=("Segoe UI", 8))
            if m:
                cv.create_text((x0 + x1) / 2, y0 - 10, text=f"{m / 60:.1f}h",
                               font=("Segoe UI", 8))
        cv.create_line(PAD, H - PAD, W - PAD, H - PAD)

    # ----- calendar export -----

    def _export_ics(self):
        monday = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
        path, n = week_to_ics(monday)
        if messagebox.askyesno(APP_NAME,
                               f"Exported {n} sessions to\n{path}\n\nOpen folder?"):
            self._open_folder()

    # ----- misc -----

    def _open_folder(self):
        os.startfile(data_dir())

    def _on_close(self):
        if self.state != "idle":
            ans = messagebox.askyesnocancel(
                APP_NAME, "Timer is still going.\n\n"
                          "Yes = log the session and close\n"
                          "No = keep it running (resumes at next launch)\n"
                          "Cancel = don't close")
            if ans is None:
                return
            if ans:
                now = dt.datetime.now()
                if self.state == "working":
                    self._log_work_until(now)
                elif self.state == "break":
                    bsecs = int((now - self.break_start).total_seconds())
                    self._append_text(f"--- Break duration: {hms_unpadded(bsecs)} ")
                    self._csv_interval("break", self.break_start, now)
                self._append_text("--- Session reset, studying duration: "
                                  f"{hms_padded(self.cum_secs)}\n"
                                  + event_line("Reset", now, self.cum_secs))
                self.state = "idle"
            self._save_state()
        self._save_diary()
        self.destroy()


if __name__ == "__main__":
    if already_running():
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(APP_NAME, "TimerDiary is already running — "
                                      "check the taskbar (or the other monitor).")
        sys.exit(0)
    App().mainloop()
