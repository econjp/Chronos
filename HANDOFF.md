# HANDOFF — TimerDiary / Life Management Platform

Paste-able project brain. Any new session, agent, or development platform
should read this file first; it replaces re-explaining the vision.
**Keep it updated in the same commit as the feature it describes.**

## The big vision (the user's own, restated once)

A **total life management platform**, grown outward from a work timer.
Not a productivity toy: one system that sees work, body, commitments,
goals and memory together, tells the truth about them, and keeps the data
forever. The end state: every meaningful fact about a day lives in one
record; one dashboard reads it; an AI reviews it weekly; the owner steers
their life with it.

## Architecture (the one idea that matters)

**Sources → day record → views.**

- Every capability is a *source* that writes keys onto the **day record**
  (`_life_day(date)` in `timerv2/timer_diary_v5.py`): timer → work/break/
  task minutes; SIGNAL line → signal minutes; ENERGY line → 1–5; Apple
  Health csvs → sleep/workout/steps; .ics calendar → meeting hours; week
  plan → capacity; diary txt → memory.
- Views (dashboard, summaries, insights, exports) are *readers* of the
  record / the cached `day_index()`. **A new life-data source (mood,
  money, screen time) = one new key on the record — never a new parser
  per window.** This rule is the platform.
- csv parsing is cached on file mtime (`read_rows()` / `day_index()`);
  the Data doctor keeps the substrate clean.

## Design rules (non-negotiable, learned over many iterations)

1. **The day file is the app.** Everything visible lands in the day .txt
   (SIGNAL/ENERGY lines, plans, verdicts, reviews, Done-lines). No hidden
   state the user can't read and edit as text.
2. Single file, **stdlib only**, tkinter, Windows (`build_exe.bat` →
   PyInstaller exe). No dependencies, ever.
3. **Honest, rule-based voice.** No flattery, no gamification. Insights
   speak only with enough samples (n≥3 per bucket) and are always the
   user's own history ("your actuals run ×1.5").
4. Estimates meet reality automatically (Done-lines accrue the history).
5. Day rolls over at 04:00. Finnish locale quirks in csv (`;`-delimited,
   decimal commas tolerated on import).

## Repo map & data formats

- `timerv2/timer_diary_v5.py` — the whole app (~3300 lines). v4 kept as
  reference. `timerv2/README.md` — user-facing docs, newest feature first.
- Data at `%APPDATA%\TimerDiary\`: `sessions.csv`
  (`date;type;start;end;minutes;task;note`, type=work|break, HH:MM times),
  `settings.json` (keys: deadlines, goals, tasks, capacity, off_dates,
  sleep_over, ics_path, health_dir, target_min, rollover_hour, hotkey…),
  `diary\YYYY-MM-DD.txt` day files, `backups\`.
- Day-file conventions parsed by code: `SIGNAL: kw, kw`, `ENERGY: 1-5`,
  `TODO` lines (carried to next day), `--- Done: task (est Xh, actual
  Yh)`, `--- Task:`, session/break lines, `WEEK REVIEW Wnn:` (Mondays).
- **Export life record (JSON)** (File menu) is the canonical portable
  dump: per-day record + diary text + goals + deadlines + capacity.

## Version history (one line each)

- v5.0–5.4: timer+diary merged, csv log, idle detection, break pill,
  hotkey, timeline, health import, signal meter, sleep band.
- v5.5–5.7: morning verdict, TODO carry-over, time-boxes, multiple
  deadlines, fatigue window, velocity, burn-down.
- v5.8–5.9: deadline scopes, capacity planner, task backlog with
  est-vs-actual learning, morning plan, .ics capacity, heatmap.
- **v6.0**: unified day record + `day_index()` cache, **Life dashboard**
  (Ctrl+D, one window instead of nine, cross-domain insights), **Data
  doctor** (clean task variants/dups/junk with backup).
- **v6.1**: **ENERGY line** (first proof: new source = one key),
  **LIFE BALANCE** (waking week accounted, "unaccounted ~Xh" honesty),
  **JSON life export**; summaries read the day index.
- **v6.2**: **GOALS layer** (why above when; dashboard shows where hours
  point, drift warnings), **Monday WEEK REVIEW block** in the day file,
  goals in JSON export, this HANDOFF.md.

## BACKLOG (priority order — continue here)

1. **Dashboard as home**: retire/merge the now-redundant standalone
   windows (weekly summary, trend, health view) once the user confirms
   the dashboard covers them; keep heatmap + burn-down as drill-downs.
2. **Goal ↔ deadline ↔ signal linking**: a deadline can point at a goal;
   SIGNAL defaults from the top goal's keywords; review block shows
   goal-vs-ambition arrows.
3. **Screen-time / doomscroll source**: the 19–21 window is documented;
   import phone screen-time (csv drop like health) → new day-record key →
   insight "scroll vs next-day energy".
4. **Mood ≠ energy**: optional second header line or extend ENERGY with a
   word ("ENERGY: 3 anxious") — parse the word, correlate.
5. **Money source**: monthly csv drop (bank export) → spend per day key;
   balance section gains a cost line. (User hinted "total life".)
6. **JSON import/restore**: make the life export round-trippable so the
   exe can be rebuilt from life.json alone — true data sovereignty.
7. **Multi-machine**: settings/diary already OneDrive-able; document a
   two-PC setup properly (single-instance mutex is per-machine).
8. Insights v3: weekday patterns ("your Tuesdays are 40% weaker"),
   meeting-load vs deep-hours correlation, break-ratio drift alarm.

## How to verify changes without Windows

Extract pure functions via ast and test them (pattern in previous
sessions): seed a messy csv (v4 rows, case variants, dups, junk,
overlaps), test `read_rows`/`day_index`/`_doctor_scan`/`_insight_lines`/
`_sleep_h`/`_energy_from_text` with stubbed `self`. Always
`python3 -m py_compile` the app file. The tkinter surfaces need a real
run on the user's Windows machine (Ctrl+D dashboard, Data doctor scan).

## Git

Branch: `claude/life-management-platform-arch-6s4hrv` on
`econjp/chrono`. Master holds pre-v5.5 history. Commit style: short
imperative title + honest body listing user-visible changes first.
