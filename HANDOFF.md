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

## The concept model (read this when it feels scattered)

There are only **three kinds of thing** in this app. Every feature is one
of them; the scatter came from not naming them:

1. **SOURCES** feed the day record (see above). Adding one is cheap.
2. **LENSES** — a *lens* is a set of task keywords over a date range. This
   is the dot most recently connected: **SIGNAL, Goals and Deadlines are
   the same shape** — `(keywords, window) → minutes`. They differ only in
   framing: SIGNAL = today's focus, Goal = the standing *why*, Deadline =
   a *when* with a scope. All three now resolve through ONE primitive:
   `matched_minutes(kws, lo, hi)` + `task_matches(task, kws)` (module top).
   A goal seeds SIGNAL when the day starts blank; a deadline should be
   able to point at a goal. Think of them as one system with three faces.
3. **VIEWS** read the record and the lenses and say something honest:
   dashboard (the home), summaries, insights, exports, burn-down, heatmap.

If a new idea isn't a source, a lens, or a view, it probably doesn't
belong — or it's a new *source key* in disguise.

## Realization gap (the actual scatter, be honest with the user)

The model above is TRUE in intent but only PARTLY realized in code:

- `_life_day` / `day_index` unified **dates**; `matched_minutes` (v6.3)
  unified the **keyword lens** — but only `_is_signal` and `_goal_minutes`
  route through it so far.
- Still hand-rolling their own row scan + substring match (migrate these
  to `matched_minutes` next, one per commit, each has tests to add):
  `_dl_progress`, `_refresh_totals` (deadline weekly block),
  `_burndown_series`, `_capacity_lines`. ~6 near-identical loops remain.
- `App` is one ~3600-line class doing storage + timer state machine +
  every window. Not worth splitting files (stdlib-single-file rule), but
  the method groups (`# ----- xxx -----` banners) are the seams; keep new
  code inside the right banner, keep lenses/sources/views separated.

Consolidation direction (no rewrite, just convergence): every place that
answers "how many minutes on X over range Y" calls `matched_minutes`;
every place that asks "what does the app know about day D" calls
`_life_day`. When both are true everywhere, the scatter is gone.

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
  goals in JSON export, this HANDOFF.md. SIGNAL seeds from goals.
- **v6.3**: **the lens primitive** — `matched_minutes` / `task_matches`
  at module top; SIGNAL + Goals converge on it. Concept model documented
  above. No new feature; this was a *consolidation* pass.
- **v6.4**: **Themed writing** (`Ctrl+T` / View → Browse themes) — option
  C from the 2026-07-12 proposal, picked by the user and extended: a
  distraction-free popup writes a delimited `=== THEME: x ===` block into
  *today's* day file (no second data store — Browse themes is a read-only
  scan across every day file's blocks, same pattern as Search all days);
  supports the `[Xm]` time-box syntax; covers reflection, brainstorming
  and "someday" listing as one generic mechanism, not three modes.
  **Insights fixed**: sleep/energy-vs-output were silently averaging in
  days with zero tracked work (a weekend you didn't open the app dragged
  the average toward zero) — now filtered to active days only, and the
  wording spells out what's being compared instead of a terse arrow
  chain. **TODO carry-over tightened**: only `-`/`*`/`[ ]` bullet lines
  under a `TODO:` header carry — free paragraphs (even ones mentioning
  "todo") no longer sweep in wholesale. New `SOMEDAY:` header (same
  bullet syntax) is recognized by never being carried — no new parsing
  needed, "someday" just doesn't contain "todo". **Life dashboard** gained
  a sleep-bars graph (14 nights, ≥7h/<7h shading, workout dot) under the
  week bars — the user's ask: "you catch things way faster from graphs."
  Also: an externally-authored (mobile Claude Code) branch was merged
  after a full re-review + regression pass and a from-scratch re-author
  as the user with no AI trailers — see CLAUDE.md incident log, not
  duplicated here since it's private/operational, not architecture.
- **v6.5**: **the task library** — Goals/Tasks/TODO/SOMEDAY were four
  overlapping half-systems (user's own diagnosis: "so scattered"). Unified
  around the existing `settings["tasks"]` backlog rather than inventing a
  fifth: every item now carries `priority` (signal/normal/someday, click
  to cycle in the Tasks window — `_PRI_NEXT`), an optional linked `goal`,
  and a `source` (which day or theme it came from). `TODO:`/`SOMEDAY:`
  bullets anywhere — main diary or a themed-writing session — auto-capture
  into the library via `_extract_bullets`/`_add_task` (deduped by
  normalized name), immediately on a themed-writing save and at day
  rollover for the main diary; the bullet text stays visible in the day
  file too, the library is a tracked *copy*, never the only place it
  lives. Status bar quietly flags `⚠ not today's signal` when the active
  task doesn't match SIGNAL — informational, deliberately not the
  drift-prompt/priority-gate that's still on hold (see below). Also this
  release: per-monitor DPI awareness set at startup (root cause of
  dashboard widgets overlapping on the user's mixed-DPI laptop+monitor
  setup — Tk was never told the process is DPI-aware); dashboard given
  explicit geometry + a scrollbar as defense in depth; workout-dot on the
  sleep graph now needs ≥10 min (was flagging Apple Watch's auto-detected
  "Other" activity blips as young as 5 min as a full workout).
- Outlook `.ics` export researched 2026-07-13: **new Outlook and the
  classic Import/Export wizard no longer offer iCalendar export at all**
  (CSV or PST only — matches what the user found). The working path is
  Outlook on the web → Settings → Calendar → Shared calendars → **Publish
  a calendar**, detail level "Availability only" (no titles/attendees —
  matches the user's privacy instinct and is all `parse_ics_busy` reads
  anyway), which gives an `.ics` URL to periodically re-download. May be
  disabled by org policy on managed accounts. No code change from this —
  advisory only, logged here so it isn't re-researched from scratch.

## BACKLOG (priority order — continue here)

1. **Dashboard as home**: retire/merge the now-redundant standalone
   windows (weekly summary, trend, health view) once the user confirms
   the dashboard covers them; keep heatmap + burn-down as drill-downs.
2. **Finish the lens convergence** (started v6.3): migrate `_dl_progress`,
   `_refresh_totals` deadline block, `_burndown_series`, `_capacity_lines`
   onto `matched_minutes`. Then **link the faces**: a deadline can point
   at a goal (dropdown of goal names); SIGNAL already seeds from goals;
   review block shows goal-vs-ambition arrows. One system, three faces.
2b. **Themed writing v2** (v1 done in v6.4): progression view could diff
   or highlight changed stance between entries on the same topic ("your
   thinking on X shifted here"); consider a lightweight `#tag` alternative
   for one-line mentions that don't deserve a whole popup session (the
   user floated this as option A before picking C — still cheap to add
   alongside, not a replacement). User asked whether the writing popup
   should show old entries inline while continuing a topic — declined for
   now, Browse Themes open in a second window already covers it; revisit
   only if that workflow proves annoying in practice.
2c. **Task library v2** (v1 done in v6.5): the library still only links
   to ONE goal per item and has no due-date/deadline link — could point a
   task at a deadline the same way it points at a goal. Priority is a
   flat 3-state cycle; if the user wants more granularity later (e.g. a
   4th state, or per-goal color) extend `_PRI_ICON`/`_PRI_NEXT`, don't
   add a parallel priority concept. Auto-capture only fires on themed-
   writing save and day rollover — a TODO: bullet typed straight into the
   main diary and never revisited won't be captured until the day rolls
   over; acceptable (matches how carry-over already worked) but worth
   knowing if the user asks "why isn't X in the library yet".
3b. **Screen-time / doomscroll source**: the 19–21 window is documented;
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
