# TimerDiary v5

The old timer's workflow (timer lines + free diary notes in one .txt per day),
with the bottlenecks removed. Run `dist\TimerDiary.exe` — or rebuild it any
time with `build_exe.bat`.

## Daily flow

1. It starts with Windows (asked once on first run; toggle in Tools).
2. Today's file already exists — header + yesterday's totals at the top.
3. **Start** to work, **Stop** for a break, **Start** again → a
   `--- Break duration: 0:12:3 ` line appears with the cursor parked at the
   end so you can type what the break was, exactly like the old format.
4. Type diary notes anywhere in the text pane, any time. Autosaves every 10 s.
5. **Reset** (or Ctrl+R) ends the session → `--- Session reset, studying
   duration: 1:29:14`.
6. Walk away without stopping? When you come back it asks
   *"away ~14 min — log as break?"* and fixes the log retroactively.
7. Closing (or a crash / reboot) with the timer running: choose *keep
   running* and it resumes on next launch.

### Time-boxing (v5.6)

Type a task as `email: EU [15m]` (or `[1h]`, `[1h 30m]`) — when today's
total on that task blows the box, the big clock turns **red**, it beeps,
and `!!! time-box exceeded !!!` lands in the day file. For admin tasks
that balloon. The csv/dropdown store the clean task name.

### Pacing (v5.7)

Starting a task shows your **real velocity** in the status bar — "pace
2.31h/active-day (5d of last 14)" — history, not hopes. View → **Deadline
burn-down** draws the target-pace line vs your actual cumulative hours;
the red vertical gap is how far behind you are, in hours.

### Deadlines (v2 in v5.8)

Tools → Deadline countdowns: up to 4, each with an optional **start date
and total-hours scope** plus a task keyword. With a scope the totals line
turns into the real story — `Thesis 10d 6.0/60h · 5.4h/d` (done/scope and
the h/day now required) — and **⚠** appears when you're behind the
start→due line. Without a scope, the weekly-target pace logic applies.
The dot is green while you're working on any of them.

### Week plan / capacity (v5.8)

View → Week plan: set your realistic hours per weekday once. The window
then compares available hours until each due date against what your
deadlines demand: `✓ Thesis — needs 54.0h, 66.0h available → slack
+12.0h`, plus the combined verdict — "12h of real slack, the friend on
Tuesday is fine" or "⚠ overbooked by 9h: cut scope or say no to
something". (Calendar import may come later; weekday capacity is the
80% version.)

### Tasks / backlog (v5.8)

View → Tasks: add tasks as `write intro [2h]` (the `[2h]` becomes the
estimate), see actual hours accumulate against it, **Start ▶** puts it
straight into the timer, **Done ✓** removes it and writes
`--- Done: write intro (est 2h, actual 3.40h)` into the day file — your
estimate-vs-reality history, accruing for free.

### Tasks (v5.1)

Type a task (e.g. `thesis: ch4`) and press Start — a `--- Task: thesis: ch4`
line goes into the day file, so the notes always say what you were doing.
Changed to something else mid-session? Type the new task and press **Enter**
(or the Switch button / `Ctrl+Enter`): the log splits at that moment, the
time already worked stays on the old task.

### Break pill (v5.1)

Press Stop and a small always-on-top **"☕ break 12:34 — click to work"**
appears — visible over the browser, turns red after 15 min, one click
resumes work. **Drag it once to where you want it (any monitor) and it
remembers that spot for every future break.** Disable in Tools.

### Day timeline (v5.2, sleep band v5.4)

A thin 00–24 bar under the task row: blue = focus, green = signal work,
orange = breaks, ticks every 3 h. The shape of your day at a glance.

A dark **"zzz (est.)"** band shows last night's sleep — *estimated*: bed ≈
your last logged event + 1 h (00:00 if the evening wasn't logged late),
band length = the imported sleep total, clipped to end before your first
activity. The gap between midnight and the band start is your visible
doomscroll tax; the gap between band end and your first session is the
morning-efficiency one. **Right-click the bar** to enter the real bed/wake
times for last night — the label becomes "zzz (set)" (empty bed time =
back to the estimate).

The break pill escalates faster (5 min instead of 15) between **19–21** —
the documented fatigue/doomscroll window.

### Hotkeys

`Ctrl+Shift+Space` start/stop **from any app** (high beep = working, low =
break) — change it in Tools → Global hotkey (Pause, F9, …) · Enter in the
task box / `Ctrl+Enter` = switch task · `Ctrl+R` reset · `F5` insert HH:MM
timestamp. The `—` button = tiny always-on-top mode.

### Signal meter (v5.3)

Every new day file has a `SIGNAL:` line under the header — type your focus
as comma-separated keywords, right in the text (e.g. `SIGNAL: thesis, day job`).
It carries over to the next day until you change it. Work on tasks matching
a keyword = signal; the totals line shows **signal 71% (wk 64%)**, the
timeline paints signal work **green** vs other work blue, and the weekly
summary + AI export get a SIGNAL row. Leave the line empty to turn it off.

### Health import (v5.3)

File → *Health import folder…* → point at a folder where a phone app drops
Apple Health CSVs. Each day's header then gets `(sleep 6h12m, workout 45m)`
automatically (checked every 30 min, since sleep syncs after you wake up).

Setup on the iPhone: install **Health Auto Export** (App Store), create an
automation exporting *Sleep Analysis* + *Exercise Time* as **CSV**, daily,
into a folder that syncs to this PC (iCloud Drive folder synced via
iCloud for Windows, or OneDrive via a Shortcuts automation). Fallback: any
csv with `date;sleep_h;workout_min` columns works — even hand-written.

### Weekly AI review (v5.1)

View → **Copy week for AI review** puts totals, per-task hours and every
day's diary text on the clipboard. Paste into Claude on Friday and ask
*"what did I actually spend time on, what slipped, what should next week
look like."*

### Deadline countdown (v5.1)

Tools → Deadline countdown: name + date + task keyword + weekly target →
the totals line shows e.g. `thesis: 18d left · 6.20/10h wk`, with a dot in
front: green = working on it right now, orange = on break, grey = not on
it. Clear the name to remove it.

The "day" rolls over at **04:00**, not midnight — a 00:30 grind stays in the
evening's file (Tools → Day rollover hour).

## Data & analysis

- Day files: `%APPDATA%\TimerDiary\diary\YYYY-MM-DD.txt`
  (File → *Change diary folder…* to point at OneDrive for sync/backup).
- `%APPDATA%\TimerDiary\sessions.csv` — every work **and** break interval:
  `date;type;start;end;minutes;task;note`. `;`-delimited → double-click opens
  straight in Excel (Finnish locale). pandas: `pd.read_csv(p, sep=';')`.
- Task naming `project: subtask` (e.g. `thesis: ch4`) groups summaries by
  project automatically.
- View menu: weekly/monthly summary (work *and* break hours per day, per
  task), 8-week trend chart, full-text search across every day file.
- File menu: export the week as `.ics` → import into Google/Outlook calendar.
- `backups\` gets a weekly copy of the csv automatically.

## Files

- `timer_diary_v5.py` — the app (single file, stdlib only)
- `timer_diary_v4.py` — previous iteration, kept for reference
- `build_exe.bat` — rebuilds `dist\TimerDiary.exe`
