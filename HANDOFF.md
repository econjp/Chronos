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

## Version history (one line each)

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

14. **"Ask your diary" — smart multi-day search, still copy-paste not
    API.** Search-all-days (existing) is a literal substring match.
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

18. **Commitment-reliability ledger (SELF-KNOWLEDGE).** A `COMMIT: thesis
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

20. **Weekly experiment engine (FEEDBACK → ACTION → MEASUREMENT).** The
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

21. **Meeting fragmentation tax (ANALYSIS).** Meetings cost more than
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

22. **Lag correlations — "what today does to tomorrow" (ANALYSIS).**
    Every current insight correlates same-day pairs. The new dimension is
    TIME-LAGGED: workout day → next-day output/energy; short sleep →
    NEXT-day output (sleep debt lands late); late-evening work (tracked
    past 21:00) → next-morning first-session start time. Same honesty
    gates (n≥5 pairs per bucket), same day-record data, one new loop
    shape: iterate (day, day+1) pairs instead of days. Output like "the
    morning after a workout day you start 40min earlier and do +0.9h
    (n=14) — the gym is a productivity tool, not a cost." Probably the
    highest insight-per-line-of-code item left.

23. **Sensor health meter (TRUST / USABILITY).** Every insight silently
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

24. **Running-hot index / recovery-debt early warning (FEEDBACK).** The
    trajectory line spots a sleep-for-work trade AFTER four weeks; this
    is the early-warning version: a rolling debt score from days of
    sleep-below-your-norm, workout-frequency drop vs baseline, tracked
    minutes past 21:00, and break-ratio compression — surfaced as one
    co-pilot-eligible line only when several move together: "9 days
    running hot (sleep −0.8h/night vs norm, workouts halved, 3 late
    nights) — schedule one flat day before your body schedules it."
    All from existing day-record keys; n-gated; anti-nagging guardrail
    applies (stated once, never repeated daily unless the score worsens).

25. **Planner realism factor — the schedule audits itself (PLANNING).**
    v8.0/v8.8 write a suggested schedule every morning; nothing ever
    checks what became of it. Reconcile each past day's written schedule
    block (parse it back out of the day file — same in-file convention
    trick as `_estimate_factor`) against the csv's actual placed hours,
    and learn a personal plan-survival rate: "your average planned day
    survives 62% — the planner now plans at 62% density instead of
    pretending." Self-calibrating planning WITHOUT compliance tracking of
    the user (the guardrail): it grades the PLANNER's realism, not the
    person, and only changes how much the planner dares to schedule.

26. **Year rhythm map (VISUAL MEMORY).** The heatmap shows how MUCH per
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

28. **Deadline post-mortem (FEEDBACK/MEMORY).** When a scoped deadline's
    date passes (or its task is Done), write one retro block into that
    day's file: scope vs actual hours, the estimate factor on THIS
    project, what the v8.1 projection predicted vs what happened
    ("projection ran 4d pessimistic"), pace curve in one line. Each
    deadline closed becomes calibration data — and the projection engine
    can later quote its own track record ("my forecasts have run ±3d on
    your last 4 deadlines"), which is the honest version of trust.

29. **Energy forecast for today (ANALYSIS/PLANNING).** Morning header
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

33. **Break budget (FEEDBACK — reframe, not police).** Instead of judging
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

35. **Weekly "one less" — subtraction advisor (FEEDBACK).** Every insight
    adds awareness; this one subtracts a thing. Each Monday review picks
    ONE concrete removal candidate from the data: the recurring meeting
    that splits your best block (#21's math), the 11:00 email check that
    fragments mornings, the after-22:00 work that taxes tomorrow. "This
    week, try one less: X." Rotates candidates, never repeats an ignored
    one twice in a row. Improvement by removal — the most underrated
    productivity move and almost never what software suggests.

36. **Milestones inside a deadline (PLANNING — content, not just hours).**
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

41. **Rescue block — the day is not lost (FEEDBACK/PLANNING).** When a
    day is clearly going sideways by mid-afternoon (tracked << plan and
    the deadline needs it), one stated salvage line via the co-pilot
    surface: "salvage plan: one 45m block on Thesis before dinner makes
    today count — 0.7h is 100% more than 0h." Attacks the all-or-nothing
    write-off spiral. Reuses _recommend_now's inputs; strictly a stated
    line (anti-nagging precedent), at most once per day.

42. **Monday week-ahead risk brief (FORESIGHT).** The Monday review looks
    back; nothing yet looks at the WEEK ahead as a whole. One block:
    calendar density per day (free-slot totals), the outlook's late
    deadlines mapped onto those days, sleep-debt carry-in — "this week's
    biggest risk: Thu is 80% meetings while TUTA needs 2h/day; front-load
    to Tue/Wed." Composes _free_slots + _outlook_lines + _sleep_h over
    the next 7 days; the weekly twin of the daily co-pilot line.

43. ~~**Library graveyard sweep (USABILITY/HYGIENE).**~~ — DONE v8.20
    (`_graveyard_lines`). "Untouched" approximated by ADDED date, not a
    true last-touched signal — see the version-history note.

44. **Waiting-on / blocked tasks (PLANNING — external dependencies).**
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

45. **Goal lifetime ledger (SELF-KNOWLEDGE — the un-windowed view).**
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

46. **Deadline renegotiation tracker (SELF-KNOWLEDGE — scope-creep
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

48. **Lens overlap check (TRUST/HYGIENE — the honesty layer auditing
    itself).** Nothing currently checks whether two goals/domains/
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

50. **Protected time windows (PLANNING — the scheduler's missing
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

52. **Cost of yes — a prospective preview before committing to a new
    deadline (PLANNING — the capacity math run BEFORE, not after).**
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

53. **Focus signature — hour-of-day × day-of-week, not either alone
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

## How to verify changes without Windows

**Run `python3 timerv2/selftest.py`** — the committed, stdlib-only
harness (v8.x): lifts pure functions out of the app via ast (no tkinter/
ctypes import, never touches the real data dir) and runs 12 suites
covering projection, trajectory, outlook, alignment, review synthesis,
anomaly watch, recommend-now, energy placement, last-context, break-pull,
reentry and procrastination. Exit 0 = green. Add a suite there in the
same commit as any new pure-logic feature.

The older ad-hoc pattern (extract via ast in a scratch file, seed a messy
csv — v4 rows, case variants, dups, junk, overlaps — and test
`read_rows`/`day_index`/`_doctor_scan`/`_insight_lines`/`_sleep_h`/
`_energy_from_text` with stubbed `self`) still applies for anything
selftest doesn't cover yet. Always `python3 -m py_compile` the app file.
The tkinter surfaces need a real run on the user's Windows machine
(Ctrl+D dashboard, Data doctor scan).

## Git

Private repo `econjp/chrono`, all work happens directly on `master` —
no other branch is active. (A mobile-session branch,
`claude/life-management-platform-arch-*`, was cherry-picked into master
and re-authored on 2026-07-12 — see CLAUDE.md incident log — and its
now-redundant remote pointer was deleted on 2026-07-13 during the
v8.1–v8.12 landing audit below. A second mobile branch,
`claude/finish-date-projection`, held the fourteen v8.1–v8.12 commits
that landed the same day — kept on origin at the owner's choice even
though its content is now redundant on master too.) Commit style:
short imperative title + honest body listing user-visible changes
first. No AI co-author trailers, ever (CLAUDE.md).
