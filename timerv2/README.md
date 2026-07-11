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

### Day timeline (v5.2)

A thin 00–24 bar under the task row: blue = focus, orange = breaks, ticks
every 3 h. The shape of your day at a glance.

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
