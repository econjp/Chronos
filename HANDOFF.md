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

The model above is TRUE in intent and now MOSTLY realized in code (as of
v6.6):

- `_life_day` / `day_index` unified **dates**; `matched_minutes` +
  `task_matches` (v6.3, finished v6.6) unified the **keyword lens** —
  `_is_signal`, `_goal_minutes`, `_dl_progress`, the `_refresh_totals`
  weekly-target block, `_burndown_series` (via `day_index`+`task_matches`
  directly — it needs a per-day running sum, which `matched_minutes`
  itself doesn't return) and `_capacity_lines` (transitively, via
  `_dl_progress`) all route through it now. No more hand-rolled row
  scans for "minutes on X over range Y" anywhere in the app.
- Still open: the three lenses (SIGNAL/Goals/Deadlines) don't yet point
  *at each other* — a Deadline can't reference a Goal by name, though a
  Goal already seeds SIGNAL when the day starts blank. See BACKLOG #2.
- `App` is one ~4100-line class doing storage + timer state machine +
  every window. Not worth splitting files (stdlib-single-file rule), but
  the method groups (`# ----- xxx -----` banners) are the seams; keep new
  code inside the right banner, keep lenses/sources/views separated.
- The **task library** (v6.5) is a fourth kind of thing, not a lens: a
  discrete backlog item with a flat `priority` attribute, not a
  keyword-over-a-range. Deliberately NOT forced into the lens shape —
  see the v6.5 changelog entry for why. It's closer to a SOURCE (writes
  `--- Done: ...` lines onto the day record) that also happens to have
  its own persistent list in settings.

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

### Signal vs. maintenance (a recurring question, resolved 2026-07-13)

The user has asked more than once, across sessions, whether recovery/
maintenance activity (a run, sleep, physical upkeep) should count as
"signal" — the app's Musk/O'Leary-inspired "zero noise, 100% signal"
framing from early in the project. Resolved position, worth restating if
this comes up again rather than re-litigating from scratch:

**SIGNAL stays reserved for today's one declared sharpest priority.**
Maintenance is not noise, but it is also not signal — it's a third
thing. The "100% signal, zero noise" framing was always about
eliminating *noise* (drift, doomscrolling, admin that silently expands
to fill available time) — not about eliminating rest. Even maximally
focused people sleep and exercise; the framing was never "never
recover," it was "never let low-value distraction eat your attention."
Collapsing maintenance into "signal" would inflate the metric and kill
its one job: telling the user, honestly, whether today's actual hours
went to the thing they said mattered most *today*.

The architecture already had the right answer before this was asked
explicitly: **GOALS is where maintenance gets its due.** A goal like
"Physical Engine Maintenance" (already configured, 7h/week ambition)
tracks recovery as real, weighted, legitimate time — just not *today's*
signal. This is why the timeline (v7.2) now paints goal-aligned-but-
off-signal work in a third color (`TL_GOAL`, distinct from signal-green
and plain-work-blue) instead of forcing a binary signal/not-signal
choice, and why the status-bar flag (v7.2) says "counts toward: X"
instead of a bare warning. Three buckets, not two: signal (today's one
thing) > goal-aligned (matters, just not today's specific lever) > plain
work (tracked, unattributed to any declared priority) > noise (matches
nothing, actively erodes capacity — e.g. doomscrolling). Don't build a
"maintenance is 50% signal" scoring compromise if this comes up again;
the three-bucket model is already correct and more honest than a blend.

## Repo map & data formats

- `timerv2/timer_diary_v5.py` — the whole app (~4100 lines, v6.6 as of
  2026-07-13). v4 kept as reference. `timerv2/README.md` — user-facing
  docs, newest feature first.
- Data at `%APPDATA%\TimerDiary\`: `sessions.csv`
  (`date;type;start;end;minutes;task;note`, type=work|break, HH:MM times),
  `settings.json`, `diary\YYYY-MM-DD.txt` day files, `backups\`.
- `settings.json` keys: `deadlines` (list: name/start/date/total_h/
  target_h/match), `goals` (list: name/why/match/target_h, max 5),
  `tasks` (the task library, list: name/est_h/priority[signal|normal|
  someday]/goal/source/added), `capacity` (7 floats, Mon..Sun),
  `off_dates`, `sleep_over` ({iso: [bed HH:MM, wake HH:MM]}), `ics_path`,
  `health_dir`, `diary_dir`, `target_min`, `rollover_hour`, `hotkey`,
  `idle_min`, `float_break`, `nudge`, `asked_autostart`.
- Day-file conventions parsed by code: `SIGNAL: kw, kw` (carries daily,
  seeds from goals if blank), `ENERGY: 1-5`, `TODO:`/`SOMEDAY:` headers
  with `-`/`*`/`[ ]` bullets (TODO carries to next day AND auto-captures
  into the task library; SOMEDAY never carries, library-captures only),
  `--- Done: task (est Xh, actual Yh)`, `--- Task:`, `!!! time-box
  exceeded !!!`, session/break lines, `WEEK REVIEW Wnn:` (Mondays),
  `=== THEME: name — HH:MM (Xm) === ... === END THEME ===` (themed
  writing blocks, read back out by Browse Themes — never a second file).
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
- **v6.6**: friction pass + finished the lens convergence. Sleep-override
  time entry (`_parse_time_loose`) accepts `1`/`01`/`0120`/`120`/`1:20` —
  no colon, no leading zero required. Tasks/Library "Add" bar gets a
  plain "est h" field and a priority selector — typing `[2h]` inline
  still works as a fallback but is no longer required (this is what the
  user meant by "goal setting... have to manually write the []
  brackets"; the Deadline/Goals dialogs themselves never required
  brackets — those were already plain fields). File > Add past session
  gained a "carved out of a break" checkbox — logs the work interval AND
  shrinks the covering break row by the same minutes (`_shrink_last_
  break`, approximate: adjusts the break's `minutes` total, not a
  pixel-exact re-slice of its start/end) so reclassifying part of a
  break as real work doesn't double-count it. Lens convergence
  (backlog #2) finished: `_dl_progress` and the `_refresh_totals`
  weekly-target block now call `matched_minutes`; `_burndown_series`
  routes through `day_index()` + `task_matches` (needs a per-day running
  sum, which `matched_minutes` — a range total — doesn't return, so it's
  one call-site short of literally calling the shared function, but
  reads the same substrate through the same predicate); `_capacity_lines`
  converged transitively. Side effect: deadlines' `match` field now
  accepts comma-separated multi-keyword matching, same as Goals/SIGNAL.
- **v6.7**: deadlines can point at a goal (dropdown), the linked goal's
  "why" shows next to the deadline in the dashboard and burn-down title.
- **v6.8** (real bug, found via the user's actual diary file, not
  guessed): TODO:/SOMEDAY: auto-capture had NEVER worked, because every
  bullet the user actually typed had no space after the dash
  ("-THESIS") and the parser required one — fixed, with a `(?!-)` guard
  so the app's own "---" decorator lines don't get mistaken for bullets
  (a real regression caught in testing before it shipped). Same-line
  "TODO: text" now also works. Capture moved onto the live 10s autosave
  (same-day, not just at rollover/theme-save) with a status-bar
  confirmation; a one-time 14-day backfill on launch recovers writing
  the old parser missed. Also fixed: Tasks window's leftmost priority
  column silently ate row selection on click (the natural place to
  click to select a row for Done/Start), because refresh() rebuilds the
  tree and drops selection — now preserved. Audited the user's real
  settings.json end-to-end (goals, deadline-goal links, dashboard
  render) — all correct; 3 of 4 goals show "nothing in 14 days"
  including Thesis, which is accurate, not a bug.
- **v7.0** (the day file becomes provably the source of truth):
  `parse_day_file_to_rows()` is the exact inverse of `event_line()` —
  given a day file's own Start/Stop/Task lines, it reconstructs the
  work/break csv rows that produced them (handles a session that runs
  past real midnight correctly: the Stop line embeds the next calendar
  date even though it belongs to this effective day's file — the day
  only rolls at the configurable rollover hour, not midnight). Tools >
  "Rebuild sessions.csv from day files…" wires this up as a backup-first
  recovery tool — "the day file is the source of truth, csv is a
  derived cache" stops being a design principle nothing exercises and
  becomes something you can actually do. Tasks link to deadlines too,
  not just goals (same dropdown pattern, own column; right-click any
  row to set/change its goal or deadline after the fact — auto-captured
  items land with neither set). Life dashboard becomes a tabbed home
  (Today & Week / Deadlines & Goals / Insights, built by splitting
  `_dashboard_lines`'s existing output on its own section headers — zero
  risk of new computation bugs, pure layout change) plus a hub row
  linking to every detail view; nothing was deleted, each still holds
  unique detail the condensed tabs don't. File > Import life record
  (JSON) restores goals/deadlines/capacity (merged by name, never
  replaces existing) and day files (only ones missing locally, never
  overwrites current work) from a previous export — paired with the csv
  rebuild for a full, lossless recovery path.
- **v7.1**: Week plan / capacity, when overbooked, states a priority
  order (most-urgent-first allocation of the shared pool) instead of
  just an aggregate ⚠ — first tier of the planning engine.
- **v7.2**: the "not today's signal" status flag checks whether the
  active task matches a GOAL even though it's off-signal — "not
  today's signal, but counts toward: X" instead of a bare warning.
- **v7.3**: the day timeline paints goal-aligned-but-not-signal work
  (a run, when today's signal is thesis) in a third color — signal /
  goal-aligned / plain-work are three buckets, not a binary (see the
  "signal vs. maintenance" design note above). New day headers get a
  "focus order today" block when 2+ scoped deadlines compete — second
  tier of the planning engine.
- **v7.4** (Insights v3): weekday pattern (needs every weekday
  represented, n≥3, before it speaks), meeting-load vs deep-hours,
  break-ratio drift — all reuse existing data, no new sources.
- **v7.5**: focus order names the uncommitted hours — when slack
  remains after deadlines are fed, points at signal-priority Task
  library items instead of leaving leftover capacity unexplained.
- **v7.6** (readable diary, pure view layer): syntax highlighting in
  the diary Text widget — day headers bold, SIGNAL/ENERGY/TODO/WEEK
  REVIEW headers bold green, themed-writing blocks purple, warnings
  red, raw `Start;`/`Stop;`/`Reset;` bookkeeping lines small grey,
  free-typed text untouched. Tools > "Hide raw timer lines" folds the
  raw event lines out of view entirely via Tk's `elide` tag option
  (zero rendered height, not just invisible) — verified the file on
  disk stays byte-identical regardless of fold state, this is
  presentation only. On the user's real file: 255 lines, 35% raw
  events — folding shrinks the visible document by a third. Prompted
  by a direct complaint ("messy to read... ass to scroll") — the fix
  respects design rule #1 (day file is the app) by changing nothing
  about the file, only how Tk renders it.

## BACKLOG (priority order — continue here)

1. ~~Dashboard as home~~ — DONE v7.0, but as a HUB not a replacement:
   became a tabbed window (Today & Week / Deadlines & Goals / Insights)
   with a button row linking to every detail view (weekly, monthly,
   trend, health, heatmap, burn-down) — none were retired, each still
   holds unique detail (full per-day/per-task tables, the 8-week chart)
   the condensed tabs deliberately don't replicate. Revisit actual
   retirement only if the user says a specific standalone window has
   gone unused for a while.
2. ~~Finish the lens convergence~~ — DONE v6.6: `_dl_progress` and the
   `_refresh_totals` weekly-target block now call `matched_minutes`;
   `_burndown_series` routes through `day_index()` + `task_matches`
   (needs a per-day running sum, which `matched_minutes` — a range
   total — doesn't return, so it's one call-site short of literally
   calling the shared function, but reads the same substrate through the
   same predicate). `_capacity_lines` converged transitively (it only
   ever called `_dl_progress`). Side effect worth knowing: deadlines'
   `match` field now accepts **comma-separated multi-keyword** matching,
   same as Goals/SIGNAL — was previously a single substring only.
   ~~Link the faces~~ — DONE v6.7: deadlines carry an optional `goal`
   field (dropdown of goal names in the Deadline dialog, `_goal_why`
   resolves it); the linked goal's one-line "why" now shows next to the
   deadline in the dashboard's DEADLINES section and in the burn-down
   window title — seeing WHY next to WHEN. SIGNAL already seeded from
   goals (v6.2). Still open: task-library items only link to a goal, not
   a deadline (see 2c below); no reverse view yet ("which deadlines/
   tasks point at this goal" from the Goals dialog itself).
2b. **Themed writing v2** (v1 done in v6.4): progression view could diff
   or highlight changed stance between entries on the same topic ("your
   thinking on X shifted here"); consider a lightweight `#tag` alternative
   for one-line mentions that don't deserve a whole popup session (the
   user floated this as option A before picking C — still cheap to add
   alongside, not a replacement). User asked whether the writing popup
   should show old entries inline while continuing a topic — declined for
   now, Browse Themes open in a second window already covers it; revisit
   only if that workflow proves annoying in practice.
2c. **Task library v2** (v1 done in v6.5, deadline-link done in v7.0 —
   right-click a row to set/change goal or deadline). Still open:
   priority is a flat 3-state cycle; if the user wants more granularity
   later (a 4th state, or per-goal color) extend `_PRI_ICON`/`_PRI_NEXT`,
   don't add a parallel priority concept. Auto-capture now also fires on
   the live 10s autosave (v6.8), so same-day main-diary TODOs land
   within seconds — the "won't be captured until rollover" limitation
   noted here originally no longer applies, only themed-writing-save and
   rollover triggers remain relevant to keep in mind for edge cases
   (e.g. a TODO written and the app closed within 10s, before an
   autosave tick fires).
3b. **Screen-time / doomscroll source**: the 19–21 window is documented;
   import phone screen-time (csv drop like health) → new day-record key →
   insight "scroll vs next-day energy".
4. **Mood ≠ energy**: optional second header line or extend ENERGY with a
   word ("ENERGY: 3 anxious") — parse the word, correlate.
5. **Money source**: monthly csv drop (bank export) → spend per day key;
   balance section gains a cost line. (User hinted "total life".)
6. ~~JSON import/restore~~ — DONE v7.0, honestly scoped: File > Import
   life record restores settings (goals/deadlines/capacity, merged by
   name) and day files (only ones missing locally) from an export; it
   deliberately does NOT try to rebuild sessions.csv from the JSON's
   per-day aggregates (lossy — no individual start/end times survive
   aggregation). Pair with Tools > Rebuild sessions.csv from day files
   (also v7.0) instead, which reconstructs losslessly from the restored
   day files' own event lines. Import → Rebuild is the full, lossless
   recovery path — not a single "import" button doing both silently.
7. **Multi-machine**: settings/diary already OneDrive-able; document a
   two-PC setup properly (single-instance mutex is per-machine).
8. ~~Insights v3~~ — DONE v7.4: weekday pattern (needs every weekday
   to have n>=3 samples before it speaks — won't fire until real
   history accumulates), meeting-load vs deep-hours ("meetings are
   eating your focus" / "holding up fine"), break-ratio drift (this
   week vs the 3 weeks before). All reuse existing data, no new
   sources.
9. **Deliberately NOT NOW — from the user's career/life-context chat,
   2026-07-13.** A separate long-running chat that holds career-planning
   context proposed three ideas, explicitly self-aware that shipping them
   should wait: "the app will still be v6.7 next week; the thesis
   deadline won't wait" (9 days out, zero words at time of writing). Do
   not build these until the user asks again post-draft.
   - **Reopening Guard / Decision Ledger**: a `decide: <keyword>` task
     type — on Stop, prompts for verdict + reason, stored locally; future
     matching tasks show a banner with the original date/verdict/reason
     and a reopen counter, requiring typed new-data justification to
     unlock. Real named settled-decision seed data was provided (retake-
     a-course, paid application services, accept-then-quit, spray
     applications — all previously decided NO/SKIP). **Flagged by its own
     author as adjacent to the drift-prompt/priority-gate this app has
     twice deliberately held back** (see the `⚠ not today's signal`
     status flag, v6.5, and the standing "only if the meter fails"
     decision from 2026-07-11) — if revisited, explicitly re-check
     against that precedent rather than building a second gating
     mechanism side by side with the first.
   - **Opportunity triage capture**: a `consider: <opportunity>` capture
     landing in the task library as a low-priority someday item,
     deliberately not actioned same-day — a holding pen for FOMO pulls
     toward new offers. Same shape as SOMEDAY: already is; may not need
     new code beyond documenting the convention, similar to how SOMEDAY
     itself turned out to be nearly free in v6.4.
   - **Blunt capacity-shortfall line**: on rollover, one hard sentence in
     the day file if required hours for the nearest deadline exceed net
     capacity — "something gets cut," not a soft nudge. Check first
     whether `_plan_line`/`_capacity_lines` already compute this and just
     need harder-line presentation rather than new math — likely the
     latter, since `_capacity_lines` already produces a "⚠ overbooked by
     Xh" verdict; the ask is about surfacing it in the day file's morning
     plan line, not inventing the number. **Update 2026-07-13: partially
     done as of the capacity-conflict-prioritization work below** — that
     is plain math over already-computed numbers (not the Reopening-
     Guard-style relitigating/FOMO gate the career chat was actually
     warning against), so it shipped; re-check against the career chat's
     framing before adding anything that asks the user to justify or
     confirm a decision, which is the part that's still deliberately held.

10. **Recovered from old version-history "still open" notes that never
    got promoted to this list — a real gap the 2026-07-13 audit found,
    not new ideas:**
    - **Weekly report generator, AI-written.** Different from "Copy for
      AI review" (manual copy-paste, exists since v5.x): this would call
      an LLM API automatically (Friday, on rollover, or on demand) with
      the week's consolidated data and write the response INTO the day
      file as a real paragraph, not just prep the clipboard. Needs an
      API key stored somewhere (`settings.json`? a separate untracked
      file, given CLAUDE.md's OSINT sensitivity around what's committed)
      and a stdlib-only HTTP call (`urllib.request`, no `requests` dep).
      Real design question before building: does an API key belong in
      settings.json at all, given that file is OneDrive-synced and
      partially exported via the JSON life-record export? Probably needs
      its own gitignored/unexported file. Ask the user before touching
      this — it's the one item here with a real credential-handling
      decision attached, not just code.
    - **Real bed/wake times for the sleep band** (currently estimated —
      `_sleep_band`, v5.4 — or manually overridden — `_set_sleep_override`,
      v5.6). Health Auto Export (the paid app recommended to the user
      back in the health-automation research) exports actual sleep-phase
      start/end times, not just a daily total; the free FUNN Media app
      currently in use only gives totals. No code change possible until
      the user's actual data source changes — revisit if they switch
      apps, don't build speculatively against a format that doesn't
      reach this machine yet.
    - **`.ics` recurring-event (RRULE) expansion.** `parse_ics_busy`
      (v5.9) explicitly skips RRULE events — stated as a known limitation
      at the time, never revisited. If the user's real calendar leans on
      recurring meetings (a "very booked" calendar, per their own words,
      plausibly does), capacity numbers are undercounting busy time.
      RRULE expansion (even just weekly/daily, skip the gnarlier
      monthly/yearly cases) is a real, scoped, stdlib-only task — the
      `icalendar` PyPI package would make this trivial but violates the
      no-dependencies rule, so it's a manual RRULE parser, which is
      fiddlier than it sounds (UNTIL/COUNT bounds, BYDAY lists, timezone
      handling). Medium effort, real payoff if the calendar sync (v5.9,
      still advisory-only per the 2026-07-13 Outlook research) actually
      gets set up.
    - **Per-task-category estimate factor.** `_estimate_factor` (v5.8)
      returns ONE global actual/estimate multiplier across every
      finished task. Splitting by category (the `project:` prefix
      convention already used elsewhere — Data doctor, category totals
      in `_summary`) would be more honest: "thesis-type tasks run ×2.4,
      admin-type tasks run ×1.1" is more useful than one blended number.
      Needs enough Done-lines per category to be meaningful (n≥3, same
      honesty gate as everywhere else) — likely not enough data yet;
      revisit once the task library (v6.5+) has accumulated more Done
      history.

11. **Planning & recommendation engine — the user's 2026-07-13 ask,
    "daily/weekly/monthly recommendations... calendaring... planning my
    time and schedules."** This is a real, coherent NEW direction, not a
    tweak to something existing, and deserves a full design pass before
    a big build — logged here in detail so a future session doesn't
    start from zero. Important framing up front: this repo is stdlib-only
    (design rule #2), so "ML" in the literal sense (numpy/sklearn/a
    trained model) is off the table — everything here has to be honest
    rule-based heuristics, which is genuinely how most calendar apps'
    "smart suggestions" work anyway, not a downgrade.

    **What already exists that this would build on** (don't rebuild):
    `_dl_progress` (needed-h/day per deadline), `_day_capacity`/
    `_avail_hours` (net capacity per day, calendar-aware since v5.9),
    `_capacity_lines` (slack/overbooked verdict across all deadlines),
    `_plan_line` (today's needed-vs-available one-liner in the day
    header), the task library's `priority`/`goal`/`deadline` fields
    (v6.5, v7.0) and `est_h`. A real recommender is mostly a NEW VIEW
    over data that's already computed, not a new data pipeline —
    matches the concept model's own "sources/lenses/views" shape (see
    above): this would be a view, arguably the most important one.

    **The one real infrastructure gap**: `parse_ics_busy` (v5.9) returns
    `{date_iso: total_busy_hours}` — a per-day SCALAR, not actual time
    RANGES within the day. A genuinely gap-aware scheduler ("you're free
    09-11 and 14-17") needs interval-level busy data, which means
    extending `parse_ics_busy` (or a sibling function) to return
    `{date_iso: [(start_time, end_time), ...]}` instead of a sum. This
    is the prerequisite for the ambitious version below; the modest
    version doesn't need it.

    **Three scopes, cheapest first — pick one, don't build all three
    at once:**
    a) ~~Priority ordering when capacity is scarce~~ — DONE v7.1, in
       `_capacity_lines`: when total needed-hours across active
       deadlines exceeds net capacity, states explicitly which is fully
       funded and which takes the cut, by how much.
    b) ~~Suggested focus list~~ — DONE v7.3 + v7.5: new day headers get
       a "focus order today" block when 2+ scoped deadlines compete —
       most urgent first (behind-pace overrides a merely-sooner due
       date), each with its needed h/day, plus (v7.5) a final line
       naming signal-priority Task-library items when slack remains
       after the deadlines are fed. Matches the original sketch fully
       now.
    c) **True time-blocked schedule** ("09:00-11:30 Thesis, 11:30-12:00
       email [boxed]...") — needs the `parse_ics_busy` interval upgrade
       above to respect WHERE in the day meetings actually are, not just
       how many hours they consume. Bigger lift; (a) and (b) are done —
       revisit whether they're enough before reaching for this.

    **Guardrail, matching the career-chat prompt's caution (item 9
    above) even though this is a different feature**: a recommendation
    is a VIEW the user glances at and either follows or ignores — it
    must never become a thing they configure, tune, or negotiate with
    (no "accept/reject suggestion" UI, no learning-from-rejections
    loop, no separate settings panel). If it starts accumulating its own
    options and toggles, that's the signal it's turned into a grooming
    surface and should be cut back to something that just states a
    recommendation in the day file and moves on — same pattern as the
    morning verdict, which works precisely because it's not interactive.

## How to verify changes without Windows

Extract pure functions via ast and test them (pattern in previous
sessions): seed a messy csv (v4 rows, case variants, dups, junk,
overlaps), test `read_rows`/`day_index`/`_doctor_scan`/`_insight_lines`/
`_sleep_h`/`_energy_from_text` with stubbed `self`. Always
`python3 -m py_compile` the app file. The tkinter surfaces need a real
run on the user's Windows machine (Ctrl+D dashboard, Data doctor scan).

## Git

Private repo `econjp/chrono`, all work happens directly on `master` —
no other branch is active. (A mobile-session branch,
`claude/life-management-platform-arch-*`, was cherry-picked into master
and re-authored on 2026-07-12; see CLAUDE.md incident log. It may still
exist on origin as a harmless leftover pointer — safe to delete, not
urgent.) Commit style: short imperative title + honest body listing
user-visible changes first. No AI co-author trailers, ever (CLAUDE.md).
