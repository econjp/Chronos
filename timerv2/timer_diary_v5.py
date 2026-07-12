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

New in v6.7 (link the faces):
  - Deadlines can now point at a Goal (dropdown in Tools > Deadline
    countdowns). The linked goal's one-line "why" shows next to the
    deadline in the Life dashboard and the burn-down window title —
    seeing why a deadline matters next to when it's due.

New in v6.6 (friction pass + lens convergence finished):
  - sleep-override time entry accepts 1/01/0120/120/1:20 — no colon, no
    leading zero required.
  - Tasks/Library "Add" gets a plain est-h field and a priority picker —
    [2h] bracket typing no longer required (still works as a fallback).
  - Add past session gained a "carved out of a break" checkbox: logs the
    work AND shrinks the covering break by the same minutes, so
    reclassifying part of a break as real work doesn't double-count it.
  - deadlines' match field now accepts comma-separated multi-keyword
    matching, same as Goals/SIGNAL (a side effect of finishing the lens
    convergence started in v6.3 — see HANDOFF.md).

New in v6.5 (the task library):
  - TASK LIBRARY: Goals/Tasks/TODO/SOMEDAY unified around the existing
    Tasks window. Every item now has a priority you click to cycle
    (signal/normal/someday), an optional linked goal, and a source (which
    day or theme it came from). TODO:/SOMEDAY: bullets anywhere — main
    diary or a themed-writing session — auto-capture into the library;
    the bullet text still lives in the day file too, this just tracks it.
  - status bar quietly flags "not today's signal" when the active task
    doesn't match SIGNAL — visibility, not a blocking gate.
  - per-monitor DPI awareness set at startup — fixes dashboard widgets
    overlapping on a mixed-DPI laptop+monitor setup.
  - workout dot on the sleep graph now needs >=10 min (was flagging tiny
    Apple Watch "Other" activity blips as a workout).

New in v6.4 (themed writing + honest insights):
  - THEMED WRITING (Ctrl+T / View > Browse themes): a distraction-free
    popup for anything that isn't work — career thinking, a house move,
    a business idea, brainstorming, a someday list. Save writes one
    delimited block into TODAY's day file; no second data store. Browse
    themes reads every day file's blocks back out, grouped by topic,
    oldest first — the whole thread on one subject in one scroll.
  - INSIGHTS FIXED: sleep/energy-vs-output were quietly averaging in
    days you never opened the app (0 tracked minutes dragging the
    average toward zero) — now active-days-only, and spelled out in
    full sentences instead of a terse arrow chain.
  - TODO carry-over now requires '-'/'*'/'[ ]' bullets under a 'TODO:'
    header — a paragraph of brainstorming no longer becomes tomorrow's
    todo wall. New 'SOMEDAY:' header (same bullets) is simply never
    carried — write low-priority ideas there.
  - Life dashboard gained a 14-night sleep bar graph (>=7h/<7h shading,
    workout dot) under the week bars.

New in v6.3 (consolidation, not a feature — the architecture converges):
  - THE LENS PRIMITIVE: SIGNAL, Goals and Deadlines were three concepts
    secretly the same shape — (keywords, date range) -> minutes. They now
    resolve through ONE pair of module functions, task_matches() and
    matched_minutes(); _is_signal and _goal_minutes route through it.
    Deadline/burn-down/capacity migrate next (see HANDOFF.md). No user-
    visible change; the code just stopped saying the same thing 6 ways.

New in v6.2 (direction: goals above deadlines, the loop closes weekly):
  - GOALS (Tools > Goals — the why layer): deadlines answer WHEN, goals
    answer WHY. Each goal = name + one-line why + task keywords +
    optional h/week ambition. The dashboard's GOALS section shows where
    the hours actually point — this week, 4-week average, % of tracked —
    and calls out drift: "nothing in 14 days; still a goal?"
  - WEEK REVIEW: Monday's day file opens with last week's honest numbers
    (hours, active days, signal %, vs the week before, per goal) and the
    two questions that matter — "what worked / what stole time? ->" —
    answered in the text, where they live. The Friday AI export and the
    Monday review now close the same loop.
  - goals ride along in the JSON life export.
  - HANDOFF.md at the repo root: vision, architecture, data formats and
    backlog — any future session (or another dev platform) starts there.

New in v6.1 (the whole life joins the record):
  - ENERGY line: each day header gets "ENERGY: " — type 1-5 when you know
    it, right in the text (the sacred rule: everything lives in the day
    txt). It becomes one more key on the day record — exactly the way
    v6.0 said new sources would — and the insights cross it with the
    rest: energy >=4 vs <=2 days' output, energy after >=7h vs <7h sleep.
  - LIFE BALANCE (in the dashboard): the week's WAKING hours accounted —
    tracked work, breaks, meetings, workouts, by-project split, and the
    honest remainder: "unaccounted ~34h — meals, commute, people, scroll.
    The diary knows; the timer doesn't." A life platform that only sees
    the tracked slice isn't one.
  - EXPORT LIFE RECORD (File menu): every day the app knows anything
    about — timer, signal, energy, sleep, workout, steps, meetings,
    capacity, full diary text — as one plain JSON file. The data outlives
    the app; any future tool starts from this file.
  - weekly/monthly summary and the AI export now read through the v6.0
    day index (one parse, not one scan per view); calendar busy-time now
    also covers the past two weeks so the balance sees real meetings.

New in v6.0 (the consolidation — one record, one dashboard, clean data):
  - THE DAY RECORD: one internal unit (_life_day) that merges everything
    known about a date — timer minutes, signal share, sleep (override >
    import), workout, steps, meeting hours, planned capacity. This is the
    platform atom: a future data source (mood, money, screen time) becomes
    one new key on the record, not a new parser in every window.
  - LIFE DASHBOARD (View menu / Ctrl+D): one window instead of nine —
    today (work, signal, plan vs capacity, sleep), the week as bars vs
    last week and planned capacity, every deadline with the slack verdict,
    and INSIGHTS that cross-reference the sources: sleep ≥7h vs <7h daily
    output, your deep hours of day, focus-block fragmentation trend,
    estimate multiplier, streaks. One "Copy for AI review" exports the
    whole consolidated picture.
  - DATA DOCTOR (Tools): scans sessions.csv for task-name spelling
    variants ("Thesis"/"thesis: ch4 "), junk rows, exact duplicates and
    overlapping intervals — shows the report, and Clean merges/drops with
    a backup first. The analyses are only as honest as the substrate.
  - cached csv parsing (mtime-keyed) + a per-day index: the history is
    parsed once per change instead of once per window per task per day.

New in v5.9 (the pieces feed each other):
  - MORNING PLAN: the new day header now states today's mission —
    "plan today: Thesis 5.4h = 5.4h needed · 4.0h available ⚠ tight".
    Deadline scopes x capacity x calendar, decided before you decide.
  - CALENDAR-AWARE CAPACITY: File > "Calendar busy-time (.ics)" — export
    your Outlook calendar once in a while; meeting hours are subtracted
    from available capacity everywhere (week plan, morning plan).
    Recurring events and all-day events are skipped (stated, not hidden).
  - OFF DAYS: list vacation dates in the Week plan window — zero capacity.
  - ESTIMATE LEARNING: the Tasks window reads your own "--- Done: x
    (est 2h, actual 3.4h)" history and tells you your personal multiplier
    ("your actuals run ×1.7 your estimates").
  - MEETING MODE (Tools): pauses idle detection for 90 min — lectures,
    meetings, long reading. Invoke again to cancel.
  - MONTH HEATMAP (View): GitHub-style grid of the last 16 weeks' daily
    hours. Streaks and dead weeks, visible.

New in v5.8 (the planning engine):
  - DEADLINES V2: each deadline can carry a start date and a TOTAL-HOURS
    scope. With a scope the burn-down becomes real (ideal line start->due
    covering the scope) and the app states "needs 4.3h/day from now".
  - burn-down works for EVERY deadline (picker when there are several).
  - CAPACITY PLANNER (View > Week plan): set your realistic hours per
    weekday once; the app compares available hours until each due date
    against what the deadlines demand and prints the honest verdict —
    "slack +6h" or "overbooked by 9h: cut something".
  - TASK BACKLOG (View > Tasks): add tasks as "name [2h]", see actual
    hours accumulate against the estimate, Start straight from the list,
    mark Done -> "--- Done: task (est 2h, actual 1.4h)" lands in the day
    file. Estimate-vs-actual history starts accruing for future learning.

New in v5.7 (pacing):
  - VELOCITY: starting a task shows your real pace in the status bar —
    "pace 2.31h/active-day (5d of last 14)" — computed from csv history,
    so estimates meet reality before the time-box even starts.
  - DEADLINE BURN-DOWN (View menu): ideal cumulative line at your weekly
    target vs the actual line, red gap when trailing. The panic view.

New in v5.6 (task engine):
  - TIME-BOX a task by typing e.g. "email: EU [15m]" — when today's total
    on that task blows the box, the clock turns red, it beeps, and
    "!!! time-box exceeded !!!" lands in the day file. For admin tasks
    that balloon ("the air-mattress problem").
  - MULTIPLE DEADLINES (Tools menu): up to 4, each with date, task
    keyword and weekly target; the totals line shows them all, with ⚠
    when you're behind pace with <3 weeks left.
  - FATIGUE WINDOW: 19:00-21:00 the break pill escalates at 5 min
    (not 15) — "move or leave, don't scroll!" (the user's own dead zone).
  - RIGHT-CLICK the timeline to set real bed/wake times for last night —
    overrides the estimate, band label becomes "zzz (set)".

New in v5.5 (feedback engine v1):
  - MORNING VERDICT: a new day file opens with yesterday's numbers AND one
    honest rule-based line ("busy but scattered (4.2h, only 31% signal) —
    pick the signal task FIRST today.").
  - TODO CARRY-OVER: yesterday's TODO lines are copied under the new day's
    header, so the morning file opens with your own instructions.
  - signal trend arrow in the totals line (last 7 days vs previous 7).
  - PER-TASK TODAY counter in the title ("0:21 — Building · today 1.42h") —
    the session clock resets between sessions, this doesn't.
  - the break pill escalates after 15 min: "move, don't scroll!"
  - easter egg: double-click the big clock.

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


_ROWS_CACHE = {"key": None, "rows": [], "idx_key": None, "days": {}}


def read_rows():
    """All csv rows, normalised to 7 columns (v4 files had no 'type').
    Cached on the file's (mtime, size): every window reads through here,
    so the history is parsed once per change, not once per view. Callers
    must treat the result as read-only."""
    try:
        st = os.stat(SESSIONS_CSV)
    except OSError:
        _ROWS_CACHE.update(key=None, rows=[])
        return []
    key = (st.st_mtime_ns, st.st_size)
    if _ROWS_CACHE["key"] == key:
        return _ROWS_CACHE["rows"]
    with open(SESSIONS_CSV, newline="", encoding="utf-8") as f:
        raw = list(csv.reader(f, delimiter=";"))
    out = []
    for r in raw[1:]:
        if len(r) == 6:          # v4 format: date;start;end;minutes;task;note
            r = [r[0], "work"] + r[1:]
        if len(r) >= 5:
            out.append(r + [""] * (7 - len(r)))
    _ROWS_CACHE.update(key=key, rows=out)
    return out


def day_index():
    """{date_iso: {"work": min, "brk": min, "tasks": {task: min}}} over the
    whole history — the base aggregate every consolidated view reads.
    Rebuilt only when the csv changes."""
    read_rows()
    if _ROWS_CACHE["idx_key"] != _ROWS_CACHE["key"]:
        idx = {}
        for r in _ROWS_CACHE["rows"]:
            try:
                m = int(r[4])
            except ValueError:
                continue
            rec = idx.setdefault(r[0], {"work": 0, "brk": 0, "tasks": {}})
            if r[1] == "break":
                rec["brk"] += m
            else:
                rec["work"] += m
                t = r[5].strip() or "(no task)"
                rec["tasks"][t] = rec["tasks"].get(t, 0) + m
        _ROWS_CACHE.update(idx_key=_ROWS_CACHE["key"], days=idx)
    return _ROWS_CACHE["days"]


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
    rec = day_index().get(date_iso)
    return (rec["work"], rec["brk"]) if rec else (0, 0)


def task_matches(task, kws):
    """The one definition of 'this task belongs to this lens': any keyword
    is a case-insensitive substring of the task name. SIGNAL, Goals and
    Deadlines are all just different keyword sets over this same test."""
    t = (task or "").lower()
    return any(k in t for k in kws)


def matched_minutes(kws, lo, hi):
    """Work minutes on tasks matching `kws` over the inclusive date range
    [lo, hi]. The shared primitive under every keyword-lens: a goal's
    weekly hours, a deadline's progress and a day's signal are all this
    call with a different keyword set and window. Reads the cached day
    index, so it's one dict walk, not a csv rescan."""
    if not kws:
        return 0
    idx, tot, d = day_index(), 0, lo
    while d <= hi:
        rec = idx.get(d.isoformat())
        if rec:
            for t, m in rec["tasks"].items():
                if task_matches(t, kws):
                    tot += m
        d += dt.timedelta(days=1)
    return tot


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


# ---------------- calendar (.ics) busy-time import ----------------

def parse_ics_busy(path, start, end):
    """{date_iso: busy_hours} from an exported .ics, window [start, end].
    Skips all-day events and recurring (RRULE) events — good enough for
    'subtract my meetings from capacity', not a calendar client."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return {}
    text = text.replace("\r\n ", "").replace("\n ", "")   # unfold folds
    utc_off = dt.datetime.now().astimezone().utcoffset() or dt.timedelta()
    busy = {}
    for block in text.split("BEGIN:VEVENT")[1:]:
        block = block.split("END:VEVENT")[0]
        if "RRULE:" in block:
            continue

        def field(name):
            m = re.search(rf"^{name}[^:\n]*:([^\s]+)", block, re.M)
            return m.group(1).strip() if m else None

        def parse(v):
            if v is None or len(v) <= 8:      # missing or all-day
                return None
            naive = dt.datetime.strptime(v[:15], "%Y%m%dT%H%M%S")
            return naive + utc_off if v.rstrip().endswith("Z") else naive

        try:
            sdt, edt = parse(field("DTSTART")), parse(field("DTEND"))
        except ValueError:
            continue
        if not sdt or not edt or edt <= sdt:
            continue
        cur = sdt
        while cur < edt:                       # split multi-day per day
            nxt = dt.datetime.combine(cur.date() + dt.timedelta(days=1),
                                      dt.time())
            seg_end = min(edt, nxt)
            if start <= cur.date() <= end:
                iso = cur.date().isoformat()
                busy[iso] = busy.get(iso, 0.0) + (
                    seg_end - cur).total_seconds() / 3600
            cur = seg_end
    return busy


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
        self.task_box_secs = None      # [15m]-style time-box for active task
        self.box_warned = False
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

    _is_signal = staticmethod(task_matches)   # a lens is a lens; see module top

    def _day_signal(self, day, kws=None, rows=None):
        """(signal_min, work_min) for one day given its keywords."""
        if kws is None:
            kws = self._signal_kws(day)
        sig = work = 0
        if kws:
            iso = day.isoformat()
            for r in (rows if rows is not None else read_rows()):
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

    # ----- energy meter (1-5 in the day header, like SIGNAL) -----

    @staticmethod
    def _energy_from_text(text):
        """First 1-5 digit on the first 'ENERGY:' line, else None."""
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("energy:"):
                m = re.search(r"[1-5]", s[7:12])
                return int(m.group()) if m else None
        return None

    def _day_energy(self, day=None):
        if day is None or day == self.today:
            return self._energy_from_text(self.diary.get("1.0", "end-1c"))
        try:
            with open(self.diary_path(day), encoding="utf-8") as f:
                return self._energy_from_text(f.read())
        except OSError:
            return None

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
        filem.add_command(label="Export life record (JSON)…",
                          command=self._export_life_json)
        filem.add_separator()
        filem.add_command(label="Open data folder", command=self._open_folder)
        filem.add_command(label="Change diary folder…", command=self._change_diary_dir)
        filem.add_command(label="Health import folder…", command=self._set_health_dir)
        filem.add_command(label="Calendar busy-time (.ics)…", command=self._set_ics)
        filem.add_separator()
        filem.add_command(label="Exit", command=self._on_close)
        m.add_cascade(label="File", menu=filem)

        viewm = tk.Menu(m, tearoff=0)
        viewm.add_command(label="Life dashboard", accelerator="Ctrl+D",
                          command=self._dashboard)
        viewm.add_command(label="Themed writing…", accelerator="Ctrl+T",
                          command=self._themed_writing)
        viewm.add_command(label="Browse themes…", command=self._browse_themes)
        viewm.add_separator()
        viewm.add_command(label="Weekly summary", command=lambda: self._summary("week"))
        viewm.add_command(label="Monthly summary", command=lambda: self._summary("month"))
        viewm.add_command(label="Tasks / backlog…", command=self._tasks_win)
        viewm.add_command(label="Week plan / capacity…", command=self._capacity_win)
        viewm.add_separator()
        viewm.add_command(label="Trend (8 weeks)", command=self._trend)
        viewm.add_command(label="Month heatmap", command=self._heatmap)
        viewm.add_command(label="Deadline burn-down", command=self._burndown)
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
        toolsm.add_command(label="Meeting mode (idle off 90 min)",
                           command=self._meeting_mode)
        toolsm.add_separator()
        toolsm.add_command(label="Data doctor — check & clean history…",
                           command=self._data_doctor)
        toolsm.add_separator()
        toolsm.add_command(label="Global hotkey…", command=self._set_hotkey)
        toolsm.add_command(label="Deadline countdown…", command=self._set_deadline)
        toolsm.add_command(label="Goals — the why layer…", command=self._set_goals)
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

    def deadlines(self):
        """List of deadline dicts; migrates the old single dl_* settings."""
        dls = self.settings.get("deadlines")
        if dls is None and self.settings.get("dl_name"):
            dls = [{"name": self.settings["dl_name"],
                    "date": self.settings.get("dl_date", ""),
                    "match": self.settings.get("dl_match", ""),
                    "target_h": self.settings.get("dl_target_h", 0)}]
        return dls or []

    def _set_deadline(self):
        win = tk.Toplevel(self)
        win.title("Deadline countdowns")
        win.resizable(False, False)
        win.grab_set()
        cols = ("Name (empty = off)", "Start (opt)", "Due (YYYY-MM-DD)",
                "Total h (opt)", "h/week (opt)", "Tasks containing", "Goal (opt)")
        keys = ("name", "start", "date", "total_h", "target_h", "match", "goal")
        for c, lbl in enumerate(cols):
            ttk.Label(win, text=lbl).grid(row=0, column=c, padx=4, pady=(8, 2))
        cur = self.deadlines()
        goal_names = [""] + [g["name"] for g in self.goals()]
        grid = []
        for i in range(4):
            row = []
            d = cur[i] if i < len(cur) else {}
            for c, key in enumerate(keys):
                if key == "goal":
                    e = ttk.Combobox(win, state="readonly", width=11,
                                     values=goal_names)
                    e.set(d.get("goal") or "")
                else:
                    e = ttk.Entry(win, width=13 if c in (0, 5) else 10)
                    v = d.get(key, "")
                    e.insert(0, str(v) if v else "")
                e.grid(row=i + 1, column=c, padx=4, pady=2)
                row.append(e)
            grid.append(row)

        def save():
            out = []
            for row in grid:
                vals = {k: (row[c].get() if k == "goal" else row[c].get().strip())
                        for c, k in enumerate(keys)}
                if not vals["name"]:
                    continue
                try:
                    dt.date.fromisoformat(vals["date"])
                    if vals["start"]:
                        dt.date.fromisoformat(vals["start"])
                    total = float(vals["total_h"] or 0)
                    target = float(vals["target_h"] or 0)
                except ValueError:
                    messagebox.showerror(
                        APP_NAME, f"Check dates / hours for '{vals['name']}'.",
                        parent=win)
                    return
                out.append({"name": vals["name"], "start": vals["start"],
                            "date": vals["date"], "total_h": total,
                            "target_h": target, "match": vals["match"],
                            "goal": vals["goal"] or None})
            self.settings["deadlines"] = out
            self.settings["dl_name"] = ""      # retire the legacy single form
            save_settings(self.settings)
            self._refresh_totals()
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(
            row=5, column=6, sticky="e", padx=4, pady=8)

    def _goal_why(self, name):
        """The one-line 'why' text for a linked goal, or ''."""
        for g in self.goals():
            if g["name"] == name:
                return g.get("why") or ""
        return ""

    # ----- goals (the why layer above deadlines) -----

    def goals(self):
        return self.settings.get("goals") or []

    @staticmethod
    def _match_kws(spec):
        """Comma-separated keyword spec -> lowered keyword list. Goals use
        a comma list; deadlines use a single 'match' string — same thing."""
        return [k.strip().lower() for k in (spec or "").split(",") if k.strip()]

    def _goal_minutes(self, g, lo, hi):
        """Tracked minutes [lo, hi] on tasks matching the goal's keywords."""
        return matched_minutes(self._match_kws(g.get("match")), lo, hi)

    def _set_goals(self):
        """Deadlines answer 'when'; goals answer WHY the hours happen.
        Each goal: a name, the reason, task keywords, an optional weekly
        ambition. The dashboard then shows where the hours actually point."""
        win = tk.Toplevel(self)
        win.title("Goals — the why layer")
        win.resizable(False, False)
        win.grab_set()
        cols = ("Goal (empty = off)", "Why (one line)",
                "Tasks containing (comma-sep)", "h/week (opt)")
        keys = ("name", "why", "match", "target_h")
        for c, lbl in enumerate(cols):
            ttk.Label(win, text=lbl).grid(row=0, column=c, padx=4, pady=(8, 2))
        cur = self.goals()
        grid = []
        for i in range(5):
            g = cur[i] if i < len(cur) else {}
            row = []
            for c, key in enumerate(keys):
                e = ttk.Entry(win, width=(8 if key == "target_h" else 22))
                v = g.get(key, "")
                e.insert(0, str(v) if v else "")
                e.grid(row=i + 1, column=c, padx=4, pady=2)
                row.append(e)
            grid.append(row)

        def save():
            out = []
            for row in grid:
                vals = {k: row[c].get().strip() for c, k in enumerate(keys)}
                if not vals["name"]:
                    continue
                try:
                    vals["target_h"] = float(vals["target_h"] or 0)
                except ValueError:
                    messagebox.showerror(
                        APP_NAME, f"h/week must be a number on "
                                  f"'{vals['name']}'.", parent=win)
                    return
                out.append(vals)
            self.settings["goals"] = out
            save_settings(self.settings)
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(
            row=6, column=3, sticky="e", padx=4, pady=8)

    def _dl_progress(self, dl):
        """Progress numbers for one deadline: matched hours done since its
        start (or all time), days left, and — when a total-hours scope is
        set — remaining hours, needed h/day, and whether we're behind the
        straight start->due line. Routes through matched_minutes — the
        same (keywords, window) -> minutes primitive SIGNAL and Goals
        use — when a task keyword is set; an empty match keeps its old
        meaning of 'count all work', which matched_minutes deliberately
        doesn't support (there, no keywords means no signal)."""
        due = dt.date.fromisoformat(dl["date"])
        start = None
        if dl.get("start"):
            try:
                start = dt.date.fromisoformat(dl["start"])
            except ValueError:
                pass
        kws = self._match_kws(dl.get("match", ""))
        lo = start or dt.date.min
        if kws:
            done = matched_minutes(kws, lo, self.today)
        else:
            idx = day_index()
            lo_iso = lo.isoformat()
            done = sum(rec["work"] for iso, rec in idx.items()
                      if lo_iso <= iso <= self.today.isoformat())
        out = {"due": due, "start": start, "done_h": done / 60,
               "left": (due - dt.date.today()).days}
        total = float(dl.get("total_h") or 0)
        if total:
            rem = max(0.0, total - done / 60)
            out["total_h"] = total
            out["remaining_h"] = rem
            out["needed_per_day"] = rem / max(out["left"], 1)
            if start:
                span = max((due - start).days, 1)
                elapsed = min(max((dt.date.today() - start).days + 1, 0), span)
                out["behind"] = done / 60 < total * elapsed / span - 0.1
            else:
                out["behind"] = False
        return out

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
        self._quote_i = 0
        self.clock.bind("<Double-Button-1>", self._signal_quote)

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
        self.timeline.bind("<Button-3>", self._set_sleep_override)

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

    QUOTES = ["Zero noise. 100% signal.",
              "Every genius in history ran at ~100% signal.",
              "The phone is the anti-signal device.",
              "Tired? Move. Don't scroll.",
              "The day file doesn't lie."]

    def _signal_quote(self, event=None):
        self.status.config(text=self.QUOTES[self._quote_i % len(self.QUOTES)])
        self._quote_i += 1

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
        self.bind("<Control-d>", self._dashboard)
        self.bind("<Control-t>", self._themed_writing)
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
            note = ""
            if self.active_task and getattr(self, "task_today_min", 0):
                note = f" · {self.task_today_min / 60:.2f}h on it today"
            if self.active_task:
                v = self._task_velocity(self.active_task)
                if v:
                    note += f" · pace {v[0] / 60:.2f}h/active-day ({v[1]}d of last 14)"
                kws = self._signal_kws()
                if kws and not self._is_signal(self.active_task, kws):
                    note += " · ⚠ not today's signal"
            self.status.config(text=f"Working — {self.active_task or '(no task)'}{note}")
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

    TASKBOX_RE = re.compile(r"\s*\[(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\]\s*$", re.I)

    @classmethod
    def _parse_box(cls, raw):
        """'email: EU [15m]' -> ('email: EU', 900). No box -> (raw, None)."""
        m = cls.TASKBOX_RE.search(raw)
        if m and (m.group(1) or m.group(2)):
            secs = (int(m.group(1) or 0) * 60 + int(m.group(2) or 0)) * 60
            return raw[:m.start()].strip(), secs
        return raw.strip(), None

    def _log_task_if_new(self):
        """Remember the task for csv rows and write it into the day file.
        A trailing [15m] / [1h30m] time-boxes the task (today's total)."""
        t, box = self._parse_box(self.task_var.get())
        self.active_task = t
        self.task_box_secs = box
        self.box_warned = False
        if t:
            self._remember_task(t)
        if t and t != self.logged_task:
            self._append_text(f"--- Task: {t}"
                              + (f" [time-box {box // 60}m]" if box else ""))
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
        if self._parse_box(self.task_var.get())[0] == self.active_task:
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

    def _task_velocity(self, task, days=14):
        """(avg_min_per_active_day, active_days) over the last N days,
        or None if the task has no history. Real pace, not wishes."""
        t = task.strip().lower()
        cutoff = self.today - dt.timedelta(days=days - 1)
        per_day = {}
        for r in read_rows():
            if r[1] == "break" or r[5].strip().lower() != t:
                continue
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[4])
            except ValueError:
                continue
            if cutoff <= d <= self.today:
                per_day[d] = per_day.get(d, 0) + m
        if not per_day:
            return None
        return sum(per_day.values()) / len(per_day), len(per_day)

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
            title = (f"{secs // 3600}:{secs % 3600 // 60:02} — "
                     f"{self.task_var.get().strip() or APP_NAME}")
            task_tot = None
            if self.active_task and self.work_start:
                task_tot = (getattr(self, "task_today_min", 0) * 60
                            + int((dt.datetime.now() - self.work_start).total_seconds()))
                title += f" · today {task_tot / 3600:.2f}h"
            self.title(title)
            self._check_time_box(task_tot)
            self._watch_idle()
        elif self.state == "break":
            bsecs = int((dt.datetime.now() - self.break_start).total_seconds())
            self.clock.config(text=f"☕ {hms_padded(bsecs)}", foreground="")
            self.title(f"☕ break {bsecs // 60}:{bsecs % 60:02} — {APP_NAME}")
            self._update_pill(bsecs)
        else:
            self.clock.config(text="0:00:00", foreground="")
            self.title(("⏸ not tracking — " + APP_NAME)
                       if self.nudge_var.get() else APP_NAME)
        if self.state != "break":
            self._hide_pill()
        self._tl_tick = getattr(self, "_tl_tick", 0) + 1
        if self._tl_tick % 60 == 0 and not self.compact:
            self._draw_timeline()      # keep the live segment growing
        self.after(1000, self._tick)

    def _check_time_box(self, task_tot):
        """Escalate when today's total on the boxed task exceeds the box."""
        if not self.task_box_secs or task_tot is None:
            self.clock.config(foreground="")
            return
        if task_tot <= self.task_box_secs:
            self.clock.config(foreground="")
            return
        self.clock.config(foreground="#a03030")
        if not self.box_warned:
            self.box_warned = True
            over = (task_tot - self.task_box_secs) // 60
            self._append_text(
                f"!!! {dt.datetime.now():%H:%M} time-box exceeded: "
                f"{self.active_task} [{self.task_box_secs // 60}m]"
                + (f" +{over}m" if over else "") + " — wrap it up !!!")
            try:
                import winsound
                winsound.MessageBeep(0x30)
            except Exception:
                pass

    # ----- floating break pill -----

    BREAK_WARN_SECS = 15 * 60      # pill turns red after this
    FATIGUE_WARN_SECS = 5 * 60     # 19-21: the user's own doomscroll window

    def _update_pill(self, bsecs, now_h=None):
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
        fatigue = 19 <= (now_h if now_h is not None
                         else dt.datetime.now().hour) < 21
        over = bsecs > (self.FATIGUE_WARN_SECS if fatigue
                        else self.BREAK_WARN_SECS)
        t = f"☕ break {bsecs // 60}:{bsecs % 60:02} — "
        if over and fatigue:
            t += "fatigue window: move or LEAVE, don't scroll!"
        elif over:
            t += "move, don't scroll!"
        else:
            t += "click to work"
        self.pill_lbl.config(text=t, bg="#7a1f1f" if over and fatigue
                             else ("#a03030" if over else "#505050"))

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

    def _meeting_mode(self):
        now = dt.datetime.now()
        if getattr(self, "idle_off_until", None) and now < self.idle_off_until:
            self.idle_off_until = None
            self.status.config(text="Meeting mode off — idle detection back on.")
        else:
            self.idle_off_until = now + dt.timedelta(minutes=90)
            self.status.config(text=f"Meeting mode: idle detection paused "
                                    f"until {self.idle_off_until:%H:%M}. "
                                    "Invoke again to cancel.")

    def _watch_idle(self):
        off = getattr(self, "idle_off_until", None)
        if off and dt.datetime.now() < off:
            self.idle_since = None
            return
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
        rows = read_rows()
        for r in rows:
            if r[1] == "break":
                continue
            try:
                d = dt.date.fromisoformat(r[0])
                if monday <= d <= self.today:
                    week += int(r[4])
            except ValueError:
                continue
        # cumulative minutes on the active task today (title shows it live)
        at = (self.active_task or "").strip().lower()
        self.task_today_min = sum(
            int(r[4]) for r in rows
            if at and r[0] == today_iso and r[1] != "break"
            and r[5].strip().lower() == at and r[4].isdigit())
        text = (f"{self.today.isoformat()} — today {w / 60:.2f} h work"
                + (f" / {b / 60:.2f} h breaks" if b else "")
                + f"   |   week {week / 60:.2f} h")
        # signal %: today by today's SIGNAL line, week per each day's own line
        kws_today = self._signal_kws()
        if kws_today and w:
            sig_today, _ = self._day_signal(self.today, kws_today, rows)
            wk_sig = wk_work = 0
            d = monday
            while d <= self.today:
                s, tot = self._day_signal(
                    d, kws_today if d == self.today else None, rows)
                wk_sig += s
                wk_work += tot
                d += dt.timedelta(days=1)
            text += f"   |   signal {round(100 * sig_today / w)}%"
            if wk_work and wk_work != w:
                text += f" (wk {round(100 * wk_sig / wk_work)}%)"

            def period_pct(lo, hi):
                s = tot = 0
                d = lo
                while d <= hi:
                    kw = kws_today if d == self.today else None
                    ds, dw = self._day_signal(d, kw, rows)
                    s += ds
                    tot += dw
                    d += dt.timedelta(days=1)
                return 100 * s / tot if tot else None

            cur = period_pct(self.today - dt.timedelta(days=6), self.today)
            prev = period_pct(self.today - dt.timedelta(days=13),
                              self.today - dt.timedelta(days=7))
            if cur is not None and prev is not None:
                text += " ↑" if cur - prev >= 5 else (
                        " ↓" if cur - prev <= -5 else " →")
        dls = self.deadlines()
        on_any = False
        for dl in dls:
            try:
                p = self._dl_progress(dl)
                match = dl.get("match", "").lower()
                seg = f"{dl['name']} {p['left']}d"
                if p.get("total_h"):
                    seg += (f" {p['done_h']:.1f}/{p['total_h']:g}h"
                            f" · {p['needed_per_day']:.1f}h/d")
                    if p["behind"] or p["needed_per_day"] > 8:
                        seg = "⚠" + seg
                else:
                    target = float(dl.get("target_h") or 0)
                    if target:
                        kws = self._match_kws(dl.get("match", ""))
                        if kws:
                            wk_m = matched_minutes(kws, monday, self.today)
                        else:
                            idx = day_index()
                            wk_m = sum(rec["work"] for iso, rec in idx.items()
                                      if monday.isoformat() <= iso
                                      <= self.today.isoformat())
                        seg += f" {wk_m / 60:.2f}/{target:g}h"
                        expected = target * 60 * (self.today.weekday() + 1) / 7
                        if p["left"] <= 21 and wk_m < 0.75 * expected:
                            seg = "⚠" + seg
                text += "   |   " + seg
                if not match or match in (self.active_task or "").lower():
                    on_any = True
            except (ValueError, KeyError):
                continue
        # activity dot: green = working on a deadline task right now
        if dls:
            if self.state == "working" and on_any:
                c = "#2e8b2e"
            elif self.state == "break" and on_any:
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
    WORKOUT_DOT_MIN = 10   # minutes — filters Apple Watch's auto-detected
                            # "Other" activity blips from a real workout

    def _sleep_band(self):
        """Sleep band for today's 00-24 bar: (start_min, end_min, exact)
        or None. A right-click override (real bed/wake times) wins;
        otherwise ESTIMATED from last night's imported sleep TOTAL:
        bed ~= last logged event yesterday + 1 h (default 00:00 if the
        evening wasn't logged late), band length = the imported total,
        clipped so it ends before today's first logged activity."""
        ov = self.settings.get("sleep_over", {}).get(self.today.isoformat())
        if ov:
            try:
                bh, bm = map(int, ov[0].split(":"))
                wh, wm = map(int, ov[1].split(":"))
                bed = bh * 60 + bm
                bed += 1440 if bed < 720 else 0     # 01:30 = past midnight
                wake = wh * 60 + wm + 1440          # wake is always today
                if wake > bed:
                    return max(0, bed - 1440), wake - 1440, True
            except (ValueError, IndexError):
                pass
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
        return max(0, bed - 1440), wake - 1440, False

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
                cv.create_text((x0 + x1) / 2, (H + 1) / 2,
                               text="zzz (set)" if band[2] else "zzz (est.)",
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

    @staticmethod
    def _parse_time_loose(s):
        """A bedtime should never need the shift key. Accepts 'HH:MM' /
        'H:MM', or no colon at all: '1'/'01' (hour, :00 assumed),
        '120' (H+MM), '0120'/'1001' (HHMM). Returns (h, m) or None."""
        s = s.strip()
        if not s:
            return None
        if ":" in s:
            parts = s.split(":")
            if len(parts) != 2:
                return None
            h, m = parts
        elif len(s) <= 2:
            h, m = s, "0"
        elif len(s) == 3:
            h, m = s[0], s[1:]
        elif len(s) == 4:
            h, m = s[:2], s[2:]
        else:
            return None
        try:
            h, m = int(h), int(m)
        except ValueError:
            return None
        return (h, m) if 0 <= h < 24 and 0 <= m < 60 else None

    def _set_sleep_override(self, event=None):
        """Right-click on the timeline: enter real bed/wake for last night."""
        cur = self.settings.get("sleep_over", {}).get(self.today.isoformat(),
                                                      ["", ""])
        bed = simpledialog.askstring(
            APP_NAME, "Bed time last night — 1, 01, 0120 or 1:20 all work "
                      "(empty = back to estimate):",
            initialvalue=cur[0], parent=self)
        if bed is None:
            return
        overs = self.settings.setdefault("sleep_over", {})
        if not bed.strip():
            overs.pop(self.today.isoformat(), None)
        else:
            bed_t = self._parse_time_loose(bed)
            if not bed_t:
                messagebox.showerror(APP_NAME, "Couldn't read that time — "
                                     "try 1, 01, 0120 or 1:20.", parent=self)
                return
            wake = simpledialog.askstring(
                APP_NAME, "Wake time this morning — same shortcuts work:",
                initialvalue=cur[1], parent=self)
            if wake is None:
                return
            wake_t = self._parse_time_loose(wake)
            if not wake_t:
                messagebox.showerror(APP_NAME, "Couldn't read that time — "
                                     "try 1, 01, 0120 or 1:20.", parent=self)
                return
            overs[self.today.isoformat()] = [f"{bed_t[0]:02}:{bed_t[1]:02}",
                                             f"{wake_t[0]:02}:{wake_t[1]:02}"]
        save_settings(self.settings)
        self._draw_timeline()

    # ----- diary file -----

    def _load_diary(self, create=False):
        p = self.diary_path()
        self.diary.delete("1.0", "end")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                self.diary.insert("1.0", f.read())
        elif create:
            self.diary.insert("1.0", self._new_day_header() + "\n\n")
            self._save_diary()
        self.diary.mark_set("insert", "end")
        self.diary.edit_modified(False)
        self._maybe_insert_health()

    def _new_day_header(self):
        """Header + yesterday's numbers + a rule-based verdict + carried
        TODOs — the morning brief, straight into the file per the sacred
        rule (everything visible in the day txt)."""
        yday = self.today - dt.timedelta(days=1)
        parts = [f"=== {self.today:%A %d.%m.%Y} ==="]
        yw, yb = day_totals(yday.isoformat())
        if yw or yb:
            ysig, ywork = self._day_signal(yday)
            line = (f"(yesterday: {yw // 60}h{yw % 60:02}m work"
                    f" / {yb // 60}h{yb % 60:02}m breaks")
            if ywork:
                line += f", signal {round(100 * ysig / ywork)}%"
            parts.append(line + ")")
            v = self._verdict(yw, ysig, ywork)
            if v:
                parts.append(v)
        plan = self._plan_line()
        if plan:
            parts.append(plan)
        if self.today.weekday() == 0:
            parts += self._week_review_block()
        parts.append(f"SIGNAL: {self._carry_signal()}")
        parts.append("ENERGY: ")   # type 1-5 when you know it — feeds the record
        todos = self._carry_todos(yday)
        if todos:
            parts += ["", "TODO (carried from yesterday):"] + todos
        try:
            with open(self.diary_path(yday), encoding="utf-8") as f:
                self._auto_capture_bullets(f.read(), f"{yday} diary")
        except OSError:
            pass
        return "\n".join(parts)

    def _plan_line(self):
        """Today's mission: needed h/day per scoped deadline vs today's
        net capacity (weekday hours minus meetings, zero on off days)."""
        parts, need = [], 0.0
        for dl in self.deadlines():
            try:
                p = self._dl_progress(dl)
            except (ValueError, KeyError):
                continue
            if p["left"] >= 0 and p.get("total_h") and p["remaining_h"] > 0:
                parts.append(f"{dl['name']} {p['needed_per_day']:.1f}h")
                need += p["needed_per_day"]
        if not parts:
            return None
        avail = self._day_capacity(self.today)
        busy = self._busy_data().get(self.today.isoformat(), 0.0)
        line = ("plan today: " + " + ".join(parts)
                + f" = {need:.1f}h needed · {avail:.1f}h available")
        if busy:
            line += f" ({busy:.1f}h in meetings)"
        line += (" ✓" if avail >= need else
                 " ⚠ tight — start early, cut the admin")
        return line

    def _week_review_block(self):
        """Monday's file opens with last week's honest numbers and the two
        questions that close the loop — answered in the text, where they
        live. The review ritual, without opening a single window."""
        mon = self.today - dt.timedelta(days=7)
        sun = mon + dt.timedelta(days=6)
        idx = day_index()
        tot = brk = active = 0
        d = mon
        while d <= sun:
            rec = idx.get(d.isoformat())
            if rec:
                tot += rec["work"]
                brk += rec["brk"]
                if rec["work"] >= 30:
                    active += 1
            d += dt.timedelta(days=1)
        if not tot:
            return []
        rows = read_rows()
        sig = 0
        d = mon
        while d <= sun:
            sig += self._day_signal(d, None, rows)[0]
            d += dt.timedelta(days=1)
        # the week before, for the direction arrow
        prev = sum((idx.get((mon - dt.timedelta(days=7 - i)).isoformat())
                    or {"work": 0})["work"] for i in range(7))
        head = (f"WEEK REVIEW W{mon.isocalendar().week}: {tot / 60:.1f}h "
                f"over {active} active day(s)")
        if sig:
            head += f", signal {round(100 * sig / tot)}%"
        if prev:
            head += f" ({(tot - prev) / 60:+.1f}h vs week before)"
        parts = ["", head]
        for g in self.goals():
            m = self._goal_minutes(g, mon, sun)
            parts.append(f"  {g['name']}: {m / 60:.1f}h")
        parts.append("  what worked / what stole time? ->")
        return parts

    @staticmethod
    def _verdict(work_min, sig_min, sig_work):
        """One honest line about yesterday. Rule-based, no flattery."""
        h = work_min / 60
        if sig_work:
            pct = 100 * sig_min / sig_work
            if h >= 5 and pct >= 60:
                return (f"verdict: strong day ({h:.1f}h, {pct:.0f}% signal)"
                        " — repeat it.")
            if h >= 3 and pct < 40:
                return (f"verdict: busy but scattered ({h:.1f}h, only "
                        f"{pct:.0f}% signal) — pick the signal task FIRST today.")
        if h < 3:
            return f"verdict: light day ({h:.1f}h tracked) — what stole it?"
        return None

    _BULLET_RE = re.compile(r"^[-*]\s+\S|^\[[ xX]\]\s+\S")

    def _carry_todos(self, yday):
        """Bullet lines ('- x', '* x', '[ ] x') directly under a 'TODO:'
        header from yesterday's file — carried forward until done or
        deleted. Free paragraphs are never swept in, even ones that
        mention 'todo' in passing — only marked bullets are, so a day of
        brainstorming prose doesn't become tomorrow's todo wall. Write
        low-priority someday/maybe items under a 'SOMEDAY:' header
        instead — same bullet syntax, never carried, just browsable
        (Search all days / Browse themes)."""
        try:
            with open(self.diary_path(yday), encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError:
            return []
        out, grab = [], False
        for ln in lines:
            s = ln.strip()
            low = s.lower()
            if grab:
                if self._BULLET_RE.match(s):
                    out.append(ln)
                    continue
                if s == "":
                    continue
                grab = False
            if low in ("todo:", "todo") and not low.startswith("todo (carried"):
                grab = True
        return out[:12]

    # ----- task library (the one place messy ideas/todos live) -----

    def _extract_bullets(self, text):
        """[(kind, item_text), ...] for every bullet under a 'TODO:' or
        'SOMEDAY:' header anywhere in `text`. kind is 'normal' or
        'someday' — the same bullet syntax, just a different header, so
        no new parsing rule to learn."""
        out, grab = [], None
        for ln in text.splitlines():
            s = ln.strip()
            low = s.lower()
            if grab:
                m = self._BULLET_RE.match(s)
                if m:
                    out.append((grab, s[m.end() - 1:].strip()))
                    continue
                if s == "":
                    continue
                grab = None
            if low in ("todo:", "todo") and not low.startswith("todo (carried"):
                grab = "normal"
            elif low in ("someday:", "someday"):
                grab = "someday"
        return out

    def _add_task(self, name, est_h=0, priority="normal", goal=None, source=None):
        """Add to the library, deduped by normalized name — the same
        bullet carried unchanged for a few days doesn't create
        duplicates every time it's re-scanned."""
        name = name.strip()
        if not name:
            return
        key = " ".join(name.lower().split())
        tasks = self.settings.setdefault("tasks", [])
        if any(" ".join(t["name"].lower().split()) == key for t in tasks):
            return
        tasks.append({"name": name, "est_h": est_h, "priority": priority,
                      "goal": goal, "source": source,
                      "added": self.today.isoformat()})
        save_settings(self.settings)

    def _auto_capture_bullets(self, text, source):
        """Every TODO:/SOMEDAY: bullet in `text` lands in the task
        library automatically — write one anywhere (main diary, a
        themed-writing session) and it's tracked, not just carried
        forward as raw text until you happen to reread it."""
        for kind, item in self._extract_bullets(text):
            self._add_task(item, priority=("someday" if kind == "someday"
                                           else "normal"), source=source)

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
        # no signal yet? goals seed it — the why layer sets today's focus
        kws = []
        for g in self.goals():
            kws += [k.strip() for k in g.get("match", "").split(",")
                    if k.strip()]
        return ", ".join(dict.fromkeys(kws))

    # ----- themed writing (reflection / brainstorm / someday, one topic) -----

    _THEME_RE = re.compile(
        r"=== THEME: (.+?) — (\d\d:\d\d)(?: \((\d+)m\))? ===\n"
        r"(.*?)\n=== END THEME ===", re.S)

    def _scan_themes(self):
        """{normalized_name: {"display": canonical case, "entries":
        [(date, time, mins_or_None, text), ...]}} across every day file,
        oldest first — a themed session is never a second data store, it's
        this file's own '=== THEME: x ===' blocks read back out, exactly
        like Search all days already does for free text."""
        out = {}
        try:
            names = sorted(os.listdir(self.diary_dir()))
        except OSError:
            return out
        for fn in names:
            if not fn.endswith(".txt"):
                continue
            date = fn[:-4]
            try:
                with open(os.path.join(self.diary_dir(), fn),
                          encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                continue
            for m in self._THEME_RE.finditer(text):
                name, hhmm, mins, body = m.groups()
                name = name.strip()
                key = " ".join(name.lower().split())
                rec = out.setdefault(key, {"display": {}, "entries": []})
                rec["display"][name] = rec["display"].get(name, 0) + 1
                rec["entries"].append((date, hhmm, int(mins) if mins else None,
                                       body.strip()))
        for rec in out.values():
            rec["display"] = max(rec["display"], key=rec["display"].get)
            rec["entries"].sort(key=lambda e: (e[0], e[1]))
        return out

    def _themed_writing(self, event=None):
        """Ctrl+T: pick or type a topic (existing ones autocomplete), then
        write in a distraction-free popup. Nothing forced, nothing on a
        timer or rollover — you summon this, it never summons you."""
        themes = self._scan_themes()
        names = sorted((r["display"] for r in themes.values()), key=str.lower)
        win = tk.Toplevel(self)
        win.title("Themed writing")
        win.resizable(False, False)
        win.grab_set()
        ttk.Label(win, text="Topic — existing or new, optional [Xm]:").grid(
            row=0, column=0, padx=8, pady=(8, 3))
        var = tk.StringVar()
        box = ttk.Combobox(win, textvariable=var, values=names, width=32)
        box.grid(row=1, column=0, padx=8, pady=3)
        box.focus_set()

        def go(event=None):
            raw = var.get().strip()
            if not raw:
                return
            win.destroy()
            self._open_theme_popup(raw)

        box.bind("<Return>", go)
        ttk.Button(win, text="Start", command=go).grid(
            row=2, column=0, sticky="e", padx=8, pady=(0, 8))

    def _open_theme_popup(self, raw):
        name, box_secs = self._parse_box(raw)
        if not name:
            return
        start = dt.datetime.now()
        p = tk.Toplevel(self)
        p.title(f"Themed writing — {name}")
        p.geometry("640x480")
        hdr = ttk.Frame(p)
        hdr.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(hdr, text=name, font=("Segoe UI", 13, "bold")).pack(side="left")
        timer_lbl = ttk.Label(hdr, text="0:00")
        timer_lbl.pack(side="right")
        txt = tk.Text(p, wrap="word", font=("Consolas", 11), undo=True)
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        txt.focus_set()
        alive = [True]

        def tick():
            if not alive[0]:
                return
            secs = int((dt.datetime.now() - start).total_seconds())
            m, s = divmod(secs, 60)
            over = box_secs and secs > box_secs
            timer_lbl.config(
                text=f"{m}:{s:02d}" + (f" / target {box_secs // 60}m" if box_secs else ""),
                foreground="#c03030" if over else "")
            p.after(1000, tick)

        def save(event=None):
            alive[0] = False
            body = txt.get("1.0", "end-1c").strip()
            if body:
                mins = max(1, round((dt.datetime.now() - start).total_seconds() / 60))
                self._append_text(f"=== THEME: {name} — {start:%H:%M} "
                                  f"({mins}m) ===\n{body}\n=== END THEME ===")
                self._auto_capture_bullets(body, f"theme: {name}")
                self.status.config(text=f"Saved {mins}m of themed writing — {name}")
            p.destroy()

        bar = ttk.Frame(p)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(bar, text="Save & close", command=save).pack(side="left")
        ttk.Label(bar, text="Ctrl+Enter to save · closing the window saves too",
                 foreground="#777777").pack(side="left", padx=8)
        p.bind("<Control-Return>", save)
        p.protocol("WM_DELETE_WINDOW", save)
        tick()

    def _browse_themes(self):
        """Read-only, across every day file: pick a topic, see its whole
        thread in order — 'what did I think about X, and how has that
        changed' answered by scrolling, not remembering."""
        themes = self._scan_themes()
        win = tk.Toplevel(self)
        win.title("Browse themes")
        win.geometry("620x480")
        top = ttk.Frame(win)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Topic:").pack(side="left")
        names = sorted(themes, key=lambda k: -len(themes[k]["entries"]))
        var = tk.StringVar(value=themes[names[0]]["display"] if names else "")
        box = ttk.Combobox(top, state="readonly", width=30,
                           values=[f"{themes[k]['display']} ({len(themes[k]['entries'])})"
                                   for k in names])
        if names:
            box.current(0)
        box.pack(side="left", padx=(6, 0))
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        def render(event=None):
            txt.config(state="normal")
            txt.delete("1.0", "end")
            if not names:
                txt.insert("1.0", "No themed sessions yet — Ctrl+T to start one.")
                txt.config(state="disabled")
                return
            key = names[box.current()]
            for date, hhmm, mins, body in themes[key]["entries"]:
                txt.insert("end", f"----- {date} {hhmm}"
                                  f"{f' ({mins}m)' if mins else ''} -----\n")
                txt.insert("end", body + "\n\n")
            txt.config(state="disabled")

        def copy():
            self.clipboard_clear()
            self.clipboard_append(txt.get("1.0", "end-1c"))
            self.status.config(text="Theme thread copied.")

        box.bind("<<ComboboxSelected>>", render)
        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(bar, text="Copy this thread", command=copy).pack(side="left")
        ttk.Button(bar, text="Continue writing on this topic",
                  command=lambda: (win.destroy(),
                                   self._open_theme_popup(
                                       themes[names[box.current()]]["display"]))
                  if names else None).pack(side="left", padx=6)
        render()

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

    def _shrink_last_break(self, date_iso, minutes):
        """'Actually 10 of those 23 break minutes were real work' — reduce
        the most recent break row on this date by `minutes` (dropping it
        entirely if it hits zero) so reclassifying part of a break as
        work doesn't double-count it. Approximate by design: adjusts the
        minutes total (what every view/total reads), not a pixel-perfect
        re-slice of the break's start/end — those only feed the timeline
        picture, not the numbers."""
        rows = read_rows()
        for i in range(len(rows) - 1, -1, -1):
            if rows[i][0] == date_iso and rows[i][1] == "break":
                try:
                    m = int(rows[i][4])
                except ValueError:
                    continue
                new_m = max(0, m - minutes)
                if new_m == 0:
                    del rows[i]
                else:
                    rows[i] = rows[i][:4] + [str(new_m)] + rows[i][5:]
                tmp = SESSIONS_CSV + ".tmp"
                with open(tmp, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f, delimiter=";")
                    w.writerow(CSV_HEADER)
                    w.writerows(rows)
                os.replace(tmp, SESSIONS_CSV)
                return True
        return False

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
        carve_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            win, variable=carve_var,
            text="Carved out of a break — actually working, not resting"
        ).grid(row=len(defaults), column=0, columnspan=2, sticky="w",
               padx=6, pady=(0, 3))

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
            carved = carve_var.get() and self._shrink_last_break(d.isoformat(), mins)
            if d == self.today:
                self._append_text(f"{start:%H:%M}-{end:%H:%M}  {task or '(no task)'} "
                                  f"({mins}m, added afterwards"
                                  + (", carved from break" if carved else "") + ")"
                                  + (f" - {note}" if note else ""))
            if task:
                self._remember_task(task)
            self._refresh_totals()
            win.destroy()
            self.status.config(text=f"Added {mins} min — {task or '(no task)'}"
                                    + (" (break reduced to match)" if carved else ""))

        ttk.Button(win, text="Save", command=save).grid(
            row=len(defaults) + 1, column=1, sticky="e", padx=6, pady=8)

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
        idx = day_index()
        d = first
        while d <= last:
            rec = idx.get(d.isoformat())
            if rec:
                work += rec["work"]
                brk += rec["brk"]
                for t, m in rec["tasks"].items():
                    tasks[t] = tasks.get(t, 0) + m
            d += dt.timedelta(days=1)

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

        lines = [" day        sleep  workout   steps   work   signal   en",
                 " " + "-" * 55]
        good, short = [], []      # (work_min, sig_pct) split at 7 h sleep
        for i in range(13, -1, -1):
            d = self.today - dt.timedelta(days=i)
            rec = hd.get(d.isoformat(), {})
            w, _b = day_totals(d.isoformat())
            sig, tot = self._day_signal(d)
            sl = rec.get("sleep_h")
            en = self._day_energy(d)
            pct = round(100 * sig / tot) if tot else None
            lines.append(
                f" {d:%a %d.%m}  "
                + (f"{fmt_sleep(sl):>6}" if sl else "     -")
                + (f"  {round(rec['workout_min']):>4}m" if rec.get("workout_min") else "     -")
                + (f"  {rec['steps']:>6}" if rec.get("steps") else "       -")
                + (f"  {w / 60:>5.2f}h" if w else "      -")
                + (f"  {pct:>4}%" if pct is not None else "      -")
                + (f"  {en}/5" if en else "    -"))
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

        days, breaks, tasks, sig, kws_by_day = {}, {}, {}, {}, {}
        idx, rows = day_index(), read_rows()
        d = first
        while d <= last:
            rec = idx.get(d.isoformat()) or {"work": 0, "brk": 0, "tasks": {}}
            days[d], breaks[d] = rec["work"], rec["brk"]
            kws_by_day[d] = self._signal_kws(d)
            sig[d] = (self._day_signal(d, kws_by_day[d], rows)[0]
                      if kws_by_day[d] else 0)
            for t, m in rec["tasks"].items():
                tasks[t] = tasks.get(t, 0) + m
            d += dt.timedelta(days=1)

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

    # ----- capacity planner -----

    DEFAULT_CAP = [6, 6, 6, 6, 6, 5, 3]     # realistic h per Mon..Sun

    def _capacity(self):
        cap = self.settings.get("capacity", self.DEFAULT_CAP)
        return [float(x) for x in cap] if len(cap) == 7 else self.DEFAULT_CAP

    def _busy_data(self):
        """Calendar busy hours per date, cached on the ics file's mtime."""
        path = self.settings.get("ics_path")
        if not path or not os.path.exists(path):
            return {}
        key = (path, os.path.getmtime(path), dt.date.today().isoformat())
        cache = getattr(self, "_busy_cache", None)
        if cache and cache[0] == key:
            return cache[1]
        # two weeks back so the balance/summary views see past meetings too
        data = parse_ics_busy(path, dt.date.today() - dt.timedelta(days=14),
                              dt.date.today() + dt.timedelta(days=90))
        self._busy_cache = (key, data)
        return data

    def _set_ics(self):
        p = filedialog.askopenfilename(
            parent=self, filetypes=[("Calendar", "*.ics")],
            title="Exported calendar (.ics) — busy time reduces capacity")
        if not p:
            return
        self.settings["ics_path"] = p
        save_settings(self.settings)
        self._busy_cache = None
        busy = self._busy_data()
        nxt14 = sum(h for iso, h in busy.items()
                    if iso <= (dt.date.today() + dt.timedelta(days=14)).isoformat())
        self.status.config(text=f"Calendar linked — {nxt14:.1f}h of meetings "
                                "in the next 14 days now reduce capacity.")

    def _day_capacity(self, d):
        """Net available hours on one date: weekday capacity minus
        calendar busy time; zero on off days."""
        if d.isoformat() in self.settings.get("off_dates", []):
            return 0.0
        return max(0.0, self._capacity()[d.weekday()]
                   - self._busy_data().get(d.isoformat(), 0.0))

    def _avail_hours(self, until):
        """Net capacity hours from today through `until` (inclusive)."""
        d, total = dt.date.today(), 0.0
        while d <= until:
            total += self._day_capacity(d)
            d += dt.timedelta(days=1)
        return total

    def _capacity_lines(self):
        """The honest verdict: available hours vs deadline demand."""
        lines, reqs, far = [], [], None
        busy = self._busy_data()
        if busy:
            nxt14 = sum(h for iso, h in busy.items()
                        if iso <= (dt.date.today()
                                   + dt.timedelta(days=14)).isoformat())
            if nxt14:
                lines.append(f" (calendar: {nxt14:.1f}h of meetings in the "
                             "next 14 days already subtracted)")
        for dl in self.deadlines():
            try:
                p = self._dl_progress(dl)
            except (ValueError, KeyError):
                continue
            if p["left"] < 0:
                continue
            if p.get("total_h"):
                req = p["remaining_h"]
            elif float(dl.get("target_h") or 0):
                req = float(dl["target_h"]) * (p["left"] + 1) / 7
            else:
                lines.append(f" {dl['name']}: no scope or weekly target set "
                             "— excluded from the math")
                continue
            avail = self._avail_hours(p["due"])
            slack = avail - req
            mark = "✓" if slack >= 0 else "⚠"
            lines.append(f" {mark} {dl['name']} — due {p['due']:%d.%m} "
                         f"({p['left']}d): needs {req:.1f}h, "
                         f"{avail:.1f}h available → slack {slack:+.1f}h")
            reqs.append(req)
            far = max(far or p["due"], p["due"])
        if len(reqs) > 1 and far:
            avail = self._avail_hours(far)
            slack = avail - sum(reqs)
            lines.append("")
            if slack >= 0:
                lines.append(f" ALL deadlines together: {sum(reqs):.1f}h needed, "
                             f"{avail:.1f}h available → {slack:.1f}h of real slack."
                             " The friend on Tuesday is fine.")
            else:
                lines.append(f" ⚠ ALL deadlines together: {sum(reqs):.1f}h needed "
                             f"but only {avail:.1f}h available → overbooked by "
                             f"{-slack:.1f}h. Cut scope or say no to something.")
        return lines

    def _capacity_win(self):
        win = tk.Toplevel(self)
        win.title("Week plan — your hours vs your deadlines")
        top = ttk.Frame(win)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Realistic work hours per day:").grid(
            row=0, column=0, columnspan=8, sticky="w")
        cap = self._capacity()
        entries = []
        for i, day in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            ttk.Label(top, text=day).grid(row=1, column=i, padx=3)
            e = ttk.Entry(top, width=4)
            e.insert(0, f"{cap[i]:g}")
            e.grid(row=2, column=i, padx=3)
            entries.append(e)
        ttk.Label(top, text="Off days (YYYY-MM-DD, comma-sep):").grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        off_e = ttk.Entry(top, width=40)
        off_e.insert(0, ", ".join(self.settings.get("off_dates", [])))
        off_e.grid(row=4, column=0, columnspan=7, sticky="we", pady=(0, 2))
        txt = tk.Text(win, wrap="word", font=("Consolas", 10), height=14,
                      width=76)
        txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        def render():
            txt.config(state="normal")
            txt.delete("1.0", "end")
            body = self._capacity_lines() or [
                " No deadlines set — Tools > Deadline countdowns…"]
            txt.insert("1.0", "\n".join(body))
            txt.config(state="disabled")

        def save():
            try:
                self.settings["capacity"] = [float(e.get().replace(",", "."))
                                             for e in entries]
                offs = []
                for s in off_e.get().split(","):
                    s = s.strip()
                    if s:
                        dt.date.fromisoformat(s)
                        offs.append(s)
                self.settings["off_dates"] = offs
            except ValueError:
                messagebox.showerror(APP_NAME, "Hours must be numbers and "
                                               "off days YYYY-MM-DD.",
                                     parent=win)
                return
            save_settings(self.settings)
            render()

        ttk.Button(top, text="Save", command=save).grid(row=2, column=7, padx=6)
        render()

    # ----- task backlog -----

    _PRI_ICON = {"signal": "●", "normal": "○", "someday": "‥"}
    _PRI_NEXT = {"normal": "signal", "signal": "someday", "someday": "normal"}

    def _tasks_win(self):
        """The library: everything that would otherwise live in a
        WhatsApp-to-self thread — todos, someday ideas, real backlog
        with estimates — in one scrollable, click-to-prioritize list.
        TODO:/SOMEDAY: bullets from the diary or a themed session land
        here on their own; this window is where you triage them."""
        win = tk.Toplevel(self)
        win.title("Tasks / Library")
        win.geometry("780x420")
        cols = ("pri", "task", "est", "actual", "goal", "source")
        heads = {"pri": "!", "task": "task", "est": "est", "actual": "actual",
                 "goal": "goal", "source": "from"}
        widths = {"pri": 26, "task": 260, "est": 55, "actual": 70,
                  "goal": 110, "source": 160}
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=heads[c])
            tree.column(c, width=widths[c], anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        tree.tag_configure("signal", foreground="#2e8b2e")
        tree.tag_configure("someday", foreground="#999999")

        def task_actual_h(name, added):
            t, tot = name.strip().lower(), 0
            for r in read_rows():
                if (r[1] != "break" and r[5].strip().lower() == t
                        and r[0] >= added):
                    try:
                        tot += int(r[4])
                    except ValueError:
                        pass
            return tot / 60

        def refresh(keep_selection=None):
            sel = keep_selection if keep_selection is not None else tree.selection()
            tree.delete(*tree.get_children())
            for i, t in enumerate(self.settings.get("tasks", [])):
                pri = t.get("priority", "normal")
                est = t.get("est_h")
                tree.insert("", "end", iid=str(i), tags=(pri,), values=(
                    self._PRI_ICON.get(pri, "○"), t["name"],
                    f"{est:g}h" if est else "—",
                    f"{task_actual_h(t['name'], t['added']):.2f}h",
                    t.get("goal") or "—", t.get("source") or "—"))
            # rebuilding the tree drops selection unless we restore it — a
            # priority click on row 2 must not silently un-pick row 2
            keep = [iid for iid in sel if tree.exists(iid)]
            if keep:
                tree.selection_set(keep)

        def picked():
            sel = tree.selection()
            return int(sel[0]) if sel else None

        def toggle_priority(event):
            row, col = tree.identify_row(event.y), tree.identify_column(event.x)
            if not row or col != "#1":
                return
            i = int(row)
            cur = self.settings["tasks"][i].get("priority", "normal")
            self.settings["tasks"][i]["priority"] = self._PRI_NEXT[cur]
            save_settings(self.settings)
            refresh(keep_selection=[row])

        tree.bind("<Button-1>", toggle_priority)

        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=(0, 4))
        entry = ttk.Entry(bar)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Label(bar, text="est h:").pack(side="left", padx=(6, 2))
        est_entry = ttk.Entry(bar, width=5)
        est_entry.pack(side="left")
        pri_var = tk.StringVar(value="normal")
        ttk.Combobox(bar, textvariable=pri_var, state="readonly", width=8,
                    values=["normal", "signal", "someday"]).pack(
                        side="left", padx=(4, 0))
        goal_var = tk.StringVar()
        goal_box = ttk.Combobox(bar, textvariable=goal_var, state="readonly",
                                width=14,
                                values=[""] + [g["name"] for g in self.goals()])
        goal_box.pack(side="left", padx=(4, 0))

        def add(event=None):
            raw = entry.get().strip()
            if not raw:
                return
            # a plain hours field is the primary path; [2h] typed straight
            # into the name still works too, for muscle memory
            name, box = self._parse_box(raw)
            est_h = 0
            if est_entry.get().strip():
                try:
                    est_h = float(est_entry.get().strip().replace(",", "."))
                except ValueError:
                    messagebox.showerror(APP_NAME, "est h must be a number.",
                                         parent=win)
                    return
            elif box:
                est_h = box / 3600
            self._add_task(name, est_h=est_h, priority=pri_var.get(),
                           goal=goal_var.get() or None, source="added manually")
            entry.delete(0, "end")
            est_entry.delete(0, "end")
            refresh()

        def start():
            i = picked()
            if i is None:
                return
            self.task_var.set(self.settings["tasks"][i]["name"])
            win.destroy()
            self._go()

        def done():
            i = picked()
            if i is None:
                return
            t = self.settings["tasks"].pop(i)
            save_settings(self.settings)
            line = f"--- Done: {t['name']}"
            if t.get("est_h"):
                line += (f" (est {t['est_h']:g}h, actual "
                         f"{task_actual_h(t['name'], t['added']):.2f}h)")
            self._append_text(line)
            refresh()

        def delete():
            i = picked()
            if i is None:
                return
            del self.settings["tasks"][i]
            save_settings(self.settings)
            refresh()

        entry.bind("<Return>", add)
        for label, cmd in (("Add", add), ("Start ▶", start),
                           ("Done ✓", done), ("Delete", delete)):
            ttk.Button(bar, text=label, command=cmd).pack(side="left", padx=(4, 0))
        hint = ("Click ! to cycle priority (● signal / ○ normal / ‥ someday). "
               "TODO:/SOMEDAY: bullets anywhere (diary, themed writing) land "
               "here on their own.")
        ef = self._estimate_factor()
        if ef:
            hint += f"  Your history: actuals run ×{ef[0]:.1f} your estimates."
        ttk.Label(win, text=hint, foreground="#777777",
                  wraplength=760).pack(anchor="w", padx=8, pady=(0, 6))
        refresh()

    def _estimate_factor(self):
        """(median actual/estimate ratio, sample count) from '--- Done: x
        (est Yh, actual Zh)' lines across all day files. None until 3+
        samples exist."""
        pat = re.compile(r"--- Done: .*\(est ([0-9.]+)h, actual ([0-9.]+)h\)")
        ratios = []
        try:
            names = os.listdir(self.diary_dir())
        except OSError:
            return None
        for fn in names:
            if not fn.endswith(".txt"):
                continue
            try:
                with open(os.path.join(self.diary_dir(), fn),
                          encoding="utf-8") as f:
                    found = pat.findall(f.read())
            except OSError:
                continue
            for e, a in found:
                e, a = float(e), float(a)
                if e > 0 and a > 0:
                    ratios.append(a / e)
        if len(ratios) < 3:
            return None
        ratios.sort()
        return ratios[len(ratios) // 2], len(ratios)

    # ----- deadline burn-down -----

    def _burndown_series(self, dl, days_back=14):
        """(dates, ideal_h, actual_h). With a total-hours scope the ideal
        line runs start->due covering the scope; otherwise it's the linear
        weekly-target pace over the last `days_back` days. Actual stops
        at today. Reads day_index() + task_matches() — the same cached
        substrate and match predicate as everything else — rather than
        its own csv scan; matched_minutes() itself only returns a range
        total, not a per-day running sum, so this stays one call-site
        below full convergence (see HANDOFF.md)."""
        end = dt.date.fromisoformat(dl["date"])
        total = float(dl.get("total_h") or 0)
        start = None
        if total and dl.get("start"):
            try:
                start = dt.date.fromisoformat(dl["start"])
            except ValueError:
                pass
        if start is None:
            start = self.today - dt.timedelta(days=days_back - 1)
        kws = self._match_kws(dl.get("match", ""))
        idx = day_index()
        dates, ideal, actual = [], [], []
        cum = 0
        d = start
        span = max((end - start).days + 1, 1)
        rate = float(dl.get("target_h") or 0) / 7
        while d <= max(end, self.today):
            dates.append(d)
            i = (d - start).days + 1
            ideal.append(total * min(i, span) / span if total else rate * i)
            if d <= self.today:
                rec = idx.get(d.isoformat())
                if rec:
                    cum += (sum(m for t, m in rec["tasks"].items()
                               if task_matches(t, kws)) if kws else rec["work"])
                actual.append(cum / 60)
            d += dt.timedelta(days=1)
        return dates, ideal, actual

    def _burndown(self):
        dls = [d for d in self.deadlines()
               if float(d.get("target_h") or 0) or float(d.get("total_h") or 0)]
        if not dls:
            messagebox.showinfo(APP_NAME, "Set a deadline with a total-hours "
                                          "scope or weekly target first (Tools).")
            return
        if len(dls) == 1:
            self._draw_burndown(dls[0])
            return
        win = tk.Toplevel(self)
        win.title("Burn-down")
        win.resizable(False, False)
        win.grab_set()
        ttk.Label(win, text="Which deadline?").grid(row=0, column=0,
                                                    padx=8, pady=(8, 3))
        var = tk.StringVar(value=dls[0]["name"])
        ttk.Combobox(win, textvariable=var, state="readonly",
                     values=[d["name"] for d in dls]).grid(row=1, column=0,
                                                           padx=8, pady=3)

        def go():
            win.destroy()
            self._draw_burndown(next(d for d in dls if d["name"] == var.get()))

        ttk.Button(win, text="Show", command=go).grid(row=2, column=0,
                                                      sticky="e", padx=8, pady=8)

    def _draw_burndown(self, dl):
        try:
            dates, ideal, actual = self._burndown_series(dl)
            p = self._dl_progress(dl)
        except ValueError:
            messagebox.showerror(APP_NAME, f"Bad date on '{dl['name']}'.")
            return
        title = f"{dl['name']} — {p['left']}d left"
        if p.get("total_h"):
            title += (f" · {p['done_h']:.1f}/{p['total_h']:g}h"
                      f" · needs {p['needed_per_day']:.1f}h/day")
        elif float(dl.get("target_h") or 0):
            title += f" · target {dl['target_h']:g}h/wk"
        why = self._goal_why(dl.get("goal"))
        if why:
            title += f" — {why}"
        win = tk.Toplevel(self)
        win.title(title)
        W, H, PAD = 560, 320, 40
        cv = tk.Canvas(win, width=W, height=H, background="white",
                       highlightthickness=0)
        cv.pack(padx=8, pady=8)
        mx = max(ideal[-1], (actual[-1] if actual else 0), 1)
        n = len(dates)

        def xy(i, v):
            return (PAD + (W - 2 * PAD) * i / max(n - 1, 1),
                    H - PAD - (H - 2 * PAD) * v / mx)

        cv.create_line(PAD, H - PAD, W - PAD, H - PAD)
        cv.create_line(PAD, PAD, PAD, H - PAD)
        for pts, color, wdt in (
                ([xy(i, v) for i, v in enumerate(ideal)], "#999999", 1),
                ([xy(i, v) for i, v in enumerate(actual)], "#4a6fa5", 2)):
            for a, b in zip(pts, pts[1:]):
                cv.create_line(*a, *b, fill=color, width=wdt)
        # the gap, in red, at today
        i_today = len(actual) - 1
        if i_today >= 0:
            gap = ideal[i_today] - actual[i_today]
            xa, ya = xy(i_today, actual[i_today])
            _, yi = xy(i_today, ideal[i_today])
            if gap > 0.1:
                cv.create_line(xa, ya, xa, yi, fill="#c03030", width=2)
                cv.create_text(min(xa + 6, W - 60), (ya + yi) / 2, anchor="w",
                               text=f"-{gap:.1f}h behind", fill="#c03030",
                               font=("Segoe UI", 9, "bold"))
            else:
                cv.create_text(xa, ya - 12, text="on pace ✓", fill="#2e8b2e",
                               font=("Segoe UI", 9, "bold"))
        for i in (0, n - 1):
            cv.create_text(*xy(i, 0)[:1], H - PAD + 12,
                           text=f"{dates[i]:%d.%m}", font=("Segoe UI", 8))
        cv.create_text(PAD - 4, PAD, text=f"{mx:.0f}h", anchor="e",
                       font=("Segoe UI", 8))
        cv.create_text(W - PAD, PAD, anchor="e", font=("Segoe UI", 8),
                       fill="#777777",
                       text="grey = target pace · blue = actual")

    # ----- month heatmap -----

    HEAT = ["#ebedf0", "#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#215a8f"]

    def _heatmap(self):
        per = {}
        for r in read_rows():
            if r[1] == "break":
                continue
            try:
                per[r[0]] = per.get(r[0], 0) + int(r[4])
            except ValueError:
                continue
        weeks, cell, pad = 16, 20, 34
        this_mon = self.today - dt.timedelta(days=self.today.weekday())
        start_mon = this_mon - dt.timedelta(weeks=weeks - 1)
        W, H = pad * 2 + weeks * cell, pad + 7 * cell + 30
        win = tk.Toplevel(self)
        win.title("Daily hours — last 16 weeks")
        cv = tk.Canvas(win, width=W, height=H, background="white",
                       highlightthickness=0)
        cv.pack(padx=8, pady=8)
        seen_month = None
        for w in range(weeks):
            for wd in range(7):
                d = start_mon + dt.timedelta(weeks=w, days=wd)
                if d > self.today:
                    continue
                h = per.get(d.isoformat(), 0) / 60
                shade = next(i for i, lim in
                             enumerate((0.01, 2, 4, 6, 8, 99)) if h < lim)
                x, y = pad + w * cell, pad + wd * cell
                cv.create_rectangle(x, y, x + cell - 3, y + cell - 3,
                                    fill=self.HEAT[shade], outline="")
                if wd == 0 and d.strftime("%b") != seen_month:
                    seen_month = d.strftime("%b")
                    cv.create_text(x, pad - 8, text=seen_month, anchor="w",
                                   font=("Segoe UI", 8), fill="#666666")
        for wd, lbl in ((0, "Mon"), (3, "Thu"), (6, "Sun")):
            cv.create_text(pad - 6, pad + wd * cell + cell / 2 - 1,
                           text=lbl, anchor="e", font=("Segoe UI", 7),
                           fill="#888888")
        cv.create_text(pad, H - 12, anchor="w", font=("Segoe UI", 8),
                       fill="#666666",
                       text="shade steps: 0 · <2h · <4h · <6h · <8h · 8h+")

    # ----- the life record + dashboard (the consolidation) -----

    def _sleep_h(self, iso):
        """Sleep hours for one date: the right-click override wins over the
        health import; None when neither knows."""
        over = self.settings.get("sleep_over", {}).get(iso)
        if over:
            try:
                bh, bm = map(int, over[0].split(":"))
                wh, wm = map(int, over[1].split(":"))
                return ((wh * 60 + wm - bh * 60 - bm) % 1440 or 1440) / 60
            except ValueError:
                pass
        return self._health_data().get(iso, {}).get("sleep_h")

    def _life_day(self, d, signal=True):
        """Everything the app knows about one date, merged into ONE dict —
        the unit every consolidated view consumes: timer minutes from the
        csv, signal minutes per that day's own SIGNAL line, sleep/workout/
        steps from the health import, meeting hours from the calendar, net
        capacity from the week plan. A future data source (mood, money,
        screen time) becomes a new key here — not a new parser per window."""
        iso = d.isoformat()
        base = day_index().get(iso) or {"work": 0, "brk": 0, "tasks": {}}
        rec = {"date": d, "work": base["work"], "brk": base["brk"],
               "tasks": dict(base["tasks"]),
               "signal": self._day_signal(d)[0] if signal else None,
               "energy": self._day_energy(d),
               "sleep_h": self._sleep_h(iso),
               "workout_min": self._health_data().get(iso, {}).get("workout_min"),
               "steps": self._health_data().get(iso, {}).get("steps"),
               "busy_h": self._busy_data().get(iso, 0.0),
               "capacity_h": self._day_capacity(d)}
        return rec

    def _dashboard(self, event=None):
        """One window instead of nine: today, the week, every deadline and
        the cross-domain insights, plus one consolidated AI export."""
        self._save_diary()
        win = tk.Toplevel(self)
        win.title("Life dashboard")
        win.geometry("700x820")
        win.minsize(680, 500)
        cv = tk.Canvas(win, width=660, height=150, background="white",
                       highlightthickness=0)
        cv.pack(padx=8, pady=(8, 4))
        sleep_cv = tk.Canvas(win, width=660, height=80, background="white",
                             highlightthickness=0)
        sleep_cv.pack(padx=8, pady=(0, 4))
        txt_frame = ttk.Frame(win)
        txt_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        txt_scroll = ttk.Scrollbar(txt_frame, orient="vertical")
        txt = tk.Text(txt_frame, wrap="word", font=("Consolas", 10),
                      width=88, height=18, yscrollcommand=txt_scroll.set)
        txt_scroll.config(command=txt.yview)
        txt_scroll.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.tag_configure("h", font=("Consolas", 10, "bold"))
        txt.tag_configure("warn", foreground="#c03030")
        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        shown = [""]

        def render():
            monday = self.today - dt.timedelta(days=self.today.weekday())
            week = [self._life_day(monday + dt.timedelta(days=i))
                    for i in range(7)]
            self._draw_week_bars(cv, week)
            self._draw_sleep_bars(sleep_cv)
            lines = self._dashboard_lines(week)
            shown[0] = "\n".join(lines)
            txt.config(state="normal")
            txt.delete("1.0", "end")
            for ln in lines:
                tag = ("h" if ln and not ln.startswith(" ") else
                       "warn" if "⚠" in ln else ())
                txt.insert("end", ln + "\n", tag)
            txt.config(state="disabled")

        def copy():
            self.clipboard_clear()
            self.clipboard_append(
                shown[0] + "\n\nAsk: what slipped, what pattern am I not "
                "seeing, what should next week look like?")
            self.status.config(text="Dashboard copied — paste into Claude.")

        ttk.Button(bar, text="Copy for AI review", command=copy).pack(side="left")
        ttk.Button(bar, text="Refresh", command=render).pack(side="left", padx=6)
        render()

    def _dashboard_lines(self, week):
        t = week[self.today.weekday()]
        w = t["work"]
        if self.state == "working" and self.work_start:
            w += (dt.datetime.now() - self.work_start).total_seconds() / 60
        lines = [f"TODAY — {self.today:%A %d.%m.%Y}"]
        line = f"  {w / 60:.2f}h work"
        if t["brk"]:
            line += f" · {t['brk'] / 60:.2f}h breaks"
        if t["signal"] and w:
            line += f" · signal {round(100 * t['signal'] / w)}%"
        target = self.settings.get("target_min", 0)
        if target:
            line += f" · target {min(100, round(100 * w / target))}%"
        lines.append(line)
        plan = self._plan_line()
        if plan:
            lines.append("  " + plan)
        hl = []
        if t["energy"]:
            hl.append(f"energy {t['energy']}/5")
        if t["sleep_h"]:
            hl.append(f"slept {fmt_sleep(t['sleep_h'])}")
            past = [self._sleep_h((self.today - dt.timedelta(days=i)).isoformat())
                    for i in range(1, 8)]
            past = [s for s in past if s]
            if past:
                hl.append(f"7-day avg {fmt_sleep(sum(past) / len(past))}")
        if t["workout_min"]:
            hl.append(f"workout {round(t['workout_min'])}m")
        if t["busy_h"]:
            hl.append(f"{t['busy_h']:.1f}h of meetings today")
        if hl:
            lines.append("  " + " · ".join(hl))

        lines += ["", f"THIS WEEK — W{self.today.isocalendar().week}"]
        idx = day_index()
        wk = sum(r["work"] for r in week)
        brk = sum(r["brk"] for r in week)
        lw = sum((idx.get((week[0]["date"] - dt.timedelta(days=7)
                           + dt.timedelta(days=i)).isoformat())
                  or {"work": 0})["work"]
                 for i in range(self.today.weekday() + 1))
        line = f"  {wk / 60:.2f}h tracked"
        if lw:
            line += (f" · last week at this point {lw / 60:.2f}h"
                     f" ({(wk - lw) / 60:+.1f}h)")
        if wk + brk:
            line += f" · breaks {round(100 * brk / (wk + brk))}% of tracked time"
        lines.append(line)
        sig = sum(r["signal"] or 0 for r in week)
        if sig and wk:
            lines.append(f"  signal {sig / 60:.2f}h — {round(100 * sig / wk)}% "
                         "of the week went to what you said matters")
        tasks = {}
        for r in week:
            for k, m in r["tasks"].items():
                tasks[k] = tasks.get(k, 0) + m
        if tasks:
            top = sorted(tasks.items(), key=lambda x: -x[1])[:6]
            lines.append("  top: " + " · ".join(
                f"{k} {m / 60:.1f}h" for k, m in top))

        gs = self.goals()
        if gs:
            lines += ["", "GOALS — where the hours actually point"]
            monday = week[0]["date"]
            for g in gs:
                m_wk = self._goal_minutes(g, monday, self.today)
                m4 = self._goal_minutes(
                    g, self.today - dt.timedelta(days=27), self.today)
                m14 = self._goal_minutes(
                    g, self.today - dt.timedelta(days=13), self.today)
                tgt = float(g.get("target_h") or 0)
                expected = tgt * (self.today.weekday() + 1) / 7
                mark = "⚠" if (m14 == 0 or
                               (tgt and m_wk / 60 < 0.75 * expected)) else "·"
                seg = f"  {mark} {g['name']}"
                if g.get("why"):
                    seg += f" ({g['why']})"
                seg += (f": {m_wk / 60:.1f}h this wk"
                        f" · 4-wk avg {m4 / 4 / 60:.1f}h/wk")
                if tgt:
                    seg += f" · ambition {tgt:g}h/wk"
                if wk:
                    seg += f" · {round(100 * m_wk / wk)}% of tracked"
                if m14 == 0:
                    seg += " — nothing in 14 days; still a goal?"
                lines.append(seg)

        # the whole life, not just the tracked slice: account the waking week
        n = self.today.weekday() + 1
        sofar = week[:n]
        waking, assumed = 0.0, False
        for r in sofar:
            if r["sleep_h"]:
                waking += 24 - r["sleep_h"]
            else:
                waking += 16
                assumed = True
        work_h, brk_h = wk / 60, brk / 60
        meet_h = sum(r["busy_h"] for r in sofar)
        wo_h = sum(r["workout_min"] or 0 for r in sofar) / 60
        lines += ["", f"LIFE BALANCE — {n} day(s), ~{waking:.0f} waking hours"
                      + (" (8h sleep assumed where unknown)" if assumed else "")]
        lines.append(f"  tracked work {work_h:.1f}h "
                     f"({round(100 * work_h / waking) if waking else 0}%)"
                     f" · breaks {brk_h:.1f}h · meetings {meet_h:.1f}h"
                     f" · workout {wo_h:.1f}h")
        cats = {}
        for r in sofar:
            for k, m in r["tasks"].items():
                c = k.split(":")[0].strip() if ":" in k else "(uncategorised)"
                cats[c] = cats.get(c, 0) + m
        if cats:
            lines.append("  by project: " + " · ".join(
                f"{c} {m / 60:.1f}h" for c, m in
                sorted(cats.items(), key=lambda x: -x[1])[:4]))
        other = waking - work_h - brk_h - meet_h - wo_h
        if other > 0:
            lines.append(f"  unaccounted ~{other:.0f}h — meals, commute, "
                         "people, scroll. The diary knows; the timer doesn't.")

        dls = self.deadlines()
        if dls:
            lines += ["", "DEADLINES"]
            for dl in dls:
                try:
                    p = self._dl_progress(dl)
                except (ValueError, KeyError):
                    continue
                seg = (f"  {'⚠' if p.get('behind') else '·'} {dl['name']} — "
                       f"due {p['due']:%d.%m} ({p['left']}d)")
                if p.get("total_h"):
                    seg += (f": {p['done_h']:.1f}/{p['total_h']:g}h done"
                            f" · needs {p['needed_per_day']:.1f}h/day now")
                else:
                    seg += f": {p['done_h']:.1f}h done"
                why = self._goal_why(dl.get("goal"))
                if why:
                    seg += f"  ({why})"
                lines.append(seg)
            lines += [" " + s for s in self._capacity_lines()]

        lines += ["", "INSIGHTS — your last 60 days, cross-referenced"]
        ins = self._insight_lines()
        if ins:
            lines += ["  · " + s for s in ins]
        else:
            lines.append("  (still collecting — these appear as sleep, "
                         "estimate and streak history builds up)")
        return lines

    def _insight_lines(self, days=60):
        """Rule-based findings that each connect two data sources the app
        already collects. Every line is your own history — it only speaks
        when there are enough samples to mean something."""
        out = []
        idx = day_index()
        # sleep x output — the reason the health import exists.
        # Only days you actually tracked work count: a weekend with 8h
        # sleep and 0 tracked hours isn't evidence sleep hurt your output,
        # it's evidence you didn't open the app — mixing that in silently
        # drags the averages toward zero and the insight into nonsense.
        good, short = [], []
        for i in range(1, days + 1):            # today isn't finished yet
            d = self.today - dt.timedelta(days=i)
            sl = self._sleep_h(d.isoformat())
            w = (idx.get(d.isoformat()) or {"work": 0})["work"]
            if sl and w > 0:
                (good if sl >= 7 else short).append(w)
        if len(good) >= 3 and len(short) >= 3:
            g = sum(good) / len(good) / 60
            s = sum(short) / len(short) / 60
            out.append(f"on days you tracked work: after ≥7h sleep you "
                       f"averaged {g:.1f}h of work ({len(good)} such days) "
                       f"vs {s:.1f}h after <7h sleep ({len(short)} days) "
                       f"— a {g - s:+.1f}h/day difference")
        # energy x everything — the 1-5 you type into the header. Same
        # active-days-only filter as above, same reason.
        ehi, elo, en_sl = [], [], []
        for i in range(1, days + 1):
            d = self.today - dt.timedelta(days=i)
            e = self._day_energy(d)
            if not e:
                continue
            w = (idx.get(d.isoformat()) or {"work": 0})["work"]
            if e >= 4 and w > 0:
                ehi.append(w)
            elif e <= 2 and w > 0:
                elo.append(w)
            sl = self._sleep_h(d.isoformat())
            if sl:
                en_sl.append((sl, e))
        if len(ehi) >= 3 and len(elo) >= 3:
            out.append(f"on days you tracked work: energy ≥4 averaged "
                       f"{sum(ehi) / len(ehi) / 60:.1f}h of work "
                       f"({len(ehi)} days) vs {sum(elo) / len(elo) / 60:.1f}h "
                       f"on energy ≤2 days ({len(elo)} days) — protect what "
                       "charges you, it IS the productivity")
        g_e = [e for sl, e in en_sl if sl >= 7]
        s_e = [e for sl, e in en_sl if sl < 7]
        if len(g_e) >= 3 and len(s_e) >= 3:
            out.append(f"energy after ≥7h sleep: {sum(g_e) / len(g_e):.1f}/5 · "
                       f"after <7h: {sum(s_e) / len(s_e):.1f}/5 — your own "
                       "body, measured")
        # deep hours — when the work actually happens
        by_hour, tot = [0] * 24, 0
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        for r in read_rows():
            if r[1] == "break" or r[0] < cutoff:
                continue
            try:
                h = int(r[2].split(":")[0]) % 24
                m = int(r[4])
            except (ValueError, IndexError):
                continue
            by_hour[h] += m
            tot += m
        if tot >= 20 * 60:
            best, h0 = max((sum(by_hour[h:h + 3]), h) for h in range(22))
            out.append(f"deep hours {h0:02d}–{h0 + 3:02d}: "
                       f"{round(100 * best / tot)}% of all your work lands "
                       "there — guard that window, schedule meetings outside it")
        # focus block length — fragmentation trend
        monday = self.today - dt.timedelta(days=self.today.weekday())
        prev_lo = monday - dt.timedelta(days=21)
        cur, prev = [], []
        for r in read_rows():
            if r[1] == "break":
                continue
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[4])
            except ValueError:
                continue
            if d >= monday:
                cur.append(m)
            elif d >= prev_lo:
                prev.append(m)
        if len(cur) >= 5 and len(prev) >= 10:
            ca, pa = sum(cur) / len(cur), sum(prev) / len(prev)
            verdict = ("more fragmented — batch the interruptions"
                       if ca < 0.85 * pa else
                       "deeper focus" if ca > 1.15 * pa else "steady")
            out.append(f"average unbroken work block {ca:.0f}m this week vs "
                       f"{pa:.0f}m the 3 weeks before — {verdict}")
        # estimate honesty
        ef = self._estimate_factor()
        if ef:
            out.append(f"estimates: actuals run ×{ef[0]:.1f} across "
                       f"{ef[1]} finished tasks — read every [2h] as "
                       f"{2 * ef[0]:.1f}h when planning")
        # streaks
        def active(d):
            return (idx.get(d.isoformat()) or {"work": 0})["work"] >= 30
        d = self.today if active(self.today) else self.today - dt.timedelta(days=1)
        run = 0
        while active(d):
            run += 1
            d -= dt.timedelta(days=1)
        best = cur_s = 0
        for i in range(112):
            if active(self.today - dt.timedelta(days=111 - i)):
                cur_s += 1
                best = max(best, cur_s)
            else:
                cur_s = 0
        if best:
            out.append(f"streak: {run} active day(s) (≥30m) · best in "
                       f"16 weeks: {best}")
        return out

    def _draw_week_bars(self, cv, week):
        """Mon–Sun bars: blue work with the green signal share inside,
        last week's same weekday as the grey ghost behind, the week-plan
        capacity as a red dashed tick."""
        cv.delete("all")
        W, H = int(cv["width"]), int(cv["height"])
        pad = 30
        idx = day_index()
        ghosts = [(idx.get((r["date"] - dt.timedelta(days=7)).isoformat())
                   or {"work": 0})["work"] for r in week]
        mx = max([r["work"] for r in week] + ghosts
                 + [int(r["capacity_h"] * 60) for r in week] + [60])
        bw = (W - 2 * pad) / 7

        def y(m):
            return H - 22 - (H - 44) * m / mx

        for i, r in enumerate(week):
            x0 = pad + i * bw
            if ghosts[i]:
                cv.create_rectangle(x0 + 6, y(ghosts[i]), x0 + bw - 6, H - 22,
                                    fill="#e4e7ec", outline="")
            if r["date"] <= self.today and r["work"]:
                cv.create_rectangle(x0 + 12, y(r["work"]), x0 + bw - 12,
                                    H - 22, fill=self.TL_WORK, outline="")
                if r["signal"]:
                    cv.create_rectangle(x0 + 12, y(r["signal"]), x0 + bw - 12,
                                        H - 22, fill=self.TL_SIGNAL, outline="")
                cv.create_text(x0 + bw / 2, y(r["work"]) - 8,
                               text=f"{r['work'] / 60:.1f}",
                               font=("Segoe UI", 7), fill="#555555")
            cap = int(r["capacity_h"] * 60)
            if cap:
                cv.create_line(x0 + 4, y(cap), x0 + bw - 4, y(cap),
                               fill="#c03030", dash=(2, 2))
            cv.create_text(x0 + bw / 2, H - 12, text=r["date"].strftime("%a"),
                           font=("Segoe UI", 8),
                           fill="#000000" if r["date"] == self.today
                           else "#666666")
        cv.create_line(pad, H - 22, W - pad, H - 22)
        cv.create_text(pad, 10, anchor="w", font=("Segoe UI", 8),
                       fill="#777777",
                       text="blue = work · green = signal share · grey = "
                            "last week · red dash = planned capacity")

    def _draw_sleep_bars(self, cv, days=14):
        """Last N nights: sleep hours as bars (dark = >=7h, amber = <7h),
        a dot on top when a workout was logged that day — the two body
        signals merged into one glance, since a graph reads faster than
        any sentence about them ever will."""
        cv.delete("all")
        W, H, pad = int(cv["width"]), int(cv["height"]), 26
        dates = [self.today - dt.timedelta(days=i) for i in range(days - 1, -1, -1)]
        vals = [(self._sleep_h(d.isoformat()),
                 self._health_data().get(d.isoformat(), {}).get("workout_min"))
                for d in dates]
        mx = max([v[0] or 0 for v in vals] + [8])
        bw = (W - 2 * pad) / days

        def y(h):
            return H - 16 - (H - 32) * h / mx

        ref = y(7)
        cv.create_line(pad, ref, W - pad, ref, fill="#c9c9c9", dash=(2, 2))
        cv.create_text(W - pad, ref - 8, anchor="e", text="7h",
                       font=("Segoe UI", 7), fill="#999999")
        for i, (d, (sl, wk)) in enumerate(zip(dates, vals)):
            x0 = pad + i * bw + 3
            x1 = pad + (i + 1) * bw - 3
            if sl:
                cv.create_rectangle(x0, y(sl), x1, H - 16,
                                    fill=self.TL_SLEEP if sl >= 7 else "#c98a3a",
                                    outline="")
            if wk and wk >= self.WORKOUT_DOT_MIN:
                cv.create_oval((x0 + x1) / 2 - 3, 4, (x0 + x1) / 2 + 3, 10,
                               fill="#3a8a3a", outline="")
            if d == self.today:
                cv.create_text((x0 + x1) / 2, H - 6, text="today",
                               font=("Segoe UI", 7), fill="#000000")
        cv.create_line(pad, H - 16, W - pad, H - 16)
        cv.create_text(pad, 10, anchor="w", font=("Segoe UI", 8),
                       fill="#777777",
                       text="sleep, last 14 nights — dark = ≥7h · amber = "
                            "<7h · green dot = workout logged that day")

    def _export_life_json(self):
        """The whole life record — every day the app knows anything about,
        as plain JSON. The data outlives the app: any future tool (or the
        next version of this platform) starts from this file."""
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".json",
            initialfile=f"life_{dt.date.today()}.json",
            filetypes=[("JSON", "*.json")],
            title="Export the full life record")
        if not path:
            return
        self._save_diary()
        isos = set(day_index()) | set(self._health_data())
        try:
            isos |= {fn[:-4] for fn in os.listdir(self.diary_dir())
                     if fn.endswith(".txt")}
        except OSError:
            pass
        days = {}
        for iso in sorted(isos):
            try:
                d = dt.date.fromisoformat(iso)
            except ValueError:
                continue
            rec = self._life_day(d)
            del rec["date"]
            try:
                with open(self.diary_path(d), encoding="utf-8") as f:
                    rec["diary"] = f.read()
            except OSError:
                pass
            days[iso] = rec
        out = {"exported": dt.datetime.now().isoformat(timespec="seconds"),
               "app": "TimerDiary v6.2",
               "goals": self.goals(),
               "deadlines": self.deadlines(),
               "capacity_per_weekday": self._capacity(),
               "days": days}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        self.status.config(text=f"Life record exported — {len(days)} day(s) "
                                f"→ {os.path.basename(path)}. Plain JSON, "
                                "yours forever.")

    # ----- data doctor (keep the substrate clean) -----

    def _doctor_scan(self):
        """One pass over the csv: task-name spelling variants, junk rows,
        exact duplicates, overlapping work intervals. Returns
        (report_lines, rename_map, junk_count, dup_count)."""
        rows = read_rows()
        by_key, by_day = {}, {}
        seen, junk, dups, overlaps = set(), 0, 0, 0
        for r in rows:
            tup = tuple(r)
            if tup in seen:
                dups += 1
                continue
            seen.add(tup)
            try:
                dt.date.fromisoformat(r[0])
                ok = int(r[4]) > 0
            except ValueError:
                ok = False
            if not ok:
                junk += 1
                continue
            t = r[5].strip()
            if t:
                key = " ".join(t.lower().split())
                sp = by_key.setdefault(key, {})
                sp[t] = sp.get(t, 0) + int(r[4])
            if r[1] != "break":
                by_day.setdefault(r[0], []).append(r)
        for rs in by_day.values():
            ivs = []
            for r in rs:
                try:
                    sh, sm = map(int, r[2].split(":")[:2])
                    eh, em = map(int, r[3].split(":")[:2])
                except (ValueError, IndexError):
                    continue
                a, b = sh * 60 + sm, eh * 60 + em
                if b < a:
                    b += 1440              # crossed midnight
                ivs.append((a, b))
            ivs.sort()
            overlaps += sum(1 for p, q in zip(ivs, ivs[1:]) if q[0] < p[1] - 1)
        rename = {}
        for sp in by_key.values():
            if len(sp) > 1:
                canon = max(sp, key=sp.get)
                for s in sp:
                    if s != canon:
                        rename[s] = canon
        dates = sorted(r[0] for r in rows if len(r[0]) == 10)
        lines = [f"{len(rows)} rows"
                 + (f", {dates[0]} … {dates[-1]}" if dates else "")
                 + f", {len(by_key)} distinct tasks", ""]
        if rename:
            lines.append("Task spelling variants (Clean merges each into "
                         "the most-used spelling):")
            for sp in by_key.values():
                if len(sp) > 1:
                    canon = max(sp, key=sp.get)
                    lines.append(f"  → '{canon}'  absorbs  "
                                 + ", ".join(f"'{s}' ({m / 60:.1f}h)"
                                             for s, m in sp.items()
                                             if s != canon))
            lines.append("")
        if junk:
            lines.append(f"{junk} junk row(s) — unreadable date or ≤0 "
                         "minutes; invisible to every view already. "
                         "Clean drops them.")
        if dups:
            lines.append(f"{dups} exact duplicate row(s). Clean drops them.")
        if overlaps:
            lines.append(f"{overlaps} overlapping work interval pair(s) — "
                         "usually a hand-added past session over tracked "
                         "time. Listed only; fix via the csv if the totals "
                         "matter.")
        if not (rename or junk or dups or overlaps):
            lines.append("Nothing to fix — the history is clean. ✓")
        return lines, rename, junk, dups

    def _data_doctor(self):
        win = tk.Toplevel(self)
        win.title("Data doctor — sessions.csv")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10),
                      width=86, height=24)
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        btn = ttk.Button(bar, text="Clean now (backs up first)")
        btn.pack(side="left")
        note = ttk.Label(bar, text="", foreground="#777777")
        note.pack(side="left", padx=8)

        def render():
            lines, rename, junk, dups = self._doctor_scan()
            txt.config(state="normal")
            txt.delete("1.0", "end")
            txt.insert("1.0", "\n".join(lines))
            txt.config(state="disabled")
            btn.config(state="normal" if (rename or junk or dups)
                       else "disabled")
            return rename

        def clean():
            _lines, rename, _j, _d = self._doctor_scan()
            bdir = os.path.join(data_dir(), "backups")
            os.makedirs(bdir, exist_ok=True)
            shutil.copy2(SESSIONS_CSV, os.path.join(
                bdir, f"sessions_before_doctor_{dt.date.today()}.csv"))
            seen, out = set(), []
            for r in read_rows():
                tup = tuple(r)
                if tup in seen:
                    continue
                seen.add(tup)
                try:
                    dt.date.fromisoformat(r[0])
                    if int(r[4]) <= 0:
                        continue
                except ValueError:
                    continue
                t = r[5].strip()
                out.append(r[:5] + [rename.get(t, t)] + r[6:])
            tmp = SESSIONS_CSV + ".tmp"
            with open(tmp, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(CSV_HEADER)
                w.writerows(out)
            os.replace(tmp, SESSIONS_CSV)
            self._refresh_totals()
            note.config(text=f"Cleaned — backup in backups\\. "
                             f"{len(out)} rows kept.")
            render()

        btn.config(command=clean)
        render()

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
    # per-monitor DPI awareness — without this, Tk mis-scales/overlaps
    # widgets on a laptop+external-monitor setup with different scaling
    # (must run before any Tk() is created)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # per-monitor v2
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()     # system-DPI fallback
        except Exception:
            pass
    if already_running():
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(APP_NAME, "TimerDiary is already running — "
                                      "check the taskbar (or the other monitor).")
        sys.exit(0)
    App().mainloop()
