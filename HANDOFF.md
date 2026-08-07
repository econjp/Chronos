# HANDOFF — TimerDiary / Life Management Platform

Paste-able project brain. Any new session, agent, or development platform
should read this file first; it replaces re-explaining the vision.
**Keep it updated in the same commit as the feature it describes.**

## If you are Claude Code running via GitHub / mobile — read this first

This repo has no committed `CLAUDE.md`. The maintainer keeps a private,
gitignored one on their main machine with personal context (data
locations, past incidents, working style) that never leaves that
machine — it is deliberately not here. If you're working from a mobile
session or a fresh GitHub checkout, this section stands in for it. A
few hard rules, learned from a real incident, not theoretical caution:

1. **No AI co-author trailers, ever.** No `Co-Authored-By: Claude`, no
   `Claude-Session:`, nothing identifying a commit as AI-authored.
   Plain commit messages: short technical subject, first line says
   what changed and why, humble tone. This is a standing, explicit
   rule — a past mobile session violated it, and every one of its
   commits had to be cherry-picked and re-authored by hand before they
   could touch `master`.
2. **Never push to or merge into `master` directly.** Work on a clearly
   named branch (e.g. `claude/short-topic`). The maintainer reviews,
   audits, and merges by hand from their main machine — don't
   fast-forward or merge-commit your own branch in yourself, even if
   the diff looks clean.
3. **Keep it small.** 1-3 commits, one well-scoped item — ideally
   something already described in this file's BACKLOG section below,
   not a new architectural direction improvised on the spot. A mobile
   session doesn't carry this project's full working history in
   context; picking a pre-scoped item is much safer than inventing
   scope.
4. **Never commit personal data.** Only touch `timerv2/*.py`,
   `HANDOFF.md`, `README.md`, and repo config (`.gitignore`, etc.).
   Never create, reference, or paste in a commit the contents of any
   diary/day-file text, health export, calendar export, or anything
   resembling a real name, email, or personal detail — even in a
   commit message or code comment. If unsure whether something counts
   as personal data, leave it out.
5. **Preserve the format rules.** The day-file's own text format
   (`Start;`/`Stop;`/`Reset;` lines, `--- Task:` etc., see "Repo map &
   data formats" below) must never change — it's the actual product,
   not a log. stdlib only, single file (`timerv2/timer_diary_v5.py`),
   no new pip dependencies, ever.
6. **Leave a clear trail.** The next laptop session won't have this
   conversation's context either — write commit messages and a short
   PR/branch description that explain exactly what changed and why, as
   if handing off to a stranger, because you are.

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

## Data architecture for the long term (owner asked 2026-07-14: "won't we realise in 6 months we should have logged more?")

Worth a direct, permanent answer since it's a recurring anxiety, not a
one-off question. Short version: **the architecture is already built so
that regret is cheap, and v8.27 made the one remaining gap cheap too.**
The reasoning, so a future session doesn't re-derive it:

1. **The day record is a VIEW, not the source of truth — this is the
   whole trick.** `_life_day`/`day_index` are recomputed on demand from
   the RAW sources (sessions.csv, day-file text, the health-folder CSVs,
   the .ics file). Nothing is baked into a fixed schema at write time.
   Consequence: if a source's parser gets WIDENED tomorrow to read a
   column it ignored before, every past day whose raw file still has
   that column backfills automatically, for free, no migration. This is
   exactly what happened in v8.27: `parse_health_dir` started reading
   mindful-minutes/RHR/HRV/weight columns that may have been sitting in
   the user's already-exported CSVs unread the whole time.
2. **Two genuinely different kinds of "missing data," two different
   fixes — don't conflate them:**
   - *A source already reaches the machine but the parser doesn't read
     every column it could* (health export, calendar, a bank csv). Fix:
     widen the existing parser generically (v8.27 did this for health).
     Zero regret possible here except the delay before someone widens
     the parser — and it backfills retroactively per point 1.
   - *Nobody ever wrote the fact down anywhere* (a subjective state, a
     habit, a one-off event). This is the ONLY case with real,
     unrecoverable regret — no parser can invent a fact that was never
     recorded. The fix is not to guess every future variable in advance
     (that violates the standing no-speculative-sources rule — see the
     "Real bed/wake times" backlog note: don't build against a format
     that doesn't reach the machine yet) — it's to make the COST of
     starting to log a NEW thing, the day it's actually wanted, as close
     to zero as possible. **METRICS (v8.27) is that mechanism**: one
     generic `key=value` line, one parser, works for any future metric
     with no new code. SIGNAL/AVOID/ENERGY/mood each needed their own
     bespoke one-line parser as a new axis came up over eight versions;
     METRICS is the generalisation of that pattern, done once.
3. **The portability safety net already exists.** File > Export life
   record (JSON) serialises the full day record + diary text + settings.
   If the record's shape ever needs a real restructuring later (not
   just a new key), the whole history round-trips through that export —
   sensor/parsing work never has to be redone from raw files, only the
   shape of what's already been extracted.
4. **Practical checklist for "should I capture X":** is X already
   reaching the machine in some file (a phone export, a calendar, a bank
   statement)? → widen that source's parser generically, don't wait to
   be asked for the specific field. Is X something only the person knows
   (a feeling, a habit, a supplement)? → it's already free via METRICS;
   type it under whatever key name makes sense, no code needed. Is X a
   format that doesn't exist on this machine yet (e.g. sleep-phase
   times, which need a paid app the user hasn't switched to)? → correctly
   NOT built yet, per the existing precedent; revisit only when the real
   file shows up.

**The health-hub direction, concretely.** The owner floated turning the
app toward biohacking/health (meditation etc.) and "combining into the
diary." That's not a new direction bolted on — METRICS + the wider health
import ARE that pivot, using the existing architecture: the day file
already holds SIGNAL/AVOID/ENERGY next to free-typed diary text; METRICS
takes the same slot for meditation, water, caffeine, supplements, cold
exposure, anything — one line, no second app, no new settings dialog.
RHR/HRV/weight now ride along from the same health-export folder already
configured, and DONE as of v8.36: `_health_extras_lines` surfaces all of
it (mindful/RHR/HRV/weight/daylight) as more than one header line. Still
open: a readiness-style insight once real HRV/RHR history accumulates
(backlog #68) — deliberately gated on real data existing first.

**2026-07-14 follow-up session, answering "are we REALLY collecting all
the data we could."** Two moves, both shipped the same session: (1) a
brand-new SOURCE that needs no export file and no typed line at all —
**daylight** (v8.28, `day_length_hours`, pure astronomical math from a
latitude) — proof that "more data to capture" doesn't only mean widening
existing importers, it can mean noticing a computable fact was never
being asked for. (2) **word drift** (v8.29) — the realisation that the
diary's free-typed prose had been FULLY collected the whole time and
never read as itself, only mined for TODO/SOMEDAY bullets; the "we forgot
to capture X" anxiety sometimes resolves to "we captured it, we just
never looked." Both directions matter for the same question: before
building a new importer, check whether the fact is (a) already sitting in
a file nobody's parsing fully yet, (b) computable for free from data
already known (date, latitude, a diary line), or (c) genuinely something
that has to be typed — METRICS makes (c) nearly free too, so the honest
remaining gap is narrower than it feels.

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

**Addendum, v9.0 (2026-07-29):** `SIGNAL2:` (backlog #96, tiered
priorities) was checked against this precedent before being built and
does not violate it. It is a fourth, DISJOINT bucket (a discrete
tier-2 ranking), not a blend of tier-1 — a task matching both tiers
counts as tier-1 only, and tier-1's own percentage is computed exactly
as before, untouched by SIGNAL2 existing. If a future ask wants
tier-2 folded INTO tier-1's number ("just count it all as signal"),
that's the same rejected compromise as maintenance-as-signal and
should get the same answer.

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
  `idle_min`, `float_break`, `nudge`, `asked_autostart`, `daylight_lat`
  (v8.28, a single float degrees, absent = source off), `domains`
  (v8.4), `pull_min` (v8.10).
- Day-file conventions parsed by code: `SIGNAL: kw, kw` (carries daily,
  seeds from goals if blank), `AVOID: kw, kw` (v8.13, the inverse lens,
  carries daily, no goal-seed), `ENERGY: 1-5` optionally + a mood word
  ("3 anxious", v8.23), `METRICS: key=val, key=val` (v8.27 — the generic
  logging line, see the data-architecture section above; ANY future
  personal metric, no new parser needed), `TODAY: 4h` / `TODAY: sick`
  (v8.16, declares a short day), `TODO:`/`SOMEDAY:` headers with
  `-`/`*`/`[ ]` bullets (TODO carries to next day AND auto-captures into
  the task library; SOMEDAY never carries, library-captures only),
  `--- Done: task (est Xh, actual Yh)`, `--- Task:`, `!!! time-box
  exceeded !!!`, session/break lines, `WEEK REVIEW Wnn:` (Mondays),
  `=== THEME: name — HH:MM (Xm) === ... === END THEME ===` (themed
  writing blocks, read back out by Browse Themes — never a second file).
- The day record (`_life_day`) as of v8.28: `work`/`brk`/`tasks` (csv),
  `signal`/`energy`/`sleep_h` (existing), `workout_min`/`steps`
  (health import), `mindful_min`/`rhr`/`hrv`/`weight_kg` (health import,
  v8.27 — opportunistic, only present if the export CSV has the column),
  `metrics` (dict from the METRICS line, v8.27), `daylight_h` (v8.28,
  pure computed, present only when `daylight_lat` is set), `busy_h`/
  `capacity_h`
  (calendar/week-plan). A new source is still always one new key here.
- **Export life record (JSON)** (File menu) is the canonical portable
  dump: per-day record + diary text + goals + deadlines + capacity.

## NORTH STAR — the major direction (owner asked 2026-07-13: "vision big things")

The owner's recurring feeling: lots of useful features, nothing yet that
feels *major* — not at the full potential of a "total life management
platform." This is the honest frame for the leap, and the lens for
prioritising the backlog below. **Don't build this whole thing in one
session** (it violates the mobile-session rules); build it one brick at a
time, but know which wall each brick is in.

**The reframe: from a MIRROR to a CO-PILOT.**
Today the app is an honest *mirror* — it reflects what happened,
cross-referenced, without flattery (verdicts, insights, the v8.2
trajectory line). That's necessary but it's still backward- and
present-looking, and passive. The full-potential version is a *life
co-pilot*: it holds what you're aiming at, models your real patterns and
capacity, looks FORWARD, helps you decide and remember at the scale of
years. Three pillars, each an extension of primitives that already exist
— not a rewrite:

**Pillar A — FORESIGHT (model the future, not just report the past).**
The app already computes needed-h/day (`_dl_progress`), today's
time-blocked schedule (v8.0 `_day_schedule_lines`+`_free_slots`) and, as
of v8.1, where ONE deadline actually lands at real pace (`_dl_projection`).
The leap: a **multi-week life simulation** across ALL deadlines + capacity
+ real velocity + health limits at once — roll today's `_free_slots` and
`_dl_velocity` forward N weeks, place every deadline's need, and surface
*collisions before they happen*: "weeks of Jul 20 & 27 are both overbooked;
at your real pace Thesis lands 5d late AND TUTA slips — here are two
reallocations that clear both." Still a VIEW, still rule-based, still no
negotiation UI (the standing planning-engine guardrail holds). Backlog
#11's tier-c is the seed; the new part is *many deadlines × many weeks ×
real (not assumed) pace*. **First brick DONE v8.3**: `_outlook_lines()` +
View > Outlook — all scoped deadlines projected at real pace, ranked by
lateness, with the aggregate "+Xh/day clears everything" lever. Next
bricks: fold in *capacity per future week* (not just aggregate rate) so it
places the shortfall in a specific week; then a light multi-week
`_free_slots` roll-forward so it can say *which* week overbooks.

**Pillar B — MEMORY (life at the scale of years, queryable + narrative).**
Every view still tops out at a season; v8.2's trajectory line is the first
crack past that. The leap: the archive becomes a **life memory** you can
ask and that can tell you its own story. Concrete, staged, all stdlib:
  1. #14 "ask your diary" — ranked multi-term search + "copy matching days
     for AI" (no credentials). Makes a year of day-files *queryable*.
  2. Trajectory v2 — extend v8.2 to per-goal and per-domain arcs over
     months ("Thesis 2→12h/wk over the term; the term you gave it, sleep
     fell 0.7h and workouts halved — the true price you paid").
  3. #15 year-in-review — the once-a-year long read.
  4. Eventually the AI-analyst layer (see connective tissue) writing a
     real narrative paragraph INTO the record, not just prepping clipboard.

**Pillar C — ALIGNMENT (life management, not time management).**
The deepest gap and the most on-vision. The app tracks *time*; a *life*
platform manages *commitments, decisions and values*. Two moves:
  1. **A values/domains layer above goals. — BRICK 1 DONE v8.4.**
     `domains()` (settings["domains"]: name/match/target_pct),
     `_domain_minutes` (reuses `matched_minutes`), `_alignment_lines`
     (8-week actual share per domain vs target, names the widest say-do
     gap), `_alignment_win` + `_set_domains` dialogs. The missing top of
     the source→lens→view stack now exists. Next bricks: (a) make it
     LONGITUDINAL — alignment this 4 weeks vs the prior 4 (is the gap
     closing or widening?), reusing the v8.2 trajectory split; (b) roll
     Body/Rest in from health (workout+sleep) and the waking-hours
     unaccounted block so it spans the whole life, not only tracked work;
     (c) surface the single widest-gap line on the dashboard. Watch the
     keyword-overlap caveat (percentages only add up if domains are
     roughly disjoint — the dialog warns, `_alignment_lines` guards the
     unmapped calc).
  2. **The decision ledger** (career-chat idea, backlog #9, currently held
     behind the anti-nagging guardrail — revisit deliberately, not as a
     second gate). A life platform remembers the big NO/SKIP decisions and
     their reasons so you stop relitigating settled things — tracking
     *decisions and their outcomes over time*, which is squarely "life
     management," not time-tracking. Keep it a VIEW/record, never a
     blocking negotiation, per the twice-held precedent.

**The connective tissue — an AI analyst layer.**
"Copy for AI review" (v5.1) is v0 of this: the whole record already
serialises to text/JSON. **v0.5 DONE v8.5**: `_life_review_lines()` +
`_review_bottom_line()` (View > Life review) compose all three pillars
into one briefing with a rule-based synthesized bottom line that reconciles
Foresight (slipping deadlines) and Alignment (starving domains) into a
single action — the pillars finally speaking as one voice, keyless. The
eventual v1 calls an LLM automatically and writes narrative feedback into
the day file; it carries the one real **credential-handling decision** in
this roadmap (API key vs OneDrive-synced settings.json — see backlog #10).
**Ask the owner before building the LLM version**; the rule-based synthesis
(v8.5) is the keyless proof it works, and the "Copy for AI second opinion"
button bridges to a real LLM manually in the meantime.

**How to use this section:** every backlog item below is a brick in one of
these walls — when picking the next thing, prefer the one that most
advances a pillar (A/B/C) rather than an isolated nicety. That is the
answer to "nothing feels major yet": the individual features are small on
purpose; the *walls* are the major thing, and they're now named.

### Reflection, 2026-07-15 — "many different features, bit scattered"

The owner named a real feeling after two mobile-session pushes landed
back to back (v8.16–v8.26 here, v8.27–v8.63 from mobile — 85 backlog
items, v8.64, dozens of Insights lines). Worth answering directly
rather than just shipping more, since the feeling is legitimate even
though the underlying architecture is not actually scattered:

**What's NOT scattered — checked, not assumed.** Every one of those
85 items is still a VIEW or an INSIGHT sitting on top of the same
handful of primitives: `day_index()` (the day record), `matched_minutes`/
`task_matches` (the one lens shape SIGNAL/AVOID/goals/domains/deadlines
all share), `_free_slots`/`_day_schedule_lines` (the scheduler), and
now `METRICS` (v8.27, the generic capture mechanism). Nothing added in
either push introduced a second way to do something the app already
does. Mapped against the three NORTH STAR pillars above, the two
pushes are legible, not random: v8.16–v8.26 mostly filled in FEEDBACK/
SELF-KNOWLEDGE gaps (declared short day, mood, best-weeks, thrash);
v8.27–v8.63 mostly built out MEMORY (word drift, ask-your-diary,
year rhythm, decision log, time capsule) and closed real FORESIGHT/
TRUST gaps (planner realism, lens overlap, sensor health, backup
integrity). The scatter feeling is about SURFACE AREA, not structure.

**What actually IS scattered, and what got fixed this round.** The
View menu had grown to 22 flat commands with three separators and no
grouping — a genuine "junk drawer," found and fixed in v8.64 by
grouping into submenus that mirror the pillars above (Planning /
Memory / Values), so the menu now reads as the architecture instead
of hiding it. `_insight_lines()` (Insights tab / Copy-for-AI-review)
is the one place still genuinely flat — 20+ independent insight
generators concatenated with no grouping or priority ordering. Not
fixed this round (a real design question — group by pillar? cap at
N lines? rank by how unusual/actionable each finding is? — deserves
its own pass, not a rushed one). Logged as backlog #86.

**The mechanism for what to prune next, going forward: don't guess,
measure.** v8.24's usage-pattern meter (Tools > "Feature usage…")
now exists specifically to answer "which of these 85 things are
actually earning their keep" with real data instead of another
guess — let it accumulate a few weeks of real counts, then the next
consolidation pass (menu trimming, Insights grouping, or an honest
"retire this" decision) should read that data first. This is the
standing answer to "are we building too much": the backlog stays
large because saying yes is cheap (small, honest, pure-view bricks);
what to actively surface or retire should increasingly be decided by
the owner's own usage, not by continuing to add without ever
measuring what's already there.

## Version history (one line each)

- **v8.27–v8.63** (a second mobile-session push, landed 2026-07-15 —
  37 commits, hand-audited: clean authorship throughout, zero AI
  trailers, zero OSINT hits, 45/45 selftest suites independently
  re-verified before landing). The headline architectural move is
  **v8.27, the health-hub pivot**: a generic `METRICS: key=value` line
  generalises the SIGNAL/AVOID/ENERGY/mood pattern (a bespoke one-line
  parser per new axis, eight versions running) into ONE parser for any
  future fact — meditation minutes, water, caffeine, supplements,
  anything, no new code per metric. See "Data architecture for the
  long term" below for the full reasoning. Everything else in this
  range is a real backlog item closed: daylight (a computed source
  needing no export file, v8.28), word drift + fade (the diary's own
  prose finally read as itself, v8.29/v8.37), ask-your-diary +
  pinned searches (v8.30/v8.46), lag correlations (v8.31/v8.38),
  week-ahead risk brief (v8.32), break budget + v2 weekday norms
  (v8.34/v8.39), **lens overlap check (v8.35 — backlog #48, matching
  the idea proposed here; the mobile session's version catches a
  sharper case than the original sketch — two DIFFERENT keywords each
  independently matching one task name, not just a keyword-string
  collision)**, health-hub view (v8.36), backup integrity (v8.40),
  running-hot index (v8.41), meeting fragmentation tax (v8.42), year
  rhythm map (v8.43), energy forecast (v8.44), weekly experiment
  engine (v8.45), decision log lite (v8.47 — correctly built WITHOUT
  #9's rejected reopen-counter mechanics), annual theme (v8.48), goal
  lifetime ledger (v8.49), deadline post-mortem (v8.50) + renegotiation
  tracker (v8.51), weekly "one less" (v8.52), sensor health meter
  (v8.53), planner realism factor (v8.54), **screen-lock break
  detection (v8.55 — the owner's direct, repeated ask: Win+L now
  triggers the same break-offer dialog idle detection already used,
  via the `OpenInputDesktop` ctypes trick, fails open, a 30s floor
  against tap-and-untap noise)**, time capsule (v8.56), commitment-
  reliability ledger (v8.57), protected time windows (v8.58),
  milestones inside a deadline (v8.59), waiting-on/blocked tasks
  (v8.60), cost of yes (v8.61), conversation-ready status export
  (v8.62), focus signature (v8.63). Landed via the standing policy
  (individual cherry-pick --no-commit + fresh commit per commit, not a
  bulk merge) despite already being cleanly authored — the process is
  about the audit step, not just the end state.
- **v8.64** (View menu reorganized — the map matches the territory).
  22 flat commands grouped into submenus mirroring the NORTH STAR's
  own three pillars: Planning (foresight), Memory (the archive),
  Values (alignment), plus Writing/Reports for the practical extras.
  Dashboard/"What should I do now?"/Tasks stay top-level as the
  highest-frequency entries. Pure reorganization, zero behavior
  change — verified via a full menu-tree walk that no command was
  lost, not just a visual check. Direct response to the owner naming
  the felt "many different features, bit scattered" experience —
  see the reflection added to NORTH STAR below.
- **v9.12** (#125 + #126, owner's own "automate and make it so much
  easier" ask, 2026-08-07, DONE). #126: the Recurring commitments
  editor now suggests a Sleep row from real tracked data (median
  bedtime/wake over n>=10 real nights, wake proxied by each day's
  first logged activity) when none is declared yet — pre-filled and
  editable, never auto-saved, resolving the "auto-set" instinct #121
  deliberately left blank rather than guess. #125: a new grouped
  insight (`_commitment_drift_lines`, TIME & FOCUS) compares each
  declared commitment against what tracked data actually shows —
  Sleep against #126's own suggestion (so the two features can't
  quietly disagree), everything else against the day's first tracked
  work activity on the days it applies. Same "declared vs actual"
  honesty pattern as #47/#99, same >=30min/n>=10 gating shape as
  every other insight in this app.
- **v9.11** (toolbar calendar button + #124, owner's own ask,
  2026-08-07, DONE: "this scheduling or cal shuld have its own
  button in task bar"). A 📅 button in the main toolbar opens the
  Calendar view directly, always visible (compact mode doesn't hide
  the top bar), sharing the View-menu entry's own usage counter. #124:
  setting a task due date now runs `_due_date_feasibility_line` — an
  honest, non-blocking check reusing `_avail_hours` (already aware of
  #121's commitments, #114/#116's calendar events, #113's locked
  windows) — and surfaces a warning only when the numbers genuinely
  look thin, never blocking the save. Wired into both due-date entry
  points (#123's calendar right-click and the Tasks window).
- **v9.10** (#123, the other half of the original calendar-scheduling
  ask, 2026-08-07, DONE). Right-click a day in the calendar's month
  view → "Set task due date…" — a lightweight due-date field directly
  on task-library items, deliberately NOT a full scoped Deadline (no
  total_h estimate needed, doesn't clutter the deadlines list for a
  quick ad-hoc "done by X"). Tasks window gets a `Due` column
  (overdue = ⚠) and the same action via right-click, for anyone who'd
  rather not open the calendar. Month view shows a ⚑ marker on the
  due date itself. Cleanly split from #122 by granularity: week view
  (hour-precise) locks working windows, month view (day-precise)
  sets due dates — each action matches what its own view can actually
  resolve a click to.
- **v9.9** (#122, owner's own chosen interaction model, 2026-08-07,
  DONE). Right-click an hour cell in the calendar's week view → pick
  a deadline from the context menu → locks that exact hour for it —
  the interactive half of #113/#120 the owner asked for after seeing
  the read-only calendar view. `_week_click_to_slot` inverts
  `_draw_calendar_week`'s own layout math (now shared class
  constants so the two can't drift apart); locking itself reuses
  `lock_windows_to_ics` completely unchanged — a new entry point, not
  new export logic. Asked which interaction model (right-click vs
  drag-and-drop vs click-then-dialog) before building, rather than
  guessing — direct payoff from #103's earlier lesson about a wrong
  guess costing a full redo.
- **v9.8** (#121, owner's own follow-up, 2026-08-07, DONE: "realistic
  blocks... sleep, eating, work blocks... dont wanna fill my outlook
  with that... shuld ofc affect my DL calcs everythng"). Extended
  #50's protected-windows mechanism (same settings key, fully
  backward compatible) rather than building a parallel system: added
  a `Days` field (`_parse_weekdays`, "Mon-Fri" style) so a day-job
  block doesn't also eat weekend capacity, and midnight-crossing
  support for sleep — capped at a 14h wrapped span so a genuine typo
  (e.g. "15:00-14:00", 23h) still degrades to "ignored" rather than
  silently eating almost the whole day, preserving the pre-#121
  safety behavior the existing selftest suite already locked in
  (caught this BEFORE shipping by re-running that suite, not after —
  worth remembering as a case where a routine regression check found
  a real design gap, not just a mechanical break). `_protected_
  intervals`/`_protected_hours` becoming weekday-aware means #82's
  capacity model and #113/#118's `_free_slots`-based views all
  inherited the fix automatically, zero new capacity-math code.
  Rendered as a labeled background layer in #120's week view. Applied
  directly: owner's stated day-job (09:30-17:00) and morning-admin
  (08:30-09:30) hours, both Mon-Fri, from their own words in the
  request — sleep/grey-admin left blank, no concrete times given.
- **v9.7** (#120, owner's own follow-up, 2026-08-07, DONE: "proper
  monthly or weekly calendar views... event or stuff names there...
  similar to outlooks monthly setup"). View > Planning > "Calendar
  (week/month)…": a real Outlook-shaped week (hour grid, 7 columns,
  events at their real clock position) and month (date grid, event
  names per cell, "+N more" overflow) view, Prev/Today/Next + a
  Week/Month toggle. Two new parsers — `parse_ics_events`/
  `parse_csv_events` — keep each event's SUMMARY/Subject text instead
  of discarding it like the existing capacity-math parsers do;
  completely separate/additive, so #113/#114/#116/#118's tested
  behavior couldn't regress. Shows imported calendar events AND
  tracked work sessions together, both named, both at their real
  time. Deliberately read-only — the visual foundation #119
  (automated schedule building) would sit on top of, not that
  feature itself.
- **v9.6** (#118, owner's own ask, 2026-08-07, DONE: "calendar
  view... very simple... easier to visually inspect free slots").
  View > Planning > "Free-time forecast (calendar)…": one green/grey
  bar per day, next 3 weeks, green = free — `_day_forecast` +
  `_draw_forecast_bars`, both reusing `_free_slots` (so this view,
  #113's lock-window picker, and the day scheduler can never
  disagree with each other about what's actually free). Deliberately
  glance-only, no actions — matches the standing "views, never
  compliance-tracked actions" guardrail. Backlog #119 (automated
  schedule building — auto-drafting a placement across ALL deadlines
  over multiple days, not just today) logged as the owner's own
  follow-on idea, explicitly flagged as a future project, not built
  this round.
- **v9.5** (#116, owner's own ask for a redundant path: "try to build
  also other ways to integrate calendar," 2026-08-07, DONE). A second,
  independent calendar source alongside #114's subscribe-URL: File >
  "Import calendar CSV (Power Automate export)…", for when Outlook
  won't publish a calendar link at all (external sharing disabled by
  tenant policy — researched via web search, a common EDU/work-tenant
  restriction, distinct from and more commonly blocked than standard
  Power Automate connector access). `parse_csv_busy_export`/
  `csv_busy_data` mirror the .ics parsers' exact output shape, so
  `_busy_data`/`_busy_intervals` just dispatch by file extension —
  every capacity view (`_free_slots`, #113's lock windows,
  `_capacity_lines`) already works with any of the three sources
  (local .ics, subscribe URL, CSV) with zero further changes. Manual
  Power Automate flow setup is a genuinely user-side task (no-code,
  in Microsoft's own UI) — documented step-by-step in
  `private-recommendations/calendar-integration-setup.md`
  (gitignored, not this file, since it's personal how-to, not
  architecture).
- **v9.4** (#114, closing the gap v9.3 immediately surfaced, 2026-08-07,
  DONE — owner's school/uni Outlook tenant, used for everything
  personal too). File > "Subscribe to a calendar link (.ics URL)…":
  `resolve_ics_source` lets `settings["ics_path"]` be a local file
  (unchanged) or a publish/subscribe URL, resolved to a local cache
  (`data_dir()/calendar_cache.ics`, refreshed every 60min) before
  `parse_ics_intervals`/`parse_ics_busy` ever see it — neither of
  those changed at all. Failed refresh keeps serving the last good
  cache rather than going blank; a link that's never worked signals
  failure so `_set_ics_url` can report it clearly (validated by an
  actual fetch + content check before saving, not just a URL-shape
  check). Chosen over Microsoft Graph API sign-in as the FIRST thing
  to try — no login/token complexity, works for personal-tier
  accounts; Graph API is the documented fallback (see #115 below) if
  the owner's school tenant turns out to block calendar publishing,
  which many EDU tenants do — not built speculatively before knowing
  the simple path even works.
- **v9.3** (#113, owner's own top-priority ask, 2026-08-07, DONE).
  File > "Lock study windows for a deadline (.ics)…": `_lock_window_
  candidates` walks today through a deadline's due date, ranks each
  day by its single biggest contiguous free block (`_free_slots` —
  already prices in imported calendar busy time + protected windows),
  keeps 2h+ blocks. Pick which to lock, `lock_windows_to_ics` exports
  them as real calendar events (same flat-.ics shape as the existing
  week-export) for Outlook/Google Calendar import. Exporting appends
  a visible day-file trace from day one — #112's principle applied to
  a brand-new feature rather than retrofitted. Ranking deliberately
  kept simple (biggest block wins, no peak-hour weighting) after
  direct feedback that the .ics mechanics aren't the hard part and
  the picker shouldn't be over-engineered. Tested: ranking order,
  threshold filtering, malformed/past-due deadlines degrade to no
  candidates not a crash, and — the actual point — a real imported
  .ics busy block correctly shrinks/removes that day's candidacy.
- **v9.2** (two small high-priority fixes, 2026-07-29, DONE). #109:
  `_carry_signal`'s fallback now seeds from the single most-urgent
  scoped deadline (`_focus_items`' own ranking) instead of blending
  every goal's keywords — a real morning's confusion traced directly
  to the diffuse blend, even though the day's own plan line had
  already named the urgent deadline. Falls back to the all-goals
  blend only when no deadline is scoped. #83: the status export now
  reports the current milestone ("Currently on ch5, 60% of its
  hours") instead of a bare date when a deadline has a milestone
  breakdown — `_milestone_progress_line`'s credit math factored out
  into `_milestone_credit`, shared by both the internal and external-
  facing renderings so they can't drift apart. selftest.py's `METH`
  extraction set updated to include the new shared method — a
  mechanical step easy to forget when factoring out a helper.
- **v9.1** (two follow-ups from v9.0, 2026-07-29, DONE). #105: a 5th
  timeline color (`TL_SIGNAL2`) so tier-2 matched time is visually
  distinct from plain work, same priority order as the text metrics
  (tier-1 > tier-2 > goal-aligned > plain work). #106: Data doctor
  gained a header-line adoption report — which of the ~12 optional
  header conventions actually got used in the last 60 days, reusing
  `_line_ever_used`'s own logic (refactored into a shared
  `_line_usage_count` core so the bool-check and the count report
  can't drift apart). Both small, both fully tested, zero regressions.
- **v9.0** (FLAGSHIP, 2026-07-29, DONE — the owner's own call: "this
  update shuld be rly a major update... v9 makes sense"). Two real
  additions to the core data model, not connective fixes:
  **#96, tiered SIGNAL** — a new `SIGNAL2:` header line, a second
  DISCRETE priority tier. Deliberately checked against the "Signal vs.
  maintenance" precedent (resolved 2026-07-13) before building: SIGNAL
  keeps meaning exactly what it always meant (today's ONE sharpest
  priority, the headline honesty number, completely untouched);
  SIGNAL2 is a strictly disjoint second bucket — a task matching both
  tiers counts as tier-1 only, so tier-1 is never diluted by tier-2
  existing. This is a discrete ranking, not the rejected "50% signal"
  blend. Surfaces in the live totals line, tomorrow's yesterday-recap,
  and a new trailing-window insight (`_signal_tier_insight`, MOMENTUM
  & TRENDS, n>=5 declared days). **#100 (first half), declared work-
  block window** — a new `WORKBLOCK: HH:MM-HH:MM` header line for an
  externally-committed window (a day job): inside it, idle detection
  and the v8.55 screen-lock detector both wait ~3x longer
  (`_WORKBLOCK_IDLE_FACTOR`) before offering to log a break, since a
  quick meeting or email check during already-spoken-for time isn't a
  break the way it is outside it. #100's SECOND half (genuinely
  parallel/overlapping work) stays explicitly out of scope — flagged
  in the original backlog note as likely unsolvable honestly within a
  single-threaded, one-task-at-a-time timer; no fake 50/50 split
  invented. Both features are fully additive and hidden until first
  used (`_line_ever_used`, same gate as AVOID/YEAR) — a day file that
  never touches either line behaves byte-for-byte like v8.69. Help
  topic "SIGNAL, AVOID & WORKBLOCK" (renamed from "SIGNAL & AVOID")
  documents both. 45/45 selftest suites + dedicated new-feature tests
  (disjoint-bucket math, carry-forward, header gating, idle/lock
  threshold multiplication with an explicit outside-workblock control
  test) all green, zero regressions in the existing suite.
- **v8.69** (four backlog items in priority/value order, 2026-07-29,
  DONE). #82: fixed a real capacity-model inconsistency this session's
  own v8.58 protected-windows feature created — protected windows
  subtracted from the scheduler but not from `_day_capacity`'s
  separate aggregate-hours model, so the capacity dashboard and cost-
  of-yes preview kept counting a declared lunch/wind-down window as
  available. #84: cost-of-yes now surfaces pre-existing `blocked_by`
  task-library items under the same goal as the hypothetical deadline
  — connects v8.60 and v8.61, no new computation. #93: File > "Open a
  day file…" is a lighter in-app picker (recent-days Listbox + relative
  jump buttons, reusing the diary-read path) instead of going straight
  to the OS file dialog — the owner's own ask from 2026-07-19. #86: the
  Insights tab's 20+ independent findings, previously one flat
  undifferentiated block (the same wall-of-text problem v8.64 fixed
  for the View menu), now group under three theme sub-headers (TIME &
  FOCUS / ENERGY & BODY / MOMENTUM & TRENDS) tagged at the point each
  finding is generated — resolved as thematic grouping (design option
  (a) from the original backlog note), not severity ranking (option
  (b)), since no severity/actionability score exists yet; revisit if
  backlog #56's usage-meter data accumulates enough to rank by what's
  actually acted on. `_insight_lines()` stays a flat-string wrapper
  around the new `_insight_lines_grouped()` for the one caller (life
  review's top-3 excerpt) that doesn't need themes.
- **v8.68** (quick reference restructured, direct follow-up feedback
  on v8.67, 2026-07-29, DONE). Three changes: (1) moved from a new
  top-level Help menu into Tools > "Quick reference — what does this
  app do?…" — no new top-level menu. (2) Rebuilt as a real two-pane
  topic viewer (`tk.Listbox` of 13 topics + a `tk.Text` content pane
  that updates on selection) instead of one scrolling wall of text —
  the WinHelp/CHM shape the owner asked for by name ("og windows
  vibe"), plain tkinter, no new dependency. (3) Every topic expanded
  into real paragraphs explaining what each convention does and why,
  not just its syntax. `_HELP_TOPICS` is now a list of (title, body)
  tuples instead of one big string. Tested via a real menu invocation
  plus a simulated mouse click on a listbox row (a virtual
  `<<ListboxSelect>>` event doesn't dispatch headlessly without a
  running mainloop — needed `win.deiconify()` + click coordinates via
  `bbox()`, noted here since it'll trip up the next session that
  tries to test a Listbox binding the same way). Full regression +
  selftest.py (45/45) green.
- **v8.67** (Help menu — a quick reference, owner's own ask,
  2026-07-29, DONE). New top-level Help menu (classic File/View/
  Tools/Help order) > "Quick reference…": one short, hand-written
  window — header-line conventions (SIGNAL/AVOID/YEAR/ENERGY/
  METRICS/TODO/DECIDED/CAPSULE/COMMIT/EXPERIMENT/TODAY), task-box
  shortcuts, the View menu's own categories, and an "easy to forget
  exists" list (prompted directly by the owner rediscovering the
  Decision log). Deliberately NOT auto-generated from the changelog
  and NOT meant to be rewritten every version — styled after the old
  Windows Help/About pattern the owner asked for, kept short on
  purpose. If a future feature changes one of these conventions,
  update this text in the same commit; otherwise leave it alone.
- **v8.66** (CRITICAL FIX + wall-of-text reduction, 2026-07-29, DONE).
  **`_carry_signal` was silently dead for anyone who never manually
  typed into SIGNAL**: it returned the moment it found a "SIGNAL:"
  line in yesterday's file, even blank — which is every day's line,
  auto-written since v6.1. The goal-seed fallback beneath it never
  actually ran once a single blank day existed, meaning every SIGNAL-
  dependent feature in the app (timeline color, the status-bar flag,
  best-weeks/mood/thrash/avoid-trend insights) had nothing to work
  with, silently, for as long as the owner never filled the line in.
  Fixed directly from the owner's own bug report ("all the recaps...
  signal ratio... always empty"); a blank-but-present line now falls
  through to goal-seeding exactly like a missing line always did.
  Also: AVOID/YEAR/METRICS no longer print unconditionally every day
  when never used — `_line_ever_used` checks the trailing 60 days
  before showing them (or shows them anyway if currently carrying a
  real value); SIGNAL/ENERGY stay unconditional. Direct response to
  "huge txt wall... not easily eye-able... I'm human not machine" —
  a first, scoped step; #86 (grouping the Insights tab itself) is the
  next piece of the same complaint, still open. Tested: the exact
  reported scenario reproduced and fixed, explicit-signal-carries-
  verbatim unaffected, no-goals-blank-line still correctly empty, and
  the three conditional-hiding scenarios (never used / historically
  used / currently live). Full regression + selftest.py (45/45) green.
- **v8.65** (bug fixes + two small features straight from the owner's
  own real data, 2026-07-29, DONE). **#97 fixed**: auto-capture no
  longer creates a duplicate task-library entry for every growing
  snapshot of a still-being-typed TODO bullet — `_add_task` collapses
  a same-source prefix-extension into the existing entry in place. The
  owner's real settings.json was cleaned with the identical logic
  (backup taken first): 77 → 34 entries, 43 stale duplicates removed.
  **Old bug report checked and closed**: task-switch-during-a-break
  time inheritance (2026-07-11) — not reproducible against current
  code. **#91 completed-task archive**: Done items now append to
  `settings["tasks_done"]` instead of being discarded. **#92 command
  shorthand**: `done: X` in the task box marks a matching task done —
  fixed-verb parsing, not #60's much riskier deferred console. **#99
  polish**: extreme deadline-projection lateness now reads "far
  behind — see the date" instead of an absurd triple-digit number,
  math unchanged. **New bug found, not fixed** (#101): Finnish ä/ö
  characters can get mangled upstream of the diary save — traced to
  the source day-file text itself (not settings.json handling, which
  is clean), likely Tk's Windows clipboard paste; needs live
  reproduction to pin down further. Full regression suite and
  selftest.py (45/45) green throughout.
- **v8.12** (procrastination pattern map — backlog #32). New
  `_procrastination_insight(days=60)`: maximal same-task work runs per
  day (rows sorted by start time); a run ≤10 min followed by a break is a
  bounce; ≥6 starts and ≥50% rate names the worst offender with the
  decomposition advice. Hooked into `_insight_lines` ahead of the break
  insight. selftest suite 12; 12/12 green.
- **v8.11** (re-entry ramp — backlog #34, completes the anti-
  procrastination arc with v8.10). `_reentry_opener(task)` picks the
  smallest concrete opener (related > signal > any, by estimate; TODO-
  bullet fallback skips machine lines); `_toggle` records
  `_last_break_secs` (reset on fresh starts); Working-status appends
  "start small: …" after 30m+ breaks. Known gap noted at #34: idle-logged
  breaks don't set `_last_break_secs` yet. selftest suite 11; 11/11.
- **v8.10** (breaks get teeth — backlog #30 + the owner's pull-back ask).
  `_pull_level(bsecs, pull_min, from_signal)` (pure, staticmethod) +
  pill escalation in `_update_pill` (two stages, beep once per stage,
  lift; only for breaks that interrupted a signal task — recorded at Stop
  in `_toggle`); Tools > "Break pull-back (signal tasks)…" sets `pull_min`
  (default 20, 0=off). NOT a lock — see the precedent note at backlog #30.
  `_break_insight(days=60)`: break-note keywords (move vs scroll buckets)
  paired with the next work block's minutes; one insight line, n≥5 per
  bucket; hooked into `_insight_lines` (textually adjacent to v8.2's
  trajectory hook — trivial conflict if 8.2 skipped in cherry-pick).
  selftest suite 10 covers both; loader now also lifts class attrs.
- **v8.9** (where you left off — backlog #27). `_last_context(task)`:
  most recent tracked day for the task via `day_index`, then the last
  human line after that day's final `--- Task:` marker (machine lines
  skipped via `_LINE_TAG_RULES`); surfaced in the Working status line and
  on Switch — 'last time (08.07): "…"'. Read-only, standalone (no deps on
  other branch commits beyond v8.0). selftest suite 9 covers marker
  priority, skip rules, no-history/empty/missing-file gates. Walkthrough
  table gains this commit; same audit rules apply.
- **(docs, no version bump)** `REVIEW_WALKTHROUGH.md` at repo root: the
  full landing guide for the main machine (pre-flight + policy-compliance
  commands, per-commit think-through with revert costs, Path A/B landing,
  smoke list, cleanup steps). Corrected the review kit's dependency map
  (8.5 needs 8.1–8.4, not just 8.1). Backlog gained #24–27 (running-hot
  index, planner realism factor, year rhythm map, where-you-left-off).
  Walkthrough file is scaffolding — deleted after landing.
- **(tooling, no version bump)** `timerv2/selftest.py`: committed,
  stdlib-only, cross-platform test harness — lifts pure logic out of the
  app via ast (no GUI import, sandboxed temp csv) and runs 8 suites over
  the v8.1–v8.8 tier. Replaces the per-session scratchpad test files that
  died with each container. `python timerv2/selftest.py`, exit 0 = green.
  Plus the BRANCH REVIEW KIT section below (per-commit Windows smoke
  checks + dependency notes for the hand-audit) and backlog #20–23.
- **v8.8** (energy-aware scheduling — backlog #17, the planner gets smart).
  `_hour_quality(days=60)` (0–1 per-hour profile of where work lands) +
  `_energy_place(items, slots, quality)` (each item claims its best-quality
  free time, most-urgent first, contiguous blocks). `_day_schedule_lines`
  now steers the hardest work into peak hours instead of the earliest gap;
  no-history path is byte-identical to v8.0. First upgrade to the PLANNER
  itself rather than a new view. Verified on Linux (peak-claim vs
  earliest-first divergence, shortfall, hour-quality profile).
- **v8.7** (right-now recommender — the day plan made real-time).
  `_deep_window(days=60)` learns your best 3h block from history;
  `_recommend_now(now=None)` reads current hour vs that window + the
  most-behind deadline (real pace) + today's energy + the 19–21 fatigue
  window and states one pick; View > "What should I do now?" shows it in
  the status bar (`_show_recommend_now`). Rule-based, `now` injectable,
  every branch verified on Linux. Complements the v8.0 morning schedule
  (static, whole-day) with a moment-to-moment call. Backlog gained 4 new
  ideas (#16 task-thrash meter, #17 energy-aware scheduling, #18
  commitment-reliability ledger, #19 frictionless quick-capture).
- **v8.6** (the co-pilot speaks first — proactive/attentive layer).
  `_anomaly_lines(weeks=10)`: deviations from the user's OWN baseline —
  worst/best sleep week vs the trailing weeks, days-since-last-touch for a
  declared domain/goal (neglect), trailing 0%-signal drought. Ranked,
  honesty-gated. `_copilot_note()` picks the single most important line
  (actionable risk from `_review_bottom_line` first, else top anomaly) and
  `_new_day_header` prepends it as "co-pilot: …" — the app greeting you in
  the day file instead of waiting to be opened. Anomalies also show under
  UNUSUAL in the Life review. Pure logic; anomaly ranking + note
  prioritisation + drought path verified on Linux. NOTE: this is the app's
  first PROACTIVE surface (writes into the morning header); it stays a
  stated line the user reads and ignores or acts on — NOT a gate/nag, per
  the standing anti-nagging guardrail. Keep it that way.
- **v8.5** (Life review — the connective tissue, AI-analyst v0.5 keyless).
  `_life_review_lines()` composes week numbers + `_alignment_lines` +
  `_outlook_lines` + `_trajectory_lines` + top `_insight_lines` into one
  briefing; `_review_bottom_line()` is the new synthesis — reads Foresight
  (deadlines late at real pace) and Alignment (widest say-do domain gap)
  together and emits ONE action across 4 rule branches (behind+gap /
  behind / gap / all-good). View > Life review window + "Copy for AI
  second opinion". Pure view composing tested functions; the 4 bottom-line
  branches + composition verified on Linux. The first surface where the
  three pillars speak as one voice.
- **v8.4** (Life domains — first brick of Pillar C / Alignment, the most
  on-vision leap: time tracker → life management). `domains()` +
  `_domain_minutes` + `_alignment_lines(weeks=8)` + `_alignment_win` +
  `_set_domains` (Tools > Life domains, View > Life alignment). Domains
  are a keyword lens one level above goals; the view shows actual share
  per domain over 8 weeks vs a stated target and names the widest say-do
  gap. Pure view, reuses the lens primitive, no new source. Verified on
  Linux (share math, target gap, widest-gap headline, no-domains and
  no-work cases). Keyword-overlap caveat noted (disjoint domains only for
  honest percentages).
- **v8.3** (Outlook — first brick of Pillar A / Foresight). New
  `_outlook_lines()` + `_outlook_win()` (View > Outlook — weeks ahead) and
  a menu entry. Forward simulation across ALL scoped deadlines at real
  pace (reuses v8.1 `_dl_projection`/`_dl_velocity`): classifies each as
  late / on-pace / too-blind-to-project, ranks the late ones, and states
  the aggregate per-day lever (Σ max(0, needed_per_day − real_rate) over
  late deadlines). Complements `_capacity_lines` (abstract capacity) with
  actual-pace prediction. Pure view, no new data; window mirrors the
  `_health_view` boilerplate. Verified on Linux (late/on-time/blind
  classification, gap line, no-scope empty).
- **v8.2** (trajectory insight — first brick of Pillar B / Memory). New
  `_trajectory_lines(weeks=8)` in the insights section: splits the last 8
  weeks in half, compares work h/wk, sleep, and signal% across the two,
  and names the sharpest inverse trade-off ("buying work hours with
  sleep"). Same honesty gates as insights v3 (both halves ≥5 active days;
  silent when nothing moved). Pure view, reuses `day_index`/`_day_signal`/
  `_sleep_h`, no new source. Verified on Linux via extracted logic
  (tradeoff fires, both quiet-gates hold).

- **v8.1** (deadline finish-date projection — backlog #13, DONE). The
  burn-down window footer now extrapolates the ACTUAL landing date from
  real recent pace instead of only stating "needs Xh/day":
  `_dl_velocity(dl, days=21)` measures avg hours per active day × active
  fraction on the deadline's keyword lens (via `task_matches`, same
  empty-keyword=all-work rule as `_dl_progress`); `_dl_projection`
  solves remaining_h ÷ (that combined rate) for the land date and a
  "+1h/day → N days sooner" sensitivity (the same solve at rate+1);
  `_projection_line` is the one honest sentence, coloured red/green in
  `_draw_burndown`. Pure VIEW, no day-file write, no new source. Honesty
  gate: 5+ real intervals in the window, scoped deadlines only. Verified
  on Linux via ast-extracted logic (velocity, projection, gate,
  no-scope) since tkinter can't run here.

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
- **v7.7**: per-task clock. The big clock is session-cumulative on
  purpose (matches the old app's "studying duration," only Reset clears
  it) but visually read as "the timer kept going" across a Switch. New
  small readout — "this task: 3:12" — shows current-interval elapsed
  time only, resets to 0:00 on Switch/Start. Confirmed the csv/day-file
  attribution was already correct per task; this was a display gap, not
  a logging bug.
- **v7.8** (on this day): morning header checks for a day file exactly
  one year ago (same month/day; Feb 29 falls back to -365 days) and
  prints a one-line callback — hours worked + the first free-typed line
  — if one exists. Read-only, zero setup, pays back the "keeps the data
  forever" idea directly in the file the user already reads every
  morning rather than as a separate view to remember to open.
- **v7.9** (scheduler foundations — the v7.9 prep release for the v8.0
  "big push," user-chosen direction: The Scheduler). Closes the one
  real infra gap flagged under item 11 below: `parse_ics_intervals` now
  returns actual per-day busy TIME RANGES (merged/sorted), and
  `parse_ics_busy` becomes a thin hours-sum over it — every existing
  capacity call site is unaffected (same signature), except that
  double-booked meetings now count their overlap once instead of once
  per event (a genuine, called-out behavior fix, not silent). New
  `_free_slots(date)` — work-day window (Tools > "Work-day window",
  default 08:00-22:00) minus calendar busy ranges minus (today only)
  already-logged csv time — is the actual foundation v8's real
  scheduler builds on. Proved end-to-end with one visible line in the
  morning header: "biggest free block today: 14:00-17:00 (3.0h)".
- **v8.0** (the actual scheduler — planning-engine tier c, DONE). The
  "focus order today" list is now a real time-blocked schedule:
  `_focus_items()` (the ranking, factored out of the old
  `_focus_order_lines` so both views share it) is greedily placed into
  `_free_slots(today)`, most-urgent-deadline-first into
  earliest-free-time-first — "08:00-12:05 Thesis (4.1h) ⚠ behind pace"
  instead of a bare "needs 4.1h." MVP scope on purpose: today only, one
  pass, no multi-day optimization; falls back to the plain priority
  list on a fully-booked day. Sanity-checked against the user's real
  deadline set (Thesis/TUTA/HHegemon draft via a sandboxed settings.json
  copy, not the live file) and produced a sensible placement. Still
  purely a VIEW — the planning-engine guardrail (no accept/reject UI,
  no compliance tracking) holds; see the design notes under backlog
  item 11c below, now marked done.
- **v8.1–v8.12** (landed as one set from a mobile Claude Code session,
  hand-audited on the main machine before touching master — see the
  Git section below for the landing process). Fourteen commits,
  reviewed individually plus one integration smoke test combining all
  of them, all correctly authored `econjp`, zero AI trailers, zero
  personal data: **v8.1** deadline finish-date projection in the
  burn-down window (backlog #13, real-pace forecast + a "+1h/day"
  lever); **v8.2** 8-week cross-domain trajectory in Insights; **v8.3**
  Outlook — all deadlines forward-simulated at real pace; **v8.4**
  Life domains, the values layer above goals (same keyword-lens
  primitive, one level up — inert until configured); **v8.5** Life
  review, one briefing synthesizing v8.1–v8.4; **v8.6** the co-pilot
  header line — a "co-pilot:" line opens new day headers only when
  something genuinely crosses an anomaly-vs-your-own-baseline gate,
  silent otherwise; **v8.7** "What should I do now?" — a real-time
  companion reading the current hour against a learned deep-focus
  window; **v8.8** energy-aware scheduling — the v8.0 planner now
  steers the hardest/most-behind work into learned peak hours instead
  of earliest-free-gap, falling back to exact v8.0 behavior under 20h
  of history; **v8.9** "where you left off" — starting a task with
  history hands back the last line you wrote about it; **v8.10** break
  pull-back (a loud, never-locking escalation on breaks off a SIGNAL
  task past a configurable threshold — verified by hand: only
  triggers for signal tasks, two stages, no persisted compliance
  tracking) plus the doomscroll tax measured from years of break
  notes; **v8.11** re-entry ramp, the smallest concrete opener offered
  after a 30+ minute break; **v8.12** procrastination pattern map,
  naming the specific task you bounce off within 10 minutes. Also
  landed: `timerv2/selftest.py`, an ast-extraction test harness for
  the v8.x logic tier (12 suites, independently re-run and green
  before landing — see "How to verify" below).
- **v8.13** (AVOID — backlog #39, DONE). The inverse of SIGNAL: a new
  "AVOID: news, email" header line, same keyword-lens shape
  (`matched_minutes`/`task_matches`) inverted, carrying forward day to
  day (no goal-seeded fallback, unlike SIGNAL — a standing declaration,
  not a daily pick). Avoid-share reported next to signal% on the
  yesterday-summary line, with a quiet week-over-week arrow (this week
  so far vs. all of last week, needs 2+ active days both sides, ≥3-pt
  move). `_kws_from_text` generalized to take a `prefix` argument so
  SIGNAL and AVOID share one parser instead of two near-identical ones.
- **v8.14** (behind-pace root cause — backlog #47, DONE). The burn-down
  window's real-pace footer gains a second, honesty-gated line:
  capacity problem (genuinely not enough free time this week) vs.
  choice problem (plenty of free time, just went elsewhere). Pure math
  over `_dl_progress`'s own `behind` flag + `_day_capacity` +
  `matched_minutes` — no new data source. Only speaks Wednesday onward
  (needs the week mostly through to be a fair sample). Tested against
  both branches plus both silence gates (not-behind, no-scope,
  too-early-in-week) with realistic synthetic deadlines.
- **v8.15** (personal block-length decay curve — backlog #38, DONE).
  `_decay_cycle` buckets work blocks by length and compares the break
  immediately following each bucket, finding where break length jumps
  sharply — the personal focus cycle, derived from real history
  instead of an imposed pomodoro number. Feeds two surfaces: an
  Insights line (`_block_decay_lines`) and a quiet status-bar
  suggestion when starting a SIGNAL task with no explicit `[Xm]` box
  (`_suggested_time_box`, wired alongside the existing "not today's
  signal" flag in `_toggle`) — never overrides an explicit box, only
  fills the silence when there wasn't one. n≥3 per bucket, needs 2+
  populated buckets. Tested with seeded short-block/short-break vs.
  long-block/long-break history producing a real detected jump.
- **v8.16–v8.21** (a bigger batch — six backlog items landed in one
  push, DONE). **v8.16 declared short day (#37)**: "TODAY: 4h" (or
  "TODAY: sick", no number) in the day's own file replaces the next
  morning's usual verdict judgment with "short day as declared — plan
  honored," and bridges the streak through a declared day (21-day
  lookback, so it doesn't cost a file-open per day across the full
  112-day best-streak scan). **v8.17 first-hour audit (#40)**: signal-
  first vs other-first days compared on total hours, n≥5 each side.
  **v8.18 task-thrash meter (#16)**: signal% on high-switch days vs
  low-switch days, distinct from #38's duration-based decay curve;
  also a live status-bar switch count past 4. **v8.19 shallow-work
  ratio (#49)**: same-day block-length depth check, threshold derived
  from #38's decay cycle when available. **v8.20 library graveyard
  sweep (#43)**: first-Monday-of-month naming of Task-library items
  60+ days untouched (approximated by ADDED date — no separate
  last-touched tracking exists, an honest simplification). **v8.21
  task-library commitment density (#55)**: the Tasks/Library window
  header shows total signal-priority volume undated. All six: pure
  views/math over data already collected, tested individually and in
  combination (a single header generation exercising declared-short-
  day + graveyard-sweep together), full regression + selftest.py
  (12/12) green throughout.
- **v8.22–v8.26** (same push, second wave — five more, DONE).
  **v8.22 rescue block (#41)**: "What should I do now?" gets a
  15:00–21:00 going-sideways branch — real deadline need + under 25%
  of the day's expected hours tracked → one salvage line instead of
  the normal pick, silent once real progress exists. **v8.23 mood ≠
  energy (#4)**: ENERGY accepts an optional word ("3 anxious"); new
  insight names the mood with the biggest signal-share departure from
  baseline (n≥3/mood, n≥10 days). **v8.24 app usage-pattern meter
  (#56)**: every View-menu command bumps a counter (`_tracked`
  wrapper), Tools > "Feature usage…" to see it — the tool auditing its
  own use. **v8.25 best-weeks retrospective (#58)**: top-3 historical
  weeks by signal-hours×share, naming which weekday carried most of
  it — the positive-framed complement to a mostly diagnostic insight
  set. **v8.26 reallocation scenario (#59)**: `_capacity_lines` gains
  one concrete trade when the most-urgent deadline has a real TODAY
  capacity problem and a less-urgent one has slack. Verified #56's
  wiring via an actual menu invocation, not just the wrapper function
  in isolation. Full regression + selftest.py green throughout.
- **v8.27** (the health-hub pivot — a generic metrics line + wider
  health capture, DONE). Answers the owner's 2026-07-14 "will we regret
  not logging enough" question with a mechanism, not a promise: **METRICS**
  header line (`_metrics_from_text`/`_day_metrics`), the SIGNAL/AVOID/
  ENERGY/mood pattern generalised into one `key=value` parser that takes
  any future personal metric with zero new code; `_metrics_insight`
  compares signal-share on logged-vs-not days for whatever key gets used,
  n≥5/side, n≥10 total. `parse_health_dir` widened to opportunistically
  capture mindful/meditation minutes, resting heart rate, HRV and weight
  from the same already-recommended export app, AND fixed a real gap
  where a CSV containing only one such metric (common — one file per
  metric type) was silently skipped entirely by the old sleep/workout-
  only gate. Mindful minutes surfaced in the existing health header line;
  RHR/HRV/weight captured onto `_life_day` for a future health view
  (#65), not yet in the UI. New "Data architecture for the long term"
  section above records the reasoning for future sessions. selftest
  gains suites 13-14 (metrics parsing/insight, widened health parsing);
  14/14 green. Landed on a freshly recreated `claude/life-management-
  platform-arch-6s4hrv` branch (the old one had already been merged +
  deleted) — see Git section.
- **v8.28** (daylight — the first source needing NO export file at all,
  DONE). `day_length_hours(d, lat_deg)`: a standard declination/hour-
  angle approximation, pure math, no network/API/dependency — verified
  against real-world solstice values (Helsinki ~18.6h/5.4h summer/winter,
  equator flat 12h) within the expected few-minutes error. Tools >
  "Daylight location (latitude)…" (`_set_daylight_lat`, empty clears it);
  `_daylight_h`/new `_life_day` key `daylight_h`; `_daylight_insight`
  compares output/energy on shortest- vs longest-daylight days, gated on
  a REAL seasonal swing existing in the user's own history (n≥8/side,
  ≥2h median gap) so it can't manufacture a season out of a few flat
  weeks. Directly extends the v8.27 "data architecture" answer: capture
  the free stuff now, even when the payoff is literally seasons away.
  selftest suite 15 (formula reference points, off-by-default, all three
  silence gates, the positive-fire case); 15/15 green.
- **v8.29** (word drift — Pillar B/Memory, the diary's own text finally
  read as itself, DONE). `_diary_word_counts(lo, hi)` tokenizes free-
  typed diary text (unicode word chars, len≥4, small EN+FI stopword
  list), skipping every structural line via the SAME `_LINE_TAG_RULES`
  the syntax highlighter already uses — no double-reading of SIGNAL/
  METRICS/TODO/timer lines as if they were prose. `_word_drift_insight`
  compares normalised frequency over the last 30 days vs the prior 90,
  naming the word with the sharpest real increase (n≥3 recent mentions,
  either brand-new or ≥3x its prior share; ≥30 total words each side or
  silent). No new source — the diary text has always been fully
  captured, this is the first view to read it on its own terms rather
  than only mining it for TODO/SOMEDAY bullets. Real bug fixed en route:
  `METRICS:`/`TODAY:` lines (v8.27/v8.16) were missing from
  `_LINE_TAG_RULES` and rendered as plain unstyled text instead of bold
  like their siblings — also would have polluted this feature's word
  counts had it not been caught first. selftest suite 16 (exclusion
  correctness incl. TODO-bullet-text-counts-but-TODO-header-doesn't,
  stopwords, the drift-detection case with hand-verified arithmetic, the
  volume-gate silence case); 16/16 green.
- **v8.30** (ask your diary — backlog #14, DONE). `_diary_rank_days`:
  splits a query into terms, OR-matches across every day file, ranks by
  breadth (distinct terms hit) then depth (total hits) then recency —
  the honest "better keyword search" the backlog asked for, not fake
  semantic search. `_matching_days_text` builds the clipboard payload
  (top 5 days' matching lines, not whole files, dated headers). A new
  "Copy matching days for AI" button sits ALONGSIDE the existing
  literal single-term search in the same Search-all-days window —
  nothing removed or replaced. selftest suite 17 (breadth beats raw hit
  count, no-match/empty-query cases, clipboard text ordering); 17/17
  green.
- **v8.31** (lag correlations — backlog #22, DONE). Every insight before
  this correlates SAME-DAY pairs; three new checks use (day, day+1)
  instead, same n≥5/bucket + real-swing gates: `_lag_workout_line`
  (workout day → next day's output, via `_health_data`'s workout_min),
  `_lag_sleep_debt_line` (a short-sleep NIGHT → the day AFTER that, a
  genuinely different pairing from the existing same-day sleep-vs-output
  check, not a duplicate of it), `_lag_evening_start_line` (work past
  21:00 → next morning's first-session start time, via a new shared
  single-pass `_day_start_late_map` over `read_rows()`). All three
  compose into `_lag_insight`, hooked into Insights. selftest suite 18
  (each sub-check's positive-fire case with hand-traced arithmetic,
  full silence-gate coverage); 18/18 green.
- **v8.32** (week-ahead risk brief — backlog #42, DONE). Monday's header
  gains WEEK AHEAD alongside the existing backward-looking WEEK REVIEW:
  `_week_ahead_lines` composes `_day_capacity` over the next 7 days with
  every scoped deadline's `_dl_progress`/`_dl_projection` — aggregate
  free hours vs aggregate need, the single tightest day if it's genuinely
  tight (not just the least-roomy of an otherwise-even week), and which
  deadlines are already behind at real pace. Silent unless at least one
  of overbooked/tight-day/behind actually holds — a normal week produces
  nothing. Built on simpler primitives than the original design note
  sketched (`_day_capacity` instead of `_free_slots`+`_outlook_lines`);
  the note is kept at backlog #42 with what's still open. selftest suite
  19 (overbooked, genuinely-tight-day, behind-at-pace, and both silence
  cases — no deadlines at all, and a normal roomy/on-pace week); 19/19
  green.
- **v8.33** (metrics shorthand — backlog #66, DONE). `_metrics_from_text`
  rewritten to split-by-comma then match per-token, so a bare word with
  no `=`/`:` implicitly logs `word=1` ("METRICS: meditation,
  cold_shower") alongside normal `key=value` tokens on the same line.
  `_metrics_insight` needed zero changes — it already only checks
  presence-of-key. Same "metrics" selftest suite extended (mixed-form
  line, bare-word-only line, invalid-bare-token-skipped); existing
  key=value/key:val cases unchanged, no regression; 19/19 green (no new
  suite — an existing one grew).
- **v8.34** (break budget — backlog #33, DONE). `_break_budget_line`
  learns the full-day break norm as the MEDIAN break-total across real
  workdays (work ≥3h, n≥10 required) and "typical by this hour" as the
  median CUMULATIVE break minutes those same days had by the current
  hour — days with no break yet by that hour correctly count as zero
  (`dict.fromkeys(real_days, 0)` pre-fill) rather than being silently
  absent from the median, which would skew it toward only the days that
  happened to break early. Wired into `_refresh_totals`'s totals line as
  one more segment; confirmed that function is event-driven (toggle/
  switch/reset/day-roll) not a per-second tick before adding another
  `read_rows()` scan there. selftest suite 20 specifically constructed
  to catch the zero-fill omission (asserts the correct 0m, which a naive
  implementation would instead compute as 200m); 20/20 green.
- **v8.35** (lens overlap check — backlog #48, DONE). `_lens_registry`
  gathers every declared goal/domain/scoped-deadline keyword lens
  (empty-match deadlines excluded — overlap with "everything" isn't
  actionable). `_lens_overlap_lines` checks every PAIR for REAL
  double-counted minutes in the last 30 days — deliberately not just a
  keyword-string intersection, since two DIFFERENT keywords can each
  independently match the same task name with zero shared keyword
  string (tested explicitly: "run" + "training" both matching "morning
  run training"). View > "Lens overlap check…" is its own window
  (mirrors Data doctor), not folded into `_insight_lines` — the nested
  pairs×days×tasks scan doesn't belong in the per-refresh insight path.
  selftest suite 21 (registry exclusion, the no-shared-string-but-real-
  overlap case, keyword-collision-that-never-fired stays silent,
  no-overlap and <2-lenses silence); 21/21 green.
- **v8.63** (focus signature — backlog #53, DONE, the shape of a real
  week). New `_focus_signature_grid`: for each (weekday, 4-hour
  bucket) cell, the fraction of that weekday's occurrences (trailing
  180 days) with any SIGNAL-matched work in that bucket — a
  consistency score, not a raw total. n>=4 occurrences per weekday
  gate. New `_focus_signature_line`, in the Monday review: "focus
  signature: Tue 08-12 lights up 100% of the time (n=4); Mon 00-04
  never does (n=4)." Silent unless the best cell clears a real 50%
  consistency bar. New "focus-signature" selftest suite (a hand-
  verified 4-week scenario landing on exact grid values, silence with
  no SIGNAL, silence below the consistency bar, silence below the
  occurrence gate); 45/45 green (new suite, was 44).
- **v8.62** (conversation-ready status export — backlog #57, DONE, a
  deliberately different register). New `_status_update_text`/
  `_status_update_all` + Life dashboard "Copy status update" button:
  "Progress update — Thesis: 12h this week (up from 8h last).
  Currently projected 3d behind pace, landing August 04. Blocked on:
  ch5 draft." Pure reuse of `_dl_progress`/`_dl_projection`'s own
  numbers plus v8.60's fresh `blocked_by` field for the blockers
  sentence. Explicitly the one surface meant to sound different on
  purpose (external-facing), not a precedent for softening the rest
  of the app's blunt voice. New "status-update" selftest suite
  (behind-pace/on-pace phrasing, a blocker pulled in, silence for
  unscoped, `_status_update_all` joining and skipping); 44/44 green
  (new suite, was 43).
- **v8.61** (cost of yes — backlog #52, DONE, capacity math run BEFORE
  you commit). New `_cost_of_yes_line(hypothetical, existing)`: the
  exact aggregate-slack math `_capacity_lines` already runs for real
  deadlines, against a pool with one hypothetical more in it —
  "committing to 'NewProj' would push slack from +5.0h to -10.0h —
  Thesis would need to give up 1.0h/day to make room." Wired as a
  live keystroke-updated preview in the deadline edit dialog, only
  for a genuinely NEW row (a name not already saved); editing an
  existing deadline in place is deliberately not previewed here —
  v8.51's renegotiation tracker covers that on save instead. New
  "cost-of-yes" selftest suite (no-existing-deadlines baseline, a
  hand-verified give-ground scenario, silence on missing/zero scope,
  a past due date, an unparseable date); 43/43 green (new suite, was
  42).
- **v8.60** (waiting-on / blocked tasks — backlog #44, DONE, external
  dependencies the planner can't see). New `blocked_by` task-library
  field (Tasks window right-click > "Set blocked by…", free text,
  same popup shape as Set goal/Set deadline). Filtered out of
  `_reentry_opener`'s candidates and both "uncommitted hours → pick
  from Task library" lines. New `_waiting_on_lines`, a new "WAITING
  ON:" section in the dashboard's "Deadlines & Goals" tab. Blocked
  rows get a ⛔ marker + reason inline in the Tasks window, tagged
  red. Corrected the original note's claim: `_recommend_now`/
  `_focus_items` don't actually read the task library (deadline-
  scoped only), so no filtering was needed there. New "waiting-on"
  selftest suite; existing "reentry" suite extended with a blocked-
  item case; 42/42 green (new suite, was 41).
- **v8.59** (milestones inside a deadline — backlog #36, DONE,
  content not just hours). Deadlines gain an optional "Milestones"
  field in the existing edit dialog: `ch4 [15h]*, ch5 [20h], revisions
  [10h]` (same `[Nh]` bracket convention the task time-box already
  uses, trailing `*` = done). New module-level `_parse_milestones`
  (pure) + `_milestone_progress_line`, surfaced in the dashboard's
  "Deadlines & Goals" tab — "ch4 done, ch5 at 60% of its hours,
  revisions at 0% of its hours." Hours accrue in milestone order: the
  current (first not-done) milestone gets credit for whatever matched
  hours haven't already been claimed by earlier done ones. A proxy,
  not a real per-milestone tracker — but honest, since it never
  claims more than the deadline's own real matched total. Scoped down
  from the original note: burn-down/projection and a per-milestone
  estimate factor NOT wired in, dashboard line only. New "milestones"
  selftest suite (parsing incl. the done-marker and malformed text, a
  hand-verified scenario landing exactly on the design's own "ch5 at
  60%" example, silence with no milestones field); 41/41 green (new
  suite, was 40).
- **v8.58** (protected time windows — backlog #50, DONE, the
  scheduler's missing exclusion zone). New Tools > "Protected time
  windows…" (grid dialog, same pattern as Goals/Deadlines): named
  daily-recurring windows ("lunch 12:00-13:00", "wind-down
  21:00-22:00"). New `_protected_intervals` parses them (malformed
  entries skipped, not raised); `_free_slots` subtracts them exactly
  like calendar busy-time already is — one more "busy" source merged
  into the same primitive. New "protected-windows" selftest suite
  (valid parsing, a backwards range/malformed time/missing key all
  skipped, empty-settings silence); 40/40 green (new suite, was 39).
- **v8.57** (commitment-reliability ledger — backlog #18, DONE, self-
  calibration feedback not a gate). New opt-in `COMMIT: thesis 4h` /
  `COMMIT: 4h` header line (never auto-inserted, same convention as
  EXPERIMENT/DECIDED). New `_commit_from_text` (same template as
  `_energy_from_text`) + `_commitment_reliability` (n>=5 gate,
  keyword-scoped or whole-day commitments), surfaced in the Monday
  review — "you hit your morning commitment 3 of the last 5 days —
  you reliably deliver ~60% of what you promise yourself." Never
  grades any one day, only the trailing rate. `COMMIT:` added to the
  header syntax-highlight rules. New "commitment-reliability" selftest
  suite (parsing variants including malformed input, a hand-verified
  5-commitment/3-hit mixed scenario, silence below the gate); 39/39
  green (new suite, was 38).
- **v8.56** (time capsule — backlog #61, DONE, the forward-looking
  counterpart to on-this-day). New `_due_capsules`: scans every day
  file for a `CAPSULE: YYYY-MM-DD | message` line whose date equals
  today (a same-day self-reference is excluded — a file can't be "the
  past" relative to itself); `_capsule_lines` formats the days-ago
  phrasing. Hooked into `_new_day_header` next to on-this-day.
  `CAPSULE:` added to the header syntax-highlight rules. New
  "time-capsule" selftest suite (two capsules due the same day from
  different files in chronological order, a different-date capsule
  excluded, a malformed no-pipe line safely ignored, the same-day
  edge case, full silence); 38/38 green (new suite, was 37).
- **v8.55** (screen-lock break detection — backlog #81, DONE, direct
  owner request). New `is_locked()`: OpenInputDesktop ctypes trick
  (stdlib only, no pywin32) — fails when the interactive desktop
  isn't reachable, i.e. while locked. New `_watch_lock`, called from
  `_tick` next to `_watch_idle`: on unlock, reuses the EXISTING
  `_offer_idle_break` dialog directly (no new UI), with a 30s
  (`MIN_LOG_SECS`) floor against an accidental tap-and-untap. Gated
  on `idle_min` being on at all, deliberately NOT on meeting-mode's
  `idle_off_until` (a lock is unambiguous even mid-call). UNTESTED by
  the selftest harness — same category as the pre-existing idle-
  detection code, a live-Windows-only interaction; needs the owner to
  confirm on their real machine. No new suite (nothing testable
  without live Windows); still 37/37 green, no regressions.
- **v8.54** (planner realism factor — backlog #25, DONE, the schedule
  audits itself). New `_planned_hours_from_file`: reads a past day's
  own written schedule block back out of its file (same in-file
  convention trick `_estimate_factor` uses), excluding the
  "uncommitted" free-time line. New `_planner_realism_factor`: median
  (actual/planned, capped at 1.0) over the last 60 scheduled days,
  n>=5 gate. `_day_schedule_lines` now scales each item's needed
  hours by that ratio before placing blocks and prints the density in
  the schedule header. No compliance tracking of the person — grades
  the planner only. New "planner-realism" selftest suite (placement-
  line parsing correctly excludes the uncommitted line, a hand-
  verified 6-day median with one overshoot day capped at 1.0, silence
  below the n>=5 gate); 37/37 green (new suite, was 36).
- **v8.53** (sensor health meter — backlog #23, DONE, the platform
  watching its own instruments). New `_sensor_health_lines`, a new
  section at the top of the Data doctor window: per source (sleep
  import, calendar, ENERGY logging) — last date seen with real data,
  coverage % over the trailing 30 days, a plain alarm once it's gone
  quiet longer than a reasonable cadence ("sleep import: last seen
  2026-06-15 (30d ago), 0% coverage — the phone automation may have
  stopped"). Also lists the personal baselines the anomaly watch
  judges against (median sleep, median week). New "sensor-health"
  selftest suite (all three alarms firing together with exact
  coverage/gap numbers, a healthy pass with no alarms, the fully-
  unconfigured silence path); 36/36 green (new suite, was 35).
- **v8.52** (weekly "one less" — backlog #35, DONE, a subtraction
  advisor). New `_one_less_candidates`: three removal candidates
  sourced from mechanisms already built this session — the worst
  single meeting-fragmentation cost (v8.42), the task bounced off
  most (v8.12), the after-21:00 work that taxes tomorrow (v8.38) —
  each only included when it clears its own honesty gate. New pure
  `_pick_one_less`: picks the first candidate that isn't last week's
  key, falling back to a repeat only when it's the sole remaining
  option. One line in the Monday review: "THIS WEEK, TRY ONE LESS:
  the meeting that fragments your day — Wed's meeting cost 1.3h."
  New "one-less" selftest suite (the pure rotation rule, candidate
  composition/framing via stubs on the three already-tested
  sub-insights, an actual back-to-back-repeat avoidance, a single-
  candidate week correctly repeating instead of going silent);
  35/35 green (new suite, was 34).
- **v8.51** (deadline renegotiation tracker — backlog #46, DONE,
  scope-creep honesty). New module-level
  `_deadline_revisions_after_save(old, new, today_iso)`: compares the
  deadline list before/after a save (matched by name), appends a
  `history` entry (the OLD date/total_h, timestamped) to any deadline
  whose date or total_h actually changed; wired into the existing
  edit dialog's save(), no new UI. Once 2+ revisions exist, new
  `_deadline_renegotiation_line` adds one line under that deadline in
  the dashboard — "this deadline has moved 2 time(s) since 2026-06-29
  — due date is now 45d later than first set, scope grew from 20h to
  45h." Live and ongoing, distinct from v8.50's post-mortem (fires
  once, after resolution). New "deadline-renegotiation" selftest
  suite (history accumulates without overwriting, a no-op save adds
  no phantom entry, a new deadline gets no history key, three
  phrasing variants, a malformed entry stays silent); 34/34 green
  (new suite, was 33).
- **v8.50** (deadline post-mortem — backlog #28, DONE, each closed
  deadline becomes calibration data). New `_deadline_postmortem_lines`
  (pure): scope vs actual hours, the estimate factor on THIS project
  (`_estimate_factor` extended with an optional keyword filter, app-
  wide blend unchanged by default), a retrospective projection check
  (what the trailing-21-day pace math would have predicted 21 days
  before the due date vs when the scope was actually completed —
  "predicted 13.07, actually finished 04.07 — ran 9d pessimistic"),
  and the real pace kept over the project's whole life. New
  `_run_deadline_postmortems` write-once guard (`postmortem_written`
  on the deadline dict), hooked into `_new_day_header`. Only the "due
  date passes" trigger implemented, not "or its task is Done" (no
  deadline-to-task-library linkage exists to hook that on). New
  "deadline-postmortem" selftest suite (fully hand-verified scenario
  exercising all four lines, two silence gates, the write-once guard);
  33/33 green (new suite, was 32).
- **v8.49** (goal lifetime ledger — backlog #45, DONE, the un-windowed
  view). New `_lifetime_ledger_line(name, kws, start_iso)`: total
  hours + session count since `start_iso` (a deadline's own stored
  start, if set) or the first-ever matching csv row (goals have no
  start field yet). One new line under each goal/deadline in the
  dashboard's "Deadlines & Goals" tab — "Thesis: 187h across 62
  session(s) since 2026-06-29 (134 days — 1.4h/day lifetime
  average)." Row-level scan (needed for the session count;
  `matched_minutes` alone only gives a total). New "lifetime-ledger"
  selftest suite (fallback to earliest matching row, an explicit
  start_iso anchoring the date AND filtering out earlier matches,
  two silence gates); 32/32 green (new suite, was 31).
- **v8.48** (annual theme — backlog #64, DONE, the year-scale sibling
  of SIGNAL/AVOID). New `YEAR: <theme>` header line, new `_carry_year`
  (same shape as `_carry_avoid`, v8.13), auto-carried into every day
  file. The on-this-day (one-year-back) line now surfaces that year's
  theme when one was set: "· that year's theme: 'finish the thesis'
  — still true?" `YEAR:` added to the header syntax-highlight rules.
  #15's year-in-review reference deferred (doesn't exist yet). New
  "annual-theme" selftest suite (carry-forward, blank when unset, the
  on-this-day callback with/without a theme, silence with no file);
  31/31 green (new suite, was 30).
- **v8.47** (decision log lite — backlog #62, DONE, "didn't I already
  think this through"). New `DECIDED: <topic> — <verdict>` archival
  line convention + View > "Decision log…" (new pure `_scan_decisions`
  + thin `_decision_log_view` Tk layer, newest-file-first). No
  counter, no reopening friction, no unlock mechanic — deliberately
  NOT #9's rejected Reopening Guard mechanics. `DECIDED:` added to
  the header syntax-highlight rules. New "decision-log" selftest
  suite (ordering, a mid-sentence false-positive correctly excluded,
  silence with none declared); 30/30 green (new suite, was 29).
- **v8.46** (ask-your-diary pinned searches — backlog #71, DONE, a
  recurring lookup becomes one click). Search all days gains a
  pinned-search button row: click to re-run, 📌 Pin to save the
  current query, right-click to remove. New pure
  `_pinned_after_add`/`_pinned_after_remove` behind `_pin_search`/
  `_unpin_search`, settings-backed (`settings["pinned_searches"]`),
  capped at 5 — re-pinning an existing query re-surfaces it at the
  front, pinning past the cap drops the least-recently-used one. Pure
  UI addition over `_diary_rank_days` (v8.30), no ranking-logic
  change. New "pinned-searches" selftest suite (front-insert, re-add
  re-surfaces not duplicates, cap drops oldest, blank query no-op,
  remove); 29/29 green (new suite, was 28).
- **v8.45** (weekly experiment engine — backlog #20, DONE, closing the
  diagnose-then-nothing loop). New opt-in in-file convention:
  `EXPERIMENT: no work after 21:00` typed in Monday's header (never
  auto-inserted, same convention as SIGNAL/AVOID/ENERGY). The
  FOLLOWING Monday's WEEK REVIEW reports that week's measured shift
  on work, late-evening minutes and sleep vs the trailing 4-week
  baseline — "EXPERIMENT 'no work after 21:00': late-evening -1.0h vs
  baseline; sleep +0.5h/night vs baseline; output +0.0h vs baseline."
  Deliberately never verdicts on whether the free-text RULE was
  followed (too fragile to parse honestly); a plain before/after on
  tracked numbers instead. New `_experiment_from_file`/
  `_week_metric_totals`/`_experiment_review_line`, hooked into
  `_week_review_block`. `EXPERIMENT:` added to the header syntax-
  highlight rules. New "experiment-engine" selftest suite (hand-
  verified 3-metric delta, silence with no EXPERIMENT declared,
  silence with too little baseline history); 28/28 green (new suite,
  was 27).
- **v8.44** (energy forecast for today — backlog #29, DONE, what your
  data suggests vs what the weekday table plans). New
  `_energy_forecast_line(days=90)`, hooked into the morning header
  right after the co-pilot note. "Last night's sleep" + "trailing
  sleep debt" combine into ONE signal (the 3-night rolling average
  ending on a given day) vs your own trailing-90-day median; bucketed
  by weekday + rolling-sleep tier (rested/debt); the matching
  bucket's 25th-75th percentile tracked-work range is the forecast —
  "today smells like a 3.5-4.5h day (Tuesday, running on debt, n=6)."
  `_capacity` unchanged (still the PLANNED weekday table); this is a
  separate ACTUAL-data signal alongside it. Needs today's own
  rolling-sleep reading and n>=5 matching historical days; silent
  otherwise. New "energy-forecast" selftest suite (hand-verified
  10-Tuesday rest/debt split collapsing to one exact value, silence
  with no usable rolling reading, silence with too little sleep
  history); 27/27 green (new suite, was 26).
- **v8.43** (year rhythm map — backlog #26, DONE, the year's shape at
  a glance). View > "Year rhythm map": a 52-week × 24-hour canvas,
  each cell shaded by tracked minutes in that hour that week — where
  `_heatmap` shows how MUCH per day, this shows WHEN, at year scale.
  New pure `_year_rhythm_grid(weeks=52)` returns {(week_idx, hour):
  minutes} (Monday-start weeks, same convention as `_heatmap`; both
  work and break rows count); `_year_rhythm_view` is the thin Tk
  canvas layer mirroring `_heatmap`'s drawing code. New "year-rhythm"
  selftest suite (same-cell summing across different days, a break
  row counting, the oldest in-window week landing right at the edge,
  a one-day-outside-window exclusion, a future-date exclusion);
  26/26 green (new suite, was 25).
- **v8.42** (meeting fragmentation tax — backlog #21, DONE, meetings
  cost more than their duration). New `_meeting_fragmentation_lines`/
  `_day_fragmentation_tax`: for each meeting on each of the last 7
  days, simulates removing just that ONE meeting (others held fixed)
  and measures the deep-capacity (free blocks ≥90m) recovered — a
  20-minute meeting stranding a 60-minute sliver can cost 1.3h, not
  0.3h. Reports the worst offender + week total: "Wednesday's 15:40
  meeting: 0.3h long, cost 1.3h of deep capacity" / "meeting
  fragmentation tax this week: 1.7h." New module-level
  `_free_from_busy`/`_deep_capacity_minutes` factored out of
  `_free_slots` so the scheduler's own free-time math is shared
  instead of reimplemented; `_free_slots` itself refactored onto it,
  behaviour unchanged. Hooked into `_insight_lines` next to the
  meeting-load check it complements. New "meeting-fragmentation"
  selftest suite (pure-helper checks, hand-verified marginal cost,
  two silence gates, the worst-offender+total composition, a 7-day
  window honesty check); 25/25 green (new suite, was 24).
- **v8.41** (running-hot index — backlog #24, DONE, the early-warning
  version of the sleep-for-work trade). New `_running_hot_line`,
  recent-vs-prior window shape (last 14 days vs the 60 before that,
  same shape as word drift v8.29/v8.37). Four independently n-gated
  signals — sleep below your own recent norm (>=0.4h real swing),
  workout frequency drop (recent rate <=60% of prior rate, n>=3
  prior workouts), late-night count (reuses `_day_start_late_map`
  from v8.38, >=3 in the window), break-ratio compression (recent
  ratio <=60% of prior ratio, real minute floors both sides) — speaks
  only when >=2 move together, never off one alone. Hooked into
  `_copilot_note` between the bottom-line risk and the sharpest
  anomaly. New "running-hot" selftest suite (sleep+late two-signal
  speak case, sleep-alone silence, sparse-sleep-data gate silence,
  workouts+breaks two-signal speak case); 24/24 green (new suite, was
  23).
- **v8.40** (backup integrity check — backlog #63, DONE — the safety
  net auditing itself). New module-level `backup_integrity_line()`:
  scans `backups/` for the newest `sessions_YYYY-MM-DD.csv`, silent
  when it's ≤10 days old (a buffer over the 7-day `backup_if_due`
  cadence so normal use never sees it), else "last backup: 15 days ago
  (expected weekly) — the automation may have stopped" (or "no backup
  found yet" if the folder's empty). Surfaced as the first line of the
  Data doctor window, opportunistic rather than a startup nag —
  directly on-brand given the 2026-07-11 dual-instance data-loss
  incident. New "backup-integrity" selftest suite (silent with no csv
  yet, speaks when backups/ is empty, silent within the 10-day buffer,
  speaks past it, picks the newest of several backup files not the
  oldest); 23/23 green (new suite, was 22).
- **v8.39** (break budget v2 — backlog #72, DONE, weekday-specific
  norms). `_break_budget_line` (v8.34) now buckets `real_days` by
  `dt.date.weekday()`: uses today's own weekday's median once it has
  its own n≥10 ("full-day norm ~50m (Mons)"), matching the weekday-
  aware capacity table (`_capacity`, v5.8) the rest of the app already
  assumes; falls back to the old all-days blend when a specific
  weekday doesn't have its own n≥10 yet. Existing "break-budget"
  selftest suite extended with a per-weekday-engaged case (10 Mondays
  at 50m vs 10 Tuesdays at 10m, weekday median wins) and a fallback
  case (9 Tuesdays stays under n≥10, blend applies, no weekday tag);
  22/22 green (no new suite — an existing one grew).
- **v8.38** (lag correlation #4 — backlog #70, DONE). A fourth check
  joins `_lag_insight`: `_shallow_threshold`/`_day_shallow_frac` factored
  out of `_shallow_work_lines` (v8.19) so the same shallow-block logic
  applies to ANY day, not just today; `_lag_fragmentation_line` pairs
  yesterday's `_day_switches` (v8.18, ≥6 vs ≤2) against today's shallow-
  work fraction — "the day after a 6+ switch day, 100% of your signal
  work lands in shallow blocks vs 0% after a focused day — fragmentation
  carries over." Same n≥5/bucket gate as the other three lag checks.
  Existing "lag" selftest suite extended with a hand-verified positive
  case (four distinct-named 15m blocks summing to the 60m minimum, all
  under the flat 20m threshold, vs one 60m deep block) plus the new
  silence case; registered five new methods + one class attribute
  (`_DECAY_BUCKETS`) the harness needed once `_lag_insight`'s
  composition pulled them in transitively; 22/22 green.
- **v8.37** (word drift, the fade direction — backlog #69, DONE, start
  of a new session's batch). `_word_drift_counts` factored out of
  `_word_drift_insight` so the increase check (v8.29) and the new
  `_word_fade_insight` share one file scan instead of two identical
  ones. Fade check is symmetric to the increase check (pn≥3 in the OLD
  window, vanished or collapsed to ≤1/3 its prior share), reported as
  its own separate insight line. Same "word-drift" selftest suite
  extended (a dedicated fade word with zero overlap with the existing
  increase test's data, silence gate covers both directions); 22/22
  green (no new suite — an existing one grew).
- **v8.36** (health-hub view — backlog #65, DONE — last of this
  session's run). `_health_view` gains a SECOND compact 14-day table
  (mindful minutes, RHR, HRV, weight, daylight) rather than widening the
  proven sleep/workout/steps/work/signal/energy table into one ~90-char
  row — same window, "don't duplicate a view" respected, nothing about
  the first table changed. `_health_extras_lines` split out as pure
  logic (same self/Tk-glue separation pattern as every other feature
  this session), with an explanatory footer when every column is still
  empty. selftest suite 22 (empty-state footer, real-data exact column
  formatting, a data-free day still renders as dashes not a crash);
  22/22 green.

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
   insight "scroll vs next-day energy". CHEAP STOPGAP now available via
   METRICS (v8.27): `METRICS: screen_time=143` typed by hand gets the
   insight machinery for free today; a real csv-drop importer is still
   the better end state (zero manual typing) but no longer blocking —
   don't let "no importer yet" stop the owner from starting to log this
   NOW if they want the data trend started.
4. ~~**Mood ≠ energy**~~ — DONE v8.23 (`_mood_from_text`/`_day_mood`/
   `_mood_insight`).
5. **Money source**: monthly csv drop (bank export) → spend per day key;
   balance section gains a cost line. (User hinted "total life".) Same
   METRICS stopgap note as #3b applies if a rough manual number
   (`METRICS: spend=45`) is more useful sooner than a real importer later.
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

    ~~**The one real infrastructure gap**~~ — CLOSED v7.9: `parse_ics_busy`
    used to return `{date_iso: total_busy_hours}`, a per-day SCALAR, not
    actual time RANGES within the day. `parse_ics_intervals` now returns
    `{date_iso: [(start_time, end_time), ...]}` (merged/sorted);
    `parse_ics_busy` is a thin sum over it, so every existing capacity
    call site kept working unchanged. `_free_slots(date)` (work window
    minus calendar minus today's own logged csv time) is the actual
    gap-aware primitive tier (c) below needs — this was the prerequisite,
    now done.

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
    c) ~~True time-blocked schedule~~ — DONE v8.0: `_focus_items()`
       (ranking, shared with tier b) placed greedily into
       `_free_slots()`, most-urgent-first into earliest-free-time-first.
       Answered the three open questions from the original design note:
       (1) written directly into the day header as a "suggested
       schedule today:" block, same tier as plan/focus-order, not a
       separate dashboard-only view — regenerated fresh each morning,
       never edited in place, so a wrong suggestion just doesn't
       reappear tomorrow rather than sitting stale in the file forever;
       (2) no compliance tracking added, per the guardrail below — it's
       a VIEW, full stop; (3) shipped as literally TODAY-only, one
       greedy pass, falling back to the plain priority list on a
       fully-booked day. Next real extension, if wanted: multi-day
       lookahead (place tomorrow's leftover need into tomorrow's free
       slots too) — deliberately not attempted here, MVP first.

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

12. ~~On this day~~ — DONE v7.8 (see version history above). Small, but
    the first feature to look BACKWARD across the whole archive rather
    than at the current week — worth naming as its own category because
    the next three ideas extend it.

13. ~~**Deadline finish-date projection (velocity-based forecast).**~~ —
    DONE v8.1, in the burn-down window footer (a VIEW, not `_plan_line` —
    kept out of the day file to avoid touching the format and to stay
    purely visual). `_dl_velocity`/`_dl_projection`/`_projection_line`;
    the "+1h/day → N sooner" sensitivity shipped too. Possible follow-ups
    if wanted: also surface the line in the dashboard's DEADLINES section,
    and/or a per-deadline "land date" column — deliberately left for the
    maintainer to decide, since more surfaces = more day-file/UI risk.
    Original design note kept below for reference.
    Currently `_dl_progress`/`_capacity_lines`/burn-down all answer "what
    pace do you NEED" — none answer "at your ACTUAL recent pace, when do
    you actually land." `_task_velocity` (v6/v7.0) already computes real
    h/day on a matched task; extend it (or a sibling) to project forward:
    take the trailing-N-day real average (not the whole history — recent
    behavior predicts near-term better than a stale average) and a
    trailing "active-day rate" (fraction of days with any tracked time on
    it, since "2h/active-day, active 40% of the time" ≠ "2h/day"), then
    solve for the date the remaining hours clear at that combined rate.
    Surface as one line, probably in `_plan_line` or a burn-down window
    addition: "at your current pace (2.3h on active days, active 55% of
    the time) you land around Jul 28 — 5 days past the Jul 23 deadline."
    Deliberately more honest than the existing "Xh/day needed" framing,
    which silently assumes perfect future compliance — this instead
    extrapolates from what actually happened, matching the project's
    established taste for blunt math over soft encouragement (the
    overbooked-capacity line, the morning verdict, all already work this
    way). Pair naturally with a one-line sensitivity add-on ("+1h/day
    from tomorrow would land you 4 days earlier") since the same
    projection function gives you that for free by re-solving at a
    higher rate — cheap, and turns a diagnosis into a lever. Purely a
    VIEW over `_task_velocity` + `_dl_progress`'s existing numbers, no
    new data source; needs n≥5ish real intervals on a task before it
    speaks, same honesty gate as insights v3.

14. ~~**"Ask your diary" — smart multi-day search, still copy-paste not
    API.**~~ — DONE v8.30. `_diary_rank_days`/`_matching_days_text` +
    a "Copy matching days for AI" button added ALONGSIDE the existing
    literal single-term search in the same window (nothing replaced).
    Original design note kept below for reference.
    Search-all-days (existing) is a literal substring match.
    The gap: with a year+ of day files accumulating, "when did I last
    mention the EU thing" or "what did I decide about X" needs more than
    exact-string recall. Given the no-dependencies rule rules out real
    embeddings/vector search, the honest stdlib-only version is a BETTER
    keyword search, not fake semantic search: split the query into terms,
    OR-match across them, rank hits by term-overlap count and recency,
    and — this is the actual new idea — extend "Copy for AI review" (v5.1,
    already ships week/day text + totals to the clipboard for pasting
    into an AI chat) into "Copy matching days for AI review": run the
    ranked search, paste the top N matching day-file excerpts (not the
    whole file) onto the clipboard with dates as headers, ready to paste
    into Claude/whatever with the user's own question on top. Keeps the
    existing manual-copy-paste pattern (no API key, no credential
    question like item 10's weekly-report idea) while making the archive
    actually queryable instead of just greppable. Medium effort — mostly
    a ranking function plus a clipboard-format function, both new but
    small; reuses `diary_path`/day iteration already used by Search all
    days and the JSON export.

15. **Year in review.** Every existing view (dashboard, weekly, monthly,
    8-week trend, heatmap) tops out at roughly a season. Once a
    reasonable amount of history exists (first natural trigger: the
    thesis defense, or just New Year), a single long-horizon summary —
    total hours by goal across the whole year, signal% trend, the
    deadline wins and misses, sleep/workout consistency, the single
    longest streak and the single worst week — read once and put away,
    not a working view. Lowest urgency of the four new ideas here (needs
    real time to accumulate to be worth anything, and the payoff is a
    once-a-year moment rather than daily utility) but worth having
    designed before the point where it'd actually matter arrives. Would
    reuse `day_index()` + the same lens primitives as everything else;
    the only new part is the wider date range and a text layout suited
    to a once-a-year read rather than a daily glance.

16. ~~**Task-thrash / context-switch meter (FEEDBACK).**~~ — DONE v8.18
    (`_day_switches`/`_thrash_insight`, plus a live status-bar count
    past 4 switches).

17. ~~**Energy-aware scheduling (PLANNING).**~~ — DONE v8.8.
    `_hour_quality(days=60)` = a 0–1 per-hour profile of where your work
    actually lands; `_energy_place(items, slots, quality)` gives each
    item (most-urgent first) its best-quality free time, so the hardest/
    most-behind deadline claims your peaks and admin drifts to the
    troughs. `_day_schedule_lines` calls it; contiguous blocks preserved;
    no-history falls back to the exact v8.0 earliest-first. Still open
    (deferred on purpose): fold LOGGED per-hour ENERGY into the profile
    (currently it's tracked-minutes only — a decent proxy, but a day you
    forced work through a slump still reads as "peak"); and a light note
    on WHY a block moved ("your 13–15 peak"). Both small follow-ups on
    `_hour_quality`.

18. ~~**Commitment-reliability ledger.**~~ — DONE v8.57. New
    `_commit_from_text` (same template as `_energy_from_text`) +
    `_commitment_reliability`, surfaced in the Monday review next to
    the one-less advisor. Original design note kept below for
    reference.
    (SELF-KNOWLEDGE).** A `COMMIT: thesis
    4h` line the user optionally types in the morning header (same in-file
    convention as SIGNAL/ENERGY). At rollover the app compares committed
    vs delivered per that day's csv and accrues a personal stat over time:
    "you hit your morning commitment 3 of the last 10 days; you reliably
    deliver ~65% of what you promise yourself — so promise 65% and mean
    it." Self-calibration feedback, not nagging (it's a stated number the
    user reads, never a gate — re-check against the anti-nagging precedent
    before adding any prompt). Reuses the day-file line-parse pattern
    (`_energy_from_text` is the template) + `day_index`. Turns the plan
    into honest self-knowledge about your own reliability.

19. **Frictionless quick-capture (USABILITY).** The task library (v6.5)
    captures TODO/SOMEDAY bullets from the diary, but only when you're in
    the app. A global-hotkey quick-capture popup — a tiny always-on-top
    entry box, same spirit as the break pill — lets you dump a thought or
    task from anywhere in one keystroke, landing it straight in the task
    library with source="quick" + timestamp, no context-switch into the
    main window. Removes the friction that currently sends stray todos to
    a WhatsApp-to-self thread (the exact thing the library was meant to
    replace). Reuses the existing global-hotkey thread pattern + the task
    library's add path; the popup is ~30 lines mirroring the break-pill
    Toplevel. Pure usability, high daily value.

20. ~~**Weekly experiment engine.**~~ — DONE v8.45. New
    `_experiment_from_file`/`_week_metric_totals`/
    `_experiment_review_line`, hooked into `_week_review_block`.
    Deliberately measures numbers (work, late-evening minutes, sleep)
    rather than parsing the free-text rule into an enforceable
    compliance check — "kept it 5/7 days" was judged too fragile to
    state honestly from arbitrary user text. Original design note
    kept below for reference.
    (FEEDBACK → ACTION → MEASUREMENT).** The
    insights diagnose ("you're more fragmented", "sleep is worth +1.3h")
    but nothing closes the loop. Opt-in, in-file, one at a time: the user
    types `EXPERIMENT: no work after 21:00` in Monday's header (same
    convention as SIGNAL/ENERGY — never prompted, never suggested more
    than once); the following Monday's WEEK REVIEW reports the measured
    delta vs the trailing 4-week baseline on the relevant metrics (late-
    evening minutes, next-day energy, sleep, output) and says plainly
    "kept it 5/7 days; sleep +0.4h; output unchanged — worth keeping?"
    Rule-based measurement of a self-chosen change — the co-pilot helping
    you CHANGE, not just know. Guardrail: results are stated once in the
    review, never enforced, never re-nagged mid-week.

21. ~~**Meeting fragmentation tax.**~~ — DONE v8.42. New
    `_meeting_fragmentation_lines`/`_day_fragmentation_tax`: for each
    meeting on each of the last 7 days, simulates removing just that
    meeting (others held fixed) and measures the deep-capacity (free
    blocks ≥90m) recovered. New `_free_from_busy`/
    `_deep_capacity_minutes` factored out of `_free_slots` so the
    scheduler's own free-time math is shared, not reimplemented.
    Confirmed `_busy_intervals`'s parse window on this branch is
    already -14/+90 days from today — covers the recent past fine, no
    widening needed. Original design note kept below for reference.
    (ANALYSIS).** Meetings cost more than
    their duration: a 1h meeting at 13:00 splits a 5h afternoon into
    2h+1.5h shards. `parse_ics_intervals` (v7.9) has the actual ranges;
    compute per day the DEEP CAPACITY (sum of free blocks ≥90m) with and
    without each meeting, and report the difference as the real price:
    "Tuesday's 13:00 status call: 1h long, cost 3.1h of deep capacity."
    Weekly total = your fragmentation tax; pairs with the existing
    meeting-load insight (which only counts hours) and gives the user
    ammunition to move a standing meeting to the edge of the day. Needs
    `_busy_data`'s parse window to cover the recent past on master
    (check — the branch widened it once; master's window may differ).

22. ~~**Lag correlations — "what today does to tomorrow" (ANALYSIS).**~~
    — DONE v8.31: `_lag_workout_line`/`_lag_sleep_debt_line`/
    `_lag_evening_start_line` (+ `_day_start_late_map` for the shared
    per-day scan) compose into `_lag_insight`. Original design note kept
    below for reference.
    Every current insight correlates same-day pairs. The new dimension is
    TIME-LAGGED: workout day → next-day output/energy; short sleep →
    NEXT-day output (sleep debt lands late); late-evening work (tracked
    past 21:00) → next-morning first-session start time. Same honesty
    gates (n≥5 pairs per bucket), same day-record data, one new loop
    shape: iterate (day, day+1) pairs instead of days. Output like "the
    morning after a workout day you start 40min earlier and do +0.9h
    (n=14) — the gym is a productivity tool, not a cost." Probably the
    highest insight-per-line-of-code item left.

23. ~~**Sensor health meter.**~~ — DONE v8.53. New
    `_sensor_health_lines`, a new section at the top of the Data
    doctor window: per source (sleep, calendar, ENERGY) last date
    seen, 30-day coverage %, a plain alarm past a reasonable cadence;
    also the personal baselines (median sleep, median week) the
    anomaly watch judges against. Original design note kept below for
    reference.
    (TRUST / USABILITY).** Every insight silently
    degrades when a source rots: the phone sleep-export automation breaks,
    the .ics goes stale, ENERGY stops being typed. One small view (or a
    Data-doctor section): per source — last date seen, coverage % over 30
    days, and a plain alarm line ("sleep import: nothing for 12 days —
    the phone automation likely broke"). Also shows the personal baselines
    the anomaly watch compares against (your normal sleep, normal week),
    making the co-pilot's judgments inspectable instead of oracular. The
    platform watching its own instruments — cheap, and protects everything
    else. Could piggyback on `_health_data`'s existing mtime cache + the
    settings keys for ics/health paths.

24. ~~**Running-hot index / recovery-debt early warning.**~~ — DONE
    v8.41. New `_running_hot_line(recent_days=14, prior_days=60)`:
    same recent-vs-prior window shape as word drift. Four signals
    (sleep vs own norm, workout frequency, late nights, break-ratio
    compression), each independently n-gated; speaks only when >=2
    move together. Hooked into `_copilot_note`. Original design note
    kept below for reference.
    (FEEDBACK).** The
    trajectory line spots a sleep-for-work trade AFTER four weeks; this
    is the early-warning version: a rolling debt score from days of
    sleep-below-your-norm, workout-frequency drop vs baseline, tracked
    minutes past 21:00, and break-ratio compression — surfaced as one
    co-pilot-eligible line only when several move together: "9 days
    running hot (sleep −0.8h/night vs norm, workouts halved, 3 late
    nights) — schedule one flat day before your body schedules it."
    All from existing day-record keys; n-gated; anti-nagging guardrail
    applies (stated once, never repeated daily unless the score worsens).

25. ~~**Planner realism factor — the schedule audits itself.**~~ —
    DONE v8.54. New `_planned_hours_from_file` (parses a past day's
    written schedule block back out, same trick as
    `_estimate_factor`) + `_planner_realism_factor` (median survival
    ratio, capped at 1.0, n≥5 gate). `_day_schedule_lines` scales
    each item's needed hours by the ratio before placing blocks and
    prints the density in the schedule header. Original design note
    kept below for reference.
    (PLANNING).**
    v8.0/v8.8 write a suggested schedule every morning; nothing ever
    checks what became of it. Reconcile each past day's written schedule
    block (parse it back out of the day file — same in-file convention
    trick as `_estimate_factor`) against the csv's actual placed hours,
    and learn a personal plan-survival rate: "your average planned day
    survives 62% — the planner now plans at 62% density instead of
    pretending." Self-calibrating planning WITHOUT compliance tracking of
    the user (the guardrail): it grades the PLANNER's realism, not the
    person, and only changes how much the planner dares to schedule.

26. ~~**Year rhythm map.**~~ — DONE v8.43. New pure
    `_year_rhythm_grid(weeks=52)` ({(week_idx, hour): minutes}) +
    `_year_rhythm_view` canvas, View menu. Mirrors `_heatmap`'s canvas
    code at year scale, by time-of-day instead of day-total. Original
    design note kept below for reference.
    (VISUAL MEMORY).** The heatmap shows how MUCH per
    day; nothing shows WHEN at year scale. One canvas: 52 columns (weeks)
    × 24 rows (hour of day), each cell shaded by tracked minutes in that
    hour that week — your year's shape at a glance: bedtime drift eras,
    morning-discipline phases, the exam-sprint block, the dead summer.
    Pure view over the csv start-times (same parse `_hour_quality` uses,
    widened); ~80 lines mirroring `_heatmap`'s canvas code. The single
    most striking "life memory" visual available for the data already
    collected.

27. ~~**"Where you left off" — context restore on task start.**~~ — DONE
    v8.9. `_last_context(task)` + hooks in the Working-status line and
    `_switch`. Still open (small): a hover/click on the status bar to see
    MORE than one line of the old context; and surfacing it in the Tasks/
    Library window's Start ▶ path too (currently only timer-box starts).

28. ~~**Deadline post-mortem.**~~ — DONE v8.50. New
    `_deadline_postmortem_lines` (pure) + `_run_deadline_postmortems`
    (write-once guard via `postmortem_written` on the deadline dict),
    hooked into `_new_day_header`. Only the "date passes" trigger is
    implemented — the "or its task is Done" trigger was dropped since
    deadlines aren't currently linked to task-library Done status (no
    such linkage exists to hook). `_estimate_factor` extended with an
    optional keyword filter for the per-project figure. Original
    design note kept below for reference.
    (FEEDBACK/MEMORY).** When a scoped deadline's
    date passes (or its task is Done), write one retro block into that
    day's file: scope vs actual hours, the estimate factor on THIS
    project, what the v8.1 projection predicted vs what happened
    ("projection ran 4d pessimistic"), pace curve in one line. Each
    deadline closed becomes calibration data — and the projection engine
    can later quote its own track record ("my forecasts have run ±3d on
    your last 4 deadlines"), which is the honest version of trust.

29. ~~**Energy forecast for today.**~~ — DONE v8.44. New
    `_energy_forecast_line`: last night's sleep + trailing debt
    combined into one signal (3-night rolling average vs personal
    90-day median), bucketed by weekday + rolling-sleep tier;
    matching bucket's 25th-75th percentile tracked-work range is the
    forecast. Hooked into the morning header after the co-pilot note.
    Original design note kept below for reference.
    (ANALYSIS/PLANNING).** Morning header
    line predicting today's likely capacity band from last night's
    imported sleep + trailing sleep debt + your weekday pattern: "today
    smells like a 3.5–4.5h day — put the must-do inside that." The
    weekday capacity table says what you PLAN to have; this says what
    your body's data suggests you'll ACTUALLY have. Same honesty gates;
    feeds the #25 realism direction.

30. ~~**Break quality ledger.**~~ — DONE v8.10 (`_break_insight`, insight
    line, n≥5/bucket; keyword lists `_BREAK_MOVE`/`_BREAK_SCROLL` — extend
    those tuples as real note vocabulary shows up). Shipped alongside the
    **break pull-back** (same commit): `_pull_level` + pill escalation for
    signal-task breaks past `pull_min` (Tools dialog, default 20, 0=off).
    IMPORTANT precedent note: the owner asked for "force me back to work";
    shipped as the strongest STATED nudge (loud, named, beep, two stages)
    and deliberately NOT a lock/gate, consistent with the twice-held
    anti-gating decision. If the owner later reports the pull-back gets
    ignored routinely, the measured escalation path is #30's own data
    (break lengths after pull-back fired) — evaluate before ever
    considering a hard gate.

31. **Morning brief beyond the desktop (USABILITY/PLATFORM).** On day
    rollover, also write a tiny `brief_today.txt` (plan line, co-pilot
    line, schedule, top anomaly) into the OneDrive-synced diary folder —
    so the phone shows the morning brief before the PC is even on. The
    platform escaping the desktop with zero new infrastructure: one extra
    file write into a folder that already syncs. (Check CLAUDE.md
    sensitivity: the brief must contain nothing beyond what the day file
    itself already holds.)

32. ~~**Procrastination pattern map.**~~ — DONE v8.12
    (`_procrastination_insight`, run-length analysis per task, n≥6 starts
    and ≥50% bounce before naming; worst offender only). Still open
    (small): a per-task bounce-rate flag in the Tasks/Library window, and
    counting a flee-into-another-task (switch within 10 min) as a softer
    second bounce type — currently only flee-into-break counts.

33. ~~**Break budget (FEEDBACK — reframe, not police).**~~ — DONE v8.34.
    `_break_budget_line`, wired into the totals line (`_refresh_totals`),
    which is event-driven (toggle/switch/reset/day-roll), not a per-
    second tick — confirmed before adding another `read_rows()` scan
    there. Original design note kept below for reference.
    Instead of judging
    each break, a daily allowance learned from your own good days: "breaks
    so far 74m · your typical by this hour 55m · full-day norm ~90m". One
    status-bar/totals-line segment. Budgets change behaviour where
    per-event nagging fails, and it's just arithmetic over day_index +
    break rows by hour. Guardrail-clean: a number, never a block.

34. ~~**Re-entry ramp.**~~ — DONE v8.11 (`_reentry_opener` + hook in the
    Working-status line when `_last_break_secs >= RAMP_BREAK_SECS`).
    Preference: related library item smallest-est first → smallest signal
    item → any smallest → today's first TODO bullet. Still open (small):
    also fire after idle-detected breaks (currently only explicit
    break→work toggles set `_last_break_secs`), and let a click on the
    status bar put the opener straight into the task box.

35. ~~**Weekly "one less" — subtraction advisor.**~~ — DONE v8.52. New
    `_one_less_candidates` (three sources: meeting fragmentation v8.42,
    procrastination bounce v8.12, after-21:00 work v8.38) + pure
    `_pick_one_less` rotation rule, one line in the Monday review.
    Original design note kept below for reference.
    (FEEDBACK).** Every insight
    adds awareness; this one subtracts a thing. Each Monday review picks
    ONE concrete removal candidate from the data: the recurring meeting
    that splits your best block (#21's math), the 11:00 email check that
    fragments mornings, the after-22:00 work that taxes tomorrow. "This
    week, try one less: X." Rotates candidates, never repeats an ignored
    one twice in a row. Improvement by removal — the most underrated
    productivity move and almost never what software suggests.

36. ~~**Milestones inside a deadline.**~~ — DONE v8.59. New
    `_parse_milestones` (pure, `[Nh]`/`*` convention) +
    `_milestone_progress_line`, an optional "Milestones" column in
    the deadline edit dialog, surfaced in the dashboard next to the
    lifetime ledger/renegotiation lines. Burn-down/projection and a
    per-milestone estimate factor NOT wired in — scoped down to the
    dashboard line only, the highest-value slice. Original design
    note kept below for reference.
    (PLANNING — content, not just hours).**
    `total_h` measures effort, not progress: 30h logged on a 60h scope
    can be 70% done or 20% done. Optional milestone list per deadline
    ("ch4 [15h], ch5 [20h], revisions [10h]" — same [Nh] convention),
    each checked off like a Done-line; burn-down and projection then
    speak in content ("ch4 done, ch5 at 60% of its hours") and the
    estimate factor applies per milestone. The honest fix for "hours
    accrue but is the thing actually getting done?"

37. ~~**Declared short day (PLANNING).**~~ — DONE v8.16
    (`_declared_cap_h`, wired into `_verdict` and the streak's `active`
    closure). Not done: compressing the actual schedule to essentials-
    only for a declared-short TODAY — the schedule is generated once at
    rollover, before a same-day TODAY: line could exist, so this piece
    would need a way to regenerate/refresh it later in the day rather
    than only at creation time. Left open; the verdict/streak
    protection was the higher-value, cleanly-scoped half.

38. ~~**Personal block length — the focus decay curve (ANALYSIS).**~~ —
    DONE v8.15 (`_decay_cycle`/`_block_decay_lines`/
    `_suggested_time_box`). Fixed 15-min buckets rather than a
    continuous curve — simpler, and the reported cycle is a bucket
    boundary, not a precise-to-the-minute figure; revisit only if that
    granularity ever feels wrong in practice. #49's shallow-work ratio
    can now derive its own threshold from this instead of guessing.

39. ~~**AVOID line — the inverse lens (FEEDBACK).**~~ — DONE v8.13.
    Shipped: the header line, carry-forward, and the week-over-week
    arrow next to signal%. Not yet done: crossing avoid-share against
    energy/trajectory in the insights — left for later, needs real
    AVOID history to accumulate before an insight over it would have
    anything honest to say.

40. ~~**First-hour audit (FEEDBACK).**~~ — DONE v8.17
    (`_first_hour_audit`).

41. ~~**Rescue block (FEEDBACK/PLANNING).**~~ — DONE v8.22, folded into
    `_recommend_now` (on-demand, not auto-injected — no "once per day"
    tracking needed since the user chooses when to check).

42. ~~**Monday week-ahead risk brief (FORESIGHT).**~~ — DONE v8.32:
    `_week_ahead_lines` (via `_day_capacity`/`_dl_progress`/
    `_dl_projection`, not the originally-sketched `_free_slots`/
    `_outlook_lines` — simpler primitives that already gave the same
    answer with less composition risk). Still open (small): fold in
    sleep-debt carry-in as originally sketched, and map the tight day
    specifically onto WHICH deadline needs it (currently names the
    tightest day and the behind deadlines as two separate facts, not
    yet "Thu is tight AND that's exactly when Thesis needs its hours").
    Original design note kept below for reference.
    The Monday review looks
    back; nothing yet looks at the WEEK ahead as a whole. One block:
    calendar density per day (free-slot totals), the outlook's late
    deadlines mapped onto those days, sleep-debt carry-in — "this week's
    biggest risk: Thu is 80% meetings while TUTA needs 2h/day; front-load
    to Tue/Wed." Composes _free_slots + _outlook_lines + _sleep_h over
    the next 7 days; the weekly twin of the daily co-pilot line.

43. ~~**Library graveyard sweep (USABILITY/HYGIENE).**~~ — DONE v8.20
    (`_graveyard_lines`). "Untouched" approximated by ADDED date, not a
    true last-touched signal — see the version-history note.

44. ~~**Waiting-on / blocked tasks.**~~ — DONE v8.60. New `blocked_by`
    task-library field (Tasks window right-click > "Set blocked by…")
    + `_waiting_on_lines` (new "WAITING ON:" dashboard section).
    Filtered out of `_reentry_opener` and both "uncommitted hours →
    pick from Task library" lines. `_recommend_now`/`_focus_items`
    turned out NOT to read the task library at all (they're deadline-
    scoped) — the original note's claim there didn't match the actual
    code, so nothing needed filtering there. Original design note
    kept below for reference.
    (PLANNING — external dependencies).**
    Everything the planner knows about is under the owner's own control;
    real work often isn't ("can't touch ch4 until the supervisor replies
    on ch3"). Task-library items gain an optional `blocked_by: <task
    name or free text>` field, set via the existing right-click menu
    (same pattern as Set goal…/Set deadline…). A blocked item is
    excluded from `_recommend_now`, `_focus_items`/the schedule, and the
    "uncommitted hours → pick from Task library" line — the planner
    stops suggesting things you structurally can't do yet. A small
    "waiting on:" list surfaces separately (dashboard or day header,
    TBD) so blocked items don't just vanish, they move to a visibly
    different bucket. No due-date logic, no reminders to chase the
    blocker — that's someone else's problem to solve, not the app's to
    nag about. Cheap: one settings field, one filter applied at the two
    existing read sites.

45. ~~**Goal lifetime ledger.**~~ — DONE v8.49. New
    `_lifetime_ledger_line(name, kws, start_iso)`, one line under each
    goal/deadline in the dashboard's "Deadlines & Goals" tab. Goals
    still have no `start` field (no UI change made for it — absent
    just means "since the first-ever matching row," the honest
    default); deadlines use their existing stored `start` when set.
    Original design note kept below for reference.
    (SELF-KNOWLEDGE — the un-windowed view).**
    Every current view is windowed — 8 weeks (alignment, trajectory),
    a deadline's own scope (burn-down), a calendar year (#15). Nothing
    answers "how much of my life has this actually taken, total, since
    I started it" — a goal or long-running deadline's true lifetime
    cost. One line per goal/deadline: "Thesis: 187h across 62 sessions
    since 2026-06-29 (134 days — 1.4h/day lifetime average)." Reuses
    `matched_minutes` from the goal/deadline's `start` (already stored
    on deadlines; goals would need one, defaulting to first-ever-seen
    in the csv if absent) through today — no new data source, just the
    lens run over its full history instead of a trailing window. Sits
    naturally in the Goals dialog or a new one-line addition to the
    dashboard's Deadlines/Goals tab. Answers a different question than
    #15's year-in-review (a goal's whole life vs. a calendar year) and
    a different one than #28's post-mortem (ongoing running total vs.
    a one-time verdict after the fact).

46. ~~**Deadline renegotiation tracker.**~~ — DONE v8.51. New
    `_deadline_revisions_after_save` (pure, wired into the existing
    edit dialog's save()) + `_deadline_renegotiation_line`, surfaced
    in the dashboard next to the lifetime ledger line. Original design
    note kept below for reference.
    (SELF-KNOWLEDGE — scope-creep
    honesty).** Deadlines can have their `date` or `total_h` edited at
    any time, silently — nothing remembers the ORIGINAL numbers. Log
    every edit to a deadline's date/scope as a small history list on
    the deadline object itself (`[{"date": "...", "total_h": ..., "as_of":
    "..."}]`, appended on save in the existing edit dialog, not a new
    UI). Once 2+ revisions exist, the deadline views gain one honest
    line: "this deadline has moved 3 times since 06-29 — due date is now
    45 days later than first set, scope grew from 20h to 45h." Different
    from #28's post-mortem (which only fires once, after the deadline
    resolves): this is a live, ongoing pattern check, catching the
    difference between genuinely re-scoping reality and repeatedly
    deferring the same discomfort. No judgment beyond stating the
    pattern — the honesty is entirely in the
    number, not in a verdict.

47. ~~**Behind-pace root cause: capacity vs. choice (PLANNING).**~~ —
    DONE v8.14 (`_root_cause_line`, wired into the burn-down window's
    footer alongside the projection line). Uses `_dl_progress`'s own
    `behind` flag directly rather than re-deriving it.

48. ~~**Lens overlap check (TRUST/HYGIENE — the honesty layer auditing
    itself).**~~ — DONE v8.35. `_lens_registry` + `_lens_overlap_lines`
    + View > "Lens overlap check…" (own window, not folded into
    `_insight_lines` — an O(pairs × days × tasks) nested scan didn't
    belong in the per-refresh insight path; deliberately opened on
    demand like Data doctor). Original design note kept below.
    Nothing currently checks whether two goals/domains/
    deadlines share keywords. If "run" matches both the Body domain and
    a "GMAT prep" goal by a copy-paste accident, that hour silently
    double-counts toward two different percentages — every honesty-gated
    number in the app (alignment shares, signal%, goal minutes) assumes
    the lenses are disjoint, and nothing verifies that assumption. A
    Data-doctor-style scan (or its own Tools entry): for every pair of
    declared lenses (goals × goals, goals × domains, domains ×
    deadlines), check keyword-list overlap and — more usefully — check
    whether they actually matched the SAME real task names in history,
    not just whether the keyword strings collide. One line per real
    collision: "'run' matches both Body and GMAT prep — 4.5h counted
    toward both this month." Cheap (nested loop over already-small
    keyword lists + a day_index scan), high trust payoff since it
    protects every % the app has ever printed.

49. ~~**Shallow-work ratio (ANALYSIS).**~~ — DONE v8.19
    (`_shallow_work_lines`, threshold from #38's `_decay_cycle` when
    available). Gated on 1h+ of signal work today, ≥50% shallow to
    speak.

50. ~~**Protected time windows.**~~ — DONE v8.58. New Tools >
    "Protected time windows…" (grid dialog, same pattern as Goals/
    Deadlines) + `_protected_intervals`, subtracted from `_free_slots`
    exactly like calendar busy-time already is. Original design note
    kept below for reference.
    (PLANNING — the scheduler's missing
    exclusion zone).** `_work_window` (v7.9) sets one daily envelope the
    scheduler is allowed to fill; nothing stops it suggesting a block
    over lunch, a wind-down hour, or any other time that's technically
    "free" but shouldn't be claimed. Tools > add named protected
    windows ("lunch 12:00-13:00", "wind-down 21:00-22:00") — a small
    settings list of (label, start, end) subtracted from `_free_slots`
    exactly like calendar busy-time already is. Small, direct extension
    of existing v7.9/v8.0/v8.8 scheduler infrastructure — one more
    source of "busy" intervals merged into the same primitive, not a
    new concept.

51. **Second opinion on SIGNAL — rare and purely observational
    (SELF-KNOWLEDGE, guardrail-sensitive).** SIGNAL is a daily
    declaration; nothing currently checks whether the declaration
    matches where the hours actually went. After several consecutive
    days where a DIFFERENT task consistently outpaces the declared
    SIGNAL, one careful, rare line: "you've called Thesis signal 5 days
    running, but TUTA got more hours each time — worth asking whether
    TUTA is the real signal right now." **Must be built carefully, not
    casually**: this is the closest any idea here comes to the
    twice-held anti-gating precedent (#9's Reopening Guard,
    the pull-back's own precedent note at #30) — it must stay a single
    quiet observation, not a repeating nag, not a thing that tracks
    whether you "listened," and probably should fire at most once every
    couple of weeks even if the pattern persists daily. If it starts
    feeling like the app second-guessing every SIGNAL choice, cut it —
    that's the same failure mode the guardrail already names.

52. ~~**Cost of yes — a prospective preview before committing to a
    new deadline.**~~ — DONE v8.61. New
    `_cost_of_yes_line(hypothetical, existing)` reusing
    `_avail_hours`/`_capacity_lines`'s aggregate-slack math, wired as a
    live keystroke-updated preview in the deadline edit dialog for a
    genuinely NEW row only (editing an existing deadline in place is
    v8.51's renegotiation tracker's territory instead). Original
    design note kept below for reference.
    (PLANNING — the capacity math run BEFORE, not after).**
    Every capacity view (`_capacity_lines`, `_plan_line`, #47's root
    cause) looks at deadlines already on the books. Nothing shows what
    ADDING one would actually do before you commit. In the deadline
    dialog, as soon as total_h + due date are both filled in, one live
    line: "committing to this would push Wednesday's slack from +3h to
    -2h — Thesis would need to give up 2h/day to make room." Pure
    reuse of `_avail_hours`/`_capacity_lines`'s existing math, run
    against a hypothetical extra deadline instead of a real one — no
    new data, just running the same function one keystroke earlier
    than it currently ever gets run. Turns the moment of over-
    committing (which currently only shows up as a ⚠ days or weeks
    later) into a visible choice at the only point it's still cheap to
    say no.

53. ~~**Focus signature — hour-of-day × day-of-week, not either
    alone.**~~ — DONE v8.63. New `_focus_signature_grid` (consistency
    %, not raw totals, per (weekday, 4h-bucket) cell) +
    `_focus_signature_line`, in the Monday review. n≥4 occurrence gate
    per weekday, ≥50% consistency bar to speak at all. Original design
    note kept below for reference.
    (SELF-KNOWLEDGE — the shape of a real week).** The weekday-pattern
    insight (v7.4) compares total HOURS per weekday; `_hour_quality`
    (v8.8) compares total hours per hour-of-day, collapsed across every
    weekday. Neither shows the actual two-dimensional shape: WHEN,
    within which days, signal work reliably happens. A compact text
    grid (7 rows × a handful of hour-buckets, weeks aggregated) —
    "Tue/Wed 09-12 lights up consistently; Fri afternoons never do" —
    read once in a while, not a daily view. Reuses `read_rows`/
    `task_matches` over the SIGNAL lens; needs real volume (many weeks)
    before a 2D grid has enough samples per cell to mean anything, so
    this is a "check back once you have months of history" feature, not
    an early one.

54. **Deadline estimate reality-check at creation (PLANNING —
    depends on #10's per-category estimate factor).** #10's recovered
    idea (per-category `_estimate_factor`, not yet built — not enough
    Done-line data existed at the time) would know that thesis-type
    tasks historically run at some real multiple of their estimate. The
    natural consumer of that number: apply it at the moment a NEW
    deadline's total_h gets typed, before the commitment is made —
    "your thesis-type estimates have run ×2.4 historically; this 20h
    scope has previously meant more like 48h." Not a correction, not a
    forced field — one line next to the input, same spirit as #52's
    cost-of-yes but auditing the NUMBER itself rather than the
    calendar. Explicitly sequenced after #10 — nothing to build here
    until that data exists.

55. ~~**Task-library commitment density (SELF-KNOWLEDGE/HYGIENE).**~~ —
    DONE v8.21. Header label in the Tasks/Library window, updates on
    every `refresh()`.

56. ~~**App usage-pattern meter (META).**~~ — DONE v8.24 (`_tracked`
    wrapper on View-menu commands, `_usage_win` under Tools > "Feature
    usage…"). Counts total opens, not recency — the "unused in 60
    days" framing from the original idea would need a timestamp per
    command, not just a count; left as a possible refinement, not
    built.

57. ~~**Conversation-ready status export.**~~ — DONE v8.62. New
    `_status_update_text`/`_status_update_all` + a "Copy status
    update" button in the Life dashboard. Also pulls in v8.60's fresh
    `blocked_by` field for the blockers sentence, a connection the
    original note couldn't have anticipated since #44 didn't exist
    yet. Original design note kept below for reference.
    (USABILITY — a different
    audience than #14/Copy-for-AI-review).** Copy-for-AI-review is
    written for feeding an LLM; nothing is written for pasting into an
    email to an actual supervisor/advisor. A "Copy status update"
    command producing a short, professionally-toned paragraph from
    numbers already computed: "Progress update — Thesis: 12h this week
    (up from 8h last), on pace to finish ch4 by the 23rd. No blockers."
    Reuses `_dl_progress`/`_dl_projection`'s own numbers, just a
    different register of sentence than the rest of the app's blunt
    internal voice — worth being explicit that this ONE surface should
    sound different on purpose (external-facing), not a precedent for
    softening anything else.

58. ~~**Best-weeks retrospective (SELF-KNOWLEDGE).**~~ — DONE v8.25
    (`_best_weeks_lines`). Shipped the day-of-week signature; avoid-
    share/meeting-load/sleep cross-referencing from the original idea
    left for later — day-of-week alone was already a real signal.

59. ~~**Reallocation scenario (PLANNING).**~~ — DONE v8.26
    (`_reallocation_line`, in `_capacity_lines`). Scoped to TODAY's
    capacity specifically (matching #47's own timeframe), not the
    "0.5h/week for 3 weeks" multi-week framing in the original sketch —
    a simpler, more honest version of the same idea.

60. **Embedded Python console — DELIBERATELY NOT NOW, needs real
    design first (2026-07-13, owner's own ask).** The owner floated
    "more commands or code that could run inside itself" specifically
    to practice terminal/Python casually and passively — not a power-
    user feature request, a learning one. Explicitly told not to ship
    this without more thought first; written up here so the thinking
    isn't lost, not as a green light.
    - **The actual hook, if built**: not a generic Python REPL (that's
      just IDLE with extra steps) — a console pre-loaded with the
      owner's OWN data as ready variables (`rows`, `goals()`,
      `day_index()`, `matched_minutes`, the lens primitives already in
      this file). Practicing Python by querying your own real life
      data ("how many hours did I spend on thesis in June") is a
      fundamentally more motivating exercise than abstract tutorial
      problems — the same instinct behind the whole platform (use
      real data, not toy examples).
    - **The real risk, stated plainly**: `exec()` inside an app that
      also holds the only copy of years of personal history is a
      different class of surface than anything else built so far —
      one typo (`del rows[:]`, a stray `save_settings`) could damage
      real data in a way nothing else in this app can. If built, the
      console should almost certainly be READ-ONLY by construction:
      pre-loaded copies/pure functions, no bound reference to
      `self.settings` or a live write path, maybe even a fully
      separate temp-copy sandbox rather than trusting scoping
      discipline alone.
    - **Architecturally**: this doesn't fit the source→lens→view
      concept model at all — it's a genuinely new CATEGORY (a
      developer/meta surface, not a life-tracking one), the same kind
      of "first of its kind" moment domains (v8.4) was for values.
      Worth being honest that it changes what kind of app this is, at
      least a little, before committing to it.
    - **Smallest safe version to prototype with, if this gets picked
      up later**: a single Tools menu entry, a Text widget for input +
      output, `eval()` (not `exec()`, expression-only, no statements)
      against a read-only namespace built fresh each time from copies
      of `read_rows()` and the lens functions — no path back to the
      real settings.json or sessions.csv at all in v1.

61. ~~**Time capsule — the forward counterpart to on-this-day.**~~ —
    DONE v8.56. New `_due_capsules`/`_capsule_lines`, hooked into
    `_new_day_header` next to the on-this-day line. Original design
    note kept below for reference.
    (MEMORY).**
    #12 (done) looks backward one year automatically. Nothing lets the
    owner deliberately seal a message for a FUTURE date — write
    yourself something today that only surfaces on a milestone day
    (defense, deadline, birthday). A `CAPSULE: 2026-08-15 | message`
    line in today's file; on the target date, the header surfaces it:
    "a note from 45 days ago: message." Pure text convention + a scan
    across day files for capsule lines whose date matches today — no
    new data source, same shape as TODO carry-over. Emotionally simple
    and, unlike most of this backlog, not diagnostic of anything.

62. ~~**Decision log lite — searchable, NOT the rejected #9
    mechanics.**~~ — DONE v8.47. New `DECIDED: <topic> — <verdict>`
    line convention + pure `_scan_decisions` + View > "Decision
    log…" (read-only, newest first). No counter, no reopening
    friction, no unlock mechanic — if this ever starts growing
    enforcement logic, it has become #9 again, stop. Original design
    note kept below for reference.
    (SELF-KNOWLEDGE).** #9's Reopening Guard (reopen counters, typed
    justification to unlock) was explicitly held back as too close to
    a gating pattern — that verdict stands, this is a different,
    smaller idea: a plain `DECIDED: <topic> — <verdict>` line, purely
    archival, searchable via #14's ask-your-diary once that exists (or
    the existing Search all days meanwhile). No counter, no reopening
    friction, no unlock mechanic — just makes "wait, didn't I already
    think this through" answerable by search instead of memory. If
    this starts growing enforcement logic, it has become #9 again —
    stop.

63. ~~**Backup integrity check.**~~ — DONE v8.40. New module-level
    `backup_integrity_line()`, silent when the newest `backups/` csv
    is ≤10 days old, else "last backup: 15 days ago (expected weekly)
    — the automation may have stopped" (or "no backup found yet").
    Surfaced on the Data doctor window. Original design note kept
    below for reference.
    (TRUST — the safety net auditing
    itself). #23 (sensor health meter) covers external INPUT sources
    going stale (health export, calendar); nothing checks the OUTPUT
    safety net — the weekly `backups/` csv copies — is actually
    current and restorable. One line, checked opportunistically (e.g.
    on Data doctor run): "last backup: 9 days ago (expected weekly) —
    the automation may have stopped." Directly on-brand given the
    2026-07-11 dual-instance data-loss incident (CLAUDE.md) — the kind
    of check that's cheap until the day it isn't.

64. ~~**Annual theme.**~~ — DONE v8.48. New `YEAR: <theme>` line, new
    `_carry_year` (same shape as `_carry_avoid`), auto-carried into
    every day; the on-this-day line now surfaces that year's theme
    when one was set. #15's year-in-review still doesn't exist so
    that reference is deferred. Original design note kept below for
    reference.
    (PLANNING/VALUES — the year-scale sibling of
    SIGNAL/AVOID).** SIGNAL declares today's focus; AVOID (v8.13) is a
    standing declaration; nothing declares at the YEAR scale. A
    `YEAR: <theme>` line, set once and carried (same carry-forward
    shape as AVOID), referenced by #15's year-in-review once that
    exists and by the on-this-day line ("a year ago, your theme was
    X — still true?"). Not a new mechanism, the same lens-declaration
    pattern one size up — the question is whether a single yearly
    theme is honest at this app's current maturity or premature until
    more multi-year data actually exists to make it mean something.

65. ~~**Health-hub view (VISUAL/HEALTH — the home for v8.27's captured
    data).**~~ — DONE v8.36. Landed as a SECOND table in the same
    `_health_view` window rather than widening the existing table into
    one ~90-char row — same "extend, don't replace" spirit as originally
    asked, just a layout call made once the column count (mindful, RHR,
    HRV, weight, AND daylight — one more than this note anticipated)
    made one flat row impractical. `_health_extras_lines` split out as
    pure logic for testability, matching every other feature this
    session. Still open: n-gated trend arrows once real HRV/RHR history
    exists, exactly as this note originally asked — not attempted yet,
    genuinely needs the real data to accumulate first.
    RHR/HRV/weight are now captured onto `_life_day` (v8.27)
    but only mindful minutes reached a visible surface (the header line)
    — the rest is sitting in the record unseen, which is exactly the
    "capture now, surface later" gap this backlog exists to close.
    EXTEND the existing `_health_view` table (14-day sleep/workout/
    steps/work/signal/energy grid) with mindful/RHR/HRV/weight columns
    rather than building a rival window — matches the concept model's
    "don't duplicate a view" precedent (see backlog #1's dashboard-as-
    hub decision). Trend arrows only once real history exists (n-gated,
    same honesty rule as everywhere else); most users' HRV/RHR history
    will be thin at first, so this should degrade gracefully to "not
    enough data yet" per metric rather than blank columns.

66. ~~**Metrics shorthand — lower friction than key=value.**~~ — DONE
    v8.33. Ended up rewriting the parser to split-by-comma-then-match-
    per-token rather than "one alternate regex branch" as originally
    sketched (needed to reliably tell a bare word apart from a malformed
    key=value token on the same line) — same end result. Still open:
    #19's quick-capture hotkey to pair with it.
    (USABILITY, pairs with #19 quick-capture). METRICS (v8.27) requires typing
    `key=value`; for simple yes/no habits (meditated, cold shower, took
    magnesium) that's more typing than the fact deserves. A shorthand:
    a bare word in the METRICS line with no `=` implicitly logs
    `word=1` — "METRICS: meditation, cold_shower" instead of
    "meditation=1, cold_shower=1". Almost free on top of
    `_metrics_from_text`'s existing regex (one alternate branch for a
    bare identifier); the generic insight (`_metrics_insight`) needs no
    change at all, since it already just checks presence-of-key. Natural
    partner for #19's quick-capture hotkey — a one-keystroke popup that
    writes straight into today's METRICS line.

67. **Supplement/stack tags — proof METRICS needs no new code per idea
    (SELF-KNOWLEDGE).** Not a new mechanism — a documented CONVENTION on
    top of METRICS/#66: log each supplement as its own bare word
    ("METRICS: magnesium, omega3") and `_metrics_insight` already finds
    whichever one correlates with a signal-share swing, with zero new
    code. Worth writing down as an explicit example in the README/Tools
    tooltip once #66 ships, specifically because it demonstrates the
    "capture now, ask questions later" architecture answer above in a
    concrete biohacking use the owner named directly.

68. **Readiness line from HRV/RHR baseline (ANALYSIS/PLANNING — the
    payoff for capturing HRV/RHR at all).** Once real HRV/RHR history
    accumulates (this is the actual gate — v8.27 only just started
    capturing them, so this should NOT be attempted until there's a
    real multi-week baseline to compare against, same discipline as
    every other insight here), a morning line comparing today's HRV/RHR
    to a trailing personal baseline: "HRV 15% below your 30-day norm,
    RHR +4bpm — a lighter day may pay off more than pushing." Feeds
    naturally into `_recommend_now`/`_energy_place` as a capacity
    signal alongside sleep, the same way sleep already informs energy
    insights. Explicitly NOT a training-load app clone — one honest
    line, same restraint as the rest of the co-pilot surfaces, never a
    gate on what the schedule allows.

69. ~~**Word drift v2 — what you've stopped writing about.**~~ — DONE
    v8.37. `_word_drift_counts` factored out so both directions share
    one file scan; `_word_fade_insight` is the decrease side, reported
    separately as designed. Original design note kept below.
    (MEMORY, the
    other direction of v8.29). `_word_drift_insight` only ever reports
    words trending UP. The DECREASE direction is at least as telling —
    a topic that was frequent and went quiet (a person, a worry, a
    plan) often matters more than a new one appearing. Same
    `_diary_word_counts` machinery, same two windows, just the opposite
    score sign: candidates where `pri_pct` was real and `rec_pct` has
    collapsed toward zero (symmetric gate: pn≥3 in the OLD window,
    rec_pct ≤ pri_pct/3 or literally zero now). Report separately from
    the existing increase line, not merged into one — "up" and "down"
    are different kinds of noticing and shouldn't compete for the same
    slot. Reuses everything v8.29 built; this is a second scoring pass
    over data already gathered, not a new source.

70. ~~**Lag correlation #4 — yesterday's fragmentation → today's shallow
    work.**~~ — DONE v8.38. `_shallow_threshold`/`_day_shallow_frac`
    factored out of `_shallow_work_lines` so the same block-shallowness
    logic works for any day, not just today; `_lag_fragmentation_line`
    is the fourth check in `_lag_insight`. Original design note kept
    below for reference.
    (ANALYSIS, extends v8.31's new loop shape). v8.18's task-
    thrash meter and v8.19's shallow-work ratio both exist as SAME-day
    checks; v8.31 proved the (day, day+1) lag shape is cheap to add
    once the loop exists. Natural fourth pairing: does a high-switch day
    predict a shallower NEXT day (more of the following day's signal
    hours landing in sub-20-minute blocks)? Reuses `_day_switches`
    (v8.18) for the bucket split and the block-length classification
    already in `_shallow_work_lines` (v8.19) for the next-day measure —
    genuinely just wiring two existing measurements through the
    (day, day+1) loop `_lag_workout_line` already demonstrates, not new
    math. Same n≥5/bucket gate as every other lag check.

71. ~~**Ask-your-diary: pinned searches.**~~ — DONE v8.46. New pure
    `_pinned_after_add`/`_pinned_after_remove` behind `_pin_search`/
    `_unpin_search`; a pinned-search button row in "Search all days,"
    settings-backed, capped at 5. Original design note kept below for
    reference.
    (USABILITY, extends v8.30).** Every
    search in the "Copy matching days for AI" window (v8.30) is typed
    fresh. A short `settings["pinned_searches"]` list (5ish saved query
    strings — "landlord", "advisor", a project codename) surfaced as
    buttons/a dropdown next to the query box turns a recurring lookup
    ("what did I decide about the advisor situation, again") into one
    click instead of retyping. Pure UI addition over `_diary_rank_days`,
    which already takes an arbitrary query string — no change to the
    ranking logic at all, just a shortcut to populate the entry.

72. ~~**Break budget v2 — weekday-specific norms.**~~ — DONE v8.39.
    `_break_budget_line` buckets `real_days` by weekday and uses
    today's own weekday's median once it has its own n≥10, falling
    back to the all-days blend otherwise. Original design note kept
    below for reference.
    (ANALYSIS, extends v8.34). `_break_budget_line` currently blends ALL real workdays
    into one median "full-day norm" regardless of weekday — but Friday
    afternoons and Tuesday mornings plausibly have genuinely different
    real break patterns, and blending them into one number is less
    honest than the weekday-aware capacity table (`_capacity()`, per-
    weekday since v5.8) the rest of the app already assumes. Bucket
    `real_days` by `dt.date.fromisoformat(iso).weekday()` before taking
    the median, falling back to the all-days blend when a specific
    weekday doesn't have its own n≥10 yet (most users won't, at first —
    the honesty gate should degrade per-weekday, not go silent
    entirely). Same shape as the existing function, one more grouping
    key.

73. **Weekday-aware peak-hour profile (PLANNING, extends `_hour_quality`
    v8.0 + the year rhythm map's grid shape, v8.43).** `_hour_quality`
    collapses ALL history into one 24-hour profile — but the year
    rhythm map just proved (week, hour) is a shape worth keeping
    separate, and break budget v2/energy forecast (v8.39/v8.44) both
    found real value in bucketing by weekday specifically. Widen
    `_hour_quality` to a (weekday, hour) grid — Monday mornings and
    Friday afternoons plausibly have genuinely different real peaks,
    not one blended curve — feeding `_energy_place`/`_recommend_now`
    a sharper signal, falling back to the flat 24-hour profile when a
    specific weekday doesn't have its own n≥20h yet (same degrade-not-
    silence discipline as every weekday-bucketed check this session).

74. **Deadline crunch cost (ANALYSIS, a lag-style check reusing the
    running-hot machinery, v8.41, against deadline PROXIMITY instead
    of weekday timing).** The running-hot index watches sleep/workout/
    late-nights/break-ratio drift over a rolling window; this asks the
    same question anchored to a different clock — the 7 days before a
    scoped deadline's due date, compared against the person's normal
    baseline. "The week before a deadline, you average 1.1h less sleep
    and 2x the late nights — crunch has a real cost, not just a
    feeling." Reuses `_week_metric_totals` (v8.45) directly: baseline
    = trailing weeks NOT adjacent to any deadline, crunch = the week
    immediately before `dl["date"]`. n-gated on real deadline history
    (needs several past deadlines to compare, not just the live one).

75. **Experiment history ledger (MEMORY, the natural follow-up to the
    weekly experiment engine, v8.45).** Once a few `EXPERIMENT:` lines
    exist, nothing lists them together. A view scanning every day file
    for an `EXPERIMENT:` line + the `_experiment_review_line` verdict
    that ran for it the following Monday (already generated and
    sitting in that week's file — this is a READ, not a new
    computation) — "3 experiments this quarter: no work after 21:00
    (sleep +0.5h, kept); no phone before 09:00 (no measurable
    change)." Turns a string of one-off self-experiments into a
    trend the person can actually learn from, same "the day file is
    the source of truth, this just reads it back" pattern as the
    on-this-day / themed-writing views.

76. **Experiment suggestion — closing the loop the OTHER direction
    (FEEDBACK, extends the lag-correlation family, v8.31/v8.38, and
    the experiment engine, v8.45).** The experiment engine measures a
    SELF-CHOSEN change; nothing suggests WHICH change might be worth
    trying. When a lag-correlation insight clears an unusually strong,
    well-gated effect (e.g. `_lag_evening_start_line`'s swing is large
    and n is comfortably past the gate), one line — stated ONCE, never
    repeated, never auto-inserted into the file — proposes the
    matching `EXPERIMENT:` text the person could paste in themselves:
    "your data suggests this might be worth testing: EXPERIMENT: no
    work after 21:00 (copy into Monday's header if you want to try
    it)." Purely a suggestion the user acts on or ignores — the
    guardrail this session held everywhere else (stated once, never a
    gate, never re-nagged) applies here at its sharpest, since this is
    the one feature that could tempt turning insight into instruction.

77. **Annual theme retrospective (MEMORY, extends the annual theme,
    v8.48, with the same "close the loop when it ends" shape v8.50's
    deadline post-mortem introduced).** v8.48 lets a `YEAR:` theme
    carry silently forever; nothing ever looks back once a theme
    actually changes (a new `YEAR:` value replaces the old one) or a
    full calendar year completes. When that happens, one retro block
    into that day's file: how many days the old theme ran, how many
    `DECIDED:` lines (v8.47) and `EXPERIMENT:` runs (v8.45) happened
    under it, and — if the theme's wording plausibly overlaps a
    declared goal or domain's keywords — the tracked hours that
    actually went there while it was standing. Not a verdict on
    whether the year was "good," just the honest record a theme
    closing deserves, same restraint as the deadline post-mortem.

78. **Sensor health trend (TRUST, extends the sensor health meter,
    v8.53, from an opportunistic snapshot to an early warning).** The
    meter only speaks when Data doctor is opened by hand — a source
    can rot for weeks before anyone happens to check. Add one
    Monday-review line (same slot as the one-less advisor, v8.52, and
    the experiment review, v8.45) comparing THIS week's per-source
    coverage % against the trailing 4-week baseline: "ENERGY logging
    dropped from 90% to 30% this week — still worth typing, or has it
    quietly stopped mattering?" Reuses `_sensor_health_lines`'
    per-source coverage math, windowed instead of all-time; same
    honesty gate (a real week of history on both sides), same
    once-stated-never-nagged restraint as everything else surfaced in
    that slot.

79. **Planner realism per-weekday (PLANNING, extends the planner
    realism factor, v8.54, with the weekday-bucketing pattern this
    session proved out three times over — break budget v2 #72, energy
    forecast #29, running-hot's weekday match).** `_planner_realism_factor`
    blends every scheduled day into one median regardless of weekday —
    but a Monday plan (written fresh, more optimistic) and a Friday
    plan (written tired, already more honest) plausibly survive at
    genuinely different rates. Bucket by `dt.date.weekday()` before
    taking the median, same degrade-to-the-blend-until-n≥10 discipline
    used everywhere else this pattern has shipped. `_day_schedule_lines`
    would then scale today's items by TODAY's own weekday's density,
    not the all-days blend.

80. **METRICS streak tracker (FEEDBACK, extends the bare-word
    shorthand, v8.33, into new territory rather than another
    extension of an existing retrospective).** `METRICS: meditation,
    cold_shower` logs a habit as a bare yes/no in seconds, but nothing
    has ever counted the RUN — how many consecutive days a given
    metric key has appeared. One line per tracked habit, wherever
    METRICS already gets summarized: "meditation: 12-day streak
    (longest ever 18, started 2026-05-02)." Pure scan over the same
    METRICS lines the app already parses (`_metrics_from_text`/
    `_day_metrics`), no new source, no new UI to configure which
    habits to track — whatever key appears becomes trackable the
    moment it's typed, same zero-config spirit as METRICS itself.

81. ~~**Screen-lock break detection — Windows+L should trigger a
    break.**~~ — DONE v8.55. Direct owner request (2026-07-15): "very
    often forget to log a break cuz using windows+L shortcut for
    locking screen." New `is_locked()` (OpenInputDesktop ctypes trick,
    stdlib only) + `_watch_lock` (called from `_tick`, reuses the
    EXISTING `_offer_idle_break` retro-split dialog on unlock — no new
    UI). No idle_min threshold wait — a lock is deliberate regardless
    of duration, just a 30s (`MIN_LOG_SECS`) floor against an
    accidental tap-and-untap. Deliberately NOT suppressed by meeting-
    mode's `idle_off_until` (that's for ambiguous no-input time during
    a call; an actual lock is unambiguous even mid-meeting).
    **UNTESTED by the selftest harness** — same category as the
    pre-existing `idle_seconds`/`_watch_idle` idle detection, a live-
    Windows-only interaction this Linux dev environment cannot
    exercise. Needs manual confirmation on the owner's real machine
    that locking and unlocking actually pops the break-offer dialog;
    if `OpenInputDesktop`'s exact access-rights argument turns out to
    need tuning on their Windows version, that's the first thing to
    check.

82. ~~**Protected windows should shrink the capacity totals too, not just
    the scheduler.**~~ — FIXED v8.69. New `_protected_hours()` sums
    `_protected_intervals()` (the same intervals `_free_slots` already
    subtracts) into a plain daily-hours figure; `_day_capacity` now
    subtracts it alongside busy-calendar time. `_avail_hours` and
    `_capacity_lines`/cost-of-yes inherit the fix for free since they
    both already route through `_day_capacity`.

83. ~~**Milestone-aware status export.**~~ — FIXED v9.2. Credit math
    factored out of `_milestone_progress_line` into `_milestone_credit`
    (shared by both renderings); `_status_update_text` now says
    "Currently on ch5 (60% of its hours)" when milestones exist, falls
    back to the date-based phrasing otherwise.

84. ~~**Cost of yes should surface pre-existing blocked work under the
    same goal.**~~ — FIXED v8.69. `_cost_of_yes_line` takes a `goal`
    key on `hypothetical` now (the deadline-editor's live preview
    passes the row's goal combobox value); when set, counts
    `blocked_by` task-library items sharing that goal and appends
    "heads up: N task(s) under 'X' are already blocked". Silent when
    no goal or nothing's blocked, same as before.

85. **Reconcile the focus signature grid with the weekday-aware
    peak-hour profile idea (ANALYSIS — avoid building the same 2D grid
    twice, supersedes/refines #73).** #73 (still open) proposed
    widening `_hour_quality` into its own (weekday, hour) grid for the
    scheduler; v8.63's `_focus_signature_grid` already computes a
    (weekday, 4h-bucket) CONSISTENCY grid for a different purpose
    (self-knowledge, not scheduling). Before building #73 as a second,
    separate grid, check whether the scheduler's peak-hour quality
    profile can be DERIVED from the signature grid's own buckets
    instead (consistency-weighted, at finer hour resolution) — one 2D
    computation feeding two consumers, not two nearly-identical ones
    maintained in parallel.

86. ~~**Group/prioritize `_insight_lines()`.**~~ — FIXED v8.69. Went
    with design option (a), thematic grouping, not (b) severity
    ranking — no severity/actionability score exists yet and backlog
    #56's usage-meter data hasn't accumulated enough to build one
    honestly. Each of the 20+ finding generators is now tagged with
    one of three themes (TIME & FOCUS / ENERGY & BODY / MOMENTUM &
    TRENDS) at the point it's generated — `_insight_lines_grouped()`
    returns `[(theme, line), ...]`; `_insight_lines()` is now a thin
    flat-string wrapper for the one caller that doesn't need themes
    (life review's top-3 excerpt). The Insights tab and Copy-for-AI-
    review both render the three theme sub-headers. Revisit option
    (b) later if #56's data ever gets there — ranking by what's
    actually acted on beats a fixed theme order.

87. **Coverage map — are we actually using what we already have
    (TRUST — the data-completeness answer, made checkable instead of
    just argued).** The 2026-07-14 "data architecture" section makes
    the case that regret is cheap because parsers can be widened
    retroactively; nothing lets the owner actually SEE the gap between
    what a source COULD offer and what's currently read. One view:
    per source (health export, .ics, METRICS keys actually used in
    the last 90 days) — for health, list any CSV column present in
    the real export file that `parse_health_dir` doesn't currently
    read (a schema diff, not a guess); for METRICS, list which keys
    have actually been typed vs. sitting unused as an idea. Turns
    "hope we're catching everything" from a feeling into a checklist
    that's either empty (reassuring) or actionable (a specific column
    to widen the parser for). Complements #23/sensor-health (which
    checks a source hasn't gone STALE) from the opposite angle — this
    checks a live source isn't being read INCOMPLETELY.

88. **Catch-up digest — "since you last opened this" (USABILITY —
    the growing-surface-area answer for return visits).** With 85+
    views/insights now built, a dashboard opened after a gap currently
    shows the same static snapshot as always — nothing frames what's
    NEW since the owner last actually looked. One line at the top of
    the dashboard, using #56's usage-counter timestamps (would need
    upgrading from a count to a count+last-seen pair — noted as a
    dependency, not built yet): "since you last opened this (12 days
    ago): Thesis moved to behind-pace, a new best week happened, 2
    fresh anomalies." Turns a big static feature surface into
    something that reads like catching up, not re-deriving everything
    from scratch every time.

89. **In-app "what's new" viewer (USABILITY — dirt cheap, directly
    on point).** The docstring at the top of `timer_diary_v5.py`
    already has a perfectly-structured "New in vX.Y (...)" block per
    version, written every single time — nobody currently reads it
    except whoever opens the source file. Tools > "What's new…":
    parse the last 5-10 "New in vX.Y" blocks straight out of the
    module docstring (already-written text, zero new authoring) into
    a scrolled window. The single cheapest, most direct answer to "I
    have a lot of features and don't fully remember what's in here
    anymore" — no new data, no new writing, just surfacing text that
    already exists every time a version ships.

90. **Backlog graveyard sweep — the hygiene pattern applied to itself
    (PROCESS, not code).** #43 sweeps Task-library items untouched 60+
    days; this backlog itself has grown to 90 items in a handful of
    sessions and will keep growing. Not an app feature (HANDOFF.md
    isn't data the running app reads) — a standing convention for
    future sessions instead: periodically (say, every +20 items, or
    whenever a session opens this file to add new ideas) scan for OPEN
    items proposed 60+ days ago that never got picked up, and ask
    explicitly whether they're still wanted, same as #43 asks about
    task-library items. Keeps the backlog itself from becoming exactly
    the kind of untrustworthy pile #43 was written to prevent
    elsewhere in the app.

91. ~~**Completed-task archive (SELF-KNOWLEDGE/HYGIENE).**~~ — DONE
    2026-07-29. `_mark_task_done` appends to `settings["tasks_done"]`
    (name/est_h/priority/goal/deadline/source/added/done_on/actual_h)
    before writing the same `--- Done:` line as before; shared by the
    Tasks window's Done button and #92's command shorthand.

92. ~~**Command shorthand for common actions (USABILITY).**~~ — DONE
    2026-07-29. `_try_command`/`_COMMAND_RE`, wired into `_go` (the
    task box's Enter/Ctrl+Enter handler): `done: thesis ch4` marks the
    matching task-library item done via the same `_mark_task_done`
    path as the Tasks window, no `exec()`/`eval()`. Status bar reports
    the match or "no item matches" — never silently does nothing.

93. ~~**Quick day-file navigator.**~~ — FIXED v8.69. File > "Open a
    day file…" is now `_quick_day_nav`: a two-pane Listbox+Text picker
    (same shape as v8.68's Help window) listing the last 30 day files,
    plus yesterday/a week ago/a month ago jump buttons, reading
    straight into the Text pane via the existing `diary_path` read
    path. "Open in Notepad…" stays one click away for editing. The old
    file-dialog behavior is still there as "Browse for a day file
    (file picker)…", one entry down.

94. **Scheduled break appointment (PLANNING — owner's own ask,
    2026-07-19, Finnish: "if it's 12:00 now, set a timer for a break at
    14:00, and until then focus is mandatory").** Distinct from the
    existing `[15m]` time-box (which boxes a TASK's duration, open-
    ended start) — this boxes a specific FUTURE break APPOINTMENT: "my
    next break is at 14:00" as a real clock time, not a duration from
    now. Natural extension of #50's protected time windows (a one-off
    scheduled break is a protected window that expires after firing
    once, not a daily-recurring one) — could reuse the same settings
    shape and `_free_slots` subtraction, plus a one-time notification
    at the target time via the existing floating-pill/status-bar
    surfaces. "Mandatory focus until then" should stay a STATED framing
    in the UI text, never an actual lock, per the standing anti-gating
    precedent (#9, #30's pull-back note) — the owner's own phrasing
    ("ns PAKKO" / "sort of mandatory") already hedges toward stated-not-
    enforced, worth preserving that instinct when this gets built.

95. **Within-session efficiency-decline detector (ANALYSIS — owner's
    own ask, 2026-07-19, explicitly speculative).** "Notices if your
    work slows down in the evening... and then you can see if you want
    to continue at home" — real-time trend detection WITHIN a single
    day/session (block lengths shrinking, more switches, longer breaks
    creeping in), distinct from every existing insight here which
    looks at PAST days, not the live trend of the one happening right
    now. Harder than most items in this backlog: needs a genuine
    live-trend model, not a threshold check, and "suggest a location
    change" is a real UX leap this app has never made (everything else
    states a line, never suggests an action outside the software
    itself). Flagged explicitly as needing real design thought before
    building, similar to #60 — log the idea, don't rush the shape.

96. ~~**Tiered SIGNAL priorities.**~~ — FIXED v9.0. Checked against
    the "Signal vs. maintenance" precedent before building, as this
    entry asked: a discrete `SIGNAL2:` tier survives the check because
    it's a strict ranking, not a blend — SIGNAL's own number is
    untouched (tier-1 stays exactly "today's one sharpest priority"),
    SIGNAL2 is a disjoint second bucket, never merged into tier-1's
    percentage. `_signal2_kws`/`_day_signal2`/`_carry_signal2` mirror
    the existing AVOID mechanism exactly; `_signal_tier_insight` adds
    the trailing-window read. Went with `SIGNAL2:` as its own header
    line (not `SIGNAL1:`/`SIGNAL2:` replacing `SIGNAL:`) — zero
    migration risk for every existing `SIGNAL:` line ever written.

97. ~~**BUG: auto-capture creates a new task for every growing snapshot
    of a still-being-typed bullet.**~~ — FIXED 2026-07-29. `_add_task`
    now also checks, within the SAME source, whether the new capture
    and an existing entry are a prefix of one another — if so, updates
    the existing entry to the longer/more-complete version instead of
    appending a new one, never merging across different sources/days.
    Also cleaned the owner's real settings.json with the identical
    logic (backed up first as `settings.json.bak-before-dedup-
    cleanup`): 77 → 34 task-library entries, 43 stale duplicates
    removed. Tested: growing-prefix collapse, distinct same-source
    bullets both kept, cross-source bullets never merged, exact-repeat
    dedup unaffected, and an out-of-order shorter snapshot arriving
    after a longer one doesn't regress it.

98. **Themed writing: toggle where it's stored (USABILITY — owner's
    own ask, 2026-07-29).** Themed writing (v6.4) always embeds its
    `=== THEME: x ===` block into TODAY's day file — no second data
    store, by design. The owner wants an option to instead store a
    theme separately (its own file/folder) rather than always landing
    in the daily log. Real design tension worth resolving before
    building, not papering over: the sacred rule is "everything visible
    lands in the day file, no hidden state" — a themed-writing session
    filed elsewhere would be exactly that hidden state, unless Browse
    Themes (which currently scans every day file for blocks) also
    learns to scan the separate location, and On-this-day/word-drift/
    ask-your-diary either follow it there too or explicitly don't (and
    say so). Probably the right shape: a per-theme-topic setting (some
    topics — reflection, brainstorming — stay in the daily log; others
    — a specific ongoing research thread, say — get their own file the
    daily log only LINKS to, not embeds) rather than one global on/off
    switch. Needs that design pass before implementation, not a quick
    toggle bolted on.

99. **Day-by-day audit, 2026-07-29 — findings from reading 19 real day
    files (2026-07-10 through 2026-07-28), software-relevant only.**
    Requested directly by the owner, done as a software-development
    review, not a life review — nothing personal below, only what's
    useful for TimerDiary's own development. Five findings:
    - **Recurring multi-hour "mega-break" gaps.** At least six times
      across these 19 days, a session was left open (not properly
      Reset) across a long gap — overnight, or many hours away — and
      on return the ENTIRE gap logs as one undifferentiated break
      (observed durations: 20h52m, 20h3m, 10h29m, 16h13m, 15h7m,
      15h11m). Not incorrect — that time genuinely wasn't worked — but
      worth checking whether v8.55's new screen-lock detection
      (shipped this session, not yet confirmed working on the owner's
      real machine) already substantially fixes the OVERNIGHT case
      going forward, since a laptop left locked overnight is exactly
      what `is_locked()` should catch. If gaps this long still slip
      through after confirming v8.55 works, that's a real follow-up:
      maybe a break past some large threshold (4h+?) deserves a
      different offer than the standard retro-split dialog.
    - ~~**Possible bug: switching task DURING a break may have made the
      new task inherit the break's elapsed time**~~ — CHECKED
      2026-07-29, NOT REPRODUCIBLE. Self-reported once early in
      development (2026-07-11); direct test against current code
      (start work, backdate, Stop, change task box, Start, inspect
      `work_start` and the resulting csv rows) shows `work_start`
      resets cleanly to the moment of Start regardless of a task-box
      change during the break, and the break itself still correctly
      attributes to the task it interrupted. Long since fixed by later
      state-machine work; closing this one out.
    - **Interleaved-task friction, observed directly (2026-07-27):**
      "checking [X] but from time to time [Y]... shuld even log as
      work, then switch, but takes time" — when two tasks interleave
      at a finer grain than feels worth a formal Switch, the owner
      just logs everything under one task rather than pay the
      switching overhead. Not necessarily fixable (may be an inherent
      tracking-granularity tradeoff, not a bug) but worth keeping in
      mind if any future feature touches task-switching friction.
    - ~~**Deadline-projection volatility in the first days of a new
      deadline**~~ — FIXED 2026-07-29. `_projection_line` and
      `_review_bottom_line`'s "Main risk" line both now say "far
      behind — see the date" / "is not on track to finish" past a
      90-day threshold instead of a triple-digit day count; the +1h/day
      sensitivity lever is also suppressed past that threshold (a
      "3383d sooner" lever is noise, not a lever). The underlying
      projection math is unchanged — only the two places that turn an
      extreme number into a sentence.
    - **Task-name drift, self-caught by the owner (2026-07-28):** two
      task names that were meant to represent related-but-different
      activities under the same goal had been used inconsistently for
      weeks before being noticed (both matched the same goal's
      keywords, so goal-level tracking was fine, but the DISTINCTION
      between the two activities was invisible until manually
      reviewed). Not a bug — the substring-matching architecture
      worked exactly as designed — but a real instance of the kind of
      drift #96's tiered-signal idea and Data doctor's existing
      variant-detection both partially address; no new action needed
      beyond noting it as a live example of why those matter.

100. **Declared work-block container (PLANNING — owner's own ask,
    2026-07-29, follows directly from #99's interleaved-task finding,
    explicitly "idk how to solve").** Two distinct problems tangled
    together — kept separate on purpose:
    - ~~**"Counting work days as breaks sometimes."**~~ — FIXED v9.0.
      `WORKBLOCK: 09:00-17:00` (same convention shape as TODAY:/AVOID:,
      carries forward the same way) declares an externally-committed
      window; inside it, `_watch_idle`/`_watch_lock` multiply the
      idle/lock threshold by `_WORKBLOCK_IDLE_FACTOR` (3x) before
      offering to log a break — the exact inversion this entry
      proposed. The opposite of #50's protected windows (those say
      "never book here"; this says "stop being strict about internal
      pauses here").
    - **Genuinely parallel/overlapping work** (day job AND thesis "at
      the same time," attention split, not sequential) — DELIBERATELY
      NOT built. Still likely unsolvable honestly within a single-
      threaded timer: the app can log ONE active task per moment by
      construction (the sacred day-file format is a sequence, not
      parallel tracks). Don't invent a fake "50/50 split" — if this
      ever needs solving, the honest version is probably just: log
      whichever task is PRIMARY at that moment, same as today, and
      accept that genuinely simultaneous attention doesn't fit this
      tool's model. Left open, same status as #60/#95.

101. **BUG, found 2026-07-29 while cleaning up #97's duplicates: Finnish
    (ä/ö) characters get mangled to replacement chars (`�`) in some
    captured diary text.** Confirmed the corruption is already present
    in the SOURCE day-file .txt itself (`2026-07-19.txt`), not
    introduced later — ruled out `save_settings`/`load_settings` (both
    correctly use `encoding="utf-8"`/`"utf-8-sig"`) and `_save_diary`
    (also plain `encoding="utf-8"`, writes `self.diary.get(...)`
    directly). No custom clipboard-paste handler exists in this file —
    every `clipboard_*` call is outbound (Copy for AI review etc.),
    nothing intercepts an inbound paste. That leaves Tk/Tcl's own
    default Windows clipboard handling as the likely site: a known
    class of issue where pasted non-ASCII text picks up the wrong
    Windows clipboard format (ANSI `CF_TEXT` instead of Unicode
    `CF_UNICODETEXT`) before Tk ever hands it to Python as a string —
    meaning by the time `self.diary.get()` reads it, the characters are
    already lost, not mis-encoded on the way out. Next step, not done
    this session: reproduce live (paste real Finnish text containing
    ä/ö from another app into the diary pane) and inspect what
    `self.diary.get()` returns immediately after the paste, before any
    save — if it's already `�` at that point, the fix is Tk-clipboard-
    specific (may need an explicit `-format` on the paste binding or a
    workaround via `windll.user32.GetClipboardData` with
    `CF_UNICODETEXT` explicitly) rather than anything in this file's
    own save/load code, which checks out clean.

102. **Manual task-name merge (TRUST/HYGIENE — a real gap Data
    doctor's existing spelling-variant merge doesn't cover, new idea
    2026-07-29).** Data doctor (v8.?) already auto-detects and merges
    CASE/whitespace variants of the same string ("Thesis" vs
    "thesis") — but it groups by `" ".join(t.lower().split())`, so it
    structurally cannot catch two genuinely different-looking labels
    the owner privately means as the same activity. #99's day-by-day
    audit caught exactly this live: "HGW" was used for weeks before
    being corrected to "Hegemon" — both matched the same goal's
    keywords so goal-level totals stayed fine, but the per-task
    breakdown (recent-tasks dropdown, Tasks window, "Copy for AI
    review" per-task hours, `_task_actual_h`) silently split one
    activity's history into two entries the whole time, and nothing
    else in the app could have caught it since the strings share no
    substring. Fix: a small manual pairing tool (in Data doctor, or
    its own Tools entry) — pick two distinct task names from history,
    choose the canonical spelling, rewrite past csv rows the same way
    Data doctor's existing Clean action already does (same rewrite
    primitive, one more mapping source: user-declared instead of
    auto-detected). Deliberately NOT auto-detected — unrelated strings
    can't be inferred safely, so this stays a manual action that can
    never silently merge two things that were actually different.

103. **Deadline phase-out: extend or spin off? (PLANNING — the owner's
    own live question, 2026-07-28: "figure out how shuld this now
    function that gonna extend the thesis DL... shuld i jsut add new
    DL for the rest of this thesis stuff, or edit the existing one,
    culd be easy fix," new idea 2026-07-29).** Nothing currently
    guides the exact moment a deadline's declared work is "done" (due
    date passed, or scope fully logged) but the SAME goal's keyword-
    matched work keeps happening afterward — right now the owner has
    to guess whether to edit the old deadline's date (keeping its
    renegotiation/ledger history continuous) or create a fresh one
    (clean scope, but the lifetime ledger, milestone progress and
    post-mortem math all start over from zero). Fix: when the deadline
    editor is opened on a deadline that's past-due or fully logged,
    and its goal still has recent matched hours, show a one-line
    prompt naming the choice and its consequence explicitly — "this
    deadline has N weeks of ledger history; extending the date keeps
    it, a new deadline starts fresh" — then act on whichever the owner
    picks with one click. Pure composition: reuses `_dl_progress`,
    `_lifetime_ledger_line`, `_deadline_revisions_after_save` as-is;
    the only new part is naming the choice at the right moment instead
    of leaving it implicit and manual.

104. **Task-library staleness flag (HYGIENE — the task library's own
    honesty gate, mirroring what #56's usage meter does for insights;
    new idea 2026-07-29).** A task-library item can sit for months
    with zero real hours logged against it and never get marked done
    or blocked — nothing currently distinguishes "queued behind real
    priorities, on purpose" from "quietly forgotten," and the list
    just grows (the #97 cleanup this session already found 43 stale
    duplicate entries hiding in it). Fix: reuse `_task_actual_h`
    (already computed for the Tasks window's display column) — an
    item older than a real threshold (e.g. 6+ weeks, so it never fires
    on work that's merely queued behind this week's priorities) with
    0h logged gets a quiet "⏳ 6wk, 0h" marker in the Tasks window,
    plus — only when at least one exists — a single MOMENTUM & TRENDS
    line in #86's new grouped insights: "N task(s) aging 6+ weeks with
    0h logged — still relevant, or done in spirit?" A flag, never a
    nag: no notification, no forced review, no auto-archival — same
    anti-nagging precedent as #9's rejected Reopening Guard.

105. ~~**Tier-2 color in the day timeline.**~~ — FIXED v9.1. `TL_SIGNAL2`
    (a lighter/desaturated green) added to `work_color(task)`, checked
    after tier-1 and before goal-aligned — same priority order the
    text metrics already use.

106. ~~**Header-line adoption panel.**~~ — FIXED v9.1. Data doctor now
    reports usage of all ~12 optional header-line conventions from one
    table. `_line_ever_used` refactored into a thin wrapper over the
    new `_line_usage_count(prefix, days)`, so the bool-check that
    gates morning-header visibility and the count report can never
    drift apart — one scan, two views.

107. **WORKBLOCK-aware scheduler (PLANNING — a gap v9.0's own WORKBLOCK
    left, new idea 2026-07-29).** v9.0 wired `WORKBLOCK:` into idle/
    lock detection only — `_free_slots` (the scheduler's own busy-time
    model, already merges calendar busy time + `_protected_intervals`)
    still doesn't know a declared work block exists, so the morning's
    suggested schedule and `_next_free_block_line` can still recommend
    deep thesis work at 10:00 during a declared 09:00-17:00 day job.
    The same "two models silently disagreeing" shape #82 just fixed
    for protected windows, one level up: `_free_slots` should also
    subtract `_workblock_window()` the same way it already subtracts
    `_protected_intervals()` — one more busy-time source merged into
    the same primitive. Open question worth resolving before building,
    not just formatting: should `_day_capacity`'s aggregate-hours model
    (deadline math) ALSO shrink inside a work block, same as #82 did
    for protected windows, or does day-job time deliberately stay
    outside the deadline-capacity pool since it's a different kind of
    commitment? Needs a real answer, not a guess — check with the
    owner rather than assuming either way.

108. **Task-library manual ranking (USABILITY — owner's own direct
    ask, 2026-07-29: "just simply can drag or number tasks to top etc
    etc and prio stuff.. idk if this already exists").** Answer: only
    partially. Tasks have a 3-tier `priority` field (normal/signal/
    someday, cycled by clicking the "!" column) but nothing orders
    WITHIN a tier, and the Treeview doesn't even sort by tier — it's
    plain insertion order regardless of priority, so a "signal"-tier
    item added last still shows at the bottom under older "normal"
    items. Fix, two parts: (a) sort the display by tier first (signal
    > normal > someday), insertion order within each tier — a pure
    rendering change, no new data; (b) a real manual rank: either drag-
    to-reorder in the Treeview (tk supports this via button-motion
    events, not trivial but doable) or simpler, an Up/Down button pair
    that swaps a task's position in `settings["tasks"]` — the list's
    own order already IS the rank, once (a) stops hiding it. Start
    with (a) + (b)'s simpler button version; drag-and-drop is a nice-
    to-have layered on top, not required for the core ask.

109. ~~**Deadline-urgency-seeded SIGNAL fallback.**~~ — FIXED v9.2.
    `_carry_signal` now seeds from the single most-urgent `_focus_items`
    entry's own match keywords when nothing carried forward and at
    least one deadline is scoped; falls back to the old all-goals
    blend only when no deadline is scoped at all.

110. **Unmatched-task-name goal/domain suggestion (TRUST — turns "plain
    work" bucket bloat into an actionable fix, new idea 2026-07-29).**
    The three/four-bucket model (signal / goal-aligned / plain work /
    noise) is correct and settled, but nothing currently helps shrink
    the "plain work" bucket when it's large for a boring reason — a
    real, meaningful task's name just never got added to any goal's or
    domain's keyword list, not because it genuinely doesn't belong
    anywhere. Fix: a Data-doctor-style scan — the top task NAMES by
    hours (last 60 days) that match neither a goal nor a domain's
    keywords — surfaced as "'life admin' — 8.2h, unattributed to any
    goal or domain. Add a keyword?" with a one-click add to an existing
    goal/domain's `match` list. Pure read of already-computed data
    (`day_index`, `goals()`, `domains()`, `_match_kws`); no new
    tracking, no auto-guessing which goal a name belongs to — the
    owner picks, same as every other lens-linking action in the app.

111. **Deadline retirement should archive, not delete (TRUST, new idea
    2026-07-29 — surfaced by actually doing this by hand today).**
    Retiring a finished deadline (per #103's "extend or spin off"
    resolution) currently means removing it outright from
    `settings["deadlines"]` — its renegotiation `history`, its
    `postmortem_written` flag, everything about it as a STRUCTURED
    record is gone the moment the entry is deleted. The day file still
    has the text (permanent, per the sacred rule), but nothing
    structured remembers "this deadline existed and was closed out" —
    future features that want a real shape (year in review #15,
    coverage map #87, "how many deadlines did I actually finish this
    year") have nothing to read. Fix: mirror `tasks_done` — a
    `settings["deadlines_done"]` list, append the full dict (plus a
    `retired_on` date and maybe `outcome`: finished/superseded) instead
    of dropping it, same shape as #91's task archival.

112. **Settings changes should leave a visible day-file trace (TRUST —
    the sacred rule applied to itself, new idea 2026-07-29).** "Every
    feature must leave a visible trace in the day file" (CLAUDE.md's
    own standing rule) currently only covers TRACKED features — goal/
    deadline/capacity edits go straight into settings.json with no
    day-file trace at all, unlike a Done task (`--- Done: X`) or a
    renegotiated deadline (already logged via #51's tracker). Fix: on
    save, goals/deadlines/capacity editors append one short line to
    today's diary — `--- Settings changed: goal 'X' target now 5h/wk`
    or `--- Settings changed: deadline 'Y' retired, 'Z' added` — same
    visible-trace treatment everything else already gets, so a glance
    at any day file shows not just what you DID but what you
    RECONFIGURED. Small, mechanical, one line per editor's save().

113. ~~**Concrete buffer-window recommendation for high-stakes
    deadlines.**~~ — FIXED v9.3, as "lock study windows" + .ics
    export. Went with the simplest honest ranking (biggest single
    contiguous free block per day, `_free_slots`) rather than the
    peak-hour-weighted version originally sketched here — direct
    owner feedback mid-build: the picker logic isn't the hard part,
    don't over-engineer it. Export-to-.ics (not protected-windows or
    WORKBLOCK) turned out to be the right mechanism since the owner
    wants these in their REAL calendar (Outlook/Google), not just
    inside this app.

114. ~~**Subscribe to a calendar link (.ics URL), no manual export.**~~
    — FIXED v9.4. See the v9.4 version-history entry above for the
    full design (`resolve_ics_source`, cache/refresh, validation).

115. **Microsoft Graph API calendar sign-in (PLANNING — the documented
    fallback to #114, not built, only needed if the simple path
    fails).** #114's publish/subscribe link is the low-effort first
    try; if the owner's school/work Microsoft 365 tenant blocks
    calendar publishing (common in EDU tenants — an admin-level
    setting a student can't override), the fallback is a real sign-in:
    device-code OAuth flow (no client secret needed for a public-
    client app, no redirect URI/local web server either — the user
    visits a Microsoft URL and enters a code, good fit for a desktop
    app), then calls to Microsoft Graph's `/me/calendarview` endpoint
    via `urllib.request` (stdlib-only, no new dependency) for the
    same busy-time data #114 gets from a static link. Real new
    surface for this app: stored tokens (refresh token needs to live
    somewhere — settings.json, or its own file), token refresh logic,
    network calls that can fail in new ways. Also: EDU tenants often
    require ADMIN CONSENT for even basic Calendars.Read delegated
    permissions, which a student can't grant themselves — worth
    confirming that isn't ALSO blocked before investing in this,
    since if it is, neither path works and the honest answer is "your
    IT department has to enable one of these," not more engineering.
    Don't build speculatively — check #114 actually fails first.
    Superseded in practice by #116 (built instead, before confirming
    #114 fails) since it needed no admin-consent gamble at all — this
    stays logged as the harder fallback if #116 ALSO turns out to be
    blocked somehow.

116. ~~**Power Automate CSV — a second, independent calendar-import
    path.**~~ — FIXED v9.5. See the v9.5 version-history entry above
    for the full design (`parse_csv_busy_export`, extension-based
    dispatch, why Power Automate over a custom Graph API app).

117. **RRULE (true recurring events) silently skipped by
    `parse_ics_intervals` (TRUST, found 2026-08-07 verifying #114
    against the owner's real published calendar).** Documented as a
    known limitation since the original .ics import (v8), but never
    actually checked against real data until now: fetched the
    owner's real Aalto Outlook publish link (103 events, live HTTP
    request, not a mock) and confirmed 0 of them were RRULE-based —
    Outlook's own "Publish calendar" export happens to expand
    recurring series into individual one-off VEVENT entries, so this
    limitation didn't bite in practice for this specific export
    method. Stays real risk for any OTHER calendar source that keeps
    events in true recurring form (a raw Exchange/CalDAV sync,
    potentially a different tool than what's configured now) — those
    would silently under-count busy time with no error, no warning.
    Not fixed — low priority since it's currently a non-issue for the
    live source, but the exact trigger condition to watch for if
    capacity numbers ever look implausibly free during a semester
    with recurring lectures/meetings.

118. ~~**Free-time forecast — a simple visual calendar view (owner's
    own ask, 2026-08-07: "calendar view... very simple... easier to
    visually inspect free slots").**~~ — FIXED v9.6. View > Planning >
    "Free-time forecast (calendar)…": one green/grey horizontal bar
    per day for the next 3 weeks, green = free (calendar busy time +
    protected windows already netted out via `_free_slots`, the same
    primitive #113's lock-window picker and the scheduler both use).
    Deliberately glance-only, no actions — #113 already owns "pick
    and lock windows for a deadline" as its own flow, this is just
    the wide-angle view underneath it.

119. **Automated schedule building (PLANNING — owner's own new idea,
    2026-08-07, explicitly flagged as a backlog idea not a build-now
    ask).** The natural next step past #118's glance-only view and
    #113's per-deadline lock-window picker: given ALL scoped
    deadlines/goals at once (not one at a time) and the real free-time
    forecast, auto-DRAFT a placement — which task/deadline work goes
    in which open block, across the next N days, not just today
    (`_day_schedule_lines`/`_energy_place` already do this for TODAY
    only, tier c of the planning engine). Real design questions before
    building, not just scaling up today's version: (a) multi-day
    placement needs to balance competing deadlines against each other
    over the WHOLE window, not greedily fill today first and hope
    tomorrow works out — a genuinely different algorithm shape than
    the existing single-day greedy pass; (b) should a draft schedule
    write anywhere (task-library due-soon flags, a diary block, an
    .ics export via #113's own export machinery) or stay read-only
    like every other planning view — the standing no-accept/reject-UI,
    no-compliance-tracking guardrail (see #59/#60 precedent) argues
    for read-only, a proposal to glance at and ignore or follow, not a
    committed plan; (c) how does it handle a day that's ALREADY
    partially spoken for (WORKBLOCK, protected windows, real calendar
    busy time from #114/#116) — probably fine already, since
    `_free_slots` already nets all of that out, worth confirming
    rather than assuming. Flagged, not scoped — a real next-round
    project once the design questions have real answers.

120. ~~**Real week/month calendar view, named events.**~~ — FIXED
    v9.7. See the v9.7 version-history entry above for the full
    design (`parse_ics_events`/`parse_csv_events`, week/month
    drawing, why it stays read-only). Directly narrows #119's open
    question (c) — confirmed while building this that `_free_slots`
    already nets out WORKBLOCK/protected windows/real calendar busy
    time correctly, since the calendar view's own "free" reads agree
    with what #113/#118 already showed.

121. ~~**Recurring commitments — weekday-aware, midnight-crossing
    protected windows (day job, sleep, admin).**~~ — FIXED v9.8. See
    the v9.8 version-history entry above for the full design
    (`_parse_weekdays`, the 14h overnight-vs-typo sanity cap, why it
    extends #50 rather than a new parallel mechanism).

122. ~~**Interactive scheduling on the calendar view — right-click
    to lock a slot (mode (b), "working windows").**~~ — FIXED v9.9.
    Mode (a) (attach a task to a "done by" date) — FIXED v9.10, see
    #123. Both halves of the original ask are now done.

123. ~~**Task due-dates via the calendar (mode (a) from #122's
    original ask).**~~ — FIXED v9.10. See the v9.10 version-history
    entry above for the full design (lightweight field vs a full
    Deadline object, week/month granularity split, `_month_click_to_day`).

124. ~~**Due-date feasibility warning.**~~ — FIXED v9.11, for TASK due
    dates (#123's two entry points: the calendar's month-view right-
    click, and the Tasks window). See the v9.11 version-history entry
    above for the design (`_due_date_feasibility_line`, non-blocking).
    DEADLINE date-setting (the deadline editor's own save()) is NOT
    covered by this fix — a genuinely separate, more invasive surface
    (a multi-row grid save, not a single date field) left for a
    follow-up if it turns out to matter in practice.

125. ~~**Recurring-commitment drift check.**~~ — FIXED v9.12. See the
    v9.12 version-history entry above for the full design
    (`_commitment_drift_lines`, Sleep vs #126's suggestion, everything
    else vs first tracked work activity).

126. ~~**Auto-suggest a sleep commitment from real tracked data.**~~ —
    FIXED v9.12. See the v9.12 version-history entry above
    (`_suggested_sleep_block`, median not mean, pre-filled not saved).

127. **Task due-dates feed SIGNAL's urgency-seeded fallback (PLANNING
    — directly extends #109 with #123's new lightweight due-date
    concept; new idea 2026-08-07).** #109 seeds SIGNAL from the
    single most-urgent scoped DEADLINE when nothing carried forward.
    Task due-dates (#123) are a second, lighter-weight urgency signal
    that didn't exist when #109 was built — a task due tomorrow with
    no full Deadline behind it currently has no influence on SIGNAL's
    auto-fill at all. Fix: when ranking "what's most urgent" for the
    fallback seed, also consider tasks with a `due` date within a
    real near-term window (e.g. 7 days), competing on the same
    urgency footing as scoped deadlines — a task due tomorrow should
    plausibly outrank a deadline three weeks out. Needs a real design
    decision on how to compare a bare due-date (no scope, no hours
    estimate) against a fully-scoped deadline's `_focus_items` ranking
    on the same footing — flagged, not scoped, since a wrong ranking
    heuristic here would quietly make SIGNAL worse, not better.

## How to verify changes without Windows

**Run `python3 timerv2/selftest.py`** — the committed, stdlib-only
harness (v8.x): lifts pure functions out of the app via ast (no tkinter/
ctypes import, never touches the real data dir) and runs 22 suites
covering projection, trajectory, outlook, alignment, review synthesis,
anomaly watch, recommend-now, energy placement, last-context, break-pull,
reentry, procrastination, metrics, the widened health parser, daylight,
word drift, the diary ranker, lag correlations, the week-ahead brief, the
break budget, lens overlap and the health-hub extras table. Exit 0 =
green. Add a suite there in the same commit as any new pure-logic
feature. NOTE: v8.13–v8.26 (the AVOID/root-cause/decay-curve/short-day/
first-hour/thrash/shallow-work/graveyard/mood/usage-meter/best-weeks/
reallocation batch) were verified by hand per their own commit messages
and never got selftest suites added — a real gap, not a judgment call;
worth backfilling opportunistically when touching adjacent code, not as
its own dedicated session.

The older ad-hoc pattern (extract via ast in a scratch file, seed a messy
csv — v4 rows, case variants, dups, junk, overlaps — and test
`read_rows`/`day_index`/`_doctor_scan`/`_insight_lines`/`_sleep_h`/
`_energy_from_text` with stubbed `self`) still applies for anything
selftest doesn't cover yet. Always `python3 -m py_compile` the app file.
The tkinter surfaces need a real run on the user's Windows machine
(Ctrl+D dashboard, Data doctor scan).

## Git

Private repo `econjp/chrono`. The owner's main machine works directly on
`master`. Mobile/GitHub Claude Code sessions work on
`claude/life-management-platform-arch-6s4hrv` (per the harness's own
designated-branch instructions) and never merge it themselves — the
owner reviews, audits and merges by hand. That branch has been merged
and deleted-then-recreated-from-master-tip more than once already as
work lands and gets cleaned up (most recently 2026-07-14, before v8.27);
if it's ever merged and gone again, the correct move for the next
session is exactly that: recreate it fresh from `origin/master`, don't
assume it still holds anything live. (A second mobile branch,
`claude/finish-date-projection`, held the v8.1–v8.12 commits that landed
2026-07-13 — kept on origin at the owner's choice even though its
content is now redundant on master too; leave it alone unless asked.)
Commit style: short imperative title + honest body listing user-visible
changes first. No AI co-author trailers, ever (CLAUDE.md).
