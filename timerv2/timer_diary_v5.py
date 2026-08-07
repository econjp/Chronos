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

New in v9.16 (#132 — a one-off exception for a recurring commitment,
2026-08-07):
  - Tools > "Recurring commitments…" gets a 5th column: "Skip dates."
    A comma-separated list of YYYY-MM-DD dates the commitment sits
    out entirely — a single holiday or sick day off the Day job
    without editing the whole commitment away and back. Everything
    else declared for that day (Sleep, Lunch, ...) still applies
    normally.
  - checked in `_protected_intervals_named` right alongside the
    existing weekday filter — same one-more-condition shape, no new
    concept, so #82/#118/#113/#130/#133's shared capacity primitives
    all inherit the fix for free.
  - malformed skip dates are rejected with an error naming the bad
    entry, same as the existing HH:MM validation right next to it —
    never silently dropped.

New in v9.15 (#135 — lock windows for tasks, not just deadlines,
2026-08-07):
  - both lock-window entry points (File > "Lock study windows…" and
    right-click an hour in the calendar's week view) now list task-
    library items alongside deadlines, not deadlines only. Closes the
    loop with #123's task due-dates — set a due date on a task, then
    lock real time for it, using the exact same picker.
  - a task with a real `due` date searches up to that date, same as a
    deadline; an undated task gets a plain 7-day window from today so
    it's never unreachable — labeled "(task, next 7 days)" in the
    picker so it's clear the window is synthetic, not a real deadline.
  - `someday`-priority and blocked tasks are left out of both pickers
    — not yet actionable, so not worth cluttering a locking list over.
  - `_lock_window_candidates` and `lock_windows_to_ics` are completely
    unchanged — both already only needed a plain name + date, so a
    task-shaped dict slots in without touching tested plumbing.

New in v9.14 (#133 — the week-ahead line names its own commitment
cost, 2026-08-07):
  - the Monday "WEEK AHEAD" block (when it fires at all — overbooked,
    a tight day, or a deadline behind pace) already netted recurring
    commitments out of its total-free-hours figure via `_day_capacity`,
    but silently — you'd see "14.0h free" with no way to tell that
    number was already down from a bigger raw figure. Now, whenever
    the week has >=30min of real recurring commitments, a second line
    names the top 3 by hours: "(of which 97.0h already committed:
    Sleep 59.5h, Day job 37.5h)." Same "show the why" instinct as
    #130's daily line, same underlying primitive (`_protected_hours`/
    `_protected_intervals_named`), no new capacity math. Stays silent
    on calm weeks and on weeks with no declared commitments, matching
    the function's existing quiet-by-default design.

New in v9.13 (#130 + #131 — commitments finally visible where the
sacred rule says they belong, plus a free/busy glance in month view,
2026-08-07):
  - #130: the morning header gets a new line, only when something's
    actually declared — "commitments today: Day job 7.5h, Sleep 9.5h
    (17.0h of 24h already spoken for)." #121's recurring commitments
    used to be visible ONLY in the Tools editor and the week calendar
    — never in the day file itself, which is exactly what CLAUDE.md's
    own standing rule ("every feature must leave a visible trace in
    the day file") says shouldn't happen. Reuses `_protected_
    intervals_named(self.today)` as-is, no new computation.
  - #131: the calendar's month view (View > Planning > Calendar) now
    shades each day cell white-to-light-green by that day's real
    `_day_capacity` — the same number #118's free-time forecast and
    #113's lock-window candidates already use. One glance now answers
    both "what's on" and "how open is it," instead of needing #118's
    separate window for the second question. `_cal_shade_color` is a
    plain linear blend, no new color infrastructure.

New in v9.12 (#125 + #126 — commitments learn from real data, owner's
own "just wanna automate and make it so much easier" ask, 2026-08-07):
  - #126: Tools > "Recurring commitments…" now suggests a Sleep row
    from real tracked data (median bedtime/wake across n>=10 real
    nights — wake proxied by each day's own first logged activity,
    sleep hours from `_sleep_h`) when there's no Sleep entry yet.
    Pre-filled, not saved — shown with "↑ suggested from N real
    tracked nights," fully editable/clearable before you hit Save.
    Resolves the "auto-set" instinct #121 deliberately left blank
    rather than guess at a bedtime that was never stated.
  - #125: a new grouped insight (TIME & FOCUS) — `_commitment_drift_
    lines` compares each declared recurring commitment against what
    your tracked data actually shows. Sleep is checked against #126's
    own suggestion (so the two features can't quietly disagree with
    each other); every other commitment (day job, admin) is checked
    against the day's own first tracked work activity, on the days
    it's declared to apply. Only speaks up at a real >=30min median
    gap over n>=10 matching days — "'Day job' declared 09:30 but
    your last 15 matching days actually start ~10:15 (45min later) —
    worth updating?" Same honesty-gate shape as every insight here,
    same "declared vs actual" pattern #47/#99 already established.

New in v9.11 (toolbar calendar button + #124 due-date feasibility
check, owner's own ask, 2026-08-07: "this scheduling or cal shuld
have its own button in task bar"):
  - 📅 button in the main toolbar (next to Reset/Switch/Start), always
    visible regardless of compact mode — opens the Calendar view
    without going through View > Planning. Shares the same usage
    counter as the View-menu entry (one "Calendar view" count, not
    two competing ones).
  - #124: setting a task's due date (via the calendar or the Tasks
    window) now runs an honest, non-blocking feasibility check —
    `_due_date_feasibility_line` reuses `_avail_hours` (already aware
    of recurring commitments, imported calendar events, and locked
    windows — no new capacity math) and, only when the numbers
    actually look thin (negative slack against a real `est_h`, or
    near-zero total free time with no estimate to compare against),
    adds a line to the status bar and the diary trace: "⚠ only 2.1h
    of real free time before 15.08 — 10h estimated, 7.9h short."
    Never blocks the save, matching the standing no-gating precedent.

New in v9.10 (#123 — task due-dates via the calendar, the other half
of the owner's original scheduling ask, 2026-08-07: "option to set
DL or just sort of set the working windows for it"):
  - Right-click a DAY cell in the calendar's month view → "Set task
    due date to <date>…" → pick a task from the library. A
    lightweight "done by" marker on the task itself, deliberately NOT
    a full scoped Deadline object — quick ad-hoc due dates don't
    clutter the deadlines list or need a total-hours estimate to mean
    something.
  - Tasks window (View > Tasks/backlog) gets a `Due` column, right-
    click → "Set due date…" as an alternative to the calendar; an
    overdue task shows a ⚠ marker.
  - Month view itself now shows a ⚑ marker with the task name on its
    due date, drawn before events/work so it's the first thing you
    see in a cell.
  - `_month_click_to_day` inverts `_draw_calendar_month`'s own cell
    layout (shared class constants, same pattern as #122's
    `_week_click_to_slot`/week view).
  - Setting a due date appends the same visible day-file trace every
    other calendar action here does.
  - Split cleanly from #122's week-view "lock an hour for a
    deadline": week view is hour-precise (working windows), month
    view is day-precise (due dates) — each right-click action matches
    the granularity its own view actually has.

New in v9.9 (#122 — right-click to lock a calendar slot, owner's own
chosen interaction model, 2026-08-07: "shuld also be able to schedule
or add events or tasks there... option to set... the working windows
for it"):
  - Right-click any hour cell in the calendar's week view (View >
    Planning > Calendar) → a context menu lists your deadlines →
    pick one to lock that exact hour for it. Reuses #113's
    `lock_windows_to_ics` completely unchanged — this is a new entry
    point into already-tested plumbing, not new export logic.
  - `_week_click_to_slot` inverts the same layout math
    `_draw_calendar_week` draws with (now shared class constants,
    `_CAL_WEEK_HDR_H`/`_CAL_WEEK_PAD_L`/`_CAL_WEEK_COL_W`/
    `_CAL_WEEK_HOUR_H`), so a click always resolves to the exact cell
    it visually landed in. Clicks outside the grid (header, time
    labels, past the last day/hour) are silently ignored — no
    confusing menu with nothing to act on.
  - Locking appends the same visible day-file trace #113's own picker
    already writes — consistent regardless of which entry point was
    used.
  - Interaction model (right-click, not drag-and-drop or a click-
    then-dialog flow) was asked directly rather than guessed, after
    #103's lesson that a wrong guess on a similar-scale decision cost
    a full redo.

New in v9.8 (#121 — recurring commitments: day job, sleep, admin,
owner's own follow-up, 2026-08-07: "this softw doesnt have the...
realistic blocks... adding like sleep, eating blocks, work work
blocks... dont wanna fill my outlook with that kind of neurotic
stuff... these shuld ofc affect my DL calcs everythng"):
  - Tools > "Recurring commitments (lunch, day job, sleep, admin)…"
    (renamed from "Protected time windows," same settings key,
    fully backward compatible) — now supports a `Days` column
    ("Mon-Fri", blank = every day) and windows that cross midnight
    (sleep, e.g. 23:00-08:30), on top of the original lunch/wind-down
    use case. Bumped from 4 to 8 rows.
  - `_protected_intervals`/`_protected_hours` are now weekday-aware
    (`_parse_weekdays`) — a day-job block only reduces capacity on
    the days it's declared for, not every day. A window with
    start > end is only treated as a deliberate overnight block when
    the wrapped span is <=14h — a typo like "15:00-14:00" (23h) stays
    treated as invalid, same safe-degrade as before this feature,
    rather than silently eating almost the whole day's capacity.
  - These blocks already fed #82's aggregate-hours model AND
    #113/#118's `_free_slots`-based views (lock-windows, free-time
    forecast) automatically, since both already routed through
    `_protected_intervals`/`_protected_hours` — no new capacity-math
    code needed, just making the existing primitive weekday-aware.
  - The week calendar view (#120) now renders these as a background
    layer (neutral tan, labeled) — "realistic blocks" made visible,
    the specific thing asked for, without ever touching a real
    Outlook calendar.
  - Applied directly: the owner's own stated day-job (09:30-17:00)
    and morning-admin/commute (08:30-09:30) hours, both Mon-Fri, per
    what they wrote in this exact request — sleep and grey-admin
    left blank since no concrete times were given for those, rather
    than guessed.

New in v9.7 (#120 — a real week/month calendar view, owner's own
follow-up ask, 2026-08-07: "proper monthly or weekly calendar
views... event or stuff names there... similar to outlooks monthly
setup... exact time slots"):
  - View > Planning > "Calendar (week/month)…": an Outlook-shaped
    week view (hour-gridded, 7 day columns, events positioned at
    their real clock time) and month view (date grid, event names
    listed per cell, "+N more" when a day's too full to list), with
    Prev/Today/Next navigation and a Week/Month toggle.
  - Shows TWO layers together: imported calendar events (blue, named,
    via the new `parse_ics_events`/`parse_csv_events` — richer
    siblings of the existing capacity-math parsers that also keep the
    SUMMARY/Subject text instead of discarding it) and your own
    tracked work sessions (darker blue, named, straight from
    sessions.csv) — what's coming up and what you actually did,
    side by side.
  - Deliberately read-only — no drag-and-drop, no placing tasks onto
    it yet. This is the visual foundation #119 (automated schedule
    building) would sit on top of, not that feature itself.
  - The existing capacity-math pipeline (`_busy_intervals`,
    `_free_slots`, #113/#118) is completely untouched — the new
    parsers are separate, additive functions so nothing already
    tested could regress.

New in v9.6 (#118 — free-time forecast, a simple visual calendar view,
owner's own ask, 2026-08-07: "calendar view.. like smthg very
simple!.. easier to visually like inspect free slots"):
  - View > Planning > "Free-time forecast (calendar)…": one green/
    grey horizontal bar per day for the next 3 weeks. Green = free,
    already netting out calendar busy time (#114/#116) and protected
    windows, via `_free_slots` — the exact same primitive #113's
    lock-window picker and the day scheduler both already use, so
    this view can't disagree with either of them.
  - Deliberately glance-only — no actions, no picking, no locking.
    #113 already owns "pick specific windows for a deadline"; this is
    the wide-angle view underneath it, for when you just want to see
    what the next few weeks actually look like.
  - `_day_forecast(days=21)` is the data half (a list of (date,
    free_slots, free_hours) — reusable if a future view wants the
    same numbers); `_draw_forecast_bars` is pure rendering, no new
    computation.
  - Logged backlog #119 (automated schedule building — auto-drafting
    a multi-day placement across ALL deadlines at once, not just
    today) as the owner's own next idea, explicitly NOT built this
    round — real design questions first (multi-day balancing across
    competing deadlines is a different algorithm than today's greedy
    single-day pass; should a draft ever write anywhere, or stay
    read-only like every other planning view here).

New in v9.5 (#116 — Power Automate CSV fallback, in case #114's
publish link is blocked by a locked-down school/work tenant, owner's
own ask, 2026-08-07: "try to build also other ways to integrate
calendar or smthg idkk"):
  - File > "Import calendar CSV (Power Automate export)…": a second,
    independent calendar source for when Outlook won't publish a
    link at all. A no-code Power Automate flow (recurring trigger ->
    "Get calendar view of events" -> "Create CSV table" -> "Create
    file" to a OneDrive-synced folder) keeps a plain CSV current; this
    reads it. Chosen because Power Automate's STANDARD Office 365
    Outlook connector typically rides on the tenant's existing
    consent — unlike a custom Azure app registration (#115, Microsoft
    Graph sign-in), which commonly needs admin approval a student
    can't grant themselves. Researched, not guessed: EDU/work tenants
    frequently disable external calendar sharing at the policy level
    (the likely reason #114 alone might not be enough) but rarely
    lock down standard first-party Power Automate connectors the same
    way.
  - `parse_csv_busy_export`/`csv_busy_data` produce the exact same
    {date: [(start,end)...]} shape as the .ics parsers — every
    existing capacity view (_free_slots, #113's lock-window
    candidates, _capacity_lines) works identically regardless of
    which of the three sources (local .ics, subscribe URL, CSV) is
    configured. Dispatched by file extension in _busy_data/
    _busy_intervals, same settings key as before — one "calendar
    source" concept, not three parallel settings.
  - Lenient CSV parsing (ISO datetimes with or without a timezone/Z
    suffix), overlapping rows merged the same way .ics events already
    are, malformed/empty rows skipped rather than crashing the import.
  - See private-recommendations/calendar-integration-setup.md
    (gitignored) for the step-by-step Power Automate build — that's
    manual setup work only the owner can do, not something to script.

New in v9.4 (#114 — subscribe to a calendar link, closing the "manual
export every time" gap the owner hit right after v9.3, 2026-08-07:
"my outlook cal not working... dont wanna do the manual import"):
  - File > "Subscribe to a calendar link (.ics URL)…": paste a
    calendar's own publish/subscribe link (Outlook/Google's "Publish
    a calendar" URL, webcal:// or https://) instead of exporting and
    re-importing a file by hand every time. No login, no API key —
    the app just fetches the link periodically (every 60min) like a
    browser would.
  - `resolve_ics_source` is the seam: settings["ics_path"] can now be
    a local file (unchanged, old behavior) or a URL — resolved to a
    local cache file (data_dir()/calendar_cache.ics) before
    parse_ics_intervals/parse_ics_busy ever see it, so neither of
    those needed to change at all. A failed refresh (offline, link
    revoked) keeps serving the last good cache instead of going
    blank; a totally new link that never worked signals failure
    clearly so it can be reported, not silently swallowed.
  - Validated on save by actually fetching + checking for
    "BEGIN:VCALENDAR" before the link is stored — a bad/wrong link
    fails immediately with a clear message, not three days later as
    an empty calendar.
  - This directly feeds v9.3's "lock study windows" (and every other
    capacity view) — once subscribed, busy time updates itself.
  - Requires the owner's Outlook to allow calendar publishing; a
    locked-down school/work tenant may block it — Microsoft Graph
    API sign-in is the fallback if so, not built this round (bigger
    lift: OAuth, token storage — deliberately not built speculatively
    before knowing the simple option even works).

New in v9.3 (#113 — lock study windows for a deadline, owner's own
top-priority ask, 2026-08-07: "calendar and this software should talk
to each other better... realistically schedule time with enough
buffer"):
  - File > "Lock study windows for a deadline (.ics)…": turns a
    deadline's abstract "X hours needed" into concrete real dates
    worth locking. `_lock_window_candidates` walks every day between
    today and the deadline's due date, takes each day's single
    biggest contiguous free block (`_free_slots` — the same primitive
    the scheduler already uses, so imported calendar busy time and
    protected windows are already priced in), keeps days with 2h+ in
    one sitting, ranked biggest-block-first.
  - Pick the windows worth locking, then export them as real calendar
    events (`lock_windows_to_ics`) — a flat .ics file (same shape as
    the existing week-export) to import into Outlook/Google Calendar
    by hand. No live calendar API, stdlib only, same as every other
    .ics feature in this app.
  - Exporting appends a visible trace to today's diary file (which
    windows, for which deadline) — the sacred rule applied to a brand
    new feature from day one, not bolted on after the fact.
  - Deliberately simple ranking (biggest block wins, no peak-hour
    weighting) per direct owner feedback: the .ics mechanics aren't
    the hard part, don't over-engineer the picker.

New in v9.2 (two small high-priority fixes):
  - #109: SIGNAL's fallback (when nothing carried forward) now seeds
    from the single MOST URGENT scoped deadline's own keywords
    (_focus_items' own ranking) instead of blending every goal's
    keywords together. "SIGNAL: thesis" because thesis is actually
    behind pace, not because it's alphabetically first among goals.
    Falls back to the old all-goals blend only when no deadline is
    scoped. Directly caused by a real morning where the auto-fill felt
    unconfident even though the day's own plan line had already named
    the urgent deadline two lines up.
  - #83: the conversation-ready status export ("Copy status update")
    now says "Currently on ch5 (60% of its hours)" instead of a bare
    projection date when a deadline has a milestone breakdown — pure
    composition of _milestone_credit (factored out of
    _milestone_progress_line so both the internal and external-facing
    renderings share one computation) and the existing status text.
    Falls back to the date-based phrasing when no milestones exist.

New in v9.1 (two follow-ups from v9.0):
  - #105: the day timeline gets a 5th color (TL_SIGNAL2) for tier-2
    matched time — was previously indistinguishable from plain work.
  - #106: Data doctor now reports header-line adoption — which of the
    ~12 optional header conventions (SIGNAL2, WORKBLOCK, AVOID, YEAR,
    METRICS…) you've actually used in the last 60 days vs never
    touched. Read-only, reuses the existing _line_ever_used plumbing
    (refactored to share a counting core, _line_usage_count).

New in v9.0 (FLAGSHIP: tiered SIGNAL + declared work-block windows —
two real additions to the core data model, not connective fixes):
  - #96 TIERED SIGNAL: a new SIGNAL2: header line — a second, DISCRETE
    priority tier, not a blend. This does NOT touch the "Signal vs.
    maintenance" precedent (resolved 2026-07-13, see the design rules
    section): SIGNAL keeps meaning exactly what it always meant
    (today's ONE sharpest priority) — SIGNAL2 is a strictly separate,
    disjoint bucket (a task matching both tiers counts as tier-1 only,
    so tier-1's own number is never diluted). Carries forward like
    AVOID; the header line stays hidden until you actually use it,
    same as every other optional axis. Shows up live in the totals
    line ("signal 45% +20% tier-2"), in tomorrow's yesterday-recap,
    and as a new trailing-window insight (_signal_tier_insight, gated
    n>=5 declared days) under MOMENTUM & TRENDS.
  - #100 (first half) DECLARED WORK BLOCK: a new WORKBLOCK: HH:MM-HH:MM
    header line for an externally-committed window (a day job).
    Inside it, idle detection and the Windows+L screen-lock detector
    (v8.55) both wait ~3x longer before offering to log a break — a
    quick meeting or email check during already-spoken-for time isn't
    a break the way it is outside it. The genuinely-parallel-work half
    of #100 stays explicitly out of scope (flagged in HANDOFF as
    likely unsolvable honestly within a single-threaded timer — no
    fake 50/50 split invented here). Carries forward like AVOID;
    zero behavior change for anyone who never declares one.
  - Both features fully additive: a day file with no SIGNAL2/WORKBLOCK
    lines behaves byte-for-byte like before. 45/45 selftest suites +
    dedicated new-feature tests green.

New in v8.69 (four backlog items, priority/value order):
  - #82 FIX: protected windows (lunch, wind-down) subtracted from the
    scheduler's block placement but not from the separate aggregate-
    hours capacity model (_day_capacity → the capacity dashboard and
    cost-of-yes preview) — two capacity models silently disagreeing.
    Now both subtract the same daily protected-window hours.
  - #84: "cost of yes" (the live slack preview when adding a new
    deadline) now also flags pre-existing blocked task-library items
    under the same goal — "heads up: N task(s) under 'X' are already
    blocked" — so a capacity decision sees blockers, not just hours.
  - #93: File > "Open a day file…" is now a lighter in-app picker (a
    Listbox of the last 30 days + yesterday/a week ago/a month ago
    jump buttons, reading straight into a Text pane) instead of
    launching straight into the OS file dialog — the old dialog is
    still one click away as "Browse for a day file (file picker)…".
  - #86: the Insights tab's 20+ independent findings (sleep, energy,
    deep hours, streaks, trends, etc.) used to concatenate into one
    flat undifferentiated block. Now grouped under three sub-headers
    — TIME & FOCUS / ENERGY & BODY / MOMENTUM & TRENDS — tagged at
    the point each finding is generated, not guessed from the
    rendered sentence. "Copy for AI review" carries the same grouping.

New in v8.68 (quick reference restructured, owner's own follow-up
feedback):
  - Three changes to v8.67's quick reference, all direct feedback:
    (1) moved out of a new top-level Help menu into Tools >
    "Quick reference — what does this app do?…" — no new top-level
    menu, folded into the existing structure. (2) Rebuilt as a real
    two-pane topic viewer (a Listbox of 13 topics on the left, a Text
    pane on the right that updates on selection) instead of one long
    scrolling wall of text — the classic WinHelp/CHM shape the owner
    asked for ("og windows vibe"), built with plain tkinter widgets,
    no new dependency. (3) Every topic got a real paragraph or two
    instead of a one-line entry — explains WHAT each convention does
    and WHY, not just the syntax. Content unchanged in substance from
    v8.67, just far more explained and far better organized.

New in v8.67 (Help menu — a quick reference, owner's own ask):
  - New Help menu (after File/View/Tools, the classic spot) >
    "Quick reference…": one hand-written, deliberately short window
    covering the header-line conventions (SIGNAL/AVOID/YEAR/ENERGY/
    METRICS/TODO/DECIDED/CAPSULE/COMMIT/EXPERIMENT/TODAY), the task-
    box shortcuts (done:, [15m], right-click), what's in each View-
    menu category, and an "easy to forget exists" list — the owner's
    own example was rediscovering the Decision log. Written by hand,
    not generated from the changelog, and explicitly NOT meant to be
    rewritten every version — a stable reference, not documentation
    that chases every release.

New in v8.66 (CRITICAL FIX: SIGNAL carry-forward was silently dead
for anyone who never typed into it, + a wall-of-text reduction,
2026-07-29):
  - FIXED, high-severity: `_carry_signal` used to `return` the moment
    it found a "SIGNAL:" line in yesterday's file, even if that line
    was blank — which is EVERY day's line, since v6.1 writes it
    unconditionally. The goal-seed fallback below it was therefore
    dead code for anyone who has ever had a single blank SIGNAL day:
    once one blank day existed, every SIGNAL-dependent feature in the
    app (timeline color, the status-bar flag, and every insight that
    reads signal% — best-weeks, mood, thrash, avoid-trend, and more)
    silently had nothing to work with, forever. Now a blank-but-
    present line falls through to goal-seeding exactly like a missing
    line always did. Confirmed and fixed directly from the owner's
    real report ("all the recaps... signal ratio... always empty").
  - Wall-of-text reduction: AVOID/YEAR/METRICS used to print
    unconditionally every single day, blank, whether or not they'd
    ever been used — three lines of pure noise for anyone who hasn't
    adopted those axes. They now only appear once actually in use (or
    currently carrying a real value); SIGNAL/ENERGY stay unconditional
    as the original pair. Direct response to "huge txt wall... not
    easily eye-able... I'm human not machine."

New in v8.65 (bug fixes + two small features from the owner's own
data, 2026-07-29):
  - FIXED (#97): auto-capture no longer creates a new task-library
    entry for every growing snapshot of a still-being-typed TODO
    bullet — `_add_task` now collapses a same-source prefix-extension
    into the existing entry instead of appending a duplicate. The
    owner's real settings.json was cleaned with the identical logic:
    77 → 34 task-library entries (backed up first).
  - CHECKED (old report from 2026-07-11): task-switch-during-a-break
    time inheritance — not reproducible against current code, closing
    it out.
  - #91 completed-task archive: marking a task Done now appends it to
    `settings["tasks_done"]` (with `done_on`/`actual_h`) instead of
    discarding it, so future features wanting clean Done history don't
    have to re-parse every day file for `--- Done:` lines.
  - #92 command shorthand: `done: thesis ch4` typed in the task box
    marks the matching task-library item done — a small fixed-verb
    parser, not #60's deferred (and much riskier) Python console.
  - Polish: extreme deadline-projection lateness (a triple-digit day
    count in the first days of a new deadline, before real velocity
    settles) now reads "far behind — see the date" instead of an
    absurd-sounding specific number; the underlying math is unchanged.
  - Also found (not fixed — needs live reproduction, see backlog
    #101): Finnish ä/ö characters can get mangled to `�` somewhere
    upstream of the diary save — confirmed the corruption is already
    in the source day-file text, not introduced by settings.json
    handling (which checks out clean); likely Tk's own Windows
    clipboard paste handling.

New in v8.64 (View menu reorganized — the map matches the territory):
  - 22 flat View-menu commands grouped into submenus that mirror the
    NORTH STAR's own three pillars (see HANDOFF.md): Planning
    (foresight), Memory (the archive), Values (alignment), plus
    Writing/Reports for the practical extras. Dashboard, "What should
    I do now?" and Tasks/backlog stay top-level since they're the
    highest-frequency entries. Pure reorganization — every command is
    the exact same function, same _tracked() wrapper, nothing moved
    behavior-wise; verified no menu item was lost via a full menu-tree
    walk, not just a visual check.

New in v8.63 (focus signature — backlog #53, the shape of a real
week):
  - The weekday-pattern insight (v7.4) compares total hours per
    weekday; `_hour_quality` (v8.8) compares total hours per hour-of-
    day, collapsed across every weekday. Neither shows the actual 2D
    shape: WHEN, within which days, signal work reliably happens. New
    `_focus_signature_grid`: for each (weekday, 4-hour bucket) cell,
    the fraction of that weekday's occurrences (trailing 180 days)
    with any SIGNAL-matched work in that bucket — a CONSISTENCY score,
    not a raw total, so one unusually long day doesn't drown out the
    pattern. A weekday needs 4+ occurrences in the window before its
    cells count at all. New `_focus_signature_line`, in the Monday
    review (read once in a while, not a daily view): "focus signature:
    Tue 08-12 lights up 100% of the time (n=4); Mon 00-04 never does
    (n=4)." Silent unless the best cell clears a real 50% consistency
    bar. New "focus-signature" selftest suite (a hand-verified 4-week
    scenario landing on the exact grid values, silence with no SIGNAL
    declared, silence below the 50% consistency bar, silence below the
    n≥4 occurrence gate); 45/45 green.

New in v8.62 (conversation-ready status export — backlog #57, a
deliberately different register):
  - Copy-for-AI-review is written for feeding an LLM; nothing was
    written for pasting into an email to an actual supervisor/advisor.
    New Life dashboard button "Copy status update": one short,
    professionally-toned paragraph per scoped deadline — "Progress
    update — Thesis: 12h this week (up from 8h last). Currently
    projected 3d behind pace, landing August 04. Blocked on: ch5
    draft." New `_status_update_text`/`_status_update_all`, pure reuse
    of `_dl_progress`/`_dl_projection`'s own numbers plus v8.60's fresh
    `blocked_by` field for the blockers line — no new computation, no
    new data source. Worth being explicit that this ONE surface sounds
    different on purpose (external-facing register), not a precedent
    for softening the rest of the app's blunt internal voice. New
    "status-update" selftest suite (behind-pace phrasing, on-pace
    phrasing with a blocker pulled in via v8.60's field, silence for
    an unscoped deadline, `_status_update_all` joining multiple
    deadlines and skipping unscoped ones); 44/44 green.

New in v8.61 (cost of yes — backlog #52, the capacity math run BEFORE
you commit, not after):
  - Every capacity view (`_capacity_lines`, `_plan_line`, #47's root
    cause) only ever looked at deadlines already on the books —
    nothing showed what ADDING one would do before you committed. New
    `_cost_of_yes_line(hypothetical, existing)`: reuses the exact same
    aggregate-slack math `_capacity_lines` already runs for real
    deadlines, against a pool with one hypothetical more in it —
    "committing to 'NewProj' would push slack from +5.0h to -10.0h —
    Thesis would need to give up 1.0h/day to make room." Wired into
    the deadline edit dialog as a LIVE preview: as soon as a genuinely
    NEW row (a name not already saved) has a real date and total_h
    typed in, the preview line updates on every keystroke, against the
    saved deadlines as the baseline — editing an EXISTING deadline in
    place is deliberately not previewed (ambiguous whether that's new
    scope or a correction; v8.51's renegotiation tracker already
    covers that case on save). Turns the moment of over-committing —
    which used to only ever show up as a ⚠ weeks later — into a
    visible choice at the only point it's still cheap to say no. New
    "cost-of-yes" selftest suite (no-existing-deadlines baseline, a
    hand-verified scenario naming which deadline gives ground and by
    how much per day, silence on missing/zero scope, a past due date,
    an unparseable date); 43/43 green.

New in v8.60 (waiting-on / blocked tasks — backlog #44, external
dependencies the planner can't see):
  - Everything the planner knew about was under the owner's own control;
    real work often isn't ("can't touch ch4 until the supervisor
    replies"). Task-library items gain an optional `blocked_by` field —
    Tasks window right-click > "Set blocked by…" (free text, same
    popup shape as Set goal/Set deadline). Blocked items are now
    excluded from `_reentry_opener`'s re-entry-ramp candidates and both
    "uncommitted hours → pick from Task library" suggestion lines — the
    planner stops suggesting things you structurally can't do yet. New
    `_waiting_on_lines` surfaces them separately (Life dashboard's
    "Deadlines & Goals" tab, a new "WAITING ON:" section) so they don't
    just vanish. In the Tasks window itself, blocked rows get a ⛔
    marker and the blocker reason inline, tagged in red. No due-date
    logic, no reminders to chase the blocker — that's someone else's
    problem to solve, not the app's to nag about. New "waiting-on"
    selftest suite (formatting, silence with nothing blocked, silence
    with no tasks); existing "reentry" suite extended with a blocked-
    item exclusion case; 42/42 green.

New in v8.59 (milestones inside a deadline — backlog #36, content not
just hours):
  - `total_h` measures effort, not progress — 30h logged on a 60h scope
    can be 70% done or 20% done depending on WHAT got done. Deadlines
    gain an optional "Milestones" field in the existing edit dialog:
    `ch4 [15h]*, ch5 [20h], revisions [10h]` — same `[Nh]` bracket
    convention the task time-box already uses, a trailing `*` marks a
    milestone done. New module-level `_parse_milestones` (pure) +
    `_milestone_progress_line`, surfaced in the dashboard's "Deadlines
    & Goals" tab: "ch4 done, ch5 at 60% of its hours, revisions at 0%
    of its hours." Hours accrue in milestone ORDER — the current
    (first not-done) milestone gets credit for whatever matched hours
    haven't already been claimed by earlier done ones; later
    milestones stay at 0% until the ones ahead of them are checked
    off. A proxy, not a real per-milestone tracker (there's no
    mechanism to tag which tracked minutes belong to which milestone)
    — but an honest one, since it never claims more than the
    deadline's own real matched total. New "milestones" selftest suite
    (parsing including the done-marker and malformed text, a hand-
    verified 3-milestone scenario landing exactly on the design's own
    "ch5 at 60%" example, silence with no milestones field); 41/41
    green.

New in v8.58 (protected time windows — backlog #50, the scheduler's
missing exclusion zone):
  - `_work_window` (v7.9) sets one daily envelope the scheduler is
    allowed to fill; nothing stopped it suggesting a block over lunch
    or a wind-down hour that's technically "free" but shouldn't be
    claimed. New Tools > "Protected time windows…": named daily-
    recurring windows ("lunch 12:00-13:00", "wind-down 21:00-22:00"),
    a small settings list, same grid-of-entries dialog pattern as
    Goals/Deadlines. New `_protected_intervals` parses them into
    (start, end) tuples, malformed HH:MM entries skipped rather than
    raising; `_free_slots` now subtracts them exactly like calendar
    busy-time already is — one more "busy" source merged into the same
    primitive, not a new concept. New "protected-windows" selftest
    suite (valid windows parse correctly, a backwards range/malformed
    time/missing key are all skipped rather than crashing, empty
    settings silence); 40/40 green.

New in v8.57 (commitment-reliability ledger — backlog #18, self-
calibration feedback, not a promise-tracking gate):
  - A new opt-in header line — never auto-inserted, same convention as
    EXPERIMENT/DECIDED: `COMMIT: thesis 4h` commits to 4h on tasks
    matching "thesis" that day; `COMMIT: 4h` (no keywords) commits to
    4h of tracked work overall. New `_commit_from_text` parses it (same
    first-match-wins template as `_energy_from_text`); new
    `_commitment_reliability` reconciles each of the last 30 days that
    had a real commitment against what actually got delivered. One
    line in the Monday review once 5+ real commitments exist: "you hit
    your morning commitment 3 of the last 5 days — you reliably
    deliver ~60% of what you promise yourself; promise that and mean
    it." Never grades any ONE day, only the trailing rate — the honest
    version of a promise-tracker without becoming a compliance gate.
    `COMMIT:` added to the header syntax-highlight rules. New
    "commitment-reliability" selftest suite (parsing with/without
    keywords and malformed input, a hand-verified 5-commitment/3-hit
    scenario mixing keyword-scoped and whole-day commitments, silence
    below the n≥5 gate); 39/39 green.

New in v8.56 (time capsule — backlog #61, the forward-looking
counterpart to on-this-day):
  - On-this-day (v8.12) looks back one year, automatically. Nothing let
    you deliberately seal a note for a FUTURE date until now: type
    `CAPSULE: 2026-08-15 | message` in any day's file, and once today
    matches that target date, the header surfaces it: "a note from 45
    days ago: message." Pure text convention — new `_due_capsules`
    scans every day file for a `CAPSULE:` line whose date equals
    today (a day can't reference itself, so a same-day capsule is
    silently excluded), `_capsule_lines` formats the days-ago phrasing;
    no new data source, same "read the day files back" shape as TODO
    carry-over. `CAPSULE:` added to the header syntax-highlight rules.
    New "time-capsule" selftest suite (two capsules due the same day
    from different files, chronologically ordered; a capsule targeting
    a different date excluded; a malformed line with no pipe safely
    ignored; the same-day self-reference edge case; full silence);
    38/38 green.

New in v8.55 (screen-lock break detection — Windows+L should trigger a
break, direct owner request):
  - The idle-minutes detector (`idle_seconds`/`_watch_idle`, long-
    standing) only catches genuine keyboard/mouse idleness — a
    deliberate Win+L lock shorter than `idle_min` (default 10m) never
    crossed that threshold, so a quick coffee-break lock never got
    offered as a break at all. New `is_locked()`: the OpenInputDesktop
    ctypes trick (stdlib only, no pywin32) — the call fails when the
    interactive desktop isn't reachable, which is exactly what happens
    while locked. New `_watch_lock`, called from `_tick()` right next
    to `_watch_idle`: on unlock, reuses the EXISTING
    `_offer_idle_break` retro-split dialog directly — one mechanism,
    two triggers, no new UI. A `MIN_LOG_SECS` (30s) floor so an
    accidental tap-and-untap doesn't pop a dialog for a 2-second gap.
    Gated on `idle_min` being on at all (0 = away-detection off covers
    this too) but deliberately NOT on meeting-mode's `idle_off_until`
    — that suppresses ambiguous no-input time during a call, but an
    actual lock is unambiguous even mid-meeting. UNTESTED by the
    selftest harness, matching the existing `idle_seconds`/
    `_watch_idle` precedent (this is a live-Windows-only interaction
    this Linux dev environment cannot exercise) — please confirm on
    your actual machine that locking and unlocking now offers the
    break dialog.

New in v8.54 (planner realism factor — backlog #25, the schedule
audits itself):
  - v8.0 writes a suggested schedule every morning; nothing ever
    checked what became of it. New `_planned_hours_from_file`: reads a
    past day's own written schedule block back out of its file (same
    in-file convention trick `_estimate_factor` uses for "--- Done:"
    lines) — total hours actually PLACED into blocks, excluding the
    "uncommitted" free-time line. New `_planner_realism_factor`:
    (actual tracked hours / planned hours, capped at 1.0) per day,
    median over the last 60 days with a real written schedule — "your
    average planned day survives 90%." `_day_schedule_lines` now
    scales each item's needed hours by that ratio BEFORE placing
    blocks, and prints the density it's planning at right in the
    schedule header. Self-calibrating planning without any compliance
    tracking of the person — it grades the PLANNER's realism only,
    same standing guardrail as everywhere else in this app. New
    "planner-realism" selftest suite (parsing sums placement lines and
    correctly excludes the uncommitted line, a hand-verified 6-day
    median with one overshoot day correctly capped at 1.0, silence
    with fewer than 5 real scheduled days); 37/37 green.

New in v8.53 (sensor health meter — backlog #23, the platform watching
its own instruments):
  - Every insight silently degrades when a source rots — the phone
    sleep-export automation breaks, the .ics goes stale, ENERGY stops
    being typed — with nothing ever surfacing that before now. New
    `_sensor_health_lines`, surfaced as a new section at the top of
    the Data doctor window: per source, last date seen with real data,
    coverage % over the trailing 30 days, and a plain alarm once it's
    gone quiet longer than a reasonable cadence ("sleep import: last
    seen 2026-06-15 (30d ago), 0% coverage — the phone automation may
    have stopped"). Also surfaces the personal baselines the anomaly
    watch judges against — median sleep, median week — so the
    co-pilot's calls are inspectable, not oracular. New
    "sensor-health" selftest suite (all three alarms firing together
    with exact coverage/gap numbers, a healthy pass with no alarms,
    the fully-unconfigured silence path); 36/36 green.

New in v8.52 (weekly "one less" — backlog #35, a subtraction advisor):
  - Every insight so far adds awareness; this one subtracts. New
    `_one_less_candidates`: three removal candidates sourced entirely
    from mechanisms this app already has — the single worst meeting-
    fragmentation cost (v8.42), the task you bounce off most (v8.12),
    the after-21:00 work that taxes tomorrow (v8.38) — each only
    included when it already clears its OWN honesty gate. New
    `_pick_one_less` (pure): picks the first candidate that isn't the
    one suggested last week, so an ignored candidate doesn't repeat
    back-to-back while a different one also qualifies — falls back to
    repeating when it's the only one left (that's not nagging, it's
    just still true). One line in the Monday review: "THIS WEEK, TRY
    ONE LESS: the meeting that fragments your day — Wed's meeting cost
    1.3h." New "one-less" selftest suite (the pure rotation rule in
    isolation, candidate composition/framing wired via stubs on the
    three already-tested sub-insights, the rotation actually avoiding a
    back-to-back repeat, a single-candidate week correctly repeating
    instead of going silent); 35/35 green.

New in v8.51 (deadline renegotiation tracker — backlog #46, scope-creep
honesty):
  - Deadlines could always have their date/scope edited silently, with
    nothing remembering the ORIGINAL numbers. New module-level
    `_deadline_revisions_after_save(old, new, today_iso)`: compares the
    deadline list before/after a save (matched by name) and appends a
    `history` entry — the OLD date/total_h, timestamped — to any
    deadline whose date or total_h actually changed; unchanged
    deadlines carry their history forward untouched. Wired into the
    existing deadline edit dialog's save(), no new UI. Once 2+
    revisions exist, new `_deadline_renegotiation_line` adds one line
    under that deadline in the dashboard's "Deadlines & Goals" tab:
    "this deadline has moved 2 time(s) since 2026-06-29 — due date is
    now 45d later than first set, scope grew from 20h to 45h." No
    judgment beyond the numbers — a LIVE, ongoing check, distinct from
    v8.50's post-mortem (which only ever fires once, after a deadline
    resolves). New "deadline-renegotiation" selftest suite (history
    accumulates across edits without overwriting, a no-op save adds no
    phantom entry, a brand-new deadline gets no history key at all,
    date-only/scope-only/both-moved phrasing, a malformed entry stays
    silent); 34/34 green.

New in v8.50 (deadline post-mortem — backlog #28, each deadline closed
becomes calibration data):
  - Once a scoped deadline's due date passes, one retro block writes
    into that day's file instead of the deadline just quietly
    disappearing: scope vs actual hours logged; the estimate factor on
    THIS project specifically (`_estimate_factor` extended to take an
    optional keyword filter, app-wide blend unchanged by default); a
    RETROSPECTIVE projection check — what the same trailing-21-day
    pace math `_dl_velocity`/`_dl_projection` use would have predicted,
    evaluated as of 21 days before the due date, against the date the
    scope was actually completed: "predicted 13.07, actually finished
    04.07 — ran 9d pessimistic"; and the real pace kept over the
    project's whole life. New `_deadline_postmortem_lines` (pure) +
    `_run_deadline_postmortems` (the write-once guard, marks
    `postmortem_written` on the deadline dict so it never repeats),
    hooked into `_new_day_header` right after the on-this-day line.
    New "deadline-postmortem" selftest suite (a fully hand-verified
    scenario exercising all four lines at once, silence for an
    unscoped deadline, silence before the due date passes, the
    write-once guard actually preventing a repeat); 33/33 green.

New in v8.49 (goal lifetime ledger — backlog #45, the un-windowed
view):
  - Every existing view is windowed — 8 weeks (alignment/trajectory), a
    deadline's own scope (burn-down), a calendar year (#15, not yet
    built). Nothing answered "how much of my life has this actually
    taken, total." New `_lifetime_ledger_line(name, kws, start_iso)`:
    total hours + session count since `start_iso` (a deadline's own
    stored start, if set) or the first-ever matching csv row (goals
    have no start field yet — "since the beginning" is the honest
    default). One new line under each goal and deadline in the
    dashboard's "Deadlines & Goals" tab: "Thesis: 187h across 62
    session(s) since 2026-06-29 (134 days — 1.4h/day lifetime
    average)." Row-level scan (needs the session count, which
    `matched_minutes` alone can't give — that only returns a total).
    New "lifetime-ledger" selftest suite (fallback to earliest matching
    row, an explicit start_iso both anchoring the date shown AND
    filtering out earlier matches, silence with no keywords, silence
    with keywords that never matched); 32/32 green.

New in v8.48 (annual theme — backlog #64, the year-scale sibling of
SIGNAL/AVOID):
  - A new `YEAR: <theme>` header line, auto-carried into every day file
    exactly like AVOID (v8.13) — set once, edited whenever the theme
    genuinely changes, silent (blank) until then. New `_carry_year`
    (same shape as `_carry_avoid`). The on-this-day line (backward-
    looking one year, existing) now also surfaces that year's theme
    when it was set: "on this day, 2025: 1h30m work — felt good about
    the outline today · that year's theme: 'finish the thesis' — still
    true?" `YEAR:` added to the header syntax-highlight rules so it's
    excluded from the on-this-day snippet search the same way SIGNAL/
    AVOID/etc already are. New "annual-theme" selftest suite
    (carry-forward, blank when unset, the on-this-day theme callback
    with/without a YEAR: line last year, silence with no file at all);
    31/31 green.

New in v8.47 (decision log lite — backlog #62, "didn't I already think
this through"):
  - A new opt-in, purely archival line convention: `DECIDED: apartment —
    staying another year, rent's still fair`. Deliberately NOT #9's
    Reopening Guard (reopen counters, typed justification to unlock) —
    that was explicitly held back as too close to a gating pattern; this
    is just a searchable record, no counter, no reopening friction, no
    unlock mechanic. New View > "Decision log…": a read-only list of
    every `DECIDED:` line across every day file, newest first — a
    shortcut to browse without typing a query first, same underlying
    text the existing Search all days already makes findable.
    `DECIDED:` added to the header syntax-highlight rules alongside
    SIGNAL/AVOID/ENERGY/METRICS/EXPERIMENT. New pure `_scan_decisions`
    (file scan, no new data source) + thin `_decision_log_view` Tk
    layer. New "decision-log" selftest suite (newest-file-first
    ordering, a false-positive line that merely MENTIONS "decided:"
    mid-sentence correctly excluded since only line-START counts,
    silence with none declared); 30/30 green.

New in v8.46 (ask-your-diary pinned searches — backlog #71, a
recurring lookup becomes one click):
  - Search all days gains a pinned-search row above the results: click
    a pin to re-run that query instantly, "📌 Pin" saves the current
    query box text, right-click a pin to remove it. Settings-backed
    (`settings["pinned_searches"]`), capped at 5 — re-pinning an
    existing query re-surfaces it at the front instead of duplicating;
    pinning past the cap drops the least-recently-used one. New pure
    `_pinned_after_add`/`_pinned_after_remove` (the list ops, testable
    without Tk) behind new `_pin_search`/`_unpin_search` App methods.
    Pure UI addition over `_diary_rank_days` (v8.30) — no change to
    the ranking logic, just a shortcut to populate the query entry.
    New "pinned-searches" selftest suite (front-insert on add,
    re-adding re-surfaces instead of duplicating, the cap drops the
    OLDEST not the newest, a blank query is a no-op, remove); 29/29
    green.

New in v8.45 (weekly experiment engine — backlog #20, closing the
diagnose-then-nothing loop):
  - A new opt-in, in-file convention: typing `EXPERIMENT: no work after
    21:00` in Monday's header (same convention as SIGNAL/AVOID/ENERGY —
    never prompted, never auto-inserted, the user types it themselves
    when they want to). The FOLLOWING Monday's WEEK REVIEW reports that
    week's measured shift on work, late-evening (≥21:00) minutes and
    sleep against the trailing 4-week baseline before it: "EXPERIMENT
    'no work after 21:00': late-evening -1.0h vs baseline; sleep
    +0.5h/night vs baseline; output +0.0h vs baseline." Deliberately
    NEVER a verdict on whether the free-text RULE was followed ("kept
    it 5/7 days") — parsing arbitrary user text into an enforceable
    check would be too fragile to state honestly; a plain before/after
    on numbers the app already tracks instead. New
    `_experiment_from_file`/`_week_metric_totals`/
    `_experiment_review_line`, hooked into the existing
    `_week_review_block`. `EXPERIMENT:` also added to the header
    syntax-highlight rules alongside SIGNAL/AVOID/ENERGY/METRICS.
    Needs ≥2 real baseline weeks; silent otherwise — stated once in
    the review, never re-nagged mid-week. New "experiment-engine"
    selftest suite (a hand-verified 3-metric delta across 4 baseline
    weeks + the experiment week, silence with no EXPERIMENT declared,
    silence with too little baseline history); 28/28 green.

New in v8.44 (energy forecast for today — backlog #29, what your body's
data suggests vs what the weekday table plans):
  - New `_energy_forecast_line(days=90)`, hooked into the morning
    header right after the co-pilot note: "today smells like a
    3.5-4.5h day (Tuesday, running on debt, n=6) — plan the must-do
    inside that." "Last night's sleep" and "trailing sleep debt"
    combine into ONE honest signal — the 3-night rolling average
    ending on a given day — compared against your own trailing-90-day
    median, then bucketed against your own weekday pattern (same
    weekday as today, same rolling-sleep tier). The matching bucket's
    actual tracked-work range (25th-75th percentile band, not a single
    guess) is the forecast. `_capacity` says what you PLAN to have;
    this says what your recent data suggests you'll ACTUALLY have — no
    change to `_capacity` itself, a separate signal alongside it.
    Needs today's own rolling-sleep reading (silent without it) and
    n≥5 matching historical days; silent otherwise. New
    "energy-forecast" selftest suite (a hand-verified 10-Tuesday
    rest/debt split where the matched band collapses to one exact
    value, silence with no usable rolling reading for today, silence
    with too little sleep history to trust a personal norm); 27/27
    green.

New in v8.43 (year rhythm map — backlog #26, the year's shape at a
glance):
  - View > "Year rhythm map": a new canvas, 52 columns (Monday-start
    weeks) × 24 rows (hour of day), each cell shaded by tracked
    minutes in that hour that week — mirrors `_heatmap`'s canvas code
    but at year scale and by TIME OF DAY, not by day total. Where
    `_heatmap` shows how MUCH per day, this shows WHEN: bedtime drift
    eras, morning-discipline phases, an exam-sprint block, the dead
    summer, all visible as one picture. Both work and break rows count
    (this is about when you're at the desk at all, not deep-work
    minutes — `_heatmap` already covers that). New pure
    `_year_rhythm_grid(weeks=52)` returns {(week_idx, hour): minutes};
    `_year_rhythm_view` is the thin Tk canvas layer over it, same
    split as every other view in this app. New "year-rhythm" selftest
    suite (two rows landing in the same cell sum instead of
    overwriting, a break row counts, the oldest in-window week lands
    right at the edge, a day one day outside the window is excluded,
    a future date is excluded); 26/26 green.

New in v8.42 (meeting fragmentation tax — backlog #21, meetings cost
more than their duration):
  - The existing meeting-load insight only ever counted HOURS busy.
    New `_meeting_fragmentation_lines(days=7)` prices what a meeting
    does to the open time AROUND it: for each meeting on each of the
    last 7 days, `_day_fragmentation_tax` simulates removing just that
    one meeting (all others held fixed) and measures the DEEP CAPACITY
    (free blocks ≥90m) recovered — a 20-minute meeting stranding a
    60-minute sliver after it can cost 1.3h, not 0.3h. Reports the
    worst single meeting plus the week's total: "Wednesday's 15:40
    meeting: 0.3h long, cost 1.3h of deep capacity" / "meeting
    fragmentation tax this week: 1.7h." New module-level
    `_free_from_busy`/`_deep_capacity_minutes` factored out of
    `_free_slots` (the scheduler's own free-time math) so the same
    core is shared instead of reimplemented; `_free_slots` refactored
    to call it, behaviour unchanged. Silent with no calendar configured
    or when the week's total tax is negligible (<0.5h) — same
    threshold discipline as every other insight. Hooked into
    `_insight_lines` right after the meeting-load check it complements.
    New "meeting-fragmentation" selftest suite (pure-helper checks,
    hand-verified single-meeting marginal cost, silence with no
    calendar, silence below the tax floor, the worst-offender+total
    composition, and an honesty check that a day outside the 7-day
    window doesn't count); 25/25 green.

New in v8.41 (running-hot index — backlog #24, the early-warning
version of the sleep-for-work trade):
  - New `_running_hot_line(recent_days=14, prior_days=60)`: same
    recent-vs-prior window shape as word drift (v8.29/v8.37). Four
    independent signals, each with its own honest sample-size gate —
    sleep below your own recent norm, workout frequency drop,
    late-night count (reuses `_day_start_late_map`, v8.38), break-ratio
    compression — speaks only when at least TWO move together: "14
    days running hot (sleep -1.0h/night vs norm, 3 late nights) —
    schedule one flat day before your body schedules it." One signal
    alone has too many honest explanations to be worth a line; two
    moving together is the actual early warning the trajectory line
    (which only catches this after ~4 weeks) misses. Hooked into
    `_copilot_note` between the bottom-line risk and the sharpest
    anomaly — a body-schedule risk outranks a task-schedule risk.
    Silent again the moment the signals ease, no memory of having
    spoken before. New "running-hot" selftest suite (two-signal speak
    case, one-signal-alone silence, sparse-data gate silence, a second
    two-signal case exercising the workout/break-ratio pair); 24/24
    green.

New in v8.40 (backup integrity check — backlog #63, the safety net
auditing itself):
  - #23's sensor health meter covers external INPUT sources going
    stale (health export, calendar); nothing checked the OUTPUT side —
    whether the weekly backups/ csv copy (backup_if_due) is actually
    still current. New backup_integrity_line(): silent when the
    newest backup is ≤10 days old, else "last backup: 15 days ago
    (expected weekly) — the automation may have stopped" (or "no
    backup found yet" if backups/ is empty entirely). Surfaced on the
    Data doctor window, opportunistic rather than a startup nag —
    directly on-brand given the 2026-07-11 dual-instance data-loss
    incident (CLAUDE.md). New "backup-integrity" selftest suite (silent
    with no csv yet, speaks when backups/ is empty, silent within the
    10-day buffer, speaks past it, picks the newest of several backup
    files not the oldest); 23/23 green.

New in v8.39 (break budget v2 — backlog #72, weekday-specific norms):
  - _break_budget_line (v8.34) blended ALL real workdays into one median
    "full-day norm" regardless of weekday. Now buckets real_days by
    dt.date.weekday() and uses TODAY's own weekday's median when there's
    enough history for it specifically (n≥10) — "full-day norm ~50m
    (Mons)" instead of a blend that quietly mixes Friday-afternoon and
    Tuesday-morning break patterns. Falls back to the all-days blend
    when a specific weekday doesn't have its own n≥10 yet (most users
    won't, at first — the gate degrades per-weekday, not to silence),
    same as the plain "full-day norm ~Xm" from before. Matches the
    weekday-aware capacity table (_capacity, v5.8) the rest of the app
    already assumes. Existing "break-budget" selftest suite extended
    with a per-weekday-engaged case and a fallback case.

New in v8.38 (lag correlation #4 — backlog #70, fragmentation carries over):
  - a fourth check joins _lag_insight: does yesterday's task-switching
    predict a SHALLOWER today, not just a scattered yesterday (#16 is
    same-day)? "the day after a 6+ switch day, 100% of your signal work
    lands in shallow blocks (<20m) vs 0% after a focused day (≤2
    switches) — fragmentation carries over." Wires two measurements
    that already existed — _day_switches (v8.18) as the trigger,
    _day_shallow_frac (v8.19's block logic, generalised from today-only
    to any day) as the next-day measure — through the (day, day+1) loop
    v8.31 introduced. _shallow_threshold factored out so both the
    today-only line and this lag check use the same personal shallow
    threshold. Same n≥5/bucket gate as the other three lag checks.
    Existing "lag" selftest suite extended with a dedicated positive
    case (hand-verified 100%/0% split) plus the new silence case.

New in v8.37 (word drift, the other direction — backlog #69):
  - _word_drift_insight (v8.29) only ever reported words trending UP.
    A new _word_fade_insight reports the opposite: a topic that was
    frequent and went quiet — "words appearing less lately: 'girlfriend'
    (20→0 mentions, last 30d vs prior 90d) — gone quiet, worth noticing
    why." Often matters more than a new word appearing. Symmetric gate
    to the increase check (pn≥3 in the old window, vanished or collapsed
    to ≤1/3 its prior share); reported as its own separate insight line,
    not merged with the increase — up and down are different kinds of
    noticing. _word_drift_counts factored out so both directions share
    one file scan instead of two identical ones. Same "word-drift"
    selftest suite extended.

New in v8.36 (health-hub view — backlog #65, captured data finally shown):
  - View > "Health × focus" gains a second table: mindful minutes, RHR,
    HRV, weight (v8.27) and daylight hours (v8.28) — all captured onto
    the day record for a while now, none of them ever shown as more
    than a single header line. Kept as its OWN table in the SAME window
    rather than widened into one ~90-char row with the proven sleep/
    workout/steps/work/signal table above — stays readable, and nothing
    about that first table had to change. A footer explains exactly how
    to turn each column on when everything's still empty. New
    `_health_extras_lines` is pure logic split from the Tk glue (same
    pattern as the rest of the app), so it's tested without a display.
    selftest suite 22 — the last of this session's run.

New in v8.35 (lens overlap check — backlog #48, the honesty layer audits itself):
  - View > "Lens overlap check…": every % this app has ever printed
    (alignment shares, signal%, goal minutes) assumes SIGNAL/AVOID/
    goals/domains/deadlines are disjoint keyword lenses — nothing ever
    verified that. Checks every PAIR of declared lenses for REAL
    double-counted minutes in the last 30 days, not just a coincidental
    keyword-string collision: "'run'/'training' both match Body (goal)
    and Fitness (domain) — 5.0h counted toward both in the last 30d."
    Catches the harder case too — two DIFFERENT keywords each
    independently matching the same task name, with no shared keyword
    string at all (the actual reason a naive "do these keyword lists
    intersect" check wouldn't be enough). Silent when nothing overlaps
    or fewer than 2 lenses are declared. selftest suite 21.

New in v8.34 (break budget — backlog #33, a reframe instead of a verdict):
  - the totals line gains one more segment, learned from your own good
    days rather than judging any single break: "breaks so far 45m ·
    your typical by this hour 0m · full-day norm ~10m". Per-event
    judgment (the pull-back, the doomscroll insight) doesn't reach every
    situation; a budget changes behaviour where nagging fails — a
    number to plan around, never a scold. _break_budget_line learns the
    full-day norm as the median break total across real workdays (work
    ≥3h), and "typical by this hour" as the median CUMULATIVE break
    minutes those same days had accrued by the current hour — days that
    hadn't taken a break yet by that hour correctly count as zero rather
    than being silently absent from the median (the actual bug this
    took care to avoid, and what the test specifically catches). Needs
    n≥10 real workdays in history to speak. selftest suite 20.

New in v8.33 (metrics shorthand — backlog #66, lower friction for habits):
  - the METRICS line (v8.27) required "key=value" for everything; a bare
    word with no "=" now implicitly logs word=1 — "METRICS: meditation,
    cold_shower" instead of typing "=1" on each. Mixed forms in the same
    line work too ("meditation, water=6, cold_shower"). _metrics_insight
    needed no change at all — it already just checks presence-of-key, so
    shorthand entries feed the exact same correlation machinery as any
    typed key=value pair. Rewrote the parser to split-by-comma first
    (was one big regex over the whole line) specifically so bare tokens
    have somewhere to be recognised; existing key=value/key:val parsing
    unchanged (same suite, extended, no regression).

New in v8.32 (week-ahead risk brief — backlog #42, the co-pilot's weekly twin):
  - Monday's file already opens with WEEK REVIEW (looking back); it now
    also gets WEEK AHEAD, looking forward across the next 7 days as a
    whole — composes _day_capacity/_dl_progress/_dl_projection (no new
    data): "14.0h free across the next 7 days · deadlines need ~40.0h ·
    ⚠ overbooked by 26.0h before the week even starts", plus which day
    is genuinely tight ("front-load elsewhere if something's due") and
    which deadlines are already behind at real pace. Silent for a normal
    week with slack and nothing behind — only speaks when something's
    actually worth flagging before Monday even starts. selftest suite 19.

New in v8.31 (lag correlations — backlog #22, what today does to tomorrow):
  - every insight so far correlates SAME-DAY pairs. Three new checks use
    the new loop shape instead — (day, day+1) — same honesty gates
    (n≥5/bucket, a real swing required): workout day -> next-day output
    ("the day after a workout you average 5.0h vs 1.0h — the gym looks
    like a productivity tool, not a cost"); short-sleep NIGHT -> the day
    AFTER that, not just the same day ("sleep debt doesn't clear in one
    day"); working past 21:00 -> next morning's first-session start time
    ("mornings after… you start 1.8h later on average"). All three
    compose into _lag_insight, hooked into Insights. selftest suite 18.

New in v8.30 (ask your diary — backlog #14, ranked multi-term search):
  - Search all days gains a second button, "Copy matching days for AI",
    next to the existing literal single-term search (kept as-is,
    nothing removed). _diary_rank_days splits a query into terms,
    OR-matches every day file, and ranks by BREADTH (distinct terms hit
    — a day mentioning all your terms beats one repeating just one of
    them), then depth, then recency — an honest better keyword search,
    not fake semantic search (no embeddings, stdlib-only rule holds).
    _matching_days_text builds the clipboard payload: the top 5 ranked
    days' matching lines (not whole files) with date headers, same
    manual-copy-paste pattern as the existing weekly "Copy for AI
    review" (v5.1) — a year of day files becomes queryable without an
    API key. selftest suite 17 (breadth-beats-depth ranking, no-match
    and empty-query cases, the clipboard text shape).

New in v8.29 (word drift — the diary's own free text, unlocked at last):
  - a new insight reads what you actually WROTE, not just your tracked
    task labels: _diary_word_counts tokenizes free-typed diary text
    (skipping every structural line via the same _LINE_TAG_RULES the
    syntax highlighter uses — no SIGNAL/METRICS/TODO/timer line ever
    counts), and _word_drift_insight compares normalised word frequency
    over the last 30 days against the 90 before that, naming the word
    with the sharpest real increase: "words appearing more lately:
    'apartment' (0→14 mentions, last 30d vs prior 90d) — what's
    actually on your mind, separate from your tracked tasks." No new
    source needed — the diary text has been fully collected the whole
    time, this is the first thing to actually read it as itself.
  - fix, found while building this: METRICS:/TODAY: lines (v8.27/v8.16)
    were never added to _LINE_TAG_RULES, so they rendered as plain
    diary text instead of bold like SIGNAL/AVOID/ENERGY — fixed, and
    it's also what made this feature's line-skipping correct from day
    one instead of double-counting those lines as prose.
  - selftest suite 16 (structural-line exclusion, stopwords, the real
    drift-detection case, the volume-gate silence case).

New in v8.28 (daylight — a data source that needs no export file at all):
  - Tools > "Daylight location (latitude)…" — a single latitude (no
    address, no network, no API key) powers day_length_hours(), a
    standard declination/hour-angle approximation (matches real-world
    solstice values within the expected few-minutes error). Every other
    source needs an export file or a typed line; this one is free the
    moment a latitude is set, because it's pure math over the date. New
    _life_day key "daylight_h". A new insight compares output/energy on
    your shortest-daylight days vs your longest — but only once your OWN
    history spans a real seasonal swing (n≥8 each side, ≥2h median gap),
    so it stays honestly silent for months and then speaks once the
    data's actually there. Answers "capture it now, even if the payoff
    is seasons away" directly. selftest suite 15.

New in v8.27 (the health-hub pivot — a generic metrics line + wider capture):
  - METRICS line: a new "METRICS: " header line, same in-file convention
    as SIGNAL/AVOID/ENERGY — type ANY future personal metric as
    "key=value" pairs ("meditation=10, water=6, mood=calm") and it lands
    as one new key on the day record, with zero new code per metric.
    This is the direct answer to "will we regret not logging something
    in 6 months": SIGNAL/AVOID/ENERGY/mood each needed a bespoke parser
    as a new axis came up; METRICS generalises the pattern once so the
    next one is free. New insight (_metrics_insight) compares signal
    share on days any given metric was logged vs days it wasn't, and
    names the metric with the biggest swing — works for whatever key
    gets invented tomorrow, not a fixed list.
  - Health import widened: parse_health_dir now also opportunistically
    captures mindful/meditation minutes, resting heart rate, HRV, and
    weight — using the SAME already-recommended export app (Health Auto
    Export), not a new integration. Also fixed a real gap: a file
    containing ONLY one of these metrics (common — the app exports one
    CSV per metric type) used to be silently skipped entirely, since the
    old skip-gate only checked for sleep/workout columns. Mindful
    minutes now shows in the existing "(sleep …, workout …)" header
    line; RHR/HRV/weight are captured onto the day record, ready for a
    future health view (backlog #65+), not yet surfaced to avoid
    cluttering today's one-line header.
  - Together these are the concrete first step of turning the app into
    a health hub without a rewrite: METRICS is where biohacking habits
    (meditation, cold exposure, supplements, caffeine) get logged, right
    next to the diary text they're already part of — one file, not a
    second app. selftest suites 13-14 (14/14 green).

New in v8.22-v8.26 (five more, same push, second wave):
  - v8.22 RESCUE BLOCK (#41): "What should I do now?" gains a mid-
    afternoon-going-sideways branch — if it's 15:00-21:00, a real
    deadline needs it, and today's tracked so far is under 25% of what
    the day was supposed to carry, one salvage line instead of the
    normal recommendation: "salvage plan: one 45m block on Thesis
    before the day ends still makes it count." Silent the moment real
    progress exists.
  - v8.23 MOOD ≠ ENERGY (#4): the ENERGY line now accepts an optional
    word ("ENERGY: 3 anxious") — a different axis than the 1-5 number
    (how it felt vs how much fuel there was). New insight: groups days
    by mood word, names the one with the biggest signal-share
    departure from baseline. n≥3 per mood, n≥10 days for a baseline.
  - v8.24 APP USAGE-PATTERN METER (#56): every View-menu command now
    bumps a counter (Tools > "Feature usage…" to see it) — the tool
    auditing its own use, not the owner's life. Which of 55+ built
    features actually get opened vs sit unused.
  - v8.25 BEST-WEEKS RETROSPECTIVE (#58): a positive-framed insight —
    the top-3 historical weeks by signal-hours×share, and what was
    distinctive (which weekday carried most of the signal work). The
    complement to a mostly diagnostic-of-problems insight set.
  - v8.26 REALLOCATION SCENARIO (#59): the sequel to #47 (done) in
    `_capacity_lines` — when the most-urgent deadline has a genuine
    TODAY capacity problem and a less-urgent one has real slack, one
    concrete trade: "cutting TUTA to 0.0h/day (from 0.5h) for now
    would free 0.5h/day for Thesis — one way to close the gap, not the
    only one."
  - All five: pure views/math over existing data (plus one small
    counter for #56), tested individually and via a real menu-command
    invocation (not just the wrapper function) for #56's wiring. Full
    regression + selftest.py (12/12) still green.

New in v8.16-v8.21 (a bigger batch: six backlog items in one push):
  - v8.16 DECLARED SHORT DAY (#37): type "TODAY: 4h" (or "TODAY: sick",
    no number needed) into today's own file and the NEXT morning's
    verdict judges against that declared cap instead of the usual
    bar — "short day as declared — 2.0h tracked, plan honored," never
    the harsh "what stole it?" for a day you already flagged honestly
    in advance. The streak also bridges through a declared day
    (checked within a 21-day lookback, so it doesn't cost a file-open
    per day across the full 112-day best-streak scan).
  - v8.17 FIRST-HOUR AUDIT (#40): new insight comparing days that open
    with signal work vs days that open with something else — "days you
    open with signal work end 3.0h heavier... the first hour is a
    lever, not a warm-up." n≥5 each side.
  - v8.18 TASK-THRASH METER (#16): new insight comparing signal% on
    high-switch-count days vs low-switch-count days — distinct from
    the block-decay curve (#38, duration) since this counts how many
    times you jumped, not how long you stayed. Also surfaces live in
    the status bar once a day crosses 4 switches.
  - v8.19 SHALLOW-WORK RATIO (#49): a same-day depth check — "62% of
    today's signal hours came in blocks under 20m — that reads as
    busy, not deep." Threshold derives from the #38 decay curve when
    available, a flat 20min guess otherwise.
  - v8.20 LIBRARY GRAVEYARD SWEEP (#43): once a month (first Monday),
    names Task-library items sitting untouched 60+ days in the week
    review block. Never auto-deletes.
  - v8.21 TASK-LIBRARY COMMITMENT DENSITY (#55): the Tasks/Library
    window header now shows total signal-priority volume undated —
    "3 signal-priority item(s), ~9.0h estimated total, undated."
  - All six: pure views/math over data already collected, no new
    settings dialogs beyond what already existed, tested individually
    and in combination (full header generation with declared-short-day
    + graveyard-sweep firing together), full regression + selftest.py
    (12/12) still green throughout.

New in v8.15 (personal block-length decay curve, backlog #38):
  - new insight: buckets work blocks by length and compares the break
    that immediately follows each bucket — "blocks past ~60m are
    followed by 4.0x longer breaks (20m vs 5m) — your natural cycle
    looks like ~60m, box accordingly." Your own focus cycle, derived
    from real history, not an imposed pomodoro number. n≥3 per bucket,
    needs 2+ populated buckets to compare.
  - starting a SIGNAL-matching task without an explicit [Xm] box now
    quietly suggests one in the status bar: "try boxing ~60m (your
    natural cycle)" — read from the same decay curve. Only appears
    when you didn't already type a box, never overrides one.

New in v8.14 (behind-pace root cause: capacity vs. choice, backlog #47):
  - the burn-down window's real-pace footer gains a second, sharper
    line for a behind-pace deadline: is it that this week genuinely
    didn't have enough free time (a capacity problem — something else
    has to give), or did plenty of free time exist and just go
    elsewhere (a choice problem — reallocate, don't add hours)? "Thesis
    is behind pace — but you had 18h free this week and only put 1h
    into it. Not a capacity problem." Reuses _dl_progress's own
    "behind" flag + _day_capacity + matched_minutes, no new data. Only
    speaks Wed onward (needs the week mostly through to be a fair
    sample) and only when actually behind pace with a real scope set.

New in v8.13 (AVOID — the inverse lens, backlog #39):
  - SIGNAL names what matters; a new "AVOID: news, email" header line
    names what you're trying to shed — the exact same keyword-lens
    shape (matched_minutes/task_matches), inverted. Carries forward
    day to day like SIGNAL, but with no goal-seeded fallback: it's a
    standing declaration, not a daily pick, so an empty line stays
    empty rather than getting auto-filled.
  - The yesterday-summary line now reports it right next to signal%:
    "(yesterday: 4h30m work / 0h30m breaks, signal 67%, avoid 12% ↓)".
    The arrow is a quiet week-over-week comparison (this week so far
    vs all of last week), only shown with 2+ active days on both sides
    and a real ≥3-point move — silent otherwise, same honesty gate as
    everything else here. Three lines of parsing, symmetric with
    SIGNAL, completes the lens family.

New in v8.12 (procrastination pattern map — treat the cause):
  - new insight: which task do you flee FROM? A 'bounce' = a work run
    that dies within 10 minutes into a break — aversion's signature.
    With 6+ starts and a 50%+ bounce rate it names the worst offender:
    "you bounce off 'thesis: intro' within 10 min on 75% of starts
    (6 of 8) — that's not laziness, the task is too big; cut it into
    [30m] pieces." The pull-back (v8.10) treats the symptom in the
    moment; this finds the task that keeps causing it. selftest suite 12.

New in v8.11 (re-entry ramp — the pull-back's click made cheap):
  - resuming work after a 30min+ break, the status line now hands you the
    smallest concrete opener: "· start small: 'thesis: fix table 3'
    (0.2h)". _reentry_opener prefers a task-library item related to the
    active task (smallest estimate first), then the smallest signal-
    priority item, then any smallest item, else today's first TODO
    bullet. Activation energy is the real enemy after a long break — the
    pull-back (v8.10) gets you to click, the ramp makes the click land on
    a ten-minute piece instead of the mountain. selftest suite 11.

New in v8.10 (breaks get teeth — and a measured tax):
  - BREAK PULL-BACK: when a break interrupts a SIGNAL task and runs past
    the threshold (Tools > Break pull-back, default 20 min, 0 = off), the
    gentle coffee pill becomes a pull-back: '⚑ 23 min off "thesis: ch4" —
    click: the first minute is the whole battle', one beep, jumps to
    front; at 2× it hardens ('⚑⚑ … is bleeding out — one click.').
    Breaks off admin keep the old gentle pill. Deliberately a LOUD nudge,
    never a lock — the twice-held anti-gating precedent stands; a lock
    you can alt-tab past is noise, this makes ignoring it a decision.
  - BREAK QUALITY (the doomscroll tax, measured): the break notes you've
    typed for years ("walk", "scroll puhelin"…) now feed an insight —
    "after a moving break your next work block averages 41m (9 samples);
    after a scroll break 19m (7)". Nothing new to log; n≥5 per bucket.
    Both tested (selftest suite 10).

New in v8.9 (where you left off — the diary pays you back at task start):
  - starting or switching to a task with history now hands you back the
    LAST line you wrote about it, right in the status bar: 'Working —
    thesis: ch4 · last time (08.07): "stuck on regression table, try
    clustered SEs next"'. _last_context() finds the most recent tracked
    day for the task and the last human-written line after that day's
    final "--- Task:" marker (machine lines skipped via the highlighter's
    own rules). Kills the re-finding-the-thread cost of every resume —
    the Memory pillar paid out at the exact moment it's useful.
    Read-only; tested in selftest (suite 9).

New in v8.8 (energy-aware scheduling — the morning plan gets smart):
  - the v8.0 time-blocked schedule stops placing work in the earliest free
    gap and starts placing it by the QUALITY of the hour. _hour_quality()
    learns a 0–1 profile of when your work actually lands (60 days);
    _energy_place() gives each item (most-urgent first) its best-quality
    free time — so the hardest/most-behind deadline claims your peak hours
    and admin drifts to the troughs — "13:00-15:00 Thesis (peak)" instead
    of "09:00-11:00 Thesis" just because 9am was the first gap. Blocks
    stay contiguous (no 15-min shards); with no history it falls back to
    the exact v8.0 earliest-first placement. The single biggest upgrade to
    the planner itself, not another view. Tested on Linux.

New in v8.7 (right-now recommender — the plan, made real-time):
  - View > "What should I do now?": the dynamic companion to the morning
    schedule. Reads the current hour against your LEARNED deep-focus
    window (_deep_window — your best 3h block from 60 days of history),
    which deadline is most behind at real pace, today's energy, and the
    documented 19–21 fatigue window, then states one clear pick in the
    status bar: "inside your deep-focus window (09–12) — spend it on
    Thesis (~22d behind), not admin" / "past your deep window — good slot
    for admin; protect Thesis for tomorrow's peak" / "fatigue window —
    move or rest". Energy ≤2 adds "a lighter task beats forcing the hard
    one." Rule-based, tested on Linux across every branch.

New in v8.6 (the co-pilot speaks FIRST — proactive, attentive):
  - ANOMALY WATCH (_anomaly_lines): flags what's unusual vs your OWN
    baseline, not an ideal — "worst sleep week in 10 weeks (5h30m vs your
    7h30m norm)", "20 days since any Finnish — drifting from something you
    flagged", "3 straight tracked days at ~0% signal". Ranked, honesty-
    gated (needs real history). Shows in the Life review under UNUSUAL.
  - THE MORNING GREETING: the new-day header now opens with a "co-pilot:"
    line — the single most important thing right now, chosen for you:
    an actionable risk (a deadline slipping, a domain starving) when there
    is one, else the sharpest anomaly. The app stops waiting to be opened
    and greets you in the day file, per the sacred "day file is the app"
    rule. Silent when there's genuinely nothing to flag (no filler).
    Pure logic, tested on Linux (anomaly ranking + note prioritisation).

New in v8.5 (Life review — the pillars finally speak as ONE voice):
  - View > "Life review — synthesized briefing…": one window that pulls
    the week's numbers + VALUES (alignment, v8.4) + AHEAD (outlook, v8.3)
    + TRAJECTORY (v8.2) + PATTERNS (insights) together, then closes with
    a synthesized BOTTOM LINE that reconciles the pillars into ONE action
    — e.g. "You're behind on Thesis (~22d late) AND under-investing in
    Growth (-14 pts): same fix, not two — the first block of each day
    goes there before the urgent small stuff eats the morning." The
    connective tissue between the three pillars; the AI-analyst idea done
    keyless (rule-based). "Copy for AI second opinion" ships the whole
    briefing to the clipboard. Pure view, composes already-tested
    functions; the bottom-line rules are tested on Linux (all 4 branches).

New in v8.4 (Life domains — time tracker becomes life management):
  - Tools > "Life domains…": name a handful of life areas (Work, Body,
    Growth, People, Rest) with the task keywords that belong to each and
    an optional target share. Domains are the VALUES layer above goals —
    same keyword-lens shape (matched_minutes), one level up: the top of
    the source -> lens -> view stack.
  - View > "Life alignment…": where your tracked time ACTUALLY went by
    domain over 8 weeks vs the share you said each should get — "Work
    40.0h 93% aim 60% (+33) · Growth 1.0h 2% aim 20% (-18)" — and it
    names the widest say-do gap: "Growth — getting 18 points less of your
    time than you said it should." The platform's core question, in one
    place: is your time flowing where you say it should? First brick of
    the ALIGNMENT pillar (HANDOFF North Star). Pure view, tested on Linux.

New in v8.3 (Outlook — the app starts looking FORWARD, not just back):
  - View > "Outlook — weeks ahead…": a forward simulation across ALL
    scoped deadlines at once, at your REAL recent pace (not the abstract
    capacity _capacity_lines uses). States which deadlines land late, in
    what order, by how much — "⚠ Thesis: due 22.07, lands ~13.08 (22d
    late) at 2.7h/wk actual · +1h/day → 23d sooner" — plus the aggregate
    lever: "landing all of them on time needs about +0.8h/day more than
    you're averaging." Prediction + prescription. First brick of the
    FORESIGHT pillar (see HANDOFF North Star); pure math over v8.1's
    _dl_projection, no new data, tested on Linux.

New in v8.2 (trajectory insight — life at the scale of months):
  - a new INSIGHT that, unlike every other one (all capped at 3-4 weeks),
    splits the last 8 weeks in half and compares the earlier half to the
    recent one across domains — "8-week trajectory: work 5.0→15.0h/wk ↑,
    sleep 7.5→6.2h ↓" — then names the sharpest TRADE-OFF in one line:
    "you're buying work hours with sleep — a sprint move, not a season."
    Same honesty gates as the rest (both halves need 5+ active days;
    silent when nothing meaningfully moved). First brick of the
    "trajectory / life-memory" North Star now written into HANDOFF.

New in v8.1 (deadline finish-date projection — backlog #13):
  - the burn-down window gains one honest footer line: instead of only
    "needs Xh/day" (which assumes perfect future compliance), it says
    where you ACTUALLY land at the pace you've kept — "at your real pace
    (2.0h on active days, active 19% of days) you land ~13.08 — 21d late
    (due 23.07). +1h/day from now → 23d sooner." Purely a VIEW: reads
    _dl_progress + a new keyword-lens velocity (_dl_velocity), writes
    nothing to the day file. Speaks only with 5+ real intervals on the
    deadline in the trailing 21 days (the usual honesty gate); silent for
    deadlines with no total-hours scope. The +1h/day line turns the
    diagnosis into a lever for free — same projection re-solved at a
    higher rate.

New in v8.0 (the actual scheduler — planning-engine tier c):
  - the morning header's "focus order today" list is now an actual
    time-blocked schedule: each competing deadline (most urgent first,
    behind-pace overrides a merely-sooner due date) greedily claims its
    needed h/day out of today's real free time (_free_slots, v7.9),
    earliest slot first — "08:00-12:05 Thesis (4.1h) ⚠ behind pace"
    instead of just "Thesis — 4.1h needed." Leftover free time after
    everything is placed gets one line naming Task-library signal
    items, same as before. If a deadline's need doesn't fit today's
    free time, says so plainly ("doesn't fit today's free time") rather
    than silently truncating.
  - MVP scope, on purpose (see HANDOFF's design notes written before
    this was built): TODAY only, one greedy pass, not a multi-day
    optimizer. Falls back to the plain priority list on a fully-booked
    day, when there's no free time to place anything into.
  - Still just a VIEW, generated once at day-header time same as
    plan/focus-order — nothing about whether you actually follow it is
    ever tracked, gated, or asked about. That guardrail was written
    into the backlog specifically because this feature is the most
    tempted to break it; it doesn't.

New in v7.9 (scheduler foundations — prep for the v8.0 push):
  - `parse_ics_busy` (the per-day busy-HOURS scalar every capacity view
    reads) is now a thin sum over a new `parse_ics_intervals`, which
    returns the actual busy TIME RANGES per day, merged and sorted.
    Same file parsed once, two views over it — this is the one real
    infra gap the planning-engine backlog flagged as blocking a true
    time-blocked schedule, now closed. Side effect, called out
    explicitly rather than left silent: double-booked/overlapping
    meetings now count their overlap once, not once per event, so
    total busy hours on a day with a real double-booking will read
    slightly lower than before — the more honest number.
  - New `_free_slots(date)`: work-day window (Tools > "Work-day window",
    default 08:00-22:00) minus calendar busy ranges minus (today only)
    already-logged work/break time from the csv, merged, slivers under
    15 min dropped. The actual foundation piece — v8's real scheduler
    reads this directly instead of re-deriving it.
  - One small end-to-end proof it works, in the day file where
    everything visible lives: "biggest free block today: 14:00-17:00
    (3.0h)" in the morning header, right after the plan line.

New in v7.8 (on this day):
  - the morning header now checks for a day file exactly one year ago
    (same month/day; Feb 29 falls back to -365 days) and, if one exists,
    prints "on this day, 2025: 3h12m work — <first diary line>" — the
    "keeps the data forever" idea paid back as a quiet delight instead
    of a feature you have to go open a window for. Read-only, never
    touches last year's file.

New in v7.7 (per-task clock, so switching doesn't look like it lied):
  - the big clock has always shown SESSION-cumulative time (matches the
    old app's "studying duration" — only Reset clears it, a task Switch
    never does, on purpose; the csv already attributed minutes to the
    right task all along). But visually, that reads as "the timer kept
    going" the instant you switch tasks. New small readout next to the
    big clock — "this task: 3:12" — shows elapsed time on the CURRENT
    interval only, visibly back to 0:00 the moment you Switch or Start.

New in v7.6 (readable diary — pure view layer, file untouched):
  - syntax highlighting in the diary pane: day headers bold, SIGNAL/
    ENERGY/TODO/WEEK REVIEW headers bold green, themed-writing blocks
    purple, warnings red, raw Start;/Stop;/Reset; bookkeeping lines
    small and grey, everything you actually typed left alone. Tags
    style how Tk renders the text; the file on disk is byte-identical
    either way — verified directly, not just claimed.
  - Tools > "Hide raw timer lines" folds Start;/Stop;/Reset; lines out
    of view entirely (Tk elide — zero height, not just invisible),
    reversible any time. On the real file this was built against: 255
    lines, 35% of them raw events — folding shrinks the visible
    document by a third immediately. Setting persists across restarts.

New in v7.5 (focus order names the leftover hours):
  - "focus order today" now adds a final line when there's slack after
    the deadlines are fed: "(5.5h uncommitted — pick from Task library:
    reply to EU email)", naming your signal-priority backlog items
    instead of leaving unclaimed capacity unexplained.

New in v7.4 (insights v3):
  - weekday pattern: flags a genuinely weaker weekday once every day of
    the week has enough samples ("Tues average 2.3h vs Thus at 5.0h —
    54% weaker") — not noise, a real recurring gap worth scheduling
    around.
  - meeting-load vs deep-hours: do days with 2h+ of meetings actually
    cost you focus, or do you work around them fine — your own history
    answers it instead of assuming.
  - break-ratio drift: this week's break share vs the 3 weeks before —
    catches a slow creep before it's obvious.
  All three reuse existing data (day_index, calendar busy-time,
  read_rows) — no new sources, no new infra, same honest n>=3 gating
  as every other insight.

New in v7.3 (timeline third color + focus order):
  - the day timeline paints goal-aligned-but-not-signal work (a run,
    when today's signal is thesis) in its own color, distinct from
    signal-green and plain-work-blue — three buckets, not a binary.
  - new day headers get a "focus order today" block when 2+ scoped
    deadlines are competing: most urgent first (behind-pace overrides
    merely-sooner), each with its needed h/day. Second tier of the
    planning/recommendation engine (see HANDOFF.md) — a stated
    recommendation, not a configurable one.

New in v7.2 (goal-aware signal flag):
  - the "not today's signal" status flag now checks whether the active
    task matches a GOAL even though it's off-signal — "not today's
    signal, but counts toward: Physical Engine Maintenance" instead of
    a bare warning. Off-signal-but-goal-aligned (a run, when today's
    signal is thesis) and genuinely unattributed (matches nothing) are
    different situations; the status bar now says which one it is.

New in v7.1 (fix + first recommendation-engine piece):
  - fix: Life dashboard tabs were empty (real bug — the tab-content
    frames were created as children of the window instead of the
    Notebook, so nb.add() couldn't actually attach them).
  - Week plan / capacity, when overbooked across multiple deadlines,
    now states a PRIORITY ORDER — most-urgent-first allocation of the
    shared capacity pool — instead of just an aggregate "overbooked by
    Xh": which deadline is fully funded, which takes the cut, by how
    much. Plain arithmetic over numbers already computed elsewhere, the
    first piece of the planning/recommendation direction (see
    HANDOFF.md's backlog for the fuller design — a suggested-focus-list
    view and a true time-blocked schedule are the next two steps).

New in v7.0 (the day file becomes provably the source of truth):
  - REBUILD sessions.csv FROM DAY FILES (Tools menu): parse_day_file_to_
    rows() is the exact inverse of event_line() — given a day file's own
    Start/Stop/Task lines, it reconstructs the work/break csv rows that
    produced them. "The day file is the source of truth, csv is a
    derived cache" stops being a design principle and becomes something
    you can actually do: lose or corrupt sessions.csv and it's fully
    recoverable from the day files alone. Backs up first.
  - TASKS LINK TO DEADLINES too, not just goals — same dropdown pattern,
    its own column. Right-click any row to set/change its goal or
    deadline after the fact (auto-captured items land with neither set).
  - LIFE DASHBOARD becomes a tabbed home (Today & Week / Deadlines &
    Goals / Insights) instead of one long scroll, plus a hub row linking
    out to every detail view (Weekly, Monthly, Trend, Health, Heatmap,
    Burn-down) — a front door, not a replacement; nothing was deleted.
  - IMPORT LIFE RECORD (File menu): restores goals/deadlines/capacity
    (merged by name, never replaces what's already configured) and day
    files (only ones missing locally, never overwrites current work)
    from a previous JSON export. Pair with the csv rebuild above for a
    full, lossless recovery: import restores the day files, rebuild
    regenerates the session log from them.

New in v6.8 (fix the actual todo-capture bug):
  - real bug: EVERY bullet the user actually typed used no space after
    the dash ("-THESIS", not "- THESIS") and the parser required one —
    nothing was ever being captured. Fixed (space now optional), with a
    guard so "---" decorator lines don't get mistaken for bullets.
  - same-line "TODO: buy milk" now works too, not just a header line
    followed by separate bullets.
  - capture now runs on the live 10s autosave (today's diary), not only
    at day-rollover or themed-writing save — same-day items land within
    seconds, with a status-bar "+N to task library" confirmation.
  - one-time-per-launch backfill sweeps the last 14 days for items the
    old parser missed — existing writing didn't need retyping.
  - Tasks window bug: the priority column is the leftmost one, so a
    click meant to select a row for Done/Start was cycling its priority
    AND wiping the whole list's selection (refresh() rebuilds the tree).
    Selection now survives.

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
import math
import os
import queue
import re
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
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


def _pinned_after_add(pins, query, max_n=5):
    """Backlog #71: pure list op behind the "pin this search" button —
    a settings-backed shortlist stays useful capped small; adding an
    already-pinned query re-surfaces it at the front (most-recently-
    used) instead of duplicating, and the oldest drops once the list
    is full."""
    query = (query or "").strip()
    if not query:
        return list(pins)
    out = [p for p in pins if p != query]
    out.insert(0, query)
    return out[:max_n]


def _pinned_after_remove(pins, query):
    return [p for p in pins if p != query]


def _deadline_revisions_after_save(old_deadlines, new_deadlines, today_iso):
    """Backlog #46: deadlines can have their date/scope edited silently
    at any time — nothing remembers the ORIGINAL numbers. Compares old
    vs new deadline lists (matched by name) and returns new_deadlines
    with a 'history' entry APPENDED to any deadline whose date or
    total_h actually changed — the OLD values, timestamped, so scope
    creep is traceable after the fact. A deadline's own history
    carries forward unchanged when nothing about it moved this save.
    Pure list op; the caller (the existing edit dialog's save()) does
    the actual settings write."""
    old_by_name = {d.get("name"): d for d in old_deadlines if d.get("name")}
    out = []
    for nd in new_deadlines:
        nd = dict(nd)
        od = old_by_name.get(nd.get("name"))
        if od:
            moved = (od.get("date") != nd.get("date") or
                    float(od.get("total_h") or 0) != float(nd.get("total_h") or 0))
            hist = list(od.get("history") or [])
            if moved:
                hist.append({"date": od.get("date"),
                            "total_h": od.get("total_h"), "as_of": today_iso})
            if hist:
                nd["history"] = hist
        out.append(nd)
    return out


def _pick_one_less(candidates, last_key):
    """Backlog #35: pure selection rule behind the subtraction advisor.
    `candidates` is [(key, text), ...] in priority order; picks the
    first whose key isn't the one suggested last week, so an ignored
    candidate doesn't repeat back-to-back when a different one also
    qualifies. Falls back to candidates[0] when everything left IS
    last week's key (the only real candidate repeating isn't nagging,
    it's just still true)."""
    if not candidates:
        return None
    return next((c for c in candidates if c[0] != last_key), candidates[0])


def _parse_milestones(spec):
    """Backlog #36: 'ch4 [15h]*, ch5 [20h]' -> [{"name": "ch4", "h":
    15.0, "done": True}, {"name": "ch5", "h": 20.0, "done": False}].
    Same [Nh] bracket convention the task time-box already uses; a
    trailing * right after the bracket marks a milestone done — same
    idea as a '--- Done:' line, just inline. Malformed or empty text
    yields an empty list, never an error (this field is optional)."""
    out = []
    for m in re.finditer(r"([^,\[\]]+?)\s*\[([0-9.]+)h\](\*)?", spec or ""):
        name = m.group(1).strip()
        if name:
            out.append({"name": name, "h": float(m.group(2)),
                       "done": bool(m.group(3))})
    return out


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


def backup_integrity_line(today=None):
    """Backlog #63: the safety net auditing itself. #23 (sensor health
    meter, v8.x) covers external INPUT sources going stale — health
    export, calendar. Nothing checked the OUTPUT side: is the weekly
    backups/ csv copy (backup_if_due, above) actually still current.
    One line, silent when healthy, surfaced opportunistically on the
    Data doctor run rather than as a startup nag — a >10-day buffer
    over the 7-day cadence so a user who opens the app every week or
    two never sees it, only someone whose backups have genuinely
    stopped (the kind of check that's cheap until the day it isn't —
    see the 2026-07-11 dual-instance data-loss incident)."""
    today = today or dt.date.today()
    if not os.path.exists(SESSIONS_CSV):
        return None
    bdir = os.path.join(data_dir(), "backups")
    newest = None
    try:
        names = os.listdir(bdir)
    except OSError:
        names = []
    for fn in names:
        try:
            d = dt.date.fromisoformat(fn[9:19])
        except (ValueError, IndexError):
            continue
        newest = d if newest is None else max(newest, d)
    if newest is None:
        return "no backup found yet — the weekly automation may not have run"
    age = (today - newest).days
    if age <= 10:
        return None
    return (f"last backup: {age} days ago (expected weekly) — the "
            "automation may have stopped")


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
    """Scan csv files for date + sleep/workout/steps/mindful/RHR/HRV/weight
    columns. Returns {date_iso: {"sleep_h", "workout_min", "steps",
    "mindful_min", "rhr", "hrv", "weight_kg"}} (only keys actually found).
    Understands Health Auto Export headers ('Sleep Analysis [Asleep] (hr)'),
    Health App Data Export Tool ('Sleep' = '7h 54m', d.m.yyyy dates,
    decimal commas) and a hand-made 'date;sleep_h;workout_min' file. Apps
    like Health Auto Export often export ONE CSV PER METRIC (a "Heart Rate
    Variability.csv" with no sleep/workout column at all) — the file is
    kept and scanned as long as date + ANY recognised column is present,
    not just the original sleep/workout pair, so a file full of a newly
    wanted metric isn't silently skipped the way it would be if this only
    matched the two metrics the app started with. Later files/rows
    overwrite earlier."""
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
        # opportunistic extras: captured whenever the SAME already-
        # recommended export app happens to have these toggled on, not
        # guessed against a format that hasn't reached this machine
        mcol = col("mindful", "meditation")
        rhrcol = col("resting heart rate", "resting_heart_rate", "rhr")
        hrvcol = col("heart rate variability", "hrv")
        wtcol = col("weight", "body mass")
        if dcol is None or not any((scol, wcol, stcol, mcol, rhrcol,
                                    hrvcol, wtcol)):
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
            if mcol is not None and mcol < len(r):
                dm = _dur_minutes(r[mcol])
                v = dm if dm is not None else _num(r[mcol])
                if v and 0 < v <= 1440:
                    rec["mindful_min"] = v
            if rhrcol is not None and rhrcol < len(r):
                v = _num(r[rhrcol])
                if v and 20 <= v <= 220:
                    rec["rhr"] = v
            if hrvcol is not None and hrvcol < len(r):
                v = _num(r[hrvcol])
                if v and 0 < v <= 500:
                    rec["hrv"] = v
            if wtcol is not None and wtcol < len(r):
                v = _num(r[wtcol])
                if v and 20 <= v <= 300:
                    if "lb" in hdr[wtcol]:
                        v *= 0.453592
                    rec["weight_kg"] = v
    return data


def fmt_sleep(h):
    return f"{int(h)}h{round(h % 1 * 60):02}m"


def health_line(rec):
    parts = []
    if rec.get("sleep_h"):
        parts.append(f"sleep {fmt_sleep(rec['sleep_h'])}")
    if rec.get("workout_min"):
        parts.append(f"workout {round(rec['workout_min'])}m")
    if rec.get("mindful_min"):
        parts.append(f"mindful {round(rec['mindful_min'])}m")
    if rec.get("steps"):
        parts.append(f"{rec['steps']} steps")
    return f"({', '.join(parts)})" if parts else ""


# ---------------- calendar (.ics) busy-time import ----------------

def _merge_time_intervals(intervals):
    """Sort + merge overlapping/adjacent (start_time, end_time) tuples —
    the shared primitive both the hours-view and the slot-finder need,
    so two meetings double-booked at the same hour count as one busy
    hour, not two."""
    merged = []
    for s, e in sorted(intervals):
        if merged and s <= merged[-1][1]:
            if e > merged[-1][1]:
                merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


def _time_span_hours(s, e):
    return (dt.datetime.combine(dt.date.min, e)
            - dt.datetime.combine(dt.date.min, s)).total_seconds() / 3600


def _free_from_busy(win_start, win_end, busy):
    """Free (start, end) time ranges inside [win_start, win_end) once
    `busy` intervals are merged and subtracted — the pure core of
    _free_slots(), factored out so backlog #21's fragmentation-cost
    simulation can ask "what if this one meeting weren't there" as a
    plain function call, no live App/csv needed."""
    merged = _merge_time_intervals(busy)
    slots, cur = [], win_start
    for s, e in merged:
        if s > cur:
            slots.append((cur, min(s, win_end)))
        cur = max(cur, e)
        if cur >= win_end:
            break
    if cur < win_end:
        slots.append((cur, win_end))
    return [(s, e) for s, e in slots if s < e]


def _deep_capacity_minutes(slots, min_block=90):
    """Total minutes across free `slots` at least `min_block` minutes
    long — a 20-minute gap between meetings isn't capacity for deep
    work, it's just a gap."""
    return sum(round(_time_span_hours(s, e) * 60) for s, e in slots
              if _time_span_hours(s, e) * 60 >= min_block)


def _add_hours(t, hours):
    return (dt.datetime.combine(dt.date.min, t)
            + dt.timedelta(hours=hours)).time()


def day_length_hours(d, lat_deg):
    """Hours of daylight on date `d` at latitude `lat_deg` — a standard
    declination/hour-angle approximation (ignores atmospheric refraction
    and the equation of time, so it's accurate to a handful of minutes,
    not an ephemeris). Pure math: no network, no API key, no dependency —
    a source that's free to capture the moment a latitude is set, unlike
    every other health source which needs an export file to exist first.
    Clamped to [0, 24] for the polar day/night edge cases."""
    doy = d.timetuple().tm_yday
    decl = math.radians(-23.44) * math.cos(math.radians(360 / 365 * (doy + 10)))
    lat = math.radians(lat_deg)
    try:
        cos_h = -math.tan(lat) * math.tan(decl)
    except ValueError:
        return 12.0
    if cos_h <= -1:
        return 24.0     # polar day
    if cos_h >= 1:
        return 0.0       # polar night
    return 2 * math.degrees(math.acos(cos_h)) / 15


ICS_REFRESH_MIN = 60   # minutes between re-fetches of a subscribed .ics URL


def resolve_ics_source(raw, force=False):
    """Backlog #114: `raw` (settings["ics_path"]) can now be a local
    file (old behavior, unchanged) OR a calendar's own publish/
    subscribe link (webcal:// or http(s)://, e.g. Outlook/Google's
    "Publish calendar" URL) — closes the "manual export every time"
    gap without needing any login or API key. A URL gets fetched to a
    local cache file (data_dir()/calendar_cache.ics), refreshed when
    the cache is older than ICS_REFRESH_MIN minutes or `force`; a
    fetch failure (offline, link revoked) silently keeps serving
    whatever was cached last rather than going blank. Returns a local
    path either way — parse_ics_intervals/parse_ics_busy never need to
    know the difference."""
    if not raw:
        return raw
    if raw.lower().startswith("webcal://"):
        url = "https://" + raw[len("webcal://"):]
    else:
        url = raw
    if not url.lower().startswith(("http://", "https://")):
        return raw   # already a local file path
    cache_path = os.path.join(data_dir(), "calendar_cache.ics")
    stale = force or not os.path.exists(cache_path) or (
        (time.time() - os.path.getmtime(cache_path)) / 60 >= ICS_REFRESH_MIN)
    if stale:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = resp.read()
            with open(cache_path, "wb") as f:
                f.write(data)
        except (urllib.error.URLError, OSError, ValueError):
            pass   # keep serving the last good cache, if any
    return cache_path if os.path.exists(cache_path) else raw


def parse_ics_intervals(path, start, end):
    """{date_iso: [(start_time, end_time), ...]} from an exported .ics,
    window [start, end] — merged, sorted time-of-day ranges per day.
    This is the v8 scheduler's foundation piece: parse_ics_busy (below)
    used to be the only view of this data, a per-day SCALAR that can't
    say WHERE in the day you're free. Skips all-day events and
    recurring (RRULE) events — same known limitation as before, see
    HANDOFF's RRULE backlog item."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return {}
    text = text.replace("\r\n ", "").replace("\n ", "")   # unfold folds
    utc_off = dt.datetime.now().astimezone().utcoffset() or dt.timedelta()
    raw = {}
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
                raw.setdefault(iso, []).append((cur.time(), seg_end.time()))
            cur = seg_end
    return {iso: _merge_time_intervals(ivs) for iso, ivs in raw.items()}


def parse_ics_busy(path, start, end):
    """{date_iso: busy_hours} — a thin sum over parse_ics_intervals, kept
    as its own function since every existing capacity call site wants a
    scalar. Note: overlapping (double-booked) meetings now count once,
    not once per event — parse_ics_intervals merges before this sums, so
    a calendar with real overlaps will show slightly LESS busy time than
    before this change, which is the more honest number."""
    return {iso: sum(_time_span_hours(s, e) for s, e in ivs)
            for iso, ivs in parse_ics_intervals(path, start, end).items()}


def parse_ics_events(path, start, end):
    """Backlog #120: [(date, start_time, end_time, summary), ...] — the
    calendar-VIEW sibling of parse_ics_intervals. Capacity math
    (_busy_intervals) only needs merged, unlabeled time ranges; the
    week/month calendar views need to show WHAT'S on, so this keeps
    each event as its own labeled, unmerged entry instead. Same all-
    day/RRULE limitations as parse_ics_intervals (see #117) — a
    rendering source, not a second capacity model, so it deliberately
    shares those gaps rather than fixing them differently in two
    places."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return []
    text = text.replace("\r\n ", "").replace("\n ", "")
    utc_off = dt.datetime.now().astimezone().utcoffset() or dt.timedelta()
    out = []
    for block in text.split("BEGIN:VEVENT")[1:]:
        block = block.split("END:VEVENT")[0]
        if "RRULE:" in block:
            continue

        def field(name):
            m = re.search(rf"^{name}[^:\n]*:([^\s]+)", block, re.M)
            return m.group(1).strip() if m else None

        def parse(v):
            if v is None or len(v) <= 8:
                return None
            naive = dt.datetime.strptime(v[:15], "%Y%m%dT%H%M%S")
            return naive + utc_off if v.rstrip().endswith("Z") else naive

        sm = re.search(r"^SUMMARY[^:\n]*:(.+)$", block, re.M)
        summary = sm.group(1).strip() if sm else "(no title)"
        try:
            sdt, edt = parse(field("DTSTART")), parse(field("DTEND"))
        except ValueError:
            continue
        if not sdt or not edt or edt <= sdt:
            continue
        cur = sdt
        while cur < edt:
            nxt = dt.datetime.combine(cur.date() + dt.timedelta(days=1),
                                      dt.time())
            seg_end = min(edt, nxt)
            if start <= cur.date() <= end:
                out.append((cur.date(), cur.time(), seg_end.time(), summary))
            cur = seg_end
    return out


def parse_csv_busy_export(path, start, end):
    """Backlog #116: the fallback path for when Outlook won't publish a
    calendar link at all (common on locked-down school/work tenants —
    see #114's own limitation) but Power Automate's STANDARD Office
    365 Outlook connector still works, because it rides on the
    tenant's existing consent rather than a custom app registration.
    A no-code flow (recurring trigger -> "Get calendar view of
    events" -> "Create CSV table" -> "Create file" to a OneDrive-
    synced folder) can produce a plain CSV with Start/End[/Subject]
    columns; this reads it into the exact same {date_iso:
    [(start_time, end_time), ...]} shape parse_ics_intervals returns,
    so every existing capacity view (_free_slots, _lock_window_
    candidates, _capacity_lines...) works identically regardless of
    which source is configured. Lenient on datetime format (ISO 8601,
    with or without a timezone/Z suffix — Power Automate's own output
    is ISO)."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return {}
    raw = {}
    for r in rows:
        s_raw = (r.get("Start") or "").strip()
        e_raw = (r.get("End") or "").strip()
        if not s_raw or not e_raw:
            continue
        try:
            s_dt = dt.datetime.fromisoformat(s_raw.replace("Z", "+00:00"))
            e_dt = dt.datetime.fromisoformat(e_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if s_dt.tzinfo:
            s_dt = s_dt.astimezone().replace(tzinfo=None)
        if e_dt.tzinfo:
            e_dt = e_dt.astimezone().replace(tzinfo=None)
        d = s_dt.date()
        if not (start <= d <= end):
            continue
        raw.setdefault(d.isoformat(), []).append((s_dt.time(), e_dt.time()))
    return {iso: _merge_time_intervals(ivs) for iso, ivs in raw.items()}


def csv_busy_data(path, start, end):
    """{date_iso: busy_hours} — the CSV sibling of parse_ics_busy, same
    thin sum over parse_csv_busy_export."""
    return {iso: sum(_time_span_hours(s, e) for s, e in ivs)
            for iso, ivs in parse_csv_busy_export(path, start, end).items()}


def parse_csv_events(path, start, end):
    """Backlog #120: [(date, start_time, end_time, summary), ...] — the
    calendar-VIEW sibling of parse_csv_busy_export, same relationship
    parse_ics_events has to parse_ics_intervals. Reads an optional
    "Subject" column if present (Power Automate's own CSV export
    includes it if you mapped it — see the setup guide); falls back
    to a placeholder when it's missing rather than failing."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return []
    out = []
    for r in rows:
        s_raw = (r.get("Start") or "").strip()
        e_raw = (r.get("End") or "").strip()
        summary = (r.get("Subject") or "").strip() or "(no title)"
        if not s_raw or not e_raw:
            continue
        try:
            s_dt = dt.datetime.fromisoformat(s_raw.replace("Z", "+00:00"))
            e_dt = dt.datetime.fromisoformat(e_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if s_dt.tzinfo:
            s_dt = s_dt.astimezone().replace(tzinfo=None)
        if e_dt.tzinfo:
            e_dt = e_dt.astimezone().replace(tzinfo=None)
        d = s_dt.date()
        if not (start <= d <= end):
            continue
        out.append((d, s_dt.time(), e_dt.time(), summary))
    return out


# ---------------- old-format line builders ----------------

def hms_unpadded(secs):
    return f"{secs // 3600}:{secs % 3600 // 60}:{secs % 60}"


def hms_padded(secs):
    return f"{secs // 3600}:{secs % 3600 // 60:02}:{secs % 60:02}"


def event_line(kind, when, cum_secs):
    # Start;2026-06-02;13:43:42;0;20;1229  (h ; total min ; total sec)
    return (f"{kind};{when:%Y-%m-%d};{when:%H:%M:%S};"
            f"{cum_secs // 3600};{cum_secs // 60};{cum_secs}")


_EVENT_RE = re.compile(r"^(Start|Stop|Reset);(\d{4}-\d\d-\d\d);(\d\d:\d\d:\d\d);")
_TASK_LINE_RE = re.compile(r"^--- Task: (.+?)(?:\s*\[time-box \d+m\])?\s*$")


def parse_day_file_to_rows(text, date_iso):
    """Reconstruct work/break sessions.csv rows purely from a day file's
    own event lines — the exact inverse of event_line(). The day file is
    the source of truth (the sacred rule); this makes the csv provably
    re-derivable from it, never the only place the log survives. Uses
    each event's own embedded date+time to compute interval length (a
    session that runs past real midnight writes a Stop line dated the
    NEXT calendar day even though it's still this effective day's file —
    the day only rolls at the configurable rollover hour, not midnight;
    every row is still filed under `date_iso`, the file it came from, not
    the possibly-later calendar date on an individual line). A
    '--- Task:' line sets the task name for every work interval until
    the next one."""
    rows, task = [], ""
    pending_start = pending_stop = None   # full datetimes, not just times

    for ln in text.splitlines():
        s = ln.strip()
        m = _TASK_LINE_RE.match(s)
        if m:
            task = m.group(1).strip()
            continue
        m = _EVENT_RE.match(s)
        if not m:
            continue
        kind, d, hms = m.groups()
        h, mi, se = (int(x) for x in hms.split(":"))
        when = dt.datetime.combine(dt.date.fromisoformat(d), dt.time(h, mi, se))
        if kind == "Start":
            if pending_stop is not None:
                secs = (when - pending_stop).total_seconds()
                if 0 <= secs and secs >= MIN_LOG_SECS:
                    rows.append([date_iso, "break", pending_stop.strftime("%H:%M"),
                                when.strftime("%H:%M"), max(1, round(secs / 60)), "", ""])
                pending_stop = None
            pending_start = when
        else:   # Stop or Reset both close an open work interval
            if pending_start is not None:
                secs = (when - pending_start).total_seconds()
                if 0 <= secs and secs >= MIN_LOG_SECS:
                    rows.append([date_iso, "work", pending_start.strftime("%H:%M"),
                                when.strftime("%H:%M"), max(1, round(secs / 60)), task, ""])
                pending_start = None
            pending_stop = when if kind == "Stop" else None
    return rows


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


def is_locked():
    """Best-effort Windows workstation-lock detector — the
    OpenInputDesktop trick: the call fails (returns a NULL handle)
    when the interactive desktop isn't reachable, which is exactly
    what happens while the workstation is locked (or a secure desktop
    like a UAC prompt is up). stdlib ctypes only, no pywin32. Fail-open
    like idle_seconds() (any error -> "not locked") so a detection
    glitch never blocks normal tracking — this is a well-known
    community technique, not something this Linux dev environment can
    verify against a live Windows session, so confirm it actually
    fires on your machine before relying on it."""
    try:
        h = ctypes.windll.user32.OpenInputDesktop(0, False, 0)
        if h:
            ctypes.windll.user32.CloseDesktop(h)
            return False
        return True
    except Exception:
        return False


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


def lock_windows_to_ics(dl_name, windows):
    """Backlog #113: the export half — chosen study/work blocks for a
    deadline written as real calendar events, same flat-file shape as
    week_to_ics (stdlib-only, one .ics the owner imports into Outlook/
    Google Calendar by hand). `windows` is
    [{"date": date, "start": time, "end": time}, ...]."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{APP_NAME}//EN"]
    for i, w in enumerate(windows):
        start = dt.datetime.combine(w["date"], w["start"])
        end = dt.datetime.combine(w["date"], w["end"])
        lines += ["BEGIN:VEVENT",
                  f"UID:timerdiary-lock-{w['date'].isoformat()}-{i}@local",
                  f"DTSTART:{start:%Y%m%dT%H%M%S}",
                  f"DTEND:{end:%Y%m%dT%H%M%S}",
                  f"SUMMARY:Locked: {dl_name}",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", dl_name)
    path = os.path.join(data_dir(), f"TimerDiary_lock_{safe}.ics")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path, len(windows)


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
        self.lock_since = None         # datetime when the workstation locked
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
        self._backfill_task_library()
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
    def _kws_from_text(text, prefix="signal:"):
        """Comma-separated keywords from the first line starting with
        `prefix` (case-insensitive), lowered. SIGNAL and AVOID are the
        same lens shape read from two different header lines — one
        parser, one prefix argument, not two near-identical functions."""
        plen = len(prefix)
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith(prefix):
                return [k.strip().lower() for k in s[plen:].split(",") if k.strip()]
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

    # ----- tier-2 signal (backlog #96): a second, DISCRETE priority tier,
    # not a blend — see "Signal vs. maintenance" in the design rules above.
    # SIGNAL keeps meaning exactly what it always meant (today's ONE
    # sharpest priority, untouched); SIGNAL2 is a separate, second-place
    # bucket that never dilutes the first. -----

    def _signal2_kws(self, day=None):
        if day is None or day == self.today:
            return self._kws_from_text(self.diary.get("1.0", "end-1c"), "signal2:")
        try:
            with open(self.diary_path(day), encoding="utf-8") as f:
                return self._kws_from_text(f.read(), "signal2:")
        except OSError:
            return []

    def _day_signal2(self, day, kws=None, kws1=None, rows=None):
        """(tier2_min, work_min) for one day given its SIGNAL2 keywords.
        Disjoint from tier-1 on purpose: a task matching BOTH SIGNAL and
        SIGNAL2 counts as tier-1 only — the sharpest priority wins the
        tie, so the two buckets never double-count the same minute and
        tier-1's own number is never diluted by this feature existing."""
        if kws is None:
            kws = self._signal2_kws(day)
        if kws1 is None:
            kws1 = self._signal_kws(day)
        sig2 = work = 0
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
                if self._is_signal(r[5], kws) and not (
                        kws1 and self._is_signal(r[5], kws1)):
                    sig2 += m
        return sig2, work

    def _carry_signal2(self):
        """Yesterday's SIGNAL2 line text, or '' — same standing-
        declaration carry shape as AVOID, no goal-seeded fallback
        (tier-2 is optional context, not the headline metric SIGNAL is,
        so there's nothing honest to seed it with when it's never been
        used)."""
        try:
            with open(self.diary_path(self.today - dt.timedelta(days=1)),
                      encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.lower().startswith("signal2:"):
                        return s[8:].strip()
        except OSError:
            pass
        return ""

    # ----- avoid meter (the inverse lens: what you're trying to shed) -----

    def _avoid_kws(self, day=None):
        if day is None or day == self.today:
            return self._kws_from_text(self.diary.get("1.0", "end-1c"), "avoid:")
        try:
            with open(self.diary_path(day), encoding="utf-8") as f:
                return self._kws_from_text(f.read(), "avoid:")
        except OSError:
            return []

    def _day_avoid(self, day, kws=None, rows=None):
        """(avoid_min, work_min) for one day given its AVOID keywords —
        the exact mirror of _day_signal, same lens primitive."""
        if kws is None:
            kws = self._avoid_kws(day)
        av = work = 0
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
                if task_matches(r[5], kws):
                    av += m
        return av, work

    def _carry_avoid(self):
        """Yesterday's AVOID line text (original case), or '' — unlike
        SIGNAL, no goal-seeded fallback: AVOID is a standing declaration,
        not a daily pick, so it only carries what you actually wrote."""
        try:
            with open(self.diary_path(self.today - dt.timedelta(days=1)),
                      encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.lower().startswith("avoid:"):
                        return s[6:].strip()
        except OSError:
            pass
        return ""

    def _line_usage_count(self, prefix, days=60):
        """How many of the last `days` days actually had something
        typed after `prefix:`? The counting core behind
        _line_ever_used (bool) and #106's adoption panel (the count
        itself) — one file-scanning loop, two views on the same
        question."""
        lower = prefix.lower() + ":"
        n = 0
        d = self.today - dt.timedelta(days=1)
        end = self.today - dt.timedelta(days=days)
        while d >= end:
            try:
                with open(self.diary_path(d), encoding="utf-8") as f:
                    for line in f:
                        s = line.strip()
                        if s.lower().startswith(lower) and s[len(lower):].strip():
                            n += 1
                            break
            except OSError:
                pass
            d -= dt.timedelta(days=1)
        return n

    def _line_ever_used(self, prefix, days=60):
        """Has the owner ever actually typed something after
        `prefix:` in the last `days` days? The morning header used to
        print AVOID/YEAR/METRICS unconditionally, even for someone who
        has never once used them — three blank lines of pure noise
        every single day (owner feedback, 2026-07-29: "huge txt
        wall... not easily eye-able"). These now only show once
        they're actually in use, or currently carrying a real value —
        cutting real, measured noise for anyone who hasn't adopted
        that axis. SIGNAL/ENERGY stay unconditional; those are the
        original, sacred pair."""
        return self._line_usage_count(prefix, days) > 0

    _HEADER_LINE_PREFIXES = ("SIGNAL", "SIGNAL2", "AVOID", "YEAR", "ENERGY",
                             "METRICS", "WORKBLOCK", "TODAY", "DECIDED",
                             "CAPSULE", "COMMIT", "EXPERIMENT")

    def _header_line_adoption_lines(self, days=60):
        """Backlog #106: a different surface than #56's usage meter
        (that counts View-menu COMMAND clicks) — this reports which of
        the ~12 optional header-LINE conventions are actually adopted
        vs set once and forgotten, reusing _line_usage_count as-is.
        Read-only, no new data, no nagging — just the table."""
        counts = {p: self._line_usage_count(p, days)
                 for p in self._HEADER_LINE_PREFIXES}
        used = {p: n for p, n in counts.items() if n}
        lines = [f"Header-line usage (last {days} days):"]
        if not used:
            lines.append("  nothing typed yet beyond SIGNAL/ENERGY — see "
                         "Tools > Quick reference for what each line is for")
            return lines
        for p, n in sorted(used.items(), key=lambda x: -x[1]):
            lines.append(f"  {p + ':':<11} used {n} of last {days} days")
        unused = [p for p in self._HEADER_LINE_PREFIXES if p not in used]
        if unused:
            lines.append(f"  never used: {', '.join(unused)}")
        return lines

    # ----- declared work-block window (backlog #100, first half): a
    # 9-5 day job or similar external commitment is already spoken for —
    # idle/lock detection can afford to be far less trigger-happy about
    # a quick meeting or email check inside it. The opposite of #50's
    # protected windows (those say "never book here"; this says "don't
    # treat a short pause here as a break"). -----

    _WORKBLOCK_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$")
    _WORKBLOCK_IDLE_FACTOR = 3   # inside a declared work block, idle/lock
                                  # detection waits this many times longer
                                  # before offering to log a break

    def _workblock_window(self, day=None):
        """Today's declared WORKBLOCK: HH:MM-HH:MM window as (start, end)
        times, or None. Same day-aware read pattern as _signal_kws/
        _avoid_kws — live buffer for today, a file read for a past day."""
        if day is None or day == self.today:
            text = self.diary.get("1.0", "end-1c")
        else:
            try:
                with open(self.diary_path(day), encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                return None
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("workblock:"):
                m = self._WORKBLOCK_RE.match(s[10:])
                if not m:
                    return None
                sh, sm, eh, em = map(int, m.groups())
                try:
                    return dt.time(sh, sm), dt.time(eh, em)
                except ValueError:
                    return None
        return None

    def _in_workblock(self, when=None):
        win = self._workblock_window()
        if not win:
            return False
        s, e = win
        if s > e:
            return False              # malformed (crosses midnight) — skip, don't guess
        return s <= (when or dt.datetime.now()).time() <= e

    def _carry_workblock(self):
        """Yesterday's WORKBLOCK line text, or '' — same standing-
        declaration carry shape as AVOID (a fixed schedule doesn't need
        re-typing every morning)."""
        try:
            with open(self.diary_path(self.today - dt.timedelta(days=1)),
                      encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.lower().startswith("workblock:"):
                        return s[10:].strip()
        except OSError:
            pass
        return ""

    def _carry_year(self):
        """Backlog #64: yesterday's YEAR: line text (original case), or
        '' — the year-scale sibling of SIGNAL/AVOID: a standing
        declaration one size up, same carry-forward shape as AVOID
        (v8.13). Set once, edited whenever the theme genuinely
        changes, silently carried into every day after that."""
        try:
            with open(self.diary_path(self.today - dt.timedelta(days=1)),
                      encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.lower().startswith("year:"):
                        return s[5:].strip()
        except OSError:
            pass
        return ""

    def _declared_cap_h(self, day):
        """Backlog #37: an honest 'TODAY: 4h' (or 'TODAY: sick', no
        number) typed into `day`'s own file — compassionate realism for
        a travel/sick/short day, declared in advance rather than judged
        after the fact. Returns the declared hour cap if a number was
        given, 0.0 if declared with no number (any tracked time at all
        counts), or None if no TODAY: line exists. Read-only."""
        try:
            with open(self.diary_path(day), encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return None
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("today:"):
                m = re.search(r"(\d+(?:\.\d+)?)\s*h", s[6:], re.I)
                return float(m.group(1)) if m else 0.0
        return None

    def _avoid_trend_suffix(self, yday):
        """', avoid Y%' (+ a quiet week-over-week arrow) appended to the
        yesterday-summary line — AVOID reported right next to SIGNAL,
        completing the lens family symmetrically. Arrow only appears with
        2+ active days in both this week (Mon-yesterday) and all of last
        week, and only when the move is >=3 points either way — silent
        otherwise, same honesty gate as every other trend line here."""
        kws = self._avoid_kws(yday)
        if not kws:
            return ""
        aday, wday = self._day_avoid(yday, kws)
        if wday <= 0:
            return ""
        pct = round(100 * aday / wday)
        suffix = f", avoid {pct}%"
        mon = yday - dt.timedelta(days=yday.weekday())
        prev_mon = mon - dt.timedelta(days=7)
        idx = day_index()

        def share(lo, hi):
            av = wk = 0
            active = 0
            d = lo
            while d <= hi:
                rec = idx.get(d.isoformat())
                if rec and rec["work"] > 0:
                    a, w = self._day_avoid(d, kws)
                    av += a
                    wk += w
                    active += 1
                d += dt.timedelta(days=1)
            return (100 * av / wk, active) if wk > 0 else (None, active)

        cur, cur_active = share(mon, yday)
        prev, prev_active = share(prev_mon, mon - dt.timedelta(days=1))
        if cur is not None and prev is not None and cur_active >= 2 and prev_active >= 2:
            if cur <= prev - 3:
                suffix += " ↓"
            elif cur >= prev + 3:
                suffix += " ↑"
        return suffix

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

    # ----- commitment-reliability ledger (backlog #18) -----
    #
    # A COMMIT: line is opt-in (same convention as EXPERIMENT/DECIDED —
    # never auto-inserted, typed only when the owner wants to make a
    # morning promise to themselves): "COMMIT: thesis 4h" commits to 4h
    # on tasks matching "thesis"; "COMMIT: 4h" (no keywords) commits to
    # 4h of tracked work overall. The ledger never grades any ONE day —
    # only the trailing rate, read back once a week, self-calibration
    # feedback rather than a promise-tracking gate.

    _COMMIT_RE = re.compile(r"^COMMIT:\s*(.*?)\s*([0-9.]+)\s*h\s*$", re.I)

    def _commit_from_text(self, text):
        """First COMMIT: line's (keyword-spec, hours), or None — same
        first-match-wins template as _energy_from_text."""
        for line in text.splitlines():
            m = self._COMMIT_RE.match(line.strip())
            if m:
                try:
                    return m.group(1).strip(), float(m.group(2))
                except ValueError:
                    continue
        return None

    def _commitment_reliability(self, days=30):
        """Backlog #18: for each of the last `days` days with a real
        COMMIT: line, whether that day's delivered hours (matched to
        the commitment's own keywords, or the day's whole tracked
        total when none were given) met or exceeded what was
        committed. Returns (hit_rate, hits, n), or None until 5+ real
        commitments exist — the honesty gate every stat here uses."""
        idx = day_index()
        hits = n = 0
        for i in range(1, days + 1):
            d = self.today - dt.timedelta(days=i)
            try:
                with open(self.diary_path(d), encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                continue
            commit = self._commit_from_text(text)
            if not commit:
                continue
            kws_str, hours = commit
            kws = self._match_kws(kws_str)
            if kws:
                delivered = matched_minutes(kws, d, d) / 60
            else:
                delivered = (idx.get(d.isoformat()) or {"work": 0})["work"] / 60
            n += 1
            if delivered + 1e-9 >= hours:
                hits += 1
        if n < 5:
            return None
        return hits / n, hits, n

    def _commitment_reliability_line(self, days=30):
        stat = self._commitment_reliability(days)
        if not stat:
            return None
        rate, hits, n = stat
        return (f"  you hit your morning commitment {hits} of the last "
               f"{n} day(s) — you reliably deliver ~{round(100 * rate)}% "
               "of what you promise yourself; promise that and mean it")

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

    def _tracked(self, key, fn):
        """Backlog #56: wraps a menu command to bump a usage counter
        before calling it, unchanged otherwise — the tool auditing its
        OWN use, not the owner's life. Visibility into which of the
        built features actually get opened; no judgment, no auto-
        pruning, informs future graveyard-sweep-style decisions by
        hand (see Tools > Feature usage)."""
        def wrapped(*a, **kw):
            counts = self.settings.setdefault("usage_counts", {})
            counts[key] = counts.get(key, 0) + 1
            save_settings(self.settings)
            return fn(*a, **kw)
        return wrapped

    def _usage_win(self):
        win = tk.Toplevel(self)
        win.title("Feature usage")
        txt = self._scrolled_text(win)
        counts = self.settings.get("usage_counts", {})
        if not counts:
            txt.insert("end", "Nothing tracked yet — open a few views first.")
        else:
            for key, n in sorted(counts.items(), key=lambda x: -x[1]):
                txt.insert("end", f"{key:<28} {n}\n")
        txt.config(state="disabled")

    def _build_menu(self):
        m = tk.Menu(self)
        filem = tk.Menu(m, tearoff=0)
        filem.add_command(label="Add past session…", command=self._add_past_session)
        filem.add_command(label="Open a day file…", command=self._quick_day_nav)
        filem.add_command(label="Browse for a day file (file picker)…",
                          command=self._open_day_file)
        filem.add_command(label="Export week to calendar (.ics)", command=self._export_ics)
        filem.add_command(label="Lock study windows (.ics)…",
                          command=self._lock_windows_win)
        filem.add_command(label="Export life record (JSON)…",
                          command=self._export_life_json)
        filem.add_command(label="Import life record (JSON)…",
                          command=self._import_life_json)
        filem.add_separator()
        filem.add_command(label="Open data folder", command=self._open_folder)
        filem.add_command(label="Change diary folder…", command=self._change_diary_dir)
        filem.add_command(label="Health import folder…", command=self._set_health_dir)
        filem.add_command(label="Calendar busy-time (.ics)…", command=self._set_ics)
        filem.add_command(label="Subscribe to a calendar link (.ics URL)…",
                          command=self._set_ics_url)
        filem.add_command(label="Import calendar CSV (Power Automate export)…",
                          command=self._set_csv_busy)
        filem.add_separator()
        filem.add_command(label="Exit", command=self._on_close)
        m.add_cascade(label="File", menu=filem)

        # Grouped by the NORTH STAR's own three pillars (see HANDOFF.md)
        # plus a couple of practical extras — the menu should read as
        # the architecture, not as a flat 22-year-old junk drawer.
        viewm = tk.Menu(m, tearoff=0)
        viewm.add_command(label="Life dashboard", accelerator="Ctrl+D",
                          command=self._tracked("Dashboard", self._dashboard))
        viewm.add_command(label="What should I do now?",
                          command=self._tracked("Recommend now", self._show_recommend_now))
        viewm.add_command(label="Tasks / backlog…",
                          command=self._tracked("Tasks/backlog", self._tasks_win))
        viewm.add_separator()

        planm = tk.Menu(viewm, tearoff=0)
        planm.add_command(label="Free-time forecast (calendar)…",
                          command=self._tracked("Free-time forecast", self._forecast_win))
        planm.add_command(label="Calendar (week/month)…",
                          command=self._tracked("Calendar view", self._calendar_view_win))
        planm.add_command(label="Week plan / capacity…",
                          command=self._tracked("Capacity planner", self._capacity_win))
        planm.add_command(label="Outlook — weeks ahead…",
                          command=self._tracked("Outlook", self._outlook_win))
        planm.add_command(label="Deadline burn-down",
                          command=self._tracked("Burn-down", self._burndown))
        viewm.add_cascade(label="Planning  (foresight)", menu=planm)

        memm = tk.Menu(viewm, tearoff=0)
        memm.add_command(label="Trend (8 weeks)",
                         command=self._tracked("Trend", self._trend))
        memm.add_command(label="Month heatmap",
                         command=self._tracked("Heatmap", self._heatmap))
        memm.add_command(label="Year rhythm map",
                         command=self._tracked("Year rhythm", self._year_rhythm_view))
        memm.add_command(label="Search all days…",
                         command=self._tracked("Search", self._search_diary))
        memm.add_command(label="Decision log…",
                         command=self._tracked("Decision log", self._decision_log_view))
        viewm.add_cascade(label="Memory  (the archive)", menu=memm)

        valm = tk.Menu(viewm, tearoff=0)
        valm.add_command(label="Life alignment — time vs values…",
                         command=self._tracked("Life alignment", self._alignment_win))
        valm.add_command(label="Life review — synthesized briefing…",
                         command=self._tracked("Life review", self._life_review_win))
        valm.add_command(label="Lens overlap check…",
                         command=self._tracked("Lens overlap", self._lens_overlap_win))
        viewm.add_cascade(label="Values  (alignment)", menu=valm)

        writm = tk.Menu(viewm, tearoff=0)
        writm.add_command(label="Themed writing…", accelerator="Ctrl+T",
                          command=self._tracked("Themed writing", self._themed_writing))
        writm.add_command(label="Browse themes…",
                          command=self._tracked("Browse themes", self._browse_themes))
        viewm.add_cascade(label="Writing", menu=writm)

        viewm.add_command(label="Health × focus (14 days)",
                          command=self._tracked("Health x focus", self._health_view))
        viewm.add_separator()

        repm = tk.Menu(viewm, tearoff=0)
        repm.add_command(label="Weekly summary",
                         command=self._tracked("Weekly summary", lambda: self._summary("week")))
        repm.add_command(label="Monthly summary",
                         command=self._tracked("Monthly summary", lambda: self._summary("month")))
        repm.add_command(label="Copy week for AI review",
                         command=self._tracked("Copy week AI",
                                               lambda: self._copy_review("week")))
        repm.add_command(label="Copy today for AI review",
                         command=self._tracked("Copy day AI",
                                               lambda: self._copy_review("day")))
        viewm.add_cascade(label="Reports", menu=repm)

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
        self.hide_raw_var = tk.BooleanVar(
            value=self.settings.get("hide_raw_lines", False))
        toolsm.add_checkbutton(label="Hide raw timer lines in the diary",
                               variable=self.hide_raw_var,
                               command=self._toggle_raw_lines)
        toolsm.add_command(label="Meeting mode (idle off 90 min)",
                           command=self._meeting_mode)
        toolsm.add_command(label="Feature usage…", command=self._usage_win)
        toolsm.add_command(label="Quick reference — what does this app do?…",
                           command=self._help_win)
        toolsm.add_separator()
        toolsm.add_command(label="Data doctor — check & clean history…",
                           command=self._data_doctor)
        toolsm.add_command(label="Rebuild sessions.csv from day files…",
                           command=self._rebuild_csv_from_diary)
        toolsm.add_separator()
        toolsm.add_command(label="Global hotkey…", command=self._set_hotkey)
        toolsm.add_command(label="Deadline countdown…", command=self._set_deadline)
        toolsm.add_command(label="Goals — the why layer…", command=self._set_goals)
        toolsm.add_command(label="Life domains — the values layer…",
                           command=self._set_domains)
        toolsm.add_command(label="Daylight location (latitude)…",
                           command=self._set_daylight_lat)
        toolsm.add_command(label="Idle detection…", command=self._set_idle)
        toolsm.add_command(label="Break pull-back (signal tasks)…",
                           command=self._set_pull)
        toolsm.add_command(label="Day rollover hour…", command=self._set_rollover)
        toolsm.add_command(label="Daily target…", command=self._set_target)
        toolsm.add_command(label="Work-day window (free-slot finder)…",
                           command=self._set_work_window)
        toolsm.add_command(label="Recurring commitments (lunch, day job, sleep, admin)…",
                           command=self._set_protected_windows)
        m.add_cascade(label="Tools", menu=toolsm)

        self.menu = m
        self.config(menu=m)

    def _save_prefs(self):
        self.settings["nudge"] = self.nudge_var.get()
        self.settings["float_break"] = self.float_var.get()
        save_settings(self.settings)

    def _toggle_raw_lines(self):
        """Folds the Start;/Stop;/Reset; bookkeeping lines out of view —
        elide hides them from Tk's rendering, the file on disk and the
        widget's own buffer are untouched, so this is purely a reading
        aid, reversible any time, never a risk to the sacred day file."""
        hide = self.hide_raw_var.get()
        self.diary.tag_configure("raw_event", elide=hide)
        self.settings["hide_raw_lines"] = hide
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
                "Total h (opt)", "h/week (opt)", "Tasks containing",
                "Goal (opt)", "Milestones (opt, 'ch4 [15h]*, ch5 [20h]')")
        keys = ("name", "start", "date", "total_h", "target_h", "match",
               "goal", "milestones")
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
                    e = ttk.Entry(win, width=24 if key == "milestones"
                                  else 13 if c in (0, 5) else 10)
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
                            "goal": vals["goal"] or None,
                            "milestones": vals["milestones"]})
            out = _deadline_revisions_after_save(
                cur, out, dt.date.today().isoformat())
            self.settings["deadlines"] = out
            self.settings["dl_name"] = ""      # retire the legacy single form
            save_settings(self.settings)
            self._refresh_totals()
            win.destroy()

        preview_lbl = ttk.Label(win, text="", foreground="#2e6da4",
                                wraplength=760, justify="left")
        preview_lbl.grid(row=6, column=0, columnspan=8, sticky="w",
                         padx=4, pady=(0, 4))

        def update_preview(_event=None):
            """Backlog #52: live "cost of yes" — as soon as a NEW row
            (a name not already in the saved list) has a real date and
            total_h, preview what committing to it would do to slack,
            against the saved deadlines as the baseline. Editing an
            EXISTING deadline in place is intentionally not previewed
            here — ambiguous whether that's new scope or a correction,
            and the renegotiation tracker (v8.51) already covers that
            case on save."""
            cur_names = {d["name"] for d in cur}
            for row in grid:
                name = row[0].get().strip()
                date_s = row[2].get().strip()
                total_s = row[3].get().strip()
                if name and name not in cur_names and date_s and total_s:
                    try:
                        dt.date.fromisoformat(date_s)
                        total = float(total_s)
                    except ValueError:
                        continue
                    line = self._cost_of_yes_line(
                        {"name": name, "date": date_s, "total_h": total,
                         "goal": row[6].get() or None},
                        existing=cur)
                    preview_lbl.config(text=line or "")
                    return
            preview_lbl.config(text="")

        for row in grid:
            row[2].bind("<KeyRelease>", update_preview)   # date
            row[3].bind("<KeyRelease>", update_preview)   # total_h

        ttk.Button(win, text="Save", command=save).grid(
            row=5, column=7, sticky="e", padx=4, pady=8)

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

    def _lifetime_ledger_line(self, name, kws, start_iso=None):
        """Backlog #45: the un-windowed view. Every other lens is
        windowed — 8 weeks (alignment/trajectory), a deadline's own
        scope (burn-down), a calendar year (#15) — nothing answers "how
        much of my life has this actually taken, total." `start_iso`
        (a deadline's own stored start, if any) anchors the window;
        goals have no such field yet, so absent means "since the
        first-ever matching row in the csv" — the true lifetime, not
        an arbitrary one. Needs row-level granularity for the session
        count, so it's its own scan, not matched_minutes() itself
        (which only returns a total)."""
        if not kws:
            return None
        total = sessions = 0
        earliest = None
        for r in read_rows():
            if r[1] == "break" or not task_matches(r[5], kws):
                continue
            if start_iso and r[0] < start_iso:
                continue
            try:
                m = int(r[4])
            except ValueError:
                continue
            total += m
            sessions += 1
            if earliest is None or r[0] < earliest:
                earliest = r[0]
        if not sessions:
            return None
        since = start_iso or earliest
        days = max((self.today - dt.date.fromisoformat(since)).days, 1)
        avg = (total / 60) / days
        return (f"{name}: {total // 60}h across {sessions} session(s) "
               f"since {since} ({days} days — {avg:.1f}h/day lifetime "
               "average)")

    def _deadline_renegotiation_line(self, dl):
        """Backlog #46: once a deadline has been edited 2+ times (its
        own `history`, appended by `_deadline_revisions_after_save` on
        every edit), one honest line stating the drift pattern — no
        judgment beyond the numbers, that's entirely the point.
        Different from #28's post-mortem (fires once, after the
        deadline resolves): this is a LIVE, ongoing check, catching
        genuine re-scoping vs repeatedly deferring the same
        discomfort."""
        hist = dl.get("history") or []
        if len(hist) < 2:
            return None
        first = hist[0]
        try:
            first_date = dt.date.fromisoformat(first["date"])
            cur_date = dt.date.fromisoformat(dl["date"])
        except (ValueError, KeyError, TypeError):
            return None
        first_total = float(first.get("total_h") or 0)
        cur_total = float(dl.get("total_h") or 0)
        date_delta = (cur_date - first_date).days
        since = first.get("as_of") or first["date"]
        line = f"this deadline has moved {len(hist)} time(s) since {since}"
        extra = []
        if date_delta:
            extra.append(f"due date is now {abs(date_delta)}d "
                        f"{'later' if date_delta > 0 else 'earlier'} "
                        "than first set")
        if first_total != cur_total:
            extra.append(f"scope {'grew' if cur_total > first_total else 'shrank'}"
                        f" from {first_total:g}h to {cur_total:g}h")
        if extra:
            line += " — " + ", ".join(extra)
        return line

    def _milestone_progress_line(self, dl):
        """Backlog #36: total_h measures effort, not progress — 30h
        logged on a 60h scope can be 70% done or 20% done depending on
        WHAT got done. When a deadline has a milestone breakdown
        (`_parse_milestones`), speak in content instead: "ch4 done,
        ch5 at 60% of its hours." Hours accrue in milestone order — the
        current (first not-done) milestone gets credit for whatever
        matched hours haven't already been claimed by earlier, DONE
        milestones; later not-done milestones stay at 0% until the
        ones ahead of them are checked off. A proxy, not a real per-
        milestone tracker (there's no mechanism to tag which tracked
        minutes belong to which milestone) — but an honest one, since
        it never claims more than the deadline's own real total."""
        parts = self._milestone_credit(dl)
        if not parts:
            return None
        return "  milestones: " + ", ".join(parts["text"])

    def _milestone_credit(self, dl):
        """The shared credit computation behind _milestone_progress_line
        (internal, blunt register) and #83's status-export phrasing
        (external register) — one pass over the milestone list, two
        renderings. Returns None when there's no breakdown; otherwise
        {"text": [...], "current": (name, pct) or None if every
        milestone is already done}."""
        milestones = _parse_milestones(dl.get("milestones", ""))
        if not milestones:
            return None
        kws = self._match_kws(dl.get("match", ""))
        start = None
        if dl.get("start"):
            try:
                start = dt.date.fromisoformat(dl["start"])
            except ValueError:
                pass
        lo = start or dt.date.min
        if kws:
            done_total_h = matched_minutes(kws, lo, self.today) / 60
        else:
            idx = day_index()
            lo_iso, hi_iso = lo.isoformat(), self.today.isoformat()
            done_total_h = sum(rec["work"] for iso, rec in idx.items()
                              if lo_iso <= iso <= hi_iso) / 60
        cum_declared, text, current = 0.0, [], None
        for m in milestones:
            if m["done"]:
                text.append(f"{m['name']} done")
            else:
                credit = max(0.0, done_total_h - cum_declared)
                pct = min(100, round(100 * credit / m["h"])) if m["h"] else 0
                text.append(f"{m['name']} at {pct}% of its hours")
                if current is None:
                    current = (m["name"], pct)
            cum_declared += m["h"]
        return {"text": text, "current": current}

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

    # ----- life domains (the values layer ABOVE goals) -----
    #
    # A goal answers "why this project"; a DOMAIN answers "why the projects
    # at all" — the handful of life areas your time is supposed to serve
    # (Work, Body, Growth, People, Rest...). Same keyword-lens shape as
    # goals/deadlines (matched_minutes), one level up: the top of the
    # source -> lens -> view stack. The alignment view is the platform's
    # real question in one place — is your time actually flowing where you
    # say it should? — turning a time tracker into life management.

    def domains(self):
        return self.settings.get("domains") or []

    def _domain_minutes(self, dom, lo, hi):
        return matched_minutes(self._match_kws(dom.get("match")), lo, hi)

    # ----- lens overlap check (the honesty layer auditing itself) -----
    #
    # Backlog #48. Every honesty-gated % this app prints (alignment
    # shares, signal%, goal minutes) assumes the declared lenses are
    # DISJOINT — nothing has ever verified that assumption. A copy-paste
    # keyword accident between two goals silently double-counts an hour
    # toward two different percentages, forever, with no one the wiser.

    def _lens_registry(self):
        """Every declared keyword lens as (category, name, keywords).
        Deadlines with an empty match ('count all work') are excluded —
        overlap with 'everything' isn't an actionable finding."""
        out = []
        for g in self.goals():
            kws = self._match_kws(g.get("match"))
            if kws:
                out.append(("goal", g["name"], kws))
        for dom in self.domains():
            kws = self._match_kws(dom.get("match"))
            if kws:
                out.append(("domain", dom["name"], kws))
        for dl in self.deadlines():
            kws = self._match_kws(dl.get("match"))
            if kws:
                out.append(("deadline", dl["name"], kws))
        return out

    def _lens_overlap_lines(self, days=30):
        """Checks every PAIR of declared lenses for REAL double-counted
        minutes in the last `days` — not just a coincidental keyword-
        string collision that never actually fired on a real task name
        (the more useful check the backlog called for: two different
        keywords can each independently match the same task, e.g. 'run'
        and 'training' both matching 'morning run training', with no
        shared keyword string at all). Only pairs with real overlapping
        time are reported; a keyword string match is cosmetic detail on
        top of that, not the gate itself."""
        reg = self._lens_registry()
        if len(reg) < 2:
            return []
        idx = day_index()
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        recent = {iso: rec for iso, rec in idx.items() if iso >= cutoff}
        out = []
        for i in range(len(reg)):
            cat_a, name_a, kws_a = reg[i]
            for j in range(i + 1, len(reg)):
                cat_b, name_b, kws_b = reg[j]
                if cat_a == cat_b and name_a == name_b:
                    continue
                double_min = 0
                for rec in recent.values():
                    for t, m in rec["tasks"].items():
                        if task_matches(t, kws_a) and task_matches(t, kws_b):
                            double_min += m
                if double_min <= 0:
                    continue
                shared = set(kws_a) & set(kws_b)
                what = f"'{next(iter(shared))}'" if shared else "overlapping keywords"
                out.append((double_min, f"{what} matches both {name_a} "
                           f"({cat_a}) and {name_b} ({cat_b}) — "
                           f"{double_min / 60:.1f}h counted toward both "
                           f"in the last {days}d"))
        out.sort(key=lambda x: -x[0])
        return [line for _m, line in out[:5]]

    def _lens_overlap_win(self):
        win = tk.Toplevel(self)
        win.title("Lens overlap check — the honesty layer auditing itself")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10),
                      width=86, height=18)
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        lines = self._lens_overlap_lines()
        if not lines:
            lines = ["No overlap found — every declared SIGNAL/AVOID/"
                    "goal/domain/deadline keyword lens matched disjoint "
                    "tasks over the last 30 days. Every % this app has "
                    "printed from them is honest.",
                    "",
                    "(Checks goals, domains and scoped deadlines against "
                    "each other; re-run any time you add or edit one.)"]
        txt.insert("1.0", "\n".join(lines))
        txt.config(state="disabled")

    def _alignment_lines(self, weeks=8):
        """Where your tracked time actually went, by life domain, over the
        last `weeks` weeks — vs the share you SAID each should get. Names
        the widest say-do gap. Pure view over the lens primitive."""
        doms = self.domains()
        if not doms:
            return []
        lo = self.today - dt.timedelta(days=weeks * 7 - 1)
        idx = day_index()
        total = 0
        d = lo
        while d <= self.today:
            rec = idx.get(d.isoformat())
            if rec:
                total += rec["work"]
            d += dt.timedelta(days=1)
        if total <= 0:
            return [f"No tracked work in the last {weeks} weeks to map yet."]
        rows, attributed = [], 0
        for dom in doms:
            m = self._domain_minutes(dom, lo, self.today)
            attributed += m
            try:
                tgt = float(dom.get("target_pct") or 0) or None
            except ValueError:
                tgt = None
            rows.append([dom["name"], m, 100 * m / total, tgt])
        lines = [f"LIFE ALIGNMENT — last {weeks} weeks, {total / 60:.0f}h of "
                 "tracked time by domain:"]
        for name, m, pct, tgt in sorted(rows, key=lambda x: -x[1]):
            seg = f"  {name[:14]:<14} {m / 60:5.1f}h  {pct:3.0f}%"
            if tgt:
                seg += f"   aim {tgt:.0f}%  ({pct - tgt:+.0f} pts)"
            lines.append(seg)
        # unmapped time — only trustworthy when keywords don't overlap and
        # inflate `attributed` past the real total
        if attributed <= total:
            upct = 100 * (total - attributed) / total
            if upct >= 5:
                lines.append(f"  {'(unmapped)':<14} "
                             f"{(total - attributed) / 60:5.1f}h  {upct:3.0f}%"
                             "   — not in any domain")
        # the sharpest misalignment, named
        gaps = [(name, pct - tgt) for name, m, pct, tgt in rows if tgt]
        if gaps:
            worst = min(gaps, key=lambda x: x[1])
            over = max(gaps, key=lambda x: x[1])
            if worst[1] <= -8:
                lines += ["", f"→ widest say-do gap: {worst[0]} — you aim for "
                          f"it but it's getting {abs(worst[1]):.0f} points "
                          "less of your time than you said it should"]
            elif over[1] >= 12:
                lines += ["", f"→ {over[0]} is taking {over[1]:.0f} points more "
                          "than you aimed — fine if that's the season, "
                          "crowding out the rest if it isn't"]
        return lines

    def _alignment_win(self):
        win = tk.Toplevel(self)
        win.title("Life alignment — time vs stated values")
        win.geometry("560x300")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        body = self._alignment_lines()
        if not body:
            body = ["No life domains set yet.", "",
                    "Tools > Life domains… — name a handful of life areas",
                    "(Work, Body, Growth, People, Rest) with the task",
                    "keywords that belong to each, and an optional target",
                    "share of your time. This view then shows where your",
                    "hours actually go vs where you said they should."]
        txt.insert("1.0", "\n".join(body))
        txt.config(state="disabled")

    def _set_domains(self):
        """Config the life domains: name + task keywords + optional target
        share (%). Mirrors the Goals dialog one level up."""
        win = tk.Toplevel(self)
        win.title("Life domains — the values layer")
        win.resizable(False, False)
        win.grab_set()
        cols = ("Domain (empty = off)", "Tasks containing (comma-sep)",
                "Target % (opt)")
        keys = ("name", "match", "target_pct")
        for c, lbl in enumerate(cols):
            ttk.Label(win, text=lbl).grid(row=0, column=c, padx=4, pady=(8, 2))
        cur = self.domains()
        grid = []
        for i in range(6):
            dom = cur[i] if i < len(cur) else {}
            row = []
            for c, key in enumerate(keys):
                e = ttk.Entry(win, width=(8 if key == "target_pct" else 24))
                v = dom.get(key, "")
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
                    vals["target_pct"] = float(vals["target_pct"] or 0)
                except ValueError:
                    messagebox.showerror(
                        APP_NAME, f"Target % must be a number on "
                                  f"'{vals['name']}'.", parent=win)
                    return
                out.append(vals)
            self.settings["domains"] = out
            save_settings(self.settings)
            win.destroy()

        ttk.Label(win, text="Tip: keep domains roughly non-overlapping so "
                            "the percentages add up honestly.",
                  foreground="#777777").grid(row=7, column=0, columnspan=3,
                                             sticky="w", padx=4, pady=(4, 0))
        ttk.Button(win, text="Save", command=save).grid(
            row=8, column=2, sticky="e", padx=4, pady=8)

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

    def _set_work_window(self):
        ws, we = self.settings.get("work_window", ["08:00", "22:00"])
        s = simpledialog.askstring(
            APP_NAME, "Work-day window start (HH:MM) — the earliest hour "
                      "the free-slot finder should ever offer:",
            initialvalue=ws, parent=self)
        if s is None:
            return
        e = simpledialog.askstring(
            APP_NAME, "Work-day window end (HH:MM):",
            initialvalue=we, parent=self)
        if e is None:
            return
        try:
            for v in (s, e):
                h, m = map(int, v.split(":"))
                assert 0 <= h <= 23 and 0 <= m <= 59
        except (ValueError, AssertionError):
            messagebox.showerror(APP_NAME, "Use HH:MM, e.g. 08:00")
            return
        self.settings["work_window"] = [s, e]
        save_settings(self.settings)

    def _set_protected_windows(self):
        """Backlog #50/#121: named recurring windows subtracted from
        _free_slots (and, via #82's _protected_hours, the aggregate
        capacity model too) exactly like calendar busy-time already
        is — lunch, a wind-down hour, but also now a day job, sleep,
        morning admin, grey admin/chores: the "realistic blocks" a
        real day has that you don't want cluttering an actual Outlook
        calendar but still want counted honestly against capacity.
        `Days` optionally restricts a window to specific weekdays
        ("Mon-Fri", blank = every day); a window can cross midnight
        (sleep, e.g. 23:00-08:30); `Skip dates` (backlog #132) lets
        one specific day sit out — a holiday off the Day job without
        editing the whole commitment and editing it back — all three
        handled by _protected_intervals, not this dialog. Same small-
        grid-of-entries pattern as Goals/Deadlines."""
        win = tk.Toplevel(self)
        win.title("Recurring commitments (lunch, day job, sleep, admin...)")
        win.resizable(False, False)
        win.grab_set()
        cols = ("Label (empty = off)", "Start (HH:MM)", "End (HH:MM)",
                "Days (blank=every day, e.g. Mon-Fri)",
                "Skip dates (comma-sep YYYY-MM-DD, e.g. one-off holiday)")
        for c, lbl in enumerate(cols):
            ttk.Label(win, text=lbl).grid(row=0, column=c, padx=4, pady=(8, 2))
        cur = self.settings.get("protected_windows", [])
        n_rows = max(8, len(cur))
        grid = []
        for i in range(n_rows):
            w = cur[i] if i < len(cur) else {}
            row = []
            for c, key in enumerate(("label", "start", "end", "days", "skip")):
                width = 26 if c == 0 else (10 if c in (1, 2) else (16 if c == 3 else 24))
                e = ttk.Entry(win, width=width)
                val = w.get(key, "")
                if key == "skip" and isinstance(val, list):
                    val = ",".join(val)
                e.insert(0, val)
                e.grid(row=i + 1, column=c, padx=4, pady=2)
                row.append(e)
            grid.append(row)

        # backlog #126: suggest a Sleep row from real tracked data into
        # the first blank row, if there's no Sleep entry yet — never
        # auto-saved, just pre-filled and immediately editable/clearable
        if not any("sleep" in (w.get("label") or "").lower() for w in cur):
            suggestion = self._suggested_sleep_block()
            if suggestion:
                bed_t, wake_t, n = suggestion
                for i in range(len(cur), n_rows):
                    if not grid[i][0].get().strip():
                        grid[i][0].insert(0, "Sleep")
                        grid[i][1].insert(0, f"{bed_t:%H:%M}")
                        grid[i][2].insert(0, f"{wake_t:%H:%M}")
                        ttk.Label(
                            win, text=f"↑ suggested from {n} real tracked "
                                     "nights — edit or clear before saving",
                            foreground="#2e6da4", font=("Segoe UI", 8)
                        ).grid(row=i + 1, column=5, sticky="w", padx=(4, 8))
                        break

        def save():
            out = []
            for row in grid:
                label = row[0].get().strip()
                start, end = row[1].get().strip(), row[2].get().strip()
                days = row[3].get().strip()
                skip_raw = row[4].get().strip()
                if not label:
                    continue
                try:
                    for v in (start, end):
                        h, m = map(int, v.split(":"))
                        assert 0 <= h <= 23 and 0 <= m <= 59
                except (ValueError, AssertionError):
                    messagebox.showerror(
                        APP_NAME, f"Use HH:MM for '{label}'.", parent=win)
                    return
                skip = []
                for part in skip_raw.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        skip.append(dt.date.fromisoformat(part).isoformat())
                    except ValueError:
                        messagebox.showerror(
                            APP_NAME, f"Use YYYY-MM-DD for '{label}' skip "
                                     f"dates — '{part}' isn't a date.",
                            parent=win)
                        return
                out.append({"label": label, "start": start, "end": end,
                           "days": days, "skip": skip})
            self.settings["protected_windows"] = out
            save_settings(self.settings)
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(
            row=n_rows + 1, column=4, sticky="e", padx=4, pady=8)

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

        # the big clock is the SESSION total (matches the old app's
        # "studying duration" — only Reset clears it, a task Switch never
        # does, on purpose). That's exactly what reads as "the timer kept
        # going" when you switch tasks, even though the log/csv already
        # attributes minutes correctly per task. This small readout is
        # the fix: elapsed time on the CURRENT interval only, visibly
        # back to 0:00 the instant you Switch or Start.
        self.task_clock = ttk.Label(self.top, text="", font=("Segoe UI", 10),
                                    foreground="#777777")
        self.task_clock.pack(side="left", padx=(8, 0), anchor="s", pady=(0, 5))

        self.compact_btn = ttk.Button(self.top, text="—", width=3,
                                      command=self._toggle_compact)
        self.compact_btn.pack(side="right")
        self.calendar_btn = ttk.Button(
            self.top, text="📅", width=3,
            command=self._tracked("Calendar view", self._calendar_view_win))
        self.calendar_btn.pack(side="right", padx=(0, 4))
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
        # syntax highlighting is purely a VIEW layer — tags style how Tk
        # renders the text, the underlying file is untouched, byte-
        # identical either way. raw_event is also elide-able (Tools >
        # Hide raw timer lines): a real fold, not a color trick, since
        # those lines are pure machine bookkeeping no human needs to read.
        self.diary.tag_configure("raw_event", foreground="#b5b5b5",
                                 font=("Consolas", 8))
        self.diary.tag_configure("struct", foreground="#7a7a8c")
        self.diary.tag_configure("day_header", foreground="#1a4a7a",
                                 font=("Consolas", 11, "bold"))
        self.diary.tag_configure("meta_header", foreground="#2e6b2e",
                                 font=("Consolas", 10, "bold"))
        self.diary.tag_configure("theme_block", foreground="#8a5ba3")
        self.diary.tag_configure("warn_line", foreground="#c0392b",
                                 font=("Consolas", 10, "bold"))
        self.diary.tag_configure("raw_event", elide=self.settings.get(
            "hide_raw_lines", False))

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

    # order matters: first match wins, so more specific patterns
    # (theme block delimiters) must precede their generic parents
    # (the day-header "===" rule)
    _LINE_TAG_RULES = [
        (re.compile(r"^(Start|Stop|Reset);"), "raw_event"),
        (re.compile(r"^=== (THEME|END THEME)"), "theme_block"),
        (re.compile(r"^==="), "day_header"),
        (re.compile(r"^(SIGNAL:|AVOID:|YEAR:|ENERGY:|METRICS:|EXPERIMENT:|"
                    r"DECIDED:|CAPSULE:|COMMIT:|TODAY:|TODO|SOMEDAY:|"
                    r"WEEK REVIEW|plan today:|focus order today)"),
         "meta_header"),
        (re.compile(r"⚠|^!!!"), "warn_line"),
        (re.compile(r"^---"), "struct"),
    ]

    def _tag_lines(self, start_line, end_line):
        """Apply syntax-highlight tags to lines [start_line, end_line]
        (1-indexed, inclusive) — a pure view layer, never touches the
        buffer content or the file on disk."""
        for lineno in range(start_line, end_line + 1):
            ls, le = f"{lineno}.0", f"{lineno}.end"
            content = self.diary.get(ls, le)
            for pattern, tag in self._LINE_TAG_RULES:
                if pattern.search(content):
                    self.diary.tag_add(tag, ls, le)
                    break

    def _retag_diary(self):
        """Full re-tag, for when the whole buffer changed at once (a
        fresh load) rather than one appended block."""
        for tag in ("raw_event", "struct", "day_header", "meta_header",
                   "theme_block", "warn_line"):
            self.diary.tag_remove(tag, "1.0", "end")
        last_line = int(self.diary.index("end-1c").split(".")[0])
        self._tag_lines(1, last_line)

    def _append_text(self, text, cursor_to_line_end=False):
        """Append at end of the day file text; optionally park the cursor at
        the end of the first appended line (so you can type a break note)."""
        cur = self.diary.get("1.0", "end-1c")
        if cur and not cur.endswith("\n"):
            self.diary.insert("end", "\n")
        index_before = self.diary.index("end-1c")
        start_line = int(index_before.split(".")[0])
        self.diary.insert("end", text + "\n")
        end_line = int(self.diary.index("end-1c").split(".")[0])
        self._tag_lines(start_line, end_line)
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
            self._last_break_secs = 0
            self.reset_btn.config(state="normal")
            self.switch_btn.config(state="normal")
            self.btn.config(text="Stop")
        elif self.state == "working":
            self._log_work_until(now)
            self.state = "break"
            self.break_start = now
            # remember what this break interrupted — the pull-back only
            # escalates when it was a SIGNAL task (procrastination risk),
            # a coffee off admin keeps the gentle pill
            self.break_from = self.active_task
            self.break_from_signal = bool(
                self.active_task
                and self._is_signal(self.active_task, self._signal_kws()))
            self._pull_seen = 0
            self.switch_btn.config(state="disabled")
            self.btn.config(text="Start")
        else:  # break -> back to work
            bsecs = int((now - self.break_start).total_seconds())
            self._last_break_secs = bsecs   # the re-entry ramp reads this
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
                    g = next((g["name"] for g in self.goals()
                             if task_matches(self.active_task,
                                             self._match_kws(g.get("match")))),
                             None)
                    note += (f" · not today's signal, but counts toward: {g}"
                             if g else " · ⚠ not today's signal (no goal either)")
                elif (kws and not self.task_box_secs
                      and self._is_signal(self.active_task, kws)):
                    box = self._suggested_time_box()
                    if box:
                        note += f" · try boxing ~{box}m (your natural cycle)"
                ctx = self._last_context(self.active_task)
                if ctx:
                    note += f' · last time ({ctx[0]:%d.%m}): "{ctx[1][:60]}"'
                switches = self._day_switches(self.today)
                if switches >= 4:
                    note += f" · {switches} switches today"
            if getattr(self, "_last_break_secs", 0) >= self.RAMP_BREAK_SECS:
                op = self._reentry_opener(self.active_task)
                if op:
                    note += f" · start small: {op}"
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
        """Enter in the task box: split if working, otherwise just
        start. Backlog #92: a recognized command ('done: X') is
        handled instead of being treated as a task name."""
        if self._try_command(self.task_var.get()):
            self.task_var.set("")
            return
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
        text = f"Switched to {self.active_task or '(no task)'}"
        ctx = self._last_context(self.active_task) if self.active_task else None
        if ctx:
            text += f' · last time ({ctx[0]:%d.%m}): "{ctx[1][:60]}"'
        self.status.config(text=text)
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

    def _last_context(self, task, max_days=120):
        """Where you left off: the last diary line you wrote about this
        task, with its date — your own note handed back at the moment you
        resume, so the thread doesn't have to be re-found. Looks for the
        most recent day the task was tracked, then the last human-written
        line after that day's final '--- Task:' marker for it (machine
        lines skipped via the same rules the highlighter uses). Returns
        (date, snippet) or None. Read-only."""
        t = (task or "").strip().lower()
        if not t:
            return None
        idx = day_index()
        last = None
        for i in range(1, max_days + 1):
            d = self.today - dt.timedelta(days=i)
            rec = idx.get(d.isoformat())
            if rec and any(k.lower() == t for k in rec["tasks"]):
                last = d
                break
        if last is None:
            return None
        try:
            with open(self.diary_path(last), encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError:
            return None
        skip = [p for p, _ in self._LINE_TAG_RULES]
        start = 0
        for i, ln in enumerate(lines):
            s = ln.strip().lower()
            if s.startswith("--- task:") and t in s:
                start = i + 1

        def pick(seq):
            out = None
            for ln in seq:
                s = ln.strip()
                if len(s) >= 4 and not any(p.search(s) for p in skip):
                    out = s
            return out

        snippet = pick(lines[start:]) or (pick(lines) if start else None)
        if not snippet:
            return None
        if len(snippet) > 118:
            snippet = snippet[:117] + "…"
        return last, snippet

    # ----- deadline finish-date projection (real-pace forecast) -----

    def _dl_velocity(self, dl, days=21):
        """Real recent pace on a deadline's keyword lens over the trailing
        `days` calendar days: average hours on the days it was actually
        touched, and how often it was touched. Recent behaviour predicts
        the near term better than the whole stale history, so this is a
        trailing window, not all-time. None until 5+ tracked intervals
        exist — the same honesty gate the insights use."""
        kws = self._match_kws(dl.get("match", ""))
        cutoff = self.today - dt.timedelta(days=days - 1)
        per_day, intervals = {}, 0
        for r in read_rows():
            if r[1] == "break":
                continue
            if kws and not task_matches(r[5], kws):   # empty kws = all work,
                continue                              # same as _dl_progress
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[4])
            except ValueError:
                continue
            if cutoff <= d <= self.today:
                per_day[d] = per_day.get(d, 0) + m
                intervals += 1
        if intervals < 5 or not per_day:
            return None
        active = len(per_day)
        window = (self.today - cutoff).days + 1
        return {"avg_active_h": sum(per_day.values()) / active / 60,
                "active_frac": active / window,
                "active_days": active, "window": window}

    def _dl_projection(self, dl, days=21):
        """When you ACTUALLY land vs the due date, extrapolated from real
        recent pace — not the 'needed h/day' figure, which silently
        assumes perfect future compliance. Combined rate = avg hours per
        active day × how often it's active ('2h/active-day, active 40% of
        the time' is 0.8h/calendar-day, not 2). Only for scoped deadlines
        with hours still remaining; None otherwise."""
        try:
            p = self._dl_progress(dl)
        except (ValueError, KeyError):
            return None
        if not p.get("total_h") or p["remaining_h"] <= 0:
            return None
        v = self._dl_velocity(dl, days)
        if not v:
            return None
        rate = v["avg_active_h"] * v["active_frac"]      # h per calendar day
        if rate <= 0:
            return None
        rem = p["remaining_h"]
        d1 = math.ceil(rem / rate)
        d2 = math.ceil(rem / (rate + 1.0))               # if +1h/day from now
        land = dt.date.today() + dt.timedelta(days=d1)
        return {"land": land, "delta": (land - p["due"]).days, "rate": rate,
                "avg_active_h": v["avg_active_h"],
                "active_frac": v["active_frac"], "due": p["due"],
                "sooner": max(0, d1 - d2)}

    def _projection_line(self, dl):
        """One honest sentence, or None. The blunt-math counterpart to
        'needs Xh/day': at the pace you've actually kept, here's the date
        you hit — and what one extra hour a day would buy."""
        pr = self._dl_projection(dl)
        if not pr:
            return None
        # backlog #99: a triple-digit day count (common in the first
        # days of a new deadline, before real velocity settles) reads
        # as absurd rather than honest — the date itself stays exact,
        # only the qualifier softens past a threshold
        when = ("on time" if pr["delta"] == 0 else
                "far behind — see the date" if pr["delta"] > 90 else
                f"{pr['delta']}d late" if pr["delta"] > 0 else
                f"{-pr['delta']}d early")
        line = (f"at your real pace ({pr['avg_active_h']:.1f}h on active "
                f"days, active {round(100 * pr['active_frac'])}% of days) "
                f"you land ~{pr['land']:%d.%m} — {when} "
                f"(due {pr['due']:%d.%m})")
        if pr["delta"] > 0 and 0 < pr["sooner"] <= 90:
            line += f".  +1h/day from now → {pr['sooner']}d sooner"
        return line

    def _deadline_postmortem_lines(self, dl):
        """Backlog #28: once a scoped deadline's due date has passed,
        one retro block instead of the deadline just quietly
        disappearing — each one closed becomes calibration data. Four
        honest numbers: scope vs actual hours; the estimate factor on
        THIS project specifically (not `_estimate_factor`'s app-wide
        blend); a RETROSPECTIVE projection accuracy check — what a
        projection made 21 days before the due date (the same trailing
        window `_dl_velocity` uses) would have predicted, against the
        date the scope was actually completed, if it was; and the real
        pace kept over the project's whole life, not just a trailing
        window. Returns None for an unscoped deadline (no `total_h`) or
        one whose due date hasn't passed yet — the caller is
        responsible for the "write once" guard."""
        if not dl.get("total_h"):
            return None
        due = dt.date.fromisoformat(dl["date"])
        if self.today <= due:
            return None
        kws = self._match_kws(dl.get("match", ""))
        start = None
        if dl.get("start"):
            try:
                start = dt.date.fromisoformat(dl["start"])
            except ValueError:
                pass
        lo = start or dt.date.min
        total_h = float(dl["total_h"])
        idx = day_index()

        def hours_through(hi):
            if kws:
                return matched_minutes(kws, lo, hi) / 60
            lo_iso, hi_iso = lo.isoformat(), hi.isoformat()
            return sum(rec["work"] for iso, rec in idx.items()
                      if lo_iso <= iso <= hi_iso) / 60

        done_h = hours_through(due)
        lines = [f"DEADLINE POST-MORTEM — {dl['name']} (due {due:%d.%m.%Y}):",
                f"  scope {total_h:g}h declared, {done_h:.1f}h actually "
                f"logged ({round(100 * done_h / total_h)}%)"]

        ef = self._estimate_factor(kws) if kws else None
        if ef:
            factor, n = ef
            verdict = ("ran long" if factor > 1.1 else
                      "ran short" if factor < 0.9 else "roughly accurate")
            lines.append(f"  estimate factor on this project: {factor:.2f}x "
                        f"(n={n}) — {verdict}")

        # retrospective projection: what the same trailing-21-day pace
        # math _dl_projection uses would have predicted, evaluated as
        # of 21 days before the due date, against what actually happened
        as_of = due - dt.timedelta(days=21)
        if start:
            as_of = max(as_of, start)
        win_lo = max(as_of - dt.timedelta(days=20), lo)
        per_day = {}
        for r in read_rows():
            if r[1] == "break":
                continue
            if kws and not task_matches(r[5], kws):
                continue
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[4])
            except ValueError:
                continue
            if win_lo <= d <= as_of:
                per_day[d] = per_day.get(d, 0) + m
        if len(per_day) >= 5:
            window = (as_of - win_lo).days + 1
            rate = (sum(per_day.values()) / len(per_day) / 60) * (
                len(per_day) / window)
            if rate > 0:
                remaining = max(0.0, total_h - hours_through(as_of))
                predicted = as_of + dt.timedelta(days=math.ceil(remaining / rate))
                actual = None
                d, cum = lo, 0.0
                while d <= due:
                    cum = hours_through(d)
                    if cum >= total_h:
                        actual = d
                        break
                    d += dt.timedelta(days=1)
                if actual:
                    delta = (predicted - actual).days
                    when = ("right on the day" if delta == 0 else
                           f"ran {delta}d pessimistic" if delta > 0 else
                           f"ran {-delta}d optimistic")
                    lines.append(f"  projection (made 21d before due): "
                                f"predicted {predicted:%d.%m}, actually "
                                f"finished {actual:%d.%m} — {when}")
                else:
                    lines.append(f"  projection (made 21d before due): "
                                f"predicted {predicted:%d.%m} — scope was "
                                "never fully completed by the due date")

        span = max((due - lo).days, 1) if lo != dt.date.min else None
        full_per_day = {}
        for r in read_rows():
            if r[1] == "break":
                continue
            if kws and not task_matches(r[5], kws):
                continue
            try:
                d = dt.date.fromisoformat(r[0])
                m = int(r[4])
            except ValueError:
                continue
            if lo <= d <= due:
                full_per_day[d] = full_per_day.get(d, 0) + m
        if full_per_day and span:
            active = len(full_per_day)
            avg_active_h = sum(full_per_day.values()) / active / 60
            lines.append(f"  pace kept: {avg_active_h:.1f}h on active days, "
                        f"active {round(100 * active / span)}% of the "
                        f"{span} day(s) since {lo:%d.%m.%Y}")
        return lines

    def _run_deadline_postmortems(self):
        """Backlog #28: checked once at day-open (_new_day_header, not
        on every insight scan — a deadline closes once, the record
        should write once). Every deadline whose due date has just
        passed and hasn't been retro'd yet gets marked
        `postmortem_written` and its lines returned for insertion into
        TODAY's file; an unscoped deadline still gets marked (nothing
        useful to say twice) even though `_deadline_postmortem_lines`
        returns None for it."""
        out, changed = [], False
        for dl in self.deadlines():
            if dl.get("postmortem_written"):
                continue
            try:
                due = dt.date.fromisoformat(dl["date"])
            except (ValueError, KeyError):
                continue
            if self.today <= due:
                continue
            lines = self._deadline_postmortem_lines(dl)
            dl["postmortem_written"] = True
            changed = True
            if lines:
                out += lines
        if changed:
            save_settings(self.settings)
        return out

    def _root_cause_line(self, dl):
        """Backlog #47: when a scoped deadline is behind the straight-
        line pace, split WHY into the right lever. Capacity problem —
        genuinely not enough free time this week even if every free
        hour had gone to it — vs. choice problem — plenty of free time
        existed, it just went elsewhere. Needs the week mostly through
        (Wed+) to be a fair sample of "this week"; silent otherwise,
        same honesty framing as the rest of the planning engine. Pure
        view over _dl_progress + _day_capacity + matched_minutes, no
        new data source."""
        if self.today.weekday() < 2:      # Mon/Tue: too early to judge
            return None
        try:
            p = self._dl_progress(dl)
        except (ValueError, KeyError):
            return None
        if not p.get("behind") or not p.get("total_h"):
            return None
        mon = self.today - dt.timedelta(days=self.today.weekday())
        elapsed = (self.today - mon).days + 1
        avail = sum(self._day_capacity(mon + dt.timedelta(days=i))
                    for i in range(elapsed))
        kws = self._match_kws(dl.get("match", ""))
        logged = (matched_minutes(kws, mon, self.today) / 60) if kws else 0.0
        needed_so_far = p["needed_per_day"] * elapsed
        name = dl["name"]
        if avail < needed_so_far - 0.3:
            return (f"{name} is behind pace — and you only had {avail:.1f}h "
                    "free this week. A capacity problem: something else "
                    "has to give.")
        if avail - logged >= 2.0:
            return (f"{name} is behind pace — but you had {avail:.1f}h "
                    f"free this week and only put {logged:.1f}h into it. "
                    "Not a capacity problem.")
        return None

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
            interval_secs = 0
            if self.active_task and self.work_start:
                interval_secs = int((dt.datetime.now() - self.work_start).total_seconds())
                task_tot = getattr(self, "task_today_min", 0) * 60 + interval_secs
                title += f" · today {task_tot / 3600:.2f}h"
            self.task_clock.config(
                text=(f"this task: {interval_secs // 60}:{interval_secs % 60:02}"
                     if self.active_task else ""))
            self.title(title)
            self._check_time_box(task_tot)
            self._watch_idle()
            self._watch_lock()
        elif self.state == "break":
            bsecs = int((dt.datetime.now() - self.break_start).total_seconds())
            self.clock.config(text=f"☕ {hms_padded(bsecs)}", foreground="")
            self.task_clock.config(text="")
            self.title(f"☕ break {bsecs // 60}:{bsecs % 60:02} — {APP_NAME}")
            self._update_pill(bsecs)
        else:
            self.clock.config(text="0:00:00", foreground="")
            self.task_clock.config(text="")
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

    @staticmethod
    def _pull_level(bsecs, pull_min, from_signal):
        """0 = normal pill rules · 1 = pull-back · 2 = hard pull-back (2×
        the threshold). Escalates ONLY when the break interrupted a signal
        task and the feature is on (pull_min > 0). Deliberately a loud
        stated nudge, never a lock — the twice-held anti-gating precedent
        stands (see HANDOFF); a lock you can alt-tab past is just noise."""
        if not from_signal or not pull_min:
            return 0
        if bsecs >= 2 * pull_min * 60:
            return 2
        if bsecs >= pull_min * 60:
            return 1
        return 0

    def _set_pull(self):
        cur = int(self.settings.get("pull_min", 20))
        v = simpledialog.askinteger(
            APP_NAME, "On a break from a SIGNAL task, the pill turns into\n"
                      "a pull-back after this many minutes (0 = off).\n"
                      "Loud and impossible to miss — never a lock.",
            initialvalue=cur, minvalue=0, maxvalue=240, parent=self)
        if v is not None:
            self.settings["pull_min"] = v
            save_settings(self.settings)

    RAMP_BREAK_SECS = 30 * 60   # after this long away, offer an opener

    def _waiting_on_lines(self):
        """Backlog #44: blocked task-library items — set via the Tasks
        window's right-click "Set blocked by…" — don't just vanish once
        filtered out of the planner's suggestions elsewhere; they move
        to a visibly different bucket instead. No due-date logic, no
        reminders to chase the blocker — that's someone else's problem
        to solve, not the app's to nag about."""
        blocked = [t for t in self.settings.get("tasks", [])
                  if t.get("blocked_by")]
        if not blocked:
            return []
        lines = ["WAITING ON:"]
        for t in blocked:
            lines.append(f"  {t['name']} — blocked by: {t['blocked_by']}")
        return lines

    def _reentry_opener(self, task):
        """The smallest concrete opener for restarting after a long break
        — activation energy is the real enemy, so hand over a 10-minute
        piece instead of the mountain. Preference order: task-library item
        related to the active task (smallest estimate first), then the
        smallest signal-priority item, then any smallest-estimate item,
        else today's first TODO bullet. Returns a short string or None.
        Blocked items (backlog #44) are excluded — the planner shouldn't
        suggest resuming something structurally not doable yet."""
        t = (task or "").lower()
        cands = []
        for item in self.settings.get("tasks", []):
            if item.get("blocked_by"):
                continue
            try:
                est = float(item.get("est_h") or 0)
            except (TypeError, ValueError):
                est = 0
            if not est:
                continue
            name = item["name"]
            rel = (0 if t and (t in name.lower() or name.lower() in t)
                   else 1 if item.get("priority") == "signal" else 2)
            cands.append((rel, est, name))
        if cands:
            _rel, est, name = min(cands)
            return f"'{name}' ({est:g}h)"
        for ln in self.diary.get("1.0", "end-1c").splitlines():
            s = ln.strip()
            if s.startswith(("- ", "* ", "[ ] ")):
                body = s.lstrip("-*[] ").strip()
                if len(body) >= 3:
                    return f"'{body[:60]}'"
        return None
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
        level = self._pull_level(bsecs, int(self.settings.get("pull_min", 20)),
                                 getattr(self, "break_from_signal", False))
        if level:
            task = getattr(self, "break_from", "") or "the signal task"
            mins = bsecs // 60
            if level == 2:
                t = f"⚑⚑ {mins} min. '{task}' is bleeding out — one click."
            else:
                t = (f"⚑ {mins} min off '{task}' — click: the first minute "
                     "is the whole battle")
            self.pill_lbl.config(text=t,
                                 bg="#5c0f0f" if level == 2 else "#b02020")
            if level > getattr(self, "_pull_seen", 0):
                self._pull_seen = level
                self.pill.lift()
                try:
                    import winsound
                    winsound.Beep(660, 220)
                except Exception:
                    pass
            return
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
        if self._in_workblock():
            thr *= self._WORKBLOCK_IDLE_FACTOR
        idle = idle_seconds()
        if idle > thr * 60:
            self.idle_since = dt.datetime.now() - dt.timedelta(seconds=idle)
        elif self.idle_since and idle < 15:
            gone_since, self.idle_since = self.idle_since, None
            self._offer_idle_break(gone_since)

    def _watch_lock(self):
        """Windows+L should trigger a break — the idle-minutes detector
        above only catches genuine keyboard/mouse idleness, and misses
        a deliberate screen lock shorter than idle_min (a quick 3-min
        lock to grab coffee is still a break, unlike 3 minutes of just
        reading the screen without touching anything). Detected via
        is_locked() (best-effort, see its own docstring); reuses the
        exact same retro-split offer _watch_idle already shows on
        return — one mechanism, two triggers. Gated on idle_min being
        on at all (0 = "away detection off" already covers this too,
        one master switch) but NOT on meeting-mode's idle_off_until —
        that suppresses ambiguous no-input time during a call, but an
        actual lock is unambiguous even mid-meeting."""
        if not int(self.settings.get("idle_min", 10)) or self.prompting:
            return
        locked = is_locked()
        if locked and self.lock_since is None:
            self.lock_since = dt.datetime.now()
        elif not locked and self.lock_since:
            gone_since, self.lock_since = self.lock_since, None
            min_secs = MIN_LOG_SECS
            if self._in_workblock(gone_since):
                min_secs = (int(self.settings.get("idle_min", 10)) * 60
                           * self._WORKBLOCK_IDLE_FACTOR)
            if (dt.datetime.now() - gone_since).total_seconds() >= min_secs:
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
            sig2_today, _ = self._day_signal2(self.today, kws1=kws_today, rows=rows)
            if sig2_today:
                text += f" +{round(100 * sig2_today / w)}% tier-2"

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
        budget = self._break_budget_line()
        if budget:
            text += "   |   " + budget
        self.diary_lbl.config(text=text)

    # ----- day timeline (00-24 bar) -----

    TL_WORK, TL_BREAK, TL_SIGNAL = "#4a6fa5", "#e0a44c", "#3a8a3a"
    TL_SLEEP = "#454569"
    TL_GOAL = "#8a5ba3"   # goal-aligned but not today's declared signal —
                          # e.g. a run, when today's signal is "thesis"
    TL_SIGNAL2 = "#7fbf7f"   # backlog #105: SIGNAL2's own tier-2 color —
                             # a lighter/desaturated TL_SIGNAL, distinct at
                             # a glance but visibly related (same family,
                             # one rank down)
    CAL_EVENT = "#6c8ebf"    # backlog #120: imported calendar events
    CAL_WORK = "#4a6fa5"     # backlog #120: tracked work sessions (= TL_WORK)
    CAL_COMMIT = "#b8b0a0"  # backlog #121: recurring commitments (sleep,
                             # day job, admin) — neutral/tan, deliberately
                             # unlike the blues used for real events/work
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
        kws2 = self._signal2_kws()
        goal_kws = [self._match_kws(g.get("match")) for g in self.goals()]

        def work_color(task):
            if kws and self._is_signal(task, kws):
                return self.TL_SIGNAL
            if kws2 and self._is_signal(task, kws2):
                return self.TL_SIGNAL2
            if any(task_matches(task, gk) for gk in goal_kws):
                return self.TL_GOAL
            return self.TL_WORK

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
        self._retag_diary()
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
                ysig2, _ = self._day_signal2(yday, kws1=self._signal_kws(yday))
                if ysig2:
                    line += f" (+{round(100 * ysig2 / ywork)}% tier-2)"
            line += self._avoid_trend_suffix(yday)
            parts.append(line + ")")
            v = self._verdict(yw, ysig, ywork, self._declared_cap_h(yday))
            if v:
                parts.append(v)
        otd = self._on_this_day_line()
        if otd:
            parts.append(otd)
        parts += self._capsule_lines()
        pm = self._run_deadline_postmortems()
        if pm:
            parts += ["", *pm]
        note = self._copilot_note()      # the co-pilot speaks first
        if note:
            parts.append(note)
        forecast = self._energy_forecast_line()
        if forecast:
            parts.append(forecast)
        plan = self._plan_line()
        if plan:
            parts.append(plan)
        fb = self._next_free_block_line()
        if fb:
            parts.append(fb)
        commit_line = self._commitments_today_line()
        if commit_line:
            parts.append(commit_line)
        parts += self._day_schedule_lines()
        if self.today.weekday() == 0:
            parts += self._week_review_block()
            parts += self._week_ahead_lines()
            parts += self._graveyard_lines()
        parts.append(f"SIGNAL: {self._carry_signal()}")
        sig2 = self._carry_signal2()
        if sig2 or self._line_ever_used("SIGNAL2"):
            parts.append(f"SIGNAL2: {sig2}")
        avoid = self._carry_avoid()
        if avoid or self._line_ever_used("AVOID"):
            parts.append(f"AVOID: {avoid}")
        year = self._carry_year()
        if year or self._line_ever_used("YEAR"):
            parts.append(f"YEAR: {year}")
        workblock = self._carry_workblock()
        if workblock or self._line_ever_used("WORKBLOCK"):
            parts.append(f"WORKBLOCK: {workblock}")
        parts.append("ENERGY: ")   # 1-5, optionally + a mood word ("3 anxious")
        if self._line_ever_used("METRICS"):
            parts.append("METRICS: ")  # meditation=10, water=6…
        todos = self._carry_todos(yday)
        if todos:
            parts += ["", "TODO (carried from yesterday):"] + todos
        try:
            with open(self.diary_path(yday), encoding="utf-8") as f:
                self._auto_capture_bullets(f.read(), f"{yday} diary")
        except OSError:
            pass
        return "\n".join(parts)

    _CAPSULE_RE = re.compile(r"^CAPSULE:\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+)$",
                             re.I | re.M)

    def _due_capsules(self):
        """Backlog #61: the forward-looking counterpart to on-this-day
        (below — that one looks back one year, automatically; this one
        is a deliberate seal for a FUTURE date the owner picks). A
        `CAPSULE: 2026-08-15 | message` line written on any past day,
        surfaced once today matches that target date. Pure text
        convention — a scan across day files for a CAPSULE: line whose
        date equals today, no new data source, same "read the day
        files back" shape as TODO carry-over. Returns [(written_iso,
        message), ...]."""
        out = []
        try:
            names = sorted(os.listdir(self.diary_dir()))
        except OSError:
            return out
        today_iso = self.today.isoformat()
        for fn in names:
            if not fn.endswith(".txt"):
                continue
            written_iso = fn[:-4]
            try:
                dt.date.fromisoformat(written_iso)
            except ValueError:
                continue
            if written_iso >= today_iso:
                continue
            try:
                with open(os.path.join(self.diary_dir(), fn),
                          encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                continue
            for target, msg in self._CAPSULE_RE.findall(text):
                if target == today_iso and msg.strip():
                    out.append((written_iso, msg.strip()))
        return out

    def _capsule_lines(self):
        caps = self._due_capsules()
        lines = []
        for written_iso, msg in caps:
            days = (self.today - dt.date.fromisoformat(written_iso)).days
            lines.append(f"a note from {days} days ago: {msg}")
        return lines

    def _on_this_day_line(self):
        """One year ago today, if a day file exists — the "keeps the
        data forever" vision paid back as a small, zero-effort delight
        rather than a feature you have to open a window for. Read-only:
        never touches last year's file."""
        try:
            last_year = self.today.replace(year=self.today.year - 1)
        except ValueError:
            last_year = self.today - dt.timedelta(days=365)  # Feb 29
        path = self.diary_path(last_year)
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return None
        skip_res = [p for p, _ in self._LINE_TAG_RULES]
        snippet = None
        for ln in text.splitlines():
            s = ln.strip()
            if len(s) < 4 or any(p.search(s) for p in skip_res):
                continue
            snippet = s
            break
        w, _ = day_totals(last_year.isoformat())
        if not w and not snippet:
            return None
        line = f"on this day, {last_year.year}: "
        if w:
            line += f"{w // 60}h{w % 60:02}m work"
            if snippet:
                line += " — "
        if snippet:
            line += snippet[:140] + ("…" if len(snippet) > 140 else "")
        theme = None
        for ln in text.splitlines():
            s = ln.strip()
            if s.lower().startswith("year:"):
                t = s[5:].strip()
                if t:
                    theme = t
                break
        if theme:
            line += f" · that year's theme: '{theme}' — still true?"
        return line

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

    def _focus_items(self):
        """Scoped deadlines with real remaining hours, ranked most-
        urgent-first (behind-pace overrides a merely-sooner due date).
        The shared ranking both _focus_order_lines (tier b: a plain
        priority list) and _day_schedule_lines (tier c: the same
        ranking placed into actual free time) read from — one
        computation, two views, same pattern as the day-record lenses
        elsewhere in this file."""
        items = []
        for dl in self.deadlines():
            try:
                p = self._dl_progress(dl)
            except (ValueError, KeyError):
                continue
            if p["left"] >= 0 and p.get("total_h") and p["remaining_h"] > 0:
                items.append((dl["name"], p["left"], p["needed_per_day"],
                             p.get("behind", False)))
        items.sort(key=lambda x: (not x[3], x[1], -x[2]))
        return items

    def _focus_order_lines(self):
        """Backlog "planning engine" tier b: when 2+ scoped deadlines are
        competing for today, an explicit priority order — most urgent
        first — instead of leaving the reader to do the sort. Purely a
        VIEW over _focus_items(); a recommendation the reader glances at
        and follows or ignores, not something to configure — no
        accept/reject UI, on purpose. Kept as the fallback
        _day_schedule_lines uses when there's no free time left to
        actually place anything into."""
        items = self._focus_items()
        if len(items) < 2:
            return []
        lines = ["focus order today (most urgent first):"]
        for i, (name, left, need, behind) in enumerate(items, 1):
            lines.append(f"  {i}. {name} — {need:.1f}h ({left}d left)"
                         + (" ⚠ behind pace" if behind else ""))
        # uncommitted capacity: what's left after the deadlines are fed,
        # pointing at signal-priority backlog items rather than leaving
        # the reader to wonder what the leftover hours are even for
        slack = self._day_capacity(self.today) - sum(x[2] for x in items)
        if slack > 0.3:
            signal_tasks = [tsk["name"] for tsk in self.settings.get("tasks", [])
                            if tsk.get("priority") == "signal"
                            and not tsk.get("blocked_by")]
            line = f"  {len(items) + 1}. ({slack:.1f}h uncommitted"
            line += (f" — pick from Task library: {', '.join(signal_tasks[:3])})"
                     if signal_tasks else " — pick from Task library)")
            lines.append(line)
        return lines

    def _day_schedule_lines(self):
        """v8.0: planning-engine tier c, actual time-blocked placement.
        MVP scope deliberately kept small (see HANDOFF's design notes
        before building this): TODAY only, one greedy pass — each
        _focus_items() deadline (most urgent first) claims its needed
        h/day out of _free_slots(today) (v7.9), earliest free time
        first, so urgent work lands as soon as the day allows rather
        than wherever leaves the prettiest gaps. A VIEW only, generated
        once at day-header time same as plan/focus-order — never
        tracked, never gated on whether followed (the standing
        planning-engine guardrail: no accept/reject UI, no compliance
        tracking, ever). Falls back to the plain priority list when
        there's no free time to place anything into — a schedule with
        nothing to block is just the old list, not silence."""
        items = self._focus_items()
        if not items:
            return []
        slots = list(self._free_slots(self.today))
        if not slots:
            return self._focus_order_lines()
        realism = self._planner_realism_factor()
        if realism:
            ratio, _n = realism
            items = [(name, left, need * ratio, behind)
                     for name, left, need, behind in items]
        quality = self._hour_quality()
        placements, slots = self._energy_place(items, slots, quality)
        lines = ["suggested schedule today (hardest work steered to your "
                 "peak hours):" if quality else "suggested schedule today:"]
        if realism:
            ratio, n = realism
            lines.append(f"  (planning at {round(100 * ratio)}% density — "
                        f"your plans have survived that rate over the last "
                        f"{n} scheduled day(s))")
        for name, behind, placed, shortfall in placements:
            tag = " ⚠ behind pace" if behind else ""
            for s, e in placed:
                lines.append(f"  {s:%H:%M}-{e:%H:%M} {name} "
                             f"({_time_span_hours(s, e):.1f}h){tag}")
            if shortfall > 0.05:
                lines.append(f"  ({name}: {shortfall:.1f}h doesn't fit "
                             "today's free time)")
        leftover = sum(_time_span_hours(s, e) for s, e in slots)
        if leftover >= 0.25:
            biggest = max(slots, key=lambda se: _time_span_hours(*se))
            signal_tasks = [tsk["name"] for tsk in self.settings.get("tasks", [])
                            if tsk.get("priority") == "signal"
                            and not tsk.get("blocked_by")]
            line = (f"  {biggest[0]:%H:%M}-{biggest[1]:%H:%M} uncommitted "
                    f"({leftover:.1f}h free today total)")
            if signal_tasks:
                line += f" — pick from Task library: {', '.join(signal_tasks[:3])}"
            lines.append(line)
        return lines

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
        exp_line = self._experiment_review_line(mon)
        if exp_line:
            parts.append(exp_line)
        one_less = self._one_less_line()
        if one_less:
            parts.append(one_less)
        commit_rel = self._commitment_reliability_line()
        if commit_rel:
            parts.append(commit_rel)
        focus_sig = self._focus_signature_line()
        if focus_sig:
            parts.append(f"  {focus_sig}")
        return parts

    def _week_ahead_lines(self):
        """Backlog #42: the weekly twin of the daily co-pilot line — the
        review above looks BACK at last week; this looks FORWARD across
        the next 7 days as a whole. Composes primitives that already
        exist (_day_capacity, _dl_progress, _dl_projection) — no new
        data. Silent unless something's actually worth flagging: no
        deadlines with real remaining scope, or a normal week with slack
        and nothing already behind, produce nothing at all."""
        week = [self.today + dt.timedelta(days=i) for i in range(7)]
        caps = [(d, self._day_capacity(d)) for d in week]
        total_cap = sum(c for _d, c in caps)
        needs = []
        for dl in self.deadlines():
            try:
                p = self._dl_progress(dl)
            except (ValueError, KeyError):
                continue
            if not p.get("total_h") or p["left"] < 0 or p["remaining_h"] <= 0:
                continue
            proj = self._dl_projection(dl)
            behind = bool(proj and proj["delta"] > 0)
            need = min(p["needed_per_day"] * 7, p["remaining_h"])
            needs.append((dl["name"], need, behind))
        if not needs:
            return []
        total_need = sum(n for _n, n, _b in needs)
        tightest_d, tightest_h = min(caps, key=lambda x: x[1])
        avg_cap = total_cap / 7
        overbooked = total_need > total_cap
        real_tight_day = tightest_h < avg_cap * 0.4 and tightest_h < 3.0
        behind_names = [n for n, _need, b in needs if b]
        if not (overbooked or real_tight_day or behind_names):
            return []                # a normal week — nothing to flag
        lines = ["", f"WEEK AHEAD: {total_cap:.1f}h free across the next "
                    f"7 days · deadlines need ~{total_need:.1f}h"]
        # backlog #133: total_cap above is already net of recurring
        # commitments (_day_capacity routes through _protected_hours),
        # but that's silent — name WHY it's smaller than raw weekday
        # capacity, same "show the why" instinct as #130's daily line
        commit_h = sum(self._protected_hours(d) for d in week)
        if commit_h >= 0.5:
            by_label = {}
            for d in week:
                for s, e, label in self._protected_intervals_named(d):
                    if label:
                        by_label[label] = by_label.get(label, 0.0) + _time_span_hours(s, e)
            top = sorted(by_label.items(), key=lambda x: -x[1])[:3]
            lines.append(f"  (of which {commit_h:.1f}h already committed: "
                        + ", ".join(f"{label} {h:.1f}h" for label, h in top) + ")")
        if overbooked:
            lines.append(f"  ⚠ overbooked by {total_need - total_cap:.1f}h "
                         "before the week even starts")
        if real_tight_day:
            lines.append(f"  tightest day: {tightest_d:%a %d.%m} "
                         f"({tightest_h:.1f}h free) — front-load elsewhere "
                         "if something's due")
        if behind_names:
            lines.append(f"  already behind at real pace: "
                         + ", ".join(behind_names))
        return lines

    @staticmethod
    def _verdict(work_min, sig_min, sig_work, declared_cap_h=None):
        """One honest line about yesterday. Rule-based, no flattery. A
        declared short day (backlog #37's 'TODAY: 4h' line) replaces the
        usual judgment entirely — compassionate realism, not a second
        bar to clear: honored the declared cap or didn't, no "what stole
        it" either way, since the day was already flagged honestly in
        advance."""
        h = work_min / 60
        if declared_cap_h is not None:
            if declared_cap_h == 0 or h + 0.05 >= declared_cap_h:
                return (f"verdict: short day as declared — {h:.1f}h "
                        "tracked, plan honored.")
            return None
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

    # bullets: dash/star/checkbox, SPACE OPTIONAL ("-x" and "- x" both count —
    # real usage showed people don't reliably type the space). The
    # negative lookahead excludes "--"/"---" so the app's own
    # "--- Session start"/"--- Task:" decorator lines are never
    # mistaken for a bullet.
    _BULLET_RE = re.compile(r"^-(?!-)\s*\S|^\*(?!\*)\s*\S|^\[[ xX]\]\s*\S")
    # header: 'TODO'/'SOMEDAY', optional colon, optional same-line item text
    # ("TODO:" alone -> bullets follow on later lines; "TODO: buy milk" ->
    # the item is right there, no separate bullet line needed)
    _HEADER_RE = re.compile(r"^(todo|someday)\b\s*:?\s*(.*)$", re.I)

    def _match_header(self, s):
        """(kind, same_line_item_or_None) if `s` is a TODO:/SOMEDAY:
        header, else None. Excludes the carried-header line itself so it
        never re-triggers grab mode on its own text."""
        if s.lower().startswith("todo (carried"):
            return None
        m = self._HEADER_RE.match(s)
        if not m:
            return None
        kind = "normal" if m.group(1).lower() == "todo" else "someday"
        rest = m.group(2).strip()
        return (kind, rest or None)

    def _carry_todos(self, yday):
        """Bullet lines ('-x', '* x', '[ ] x') under a 'TODO:' header, or
        a same-line 'TODO: item', from yesterday's file — carried forward
        until done or deleted. Free paragraphs are never swept in, even
        ones that mention 'todo' in passing — only marked items are, so a
        day of brainstorming prose doesn't become tomorrow's todo wall.
        Write low-priority someday/maybe items under 'SOMEDAY:' instead —
        same syntax, never carried, just browsable."""
        try:
            with open(self.diary_path(yday), encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError:
            return []
        out, grab = [], False
        for ln in lines:
            s = ln.strip()
            if grab:
                m = self._BULLET_RE.match(s)
                if m:
                    out.append(ln)
                    continue
                if s == "":
                    continue
                grab = False
            h = self._match_header(s)
            if h and h[0] == "normal":
                if h[1]:
                    out.append(f"- {h[1]}")   # same-line item, shown as a bullet
                else:
                    grab = True
        return out[:12]

    # ----- task library (the one place messy ideas/todos live) -----

    def _extract_bullets(self, text):
        """[(kind, item_text), ...] for every TODO:/SOMEDAY: item in
        `text` — either a bullet line under a header, or the text right
        after 'TODO:' on the same line. kind is 'normal' or 'someday'."""
        out, grab = [], None
        for ln in text.splitlines():
            s = ln.strip()
            if grab:
                m = self._BULLET_RE.match(s)
                if m:
                    out.append((grab, s[m.end() - 1:].strip()))
                    continue
                if s == "":
                    continue
                grab = None
            h = self._match_header(s)
            if h:
                kind, same_line = h
                if same_line:
                    out.append((kind, same_line))
                else:
                    grab = kind
        return out

    # Written by hand, not generated from the changelog, and not meant
    # to be rewritten every version — a stable reference. Each topic:
    # (title, body). Verify exact syntax against the real regex/parser
    # before editing this, don't write it from memory.
    _HELP_TOPICS = [
        ("Welcome",
         "TimerDiary starts as a work timer and ends up knowing more "
         "about your life than any app you've used, because it's built "
         "on one rule: your day file IS the app.\n\n"
         "Everything the app has to say lands as plain text in that "
         "one .txt file per day — no hidden database, nothing you "
         "can't read or edit yourself. Views, insights and dashboards "
         "are all just different ways of reading that same file back.\n\n"
         "This window explains what's actually in here — pick a topic "
         "on the left. It's written by hand and kept short on purpose; "
         "it won't get rewritten every time a feature ships, so if "
         "something below stops matching reality, that's itself worth "
         "mentioning."),

        ("The day file",
         "Every morning (or whenever you first open the app that day) "
         "a new day file gets created automatically, already carrying "
         "yesterday's numbers, a plan for today, and whatever header "
         "lines you use (see the other topics).\n\n"
         "Below that header, the file is a mix of two things, "
         "interleaved: raw timer lines (Start/Stop/Reset — these are "
         "what the app writes when you press the buttons) and your own "
         "free-typed notes, wherever you put them. You can write "
         "between timer lines, at the end, anywhere — it all saves "
         "automatically every ~10 seconds.\n\n"
         "Tools > \"Hide raw timer lines in the diary\" folds the "
         "Start/Stop/Reset bookkeeping out of view if it gets visually "
         "noisy — purely a display setting, the file on disk never "
         "changes."),

        ("SIGNAL, AVOID & WORKBLOCK",
         "SIGNAL: declares today's ONE real priority, as one or more "
         "comma-separated keywords — e.g. \"SIGNAL: thesis, ch4\". Any "
         "task whose name contains one of those words counts as "
         "signal time; tomorrow's header reports what share of "
         "yesterday's work was actually signal (\"signal 67%\").\n\n"
         "Leave it blank and it carries forward automatically: either "
         "repeating yesterday's SIGNAL, or — if you've never set one — "
         "seeded from your Goals' own keywords (Tools > Goals). You "
         "don't have to type it every day for it to work.\n\n"
         "SIGNAL2: a second, separate priority tier — for when two "
         "things both matter today but one is clearly sharper than the "
         "other (\"SIGNAL: thesis\" / \"SIGNAL2: hegemon\"). It never "
         "dilutes SIGNAL's own number — tier-1 stays exactly what it "
         "always meant, tier-2 is reported alongside it as its own "
         "share (\"signal 45% +20% tier-2\"). Type it once and it "
         "carries forward like SIGNAL does; the header line only "
         "appears once you've actually used it.\n\n"
         "AVOID: is the mirror image of SIGNAL — keywords for what "
         "you're trying to cut down on (\"AVOID: news, email\"). Same "
         "mechanism, inverted, reported the same way, with a quiet "
         "arrow showing whether this week is trending up or down "
         "against the previous few weeks.\n\n"
         "WORKBLOCK: declares an externally-committed window, e.g. "
         "\"WORKBLOCK: 09:00-17:00\" for a day job. Inside it, idle and "
         "screen-lock detection waits about 3x longer before offering "
         "to log a break — a quick meeting or email check during "
         "already-spoken-for time isn't a break the way it would be "
         "outside it. Carries forward like AVOID; only appears in the "
         "header once you've used it."),

        ("YEAR, ENERGY & METRICS",
         "YEAR: a standing theme for the whole year (\"YEAR: the "
         "graduation year\") — set once, carries forward silently "
         "after that, same shape as AVOID.\n\n"
         "ENERGY: a 1-5 number for how much fuel you had today, "
         "optionally followed by a word for how it FELT — \"ENERGY: 3 "
         "anxious\". The number and the word are read as two different "
         "things on purpose: you can be low-energy-but-calm or "
         "high-energy-but-anxious, and the app tracks both, separately, "
         "against your signal share.\n\n"
         "METRICS: the general-purpose one — any personal fact you "
         "want kept, as comma-separated key=value pairs, e.g. "
         "\"METRICS: water=2L, meditation=10, cold_shower\". A bare "
         "word with no \"=\" logs itself as 1 (handy for yes/no habits). "
         "This exists so a brand-new thing you want to track — "
         "caffeine, supplements, mood, anything — never needs new code "
         "or a new settings dialog. Just start typing it."),

        ("TODO / SOMEDAY — the task library",
         "Write \"TODO: reply to X\" or \"SOMEDAY: learn Y\" anywhere "
         "in any day file — the header, a themed-writing session, "
         "mid-note — and it's automatically copied into the Task "
         "library (View > Tasks/backlog) within about 10 seconds, no "
         "copying it anywhere yourself.\n\n"
         "The library tracks estimate-vs-actual hours per task once "
         "you finish it (click Done, or type \"done: <name>\" in the "
         "task box — see \"In the task box\"), so over time the app "
         "can tell you how far off your own estimates typically run.\n\n"
         "Right-click a row to link it to a Goal or a Deadline, mark "
         "its priority (signal / normal / someday), or set what it's "
         "blocked by."),

        ("DECIDED, CAPSULE, COMMIT, EXPERIMENT, TODAY",
         "Five smaller conventions, each solving one specific "
         "annoyance:\n\n"
         "DECIDED: apartment — staying another year, rent's still fair\n"
         "  Makes a real decision searchable forever (View > Memory > "
         "Decision log) so you stop relitigating settled questions "
         "from memory.\n\n"
         "CAPSULE: 2026-08-15 | a note to future you\n"
         "  Seals a message that only resurfaces in the header on that "
         "future date — a note to yourself, delivered on schedule.\n\n"
         "COMMIT: thesis 4h  (or just \"COMMIT: 4h\" for overall work)\n"
         "  A promise for the day. The Monday review reports the "
         "trailing rate you actually deliver on — self-calibration, "
         "not a daily grade.\n\n"
         "EXPERIMENT: no work after 21:00\n"
         "  Declares a one-week self-test; checked automatically "
         "against your own trailing baseline once the week's up.\n\n"
         "TODAY: 4h  (or \"TODAY: sick\", no number needed)\n"
         "  Declares a short or off day IN ADVANCE, so tomorrow's "
         "verdict judges you against what you said, not your normal "
         "day — no guilt trip for a day you already knew would be "
         "light."),

        ("In the task box",
         "Typing \"done: thesis ch4\" and pressing Enter marks the "
         "matching task-library item done, without opening the Tasks "
         "window at all.\n\n"
         "A trailing [15m] or [1h30m] on a task name time-boxes it for "
         "today — \"email: EU [15m]\" — and the app warns once you go "
         "over.\n\n"
         "Right-click a row in the Tasks window to set what it's "
         "blocked by, or link it to a Goal or Deadline."),

        ("View menu — Planning",
         "The forward-looking pillar: Week plan / capacity (your "
         "weekly hours budget vs what's due), Outlook (every scoped "
         "deadline simulated forward at your REAL recent pace, not the "
         "naive one), and Deadline burn-down (one deadline's progress "
         "chart, with a real-pace landing-date projection and — once "
         "you're behind — whether that's a capacity problem or a "
         "choice problem)."),

        ("View menu — Memory",
         "The archive, made queryable: Trend (8 weeks), Month heatmap, "
         "Year rhythm map, Search all days (ranked multi-term search "
         "across every day file, with a \"copy matching days for AI\" "
         "button), and Decision log (every DECIDED: line, newest "
         "first)."),

        ("View menu — Values",
         "Is your time actually going where you say it should: Life "
         "alignment (tracked time vs. the Domains you've declared), "
         "Life review (one weekly briefing synthesizing all three "
         "pillars into a single honest bottom line), and Lens overlap "
         "check (do two of your declared Goals/Domains/Deadlines "
         "accidentally share keywords and silently double-count the "
         "same hours toward two different percentages)."),

        ("Writing",
         "Ctrl+T opens a distraction-free popup for reflection, "
         "brainstorming, or a \"someday\" list on any topic — it saves "
         "as a folded block in today's day file, not a separate "
         "document. Browse themes (View menu) is a read-only scan "
         "across every day file for these blocks, grouped by topic, so "
         "you can revisit everything you've written about one thing "
         "over time."),

        ("Tools menu highlights",
         "Data doctor cleans up messy task names (typos, near-"
         "duplicates) across your whole history. Feature usage shows "
         "which of this app's views you actually open, honestly. Life "
         "domains is the values layer above Goals. The rest are the "
         "knobs: idle detection minutes, break pull-back threshold, "
         "day rollover hour, work-day window, protected time windows "
         "(lunch, wind-down) — all optional, all off unless you set "
         "them."),

        ("Easy to forget exists",
         "A short list of real features that are easy to lose track "
         "of in everything else this app does:\n\n"
         "• Decision log — every DECIDED: line, searchable\n"
         "• Time capsule — CAPSULE: notes to your future self\n"
         "• Life domains — the values layer above Goals\n"
         "• Lens overlap check — catches accidental double-counting\n"
         "• Cost-of-yes preview — live in the deadline-editing dialog\n"
         "• Search all days — ranked search across your whole history\n"
         "• Feature usage (Tools) — which of all this you actually use"),
    ]

    def _help_win(self):
        win = tk.Toplevel(self)
        win.title(f"{APP_NAME} — quick reference")
        win.geometry("760x520")
        win.rowconfigure(0, weight=1)
        win.columnconfigure(1, weight=1)

        side = tk.Listbox(win, width=26, exportselection=False,
                          font=("Segoe UI", 9), activestyle="dotbox",
                          relief="sunken", borderwidth=2)
        side.grid(row=0, column=0, sticky="ns", padx=(8, 4), pady=8)
        for title, _ in self._HELP_TOPICS:
            side.insert("end", title)

        txt = tk.Text(win, wrap="word", font=("Segoe UI", 10),
                      padx=12, pady=10, relief="sunken", borderwidth=2)
        txt.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)

        def show(event=None):
            sel = side.curselection()
            if not sel:
                return
            _, body = self._HELP_TOPICS[sel[0]]
            txt.config(state="normal")
            txt.delete("1.0", "end")
            txt.insert("1.0", body)
            txt.config(state="disabled")

        side.bind("<<ListboxSelect>>", show)
        side.selection_set(0)
        show()

    def _task_actual_h(self, name, added):
        """Real hours logged against a task-library item's name since
        it was added — shared by the Tasks window's display column and
        _mark_task_done's Done-line."""
        t, tot = name.strip().lower(), 0
        for r in read_rows():
            if (r[1] != "break" and r[5].strip().lower() == t
                    and r[0] >= added):
                try:
                    tot += int(r[4])
                except ValueError:
                    pass
        return tot / 60

    def _mark_task_done(self, i):
        """Backlog #91: archive task-library item `i` to `tasks_done`
        instead of discarding it — the --- Done: line in the diary
        text is honest but not structured, and #10/#45 want clean
        historical Done data without re-parsing every day file for it.
        Writes the same --- Done: line as before. Shared by the Tasks
        window's Done button and #92's 'done: X' command shorthand.
        Returns the completed task's name."""
        t = self.settings["tasks"].pop(i)
        actual_h = self._task_actual_h(t["name"], t["added"])
        done_rec = dict(t)
        done_rec["done_on"] = self.today.isoformat()
        done_rec["actual_h"] = round(actual_h, 2)
        self.settings.setdefault("tasks_done", []).append(done_rec)
        save_settings(self.settings)
        line = f"--- Done: {t['name']}"
        if t.get("est_h"):
            line += f" (est {t['est_h']:g}h, actual {actual_h:.2f}h)"
        self._append_text(line)
        return t["name"]

    _COMMAND_RE = re.compile(r"^(done)\s*:\s*(.+)$", re.I)

    def _try_command(self, raw):
        """Backlog #92: a tiny fixed-verb command parser for the task
        box — 'done: thesis ch4' marks the matching task-library item
        done. Deliberately NOT #60's deferred Python console: this is
        pattern-matching against one recognized word, not exec()/
        eval(), so none of #60's real risk (a typo damaging years of
        data) applies. Returns True if `raw` was a recognized command
        (and it was handled, successfully or not) — the caller should
        treat the task box as consumed either way, not fall through to
        starting/switching a task named literally 'done: ...'."""
        m = self._COMMAND_RE.match(raw.strip())
        if not m:
            return False
        arg = m.group(2).strip()
        key = " ".join(arg.lower().split())
        tasks = self.settings.get("tasks", [])
        i = next((i for i, t in enumerate(tasks)
                  if key in " ".join(t["name"].lower().split())), None)
        if i is None:
            self.status.config(text=f'No task-library item matches "{arg}".')
            return True
        name = self._mark_task_done(i)
        self.status.config(text=f"Marked done: {name}")
        return True

    def _add_task(self, name, est_h=0, priority="normal", goal=None,
                 deadline=None, source=None):
        """Add to the library, deduped by normalized name — the same
        bullet carried unchanged for a few days doesn't create
        duplicates every time it's re-scanned. Backlog #97: also
        collapses growing-prefix duplicates from the SAME source — a
        bullet still being typed gets re-captured on every 10s
        autosave tick, and since the text keeps growing, exact-match
        dedup alone never catches consecutive snapshots of it. If this
        capture's text and an existing same-source entry's text are a
        prefix of one another, that's one bullet mid-typing, not two —
        the entry is updated in place to the longer (more complete)
        version instead of a new one appended. Cross-source bullets
        are never merged this way, only same-day/same-theme captures.
        Returns True if a genuinely new item was added."""
        name = name.strip()
        if not name:
            return False
        key = " ".join(name.lower().split())
        tasks = self.settings.setdefault("tasks", [])
        if any(" ".join(t["name"].lower().split()) == key for t in tasks):
            return False
        if source:
            for t in tasks:
                if t.get("source") != source:
                    continue
                existing_key = " ".join(t["name"].lower().split())
                if key.startswith(existing_key) or existing_key.startswith(key):
                    if len(key) > len(existing_key):
                        t["name"] = name
                        save_settings(self.settings)
                    return False
        tasks.append({"name": name, "est_h": est_h, "priority": priority,
                      "goal": goal, "deadline": deadline, "source": source,
                      "added": self.today.isoformat()})
        save_settings(self.settings)
        return True

    def _auto_capture_bullets(self, text, source):
        """Every TODO:/SOMEDAY: item in `text` lands in the task library
        automatically — write one anywhere (main diary, a themed-writing
        session) and it's tracked, not just carried forward as raw text
        until you happen to reread it. Returns how many were new."""
        added = 0
        for kind, item in self._extract_bullets(text):
            if self._add_task(item, priority=("someday" if kind == "someday"
                                               else "normal"), source=source):
                added += 1
        return added

    def _backfill_task_library(self):
        """Runs every launch (cheap, deduped): sweeps the last 14 days'
        files for TODO:/SOMEDAY: items the parser missed before it
        recognized no-space bullets and same-line 'TODO: text' — old
        writing shouldn't need retyping just because the recognizer
        got better."""
        total = 0
        for i in range(14):
            d = self.today - dt.timedelta(days=i)
            try:
                with open(self.diary_path(d), encoding="utf-8") as f:
                    total += self._auto_capture_bullets(f.read(), f"{d} diary")
            except OSError:
                continue
        if total:
            self.status.config(
                text=f"Backfilled {total} item(s) into the task library "
                    "from the last 14 days.")

    def _experiment_from_file(self, iso):
        """The EXPERIMENT: line text from ONE day's file, or None — same
        in-file, opt-in, never-prompted convention as SIGNAL/AVOID/
        ENERGY (backlog #20). Typed once, typically in Monday's header,
        never suggested by the app itself."""
        try:
            with open(self.diary_path(dt.date.fromisoformat(iso)),
                      encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.lower().startswith("experiment:"):
                        text = s[len("experiment:"):].strip()
                        return text or None
        except OSError:
            pass
        return None

    def _week_metric_totals(self, monday):
        """Backlog #20: one week's aggregate (starting `monday`) on the
        metrics the rest of the app already tracks — work, breaks,
        late-evening (>=21:00) minutes, average sleep. Shared by the
        experiment review so declaring and measuring the same numbers
        doesn't mean two different scans."""
        days = {(monday + dt.timedelta(days=i)).isoformat() for i in range(7)}
        idx = day_index()
        work = sum((idx.get(iso) or {"work": 0})["work"] for iso in days)
        brk = sum((idx.get(iso) or {"brk": 0})["brk"] for iso in days)
        late = 0
        for r in read_rows():
            if r[0] in days and r[1] != "break":
                try:
                    h = int(r[2].split(":")[0]) % 24
                    if h >= 21:
                        late += int(r[4])
                except (ValueError, IndexError):
                    continue
        sleeps = [s for s in (self._sleep_h(iso) for iso in days) if s]
        sleep = sum(sleeps) / len(sleeps) if sleeps else None
        return {"work": work, "brk": brk, "late": late, "sleep": sleep}

    def _experiment_review_line(self, monday):
        """Backlog #20: closes the diagnose-then-nothing loop every
        other insight leaves open. If `monday`'s day file declared an
        EXPERIMENT, report that week's measured shift on work, late-
        evening minutes and sleep against the trailing-4-week baseline
        before it. Deliberately NEVER a verdict on whether the free-
        text RULE itself was followed ("kept it 5/7 days") — parsing
        arbitrary user text into an enforceable check would be too
        fragile to state honestly; a plain before/after on numbers the
        app already tracks instead. Needs >=2 real baseline weeks;
        silent otherwise. Stated once here, never re-nagged mid-week."""
        text = self._experiment_from_file(monday.isoformat())
        if not text:
            return None
        exp = self._week_metric_totals(monday)
        base = [self._week_metric_totals(monday - dt.timedelta(weeks=w))
               for w in range(1, 5)]
        base = [b for b in base if b["work"] or b["brk"]]
        if len(base) < 2:
            return None

        def avg(key):
            vals = [b[key] for b in base if b[key] is not None]
            return sum(vals) / len(vals) if vals else None

        parts = []
        b_late = avg("late")
        if b_late is not None:
            parts.append(f"late-evening {(exp['late'] - b_late) / 60:+.1f}h "
                         "vs baseline")
        b_sleep = avg("sleep")
        if exp["sleep"] is not None and b_sleep is not None:
            parts.append(f"sleep {exp['sleep'] - b_sleep:+.1f}h/night vs "
                         "baseline")
        b_work = avg("work")
        if b_work:
            parts.append(f"output {(exp['work'] - b_work) / 60:+.1f}h vs "
                         "baseline")
        if not parts:
            return None
        return f"  EXPERIMENT '{text}': " + "; ".join(parts)

    def _one_less_candidates(self):
        """Backlog #35: this week's removal candidates, one honest
        reframe — subtraction, not another thing to add. Sourced
        entirely from mechanisms this app already has: the single
        worst meeting-fragmentation cost (v8.42), the task you bounce
        off most (v8.12's procrastination pattern), and the after-
        21:00 work that taxes tomorrow (v8.38's lag check). Returns
        only candidates that already clear their OWN honesty gate, in
        priority order; empty when nothing qualifies."""
        out = []
        frag = self._meeting_fragmentation_lines()
        if frag:
            out.append(("meeting_fragmentation",
                       f"the meeting that fragments your day — {frag[0]}"))
        proc = self._procrastination_insight()
        if proc:
            out.append(("procrastination",
                       f"the task you keep bouncing off — {proc[0]}"))
        evening = self._lag_evening_start_line()
        if evening:
            out.append(("late_evening", f"the after-21:00 work — {evening}"))
        return out

    def _one_less_line(self):
        """Backlog #35: one line in the Monday review — "this week,
        try one less: X" — never a list, never a gate, just a single
        subtraction to consider. Rotates via `_pick_one_less` so an
        ignored candidate doesn't repeat back-to-back while a
        different one also qualifies; remembers only the LAST key
        suggested, not whether it was acted on (that verdict isn't
        this app's to make)."""
        pick = _pick_one_less(self._one_less_candidates(),
                              self.settings.get("one_less_last_key"))
        if not pick:
            return None
        self.settings["one_less_last_key"] = pick[0]
        save_settings(self.settings)
        return f"  THIS WEEK, TRY ONE LESS: {pick[1]}"

    def _carry_signal(self):
        """Yesterday's SIGNAL line text (original case) if it was
        actually filled in, else seeded from the most urgent scoped
        deadline (backlog #109), else goal-seeded as a last resort.

        BUG FIXED 2026-07-29: a SIGNAL line that EXISTS but was left
        blank (true for every day since v6.1 auto-writes the line
        unconditionally) used to `return s[7:].strip()` = "" the moment
        the line was found — never falling through to the goal-seed
        below. Since nearly every real day file has a SIGNAL: line
        whether or not it was ever typed into, this made the fallback
        effectively dead code: SIGNAL kept carrying forward empty
        forever once a single blank day existed, silently disabling
        every SIGNAL-dependent feature in the app (timeline color,
        the status-bar flag, and every insight that compares against
        signal%) for anyone who never manually typed a SIGNAL value.
        Now an existing-but-empty line is treated the same as a
        missing one — falls through to goal-seeding either way."""
        try:
            with open(self.diary_path(self.today - dt.timedelta(days=1)),
                      encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.lower().startswith("signal:"):
                        text = s[7:].strip()
                        if text:
                            return text
                        break   # found but blank -> fall through below
        except OSError:
            pass
        # Backlog #109: no carried value — seed from the single MOST
        # URGENT scoped deadline (_focus_items' own ranking, already
        # built for the day-schedule/focus-order views) rather than
        # blending every goal's keywords together. "SIGNAL: thesis"
        # because thesis is actually behind pace, not because it's
        # alphabetically first among goals — a diffuse blend is the
        # opposite of "today's ONE sharpest priority." Only falls back
        # to the all-goals blend when no deadline is scoped at all.
        items = self._focus_items()
        if items:
            top_name = items[0][0]
            dl = next((d for d in self.deadlines() if d["name"] == top_name), None)
            if dl and dl.get("match", "").strip():
                return dl["match"].strip()
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

    def _scan_decisions(self):
        """Backlog #62: every `DECIDED: <topic> — <verdict>` line across
        every day file, newest first. Purely archival — no counter, no
        reopening friction, no unlock mechanic (that was #9's Reopening
        Guard, explicitly rejected as too close to a gating pattern).
        This just makes "wait, didn't I already think this through"
        answerable by reading the list back, exactly like Search all
        days already does for free text — a dedicated ledger is just a
        shortcut to browse without typing a query first."""
        out = []
        try:
            names = sorted(os.listdir(self.diary_dir()), reverse=True)
        except OSError:
            return out
        for fn in names:
            if not fn.endswith(".txt"):
                continue
            date = fn[:-4]
            try:
                with open(os.path.join(self.diary_dir(), fn),
                          encoding="utf-8") as f:
                    for line in f:
                        s = line.strip()
                        if s.lower().startswith("decided:"):
                            text = s[len("decided:"):].strip()
                            if text:
                                out.append((date, text))
            except OSError:
                continue
        return out

    def _decision_log_view(self):
        win = tk.Toplevel(self)
        win.title("Decision log")
        win.geometry("640x420")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        decisions = self._scan_decisions()
        if not decisions:
            txt.insert("1.0", "No DECIDED: lines yet — type one in any "
                              "day file, e.g. \"DECIDED: apartment — "
                              "staying another year, rent's still fair\".")
        else:
            for date, text in decisions:
                txt.insert("end", f"{date}  {text}\n")
        txt.config(state="disabled")

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
                added = self._auto_capture_bullets(body, f"theme: {name}")
                msg = f"Saved {mins}m of themed writing — {name}"
                if added:
                    msg += f"  ·  +{added} to task library"
                self.status.config(text=msg)
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
            # live capture: a TODO:/SOMEDAY: item typed straight into
            # today's diary (not just a themed-writing session) now
            # lands in the task library within ~10s, not "at rollover
            # tomorrow" — that was the actual gap the user hit
            added = self._auto_capture_bullets(
                self.diary.get("1.0", "end-1c"), f"{self.today} diary")
            if added:
                self.status.config(
                    text=f"+{added} new item(s) → Task library")
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

    # ----- life review (the co-pilot's synthesis of all three pillars) -----

    def _review_bottom_line(self):
        """The synthesis the scattered views can't give on their own: read
        FORESIGHT (are deadlines slipping at real pace) and ALIGNMENT (is
        a valued domain starving) together, and say the ONE thing to do.
        Rule-based, blunt, no flattery — the connective tissue between the
        pillars, the seed of the eventual AI-analyst layer done keyless."""
        behind = []
        for dl in self.deadlines():
            try:
                proj = self._dl_projection(dl)
            except (ValueError, KeyError):
                proj = None
            if proj and proj["delta"] > 0:
                behind.append((dl["name"], proj["delta"]))
        lo = self.today - dt.timedelta(days=8 * 7 - 1)
        idx = day_index()
        total = 0
        d = lo
        while d <= self.today:
            rec = idx.get(d.isoformat())
            if rec:
                total += rec["work"]
            d += dt.timedelta(days=1)
        worst = None
        if total > 0:
            for dom in self.domains():
                try:
                    tgt = float(dom.get("target_pct") or 0) or None
                except ValueError:
                    tgt = None
                if not tgt:
                    continue
                gap = 100 * self._domain_minutes(dom, lo, self.today) / total - tgt
                if worst is None or gap < worst[1]:
                    worst = (dom["name"], gap)
        top = max(behind, key=lambda x: x[1]) if behind else None
        # backlog #99: a triple-digit day count (common in the first
        # days of a new deadline) reads as absurd rather than honest
        top_late = (f"is not on track to finish" if top and top[1] > 90 else
                    f"lands ~{top[1] if top else 0}d late")
        if top and worst and worst[1] <= -8:
            return [f"You're behind on {top[0]} ({top_late} at real pace) "
                    f"AND under-investing in {worst[0]} ({worst[1]:.0f} pts "
                    "below your aim). Same fix, not two: the FIRST block of "
                    f"each day goes to {worst[0]}/{top[0]} before the urgent "
                    "small stuff eats the morning."]
        if top:
            return [f"Main risk: {top[0]} {top_late} at your current "
                    "pace. Add ~1h/day to it or move the date now — while "
                    "moving it is still cheap, not the night before."]
        if worst and worst[1] <= -10:
            return [f"Deadlines are fine, but {worst[0]} is {abs(worst[1]):.0f} "
                    "points below where you said it should be — the quiet "
                    "erosion, not the loud crisis. One protected block this week."]
        if behind or worst:
            return ["Roughly on track. No fire — spend the slack deliberately "
                    "before it spends itself."]
        return ["On pace and living your stated priorities — the boring good "
                "state. Protect the routine that got you here."]

    def _anomaly_lines(self, weeks=10):
        """What's UNUSUAL for you right now, measured against your OWN
        baseline — the app noticing instead of waiting to be asked. Each
        line compares the present to your recent history, not an abstract
        ideal. Ranked by severity; speaks only with enough history to know
        what 'normal' is. The proactive, attentive layer."""
        out = []
        idx = day_index()
        today = self.today
        # --- sleep-week extremity vs your last `weeks` weeks
        this_mon = today - dt.timedelta(days=today.weekday())
        wk_sleep = []
        for k in range(weeks - 1, -1, -1):
            mon = this_mon - dt.timedelta(weeks=k)
            sls = []
            for i in range(7):
                dd = mon + dt.timedelta(days=i)
                if dd > today:
                    break
                sl = self._sleep_h(dd.isoformat())
                if sl:
                    sls.append(sl)
            wk_sleep.append(sum(sls) / len(sls) if sls else None)
        prior = [s for s in wk_sleep[:-1] if s is not None]
        cur = wk_sleep[-1]
        if cur is not None and len(prior) >= 3:
            base = sum(prior) / len(prior)
            if cur <= min(prior) and base - cur >= 0.5:
                out.append((3.0, f"worst sleep week in {len(prior) + 1} weeks "
                            f"— {fmt_sleep(cur)}/night vs your {fmt_sleep(base)} "
                            "norm; expect the work to feel harder"))
            elif cur >= max(prior) and cur - base >= 0.5:
                out.append((1.0, f"best sleep week in {len(prior) + 1} weeks "
                            f"({fmt_sleep(cur)}/night) — keep whatever changed"))
        # --- neglect: days since you last touched a declared domain/goal
        watch = [(d["name"], d.get("match")) for d in self.domains()] or \
                [(g["name"], g.get("match")) for g in self.goals()]
        for name, spec in watch:
            kws = self._match_kws(spec)
            if not kws:
                continue
            last = None
            for back in range(0, 91):
                rec = idx.get((today - dt.timedelta(days=back)).isoformat())
                if rec and any(task_matches(t, kws) for t in rec["tasks"]):
                    last = today - dt.timedelta(days=back)
                    break
            if last is not None and (today - last).days >= 10:
                gap = (today - last).days
                out.append((2.0 + min(gap, 40) / 40,
                            f"{gap} days since any {name} — drifting from "
                            "something you flagged as mattering"))
        # --- signal drought: trailing tracked days with 0% signal
        drought = 0
        for back in range(1, 15):
            rec = idx.get((today - dt.timedelta(days=back)).isoformat())
            if not rec or rec["work"] == 0:
                break
            s, w = self._day_signal(today - dt.timedelta(days=back))
            if w > 0 and s == 0:
                drought += 1
            else:
                break
        if drought >= 3:
            out.append((2.5, f"{drought} straight tracked days at ~0% signal "
                        "— the work's happening, just not on what you named"))
        out.sort(key=lambda x: -x[0])
        return [t for _p, t in out][:4]

    def _copilot_note(self):
        """The single most important proactive line for the morning header
        — the co-pilot greeting you rather than waiting to be opened.
        Prefer an actionable risk (the bottom line) when there is one;
        then the running-hot index (backlog #24, a body-schedule risk
        outranks a schedule risk); otherwise the sharpest anomaly. None
        when there's nothing real to say (no filler 'good state' in the
        day file)."""
        bl = self._review_bottom_line()
        if bl and any(k in bl[0] for k in
                      ("behind on", "Main risk", "below where you said")):
            return "co-pilot: " + bl[0]
        hot = self._running_hot_line()
        if hot:
            return "co-pilot: " + hot
        an = self._anomaly_lines()
        if an:
            return "co-pilot: " + an[0]
        return None

    def _life_review_lines(self):
        """One briefing that makes the pillars speak as one voice: this
        week's numbers, then VALUES (alignment), AHEAD (outlook),
        TRAJECTORY (months), PATTERNS (insights), and a synthesized BOTTOM
        LINE. Everything here is a tested view function composed together."""
        monday = self.today - dt.timedelta(days=self.today.weekday())
        idx = day_index()
        work = sig = 0
        sleeps = []
        d = monday
        while d <= self.today:
            rec = idx.get(d.isoformat())
            if rec:
                work += rec["work"]
                sig += self._day_signal(d)[0]
            sl = self._sleep_h(d.isoformat())
            if sl:
                sleeps.append(sl)
            d += dt.timedelta(days=1)
        head = f"  {work / 60:.1f}h tracked"
        if work:
            head += f" · signal {round(100 * sig / work)}%"
        if sleeps:
            head += f" · sleep avg {fmt_sleep(sum(sleeps) / len(sleeps))}"
        L = [f"LIFE REVIEW — week of {monday:%d.%m.%Y}", head]
        for title, body in (("UNUSUAL — vs your own baseline", self._anomaly_lines()),
                            ("VALUES — are you living them?", self._alignment_lines()),
                            ("AHEAD — what's coming, at your real pace", self._outlook_lines()),
                            ("TRAJECTORY — the last two months", self._trajectory_lines())):
            if body:
                L += ["", title] + body
        ins = self._insight_lines()
        if ins:
            L += ["", "PATTERNS"] + ["  · " + x for x in ins[:3]]
        L += ["", "BOTTOM LINE"] + ["  " + x for x in self._review_bottom_line()]
        return L

    def _life_review_win(self):
        self._save_diary()
        win = tk.Toplevel(self)
        win.title("Life review — the week, synthesized")
        win.geometry("660x520")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        body = "\n".join(self._life_review_lines())
        txt.insert("1.0", body)
        txt.config(state="disabled")
        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=(0, 8))

        def copy():
            self.clipboard_clear()
            self.clipboard_append(body + "\n\nAsk: given all of the above, "
                                  "what's the one change that matters most "
                                  "next week?")
            self.status.config(text="Life review copied — paste into Claude "
                                    "for a second opinion on the bottom line.")

        ttk.Button(bar, text="Copy for AI second opinion",
                   command=copy).pack(side="left")

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
        win.geometry("620x560")
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
        lines.append("")
        lines += self._health_extras_lines()
        txt.insert("1.0", "\n".join(lines))
        txt.config(state="disabled")

    def _health_extras_lines(self):
        """The health-hub extras (v8.27 mindful/RHR/HRV/weight, v8.28
        daylight) as their own compact 14-day table — captured onto the
        day record but never shown as more than one header line before
        this. Kept SEPARATE from _health_view's main table rather than
        widened into one ~90-char row (see the concept model's "don't
        duplicate a view" rule — this is one more block in the SAME
        window, not a rival view): stays readable at a normal window
        width, and nothing about the proven first table has to change to
        make room for it. Pure logic, split from the Tk glue above so it
        can be tested without a display."""
        hd = self._health_data()
        lines = [" day        mindful    rhr    hrv  weight  daylight",
                " " + "-" * 55]
        any_extra = False
        for i in range(13, -1, -1):
            d = self.today - dt.timedelta(days=i)
            rec = hd.get(d.isoformat(), {})
            dl = self._daylight_h(d)
            if any(rec.get(k) for k in ("mindful_min", "rhr", "hrv",
                                        "weight_kg")) or dl is not None:
                any_extra = True
            lines.append(
                f" {d:%a %d.%m}  "
                + (f"{round(rec['mindful_min']):>5}m" if rec.get("mindful_min") else "      -")
                + (f"  {rec['rhr']:>5.0f}" if rec.get("rhr") else "      -")
                + (f"  {rec['hrv']:>5.0f}" if rec.get("hrv") else "      -")
                + (f"  {rec['weight_kg']:>5.1f}" if rec.get("weight_kg") else "      -")
                + (f"  {dl:>6.1f}h" if dl is not None else "       -"))
        if not any_extra:
            lines += ["", " Nothing here yet — mindful/RHR/HRV/weight need",
                      " those columns in your health export (File > Health",
                      " import folder…); daylight needs a latitude (Tools",
                      " > Daylight location…). Both are free once set."]
        return lines

    # ----- open old day / search -----

    def _open_day_file(self):
        p = filedialog.askopenfilename(parent=self, initialdir=self.diary_dir(),
                                       filetypes=[("Day files", "*.txt")])
        if p:
            os.startfile(p)

    def _quick_day_nav(self):
        """Backlog #93: the owner's own ask — a lighter way to open a
        previous day than the OS file-picker (which starts back in the
        diary folder every time, the exact friction being complained
        about). A recent-days list plus a few relative jumps
        ("yesterday", "a week ago", "a month ago"); picking a day reads
        it straight into a Text pane, same two-pane Listbox+Text shape
        as the Help window. 'Open in Notepad' stays one click away for
        anyone who wants to actually edit."""
        try:
            names = sorted((fn for fn in os.listdir(self.diary_dir())
                           if fn.endswith(".txt")), reverse=True)
        except OSError:
            names = []
        days = []
        for fn in names[:30]:
            try:
                days.append(dt.date.fromisoformat(fn[:-4]))
            except ValueError:
                continue

        win = tk.Toplevel(self)
        win.title("Open a day file")
        win.geometry("760x520")
        win.rowconfigure(1, weight=1)
        win.columnconfigure(1, weight=1)

        jump = ttk.Frame(win)
        jump.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 4))
        ttk.Label(jump, text="Jump to:").pack(side="left")

        side = tk.Listbox(win, width=16, exportselection=False,
                          font=("Segoe UI", 9), activestyle="dotbox",
                          relief="sunken", borderwidth=2)
        side.grid(row=1, column=0, sticky="ns", padx=(8, 4), pady=(0, 4))
        for day in days:
            side.insert("end", f"{day:%a %d.%m.%Y}")

        txt = tk.Text(win, wrap="word", font=("Consolas", 10),
                      padx=10, pady=8, relief="sunken", borderwidth=2)
        txt.grid(row=1, column=1, sticky="nsew", padx=(0, 8), pady=(0, 4))

        current = {"day": None}

        def show(day):
            current["day"] = day
            try:
                with open(self.diary_path(day), encoding="utf-8") as f:
                    body = f.read()
            except OSError:
                body = "(no file for this date)"
            txt.config(state="normal")
            txt.delete("1.0", "end")
            txt.insert("1.0", body)
            txt.config(state="disabled")
            win.title(f"Open a day file — {day:%A %d.%m.%Y}")

        def show_selected(event=None):
            sel = side.curselection()
            if sel:
                show(days[sel[0]])

        def jump_to(delta):
            target = self.today - dt.timedelta(days=delta)
            if target in days:
                side.selection_clear(0, "end")
                side.selection_set(days.index(target))
                side.see(days.index(target))
            show(target)

        side.bind("<<ListboxSelect>>", show_selected)
        for label, delta in (("yesterday", 1), ("a week ago", 7),
                             ("a month ago", 30)):
            ttk.Button(jump, text=label,
                      command=lambda d=delta: jump_to(d)).pack(side="left",
                                                               padx=(6, 0))

        btns = ttk.Frame(win)
        btns.grid(row=2, column=0, columnspan=2, sticky="e", padx=8, pady=(0, 8))
        ttk.Button(btns, text="Open in Notepad…",
                  command=lambda: current["day"] and os.startfile(
                      self.diary_path(current["day"]))).pack(side="right")

        if days:
            side.selection_set(0)
            show(days[0])

    def _diary_rank_days(self, query, max_days=2000):
        """Backlog #14: an honest BETTER keyword search, not fake semantic
        search (no embeddings — stdlib-only rule stands). Splits the query
        into terms, OR-matches across every day file, and ranks by breadth
        (how many DISTINCT terms hit — a day mentioning 3 of your 3 terms
        beats one mentioning 1 term ten times), then depth (total matching
        lines), then recency. Returns [(date, breadth, hit_lines)], best
        match first; hit_lines is every matching line in that file, for
        building an excerpt without needing the whole file."""
        terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) >= 2]
        if not terms:
            return []
        try:
            names = sorted(os.listdir(self.diary_dir()), reverse=True)
        except OSError:
            return []
        out, seen = [], 0
        for fn in names:
            if not fn.endswith(".txt"):
                continue
            try:
                day = dt.date.fromisoformat(fn[:-4])
            except ValueError:
                continue
            if seen >= max_days:
                break
            seen += 1
            try:
                with open(os.path.join(self.diary_dir(), fn),
                          encoding="utf-8") as f:
                    lines = f.read().splitlines()
            except OSError:
                continue
            matched, hits = set(), []
            for line in lines:
                low = line.lower()
                line_terms = {t for t in terms if t in low}
                if line_terms:
                    matched |= line_terms
                    hits.append(line)
            if matched:
                out.append((day, len(matched), hits))
        out.sort(key=lambda x: (-x[1], -len(x[2]), -x[0].toordinal()))
        return out

    def _pin_search(self, query):
        """Backlog #71: save `query` to the settings-backed shortlist
        surfaced next to the search box — a recurring lookup ("what did
        I decide about the advisor situation") becomes one click
        instead of retyping."""
        pins = _pinned_after_add(self.settings.get("pinned_searches", []),
                                 query)
        self.settings["pinned_searches"] = pins
        save_settings(self.settings)
        return pins

    def _unpin_search(self, query):
        pins = _pinned_after_remove(self.settings.get("pinned_searches", []),
                                    query)
        self.settings["pinned_searches"] = pins
        save_settings(self.settings)
        return pins

    def _matching_days_text(self, query, top_n=5, max_lines_per_day=12):
        """The clipboard payload for 'Copy matching days for AI': the top
        N ranked day EXCERPTS (matching lines only, not whole files) with
        date headers — makes a year of day files queryable via a normal
        AI chat without an API key, same manual-copy-paste pattern as the
        weekly 'Copy for AI review' (v5.1)."""
        ranked = self._diary_rank_days(query)
        if not ranked:
            return None
        parts = [f'Diary search: "{query}" — top {min(top_n, len(ranked))} '
                f"of {len(ranked)} matching day(s)"]
        for day, score, hit_lines in ranked[:top_n]:
            parts.append(f"\n===== {day:%a %Y-%m-%d} (matched {score} "
                         "term(s)) =====")
            parts += hit_lines[:max_lines_per_day]
            if len(hit_lines) > max_lines_per_day:
                parts.append(f"  … {len(hit_lines) - max_lines_per_day} "
                             "more matching line(s) in this day, not shown")
        return "\n".join(parts)

    def _search_diary(self):
        win = tk.Toplevel(self)
        win.title("Search all days")
        win.geometry("700x440")
        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=8)
        q = ttk.Entry(bar)
        q.pack(side="left", fill="x", expand=True)
        q.focus_set()
        pinbar = ttk.Frame(win)
        pinbar.pack(fill="x", padx=8, pady=(0, 4))
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        def render_pins():
            for w in pinbar.winfo_children():
                w.destroy()
            pins = self.settings.get("pinned_searches", [])
            if not pins:
                ttk.Label(pinbar, text="no pinned searches yet — Pin "
                          "saves the current query", foreground="#888888"
                         ).pack(side="left")
                return
            for p in pins:
                def use(event=None, p=p):
                    q.delete(0, "end")
                    q.insert(0, p)
                    go()

                def unpin(event=None, p=p):
                    self._unpin_search(p)
                    render_pins()
                    self.status.config(text=f"Unpinned '{p}'.")

                btn = ttk.Button(pinbar, text=p, command=use)
                btn.pack(side="left", padx=(0, 4))
                btn.bind("<Button-3>", unpin)     # right-click to unpin

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

        def copy_matching():
            query = q.get().strip()
            if not query:
                return
            text = self._matching_days_text(query)
            if not text:
                self.status.config(text=f"No matches for '{query}'.")
                return
            self.clipboard_clear()
            self.clipboard_append(
                text + "\n\nAsk: what actually happened with this, and "
                "what should I do about it now?")
            self.status.config(
                text=f"Copied top matching days for '{query}' — paste "
                     "into Claude/whatever, ask your real question.")

        def pin_current():
            query = q.get().strip()
            if not query:
                return
            self._pin_search(query)
            render_pins()
            self.status.config(text=f"Pinned '{query}'.")

        ttk.Button(bar, text="Search", command=go).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Copy matching days for AI",
                  command=copy_matching).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="📌 Pin", command=pin_current).pack(
            side="left", padx=(6, 0))
        q.bind("<Return>", go)
        render_pins()

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

    def _energy_forecast_line(self, days=90):
        """Backlog #29: what today's capacity is LIKELY to be — not
        _capacity's PLANNED weekday hours, what your body's own recent
        data suggests you'll ACTUALLY have. "Last night's sleep" and
        "trailing sleep debt" combine into one honest signal: the
        3-night rolling average ending on a given day (that day's own
        last night plus the two before it) against your personal
        trailing-`days`-day median. Bucketed against your own WEEKDAY
        pattern (same weekday as today, same rolling-sleep tier — at/
        above your norm, or below it): the matching bucket's actual
        tracked-work range (25th-75th percentile band, not a single
        number) is the forecast: "today smells like a 3.5-4.5h day
        (Tuesday, running on debt, n=6) — plan the must-do inside
        that." Needs today's own rolling-sleep reading to speak at all
        (grounded in this morning's real data, not the calendar alone)
        and n≥5 matching historical days; silent otherwise — no
        forecast beats an unfounded one."""
        idx = day_index()
        cutoff = self.today - dt.timedelta(days=days)
        hist_sleep = []
        d = cutoff
        while d < self.today:
            s = self._sleep_h(d.isoformat())
            if s:
                hist_sleep.append(s)
            d += dt.timedelta(days=1)
        if len(hist_sleep) < 10:
            return None
        norm = sorted(hist_sleep)[len(hist_sleep) // 2]

        def rolling(iso):
            d0 = dt.date.fromisoformat(iso)
            vals = [self._sleep_h((d0 - dt.timedelta(days=i)).isoformat())
                   for i in range(3)]
            vals = [v for v in vals if v]
            return sum(vals) / len(vals) if len(vals) >= 2 else None

        today_roll = rolling(self.today.isoformat())
        if today_roll is None:
            return None
        rested = today_roll >= norm

        matched = []
        d = cutoff
        while d < self.today:
            iso = d.isoformat()
            if d.weekday() == self.today.weekday():
                rec = idx.get(iso)
                r = rolling(iso)
                if (rec and rec["work"] > 0 and r is not None
                        and (r >= norm) == rested):
                    matched.append(rec["work"] / 60)
            d += dt.timedelta(days=1)
        if len(matched) < 5:
            return None
        matched.sort()
        lo = matched[int(0.25 * (len(matched) - 1))]
        hi = matched[int(0.75 * (len(matched) - 1))]
        tag = "well-rested" if rested else "running on debt"
        return (f"today smells like a {lo:.1f}-{hi:.1f}h day "
               f"({self.today:%A}, {tag}, n={len(matched)}) — plan the "
               "must-do inside that")

    def _busy_data(self):
        """Calendar busy hours per date, cached on the resolved file's
        mtime. settings["ics_path"] may be a local .ics file
        (unchanged), a subscribe URL (resolve_ics_source fetches/
        caches it), or a local .csv (backlog #116 — Power Automate's
        export, always local/OneDrive-synced already, no fetching
        needed)."""
        raw = self.settings.get("ics_path")
        if not raw:
            return {}
        path = resolve_ics_source(raw)
        if not path or not os.path.exists(path):
            return {}
        key = (path, os.path.getmtime(path), dt.date.today().isoformat())
        cache = getattr(self, "_busy_cache", None)
        if cache and cache[0] == key:
            return cache[1]
        # two weeks back so the balance/summary views see past meetings too
        reader = csv_busy_data if path.lower().endswith(".csv") else parse_ics_busy
        data = reader(path, dt.date.today() - dt.timedelta(days=14),
                      dt.date.today() + dt.timedelta(days=90))
        self._busy_cache = (key, data)
        return data

    def _busy_intervals(self):
        """Calendar busy TIME RANGES per date — the interval-level
        sibling of _busy_data(), needed for slot-finding instead of just
        a daily total. Same sources (local .ics, subscribe URL, or
        Power Automate .csv — see resolve_ics_source and #116), same
        cache shape, own cache slot since the two views don't share a
        dict layout."""
        raw = self.settings.get("ics_path")
        if not raw:
            return {}
        path = resolve_ics_source(raw)
        if not path or not os.path.exists(path):
            return {}
        key = (path, os.path.getmtime(path), dt.date.today().isoformat())
        cache = getattr(self, "_busy_intervals_cache", None)
        if cache and cache[0] == key:
            return cache[1]
        reader = (parse_csv_busy_export if path.lower().endswith(".csv")
                 else parse_ics_intervals)
        data = reader(path, dt.date.today() - dt.timedelta(days=14),
                      dt.date.today() + dt.timedelta(days=90))
        self._busy_intervals_cache = (key, data)
        return data

    def _calendar_events(self, start, end):
        """Backlog #120: named calendar events for the week/month
        views — the display-layer sibling of _busy_intervals (which
        only needs times, not names, for capacity math). Same source
        dispatch (local .ics, subscribe URL, or Power Automate CSV) as
        _busy_intervals/_busy_data, just a richer parser. Not cached —
        these views are opened rarely, on demand, unlike the capacity
        math that runs on every refresh."""
        raw = self.settings.get("ics_path")
        if not raw:
            return []
        path = resolve_ics_source(raw)
        if not path or not os.path.exists(path):
            return []
        reader = (parse_csv_events if path.lower().endswith(".csv")
                 else parse_ics_events)
        return reader(path, start, end)

    def _work_sessions_by_day(self, start, end):
        """{date: [(start_time, end_time, task_name), ...]} — tracked
        work (not breaks) in [start, end], for the calendar view's own
        use. Plain read of read_rows(), not cached, same reasoning as
        _calendar_events."""
        out = {}
        for r in read_rows():
            try:
                d = dt.date.fromisoformat(r[0])
            except ValueError:
                continue
            if r[1] == "break" or not (start <= d <= end):
                continue
            try:
                sh, sm = map(int, r[2].split(":")[:2])
                eh, em = map(int, r[3].split(":")[:2])
                s, e = dt.time(sh, sm), dt.time(eh, em)
            except (ValueError, IndexError):
                continue
            if e <= s:
                continue
            out.setdefault(d, []).append((s, e, r[5] or "(untitled)"))
        return out

    def _work_window(self):
        """The daily envelope the free-slot finder is allowed to offer
        blocks within — configurable (Tools menu), defaults 08:00-22:00.
        Not the same concept as weekday capacity hours (_capacity): that
        caps TOTAL hours, this caps WHEN in the day they can land."""
        try:
            ws, we = self.settings.get("work_window", ["08:00", "22:00"])
            wsh, wsm = map(int, ws.split(":"))
            weh, wem = map(int, we.split(":"))
            return dt.time(wsh, wsm), dt.time(weh, wem)
        except (ValueError, TypeError):
            return dt.time(8, 0), dt.time(22, 0)

    def _logged_intervals(self, d):
        """Already-logged work+break time ranges for date d, read from
        the csv — so a same-day slot search doesn't re-offer hours
        already spent."""
        ivs = []
        for r in read_rows():
            if r[0] != d.isoformat():
                continue
            try:
                sh, sm = map(int, r[2].split(":"))
                eh, em = map(int, r[3].split(":"))
                ivs.append((dt.time(sh, sm), dt.time(eh, em)))
            except (ValueError, IndexError):
                continue
        return _merge_time_intervals(ivs)

    _WEEKDAY_ABBR = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4,
                     "sat": 5, "sun": 6}

    def _parse_weekdays(self, text):
        """Backlog #121: '' -> unrestricted (every day, None sentinel);
        'Mon-Fri' or 'Mon,Wed,Fri' -> {0,1,2,3,4}. Case-insensitive,
        first 3 letters of each weekday name. Malformed tokens are
        skipped, not fatal — same lenient-degrade shape as the HH:MM
        validation next to it."""
        text = (text or "").strip()
        if not text:
            return None
        days = set()
        for part in text.split(","):
            part = part.strip().lower()
            if "-" in part:
                a, b = (p.strip()[:3] for p in part.split("-", 1))
                a, b = self._WEEKDAY_ABBR.get(a), self._WEEKDAY_ABBR.get(b)
                if a is None or b is None:
                    continue
                d = a
                while True:
                    days.add(d)
                    if d == b:
                        break
                    d = (d + 1) % 7
            else:
                wd = self._WEEKDAY_ABBR.get(part[:3])
                if wd is not None:
                    days.add(wd)
        return days or None

    def _protected_intervals_named(self, d=None):
        """Backlog #50/#121: [(start, end, label), ...] — named
        recurring windows (lunch, wind-down, a day job, sleep...) on
        day `d`. `d` filters by weekday when a window declares one
        (`days`, e.g. "Mon-Fri"); omitted/blank `days` means every
        day — the original #50 behavior, unchanged, and what a caller
        gets by leaving `d` unset too. A window crossing midnight
        (sleep, 23:00-08:30) contributes to TWO calendar days — the
        tail of last night on `d`'s early morning, and the start of
        tonight on `d`'s late evening — both computed for whichever
        single day `d` is, since callers only ever ask about one day
        at a time. Malformed HH:MM entries are skipped rather than
        raising, so a bad manual edit degrades to "one window
        ignored," not a crash. Only treats start > end as a deliberate
        overnight window when the wrapped span is <=14h (generous for
        real sleep, but a typo like "15:00-14:00" — nearly 23h — stays
        treated as invalid, same as before this feature existed,
        rather than silently eating almost the whole day). `_protected_
        intervals` (below) is the plain-tuple version every interval-
        math caller actually uses; this labeled version exists for the
        calendar view (#120) to render WHAT a busy block actually is,
        not just when. Backlog #132: a window can also carry `skip`,
        a list of ISO dates it sits out entirely — one holiday off
        the Day job without editing (then re-editing back) the whole
        commitment, same one-condition-more shape as the weekday
        filter right above it."""
        out = []
        wd = d.weekday() if d is not None else None
        for w in self.settings.get("protected_windows", []):
            if d is not None and d.isoformat() in (w.get("skip") or []):
                continue
            days = self._parse_weekdays(w.get("days", ""))
            if days is not None and wd is not None and wd not in days:
                continue
            try:
                sh, sm = map(int, w["start"].split(":"))
                eh, em = map(int, w["end"].split(":"))
                s, e = dt.time(sh, sm), dt.time(eh, em)
            except (ValueError, KeyError, AttributeError, TypeError):
                continue
            label = w.get("label", "")
            if s < e:
                out.append((s, e, label))
            elif s > e:                        # possibly crosses midnight
                span_min = (24 * 60 - (s.hour * 60 + s.minute)) + (e.hour * 60 + e.minute)
                if span_min <= 14 * 60:
                    out.append((dt.time(0, 0), e, label))        # tail of last night
                    out.append((s, dt.time(23, 59, 59), label))  # start of tonight
        return out

    def _protected_intervals(self, d=None):
        """Backlog #50/#121: named recurring windows subtracted from
        _free_slots exactly like calendar busy-time already is, one
        more "busy" source merged into the same primitive — plain
        (start, end) tuples, no label. See _protected_intervals_named
        for the full behavior (weekday filter, midnight-crossing) and
        the labeled version."""
        return [(s, e) for s, e, _label in self._protected_intervals_named(d)]

    def _free_slots(self, d):
        """Free time-of-day ranges on date d: the work window minus
        calendar busy time minus protected windows (lunch, wind-down —
        backlog #50) minus (today only) already-logged work/break —
        the foundation piece v8's real time-blocked scheduler is built
        on. Returns [(start_time, end_time), ...]; slivers under 15 min
        are dropped so it reads as usable blocks, not calendar noise."""
        win_start, win_end = self._work_window()
        busy = list(self._busy_intervals().get(d.isoformat(), []))
        busy += self._protected_intervals(d)
        if d == dt.date.today():
            busy += self._logged_intervals(d)
        slots = _free_from_busy(win_start, win_end, busy)
        return [(s, e) for s, e in slots if _time_span_hours(s, e) >= 0.25]

    def _next_free_block_line(self):
        """One line that proves the interval math end to end: the
        biggest contiguous free block left today, calendar and
        already-logged time both subtracted. v8's scheduler reads the
        same _free_slots() this does — this is the smallest possible
        real exercise of it, not a demo."""
        slots = self._free_slots(self.today)
        if not slots:
            return None
        s, e = max(slots, key=lambda se: _time_span_hours(*se))
        return (f"biggest free block today: {s:%H:%M}-{e:%H:%M} "
                f"({_time_span_hours(s, e):.1f}h)")

    def _commitments_today_line(self):
        """Backlog #130: CLAUDE.md's own sacred rule — "every feature
        must leave a visible trace in the day file" — applied to
        #121's recurring commitments, which currently show up ONLY in
        the Tools editor and the week calendar view, never here. One
        line, reusing `_protected_intervals_named(self.today)` as-is;
        no new computation, just finally surfacing what #121 already
        knows in the one place this app's own rules say everything
        belongs. None on a day with nothing declared — an empty line
        would just be noise for anyone who's never used the feature."""
        by_label = {}
        for s, e, label in self._protected_intervals_named(self.today):
            if not label:
                continue
            by_label[label] = by_label.get(label, 0.0) + _time_span_hours(s, e)
        if not by_label:
            return None
        total = sum(by_label.values())
        parts = ", ".join(f"{label} {h:.1f}h" for label, h in by_label.items())
        return f"commitments today: {parts} ({total:.1f}h of 24h already spoken for)"

    def _lock_targets(self):
        """Backlog #135: widens #113/#122's lock-window pickers to also
        reach task-library items, not just Deadlines — closes the loop
        with #123's task due-dates ("this task is done by X" naturally
        continues into "let me lock time for it"). Deadlines keep
        their own real date range, unchanged; a task uses its own
        `due` if set, else a plain 7-day default window from today so
        an undated task is never unreachable — same fallback the
        backlog note itself proposed. `someday`-priority and blocked
        tasks are excluded: not yet actionable, so not worth
        cluttering a locking picker over. Returns dicts shaped like
        `_lock_window_candidates` already expects (`name`/`date`),
        plus `kind`/`has_due` for display only."""
        out = [{"kind": "deadline", "name": d["name"], "date": d.get("date"),
                "has_due": True} for d in self.deadlines()]
        for t in self.settings.get("tasks", []):
            if t.get("priority") == "someday" or t.get("blocked_by"):
                continue
            due = t.get("due")
            out.append({"kind": "task", "name": t["name"],
                        "date": due or (self.today + dt.timedelta(days=7)).isoformat(),
                        "has_due": bool(due)})
        return out

    def _lock_window_candidates(self, dl, min_hours=2.0):
        """Backlog #113: which specific upcoming days are actually worth
        locking for a deadline — the concrete next step after
        _capacity_lines' abstract "X hours needed" total. Walks every
        day from today through the deadline's due date, takes each
        day's single biggest contiguous free block (_free_slots — same
        primitive the scheduler and _next_free_block_line already use,
        so calendar busy time and protected windows are already priced
        in), and keeps days with at least `min_hours` in one sitting.
        Ranked biggest-block-first: a full open weekend day naturally
        outranks a fragmented weekday, the same way eyeballing a
        calendar would — no separate peak-hour weighting, deliberately
        kept simple."""
        try:
            due = dt.date.fromisoformat(dl["date"])
        except (KeyError, ValueError, TypeError):
            return []
        out = []
        d = self.today
        while d <= due:
            slots = self._free_slots(d)
            if slots:
                s, e = max(slots, key=lambda se: _time_span_hours(*se))
                hours = _time_span_hours(s, e)
                if hours >= min_hours:
                    out.append({"date": d, "start": s, "end": e, "hours": hours})
            d += dt.timedelta(days=1)
        out.sort(key=lambda w: -w["hours"])
        return out

    def _day_fragmentation_tax(self, meetings, win_start, win_end):
        """Backlog #21: the marginal deep-capacity cost of EACH meeting
        on one day, holding the others fixed — a 1h meeting at 13:00
        can cost far more than 1h if it splits a long open afternoon
        into two shards under the 90-minute deep-work threshold.
        Returns [(start, end, cost_hours), ...] for meetings whose
        removal would recover real capacity (>3 minutes; floating-
        point noise otherwise), most expensive first."""
        out = []
        for i, m in enumerate(meetings):
            others = meetings[:i] + meetings[i + 1:]
            with_m = _deep_capacity_minutes(
                _free_from_busy(win_start, win_end, meetings))
            without_m = _deep_capacity_minutes(
                _free_from_busy(win_start, win_end, others))
            cost = (without_m - with_m) / 60
            if cost > 0.05:
                out.append((m[0], m[1], cost))
        return sorted(out, key=lambda t: -t[2])

    def _meeting_fragmentation_lines(self, days=7):
        """Backlog #21: meetings cost more than their duration — they
        SPLIT open time. Pairs with the existing meeting-load insight
        (which only ever counted hours) by pricing the fragmentation
        itself: the worst single meeting this week plus the week's
        total 'fragmentation tax' (deep capacity — free blocks >=90m —
        recovered if that meeting simply weren't there). Needs a
        calendar configured (Tools > calendar sync) and at least one
        day with more than one meeting worth comparing; silent
        otherwise, same as the meeting-load insight it complements."""
        busy = self._busy_intervals()
        if not busy:
            return []
        win_start, win_end = self._work_window()
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        today_iso = self.today.isoformat()
        week_tax, worst = 0.0, None
        for iso, meetings in busy.items():
            if not (cutoff <= iso < today_iso) or len(meetings) < 1:
                continue
            for s, e, cost in self._day_fragmentation_tax(meetings, win_start, win_end):
                week_tax += cost
                if worst is None or cost > worst[3]:
                    worst = (iso, s, e, cost)
        if week_tax < 0.5 or worst is None:
            return []
        iso, s, e, cost = worst
        wd = dt.date.fromisoformat(iso).strftime("%A")
        return [f"{wd}'s {s:%H:%M} meeting: {_time_span_hours(s, e):.1f}h "
               f"long, cost {cost:.1f}h of deep capacity",
               f"meeting fragmentation tax this week: {week_tax:.1f}h"]

    # ----- right-now recommender (real-time companion to the day plan) -----

    def _deep_window(self, days=60):
        """Your best 3-hour block of the day, learned from history — the
        hours your work actually lands in. None until 20h are tracked."""
        by_hour, tot = [0] * 24, 0
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        for r in read_rows():
            if r[1] == "break" or r[0] < cutoff:
                continue
            try:
                h = int(r[2].split(":")[0]) % 24
                tot += int(r[4])
                by_hour[h] += int(r[4])
            except (ValueError, IndexError):
                continue
        if tot < 20 * 60:
            return None
        _best, h0 = max((sum(by_hour[h:h + 3]), h) for h in range(22))
        return (h0, h0 + 3)

    def _hour_quality(self, days=60):
        """A 0–1 score per hour of the day = how much of your work has
        historically landed in that hour, normalised. The scheduler uses
        it to steer hard work toward your peaks. None until 20h tracked."""
        by_hour, tot = [0] * 24, 0
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        for r in read_rows():
            if r[1] == "break" or r[0] < cutoff:
                continue
            try:
                h = int(r[2].split(":")[0]) % 24
                by_hour[h] += int(r[4])
                tot += int(r[4])
            except (ValueError, IndexError):
                continue
        if tot < 20 * 60:
            return None
        mx = max(by_hour) or 1
        return [x / mx for x in by_hour]

    _FOCUS_SIG_WD = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

    def _focus_signature_grid(self, days=180):
        """Backlog #53: hour-of-day × day-of-week, not either alone —
        the weekday-pattern insight (v7.4) collapses hours,
        `_hour_quality` (v8.8) collapses weekdays. Neither shows the
        actual 2D shape: WHEN, within which days, signal work reliably
        happens. For each (weekday, 4-hour bucket) cell: the fraction
        of that weekday's occurrences (over the trailing `days`) with
        ANY signal-matched work in that bucket — a CONSISTENCY score,
        not a raw total, so one unusually long day doesn't drown out
        the pattern. Needs real volume: a weekday needs 4+ occurrences
        in the window before its cells are included at all — the
        honesty gate a 2D grid needs before a cell means anything.
        Returns {(weekday, bucket): (hit_count, occurrence_count)} or
        None with no SIGNAL declared or nothing clears the gate."""
        kws = self._signal_kws()
        if not kws:
            return None
        cutoff = self.today - dt.timedelta(days=days - 1)
        occurrences = {}
        d = cutoff
        while d <= self.today:
            occurrences.setdefault(d.weekday(), set()).add(d)
            d += dt.timedelta(days=1)
        cutoff_iso, today_iso = cutoff.isoformat(), self.today.isoformat()
        hits = {}
        for r in read_rows():
            if r[1] == "break" or not (cutoff_iso <= r[0] <= today_iso):
                continue
            if not task_matches(r[5], kws):
                continue
            try:
                date = dt.date.fromisoformat(r[0])
                h = int(r[2].split(":")[0]) % 24
            except (ValueError, IndexError):
                continue
            hits.setdefault((date.weekday(), h // 4), set()).add(date)
        grid = {}
        for wd, dates in occurrences.items():
            n = len(dates)
            if n < 4:
                continue
            for bucket in range(6):
                grid[(wd, bucket)] = (len(hits.get((wd, bucket), set())), n)
        return grid or None

    def _focus_signature_line(self, days=180):
        """One line naming the standout cell(s) of the focus-signature
        grid — read once in a while, not a daily view. Silent unless
        the best cell clears a real consistency bar (≥50% of that
        weekday's occurrences)."""
        grid = self._focus_signature_grid(days)
        if not grid:
            return None

        def label(bucket):
            return f"{bucket * 4:02d}-{bucket * 4 + 4:02d}"

        best_key, (best_hits, best_n) = max(
            grid.items(), key=lambda kv: kv[1][0] / kv[1][1])
        best_pct = round(100 * best_hits / best_n)
        if best_pct < 50:
            return None
        wd, bucket = best_key
        line = (f"focus signature: {self._FOCUS_SIG_WD[wd]} {label(bucket)} "
               f"lights up {best_pct}% of the time (n={best_n})")
        worst_key, (worst_hits, worst_n) = min(
            grid.items(), key=lambda kv: kv[1][0] / kv[1][1])
        if worst_hits == 0 and worst_key != best_key:
            wwd, wbucket = worst_key
            line += (f"; {self._FOCUS_SIG_WD[wwd]} {label(wbucket)} never "
                    f"does (n={worst_n})")
        return line

    def _energy_place(self, items, slots, quality):
        """Assign free `slots` (time,time pairs) to `items` (most-urgent
        first). WITH an hour-quality profile each item claims its best-
        quality free time first — so the hardest/most-behind work lands in
        your peak hours and admin drifts to the troughs; WITHOUT one it's
        earliest-first (identical to the v8.0 behaviour). Blocks stay
        contiguous (we only reorder which slot is considered first, and cut
        from its front), so no fragmenting into scattered 15-min shards.
        Returns (placements, leftover): placements is
        [(name, behind, [(s,e)...], shortfall_h)]."""
        def slot_q(se):
            s, e = se
            n = max(1, int(round(_time_span_hours(s, e))))
            hrs = [(s.hour + i) % 24 for i in range(n)]
            return sum(quality[h] for h in hrs) / len(hrs) if quality else 0.0

        placements = []
        for name, left, need, behind in items:
            remaining, placed, leftover = need, [], []
            order = (sorted(slots, key=lambda se: (-slot_q(se), se[0]))
                     if quality else list(slots))
            for s, e in order:
                avail = _time_span_hours(s, e)
                if remaining <= 1e-9:
                    leftover.append((s, e))
                elif avail <= remaining + 1e-9:
                    placed.append((s, e))
                    remaining -= avail
                else:
                    cut = _add_hours(s, remaining)
                    placed.append((s, cut))
                    leftover.append((cut, e))
                    remaining = 0.0
            placed.sort(key=lambda se: se[0])
            placements.append((name, behind, placed, max(0.0, remaining)))
            slots = sorted(leftover, key=lambda se: se[0])
        return placements, slots

    def _recommend_now(self, now=None):
        """What to work on RIGHT NOW — the dynamic companion to the morning
        schedule. Reads the current hour against your learned deep-focus
        window, which deadline is most behind at real pace, today's energy,
        and the documented fatigue window, and states one clear pick.
        Rule-based, `now` injectable for testing."""
        now = now or dt.datetime.now()
        hour = now.hour
        behind = needy = None
        for dl in self.deadlines():
            try:
                p = self._dl_progress(dl)
            except (ValueError, KeyError):
                continue
            if not p.get("total_h") or p["left"] < 0 or p["remaining_h"] <= 0:
                continue
            proj = self._dl_projection(dl)
            if proj and proj["delta"] > 0 and (behind is None
                                               or proj["delta"] > behind[1]):
                behind = (dl["name"], proj["delta"])
            if needy is None or p["needed_per_day"] > needy[1]:
                needy = (dl["name"], p["needed_per_day"])
        if behind:
            target = f"{behind[0]} (~{behind[1]}d behind at real pace)"
        elif needy:
            target = f"{needy[0]} ({needy[1]:.1f}h/day needed)"
        else:
            sig = self._signal_kws()
            target = ("your signal (" + ", ".join(sig) + ")") if sig else None
        en = self._day_energy()
        note = (f" Energy's {en}/5 today — a lighter or shorter task beats "
                "forcing the hard one." if en and en <= 2 else "")
        if hour >= 22 or hour < 5:
            return ("It's late — sleep is the highest-leverage move now, not "
                    "more hours.")
        if 19 <= hour < 21:
            return ("You're in your 19–21 fatigue window — move or rest, don't "
                    "grind. Anything you force here you pay for tomorrow.")
        if 15 <= hour < 21 and (behind or needy):
            needed_today = sum(
                p["needed_per_day"] for dl in self.deadlines()
                for p in [self._dl_progress(dl)]
                if p.get("total_h") and p["left"] >= 0 and p["remaining_h"] > 0)
            tracked_today = (day_index().get(self.today.isoformat(),
                             {"work": 0})["work"]) / 60
            if needed_today > 0 and tracked_today < needed_today * 0.25:
                box = self._suggested_time_box() or 45
                name = behind[0] if behind else needy[0]
                return (f"salvage plan: one {box}m block on {name} before "
                        f"the day ends still makes it count — {tracked_today:.1f}h "
                        "so far doesn't have to stay there.")
        if not target:
            return ("Nothing scoped is behind — pick whatever moves a goal, "
                    "you're not firefighting." + note)
        dw = self._deep_window()
        if dw and dw[0] <= hour < dw[1]:
            return (f"You're inside your deep-focus window ({dw[0]:02d}–"
                    f"{dw[1]:02d}) — spend it on {target}, not admin." + note)
        if dw:
            return (f"Past your deep-focus window ({dw[0]:02d}–{dw[1]:02d}) — a "
                    f"good slot for admin/email; protect {target} for "
                    "tomorrow's peak." + note)
        return f"Best use of now: {target}." + note

    def _show_recommend_now(self):
        self.status.config(text="Now → " + self._recommend_now())

    def _set_ics(self):
        p = filedialog.askopenfilename(
            parent=self, filetypes=[("Calendar", "*.ics")],
            title="Exported calendar (.ics) — busy time reduces capacity")
        if not p:
            return
        self.settings["ics_path"] = p
        save_settings(self.settings)
        self._busy_cache = None
        self._busy_intervals_cache = None
        busy = self._busy_data()
        nxt14 = sum(h for iso, h in busy.items()
                    if iso <= (dt.date.today() + dt.timedelta(days=14)).isoformat())
        self.status.config(text=f"Calendar linked — {nxt14:.1f}h of meetings "
                                "in the next 14 days now reduce capacity.")

    def _set_ics_url(self):
        """Backlog #114: the other half of resolve_ics_source — a
        calendar's own publish/subscribe link (Outlook/Google's
        "Publish a calendar" URL) instead of a manual export every
        time. No login, no API key: the app just fetches the link
        periodically like a browser would. Validates by actually
        fetching before saving, so a bad link fails here with a clear
        message instead of silently going blank later."""
        url = simpledialog.askstring(
            APP_NAME, "Calendar publish/subscribe link (webcal:// or "
            "https://...ics) — from your calendar's Share/Publish "
            "settings, not the manual export file:", parent=self)
        if not url:
            return
        url = url.strip()
        fetch_url = ("https://" + url[len("webcal://"):]
                    if url.lower().startswith("webcal://") else url)
        try:
            with urllib.request.urlopen(fetch_url, timeout=10) as resp:
                sample = resp.read(4096)
        except (urllib.error.URLError, OSError, ValueError) as e:
            messagebox.showerror(
                APP_NAME, f"Couldn't fetch that link ({e}). Check it's a "
                "real publish/subscribe URL (not a login page) and that "
                "your calendar allows publishing.")
            return
        if b"BEGIN:VCALENDAR" not in sample:
            messagebox.showerror(
                APP_NAME, "That link didn't return a calendar file — "
                "double-check it's the publish/subscribe .ics link, not "
                "a regular calendar page URL.")
            return
        self.settings["ics_path"] = url
        resolve_ics_source(url, force=True)   # populate the cache for real use
        save_settings(self.settings)
        self._busy_cache = None
        self._busy_intervals_cache = None
        busy = self._busy_data()
        nxt14 = sum(h for iso, h in busy.items()
                    if iso <= (dt.date.today() + dt.timedelta(days=14)).isoformat())
        self.status.config(text=f"Calendar subscribed — {nxt14:.1f}h of "
                                "meetings in the next 14 days now reduce "
                                f"capacity. Refreshes every {ICS_REFRESH_MIN}min.")

    def _set_csv_busy(self):
        """Backlog #116: the fallback when #114's publish link isn't an
        option (a locked-down tenant with external sharing disabled) —
        a plain CSV (Start,End[,Subject] columns), meant to be kept
        current by an external no-code flow (Power Automate's standard
        Office 365 Outlook connector, synced to a local/OneDrive
        folder) rather than manually re-exported. Same settings key as
        the .ics path — one "calendar source" concept, dispatched by
        file extension in _busy_data/_busy_intervals."""
        p = filedialog.askopenfilename(
            parent=self, filetypes=[("Calendar CSV", "*.csv")],
            title="Calendar CSV (Start,End columns) — kept current by an "
                  "external sync, not re-picked manually each time")
        if not p:
            return
        data = csv_busy_data(p, dt.date.today(),
                             dt.date.today() + dt.timedelta(days=14))
        if not data:
            if not messagebox.askyesno(
                    APP_NAME, "No readable Start/End rows found in the next "
                    "14 days — the file may be empty, still the wrong "
                    "columns, or genuinely has no meetings soon. Use it "
                    "anyway?"):
                return
        self.settings["ics_path"] = p
        save_settings(self.settings)
        self._busy_cache = None
        self._busy_intervals_cache = None
        nxt14 = sum(data.values())
        self.status.config(text=f"Calendar CSV linked — {nxt14:.1f}h of "
                                "meetings in the next 14 days now reduce "
                                "capacity. Keep the external sync running "
                                "to stay current.")

    def _protected_hours(self, d=None):
        """Backlog #82/#121: total daily hours claimed by protected/
        recurring windows (lunch, wind-down, a day job, sleep...) on
        day `d` — same weekday-aware intervals _free_slots already
        subtracts from the scheduler, summed to a plain hour figure so
        _day_capacity's separate aggregate-hours model can subtract
        them too. Without this, declaring a lunch window stops the
        scheduler from booking over it but the capacity dashboard and
        cost-of-yes preview kept quietly counting that hour as
        available — two capacity models disagreeing."""
        return sum(_time_span_hours(s, e) for s, e in self._protected_intervals(d))

    def _day_capacity(self, d):
        """Net available hours on one date: weekday capacity minus
        calendar busy time minus protected/recurring windows; zero on
        off days."""
        if d.isoformat() in self.settings.get("off_dates", []):
            return 0.0
        return max(0.0, self._capacity()[d.weekday()]
                   - self._busy_data().get(d.isoformat(), 0.0)
                   - self._protected_hours(d))

    def _avail_hours(self, until):
        """Net capacity hours from today through `until` (inclusive)."""
        d, total = dt.date.today(), 0.0
        while d <= until:
            total += self._day_capacity(d)
            d += dt.timedelta(days=1)
        return total

    def _due_date_feasibility_line(self, due_date, est_h=None):
        """Backlog #124: an honest, non-blocking check for whether a
        due date set on a task (or a deadline) still has real room
        before it, given everything already declared — commitments
        (#121), imported calendar events (#114/#116), other locked
        windows (#113) — all already netted into _avail_hours, no new
        capacity math. Compares against `est_h` when the task actually
        has one; without an estimate there's nothing to honestly call
        "impossible," so it only speaks up when the total free time is
        near zero regardless. Returns None when things look fine —
        never a reason to block the save, matching the standing
        no-gating precedent (#9)."""
        avail = self._avail_hours(due_date)
        if est_h and est_h > 0:
            slack = avail - est_h
            if slack < 0:
                return (f"⚠ only {avail:.1f}h of real free time before "
                       f"{due_date:%d.%m} — {est_h:g}h estimated, "
                       f"{-slack:.1f}h short")
            return None
        if avail < 2.0:
            return f"⚠ only {avail:.1f}h of real free time before {due_date:%d.%m}"
        return None

    def _capacity_lines(self):
        """The honest verdict: available hours vs deadline demand. When
        overbooked, also states a priority order — most-urgent-first
        allocation of the same shared pool the aggregate check already
        uses — so "cut scope" becomes "cut THIS, by THIS much" instead of
        a number with no owner. Plain arithmetic over numbers already
        computed elsewhere (_dl_progress, _avail_hours), not a new
        scheduling model — see HANDOFF.md's planning-engine backlog entry
        for why a real per-window allocation is a bigger, separate task."""
        lines, items, far = [], [], None
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
            items.append((dl["name"], p["left"], req))
            far = max(far or p["due"], p["due"])
        if len(items) > 1 and far:
            avail = self._avail_hours(far)
            total_req = sum(x[2] for x in items)
            slack = avail - total_req
            lines.append("")
            if slack >= 0:
                lines.append(f" ALL deadlines together: {total_req:.1f}h needed, "
                             f"{avail:.1f}h available → {slack:.1f}h of real slack."
                             " The friend on Tuesday is fine.")
            else:
                lines.append(f" ⚠ ALL deadlines together: {total_req:.1f}h needed "
                             f"but only {avail:.1f}h available → overbooked by "
                             f"{-slack:.1f}h. Cut scope or say no to something.")
                lines.append(" priority order (most urgent first — cut from")
                lines.append(" the bottom, not the top):")
                remaining = avail
                for name, left, req in sorted(items, key=lambda x: x[1]):
                    if remaining >= req:
                        lines.append(f"   ✓ {name} ({left}d left) — fully "
                                     f"funded, {req:.1f}h")
                        remaining -= req
                    elif remaining > 0:
                        lines.append(f"   ⚠ {name} ({left}d left) — only "
                                     f"{remaining:.1f}h of {req:.1f}h fits, "
                                     f"short {req - remaining:.1f}h")
                        remaining = 0
                    else:
                        lines.append(f"   ✗ {name} ({left}d left) — 0h fits; "
                                     f"the full {req:.1f}h is the cut")
        real = self._reallocation_line()
        if real:
            lines.append("")
            lines.append(f" {real}")
        return lines

    def _cost_of_yes_line(self, hypothetical, existing=None):
        """Backlog #52: every capacity view looks at deadlines already
        on the books — nothing shows what ADDING one would do before
        you commit. `hypothetical` is a deadline-shaped dict
        (name/date/total_h) that doesn't have to be saved yet; reuses
        the exact aggregate-slack math `_capacity_lines` already runs
        for real deadlines, just against a pool with one more in it.
        `existing` defaults to the real saved deadlines but can be
        overridden (the edit dialog passes the saved list explicitly
        so a live preview isn't thrown off by its own unsaved edits).
        None for missing/invalid input — a preview needs both a real
        date and a real scope to mean anything."""
        try:
            due = dt.date.fromisoformat(hypothetical["date"])
            total_h = float(hypothetical.get("total_h") or 0)
        except (ValueError, KeyError, TypeError):
            return None
        if total_h <= 0 or due < self.today:
            return None
        items, far = [], due
        for dl in self.deadlines() if existing is None else existing:
            try:
                p = self._dl_progress(dl)
            except (ValueError, KeyError):
                continue
            if p["left"] < 0 or not p.get("total_h"):
                continue
            items.append((dl["name"], p["left"], p["remaining_h"]))
            far = max(far, p["due"])
        avail = self._avail_hours(far)
        req_before = sum(x[2] for x in items)
        slack_before = avail - req_before
        slack_after = avail - (req_before + total_h)
        name = hypothetical.get("name") or "this"
        line = (f"committing to '{name}' would push slack from "
               f"{slack_before:+.1f}h to {slack_after:+.1f}h")
        if slack_after < 0 and items:
            worst_name, worst_left, worst_req = max(items, key=lambda x: x[1])
            give = min(worst_req, -slack_after)
            per_day = give / max(worst_left, 1)
            line += (f" — {worst_name} would need to give up "
                    f"{per_day:.1f}h/day to make room")
        goal = hypothetical.get("goal")
        if goal:
            blocked = [t for t in self.settings.get("tasks", [])
                      if t.get("goal") == goal and t.get("blocked_by")]
            if blocked:
                line += (f" — heads up: {len(blocked)} task(s) under "
                        f"'{goal}' are already blocked")
        return line

    def _reallocation_line(self):
        """Backlog #59: the natural sequel to #47 (done) — not just WHY
        a deadline is behind (capacity vs choice) but WHAT SPECIFICALLY
        would fix a genuine TODAY capacity problem, when 2+ deadlines
        compete. One arithmetic scenario, not a directive: redistributes
        today's shortfall from the most-urgent item onto the least-
        urgent one and states the trade plainly. Reuses _focus_items'
        own ranking and _day_capacity — no new data."""
        items = self._focus_items()
        if len(items) < 2:
            return None
        name_m, left_m, need_m, behind_m = items[0]
        name_l, left_l, need_l, behind_l = items[-1]
        if not behind_m or name_m == name_l:
            return None
        avail = self._day_capacity(self.today)
        total_need = sum(x[2] for x in items)
        if avail >= total_need - 0.05 or need_l <= 0.05:
            return None
        shortfall = total_need - avail
        cut = min(need_l, shortfall)
        if cut < 0.2:
            return None
        return (f"reallocation: cutting {name_l} to "
                f"{max(0.0, need_l - cut):.1f}h/day (from {need_l:.1f}h) "
                f"for now would free {cut:.1f}h/day for {name_m} — one way "
                "to close the gap, not the only one.")

    def _status_update_text(self, dl):
        """Backlog #57: a DIFFERENT REGISTER on purpose — this is the
        one surface meant to sound like something you'd paste into an
        email to an actual supervisor/advisor, not the rest of the
        app's blunt internal voice. Reuses _dl_progress/_dl_projection's
        own numbers and v8.60's blocked_by field — no new computation,
        no new data source. None for an unscoped deadline (total_h) —
        nothing meaningful to report externally."""
        try:
            p = self._dl_progress(dl)
        except (ValueError, KeyError):
            return None
        if not p.get("total_h"):
            return None
        mon = self.today - dt.timedelta(days=self.today.weekday())
        prev_mon = mon - dt.timedelta(days=7)
        kws = self._match_kws(dl.get("match", ""))
        if kws:
            this_week_h = matched_minutes(kws, mon, self.today) / 60
            last_week_h = matched_minutes(
                kws, prev_mon, mon - dt.timedelta(days=1)) / 60
        else:
            idx = day_index()
            this_week_h = sum(
                rec["work"] for iso, rec in idx.items()
                if mon.isoformat() <= iso <= self.today.isoformat()) / 60
            last_week_h = sum(
                rec["work"] for iso, rec in idx.items()
                if prev_mon.isoformat() <= iso < mon.isoformat()) / 60
        trend = (f" (up from {last_week_h:.0f}h last)"
                if this_week_h > last_week_h else
                f" (down from {last_week_h:.0f}h last)"
                if this_week_h < last_week_h else "")
        text = (f"Progress update — {dl['name']}: {this_week_h:.0f}h "
               f"this week{trend}.")
        credit = self._milestone_credit(dl)
        milestone_now = credit["current"] if credit else None
        proj = self._dl_projection(dl)
        if milestone_now:
            text += f" Currently on {milestone_now[0]} ({milestone_now[1]}% of its hours)."
        elif proj:
            if proj["delta"] <= 0:
                text += f" On pace to finish by {proj['land']:%B %d}."
            else:
                text += (f" Currently projected {proj['delta']}d behind "
                        f"pace, landing {proj['land']:%B %d}.")
        blockers = [t["name"] for t in self.settings.get("tasks", [])
                   if t.get("deadline") == dl["name"] and t.get("blocked_by")]
        text += (f" Blocked on: {', '.join(blockers)}." if blockers
                else " No blockers.")
        return text

    def _status_update_all(self):
        """All scoped deadlines' status paragraphs, blank-line
        separated — the clipboard payload for "Copy status update"."""
        texts = [t for dl in self.deadlines()
                for t in [self._status_update_text(dl)] if t]
        return "\n\n".join(texts)

    def _outlook_lines(self):
        """Forward simulation across ALL scoped deadlines at REAL pace —
        the complement to _capacity_lines (which compares abstract
        available capacity to needed hours). This asks the harder
        question: at the pace you're ACTUALLY keeping, which deadlines
        land late, in what order, and what's the smallest lever that
        changes it. Prediction + prescription, not a mirror. Pure math
        over _dl_progress + _dl_projection (v8.1); no new data."""
        scoped = []
        for dl in self.deadlines():
            try:
                p = self._dl_progress(dl)
            except (ValueError, KeyError):
                continue
            if not p.get("total_h") or p["left"] < 0 or p["remaining_h"] <= 0:
                continue
            scoped.append((dl, p, self._dl_projection(dl)))
        if not scoped:
            return []
        late, ok, blind = [], [], []
        for dl, p, proj in sorted(scoped, key=lambda x: x[1]["due"]):
            if proj is None:
                blind.append((dl, p))
            elif proj["delta"] > 0:
                late.append((dl, p, proj))
            else:
                ok.append((dl, p, proj))
        seen = len(late) + len(ok)
        lines = []
        if late:
            lines.append(f"at your real recent pace, {len(late)} of {seen} "
                         "tracked deadline(s) land LATE:")
            for dl, p, proj in sorted(late, key=lambda x: -x[2]["delta"]):
                lever = (f"  ·  +1h/day → {proj['sooner']}d sooner"
                         if proj["sooner"] else "")
                lines.append(f"  ⚠ {dl['name']}: due {p['due']:%d.%m}, "
                             f"lands ~{proj['land']:%d.%m} "
                             f"({proj['delta']}d late) at "
                             f"{proj['rate'] * 7:.1f}h/wk actual{lever}")
            gap = sum(max(0.0, p["needed_per_day"] - proj["rate"])
                      for _dl, p, proj in late)
            if gap > 0.1:
                lines.append(f"  → landing all of them on time needs about "
                             f"+{gap:.1f}h/day more than you're averaging on "
                             "them now — or move a due date, or cut a scope")
        elif seen:
            lines.append(f"at your real recent pace, all {seen} tracked "
                         "deadline(s) land on time. ✓")
        for dl, p, proj in ok:
            lines.append(f"  ✓ {dl['name']}: due {p['due']:%d.%m}, "
                         f"on/ahead of pace (~{proj['land']:%d.%m})")
        for dl, p in blind:
            lines.append(f"  · {dl['name']}: due {p['due']:%d.%m}, needs "
                         f"{p['needed_per_day']:.1f}h/day — too little recent "
                         "tracked time to project a real pace yet")
        return lines

    def _day_forecast(self, days=21):
        """Backlog #118: per-day free-time forecast — the same
        _free_slots primitive #113's lock-window picker uses, but for
        every upcoming day (not filtered to one deadline's date
        range), so it's a general-purpose "what does my calendar
        actually look like" glance. Returns [(date, free_slots,
        free_hours), ...], today first."""
        win_start, win_end = self._work_window()
        out = []
        d = self.today
        for _ in range(days):
            slots = self._free_slots(d)
            free_h = sum(_time_span_hours(s, e) for s, e in slots)
            out.append((d, slots, free_h))
            d += dt.timedelta(days=1)
        return out

    def _draw_forecast_bars(self, cv, rows):
        cv.delete("all")
        win_start, win_end = self._work_window()
        win_span = _time_span_hours(win_start, win_end)
        pad_l, pad_r, row_h, bar_w = 92, 56, 20, 380
        W = pad_l + bar_w + pad_r
        for i, (d, slots, free_h) in enumerate(rows):
            y = 6 + i * row_h
            weekend = d.weekday() >= 5
            label_color = "#000000" if weekend else "#444444"
            if d == self.today:
                label_color = "#2e6da4"
            cv.create_text(6, y + row_h / 2, anchor="w",
                           text=f"{d:%a %d.%m}", fill=label_color,
                           font=("Segoe UI", 9, "bold" if weekend else "normal"))
            cv.create_rectangle(pad_l, y + 2, pad_l + bar_w, y + row_h - 4,
                                fill="#e4e7ec", outline="")
            for s, e in slots:
                x0 = pad_l + bar_w * (_time_span_hours(win_start, s) / win_span)
                x1 = pad_l + bar_w * (_time_span_hours(win_start, e) / win_span)
                cv.create_rectangle(x0, y + 2, max(x1, x0 + 1), y + row_h - 4,
                                    fill="#5fa85f", outline="")
            cv.create_text(pad_l + bar_w + 8, y + row_h / 2, anchor="w",
                           text=f"{free_h:.1f}h", fill="#555555",
                           font=("Segoe UI", 9))
        cv.create_text(pad_l, 6 + len(rows) * row_h + 6, anchor="nw",
                       text=f"{win_start:%H:%M}", fill="#999999",
                       font=("Segoe UI", 7))
        cv.create_text(pad_l + bar_w, 6 + len(rows) * row_h + 6, anchor="ne",
                       text=f"{win_end:%H:%M}", fill="#999999",
                       font=("Segoe UI", 7))
        cv.config(width=W, height=6 + len(rows) * row_h + 22)

    def _forecast_win(self):
        """Backlog #118 (owner's own ask, 2026-08-07: "calendar view...
        very simple... easier to visually inspect free slots"). Green
        = free (calendar busy time + protected windows already
        subtracted, via _free_slots — the same math #113's lock-window
        picker and the scheduler both already use), grey = busy or
        outside the work window. Deliberately just a glance, no
        actions here — #113 already covers "pick and lock windows for
        a deadline" as its own flow."""
        win = tk.Toplevel(self)
        win.title("Free-time forecast — next 3 weeks")
        rows = self._day_forecast(21)
        cv = tk.Canvas(win, background="white", highlightthickness=0)
        cv.pack(padx=8, pady=8)
        self._draw_forecast_bars(cv, rows)
        ttk.Label(win, text="green = free · grey = busy/outside work hours",
                 foreground="#777777").pack(anchor="w", padx=8, pady=(0, 8))

    @staticmethod
    def _cal_truncate(text, max_px, px_per_char=5.3):
        max_chars = max(3, int(max_px / px_per_char))
        return text if len(text) <= max_chars else text[:max_chars - 1] + "…"

    _CAL_HOUR_START, _CAL_HOUR_END = 7, 23   # displayed range, week view
    _CAL_WEEK_HDR_H, _CAL_WEEK_PAD_L = 26, 46   # backlog #122: shared with
    _CAL_WEEK_COL_W, _CAL_WEEK_HOUR_H = 96, 26  # _week_click_to_slot below,
                                                 # so a right-click inverts
                                                 # exactly the same layout
                                                 # _draw_calendar_week uses
    _CAL_MONTH_CELL_W, _CAL_MONTH_CELL_H = 104, 78   # backlog #123: shared
    _CAL_MONTH_HDR_H, _CAL_MONTH_PAD = 20, 4         # with _month_click_to_day

    def _draw_calendar_week(self, cv, monday):
        """Backlog #120 (owner's own ask, 2026-08-07: "proper monthly
        or weekly calendar views... event or stuff names there...
        similar to outlooks monthly setup... exact time slots"). An
        hour-gridded week, 7 day columns — real Outlook-week shape.
        Three layers, drawn back to front: recurring commitments
        (#121 — sleep, day job, admin, neutral tan) as background
        context, then calendar events (named, from _calendar_events)
        and tracked work sessions (named, from _work_sessions_by_day)
        on top — all positioned by real clock time, not just counted."""
        cv.delete("all")
        days = [monday + dt.timedelta(days=i) for i in range(7)]
        hdr_h, pad_l, col_w = (self._CAL_WEEK_HDR_H, self._CAL_WEEK_PAD_L,
                               self._CAL_WEEK_COL_W)
        hours = self._CAL_HOUR_END - self._CAL_HOUR_START
        hour_h = self._CAL_WEEK_HOUR_H
        W = pad_l + 7 * col_w
        H = hdr_h + hours * hour_h
        cv.config(width=W, height=H)

        def y_for(t):
            mins = max(0, min(hours * 60,
                              t.hour * 60 + t.minute - self._CAL_HOUR_START * 60))
            return hdr_h + hour_h * hours * mins / (hours * 60)

        for h in range(hours + 1):
            y = hdr_h + h * hour_h
            cv.create_line(pad_l, y, W, y, fill="#e5e5e5")
            if h < hours:
                cv.create_text(4, y + 2, anchor="nw",
                               text=f"{self._CAL_HOUR_START + h:02d}:00",
                               font=("Segoe UI", 7), fill="#999999")

        events = self._calendar_events(monday, monday + dt.timedelta(days=6))
        ev_by_day = {}
        for d, s, e, summary in events:
            ev_by_day.setdefault(d, []).append((s, e, summary))
        work_end = min(monday + dt.timedelta(days=6), self.today)
        work_by_day = (self._work_sessions_by_day(monday, work_end)
                      if work_end >= monday else {})

        for i, d in enumerate(days):
            x0 = pad_l + i * col_w
            weekend = d.weekday() >= 5
            cv.create_rectangle(x0, 0, x0 + col_w, hdr_h,
                                fill="#e4e7ec" if weekend else "#eef1f5",
                                outline="")
            cv.create_text(x0 + col_w / 2, hdr_h / 2, text=f"{d:%a %d.%m}",
                           fill="#2e6da4" if d == self.today else "#333333",
                           font=("Segoe UI", 8, "bold"))
            cv.create_line(x0, 0, x0, H, fill="#eeeeee")
            for s, e, label in self._protected_intervals_named(d):
                y0, y1 = y_for(s), max(y_for(e), y_for(s) + 9)
                cv.create_rectangle(x0 + 2, y0, x0 + col_w - 2, y1,
                                    fill=self.CAL_COMMIT, outline="")
                if label:
                    cv.create_text(x0 + 4, y0 + 1, anchor="nw",
                                   text=self._cal_truncate(label, col_w - 6),
                                   font=("Segoe UI", 6), fill="#555544")
            for s, e, name in ev_by_day.get(d, []):
                y0, y1 = y_for(s), max(y_for(e), y_for(s) + 11)
                cv.create_rectangle(x0 + 2, y0, x0 + col_w - 2, y1,
                                    fill=self.CAL_EVENT, outline="")
                cv.create_text(x0 + 4, y0 + 1, anchor="nw",
                               text=self._cal_truncate(f"{s:%H:%M} {name}",
                                                       col_w - 6),
                               font=("Segoe UI", 6), fill="white")
            for s, e, name in work_by_day.get(d, []):
                y0, y1 = y_for(s), max(y_for(e), y_for(s) + 9)
                cv.create_rectangle(x0 + 2, y0, x0 + col_w - 2, y1,
                                    fill=self.CAL_WORK, outline="")
                cv.create_text(x0 + 4, y0 + 1, anchor="nw",
                               text=self._cal_truncate(f"{s:%H:%M} {name}",
                                                       col_w - 6),
                               font=("Segoe UI", 6), fill="white")
        cv.create_line(pad_l, 0, pad_l, H, fill="#cccccc")

    def _week_click_to_slot(self, x, y, monday):
        """Backlog #122: the inverse of _draw_calendar_week's own
        layout math — a canvas click (x, y) -> (date, hour_start,
        hour_end), snapped to the hour cell it landed in. None if the
        click was outside the grid (the header row, or past the last
        day column) — right-clicking there does nothing, not a
        confusing menu with no real target."""
        if y < self._CAL_WEEK_HDR_H or x < self._CAL_WEEK_PAD_L:
            return None
        col = int((x - self._CAL_WEEK_PAD_L) // self._CAL_WEEK_COL_W)
        if not (0 <= col <= 6):
            return None
        hours = self._CAL_HOUR_END - self._CAL_HOUR_START
        hour_idx = int((y - self._CAL_WEEK_HDR_H) // self._CAL_WEEK_HOUR_H)
        if not (0 <= hour_idx < hours):
            return None
        d = monday + dt.timedelta(days=col)
        h = self._CAL_HOUR_START + hour_idx
        h_end, m_end = (h + 1, 0) if h + 1 < 24 else (23, 59)
        return d, dt.time(h, 0), dt.time(h_end, m_end)

    @staticmethod
    def _cal_shade_color(ratio, target=(0xe4, 0xf5, 0xe4)):
        """Backlog #131: white (busy) -> light green (free), ratio in
        [0, 1] — a plain linear blend, no new color math beyond what
        every other tinted-cell view in this app already does (the
        heatmap, the day timeline)."""
        ratio = max(0.0, min(1.0, ratio))
        r = round(255 - ratio * (255 - target[0]))
        g = round(255 - ratio * (255 - target[1]))
        b = round(255 - ratio * (255 - target[2]))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _draw_calendar_month(self, cv, year, month):
        """Backlog #120/#131: a real month grid — date numbers, up to a
        few event/work-session names per cell before collapsing to
        "+N more", same shape as Outlook's own month view. Cell
        background is now a light green-to-white shade by that day's
        real `_day_capacity` (the same number #118's free-time
        forecast and #113's lock-window candidates already use) —
        one glance answers both "what's on" and "how open is it,"
        instead of needing #118's separate window for the second
        question."""
        cv.delete("all")
        first = dt.date(year, month, 1)
        start_col = first.weekday()
        next_month = (dt.date(year + 1, 1, 1) if month == 12
                     else dt.date(year, month + 1, 1))
        days_in_month = (next_month - first).days
        weeks = -(-(start_col + days_in_month) // 7)

        cell_w, cell_h, hdr_h, pad = (self._CAL_MONTH_CELL_W, self._CAL_MONTH_CELL_H,
                                      self._CAL_MONTH_HDR_H, self._CAL_MONTH_PAD)
        W = pad * 2 + 7 * cell_w
        H = hdr_h + pad * 2 + weeks * cell_h
        cv.config(width=W, height=H)

        for i, wd in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            cv.create_text(pad + i * cell_w + cell_w / 2, hdr_h / 2, text=wd,
                           font=("Segoe UI", 8, "bold"), fill="#666666")

        range_end = next_month - dt.timedelta(days=1)
        events = self._calendar_events(first, range_end)
        ev_by_day = {}
        for d, s, e, summary in events:
            ev_by_day.setdefault(d, []).append((s, summary))
        work_end = min(range_end, self.today)
        work_by_day = (self._work_sessions_by_day(first, work_end)
                      if work_end >= first else {})
        due_by_day = {}
        for t in self.settings.get("tasks", []):
            due = t.get("due")
            if not due:
                continue
            try:
                dd = dt.date.fromisoformat(due)
            except ValueError:
                continue
            if first <= dd <= range_end:
                due_by_day.setdefault(dd, []).append(t["name"])

        for day_num in range(1, days_in_month + 1):
            d = dt.date(year, month, day_num)
            idx = start_col + day_num - 1
            row, col = idx // 7, idx % 7
            x0, y0 = pad + col * cell_w, hdr_h + pad + row * cell_h
            if d == self.today:
                bg = "#eaf2fb"
            else:
                bg = self._cal_shade_color(self._day_capacity(d) / 8.0)
            cv.create_rectangle(x0, y0, x0 + cell_w, y0 + cell_h, fill=bg,
                                outline="#e0e0e0")
            cv.create_text(x0 + 4, y0 + 2, anchor="nw", text=str(day_num),
                           font=("Segoe UI", 8, "bold" if d == self.today
                                 else "normal"),
                           fill="#2e6da4" if d == self.today else "#333333")
            line_y = y0 + 16
            due_color = "#c0392b" if d < self.today else "#b8621b"
            for name in due_by_day.get(d, []):
                if line_y > y0 + cell_h - 9:
                    break
                cv.create_text(x0 + 4, line_y, anchor="nw",
                               text=self._cal_truncate(f"⚑ {name}",
                                                       cell_w - 8),
                               font=("Segoe UI", 6, "bold"), fill=due_color)
                line_y += 10
            items = sorted(ev_by_day.get(d, []) +
                          [(s, n) for s, e, n in work_by_day.get(d, [])])
            shown = 0
            for s, name in items:
                if line_y > y0 + cell_h - 9:
                    break
                cv.create_text(x0 + 4, line_y, anchor="nw",
                               text=self._cal_truncate(f"{s:%H:%M} {name}",
                                                       cell_w - 8),
                               font=("Segoe UI", 6), fill=self.CAL_EVENT)
                line_y += 10
                shown += 1
            remaining = len(items) - shown
            if remaining > 0:
                cv.create_text(x0 + 4, line_y, anchor="nw",
                               text=f"+{remaining} more",
                               font=("Segoe UI", 6), fill="#999999")

    def _month_click_to_day(self, x, y, year, month):
        """Backlog #123: the inverse of _draw_calendar_month's own
        cell layout — a canvas click (x, y) -> the calendar date it
        landed in, or None outside the grid or past the month's real
        days (the trailing empty cells in the last week row)."""
        first = dt.date(year, month, 1)
        start_col = first.weekday()
        next_month = (dt.date(year + 1, 1, 1) if month == 12
                     else dt.date(year, month + 1, 1))
        days_in_month = (next_month - first).days
        cell_w, cell_h, hdr_h, pad = (self._CAL_MONTH_CELL_W, self._CAL_MONTH_CELL_H,
                                      self._CAL_MONTH_HDR_H, self._CAL_MONTH_PAD)
        if y < hdr_h + pad or x < pad:
            return None
        col = int((x - pad) // cell_w)
        row = int((y - hdr_h - pad) // cell_h)
        if not (0 <= col <= 6) or row < 0:
            return None
        day_num = row * 7 + col - start_col + 1
        if not (1 <= day_num <= days_in_month):
            return None
        return dt.date(year, month, day_num)

    def _calendar_view_win(self):
        """Backlog #120/#122/#123/#135: the Outlook-like detailed
        calendar, week/month toggle. Two right-click actions, split by
        the granularity each view actually has: in WEEK view, right-
        click an hour cell to lock it for a deadline OR a task (#122,
        widened by #135 — reuses #113's lock_windows_to_ics unchanged);
        in MONTH view, right-click a
        day cell to set a task's due date (#123 — a lightweight,
        Deadline-object-free "done by" marker, deliberately not a
        full scoped Deadline, so quick ad-hoc due dates don't clutter
        the deadlines list). Everything else here stays read-only,
        same standing guardrail as every other planning view."""
        win = tk.Toplevel(self)
        win.title("Calendar")
        top = ttk.Frame(win)
        top.pack(fill="x", padx=8, pady=8)
        mode_var = tk.StringVar(value="week")
        state = {"anchor": self.today}

        def render():
            if mode_var.get() == "week":
                monday = state["anchor"] - dt.timedelta(
                    days=state["anchor"].weekday())
                self._draw_calendar_week(cv, monday)
                title_lbl.config(text=f"Week of {monday:%d.%m.%Y}")
            else:
                self._draw_calendar_month(cv, state["anchor"].year,
                                          state["anchor"].month)
                title_lbl.config(text=f"{state['anchor']:%B %Y}")

        def nav(delta):
            if mode_var.get() == "week":
                state["anchor"] += dt.timedelta(days=7 * delta)
            else:
                y, m = state["anchor"].year, state["anchor"].month + delta
                if m < 1:
                    y, m = y - 1, 12
                elif m > 12:
                    y, m = y + 1, 1
                state["anchor"] = state["anchor"].replace(year=y, month=m, day=1)
            render()

        def go_today():
            state["anchor"] = self.today
            render()

        def lock_slot(dl_name, d, s, e):
            path, n = lock_windows_to_ics(dl_name, [{"date": d, "start": s,
                                                     "end": e}])
            self._append_text(f"--- Locked {s:%H:%M}-{e:%H:%M} {d:%d.%m} for "
                              f"{dl_name} (exported {os.path.basename(path)})")
            self.status.config(text=f"Locked {s:%H:%M}-{e:%H:%M} on {d:%d.%m} "
                                    f"for {dl_name} — exported {path}")

        def set_task_due(name, d):
            est_h = None
            for t in self.settings.get("tasks", []):
                if t["name"] == name:
                    t["due"] = d.isoformat()
                    est_h = t.get("est_h")
                    break
            else:
                return
            save_settings(self.settings)
            trace = f"--- Task due date set: '{name}' due {d:%d.%m.%Y}"
            status = f"'{name}' due {d:%d.%m.%Y}"
            feasibility = self._due_date_feasibility_line(d, est_h)
            if feasibility:
                trace += f" ({feasibility})"
                status += f" — {feasibility}"
            self._append_text(trace)
            self.status.config(text=status)
            render()

        def pick_task_due(d):
            names = [t["name"] for t in self.settings.get("tasks", [])]
            if not names:
                messagebox.showinfo(APP_NAME, "No tasks in the library yet — "
                                    "type TODO: anywhere in a day file first.",
                                    parent=win)
                return
            pop = tk.Toplevel(win)
            pop.title("Set task due date")
            pop.resizable(False, False)
            pop.grab_set()
            ttk.Label(pop, text=f"Due {d:%A %d.%m.%Y}:").grid(
                row=0, column=0, padx=8, pady=(8, 2), sticky="w")
            var = tk.StringVar()
            ttk.Combobox(pop, textvariable=var, state="readonly", values=names,
                        width=50).grid(row=1, column=0, padx=8, pady=(0, 8))

            def ok():
                if var.get():
                    set_task_due(var.get(), d)
                pop.destroy()

            ttk.Button(pop, text="Set", command=ok).grid(
                row=2, column=0, pady=(0, 8))

        def on_right_click(event):
            if mode_var.get() == "week":
                monday = state["anchor"] - dt.timedelta(
                    days=state["anchor"].weekday())
                slot = self._week_click_to_slot(event.x, event.y, monday)
                if not slot:
                    return
                d, s, e = slot
                targets = self._lock_targets()
                menu = tk.Menu(win, tearoff=0)
                if not targets:
                    menu.add_command(
                        label="No deadlines or tasks set yet",
                        state="disabled")
                else:
                    for tgt in targets:
                        menu.add_command(
                            label=f"Lock {s:%H:%M}–{e:%H:%M} {d:%a %d.%m} "
                                 f"for '{tgt['name']}'",
                            command=lambda tgt=tgt: lock_slot(tgt["name"], d, s, e))
                menu.tk_popup(event.x_root, event.y_root)
            else:
                d = self._month_click_to_day(event.x, event.y,
                                             state["anchor"].year,
                                             state["anchor"].month)
                if not d:
                    return
                menu = tk.Menu(win, tearoff=0)
                menu.add_command(label=f"Set task due date to {d:%a %d.%m}…",
                                 command=lambda: pick_task_due(d))
                menu.tk_popup(event.x_root, event.y_root)

        ttk.Radiobutton(top, text="Week", variable=mode_var, value="week",
                       command=render).pack(side="left")
        ttk.Radiobutton(top, text="Month", variable=mode_var, value="month",
                       command=render).pack(side="left", padx=(4, 12))
        ttk.Button(top, text="< Prev", command=lambda: nav(-1)).pack(side="left")
        ttk.Button(top, text="Today", command=go_today).pack(side="left", padx=4)
        ttk.Button(top, text="Next >", command=lambda: nav(1)).pack(side="left")
        title_lbl = ttk.Label(top, text="", font=("Segoe UI", 9, "bold"))
        title_lbl.pack(side="left", padx=12)

        cv = tk.Canvas(win, background="white", highlightthickness=0)
        cv.pack(padx=8, pady=(0, 8))
        cv.bind("<Button-3>", on_right_click)
        render()
        ttk.Label(win, text="blue = imported calendar events · darker = "
                 "your tracked work sessions · ⚑ = a task due that day · "
                 "greener cell (month) = more real free time that day · "
                 "right-click an hour (week) to lock it for a deadline, "
                 "or a day (month) to set a task's due date",
                 foreground="#777777", wraplength=700, justify="left"
                 ).pack(anchor="w", padx=8, pady=(0, 8))

    def _outlook_win(self):
        win = tk.Toplevel(self)
        win.title("Outlook — the weeks ahead, at your real pace")
        win.geometry("620x300")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        body = self._outlook_lines()
        if not body:
            body = ["No scoped deadlines with hours remaining to forecast.",
                    "",
                    "Set a deadline with a total-hours scope (Tools >",
                    "Deadline countdowns) and track some time against it —",
                    "this window then projects where it actually lands."]
        txt.insert("1.0", "\n".join(body))
        txt.config(state="disabled")

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
        density_lbl = ttk.Label(win, foreground="#777777", font=("Segoe UI", 9))
        density_lbl.pack(fill="x", padx=8, pady=(8, 0))
        cols = ("pri", "task", "est", "actual", "goal", "deadline", "due", "source")
        heads = {"pri": "!", "task": "task", "est": "est", "actual": "actual",
                 "goal": "goal", "deadline": "deadline", "due": "due",
                 "source": "from"}
        widths = {"pri": 26, "task": 200, "est": 50, "actual": 65,
                  "goal": 100, "deadline": 90, "due": 60, "source": 120}
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=heads[c])
            tree.column(c, width=widths[c], anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        tree.tag_configure("signal", foreground="#2e8b2e")
        tree.tag_configure("someday", foreground="#999999")
        tree.tag_configure("blocked", foreground="#a03030")

        def refresh(keep_selection=None):
            sel = keep_selection if keep_selection is not None else tree.selection()
            tree.delete(*tree.get_children())
            # backlog #55: commitment density -- how much is declared
            # signal-priority right now, in aggregate, undated
            sig_items = [t for t in self.settings.get("tasks", [])
                        if t.get("priority") == "signal"]
            if sig_items:
                est_sum = sum(float(t.get("est_h") or 0) for t in sig_items)
                density_lbl.config(
                    text=f"{len(sig_items)} signal-priority item(s), "
                        f"~{est_sum:.1f}h estimated total, undated")
            else:
                density_lbl.config(text="")
            for i, t in enumerate(self.settings.get("tasks", [])):
                pri = t.get("priority", "normal")
                est = t.get("est_h")
                tag = "blocked" if t.get("blocked_by") else pri
                name = (f"⛔ {t['name']} (blocked by: {t['blocked_by']})"
                       if t.get("blocked_by") else t["name"])
                due_txt = "—"
                if t.get("due"):
                    try:
                        due_d = dt.date.fromisoformat(t["due"])
                        due_txt = ("⚠ " if due_d < self.today else "") + f"{due_d:%d.%m}"
                    except ValueError:
                        due_txt = t["due"]
                tree.insert("", "end", iid=str(i), tags=(tag,), values=(
                    self._PRI_ICON.get(pri, "○"), name,
                    f"{est:g}h" if est else "—",
                    f"{self._task_actual_h(t['name'], t['added']):.2f}h",
                    t.get("goal") or "—", t.get("deadline") or "—",
                    due_txt, t.get("source") or "—"))
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
                                width=13,
                                values=[""] + [g["name"] for g in self.goals()])
        goal_box.pack(side="left", padx=(4, 0))
        dl_var = tk.StringVar()
        dl_box = ttk.Combobox(bar, textvariable=dl_var, state="readonly",
                              width=11,
                              values=[""] + [d["name"] for d in self.deadlines()])
        dl_box.pack(side="left", padx=(4, 0))

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
                           goal=goal_var.get() or None,
                           deadline=dl_var.get() or None, source="added manually")
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
            self._mark_task_done(i)
            refresh()

        def delete():
            i = picked()
            if i is None:
                return
            del self.settings["tasks"][i]
            save_settings(self.settings)
            refresh()

        def set_link(field, names):
            i = picked()
            if i is None:
                return
            pop = tk.Toplevel(win)
            pop.title(f"Set {field}")
            pop.resizable(False, False)
            pop.grab_set()
            var = tk.StringVar(value=self.settings["tasks"][i].get(field) or "")
            ttk.Combobox(pop, textvariable=var, state="readonly",
                        values=[""] + names, width=30).grid(
                            row=0, column=0, padx=8, pady=8)

            def ok():
                self.settings["tasks"][i][field] = var.get() or None
                save_settings(self.settings)
                pop.destroy()
                refresh(keep_selection=[str(i)])

            ttk.Button(pop, text="OK", command=ok).grid(row=1, column=0, pady=(0, 8))

        def set_blocked_by():
            i = picked()
            if i is None:
                return
            cur = self.settings["tasks"][i].get("blocked_by") or ""
            v = simpledialog.askstring(
                APP_NAME, "Blocked by (task name or free text — empty "
                          "clears it). Backlog #44: excluded from Task "
                          "library suggestions until cleared.",
                initialvalue=cur, parent=win)
            if v is None:
                return
            self.settings["tasks"][i]["blocked_by"] = v.strip() or None
            save_settings(self.settings)
            refresh(keep_selection=[str(i)])

        def set_due():
            i = picked()
            if i is None:
                return
            cur = self.settings["tasks"][i].get("due") or ""
            v = simpledialog.askstring(
                APP_NAME, "Due date (YYYY-MM-DD, empty clears it). Backlog "
                          "#123: a lightweight 'done by' marker — not a full "
                          "scoped Deadline, doesn't add to the deadlines "
                          "list. Also settable by right-clicking a day in "
                          "the Calendar view's month mode.",
                initialvalue=cur, parent=win)
            if v is None:
                return
            v = v.strip()
            if v:
                try:
                    dt.date.fromisoformat(v)
                except ValueError:
                    messagebox.showerror(APP_NAME, "Use YYYY-MM-DD.", parent=win)
                    return
            self.settings["tasks"][i]["due"] = v or None
            save_settings(self.settings)
            if v:
                feasibility = self._due_date_feasibility_line(
                    dt.date.fromisoformat(v), self.settings["tasks"][i].get("est_h"))
                if feasibility:
                    self.status.config(text=feasibility)
            refresh(keep_selection=[str(i)])

        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="Set goal…", command=lambda: set_link(
            "goal", [g["name"] for g in self.goals()]))
        menu.add_command(label="Set deadline…", command=lambda: set_link(
            "deadline", [d["name"] for d in self.deadlines()]))
        menu.add_command(label="Set due date…", command=set_due)
        menu.add_command(label="Set blocked by…", command=set_blocked_by)

        def right_click(event):
            row = tree.identify_row(event.y)
            if row:
                tree.selection_set(row)
                menu.tk_popup(event.x_root, event.y_root)

        tree.bind("<Button-3>", right_click)

        entry.bind("<Return>", add)
        for label, cmd in (("Add", add), ("Start ▶", start),
                           ("Done ✓", done), ("Delete", delete)):
            ttk.Button(bar, text=label, command=cmd).pack(side="left", padx=(4, 0))
        hint = ("Click ! to cycle priority (● signal / ○ normal / ‥ someday), "
               "right-click a row to set/change its goal or deadline. "
               "TODO:/SOMEDAY: bullets anywhere (diary, themed writing) land "
               "here on their own.")
        ef = self._estimate_factor()
        if ef:
            hint += f"  Your history: actuals run ×{ef[0]:.1f} your estimates."
        ttk.Label(win, text=hint, foreground="#777777",
                  wraplength=760).pack(anchor="w", padx=8, pady=(0, 6))
        refresh()

    def _planned_hours_from_file(self, iso):
        """Backlog #25: total hours actually PLACED into blocks in one
        day's own schedule — the '  HH:MM-HH:MM name (Xh)' lines
        `_day_schedule_lines` (v8.0) writes once at day-open. Excludes
        the trailing 'uncommitted (Xh free today total)' line (that's
        free time, not a plan — its different text shape means the
        regex naturally skips it, no special-casing needed). Same
        in-file convention trick `_estimate_factor` uses for its own
        '--- Done:' lines. None if that day never got a schedule block
        written at all (nothing to reconcile against)."""
        pat = re.compile(r"^  \d\d:\d\d-\d\d:\d\d .+? \(([0-9.]+)h\)", re.M)
        try:
            with open(self.diary_path(dt.date.fromisoformat(iso)),
                      encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return None
        if "suggested schedule today" not in text:
            return None
        matches = pat.findall(text)
        return sum(float(m) for m in matches) if matches else None

    def _planner_realism_factor(self, days=60):
        """Backlog #25: the schedule audits itself. For each of the
        last `days` days that got a written schedule, the plan-
        survival ratio = actual tracked hours that day / planned hours
        (capped at 1.0 — overshooting a plan isn't "surviving more,"
        it's just a different day). Returns (median ratio, n), or None
        until 5+ real scheduled days exist. Grades the PLANNER's
        realism only — no compliance tracking of what the person did
        on any single day, the standing planning-engine guardrail."""
        idx = day_index()
        ratios = []
        for i in range(1, days + 1):
            iso = (self.today - dt.timedelta(days=i)).isoformat()
            planned = self._planned_hours_from_file(iso)
            if not planned:
                continue
            actual = (idx.get(iso) or {"work": 0})["work"] / 60
            ratios.append(min(1.0, actual / planned))
        if len(ratios) < 5:
            return None
        ratios.sort()
        return ratios[len(ratios) // 2], len(ratios)

    def _estimate_factor(self, kws=None):
        """(median actual/estimate ratio, sample count) from '--- Done: x
        (est Yh, actual Zh)' lines across all day files — app-wide by
        default, or scoped to one project's `kws` (backlog #28's
        post-mortem wants the estimate factor on THIS project, not the
        app-wide blend). None until 3+ samples exist."""
        pat = re.compile(r"--- Done: (.*?) \(est ([0-9.]+)h, actual ([0-9.]+)h\)")
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
            for name, e, a in found:
                if kws and not task_matches(name, kws):
                    continue
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
        # a taller canvas per footer line actually present (projection,
        # root-cause split) — both optional, both honesty-gated
        proj = self._projection_line(dl)
        pr = self._dl_projection(dl) if proj else None
        cause = self._root_cause_line(dl)
        footers = []
        if proj:
            footers.append((proj, "#c03030" if pr["delta"] > 0 else
                            "#2e8b2e" if pr["delta"] < 0 else "#555555"))
        if cause:
            footers.append((cause, "#a05a00"))
        W, H, PAD = 560, 320 + 28 * len(footers), 40
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
        for i, (text, colour) in enumerate(footers):
            y = H - 14 - 18 * (len(footers) - 1 - i)
            cv.create_text(PAD, y, anchor="w", width=W - 2 * PAD,
                           font=("Segoe UI", 9), fill=colour, text=text)

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

    # ----- year rhythm map -----

    def _year_rhythm_grid(self, weeks=52):
        """Backlog #26: tracked minutes bucketed by (week, hour) across
        the last `weeks` Monday-start calendar weeks (same week
        convention as _heatmap) — the year's SHAPE at a glance instead
        of _heatmap's per-day total: bedtime drift eras, morning-
        discipline phases, the exam-sprint block, the dead summer. Both
        work and break rows count (this is about when you're at the
        desk AT ALL, not deep-work minutes — _heatmap already covers
        that). Returns {(week_idx, hour): minutes}; week_idx 0 is the
        week containing today, weeks-1 the oldest week shown."""
        this_mon = self.today - dt.timedelta(days=self.today.weekday())
        start_mon = this_mon - dt.timedelta(weeks=weeks - 1)
        start_iso = start_mon.isoformat()
        grid = {}
        for r in read_rows():
            if r[0] < start_iso:
                continue
            try:
                d = dt.date.fromisoformat(r[0])
                h = int(r[2].split(":")[0]) % 24
                m = int(r[4])
            except (ValueError, IndexError):
                continue
            if d > self.today:
                continue
            week_idx = (this_mon - (d - dt.timedelta(days=d.weekday()))).days // 7
            if 0 <= week_idx < weeks:
                key = (week_idx, h)
                grid[key] = grid.get(key, 0) + m
        return grid

    def _year_rhythm_view(self):
        grid = self._year_rhythm_grid()
        weeks, cell, pad = 52, 10, 40
        W, H = pad * 2 + weeks * cell, pad + 24 * cell + 30
        win = tk.Toplevel(self)
        win.title("Year rhythm — 52 weeks × hour of day")
        cv = tk.Canvas(win, width=W, height=H, background="white",
                       highlightthickness=0)
        cv.pack(padx=8, pady=8)
        this_mon = self.today - dt.timedelta(days=self.today.weekday())
        seen_month = None
        for w in range(weeks):
            week_start = this_mon - dt.timedelta(weeks=weeks - 1 - w)
            for h in range(24):
                mins = grid.get((weeks - 1 - w, h), 0)
                shade = next(i for i, lim in
                             enumerate((1, 60, 150, 240, 330, 99999))
                             if mins < lim)
                x, y = pad + w * cell, pad + h * cell
                cv.create_rectangle(x, y, x + cell - 1, y + cell - 1,
                                    fill=self.HEAT[shade], outline="")
            if week_start.strftime("%b") != seen_month:
                seen_month = week_start.strftime("%b")
                cv.create_text(pad + w * cell, pad - 8, text=seen_month,
                               anchor="w", font=("Segoe UI", 7),
                               fill="#666666")
        for h in (0, 6, 12, 18, 23):
            cv.create_text(pad - 6, pad + h * cell + cell / 2 - 1,
                           text=f"{h:02d}", anchor="e",
                           font=("Segoe UI", 7), fill="#888888")
        cv.create_text(pad, H - 12, anchor="w", font=("Segoe UI", 8),
                       fill="#666666",
                       text="shade = tracked minutes that hour, that week — "
                            "0 · <1h · <2.5h · <4h · <5.5h · 5.5h+")

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

    def _suggested_sleep_block(self, days=60, min_nights=10):
        """Backlog #126: infer a typical sleep window from real
        tracked data instead of guessing or leaving it blank forever
        — resolves the "auto-set" instinct #121 deliberately deferred
        (no bedtime was ever stated, and guessing one would have
        repeated the #103 mistake). Wake time proxied by each day's
        own first logged activity (already tracked, no new data);
        sleep hours from _sleep_h (override or health import). Median
        across real nights, not an average (one very late night
        shouldn't drag the suggestion around). A SUGGESTION only —
        the caller pre-fills an editable field, never auto-saves.
        Silent (None) below `min_nights` real nights — no forecast
        beats an unfounded one, same honesty gate as everywhere else
        in this app."""
        by_day = {}
        for r in read_rows():
            by_day.setdefault(r[0], []).append(r)
        wakes, sleep_hours = [], []
        d = self.today - dt.timedelta(days=1)
        end = self.today - dt.timedelta(days=days)
        while d >= end:
            iso = d.isoformat()
            sl = self._sleep_h(iso)
            rows = by_day.get(iso)
            if sl and rows:
                first = None
                for r in rows:
                    try:
                        h, m = map(int, r[2].split(":")[:2])
                        t = h * 60 + m
                    except (ValueError, IndexError):
                        continue
                    if first is None or t < first:
                        first = t
                if first is not None and first < 14 * 60:   # sanity: before 14:00
                    wakes.append(first)
                    sleep_hours.append(sl)
            d -= dt.timedelta(days=1)
        if len(wakes) < min_nights:
            return None
        wakes.sort()
        sleep_hours.sort()
        med_wake = wakes[len(wakes) // 2]
        med_sleep = sleep_hours[len(sleep_hours) // 2]
        wake_t = dt.time(med_wake // 60, med_wake % 60)
        bed_min = (med_wake - round(med_sleep * 60)) % 1440
        bed_t = dt.time(bed_min // 60, bed_min % 60)
        return bed_t, wake_t, len(wakes)

    def _commitment_drift_lines(self, days=60, min_samples=10):
        """Backlog #125: the same "declared vs actual" honesty pattern
        already used elsewhere (#47's capacity-vs-actual, #99's day
        audits), applied to #121's recurring commitments. Sleep is
        checked against #126's own suggestion (the same real-data
        inference, so the two features can't quietly disagree); every
        other commitment is checked against the day's own first
        tracked WORK activity on the days it's declared to apply — a
        "Day job" starting 45min later than declared, in practice,
        for the last N matching days. Gated on min_samples real
        matching days per commitment; a >=30min median gap is what
        gets named, smaller drift stays quiet (noise, not a pattern)."""
        out = []
        windows = self.settings.get("protected_windows", [])
        sleep_w = next((w for w in windows
                        if "sleep" in (w.get("label") or "").lower()), None)
        if sleep_w:
            try:
                sh, sm = map(int, sleep_w["start"].split(":"))
                declared_bed = sh * 60 + sm
            except (ValueError, KeyError):
                declared_bed = None
            sugg = self._suggested_sleep_block(days, min_samples)
            if declared_bed is not None and sugg:
                actual_bed_t, _wake, n = sugg
                actual_bed = actual_bed_t.hour * 60 + actual_bed_t.minute
                diff = min((declared_bed - actual_bed) % 1440,
                          (actual_bed - declared_bed) % 1440)
                if diff >= 30:
                    out.append(f"'Sleep' declared {sleep_w['start']} but "
                              f"your last {n} tracked nights suggest "
                              f"~{actual_bed_t:%H:%M} — worth updating?")

        by_day = {}
        for r in read_rows():
            if r[1] != "break":
                by_day.setdefault(r[0], []).append(r)
        for w in windows:
            label = w.get("label", "")
            if not label or "sleep" in label.lower():
                continue
            try:
                sh, sm = map(int, w["start"].split(":"))
                declared_start = sh * 60 + sm
            except (ValueError, KeyError):
                continue
            days_set = self._parse_weekdays(w.get("days", ""))
            actual_starts = []
            d = self.today - dt.timedelta(days=1)
            end = self.today - dt.timedelta(days=days)
            while d >= end:
                if days_set is None or d.weekday() in days_set:
                    rows = by_day.get(d.isoformat())
                    if rows:
                        times = []
                        for r in rows:
                            try:
                                h, m = map(int, r[2].split(":")[:2])
                                times.append(h * 60 + m)
                            except (ValueError, IndexError):
                                continue
                        if times:
                            actual_starts.append(min(times))
                d -= dt.timedelta(days=1)
            if len(actual_starts) < min_samples:
                continue
            actual_starts.sort()
            med = actual_starts[len(actual_starts) // 2]
            diff = med - declared_start
            if abs(diff) >= 30:
                med_t = dt.time((med // 60) % 24, med % 60)
                direction = "later" if diff > 0 else "earlier"
                out.append(f"'{label}' declared {w['start']} start but "
                          f"your last {len(actual_starts)} matching days "
                          f"actually start ~{med_t:%H:%M} "
                          f"({abs(diff)}min {direction}) — worth updating?")
        return out

    # ----- daylight (a zero-dependency source: date + latitude, nothing
    # imported, no export file to configure) -----

    def _daylight_h(self, d):
        lat = self.settings.get("daylight_lat")
        return day_length_hours(d, float(lat)) if lat is not None else None

    def _set_daylight_lat(self):
        """Tools > Daylight location — a latitude, not an address: enough
        for the day-length math, nothing more precise than that. Empty
        clears it (unlike askfloat's None-on-cancel, an explicit blank
        string means 'turn this off', matching the AVOID/METRICS empty-
        line convention elsewhere)."""
        cur = self.settings.get("daylight_lat")
        v = simpledialog.askstring(
            APP_NAME, "Approximate latitude in degrees — e.g. 60.2 for "
                      "Helsinki, -33.9 for Sydney (south is negative).\n"
                      "Used only for a computed daylight-hours source: no "
                      "lookup, no network, just date + latitude math.\n"
                      "Empty = off:",
            initialvalue=(f"{cur:g}" if cur is not None else ""), parent=self)
        if v is None:
            return
        v = v.strip()
        if not v:
            self.settings.pop("daylight_lat", None)
        else:
            try:
                lat = float(v.replace(",", "."))
                if not -90 <= lat <= 90:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    APP_NAME, "Latitude must be a number between -90 and 90.",
                    parent=self)
                return
            self.settings["daylight_lat"] = lat
        save_settings(self.settings)

    def _daylight_insight(self, days=365):
        """Compares output on your shortest-daylight days vs your longest
        — but only once your OWN history actually spans a real seasonal
        swing (median gap >=2h between the two halves) with n>=8 each
        side, so a few flat weeks near the equator or right after setting
        the latitude stays silent rather than inventing a 'season' out of
        noise. The reason to turn this source on well before it can speak:
        the day it CAN speak needs the history to already exist."""
        lat = self.settings.get("daylight_lat")
        if lat is None:
            return []
        idx = day_index()
        cutoff = self.today - dt.timedelta(days=days)
        pts = []                      # (daylight_h, work_min, energy)
        d = cutoff
        while d <= self.today:
            rec = idx.get(d.isoformat())
            if rec and rec["work"] > 0:
                pts.append((day_length_hours(d, float(lat)), rec["work"],
                           self._day_energy(d)))
            d += dt.timedelta(days=1)
        if len(pts) < 16:
            return []
        pts.sort(key=lambda x: x[0])
        half = len(pts) // 2
        lo, hi = pts[:half], pts[-half:]
        if len(lo) < 8 or len(hi) < 8:
            return []
        lo_med, hi_med = lo[len(lo) // 2][0], hi[len(hi) // 2][0]
        if hi_med - lo_med < 2.0:
            return []
        lo_work = sum(p[1] for p in lo) / len(lo) / 60
        hi_work = sum(p[1] for p in hi) / len(hi) / 60
        verb = "less" if lo_work < hi_work else "more"
        out = [f"shortest-daylight days (~{lo_med:.1f}h sun, n={len(lo)}): "
              f"{lo_work:.1f}h work avg vs longest (~{hi_med:.1f}h sun, "
              f"n={len(hi)}): {hi_work:.1f}h — {verb} on the darker days"]
        lo_en = [p[2] for p in lo if p[2]]
        hi_en = [p[2] for p in hi if p[2]]
        if len(lo_en) >= 3 and len(hi_en) >= 3:
            out.append(f"  energy: {sum(lo_en) / len(lo_en):.1f}/5 dark vs "
                       f"{sum(hi_en) / len(hi_en):.1f}/5 light")
        return out

    # ----- word-frequency drift (the diary's own free text, unlocked) -----
    #
    # Every other insight reads the STRUCTURED data (csv minutes, SIGNAL
    # keywords, ENERGY numbers). The diary's free-typed prose is fully
    # collected too and has been the whole time — just never analysed on
    # its own terms. This doesn't need a new source; it needs someone to
    # actually read what's already there.

    _WORD_RE = re.compile(r"[^\W\d_]{4,}")
    _WORD_STOPWORDS = {
        # English function words — cuts obvious noise, not linguistically
        # exhaustive on purpose (see the module's stdlib-only rule: no NLP
        # library, just a short hand list).
        "the", "and", "that", "this", "with", "from", "have", "were", "was",
        "been", "being", "will", "would", "could", "should", "about",
        "into", "over", "after", "before", "just", "also", "very", "really",
        "still", "already", "today", "yesterday", "tomorrow", "week",
        "month", "these", "those", "they", "them", "their", "your", "our",
        # Finnish function words — the diary is bilingual (see README's own
        # example break notes: "käv", "puhelin", "jt viestei")
        "että", "koska", "mutta", "myös", "vielä", "tänään", "huomenna",
        "eilen", "tämä", "nämä", "hänen", "heidän", "minun", "sinun",
    }

    def _diary_word_counts(self, lo, hi):
        """Lowercased word counts (letters only, len>=4, stopwords out)
        across free-typed diary text in [lo, hi] inclusive — skips every
        structural line via the same `_LINE_TAG_RULES` classifier the
        syntax highlighter uses, so only what you actually wrote counts,
        never a SIGNAL/METRICS/TODO/timer line."""
        skip = [p for p, _ in self._LINE_TAG_RULES]
        counts, total = {}, 0
        d = lo
        while d <= hi:
            try:
                with open(self.diary_path(d), encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                d += dt.timedelta(days=1)
                continue
            for line in text.splitlines():
                s = line.strip()
                if not s or any(p.search(s) for p in skip):
                    continue
                for w in self._WORD_RE.findall(s.lower()):
                    if w in self._WORD_STOPWORDS:
                        continue
                    counts[w] = counts.get(w, 0) + 1
                    total += 1
            d += dt.timedelta(days=1)
        return counts, total

    def _word_drift_counts(self, recent_days=30, prior_days=90):
        """Shared word-count computation for both drift directions (the
        increase check below and the fade check, backlog #69) — one file
        scan instead of two identical ones. Returns (rec_counts,
        rec_total, pri_counts, pri_total), or None if either window is
        too thin (<30 words) to compare honestly."""
        recent_hi = self.today
        recent_lo = recent_hi - dt.timedelta(days=recent_days - 1)
        prior_hi = recent_lo - dt.timedelta(days=1)
        prior_lo = prior_hi - dt.timedelta(days=prior_days - 1)
        rec_counts, rec_total = self._diary_word_counts(recent_lo, recent_hi)
        pri_counts, pri_total = self._diary_word_counts(prior_lo, prior_hi)
        if rec_total < 30 or pri_total < 30:
            return None
        return rec_counts, rec_total, pri_counts, pri_total

    def _word_drift_insight(self, recent_days=30, prior_days=90):
        """What's actually occupying your mind lately, separate from your
        tracked task labels — the word with the sharpest real increase in
        the last `recent_days` vs the `prior_days` before that. Compares
        NORMALISED share (count / window total) so different window
        lengths don't skew it. Needs real volume both sides (>=30 words
        each) and a real jump (>=3 recent mentions, and either new or
        >=3x its prior share) — a single passing mention never qualifies."""
        counts = self._word_drift_counts(recent_days, prior_days)
        if not counts:
            return []
        rec_counts, rec_total, pri_counts, pri_total = counts
        best = None    # (score, word, rec_n, pri_n)
        for w, rn in rec_counts.items():
            if rn < 3:
                continue
            rec_pct = rn / rec_total
            pn = pri_counts.get(w, 0)
            pri_pct = pn / pri_total
            if not (pn == 0 or rec_pct >= 3 * pri_pct):
                continue
            score = rec_pct - pri_pct
            if best is None or score > best[0]:
                best = (score, w, rn, pn)
        if not best:
            return []
        _score, word, rn, pn = best
        return [f"words appearing more lately: '{word}' ({pn}→{rn} "
                f"mentions, last {recent_days}d vs prior {prior_days}d) — "
                "what's actually on your mind, separate from your tracked "
                "tasks"]

    def _word_fade_insight(self, recent_days=30, prior_days=90):
        """Backlog #69 — the other direction. A topic that was frequent
        and went quiet often matters more than a new one appearing: a
        person, a worry, a plan that stopped getting mentioned. Symmetric
        gate to the increase check: pn>=3 in the OLD window, and either
        vanished entirely now or its share collapsed to <=1/3 of before.
        Reported separately from the increase line — up and down are
        different kinds of noticing, not one slot competing for both."""
        counts = self._word_drift_counts(recent_days, prior_days)
        if not counts:
            return []
        rec_counts, rec_total, pri_counts, pri_total = counts
        best = None    # (score, word, rec_n, pri_n)
        for w, pn in pri_counts.items():
            if pn < 3:
                continue
            pri_pct = pn / pri_total
            rn = rec_counts.get(w, 0)
            rec_pct = rn / rec_total
            if not (rn == 0 or pri_pct >= 3 * rec_pct):
                continue
            score = pri_pct - rec_pct
            if best is None or score > best[0]:
                best = (score, w, rn, pn)
        if not best:
            return []
        _score, word, rn, pn = best
        return [f"words appearing less lately: '{word}' ({pn}→{rn} "
                f"mentions, last {recent_days}d vs prior {prior_days}d) — "
                "gone quiet, worth noticing why"]

    # ----- lag correlations: what TODAY does to TOMORROW -----
    #
    # Every insight so far correlates same-day pairs. This is the new loop
    # shape: (day, day+1). Same honesty gates (n>=5/bucket, a real swing),
    # just one day offset — backlog #22.

    def _lag_workout_line(self, days=90):
        idx = day_index()
        cutoff = self.today - dt.timedelta(days=days)
        wo_next, no_wo_next = [], []
        d = cutoff
        while d < self.today:
            nxt = d + dt.timedelta(days=1)
            rec_next = idx.get(nxt.isoformat())
            if rec_next and rec_next["work"] > 0:
                wo = self._health_data().get(d.isoformat(), {}).get("workout_min")
                (wo_next if wo and wo >= 10 else no_wo_next).append(rec_next["work"])
            d += dt.timedelta(days=1)
        if len(wo_next) < 5 or len(no_wo_next) < 5:
            return None
        a = sum(wo_next) / len(wo_next) / 60
        b = sum(no_wo_next) / len(no_wo_next) / 60
        if abs(a - b) < 0.3:
            return None
        verb = ("a productivity tool, not a cost" if a > b else
               "worth the recovery trade, even so")
        return (f"the day after a workout you average {a:.1f}h of work vs "
               f"{b:.1f}h after a non-workout day (n={len(wo_next)} vs "
               f"{len(no_wo_next)}) — the gym looks like {verb}")

    def _lag_sleep_debt_line(self, days=90):
        """Not the existing same-day sleep-vs-output check — this pairs
        last night's sleep with the day AFTER that, testing whether a
        short-sleep night still costs you once the immediate day is over."""
        idx = day_index()
        cutoff = self.today - dt.timedelta(days=days)
        short_next, full_next = [], []
        d = cutoff
        while d < self.today:
            nxt = d + dt.timedelta(days=1)
            rec_next = idx.get(nxt.isoformat())
            sl = self._sleep_h(d.isoformat())
            if rec_next and rec_next["work"] > 0 and sl:
                (short_next if sl < 7 else full_next).append(rec_next["work"])
            d += dt.timedelta(days=1)
        if len(short_next) < 5 or len(full_next) < 5:
            return None
        a = sum(short_next) / len(short_next) / 60
        b = sum(full_next) / len(full_next) / 60
        if abs(a - b) < 0.3:
            return None
        if a < b:
            return (f"the day AFTER a short-sleep night (<7h), output "
                    f"averages {a:.1f}h vs {b:.1f}h after a full night "
                    f"(n={len(short_next)} vs {len(full_next)}) — sleep "
                    "debt doesn't clear in one day")
        return (f"output the day after a short-sleep night averages "
               f"{a:.1f}h vs {b:.1f}h after a full one (n={len(short_next)} "
               f"vs {len(full_next)}) — no lingering cost detected yet")

    def _day_start_late_map(self, cutoff_iso):
        """One pass over read_rows(): {iso: {'first': min-since-midnight
        of the day's first work row, 'late': any work row started >=21:00}}
        — the shared per-day scan both directions of the evening-work lag
        check need, computed once rather than once per bucket."""
        out = {}
        for r in read_rows():
            if r[1] == "break" or r[0] < cutoff_iso:
                continue
            try:
                h, m = map(int, r[2].split(":")[:2])
            except (ValueError, IndexError):
                continue
            mins = h * 60 + m
            rec = out.setdefault(r[0], {"first": mins, "late": False})
            rec["first"] = min(rec["first"], mins)
            if h >= 21:
                rec["late"] = True
        return out

    def _lag_evening_start_line(self, days=90):
        cutoff = self.today - dt.timedelta(days=days)
        m = self._day_start_late_map(cutoff.isoformat())
        late_next, normal_next = [], []
        d = cutoff
        while d < self.today:
            nxt = d + dt.timedelta(days=1)
            info_d, info_next = m.get(d.isoformat()), m.get(nxt.isoformat())
            if info_d and info_next:
                (late_next if info_d["late"] else normal_next).append(
                    info_next["first"])
            d += dt.timedelta(days=1)
        if len(late_next) < 5 or len(normal_next) < 5:
            return None
        a, b = sum(late_next) / len(late_next), sum(normal_next) / len(normal_next)
        if abs(a - b) < 15:
            return None

        def fmt(mins):
            return f"{int(mins) // 60:02d}:{int(mins) % 60:02d}"
        verb = "later" if a > b else "earlier"
        return (f"mornings after working past 21:00 you start {fmt(a)} on "
               f"average vs {fmt(b)} otherwise (n={len(late_next)} vs "
               f"{len(normal_next)}) — {abs(a - b) / 60:.1f}h {verb}")

    def _lag_fragmentation_line(self, days=90):
        """Backlog #70: does yesterday's task-switching predict a
        SHALLOWER today, not just a scattered yesterday (#16 is same-
        day)? Wires two already-existing measurements — `_day_switches`
        (v8.18) as the trigger, `_day_shallow_frac` (v8.19's block logic,
        generalised to any day) as the next-day measure — through the
        (day, day+1) loop shape v8.31 introduced. Not new math, just the
        same lag lens applied to a pairing nobody had checked yet."""
        threshold = self._shallow_threshold()
        cutoff = self.today - dt.timedelta(days=days)
        high_next, low_next = [], []
        d = cutoff
        while d < self.today:
            nxt = d + dt.timedelta(days=1)
            frac = self._day_shallow_frac(nxt, threshold=threshold)
            if frac:
                shallow, total = frac
                switches = self._day_switches(d)
                if switches >= 6:
                    high_next.append(100 * shallow / total)
                elif switches <= 2:
                    low_next.append(100 * shallow / total)
            d += dt.timedelta(days=1)
        if len(high_next) < 5 or len(low_next) < 5:
            return None
        a = sum(high_next) / len(high_next)
        b = sum(low_next) / len(low_next)
        if a - b < 10:
            return None
        return (f"the day after a 6+ switch day, {a:.0f}% of your signal "
               f"work lands in shallow blocks (<{threshold}m) vs {b:.0f}% "
               f"after a focused day (≤2 switches) (n={len(high_next)} vs "
               f"{len(low_next)}) — fragmentation carries over")

    def _lag_insight(self, days=90):
        """Time-LAGGED correlations — what today does to tomorrow, the new
        loop shape (day, day+1) instead of every other insight's same-day
        pairing. Same honesty gates throughout each sub-check."""
        return [ln for ln in (self._lag_workout_line(days),
                              self._lag_sleep_debt_line(days),
                              self._lag_evening_start_line(days),
                              self._lag_fragmentation_line(days)) if ln]

    def _running_hot_line(self, recent_days=14, prior_days=60):
        """Backlog #24: the early-warning version of the sleep-for-work
        trade the trajectory line only spots after ~4 weeks of drift.
        Same recent-vs-prior window shape as word drift (v8.29/v8.37):
        the last `recent_days` vs the `prior_days` immediately before
        that. Four independent signals — sleep below your own recent
        norm, workout frequency drop, late-night count, break-ratio
        compression — each gated on its own real sample size and a
        real swing. Speaks only when at least TWO move together (never
        off one signal alone — any single one has too many honest
        explanations); silent again the moment the signals ease, no
        memory of having spoken before."""
        recent_hi = self.today
        recent_lo = recent_hi - dt.timedelta(days=recent_days - 1)
        prior_hi = recent_lo - dt.timedelta(days=1)
        prior_lo = prior_hi - dt.timedelta(days=prior_days - 1)
        recent_isos = [(recent_lo + dt.timedelta(days=i)).isoformat()
                       for i in range(recent_days)]
        prior_isos = [(prior_lo + dt.timedelta(days=i)).isoformat()
                      for i in range(prior_days)]
        idx = day_index()
        hd = self._health_data()
        late_map = self._day_start_late_map(prior_lo.isoformat())

        flags, parts = [], []

        r_sleep = [self._sleep_h(iso) for iso in recent_isos if self._sleep_h(iso)]
        p_sleep = [self._sleep_h(iso) for iso in prior_isos if self._sleep_h(iso)]
        if len(r_sleep) >= 5 and len(p_sleep) >= 10:
            r_avg, p_avg = sum(r_sleep) / len(r_sleep), sum(p_sleep) / len(p_sleep)
            if p_avg - r_avg >= 0.4:
                flags.append("sleep")
                parts.append(f"sleep -{p_avg - r_avg:.1f}h/night vs norm")

        r_wo = sum(1 for iso in recent_isos if (hd.get(iso) or {}).get("workout_min"))
        p_wo = sum(1 for iso in prior_isos if (hd.get(iso) or {}).get("workout_min"))
        if p_wo >= 3:
            p_rate = p_wo / len(prior_isos)
            r_rate = r_wo / len(recent_isos)
            if r_rate <= p_rate * 0.6:
                flags.append("workouts")
                parts.append("workouts stopped" if r_wo == 0 else
                             f"workouts down to {round(100 * r_rate / p_rate)}%")

        n_late = sum(1 for iso in recent_isos if late_map.get(iso, {}).get("late"))
        if n_late >= 3:
            flags.append("late")
            parts.append(f"{n_late} late nights")

        r_work = sum(idx.get(iso, {"work": 0})["work"] for iso in recent_isos)
        r_brk = sum(idx.get(iso, {"brk": 0})["brk"] for iso in recent_isos)
        p_work = sum(idx.get(iso, {"work": 0})["work"] for iso in prior_isos)
        p_brk = sum(idx.get(iso, {"brk": 0})["brk"] for iso in prior_isos)
        if r_work >= 300 and p_work >= 1000 and p_brk > 0:
            r_ratio, p_ratio = r_brk / r_work, p_brk / p_work
            if r_ratio <= p_ratio * 0.6:
                flags.append("breaks")
                parts.append("breaks compressed")

        if len(flags) < 2:
            return None
        return (f"{recent_days} days running hot ({', '.join(parts)}) — "
               "schedule one flat day before your body schedules it")

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
               "mindful_min": self._health_data().get(iso, {}).get("mindful_min"),
               "rhr": self._health_data().get(iso, {}).get("rhr"),
               "hrv": self._health_data().get(iso, {}).get("hrv"),
               "weight_kg": self._health_data().get(iso, {}).get("weight_kg"),
               "metrics": self._day_metrics(d),
               "daylight_h": self._daylight_h(d),
               "busy_h": self._busy_data().get(iso, 0.0),
               "capacity_h": self._day_capacity(d)}
        return rec

    @staticmethod
    def _scrolled_text(parent):
        """A Text+Scrollbar pair packed into `parent`, returns the Text."""
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=4, pady=4)
        scroll = ttk.Scrollbar(frame, orient="vertical")
        txt = tk.Text(frame, wrap="word", font=("Consolas", 10),
                      width=84, height=18, yscrollcommand=scroll.set)
        scroll.config(command=txt.yview)
        scroll.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.tag_configure("h", font=("Consolas", 10, "bold"))
        txt.tag_configure("warn", foreground="#c03030")
        return txt

    def _dashboard(self, event=None):
        """The home screen: tabs over the same computed lines (Today &
        Week / Deadlines & Goals / Insights), plus a hub row linking to
        every detail view (weekly/monthly tables, the 8-week trend, the
        health table, the heatmap) — a real front door, not a
        replacement for the drill-downs that still hold unique detail."""
        self._save_diary()
        win = tk.Toplevel(self)
        win.title("Life dashboard")
        win.geometry("740x780")
        win.minsize(680, 500)

        # a Notebook pane must be an actual child of the notebook widget —
        # creating these as children of `win` instead left the tabs
        # switchable but visually empty, since nothing was really attached
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        top_tab = ttk.Frame(nb)
        cv = tk.Canvas(top_tab, width=660, height=150, background="white",
                       highlightthickness=0)
        cv.pack(padx=4, pady=(4, 2))
        sleep_cv = tk.Canvas(top_tab, width=660, height=80, background="white",
                             highlightthickness=0)
        sleep_cv.pack(padx=4, pady=(0, 2))
        txt_today = self._scrolled_text(top_tab)

        goals_tab = ttk.Frame(nb)
        txt_goals = self._scrolled_text(goals_tab)

        insights_tab = ttk.Frame(nb)
        txt_insights = self._scrolled_text(insights_tab)

        nb.add(top_tab, text="Today & Week")
        nb.add(goals_tab, text="Deadlines & Goals")
        nb.add(insights_tab, text="Insights")

        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=(0, 4))
        hub = ttk.Frame(win)
        hub.pack(fill="x", padx=8, pady=(0, 8))
        shown = [""]

        def render():
            monday = self.today - dt.timedelta(days=self.today.weekday())
            week = [self._life_day(monday + dt.timedelta(days=i))
                    for i in range(7)]
            self._draw_week_bars(cv, week)
            self._draw_sleep_bars(sleep_cv)
            lines = self._dashboard_lines(week)
            shown[0] = "\n".join(lines)

            sections, cur = {}, None
            for ln in lines:
                if ln and not ln.startswith(" "):
                    cur = ln
                    sections[cur] = []
                elif cur is not None:
                    sections[cur].append(ln)

            def fill(txt, prefixes):
                txt.config(state="normal")
                txt.delete("1.0", "end")
                for k, body in sections.items():
                    if not any(k.startswith(p) for p in prefixes):
                        continue
                    txt.insert("end", k + "\n", "h")
                    for ln in body:
                        txt.insert("end", ln + "\n", "warn" if "⚠" in ln else ())
                    txt.insert("end", "\n")
                txt.config(state="disabled")

            fill(txt_today, ("TODAY", "THIS WEEK", "LIFE BALANCE"))
            fill(txt_goals, ("GOALS", "DEADLINES", "WAITING ON"))
            fill(txt_insights, ("INSIGHTS",))

        def copy():
            self.clipboard_clear()
            self.clipboard_append(
                shown[0] + "\n\nAsk: what slipped, what pattern am I not "
                "seeing, what should next week look like?")
            self.status.config(text="Dashboard copied — paste into Claude.")

        def copy_status_update():
            text = self._status_update_all()
            if not text:
                self.status.config(
                    text="No scoped deadlines to report on yet.")
                return
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status.config(
                text="Status update copied — paste into an email to your "
                    "supervisor/advisor.")

        ttk.Button(bar, text="Copy for AI review", command=copy).pack(side="left")
        ttk.Button(bar, text="Copy status update",
                  command=copy_status_update).pack(side="left", padx=6)
        ttk.Button(bar, text="Refresh", command=render).pack(side="left", padx=6)

        ttk.Label(hub, text="Detail views:", foreground="#777777").pack(side="left")
        for label, cmd in (
                ("Weekly", lambda: self._summary("week")),
                ("Monthly", lambda: self._summary("month")),
                ("Trend (8wk)", self._trend),
                ("Health (14d)", self._health_view),
                ("Heatmap", self._heatmap),
                ("Burn-down", self._burndown)):
            ttk.Button(hub, text=label, command=cmd).pack(side="left", padx=(4, 0))
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

        waiting = self._waiting_on_lines()
        if waiting:
            lines += [""] + waiting

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
                lifetime = self._lifetime_ledger_line(
                    g["name"], self._match_kws(g.get("match")), g.get("start"))
                if lifetime:
                    lines.append(f"    {lifetime}")

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
                lifetime = self._lifetime_ledger_line(
                    dl["name"], self._match_kws(dl.get("match")),
                    dl.get("start"))
                if lifetime:
                    lines.append(f"    {lifetime}")
                reneg = self._deadline_renegotiation_line(dl)
                if reneg:
                    lines.append(f"    {reneg}")
                milestones = self._milestone_progress_line(dl)
                if milestones:
                    lines.append(f"  {milestones}")
            lines += [" " + s for s in self._capacity_lines()]

        lines += ["", "INSIGHTS — your last 60 days, cross-referenced"]
        ins = self._insight_lines_grouped()
        if ins:
            for theme in self._INSIGHT_THEMES:
                group = [line for th, line in ins if th == theme]
                if not group:
                    continue
                lines.append(f"  — {theme} —")
                lines += ["    · " + s for s in group]
        else:
            lines.append("  (still collecting — these appear as sleep, "
                         "estimate and streak history builds up)")
        return lines

    _BREAK_MOVE = ("walk", "käv", "gym", "sali", "run", "juoks", "ulos",
                   "ulko", "outside", "stretch", "move")
    _BREAK_SCROLL = ("scroll", "phone", "puhelin", "insta", "some", "somet",
                     "youtube", "yt", "reddit", "tiktok", "twitter", "news",
                     "uutis")

    def _procrastination_insight(self, days=60):
        """Which task do you flee FROM? A 'bounce' = a run of work on one
        task that dies within 10 minutes into a break — the signature of
        aversion, not tiredness. High bounce rate means the task is too
        big or too vague; the fix is cutting it smaller, not willpower.
        Names the worst offender only with n≥6 starts and ≥50% bounces."""
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        by_day = {}
        for r in read_rows():
            if r[0] >= cutoff:
                by_day.setdefault(r[0], []).append(r)
        stats = {}                    # lower -> [label, starts, bounces]
        for rows in by_day.values():
            rows.sort(key=lambda r: r[2])
            i = 0
            while i < len(rows):
                r = rows[i]
                if r[1] == "break" or not r[5].strip():
                    i += 1
                    continue
                t = r[5].strip().lower()
                run, j = 0, i
                while (j < len(rows) and rows[j][1] != "break"
                       and rows[j][5].strip().lower() == t):
                    try:
                        run += int(rows[j][4])
                    except ValueError:
                        pass
                    j += 1
                rec = stats.setdefault(t, [r[5].strip(), 0, 0])
                rec[1] += 1
                if run <= 10 and j < len(rows) and rows[j][1] == "break":
                    rec[2] += 1
                i = j
        worst = None
        for label, n, b in stats.values():
            if n >= 6 and b / n >= 0.5 and (worst is None
                                            or b / n > worst[2] / worst[1]):
                worst = (label, n, b)
        if worst:
            label, n, b = worst
            return [f"you bounce off '{label}' within 10 min on "
                    f"{round(100 * b / n)}% of starts ({b} of {n}) — that's "
                    "not laziness, the task is too big; cut it into [30m] "
                    "pieces"]
        return []

    def _break_insight(self, days=60):
        """Break TYPE vs what follows it: pair each labelled break (the
        note you type after '--- Break duration:') with the next work
        block that day and compare — the doomscroll tax measured at block
        level, from labels the diary has been collecting for years.
        Speaks with 5+ samples per bucket."""
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        by_day = {}
        for r in read_rows():
            if r[0] >= cutoff:
                by_day.setdefault(r[0], []).append(r)
        move, scroll = [], []
        for rows in by_day.values():
            rows.sort(key=lambda r: r[2])
            for i, r in enumerate(rows):
                if r[1] != "break":
                    continue
                note = (r[6] or "").lower()
                if any(k in note for k in self._BREAK_MOVE):
                    bucket = move
                elif any(k in note for k in self._BREAK_SCROLL):
                    bucket = scroll
                else:
                    continue
                for nxt in rows[i + 1:]:
                    if nxt[1] != "break":
                        try:
                            bucket.append(int(nxt[4]))
                        except ValueError:
                            pass
                        break
        if len(move) >= 5 and len(scroll) >= 5:
            ma = sum(move) / len(move)
            sa = sum(scroll) / len(scroll)
            return [f"after a moving break your next work block averages "
                    f"{ma:.0f}m ({len(move)} samples); after a scroll break "
                    f"{sa:.0f}m ({len(scroll)}) — the doomscroll tax, "
                    "measured at block level"]
        return []

    def _break_budget_line(self, days=60, now_hour=None):
        """Backlog #33 (+ v2 weekday split, #72): a daily ALLOWANCE
        learned from your own good days — a reframe, not a verdict on
        any one break. The full-day norm uses TODAY's own weekday when
        there's enough history for it specifically (n>=10) — Friday
        afternoons and Tuesday mornings plausibly have genuinely
        different real break patterns, matching the weekday-aware
        capacity table (`_capacity`, v5.8) the rest of the app already
        assumes — falling back to the all-days blend otherwise (most
        users won't have 10+ of one specific weekday at first; the
        honesty gate degrades per-weekday, not to silence). Per-event
        judgment (the pull-back, the doomscroll insight above) doesn't
        reach every situation; a budget changes behaviour where nagging
        fails. Needs n>=10 real workdays in history (any weekday) to
        speak at all."""
        now_hour = dt.datetime.now().hour if now_hour is None else now_hour
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        today_iso = self.today.isoformat()
        idx = day_index()
        real_days = {iso for iso, rec in idx.items()
                    if cutoff <= iso < today_iso and rec["work"] >= 3 * 60}
        if len(real_days) < 10:
            return None
        weekday_days = {iso for iso in real_days if
                        dt.date.fromisoformat(iso).weekday() == self.today.weekday()}
        per_weekday = len(weekday_days) >= 10
        norm_pool = weekday_days if per_weekday else real_days
        norms = sorted(idx[iso]["brk"] for iso in norm_pool)
        norm = norms[len(norms) // 2]
        cum_by_day = dict.fromkeys(real_days, 0)
        for r in read_rows():
            if r[1] != "break" or r[0] not in real_days:
                continue
            try:
                h = int(r[2].split(":")[0]) % 24
                cum_by_day[r[0]] += int(r[4]) if h <= now_hour else 0
            except (ValueError, IndexError):
                continue
        typical = sorted(cum_by_day.values())[len(cum_by_day) // 2]
        today_brk = idx.get(today_iso, {"brk": 0})["brk"]
        norm_label = (f"~{norm}m ({self.today:%a}s)" if per_weekday
                     else f"~{norm}m")
        return (f"breaks so far {today_brk}m · your typical by this hour "
               f"{typical}m · full-day norm {norm_label}")

    _DECAY_BUCKETS = [(0, 30), (30, 45), (45, 60), (60, 75), (75, 999)]

    def _decay_cycle(self, days=90):
        """Backlog #38 core: bucket work blocks (a run of consecutive
        same-task work rows, same definition _procrastination_insight
        uses) by length, and compare the average break that immediately
        follows each bucket — where break length jumps sharply is the
        personal focus cycle, not an imposed pomodoro number. Returns
        (cycle_min, ratio, avg_after, baseline_avg) or None. n>=3 per
        bucket, needs 2+ populated buckets to compare against."""
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        by_day = {}
        for r in read_rows():
            if r[0] >= cutoff:
                by_day.setdefault(r[0], []).append(r)
        bucket_breaks = {b: [] for b in self._DECAY_BUCKETS}
        for rows in by_day.values():
            rows.sort(key=lambda r: r[2])
            i = 0
            while i < len(rows):
                r = rows[i]
                if r[1] == "break":
                    i += 1
                    continue
                run, j = 0, i
                while j < len(rows) and rows[j][1] != "break":
                    try:
                        run += int(rows[j][4])
                    except ValueError:
                        pass
                    j += 1
                if j < len(rows) and rows[j][1] == "break":
                    try:
                        bmin = int(rows[j][4])
                    except ValueError:
                        bmin = None
                    if bmin is not None:
                        for lo, hi in self._DECAY_BUCKETS:
                            if lo <= run < hi:
                                bucket_breaks[(lo, hi)].append(bmin)
                                break
                    i = j + 1
                else:
                    i = j
        stats = [(b, sum(v) / len(v)) for b, v in bucket_breaks.items()
                 if len(v) >= 3]
        if len(stats) < 2:
            return None
        stats.sort(key=lambda x: x[0][0])
        baseline = stats[0][1]
        if baseline <= 0:
            return None
        for (lo, hi), avg in stats[1:]:
            if avg >= baseline * 1.8:
                return lo, avg / baseline, avg, baseline
        return None

    def _block_decay_lines(self, days=90):
        """One line, or none: the #38 insight, formatted from
        _decay_cycle. 'Blocks past ~55m are followed by 3x longer
        breaks; your natural cycle looks like ~55m — box accordingly.'"""
        cyc = self._decay_cycle(days)
        if not cyc:
            return []
        cycle_min, ratio, avg, baseline = cyc
        return [f"blocks past ~{cycle_min}m are followed by {ratio:.1f}x "
                f"longer breaks ({avg:.0f}m vs {baseline:.0f}m) — your "
                f"natural cycle looks like ~{cycle_min}m, box accordingly"]

    def _suggested_time_box(self):
        """Minutes for a suggested [Xm] time-box on a SIGNAL task, read
        from the personal decay curve. None without enough history —
        never guesses a pomodoro number out of thin air."""
        cyc = self._decay_cycle()
        return cyc[0] if cyc else None

    def _first_hour_audit(self, days=90):
        """Backlog #40: classify each day's FIRST work interval as
        signal or not (via that day's own SIGNAL line), then compare
        the day's total hours between signal-first and other-first
        days. Pure csv + per-day SIGNAL text, n>=5 each side."""
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        by_day = {}
        for r in read_rows():
            if r[0] >= cutoff and r[1] == "work":
                by_day.setdefault(r[0], []).append(r)
        sig_first, other_first = [], []
        for iso, rows in by_day.items():
            rows.sort(key=lambda r: r[2])
            day = dt.date.fromisoformat(iso)
            kws = self._signal_kws(day)
            if not kws:
                continue
            total = sum(int(r[4]) for r in rows if r[4].isdigit())
            (sig_first if task_matches(rows[0][5], kws)
             else other_first).append(total)
        if len(sig_first) >= 5 and len(other_first) >= 5:
            sa = sum(sig_first) / len(sig_first) / 60
            oa = sum(other_first) / len(other_first) / 60
            diff = sa - oa
            if abs(diff) >= 0.3:
                verb = "heavier" if diff > 0 else "lighter"
                return [f"days you open with signal work end {abs(diff):.1f}h "
                        f"{verb} than days you open with something else "
                        f"(n={len(sig_first)} vs {len(other_first)}) — the "
                        "first hour is a lever, not a warm-up."]
        return []

    def _day_switches(self, day):
        """Distinct task-switches on `day`: how many times a work
        interval's task differs from the one immediately before it, in
        start-time order. Not interval count (breaks don't count as
        switches) and not duration (#38 covers that already)."""
        rows = sorted((r for r in read_rows() if r[0] == day.isoformat()
                       and r[1] == "work"), key=lambda r: r[2])
        return sum(1 for a, b in zip(rows, rows[1:])
                  if a[5].strip().lower() != b[5].strip().lower())

    def _thrash_insight(self, days=60):
        """Backlog #16: days with many task-switches vs days with few,
        compared on signal share. Distinct from #38 (block DURATION):
        this measures how many times you jumped, not how long you
        stayed. n>=3 thrashy and n>=3 focused days to speak."""
        cutoff = (self.today - dt.timedelta(days=days)).isoformat()
        by_day = {}
        for r in read_rows():
            if r[0] >= cutoff and r[1] == "work":
                by_day.setdefault(r[0], []).append(r)
        thrashy, focused = [], []
        for iso in by_day:
            day = dt.date.fromisoformat(iso)
            kws = self._signal_kws(day)
            if not kws:
                continue
            sig, work = self._day_signal(day, kws)
            if work <= 0:
                continue
            pct = 100 * sig / work
            switches = self._day_switches(day)
            if switches >= 6:
                thrashy.append(pct)
            elif switches <= 2:
                focused.append(pct)
        if len(thrashy) >= 3 and len(focused) >= 3:
            ta = sum(thrashy) / len(thrashy)
            fa = sum(focused) / len(focused)
            if fa - ta >= 10 and fa > 0:
                drop = round(100 * (fa - ta) / fa)
                return [f"days with 6+ task switches average {drop}% less "
                        f"signal work than your focused days (≤2 switches) "
                        f"— {ta:.0f}% vs {fa:.0f}% signal "
                        f"(n={len(thrashy)} vs {len(focused)})"]
        return []

    def _shallow_threshold(self):
        """The block-length line under which SIGNAL work reads as
        shallow — from the personal decay cycle (#38) when available,
        else a flat 20-minute default. Shared so every 'shallow work'
        check (today's line, the lag-correlation check below) uses the
        same personal definition, not a threshold recomputed per call."""
        cyc = self._decay_cycle()
        return max(10, int(cyc[0] * 0.4)) if cyc else 20

    def _day_shallow_frac(self, day, kws=None, threshold=None):
        """(shallow_min, total_min) of one day's matched-SIGNAL work
        blocks — 'shallow' meaning under `threshold`. None if no signal
        is declared for that day or there's no matching work at all.
        Generalises the old today-only inline logic so backlog #70's
        lag-correlation check can reuse it for any day, not just today."""
        if kws is None:
            kws = self._signal_kws(day)
        if not kws:
            return None
        if threshold is None:
            threshold = self._shallow_threshold()
        rows = sorted((r for r in read_rows()
                       if r[0] == day.isoformat() and r[1] == "work"),
                      key=lambda r: r[2])
        if not rows:
            return None
        blocks = []
        i = 0
        while i < len(rows):
            t = rows[i][5].strip().lower()
            run, j = 0, i
            while j < len(rows) and rows[j][5].strip().lower() == t:
                try:
                    run += int(rows[j][4])
                except ValueError:
                    pass
                j += 1
            if task_matches(rows[i][5], kws):
                blocks.append(run)
            i = j
        total = sum(blocks)
        if total < 60:
            return None
        shallow = sum(b for b in blocks if b < threshold)
        return shallow, total

    def _shallow_work_lines(self):
        """Backlog #49: same-day depth, not switch-counting (#16) or
        what follows a block (#38). What fraction of TODAY's signal
        hours came in blocks under threshold. Needs 1h+ of signal work
        today to be a fair sample."""
        threshold = self._shallow_threshold()
        frac = self._day_shallow_frac(self.today, threshold=threshold)
        if not frac:
            return []
        shallow, total = frac
        pct = round(100 * shallow / total)
        if pct >= 50:
            return [f"{pct}% of today's signal hours came in blocks under "
                    f"{threshold}m — that reads as busy, not deep."]
        return []

    def _graveyard_lines(self):
        """Backlog #43: once a month (first Monday), name Task-library
        items sitting untouched 60+ days. 'Untouched' is approximated
        by ADDED date — there's no separate last-touched tracking, an
        honest simplification rather than the ideal signal. Never
        auto-deletes; one prompt, then silence for another month."""
        if self.today.weekday() != 0 or self.today.day > 7:
            return []
        cutoff = (self.today - dt.timedelta(days=60)).isoformat()
        old = [t for t in self.settings.get("tasks", [])
               if t.get("added", "9999") <= cutoff]
        if not old:
            return []
        names = ", ".join(t["name"][:40] for t in old[:5])
        more = f" (+{len(old) - 5} more)" if len(old) > 5 else ""
        return [f"library graveyard: {len(old)} item(s) older than 60 days "
                f"— still real? start one, re-date it, or delete it: "
                f"{names}{more}"]

    def _best_weeks_lines(self, weeks=16, top_n=3):
        """Backlog #58: the owner's own best historical weeks (by
        signal hours x signal share, a quality-weighted score) and what
        was distinctive about them — a positive-framed complement to a
        mostly diagnostic-of-problems insight set. n>=8 real weeks
        needed to rank meaningfully; silent otherwise."""
        idx = day_index()
        this_mon = self.today - dt.timedelta(days=self.today.weekday())
        names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]
        weeks_data = []
        for k in range(1, weeks + 1):
            mon = this_mon - dt.timedelta(weeks=k)
            sig_h = work_h = 0.0
            wd_sig = [0.0] * 7
            for i in range(7):
                d = mon + dt.timedelta(days=i)
                rec = idx.get(d.isoformat())
                if not rec or rec["work"] <= 0:
                    continue
                kws = self._signal_kws(d)
                s = self._day_signal(d, kws)[0] if kws else 0
                sig_h += s / 60
                work_h += rec["work"] / 60
                wd_sig[i] = s / 60
            if work_h > 0:
                pct = sig_h / work_h
                weeks_data.append((mon, sig_h * pct, sig_h, pct, wd_sig))
        if len(weeks_data) < 8:
            return []
        weeks_data.sort(key=lambda x: -x[1])
        top = weeks_data[:top_n]
        wd_totals = [0.0] * 7
        for _, _, _, _, wd_sig in top:
            for i in range(7):
                wd_totals[i] += wd_sig[i]
        best_day = names[wd_totals.index(max(wd_totals))]
        avg_h = sum(t[2] for t in top) / len(top)
        avg_pct = sum(t[3] for t in top) / len(top) * 100
        return [f"your {len(top)} best weeks in the last {weeks} averaged "
                f"{avg_h:.1f}h signal at {avg_pct:.0f}% share, most of it "
                f"landing on {best_day}s — worth protecting that pattern"]

    # ----- generic metrics line (the health-hub / biohacking primitive) -----
    #
    # SIGNAL/AVOID/ENERGY/mood each got their own bespoke one-line parser as
    # a new axis came up. METRICS is the generalisation: ONE free-form line
    # + ONE parser that takes any future personal metric (meditation
    # minutes, caffeine mg, cold exposure, water, supplements, a mood
    # scale, anything) without new code per metric. Answers "did we
    # capture everything" not by guessing every future variable in advance
    # (against the project's own no-speculative-sources rule) but by making
    # the COST of adding one, the day it's actually wanted, one typed word.

    METRICS_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*[=:]\s*(.+)$")
    METRICS_BARE_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    @classmethod
    def _metrics_from_text(cls, text):
        """First 'METRICS: ...' line -> {key: value}. Comma-separated
        tokens: 'key=val'/'key:val' (value parses as float when possible,
        else stays the typed string) OR a bare word, which shorthand-logs
        as key=1 — lower friction for yes/no habits ('METRICS: meditation,
        cold_shower' instead of typing '=1' on each). Missing line -> {}."""
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("metrics:"):
                out = {}
                for tok in s[8:].split(","):
                    tok = tok.strip()
                    if not tok:
                        continue
                    m = cls.METRICS_RE.match(tok)
                    if m:
                        key, val = m.group(1).lower(), m.group(2).strip()
                        try:
                            out[key] = float(val)
                        except ValueError:
                            out[key] = val.lower()
                    elif cls.METRICS_BARE_RE.match(tok):
                        out[tok.lower()] = 1.0
                return out
        return {}

    def _day_metrics(self, day=None):
        if day is None or day == self.today:
            return self._metrics_from_text(self.diary.get("1.0", "end-1c"))
        try:
            with open(self.diary_path(day), encoding="utf-8") as f:
                return self._metrics_from_text(f.read())
        except OSError:
            return {}

    def _metrics_insight(self, days=60):
        """The generic payoff: for every metric key you've typed, compare
        signal share on days you logged it (any value) vs days you had
        tracked work but didn't — same shape as the mood insight, but
        works for whatever key you invent tomorrow, not a fixed list.
        Names the single metric with the biggest swing; n>=5 both sides,
        n>=10 total tracked days for a fair baseline."""
        cutoff = self.today - dt.timedelta(days=days)
        idx = day_index()
        by_key_in, by_key_out, all_pcts = {}, {}, []
        d = cutoff
        while d <= self.today:
            rec = idx.get(d.isoformat())
            if rec and rec["work"] > 0:
                kws = self._signal_kws(d)
                if kws:
                    sig, work = self._day_signal(d, kws)
                    if work > 0:
                        pct = 100 * sig / work
                        all_pcts.append(pct)
                        logged = self._day_metrics(d)
                        for k in set(list(logged) + list(by_key_in)
                                    + list(by_key_out)):
                            bucket = by_key_in if k in logged else by_key_out
                            bucket.setdefault(k, []).append(pct)
            d += dt.timedelta(days=1)
        if len(all_pcts) < 10:
            return []
        best = None      # (abs_diff, key, diff, n_in, n_out)
        for k in by_key_in:
            ins, outs = by_key_in[k], by_key_out.get(k, [])
            if len(ins) < 5 or len(outs) < 5:
                continue
            diff = sum(ins) / len(ins) - sum(outs) / len(outs)
            if best is None or abs(diff) > best[0]:
                best = (abs(diff), k, diff, len(ins), len(outs))
        if best and best[0] >= 10:
            _adiff, key, diff, n_in, n_out = best
            verb = "higher" if diff > 0 else "lower"
            return [f"days you logged '{key}': signal {abs(diff):.0f} points "
                    f"{verb} ({n_in}d logged vs {n_out}d not) — worth "
                    "tracking on purpose, not by accident"]
        return []

    @staticmethod
    def _mood_from_text(text):
        """The optional word after the 1-5 number on the ENERGY line —
        'ENERGY: 3 anxious' -> 'anxious'. Mood (how it felt) is a
        different axis than energy (how much fuel there was) — backlog
        #4. None if no word was given."""
        for line in text.splitlines():
            s = line.strip()
            if s.lower().startswith("energy:"):
                m = re.search(r"[1-5]\s*([a-zA-Z]+)", s[7:])
                return m.group(1).lower() if m else None
        return None

    def _day_mood(self, day):
        try:
            with open(self.diary_path(day), encoding="utf-8") as f:
                return self._mood_from_text(f.read())
        except OSError:
            return None

    def _mood_insight(self, days=90):
        """Backlog #4: groups days by their logged mood WORD and
        compares average signal share against the overall baseline —
        naming the mood with the biggest departure. Mood and energy
        aren't the same axis; this is the mood half. n>=3 days per
        mood word, n>=10 total days to have a real baseline."""
        cutoff = self.today - dt.timedelta(days=days)
        idx = day_index()
        by_mood, all_pcts = {}, []
        d = cutoff
        while d <= self.today:
            rec = idx.get(d.isoformat())
            if rec and rec["work"] > 0:
                kws = self._signal_kws(d)
                if kws:
                    sig, work = self._day_signal(d, kws)
                    if work > 0:
                        pct = 100 * sig / work
                        all_pcts.append(pct)
                        mood = self._day_mood(d)
                        if mood:
                            by_mood.setdefault(mood, []).append(pct)
            d += dt.timedelta(days=1)
        if len(all_pcts) < 10:
            return []
        baseline = sum(all_pcts) / len(all_pcts)
        best_mood = best_diff = best_avg = best_n = None
        for mood, pcts in by_mood.items():
            if len(pcts) < 3:
                continue
            avg = sum(pcts) / len(pcts)
            diff = avg - baseline
            if best_mood is None or abs(diff) > abs(best_diff):
                best_mood, best_diff, best_avg, best_n = mood, diff, avg, len(pcts)
        if best_mood and abs(best_diff) >= 10:
            verb = "higher" if best_diff > 0 else "lower"
            return [f"days logged '{best_mood}' average {best_avg:.0f}% "
                    f"signal, {abs(best_diff):.0f} points {verb} than your "
                    f"{baseline:.0f}% overall (n={best_n}) — mood and energy "
                    "aren't the same axis"]
        return []

    _INSIGHT_THEMES = ("TIME & FOCUS", "ENERGY & BODY", "MOMENTUM & TRENDS")

    def _insight_lines(self, days=60):
        """Flat text for callers that don't care about theme (life
        review's top-3 excerpt) — same findings as _insight_lines_grouped,
        theme tags stripped."""
        return [line for _, line in self._insight_lines_grouped(days)]

    def _insight_lines_grouped(self, days=60):
        """Backlog #86: the 20+ independent findings below used to
        concatenate into one undifferentiated block — the flat-text
        problem v8.64 already fixed for the View menu, not yet fixed
        here. Each finding is tagged with one of _INSIGHT_THEMES at the
        point it's generated (a text classifier over the rendered
        sentences would be guesswork and rot as wording changes; tagging
        at the source is exact and free). Rule-based findings that each
        connect two data sources the app already collects. Every line is
        your own history — it only speaks when there are enough samples
        to mean something."""
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
            out.append(("ENERGY & BODY",
                       f"on days you tracked work: after ≥7h sleep you "
                       f"averaged {g:.1f}h of work ({len(good)} such days) "
                       f"vs {s:.1f}h after <7h sleep ({len(short)} days) "
                       f"— a {g - s:+.1f}h/day difference"))
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
            out.append(("ENERGY & BODY",
                       f"on days you tracked work: energy ≥4 averaged "
                       f"{sum(ehi) / len(ehi) / 60:.1f}h of work "
                       f"({len(ehi)} days) vs {sum(elo) / len(elo) / 60:.1f}h "
                       f"on energy ≤2 days ({len(elo)} days) — protect what "
                       "charges you, it IS the productivity"))
        g_e = [e for sl, e in en_sl if sl >= 7]
        s_e = [e for sl, e in en_sl if sl < 7]
        if len(g_e) >= 3 and len(s_e) >= 3:
            out.append(("ENERGY & BODY",
                       f"energy after ≥7h sleep: {sum(g_e) / len(g_e):.1f}/5 · "
                       f"after <7h: {sum(s_e) / len(s_e):.1f}/5 — your own "
                       "body, measured"))
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
            out.append(("TIME & FOCUS",
                       f"deep hours {h0:02d}–{h0 + 3:02d}: "
                       f"{round(100 * best / tot)}% of all your work lands "
                       "there — guard that window, schedule meetings outside it"))
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
            out.append(("TIME & FOCUS",
                       f"average unbroken work block {ca:.0f}m this week vs "
                       f"{pa:.0f}m the 3 weeks before — {verdict}"))
        # estimate honesty
        ef = self._estimate_factor()
        if ef:
            out.append(("MOMENTUM & TRENDS",
                       f"estimates: actuals run ×{ef[0]:.1f} across "
                       f"{ef[1]} finished tasks — read every [2h] as "
                       f"{2 * ef[0]:.1f}h when planning"))
        # streaks — an honestly-declared short day (#37's TODAY: line)
        # never breaks it; only checked within a recent lookback so an
        # old declared day doesn't force a file-open per day across the
        # full 112-day best-streak scan
        def active(d):
            if (idx.get(d.isoformat()) or {"work": 0})["work"] >= 30:
                return True
            if (self.today - d).days <= 21:
                return self._declared_cap_h(d) is not None
            return False
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
            out.append(("MOMENTUM & TRENDS",
                       f"streak: {run} active day(s) (≥30m) · best in "
                       f"16 weeks: {best}"))

        # weekday patterns — is one day of the week genuinely weaker,
        # not just noise. Needs every weekday represented (n>=3 each)
        # before it speaks at all.
        wd_buckets = [[] for _ in range(7)]
        for i in range(1, days + 1):
            d = self.today - dt.timedelta(days=i)
            w = (idx.get(d.isoformat()) or {"work": 0})["work"]
            if w > 0:
                wd_buckets[d.weekday()].append(w)
        if all(len(b) >= 3 for b in wd_buckets):
            names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            avgs = [sum(b) / len(b) / 60 for b in wd_buckets]
            best_i = max(range(7), key=lambda i: avgs[i])
            worst_i = min(range(7), key=lambda i: avgs[i])
            if avgs[best_i] > 0:
                diff_pct = round(100 * (avgs[best_i] - avgs[worst_i]) / avgs[best_i])
                if diff_pct >= 20:
                    out.append(("TIME & FOCUS",
                              f"{names[worst_i]}s average {avgs[worst_i]:.1f}h vs "
                              f"{names[best_i]}s at {avgs[best_i]:.1f}h — "
                              f"{diff_pct}% weaker, worth knowing before "
                              "scheduling something hard there"))

        # meeting load vs deep hours — does a busy calendar day actually
        # cost you focus, or do you work around it fine
        busy_data = self._busy_data()
        heavy, light = [], []
        for i in range(1, days + 1):
            d = self.today - dt.timedelta(days=i)
            iso = d.isoformat()
            w = (idx.get(iso) or {"work": 0})["work"]
            if w <= 0:
                continue
            (heavy if busy_data.get(iso, 0.0) >= 2 else light).append(w)
        if len(heavy) >= 3 and len(light) >= 3:
            ha = sum(heavy) / len(heavy) / 60
            la = sum(light) / len(light) / 60
            verdict = ("meetings are eating your focus" if ha < 0.85 * la
                      else "holding up fine around meetings")
            out.append(("TIME & FOCUS",
                       f"days with ≥2h of meetings: {ha:.1f}h of work "
                       f"({len(heavy)} days) vs {la:.1f}h on lighter-calendar "
                       f"days ({len(light)} days) — {verdict}"))

        # meeting fragmentation tax (backlog #21): the load check above
        # only counts HOURS; this prices the SPLITTING a meeting does to
        # the open time around it
        out += [("TIME & FOCUS", l) for l in self._meeting_fragmentation_lines()]

        # break-ratio drift — is the work:break balance creeping the
        # wrong way, not just this week being unusually chatty
        monday = self.today - dt.timedelta(days=self.today.weekday())
        prev_lo = monday - dt.timedelta(days=21)
        cur_w = cur_b = prev_w = prev_b = 0
        for r in read_rows():
            try:
                rd = dt.date.fromisoformat(r[0])
                m = int(r[4])
            except ValueError:
                continue
            if rd >= monday:
                cur_b, cur_w = (cur_b + m, cur_w) if r[1] == "break" else (cur_b, cur_w + m)
            elif rd >= prev_lo:
                prev_b, prev_w = (prev_b + m, prev_w) if r[1] == "break" else (prev_b, prev_w + m)
        if cur_w + cur_b >= 5 * 60 and prev_w + prev_b >= 15 * 60:
            cur_ratio = cur_b / (cur_w + cur_b)
            prev_ratio = prev_b / (prev_w + prev_b)
            if cur_ratio > prev_ratio + 0.10:
                out.append(("TIME & FOCUS",
                           f"breaks are {round(100 * cur_ratio)}% of tracked "
                           f"time this week vs {round(100 * prev_ratio)}% the "
                           "3 weeks before — drifting, worth a look"))

        out += [("TIME & FOCUS", l) for l in self._procrastination_insight()]
        out += [("TIME & FOCUS", l) for l in self._break_insight()]
        out += [("TIME & FOCUS", l) for l in self._block_decay_lines()]
        out += [("TIME & FOCUS", l) for l in self._first_hour_audit()]
        out += [("TIME & FOCUS", l) for l in self._thrash_insight()]
        out += [("TIME & FOCUS", l) for l in self._shallow_work_lines()]
        out += [("ENERGY & BODY", l) for l in self._mood_insight()]
        out += [("MOMENTUM & TRENDS", l) for l in self._metrics_insight()]
        out += [("ENERGY & BODY", l) for l in self._daylight_insight()]
        out += [("MOMENTUM & TRENDS", l) for l in self._word_drift_insight()]
        out += [("MOMENTUM & TRENDS", l) for l in self._word_fade_insight()]
        out += [("MOMENTUM & TRENDS", l) for l in self._lag_insight()]
        out += [("MOMENTUM & TRENDS", l) for l in self._best_weeks_lines()]
        out += [("MOMENTUM & TRENDS", l) for l in self._trajectory_lines()]
        out += [("MOMENTUM & TRENDS", l) for l in self._signal_tier_insight()]
        out += [("TIME & FOCUS", l) for l in self._commitment_drift_lines()]
        return out

    def _signal_tier_insight(self, days=60):
        """Backlog #96: now that SIGNAL2 exists as a real second tier,
        name the split honestly over time — not just today's live line,
        a trailing-window read of how much went to the sharpest priority
        vs the next one down. Only speaks on days SIGNAL2 was actually
        declared (an unused feature should stay silent, not report 0%
        as if that meant something); n>=5 such days before it speaks."""
        cutoff = self.today - dt.timedelta(days=days)
        idx = day_index()
        tot_work = tot_sig = tot_sig2 = active_days = 0
        d = cutoff
        while d < self.today:                # today isn't finished yet
            rec = idx.get(d.isoformat())
            if rec and rec["work"] > 0:
                kws1 = self._signal_kws(d)
                kws2 = self._signal2_kws(d)
                if kws2:
                    sig, work = self._day_signal(d, kws1)
                    sig2, _ = self._day_signal2(d, kws2, kws1)
                    tot_work += work
                    tot_sig += sig
                    tot_sig2 += sig2
                    active_days += 1
            d += dt.timedelta(days=1)
        if active_days < 5 or not tot_work:
            return []
        return [f"tier-2 priorities: over the last {active_days} day(s) you "
               f"declared one, {round(100 * tot_sig / tot_work)}% went to "
               f"tier-1 and {round(100 * tot_sig2 / tot_work)}% to tier-2 "
               "— worth knowing if tier-2 is quietly eating tier-1's time"]

    def _trajectory_lines(self, weeks=8):
        """The longitudinal, cross-domain view the other insights can't
        give: split the last `weeks` weeks in half, compare the earlier
        half against the recent one across domains — work, sleep, signal —
        and name the sharpest TRADE-OFF, the thing you're buying with the
        thing you're spending. Everything else in this section tops out at
        3-4 weeks; this is the first 'life at the scale of months' read,
        the seed of the trajectory/memory direction in HANDOFF."""
        idx = day_index()
        half = weeks * 7 // 2
        recent_lo = self.today - dt.timedelta(days=half - 1)
        prior_lo = self.today - dt.timedelta(days=2 * half - 1)

        def acc(lo, hi):
            work = sig = active = 0
            sleeps = []
            d = lo
            while d <= hi:
                rec = idx.get(d.isoformat())
                if rec and rec["work"] > 0:
                    work += rec["work"]
                    sig += self._day_signal(d)[0]
                    active += 1
                sl = self._sleep_h(d.isoformat())
                if sl:
                    sleeps.append(sl)
                d += dt.timedelta(days=1)
            return {"work": work, "sig": sig, "active": active, "sleeps": sleeps}

        a = acc(prior_lo, recent_lo - dt.timedelta(days=1))
        b = acc(recent_lo, self.today)
        # both halves need real work history or the comparison is noise
        if a["active"] < 5 or b["active"] < 5:
            return []

        def arrow(x, y, thr):
            return "↑" if y >= x + thr else "↓" if y <= x - thr else "→"

        wpw = (a["work"] / 60 / (half / 7), b["work"] / 60 / (half / 7))
        parts, moved = [], {}
        aw = arrow(*wpw, 1.0)
        parts.append(f"work {wpw[0]:.1f}→{wpw[1]:.1f}h/wk {aw}")
        moved["work"] = aw
        if len(a["sleeps"]) >= 5 and len(b["sleeps"]) >= 5:
            sl = (sum(a["sleeps"]) / len(a["sleeps"]),
                  sum(b["sleeps"]) / len(b["sleeps"]))
            asl = arrow(*sl, 0.3)
            parts.append(f"sleep {sl[0]:.1f}→{sl[1]:.1f}h {asl}")
            moved["sleep"] = asl
        if a["work"] and b["work"] and (a["sig"] or b["sig"]):
            sg = (100 * a["sig"] / a["work"], 100 * b["sig"] / b["work"])
            asig = arrow(*sg, 8)
            parts.append(f"signal {round(sg[0])}→{round(sg[1])}% {asig}")
            moved["signal"] = asig
        if not any(v != "→" for v in moved.values()):
            return []                       # nothing really moved — stay quiet

        out = [f"{weeks}-week trajectory: " + ", ".join(parts)]
        # the sharpest trade-off, named — one thing bought with another
        if moved.get("work") == "↑" and moved.get("sleep") == "↓":
            out.append("  → you're buying work hours with sleep — a sprint "
                       "move, not a season; watch the energy insight above")
        elif moved.get("work") == "↓" and moved.get("sleep") == "↑":
            out.append("  → fewer work hours, more sleep — recovery if it's "
                       "chosen, drift if it isn't")
        elif moved.get("work") == "↑" and moved.get("signal") == "↓":
            out.append("  → more hours, less of them on-signal — busier, not "
                       "necessarily closer to what matters")
        elif moved.get("work") == "↓" and moved.get("signal") == "↑":
            out.append("  → fewer hours but better aimed — leverage, as long "
                       "as the totals still clear your deadlines")
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
               "app": "TimerDiary v7.0",
               "goals": self.goals(),
               "deadlines": self.deadlines(),
               "capacity_per_weekday": self._capacity(),
               "days": days}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        self.status.config(text=f"Life record exported — {len(days)} day(s) "
                                f"→ {os.path.basename(path)}. Plain JSON, "
                                "yours forever.")

    def _import_life_json(self):
        """Restores goals/deadlines/capacity (merged by name — never
        silently replaces what's already configured) and day files
        (only ones missing locally — never overwrites current work)
        from a previously exported life record. Deliberately does NOT
        try to rebuild sessions.csv from the JSON's per-day aggregates —
        that would be a lossy reconstruction (no individual start/end
        times survive aggregation). Run Tools > Rebuild sessions.csv
        from day files afterward instead: the restored day files carry
        the full original event log, so that path is lossless."""
        path = filedialog.askopenfilename(
            parent=self, filetypes=[("JSON", "*.json")],
            title="Import a life record (JSON)")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            messagebox.showerror(APP_NAME, f"Couldn't read that file:\n{e}")
            return
        days = data.get("days", {})
        ddir = self.diary_dir()
        new_files = [iso for iso, rec in days.items()
                    if rec.get("diary") and not os.path.exists(
                        os.path.join(ddir, f"{iso}.txt"))]
        n_goals = len({g["name"] for g in data.get("goals", [])}
                      - {g["name"] for g in self.goals()})
        n_dls = len({d["name"] for d in data.get("deadlines", [])}
                    - {d["name"] for d in self.deadlines()})
        if not messagebox.askyesno(
                APP_NAME,
                f"Import from {os.path.basename(path)}?\n\n"
                f"• {n_goals} new goal(s), {n_dls} new deadline(s) "
                "(merged by name — nothing existing gets replaced)\n"
                f"• {len(new_files)} day file(s) restored (only ones you "
                "don't already have locally — nothing here gets "
                "overwritten)\n\n"
                "Afterward: Tools > Rebuild sessions.csv from day files "
                "to regenerate the session log losslessly from what's "
                "restored."):
            return

        def merge_named(existing, incoming):
            names = {x["name"] for x in existing}
            return existing + [x for x in incoming if x["name"] not in names]

        self.settings["goals"] = merge_named(self.goals(), data.get("goals", []))
        self.settings["deadlines"] = merge_named(
            self.deadlines(), data.get("deadlines", []))
        if data.get("capacity_per_weekday"):
            self.settings["capacity"] = data["capacity_per_weekday"]
        save_settings(self.settings)
        for iso in new_files:
            with open(os.path.join(ddir, f"{iso}.txt"), "w",
                      encoding="utf-8") as f:
                f.write(days[iso]["diary"])
        self._load_diary()
        self._refresh_totals()
        self.status.config(
            text=f"Imported: +{n_goals} goal(s), +{n_dls} deadline(s), "
                f"{len(new_files)} day file(s) restored. Now try Tools > "
                "Rebuild sessions.csv from day files.")

    # ----- data doctor (keep the substrate clean) -----

    def _sensor_health_lines(self, days=30):
        """Backlog #23: the platform watching its own instruments.
        Every insight silently degrades when a source rots — the phone
        sleep-export automation breaks, the .ics goes stale, ENERGY
        stops being typed — with nothing ever surfacing that until an
        insight just quietly stops appearing. Per source: last date
        seen with real data, coverage % over the trailing `days` days,
        a plain alarm once it's gone quiet longer than a reasonable
        cadence. Also surfaces the personal baselines the anomaly
        watch judges against (median sleep, median week) so the
        co-pilot's calls are inspectable, not oracular."""
        hd = self._health_data()
        lines = ["SENSOR HEALTH:"]

        sleep_isos = sorted(iso for iso, rec in hd.items() if rec.get("sleep_h"))
        if sleep_isos:
            last = sleep_isos[-1]
            gap = (self.today - dt.date.fromisoformat(last)).days
            cutoff = (self.today - dt.timedelta(days=days - 1)).isoformat()
            cov = round(100 * sum(1 for iso in sleep_isos if iso >= cutoff)
                       / days)
            line = (f"  sleep import: last seen {last} ({gap}d ago), "
                   f"{cov}% coverage")
            if gap > 10:
                line += " — the phone automation may have stopped"
            lines.append(line)
        else:
            lines.append("  sleep import: no data seen yet")

        path = self.settings.get("ics_path")
        if not path:
            lines.append("  calendar: not configured")
        elif not os.path.exists(path):
            lines.append("  calendar: configured path not found")
        else:
            age_days = (self.today -
                       dt.datetime.fromtimestamp(os.path.getmtime(path)).date()).days
            line = f"  calendar: export file last updated {age_days}d ago"
            if age_days > 14:
                line += " — may have gone stale"
            lines.append(line)

        logged, last_energy = 0, None
        for i in range(days):
            d = self.today - dt.timedelta(days=i)
            if self._day_energy(d) is not None:
                logged += 1
                if last_energy is None:
                    last_energy = d
        if last_energy:
            gap = (self.today - last_energy).days
            line = (f"  ENERGY: last typed {last_energy.isoformat()} "
                   f"({gap}d ago), {round(100 * logged / days)}% coverage")
            if gap > 5:
                line += " — you've stopped logging it"
            lines.append(line)
        else:
            lines.append("  ENERGY: never typed")

        hist_sleep = sorted(v for v in
                           (rec.get("sleep_h") for rec in hd.values()) if v)
        if len(hist_sleep) >= 10:
            lines.append(f"  your normal sleep: "
                         f"{hist_sleep[len(hist_sleep) // 2]:.1f}h "
                         f"(median, n={len(hist_sleep)})")
        weekly = {}
        for iso, rec in day_index().items():
            iso_date = dt.date.fromisoformat(iso)
            monday = iso_date - dt.timedelta(days=iso_date.weekday())
            weekly[monday] = weekly.get(monday, 0) + rec["work"]
        if len(weekly) >= 4:
            vals = sorted(weekly.values())
            lines.append(f"  your normal week: {vals[len(vals) // 2] / 60:.1f}h "
                         f"tracked (median, n={len(weekly)} weeks)")
        return lines

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
            lines = self._sensor_health_lines() + ["", *lines]
            lines += ["", *self._header_line_adoption_lines()]
            backup_line = backup_integrity_line()
            if backup_line:
                lines = [backup_line, ""] + lines
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

    def _rebuild_csv_from_diary(self):
        """A recovery tool, not a routine one: rebuild sessions.csv
        ENTIRELY from the day .txt files' own event lines. The day file
        is the sacred source of truth — this makes the csv provably
        derivable from it, so a corrupted or lost csv is recoverable as
        long as the day files survive (which is the whole point of the
        sacred rule)."""
        if not messagebox.askyesno(
                APP_NAME,
                "Rebuild sessions.csv entirely from your day files?\n\n"
                "Current csv is backed up first. This REPLACES the csv "
                "with what your day files' own Start/Stop/Task lines say "
                "— use it to recover from a lost or corrupted csv, not "
                "as routine maintenance."):
            return
        if os.path.exists(SESSIONS_CSV):
            bdir = os.path.join(data_dir(), "backups")
            os.makedirs(bdir, exist_ok=True)
            shutil.copy2(SESSIONS_CSV, os.path.join(
                bdir, f"sessions_before_rebuild_{dt.date.today()}.csv"))
        try:
            names = sorted(fn for fn in os.listdir(self.diary_dir())
                           if fn.endswith(".txt"))
        except OSError:
            names = []
        rows, n_files = [], 0
        for fn in names:
            date_iso = fn[:-4]
            try:
                dt.date.fromisoformat(date_iso)
            except ValueError:
                continue   # RECOVERED-... and other non-dated files: skip
            with open(os.path.join(self.diary_dir(), fn), encoding="utf-8") as f:
                rows += parse_day_file_to_rows(f.read(), date_iso)
            n_files += 1
        tmp = SESSIONS_CSV + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(CSV_HEADER)
            w.writerows(rows)
        os.replace(tmp, SESSIONS_CSV)
        self._refresh_totals()
        messagebox.showinfo(
            APP_NAME, f"Rebuilt sessions.csv: {len(rows)} row(s) from "
                      f"{n_files} day file(s). Previous csv backed up "
                      "in backups\\.")

    # ----- calendar export -----

    def _export_ics(self):
        monday = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
        path, n = week_to_ics(monday)
        if messagebox.askyesno(APP_NAME,
                               f"Exported {n} sessions to\n{path}\n\nOpen folder?"):
            self._open_folder()

    def _lock_windows_win(self):
        """Backlog #113 + #135: turn a deadline's (or now a task's)
        abstract 'X hours needed' into concrete real dates worth
        locking, then export the picked ones as .ics events for
        Outlook/Google Calendar — the owner's own ask, 2026-08-07.
        _lock_window_candidates does the ranking; this window is just
        pick-and-export."""
        win = tk.Toplevel(self)
        win.title("Lock study windows")
        win.geometry("560x420")

        top = ttk.Frame(win)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Lock for:").pack(side="left")
        targets = self._lock_targets()
        label_for = {}
        labels = []
        for t in targets:
            if t["kind"] == "deadline":
                lbl = t["name"]
            else:
                suffix = "task, due date" if t["has_due"] else "task, next 7 days"
                lbl = f"{t['name']} ({suffix})"
            label_for[lbl] = t
            labels.append(lbl)
        dl_var = tk.StringVar(value=labels[0] if labels else "")
        combo = ttk.Combobox(top, textvariable=dl_var, state="readonly",
                             values=labels, width=32)
        combo.pack(side="left", padx=(4, 0))

        ttk.Label(win, text="Click a row to pick it, then export.",
                 foreground="#777777").pack(anchor="w", padx=8)
        tree = ttk.Treeview(win, columns=("date", "window", "hours"),
                            show="headings")
        for c, label, w in (("date", "Date", 100), ("window", "Window", 140),
                            ("hours", "Hours", 70)):
            tree.heading(c, text=label)
            tree.column(c, width=w, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        tree.tag_configure("picked", background="#d7ecd7")

        picked, cand = set(), {"list": []}

        def refresh(event=None):
            tree.delete(*tree.get_children())
            picked.clear()
            tgt = label_for.get(dl_var.get())
            cand["list"] = self._lock_window_candidates(tgt) if tgt else []
            if not cand["list"]:
                status.config(text="No open block of 2h+ found before this "
                             "due date — nothing to lock.")
            else:
                status.config(text="")
            for i, w in enumerate(cand["list"]):
                tree.insert("", "end", iid=str(i), values=(
                    f"{w['date']:%a %d.%m}", f"{w['start']:%H:%M}-{w['end']:%H:%M}",
                    f"{w['hours']:.1f}h"))

        def toggle(event):
            row = tree.identify_row(event.y)
            if not row:
                return
            if row in picked:
                picked.discard(row)
                tree.item(row, tags=())
            else:
                picked.add(row)
                tree.item(row, tags=("picked",))
        tree.bind("<Button-1>", toggle)
        combo.bind("<<ComboboxSelected>>", refresh)

        status = ttk.Label(win, foreground="#2e6da4", wraplength=520,
                           justify="left")
        status.pack(fill="x", padx=8, pady=(0, 4))

        def export():
            if not picked:
                status.config(text="Pick at least one window first — click a row.")
                return
            windows = sorted((cand["list"][int(i)] for i in picked),
                            key=lambda w: w["date"])
            name = label_for[dl_var.get()]["name"]
            path, n = lock_windows_to_ics(name, windows)
            when = ", ".join(f"{w['date']:%d.%m} {w['start']:%H:%M}-"
                            f"{w['end']:%H:%M}" for w in windows)
            self._append_text(f"--- Locked {n} window(s) for {name}: "
                              f"{when} (exported {os.path.basename(path)})")
            status.config(text=f"Exported {n} window(s) to {path} — "
                         "import that file into Outlook/Google Calendar.")

        ttk.Button(win, text="Export selected to .ics",
                  command=export).pack(anchor="e", padx=8, pady=(0, 8))
        refresh()

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
