"""
TimerDiary v4 — work timer + daily diary in one small app.

v4 additions:
- SEARCH DIARY (View menu): full-text search across every day's diary —
  "what did I do about X in May" answered in 2 seconds
- TREND chart (View menu): last 8 weeks of tracked hours as bars, so you see
  your trajectory, not just this week
- DAILY TARGET (Tools menu): set e.g. 300 min/day, a progress bar fills up as
  you log time
- ADD PAST SESSION (File menu): forgot to start the timer during a meeting?
  Add it after the fact in one small form
- AUTO-BACKUP: sessions.csv copied to backups\\ once a week, silently
- CATEGORIES: name tasks like "day job: memo" or "thesis: ch4" and the
  summaries also group totals by the prefix before ":"

v3 features kept: auto diary timestamps ("09:00-09:45  thesis (45m)"),
F5 timestamp, smart task suggestion by hour, .ics calendar export, monthly
summary, not-tracking title nudge, Ctrl+Space / Ctrl+Enter hotkeys.
v2 features kept: recent-task dropdown, Switch button, right-click edit/delete,
compact always-on-top mode, crash recovery, autostart.

Data (plain, analysis-ready): %APPDATA%\\TimerDiary
  sessions.csv          ISO dates, numeric minutes, ';' delimited
                        Excel opens it directly; pandas: pd.read_csv(p, sep=';')
  diary\\YYYY-MM-DD.txt  one plain-text diary per day
  backups\\              weekly copies of sessions.csv

Build the exe:  pip install pyinstaller
  pyinstaller --onefile --noconsole --name TimerDiary timer_diary_v4.py
"""

import csv
import json
import os
import shutil
import sys
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

APP_NAME = "TimerDiary"

# ---------------- storage ----------------

def data_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_NAME)
    os.makedirs(os.path.join(d, "diary"), exist_ok=True)
    return d

SESSIONS_CSV = os.path.join(data_dir(), "sessions.csv")
RUNNING_JSON = os.path.join(data_dir(), "running.json")
SETTINGS_JSON = os.path.join(data_dir(), "settings.json")
CSV_HEADER = ["date", "start", "end", "minutes", "task", "note"]


def read_sessions():
    if not os.path.exists(SESSIONS_CSV):
        return []
    with open(SESSIONS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter=";"))
    return [r + [""] * (6 - len(r)) for r in rows[1:] if len(r) >= 5]


def write_sessions(rows):
    with open(SESSIONS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(CSV_HEADER)
        w.writerows(rows)


def append_session(row):
    new = not os.path.exists(SESSIONS_CSV)
    with open(SESSIONS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if new:
            w.writerow(CSV_HEADER)
        w.writerow(row)


def recent_tasks(limit=12):
    seen, out = set(), []
    for r in reversed(read_sessions()):
        t = r[4].strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
        if len(out) >= limit:
            break
    return out


def suggest_task(hour):
    """Task most often started around this hour (+-1h), last 60 days."""
    cutoff = dt.date.today() - dt.timedelta(days=60)
    counts = {}
    for r in read_sessions():
        try:
            d = dt.date.fromisoformat(r[0])
            h = int(r[1][:2])
        except (ValueError, IndexError):
            continue
        if d >= cutoff and abs(h - hour) <= 1 and r[4].strip():
            counts[r[4].strip()] = counts.get(r[4].strip(), 0) + 1
    return max(counts, key=counts.get) if counts else ""


def weekly_totals(n_weeks=8):
    """[(monday, minutes), ...] for the last n_weeks incl. current."""
    today = dt.date.today()
    this_mon = today - dt.timedelta(days=today.weekday())
    weeks = {this_mon - dt.timedelta(weeks=i): 0 for i in range(n_weeks - 1, -1, -1)}
    for r in read_sessions():
        try:
            d = dt.date.fromisoformat(r[0])
            m = int(r[3])
        except ValueError:
            continue
        mon = d - dt.timedelta(days=d.weekday())
        if mon in weeks:
            weeks[mon] += m
    return sorted(weeks.items())


def diary_path(day):
    return os.path.join(data_dir(), "diary", day.isoformat() + ".txt")


def search_diary_files(query):
    """[(date_str, line), ...] newest first, case-insensitive."""
    q = query.lower()
    out = []
    ddir = os.path.join(data_dir(), "diary")
    for fn in sorted(os.listdir(ddir), reverse=True):
        if not fn.endswith(".txt"):
            continue
        try:
            with open(os.path.join(ddir, fn), encoding="utf-8") as f:
                for line in f:
                    if q in line.lower():
                        out.append((fn[:-4], line.rstrip()))
        except OSError:
            continue
    return out


def load_settings():
    try:
        with open(SETTINGS_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(s):
    with open(SETTINGS_JSON, "w", encoding="utf-8") as f:
        json.dump(s, f)


def backup_if_due():
    """Copy sessions.csv to backups/ if the newest backup is >7 days old."""
    if not os.path.exists(SESSIONS_CSV):
        return
    bdir = os.path.join(data_dir(), "backups")
    os.makedirs(bdir, exist_ok=True)
    today = dt.date.today()
    newest = None
    for fn in os.listdir(bdir):
        try:
            newest = max(newest or dt.date.min,
                         dt.date.fromisoformat(fn[9:19]))
        except (ValueError, IndexError):
            continue
    if newest and (today - newest).days < 7:
        return
    shutil.copy2(SESSIONS_CSV,
                 os.path.join(bdir, f"sessions_{today.isoformat()}.csv"))


# ---------------- crash recovery ----------------

def save_running(start, task, note):
    with open(RUNNING_JSON, "w", encoding="utf-8") as f:
        json.dump({"start": start.isoformat(), "task": task, "note": note}, f)


def clear_running():
    try:
        os.remove(RUNNING_JSON)
    except FileNotFoundError:
        pass


def load_running():
    try:
        with open(RUNNING_JSON, encoding="utf-8") as f:
            d = json.load(f)
        return dt.datetime.fromisoformat(d["start"]), d.get("task", ""), d.get("note", "")
    except Exception:
        return None


# ---------------- calendar (.ics) export ----------------

def week_to_ics(monday):
    sunday = monday + dt.timedelta(days=6)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{APP_NAME}//EN"]
    n = 0
    for i, r in enumerate(read_sessions()):
        try:
            d = dt.date.fromisoformat(r[0])
        except ValueError:
            continue
        if not (monday <= d <= sunday):
            continue
        try:
            sh, sm = map(int, r[1].split(":"))
            eh, em = map(int, r[2].split(":"))
        except ValueError:
            continue
        start = dt.datetime(d.year, d.month, d.day, sh, sm)
        end = dt.datetime(d.year, d.month, d.day, eh, em)
        if end <= start:
            end += dt.timedelta(days=1)
        lines += ["BEGIN:VEVENT",
                  f"UID:timerdiary-{d.isoformat()}-{i}@local",
                  f"DTSTART:{start:%Y%m%dT%H%M%S}",
                  f"DTEND:{end:%Y%m%dT%H%M%S}",
                  f"SUMMARY:{r[4] or 'work'}",
                  f"DESCRIPTION:{r[5].replace(chr(10), ' ')}",
                  "END:VEVENT"]
        n += 1
    lines.append("END:VCALENDAR")
    path = os.path.join(data_dir(), f"TimerDiary_week_{monday.isoformat()}.ics")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path, n


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


# ---------------- helpers ----------------

def category_totals(tasks):
    """Group task->minutes by 'prefix:' category. Returns dict or None."""
    cats, any_cat = {}, False
    for t, m in tasks.items():
        if ":" in t:
            c, any_cat = t.split(":", 1)[0].strip(), True
        else:
            c = "(uncategorised)"
        cats[c] = cats.get(c, 0) + m
    return cats if any_cat else None


# ---------------- app ----------------

NORMAL_GEO = "880x520"
COMPACT_GEO = "310x88"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry(NORMAL_GEO)
        self.minsize(310, 88)
        try:
            ttk.Style().theme_use("vista")
        except tk.TclError:
            pass

        self.settings = load_settings()
        self.start_time = None
        self.today = dt.date.today()
        self.compact = False

        backup_if_due()
        self._build_menu()
        self._build_ui()
        self._bind_keys()
        self._load_today_sessions()
        self._load_diary()
        self._suggest_if_empty()
        self._recover_if_needed()
        self._tick()
        self._autosave_loop()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----- menu -----

    def _build_menu(self):
        m = tk.Menu(self)
        filem = tk.Menu(m, tearoff=0)
        filem.add_command(label="Add past session…", command=self._add_past_session)
        filem.add_command(label="Export week to calendar (.ics)", command=self._export_ics)
        filem.add_command(label="Open data folder", command=self._open_folder)
        filem.add_separator()
        filem.add_command(label="Exit", command=self._on_close)
        m.add_cascade(label="File", menu=filem)

        viewm = tk.Menu(m, tearoff=0)
        viewm.add_command(label="Weekly summary", command=lambda: self._summary("week"))
        viewm.add_command(label="Monthly summary", command=lambda: self._summary("month"))
        viewm.add_command(label="Trend (8 weeks)", command=self._trend)
        viewm.add_command(label="Search diary…", command=self._search_diary)
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
        self.autolog_var = tk.BooleanVar(value=self.settings.get("autolog", True))
        toolsm.add_checkbutton(label="Auto-log sessions into diary",
                               variable=self.autolog_var, command=self._save_prefs)
        toolsm.add_separator()
        toolsm.add_command(label="Set daily target…", command=self._set_target)
        m.add_cascade(label="Tools", menu=toolsm)
        self.menu = m
        self.config(menu=m)

    def _save_prefs(self):
        self.settings["nudge"] = self.nudge_var.get()
        self.settings["autolog"] = self.autolog_var.get()
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
        self._load_today_sessions()

    # ----- UI -----

    def _build_ui(self):
        self.top = ttk.Frame(self)
        self.top.pack(fill="x", padx=8, pady=(6, 0))

        self.clock = ttk.Label(self.top, text="00:00:00", font=("Segoe UI", 22))
        self.clock.pack(side="left")

        self.compact_btn = ttk.Button(self.top, text="—", width=3,
                                      command=self._toggle_compact)
        self.compact_btn.pack(side="right")
        self.btn = ttk.Button(self.top, text="Start", width=8, command=self._toggle)
        self.btn.pack(side="right", padx=(0, 4))
        self.switch_btn = ttk.Button(self.top, text="Switch", width=8,
                                     command=self._switch, state="disabled")
        self.switch_btn.pack(side="right", padx=(0, 4))

        row = ttk.Frame(self)
        row.pack(fill="x", padx=8, pady=4)
        ttk.Label(row, text="Task:").pack(side="left")
        self.task_var = tk.StringVar()
        self.task_box = ttk.Combobox(row, textvariable=self.task_var,
                                     values=recent_tasks())
        self.task_box.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        row2 = ttk.Frame(self.body)
        row2.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Label(row2, text="Note:").pack(side="left")
        self.note_entry = ttk.Entry(row2)
        self.note_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.target_bar = ttk.Progressbar(self.body, maximum=100)
        # packed on demand in _load_today_sessions when a target is set

        pw = ttk.Panedwindow(self.body, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self.pw = pw

        left = ttk.Frame(pw)
        pw.add(left, weight=1)
        ttk.Label(left, text="Today's sessions  (right-click to edit/delete)").pack(anchor="w")
        cols = ("start", "min", "task", "note")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=8)
        for c, w in zip(cols, (55, 40, 150, 150)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Button-3>", self._tree_menu)

        self.total_lbl = ttk.Label(left, text="Today: 0 min")
        self.total_lbl.pack(anchor="w", pady=(4, 0))

        right = ttk.Frame(pw)
        pw.add(right, weight=1)
        self.diary_lbl = ttk.Label(right, text=f"Diary — {self.today.isoformat()}   (F5 = timestamp)")
        self.diary_lbl.pack(anchor="w")
        self.diary = tk.Text(right, wrap="word", font=("Segoe UI", 10),
                             undo=True, relief="sunken", borderwidth=1)
        self.diary.pack(fill="both", expand=True, pady=(4, 0))

        self.status = ttk.Label(self, text="Ctrl+Space start/stop · Ctrl+Enter switch",
                                anchor="w")
        self.status.pack(fill="x", side="bottom", padx=8, pady=(0, 4))

    def _bind_keys(self):
        self.bind("<Control-space>", lambda e: self._toggle())
        self.bind("<Control-Return>", lambda e: self._switch())
        self.diary.bind("<F5>", self._insert_timestamp)

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
            self._load_today_sessions()

    # ----- timer -----

    def _toggle(self):
        if self.start_time is None:
            self._start()
        else:
            self._stop_and_log()

    def _start(self):
        self._roll_day_if_needed()
        self._suggest_if_empty()
        self.start_time = dt.datetime.now()
        self.btn.config(text="Stop")
        self.switch_btn.config(state="normal")
        task = self.task_var.get().strip()
        save_running(self.start_time, task, self.note_entry.get().strip())
        self.status.config(text="Running: " + (task or "(no task)"))

    def _suggest_if_empty(self):
        if not self.task_var.get().strip():
            s = suggest_task(dt.datetime.now().hour)
            if s:
                self.task_var.set(s)

    def _stop_and_log(self, end=None, restart_after=False):
        end = end or dt.datetime.now()
        start = self.start_time
        self.start_time = None
        self.btn.config(text="Start")
        self.switch_btn.config(state="disabled")
        clear_running()
        minutes = max(1, round((end - start).total_seconds() / 60))
        task = self.task_var.get().strip()
        note = self.note_entry.get().strip()
        append_session([start.date().isoformat(),
                        start.strftime("%H:%M"), end.strftime("%H:%M"),
                        minutes, task, note])
        if self.autolog_var.get():
            line = f"{start:%H:%M}-{end:%H:%M}  {task or '(no task)'} ({minutes}m)"
            if note:
                line += f" - {note}"
            self._append_diary_line(line)
        self.note_entry.delete(0, "end")
        self.task_box.config(values=recent_tasks())
        self._load_today_sessions()
        self.status.config(text=f"Logged {minutes} min — {task or '(no task)'}")
        if restart_after:
            self.task_var.set("")
            self.task_box.focus_set()
            self._start()

    def _switch(self):
        if self.start_time:
            self._stop_and_log(restart_after=True)

    def _tick(self):
        if self.start_time:
            secs = int((dt.datetime.now() - self.start_time).total_seconds())
            h, rem = divmod(secs, 3600)
            m, s = divmod(rem, 60)
            self.clock.config(text=f"{h:02}:{m:02}:{s:02}")
            self.title(f"{h:02}:{m:02} — {self.task_var.get() or APP_NAME}")
        else:
            self.clock.config(text="00:00:00")
            self.title("⏸ not tracking — " + APP_NAME
                       if self.nudge_var.get() else APP_NAME)
        self.after(500, self._tick)

    # ----- crash recovery -----

    def _recover_if_needed(self):
        rec = load_running()
        if not rec:
            return
        start, task, note = rec
        mins = max(1, round((dt.datetime.now() - start).total_seconds() / 60))
        ans = messagebox.askyesnocancel(
            APP_NAME,
            f"A session was still running when the app last closed:\n\n"
            f"  {task or '(no task)'} — started {start:%d.%m %H:%M} ({mins} min ago)\n\n"
            f"Yes = keep it running\nNo = log it (until now)\nCancel = discard")
        if ans is True:
            self.start_time = start
            self.task_var.set(task)
            self.note_entry.insert(0, note)
            self.btn.config(text="Stop")
            self.switch_btn.config(state="normal")
        elif ans is False:
            self.start_time = start
            self.task_var.set(task)
            self.note_entry.insert(0, note)
            self._stop_and_log()
        else:
            clear_running()

    # ----- sessions list + edit/delete -----

    def _load_today_sessions(self):
        self.tree.delete(*self.tree.get_children())
        total = week_total = 0
        today = dt.date.today()
        monday = today - dt.timedelta(days=today.weekday())
        for idx, r in enumerate(read_sessions()):
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[3])
            except ValueError:
                continue
            if monday <= d <= today:
                week_total += m
            if d == today:
                self.tree.insert("", "end", iid=str(idx),
                                 values=(r[1], r[3], r[4], r[5]))
                total += m
        text = (f"Today: {total} min ({total/60:.1f} h)   |   "
                f"Week: {week_total} min ({week_total/60:.1f} h)")
        target = self.settings.get("target_min", 0)
        if target:
            pct = min(100, round(100 * total / target))
            text += f"   |   Target: {pct}% of {target} min"
            self.target_bar.config(maximum=target, value=min(total, target))
            if not self.target_bar.winfo_ismapped():
                self.target_bar.pack(fill="x", padx=8, pady=(0, 4),
                                     before=self.pw)
        elif self.target_bar.winfo_ismapped():
            self.target_bar.pack_forget()
        self.total_lbl.config(text=text)

    def _tree_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit…", command=lambda: self._edit_session(int(iid)))
        menu.add_command(label="Delete", command=lambda: self._delete_session(int(iid)))
        menu.tk_popup(event.x_root, event.y_root)

    def _edit_session(self, idx):
        rows = read_sessions()
        if idx >= len(rows):
            return
        r = rows[idx]
        task = simpledialog.askstring(APP_NAME, "Task:", initialvalue=r[4], parent=self)
        if task is None:
            return
        mins = simpledialog.askinteger(APP_NAME, "Minutes:", initialvalue=int(r[3]),
                                       minvalue=1, parent=self)
        if mins is None:
            return
        note = simpledialog.askstring(APP_NAME, "Note:", initialvalue=r[5], parent=self)
        if note is None:
            note = r[5]
        r[3], r[4], r[5] = str(mins), task.strip(), note.strip()
        write_sessions(rows)
        self._load_today_sessions()
        self.task_box.config(values=recent_tasks())

    def _delete_session(self, idx):
        rows = read_sessions()
        if idx >= len(rows):
            return
        r = rows[idx]
        if messagebox.askyesno(APP_NAME, f"Delete session?\n{r[1]}  {r[3]} min  {r[4]}"):
            del rows[idx]
            write_sessions(rows)
            self._load_today_sessions()

    # ----- add past session -----

    def _add_past_session(self):
        win = tk.Toplevel(self)
        win.title("Add past session")
        win.resizable(False, False)
        win.grab_set()
        fields = {}
        defaults = [("Date (YYYY-MM-DD)", dt.date.today().isoformat()),
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
            append_session([d.isoformat(), start.strftime("%H:%M"),
                            end.strftime("%H:%M"), mins, task, note])
            self.task_box.config(values=recent_tasks())
            self._load_today_sessions()
            win.destroy()
            self.status.config(text=f"Added {mins} min — {task or '(no task)'}")

        ttk.Button(win, text="Save", command=save).grid(
            row=len(defaults), column=1, sticky="e", padx=6, pady=8)

    # ----- diary -----

    def _load_diary(self):
        p = diary_path(self.today)
        self.diary.delete("1.0", "end")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                self.diary.insert("1.0", f.read())
        self.diary.edit_modified(False)

    def _append_diary_line(self, line):
        cur = self.diary.get("1.0", "end-1c")
        if cur and not cur.endswith("\n"):
            self.diary.insert("end", "\n")
        self.diary.insert("end", line + "\n")
        self._save_diary()

    def _save_diary(self):
        text = self.diary.get("1.0", "end-1c")
        p = diary_path(self.today)
        if text.strip() or os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
        self.diary.edit_modified(False)

    def _autosave_loop(self):
        self._roll_day_if_needed()
        if self.diary.edit_modified():
            self._save_diary()
            self.status.config(text=f"Diary saved {dt.datetime.now():%H:%M:%S}")
        self.after(15000, self._autosave_loop)

    def _roll_day_if_needed(self):
        now = dt.date.today()
        if now != self.today:
            self._save_diary()
            self.today = now
            self.diary_lbl.config(text=f"Diary — {self.today.isoformat()}   (F5 = timestamp)")
            self._load_diary()
            self._load_today_sessions()

    # ----- diary search -----

    def _search_diary(self):
        win = tk.Toplevel(self)
        win.title("Search diary")
        win.geometry("560x420")
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
            query = q.get().strip()
            if not query:
                return
            hits = search_diary_files(query)
            if not hits:
                txt.insert("1.0", "No matches.")
            else:
                for date, line in hits:
                    txt.insert("end", f"{date}  {line}\n")
            txt.config(state="disabled")

        ttk.Button(bar, text="Search", command=go).pack(side="left", padx=(6, 0))
        q.bind("<Return>", go)

    # ----- summaries + trend -----

    def _summary(self, mode):
        today = dt.date.today()
        if mode == "week":
            first = today - dt.timedelta(days=today.weekday())
            last = first + dt.timedelta(days=6)
            title = f"Week {first.isocalendar().week} — {first} … {last}"
        else:
            first = today.replace(day=1)
            nxt = (first.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
            last = nxt - dt.timedelta(days=1)
            title = f"{first:%B %Y}"

        days, tasks = {}, {}
        d = first
        while d <= last:
            days[d] = 0
            d += dt.timedelta(days=1)
        for r in read_sessions():
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[3])
            except ValueError:
                continue
            if d in days:
                days[d] += m
                key = r[4] or "(no task)"
                tasks[key] = tasks.get(key, 0) + m

        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("450x520")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=8)

        lines, total = ["Per day:"], 0
        for d, m in days.items():
            total += m
            if mode == "month" and m == 0:
                continue
            lines.append(f"  {d.strftime('%a %d.%m')}  {m:>4} min  {m/60:>5.1f} h")
        lines.append(f"  {'TOTAL':<9} {total:>4} min  {total/60:>5.1f} h")

        cats = category_totals(tasks)
        if cats:
            lines += ["", "Per category:"]
            for c, m in sorted(cats.items(), key=lambda x: -x[1]):
                lines.append(f"  {m:>4} min  {m/60:>5.1f} h  {c}")

        lines += ["", "Per task:"]
        for t, m in sorted(tasks.items(), key=lambda x: -x[1]):
            lines.append(f"  {m:>4} min  {m/60:>5.1f} h  {t}")
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
                           text=f"W{mon.isocalendar().week}",
                           font=("Segoe UI", 8))
            if m:
                cv.create_text((x0 + x1) / 2, y0 - 10, text=f"{m/60:.1f}h",
                               font=("Segoe UI", 8))
        cv.create_line(PAD, H - PAD, W - PAD, H - PAD)

    # ----- calendar export -----

    def _export_ics(self):
        today = dt.date.today()
        monday = today - dt.timedelta(days=today.weekday())
        path, n = week_to_ics(monday)
        self.status.config(text=f"Exported {n} sessions -> {os.path.basename(path)}")
        if messagebox.askyesno(APP_NAME,
                               f"Exported {n} sessions to\n{path}\n\nOpen folder?"):
            self._open_folder()

    # ----- misc -----

    def _open_folder(self):
        d = data_dir()
        if sys.platform == "win32":
            os.startfile(d)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", d])

    def _on_close(self):
        if self.start_time is not None:
            if messagebox.askyesno(APP_NAME, "Timer is running. Log the session before closing?"):
                self._stop_and_log()
            else:
                clear_running()
        self._save_diary()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
