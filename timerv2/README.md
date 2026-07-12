# TimerDiary v6

The old timer's workflow (timer lines + free diary notes in one .txt per day),
with the bottlenecks removed. Run `dist\TimerDiary.exe` — or rebuild it any
time with `build_exe.bat`.

### Task library (v6.5) — View → Tasks / Library

The one place for messy ideas and todos — everything that used to live in a
WhatsApp-to-self thread. Write `TODO:` / `-` bullets anywhere (the main
diary, a themed-writing session) and they land here automatically, no extra
step — the text stays visible in the day file too, this is a tracked copy,
not a replacement. Low-priority `SOMEDAY:` bullets land here too, tagged
accordingly, and are never nagged into tomorrow's carry-over.

Each item has a **priority you click to cycle** — `●` signal (green) /
`○` normal / `‥` someday (grey) — so the backlog itself tells you what's
actually important, not just what's next. Optionally link an item to a
**goal** (the dropdown next to Add), and every auto-captured item carries
its **source** (which theme, which day) so you can trace it back. Start ▶
drops it straight into the timer; Done ✓ writes est-vs-actual into the day
file, same as before.

While working, if today's `SIGNAL:` line is set and the active task
doesn't match it, the status bar quietly says so — `⚠ not today's signal`
— visibility, not a blocking gate.

### Themed writing (v6.4) — `Ctrl+T`

For everything that isn't work: career thinking, a house move, a business
idea, brainstorming, or a "want to do this someday" list. Pick or type a
topic (autocompletes from ones you've used), write in a small
distraction-free popup, **Save & close** (or just close the window — it
always saves) drops a delimited block into *today's* day file:
`=== THEME: career — 14:00 (6m) === … === END THEME ===`. Still one file,
still plain text — no second database to desync or lose.

View → **Browse themes…** reads every day file's blocks back out, grouped
by topic, oldest first — the whole thread on "career" or "Brussels move"
in one scroll, so picking a thought back up next week is just reading, not
remembering. **Copy this thread** for pasting into Claude; **Continue
writing on this topic** opens a fresh popup under the same name.

Low-priority "someday, not now" items: write them under a `SOMEDAY:`
header with `-` bullets, same as `TODO:` — they're never carried into
tomorrow (no nagging), but stay searchable (Search all days, or as their
own theme if you write them inside a themed session).

### TODO carry-over, tightened (v6.4)

Carry-over now only pulls **`-` / `*` / `[ ]` bullet lines** written under
a `TODO:` header — free paragraphs (even ones that mention "todo" in
passing) are never swept in. Old habit of writing todos as plain sentences
under `TODO:` won't carry anymore — prefix with `-`.

## Where this is heading

The long game is a **life management platform**, and the architecture now
says so: everything the app learns about a date — tracked work, signal
share, sleep, workouts, steps, meetings, planned capacity — is merged into
**one day record** internally. Each capability is a *source* that writes
into that record (timer → work, Apple Health → body, .ics → commitments,
deadlines → goals, diary → memory), and each view is a *reader* of it.
Adding a future source (mood, money, screen time) means one new key on the
record, not another parser and another window. The **Life dashboard** is
the single pane over the record, the **Data doctor** keeps the substrate
trustworthy, and the weekly **AI review** is the analyst on top.

v6.1 delivered the first proofs of that claim: **ENERGY** became a new
source with one new key, **Life balance** widened the lens from the
tracked slice to the whole waking week, and **Export life record** made
the record portable — plain JSON that any future tool can start from.

### Goals — the why layer (v6.2)

Tools → Goals: up to five, each a **name + one-line why + task keywords +
optional h/week ambition**. Deadlines answer *when*; goals answer *why the
hours happen at all*. The dashboard's GOALS section then shows where the
hours actually point — `· Thesis (graduate): 12.3h this wk · 4-wk avg
9.8h/wk · 64% of tracked` — and calls out drift honestly: `⚠ Finnish
(live here properly): 0.0h this wk — nothing in 14 days; still a goal?`

### Week review (v6.2)

Monday's day file opens with last week already reviewed: `WEEK REVIEW
W28: 23.4h over 5 active day(s), signal 61% (+3.1h vs week before)`, one
line per goal, and the two questions that close the loop — `what worked /
what stole time? ->` — answered right in the text. Friday's AI export
asks the questions; Monday's file makes you answer them.

### Energy line (v6.1)

Each new day header carries an `ENERGY: ` line — type **1–5** when you
know it, right in the text, like SIGNAL. It flows into the day record,
shows on the dashboard, and once enough days exist the insights cross it
with everything else: *"energy ≥4 days → 5.1h of work · ≤2 days → 2.9h"*,
*"energy after ≥7h sleep: 3.9/5 · after <7h: 2.8/5 — your own body,
measured."* Leave it empty on days you don't care.

### Life balance (v6.1, in the dashboard)

The dashboard now accounts the **waking week**, not just the tracked
slice: `tracked work 18.4h (16%) · breaks 3.1h · meetings 4.5h · workout
2.3h`, the by-project split, and the honest remainder — `unaccounted
~83h — meals, commute, people, scroll. The diary knows; the timer
doesn't.` Sleep comes from the health import (8h assumed where unknown,
and it says so).

### Export life record (v6.1)

File → *Export life record (JSON)…* — every day the app knows anything
about, one JSON file: work/break/task minutes, signal, energy, sleep,
workout, steps, meeting hours, capacity, plus the full diary text, along
with your deadlines and week plan. Back it up, feed it to an AI, or build
the next tool on top of it. The data is yours and outlives the app.

### Life dashboard (v6.0) — `Ctrl+D`

One window instead of nine: **today** (hours so far incl. the running
session, signal %, the morning plan vs capacity, last night's sleep),
**the week** as bars — green signal share inside blue work, last week as
grey ghosts, planned capacity as a red dashed line — a **sleep graph**
below it (last 14 nights, dark bars ≥7h / amber <7h, a green dot on days
you also logged a workout — the body signals merged into one glance,
because a graph reads faster than any sentence about it) — **every
deadline** with done/scope, needed-per-day and the combined slack
verdict, and **insights** cross-referencing the sources over your last 60
days, counting only days you actually tracked work (a weekend you didn't
open the app isn't evidence about anything):

- *on days you tracked work: after ≥7h sleep you averaged 5.2h of work
  (18 such days) vs 3.9h after <7h sleep (12 days) — a +1.3h/day difference*
- *deep hours 09–12: 41% of all your work lands there — guard that window*
- *average unbroken block 32m this week vs 41m before — more fragmented*
- *estimates: actuals run ×1.5 across 13 finished tasks*
- *streak: 4 active days · best in 16 weeks: 9*

Every insight is your own history and only appears once there are enough
samples. **Copy for AI review** puts the whole consolidated picture on the
clipboard — one paste instead of stitching six windows together.

### Data doctor (v6.0)

Tools → Data doctor: one pass over `sessions.csv` reporting task-name
spelling variants (`Thesis` / `thesis: ch4 `), junk rows, exact duplicates
and overlapping intervals. **Clean now** merges each variant group into its
most-used spelling and drops the junk — after copying a backup into
`backups\`. Months of half-consistent task names stop poisoning the
summaries.

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

### Morning plan (v5.9)

Each new day file opens with today's mission, computed for you:
`plan today: Thesis 5.4h = 5.4h needed · 4.0h available (1.5h in
meetings) ⚠ tight — start early, cut the admin`. Deadline scopes ×
weekday capacity × calendar, decided before you've had coffee.

### Calendar & off days (v5.9)

File → *Calendar busy-time (.ics)* → point at an exported Outlook/Google
calendar file: meeting hours are subtracted from capacity everywhere
(re-read automatically when you re-export over the same file). Recurring
and all-day events are skipped — re-export fresh rather than trusting
old recurrences. Vacation dates go in the Week plan window → zero
capacity those days. Tools → **Meeting mode** pauses idle detection for
90 min (lectures, long reads).

### Estimate learning (v5.9)

Every `Done ✓` writes est-vs-actual into the day file; once 3+ exist the
Tasks window tells you your personal multiplier: *"your actuals run ×1.5
your estimates — [2h] realistically means 3h."* Your own history, no
judgment, just math.

### Month heatmap (v5.9)

View → Month heatmap: 16 weeks of daily hours, GitHub-style. Streaks and
dead weeks at a glance.

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
