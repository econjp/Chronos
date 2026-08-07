# TimerDiary v9

The old timer's workflow (timer lines + free diary notes in one .txt per day),
with the bottlenecks removed. Run `dist\TimerDiary.exe` — or rebuild it any
time with `build_exe.bat`.

### v9.14 — the weekly co-pilot names its own commitment cost

The Monday WEEK AHEAD block (see below) already netted your recurring
commitments out of its free-hours total, but silently. Now, when the
block fires and you've got real commitments that week, it says so:
"(of which 97.0h already committed: Sleep 59.5h, Day job 37.5h)" — so
the number isn't a mystery anymore.

### v9.13 — commitments in the day file, free/busy shading in month view

The morning header now names today's recurring commitments and their
total cost right in the day file — "commitments today: Day job 7.5h,
Sleep 9.5h (17.0h of 24h already spoken for)." And the calendar's
month view now shades each day white-to-green by how much real free
time it actually has — one glance instead of a separate window.

### v9.12 — commitments learn from your real data

Tools > "Recurring commitments…" now suggests a Sleep row from your
actual tracked history (not a guess) when you haven't set one —
pre-filled, fully editable, never auto-saved. And a new Insights tab
entry flags it if a declared commitment (day job, sleep) has quietly
drifted from what your tracked data actually shows — "declared 09:30
but your last 15 days actually start ~10:15 — worth updating?"

### v9.11 — toolbar calendar button + due-date feasibility check

A 📅 button now sits in the main toolbar (next to Start/Switch/Reset)
— opens the Calendar view directly, no menu digging. And setting a
task's due date now quietly checks whether there's actually enough
real free time before it (given your commitments, calendar, and
locked windows) — "⚠ only 2.1h of real free time before 15.08 — 10h
estimated, 7.9h short." Never blocks the save, just tells you.

### v9.10 — task due-dates via the calendar

Right-click a day in the calendar's month view → **"Set task due
date…"** → pick a task from the library. Shows up as a ⚑ marker on
that day, and as a `Due` column in the Tasks window (⚠ if overdue).
Lightweight on purpose — not a full deadline, just a "done by" flag.

### v9.9 — right-click a calendar slot to lock it

In the calendar's week view (v9.7), right-click any hour cell → pick
a deadline from the menu → that hour gets locked and exported to
.ics, same as "Lock study windows for a deadline" (v9.3) but directly
from the calendar instead of a separate picker.

### v9.8 — recurring commitments (day job, sleep, admin)

Tools > **"Recurring commitments (lunch, day job, sleep, admin)…"**
(the old "Protected time windows," extended) — now supports which
days a block applies to ("Mon-Fri" for a day job, blank for every
day) and windows that cross midnight (sleep, e.g. 23:00-08:30). These
reduce your real available capacity everywhere — deadline math,
lock-windows, the free-time forecast — without ever touching your
real Outlook calendar. Shows up as a background layer in the week
calendar view (v9.7).

### v9.7 — a real week/month calendar view

View > Planning > **"Calendar (week/month)…"** — an Outlook-shaped
week view (hour grid, events at their real time) and month view (date
grid with event names, "+N more" when a day's full), with Prev/Today/
Next and a Week/Month toggle. Shows your imported calendar events and
your own tracked work sessions together, both named. Read-only for
now — for picking specific windows to lock, use "Lock study windows
for a deadline" (v9.3); for a fast glance at just free/busy, use
"Free-time forecast" (v9.6).

### v9.6 — free-time forecast (a simple visual calendar view)

View > Planning > **"Free-time forecast (calendar)…"** — one green/
grey bar per day for the next 3 weeks. Green = free, already netting
out any calendar you've linked (v9.4/v9.5) and protected windows.
Glance-only, no clicking or picking — for that, use "Lock study
windows for a deadline" (v9.3).

### v9.5 — a second calendar path, for when publishing is blocked

File > **"Import calendar CSV (Power Automate export)…"** — if your
Outlook won't let you publish a calendar link (common on school/work
accounts), a no-code Power Automate flow can keep a plain CSV file
current instead. Point the app at that file once; as long as the
external flow keeps running, it stays current the same way the
subscribe link does. See
`private-recommendations/calendar-integration-setup.md` for the
step-by-step setup (personal, not in this repo).

### v9.4 — subscribe to a calendar link (no more manual export)

File > **"Subscribe to a calendar link (.ics URL)…"** — paste your
calendar's own publish/subscribe link (Outlook or Google's "Publish a
calendar" URL) once, and the app fetches it automatically from then
on (refreshed every 60 minutes). No login, no API key. Falls back to
the last-known calendar if a refresh fails, so a flaky connection
doesn't blank out your capacity numbers. The old manual "Calendar
busy-time (.ics)…" file import still works too, for anyone who'd
rather not.

If your calendar doesn't support publishing (common on locked-down
school/work accounts), that's a real limitation for now — see
HANDOFF.md #115 for the Microsoft Graph API sign-in fallback, not
built yet.

### v9.3 — lock study windows for a deadline

File > **"Lock study windows for a deadline (.ics)…"** — picks a
deadline, shows the specific upcoming days with a real 2h+ open block
(calendar busy time already priced in), you pick which ones to lock,
then exports them as calendar events to a .ics file you import into
Outlook/Google Calendar. Turns "you need ~20h before the exam" into
"lock these actual dates."

### v9.2 — two small fixes

- SIGNAL's auto-fill now seeds from your most urgent deadline instead
  of blending every goal's keywords — sharper, less diffuse.
- "Copy status update" now names the current milestone ("Currently on
  ch5, 60% of its hours") instead of a bare date, when a deadline has
  a milestone breakdown.

### v9.1 — two v9.0 follow-ups

- Day timeline gets a 5th color for tier-2 (SIGNAL2) matched time —
  was invisible before, blended into plain work.
- Data doctor now reports header-line adoption: which of the ~12
  optional header conventions you've actually used in the last 60
  days vs never touched.

### v9.0 — flagship: tiered SIGNAL + declared work-block windows

Two real additions to the core data model, not connective fixes:

- **`SIGNAL2:`** — a second, discrete priority tier. "SIGNAL: thesis"
  / "SIGNAL2: hegemon" when two things matter today but one is clearly
  sharper. SIGNAL's own number is untouched — SIGNAL2 is a strictly
  separate bucket, reported alongside it ("signal 45% +20% tier-2"),
  never blended in. Carries forward automatically; the header line
  only shows up once you've actually used it.
- **`WORKBLOCK: 09:00-17:00`** — declare an externally-committed
  window (a day job). Inside it, idle detection and the screen-lock
  break detector both wait about 3x longer before offering to log a
  break, since a quick meeting or email check during already-spoken-
  for time isn't the same as a real break. Carries forward like AVOID.

Both are fully additive — a day file that never uses either line
behaves exactly like before.

### Four backlog items, priority order (v8.69)

- **Capacity fix:** protected windows (lunch, wind-down) now shrink the
  capacity dashboard and cost-of-yes preview, not just the scheduler —
  they used to quietly disagree about whether that hour was available.
- **Cost of yes** also flags pre-existing blocked task-library items
  under the same goal when previewing a new deadline: "heads up: N
  task(s) under 'X' are already blocked".
- **File > "Open a day file…"** is now a lighter in-app picker — a
  recent-days list plus yesterday/a week ago/a month ago jump buttons,
  reading straight into a text pane. The old OS file dialog is still
  there as "Browse for a day file (file picker)…".
- **Insights tab** findings (sleep, energy, deep hours, streaks,
  trends, 20+ of them) are no longer one flat block — grouped under
  TIME & FOCUS / ENERGY & BODY / MOMENTUM & TRENDS. Copy for AI review
  carries the same grouping.

### Quick reference (v8.68)

**Tools > "Quick reference — what does this app do?…"** — a real
two-pane help window: a topic list on the left (WinHelp/CHM style),
a content pane on the right. 13 topics, each explained properly —
every header-line convention (SIGNAL/AVOID/YEAR/ENERGY/METRICS/TODO/
DECIDED/CAPSULE/COMMIT/EXPERIMENT/TODAY), task-box shortcuts, what's
in each View-menu category, and an "easy to forget exists" list.
Hand-written, not rewritten every version.

### Critical fix: SIGNAL was silently dead + less wall of text (v8.66)

**If you've never once typed a value into the SIGNAL line, this fixes
a bug that's been quietly disabling most of the signal-tracking
features since day one.** Tomorrow's header will seed SIGNAL from
your goals automatically, and once that's carrying a real value, the
timeline colors, the status-bar flag, and every insight that reads
signal% (best-weeks, mood, thrash, avoid-trend) will actually have
something to work with.

Also: AVOID/YEAR/METRICS no longer print blank every single day if
you've never used them — one less wall of empty scaffold lines to
scroll past each morning.

### Bug fixes + two small features (v8.65)

- **Fixed**: the task library no longer fills up with duplicates of a
  TODO bullet you're still typing — each growing snapshot used to
  land as its own entry.
- **Completed-task archive**: marking a task Done now keeps it (with
  the hours it actually took) instead of throwing it away.
- **Command shorthand**: type `done: thesis ch4` in the task box to
  mark a matching task done, no clicking required.
- Extreme deadline projections ("~386 days late") now read as "far
  behind" instead of an absurd-sounding specific number.

### View menu, reorganized (v8.64)

22 flat commands are now grouped into **Planning**, **Memory**, and
**Values** — the same three pillars named in HANDOFF.md's NORTH STAR
section — plus Writing/Reports for the rest. Dashboard, "What should
I do now?", and Tasks stay top-level. Same commands, same behavior,
just organized instead of a flat list.

### Focus signature (v8.63)

Neither the weekday-pattern insight (total hours per weekday) nor
`_hour_quality` (total hours per hour-of-day, collapsed across every
weekday) shows the actual two-dimensional shape: WHEN, within which
days, signal work reliably happens. A new line in the Monday review —
read once in a while, not a daily view — names the standout cell of a
(weekday × 4-hour-bucket) consistency grid: `focus signature: Tue
08-12 lights up 100% of the time (n=4); Mon 00-04 never does (n=4)`.
Needs real volume (several weeks per weekday, a real consistency
majority) before it speaks at all.

### Conversation-ready status export (v8.62)

The Life dashboard gains a **Copy status update** button — a different
audience than Copy-for-AI-review. One short, professionally-toned
paragraph per scoped deadline, ready to paste into an email to an
actual supervisor or advisor: `Progress update — Thesis: 12h this week
(up from 8h last). Currently projected 3d behind pace, landing August
04. Blocked on: ch5 draft.` Reuses the numbers the app already
computes, plus the blocked-task field from v8.60 — no new data. This
one surface is deliberately written in a different register on
purpose; the rest of the app stays blunt.

### Cost of yes (v8.61)

Every capacity view only ever looked at deadlines already on the books
— nothing showed what ADDING one would do before you committed. The
deadline edit dialog now previews it live: as soon as a new deadline's
due date and total hours are both typed in, one line updates on every
keystroke — `committing to 'NewProj' would push slack from +5.0h to
-10.0h — Thesis would need to give up 1.0h/day to make room`. Turns the
moment of over-committing, which used to only show up as a ⚠ weeks
later, into a visible choice while it's still cheap to say no.

### Waiting-on / blocked tasks (v8.60)

Real work often depends on someone else, not just your own control.
Tasks window → right-click a row → **Set blocked by…** (free text —
"waiting on advisor reply"). Blocked items stop showing up in the
re-entry-ramp suggestion and both "uncommitted hours → pick from Task
library" lines — the planner stops suggesting things you structurally
can't do yet — and get a ⛔ marker inline so they don't just vanish. The
Life dashboard's **Deadlines & Goals** tab gains a new **WAITING ON:**
section listing them with their blocker. No due-date logic, no
reminders to chase the blocker — that's someone else's problem to
solve, not the app's to nag about.

### Milestones inside a deadline (v8.59)

`total_h` measures effort, not progress — 30h logged on a 60h scope can
be 70% done or 20% done depending on WHAT got done. Deadlines gain an
optional **Milestones** field in the existing edit dialog: `ch4 [15h]*,
ch5 [20h], revisions [10h]` — same `[Nh]` bracket convention the task
time-box already uses; a trailing `*` marks one done. The dashboard's
**Deadlines & Goals** tab then speaks in content instead of just hours:
`ch4 done, ch5 at 60% of its hours, revisions at 0% of its hours`.
Hours accrue in milestone order, so the current one gets credit first.

### Protected time windows (v8.58)

**Tools → Protected time windows…**: name daily-recurring windows the
scheduler must never claim — "lunch 12:00-13:00", "wind-down
21:00-22:00" — even though they're technically free time. Subtracted
from the same free-slot math calendar busy-time already goes through,
so the suggested schedule stops offering to book over lunch.

### Commitment-reliability ledger (v8.57)

A new opt-in header line, never auto-inserted: `COMMIT: thesis 4h`
commits to 4h on tasks matching "thesis" today; `COMMIT: 4h` alone
commits to 4h of tracked work overall. The Monday review reconciles
each recent commitment against what actually got delivered and reports
the trailing rate once 5+ real ones exist: `you hit your morning
commitment 3 of the last 5 days — you reliably deliver ~60% of what you
promise yourself; promise that and mean it`. Never grades any one day —
just the honest personal rate, so you can promise what you actually
deliver instead of what you wish you did.

### Time capsule (v8.56)

On-this-day looks back one year automatically. Now you can deliberately
seal a note for a future date too — type `CAPSULE: 2026-08-15 |
message` anywhere in a day's file, and once today reaches that date,
the header surfaces it: `a note from 45 days ago: message`. A pure text
convention, same "read the day files back" spirit as TODO carry-over —
no new window, no reminders to set up.

### Screen-lock break detection (v8.55)

Windows+L now triggers a break offer directly, not just eventually
through idle detection. Locking is a deliberate step-away with no
minimum duration worth waiting on — a quick 3-minute lock to grab
coffee never crossed the idle-minutes threshold before, so it never
got offered as a break at all. Unlocking now pops the same "log it as
a break?" dialog the idle-minutes detector already used, immediately,
for locks of 30 seconds or more. Turns off along with idle detection
(`idle_min` = 0); unaffected by Meeting mode, since an actual lock is
unambiguous even mid-call. **Uses a best-effort Windows API trick this
dev environment couldn't test live — please confirm on your machine
that locking and unlocking pops the dialog as expected.**

### Planner realism factor (v8.54)

The morning schedule (v8.0) writes a suggested time-blocked plan every
day; nothing ever checked what became of it. Now it does: each past
day's own written schedule gets reconciled against what actually got
tracked, and the planner learns a personal plan-survival rate — "your
average planned day survives 90%." The morning schedule scales its own
hour estimates by that rate before placing blocks, and says so right in
the header: `(planning at 90% density — your plans have survived that
rate over the last 6 scheduled days)`. Grades the planner's realism
only, never the person — no compliance tracking of what you actually
did on any one day.

### Sensor health meter (v8.53)

**Tools → Data doctor** now opens with a new section at the top: per
data source (sleep import, calendar, ENERGY logging) — last date seen,
coverage % over the last 30 days, and a plain alarm once it's gone
quiet longer than makes sense: `sleep import: last seen 2026-06-15
(30d ago), 0% coverage — the phone automation may have stopped`. Also
lists the personal baselines the anomaly watch judges against (your
normal sleep, your normal week) — the co-pilot's calls, inspectable
instead of oracular.

### Weekly "one less" (v8.52)

Every insight so far adds awareness; this one subtracts. The Monday
review gains one line picking a single removal candidate from data the
app already tracks — the meeting that fragments your best block, the
task you keep bouncing off, or the after-21:00 work that taxes
tomorrow: `THIS WEEK, TRY ONE LESS: the meeting that fragments your day
— Wed's meeting cost 1.3h`. Rotates between whichever candidates
qualify that week so the same one doesn't repeat back-to-back while an
alternative exists — improvement by removal, not another thing to add.

### Deadline renegotiation tracker (v8.51)

Deadlines could always have their date/scope edited silently, with
nothing remembering the original numbers. Every edit through the
existing deadline dialog now logs the OLD date/hours onto that
deadline's own history. Once it's been edited 2+ times, one honest
line appears in the dashboard's **Deadlines & Goals** tab: `this
deadline has moved 2 time(s) since 2026-06-29 — due date is now 45d
later than first set, scope grew from 20h to 45h`. No judgment — just
the pattern, catching the difference between genuinely re-scoping
reality and repeatedly deferring the same discomfort.

### Deadline post-mortem (v8.50)

Once a scoped deadline's due date passes, one retro block writes into
that day's file automatically (once — never repeated): scope vs actual
hours logged, the estimate factor on that specific project, a
retrospective check of what a projection made 21 days before the due
date would have predicted vs when the scope was actually completed
("predicted 13.07, actually finished 04.07 — ran 9d pessimistic"), and
the real pace kept over the project's whole life. Each closed deadline
becomes calibration data instead of just vanishing.

### Goal lifetime ledger (v8.49)

Every existing view is windowed — 8 weeks, a deadline's own scope, a
calendar year. The **Life dashboard → Deadlines & Goals** tab now adds
one un-windowed line under each goal and deadline: `Thesis: 187h across
62 session(s) since 2026-06-29 (134 days — 1.4h/day lifetime average)`.
Anchored to a deadline's own stored start date if it has one, or the
first-ever matching session in the csv otherwise — the true lifetime
cost, not an arbitrary window.

### Annual theme (v8.48)

A new `YEAR: <theme>` header line — the year-scale sibling of SIGNAL/
AVOID. Set it once and it's auto-carried into every day after that,
exactly like AVOID already is; edit it whenever the theme genuinely
changes. The existing "on this day" callback (one year back) now
surfaces it too: `on this day, 2025: 1h30m work — felt good about the
outline today · that year's theme: 'finish the thesis' — still true?`

### Decision log lite (v8.47)

A new archival-only line convention: type `DECIDED: apartment — staying
another year, rent's still fair` anywhere in a day file. **View →
Decision log…** lists every one of them across every day file, newest
first — so "wait, didn't I already think this through" is answerable by
reading the list, not memory. Deliberately no counter, no reopening
friction, no unlock mechanic — purely archival, same spirit as Search
all days.

### Ask-your-diary pinned searches (v8.46)

**Search all days** gains a row of pinned-search buttons above the
results. Click one to re-run that query instantly instead of retyping
("what did I decide about the advisor situation, again"); **📌 Pin**
saves whatever's in the query box; right-click a pin to remove it.
Capped at 5 — a shortlist stays useful, an unbounded list doesn't;
re-pinning an existing query just re-surfaces it at the front.

### Weekly experiment engine (v8.45)

A new opt-in line for Monday's header — never inserted automatically,
you type it yourself when you want to run a self-experiment: `EXPERIMENT:
no work after 21:00`. The FOLLOWING Monday's WEEK REVIEW reports that
week's measured shift on work, late-evening minutes and sleep against
the trailing 4-week baseline before it: `EXPERIMENT 'no work after
21:00': late-evening -1.0h vs baseline; sleep +0.5h/night vs baseline;
output +0.0h vs baseline.` It never judges whether you actually followed
the rule — just the honest before/after on the numbers already tracked,
so you can decide for yourself whether it's worth keeping.

### Energy forecast for today (v8.44)

A new line in the morning header, right after the co-pilot note: `today
smells like a 3.5-4.5h day (Tuesday, running on debt, n=6) — plan the
must-do inside that.` "Last night's sleep" and "trailing sleep debt"
combine into one signal — your 3-night rolling average — compared
against your own trailing 90-day median, then matched against your own
weekday pattern. The weekday capacity table (Tools → Weekly capacity)
says what you PLANNED to have; this says what your recent data suggests
you'll ACTUALLY have. Needs today's own sleep reading and enough matching
history; silent otherwise.

### Year rhythm map (v8.43)

**View → Year rhythm map**: 52 columns (weeks) × 24 rows (hour of day),
each cell shaded by tracked minutes in that hour, that week. The existing
month heatmap shows how MUCH per day; this shows WHEN, at year scale —
bedtime drift eras, morning-discipline phases, an exam-sprint block, the
dead summer, all visible as one picture. Both work and break time count,
since this is about when you're at the desk at all.

### Meeting fragmentation tax (v8.42)

The meeting-load insight only ever counted busy hours. This prices what
a meeting does to the OPEN time around it — a short meeting stranding a
small sliver either side can cost far more than its own length in lost
deep-work capacity (contiguous free blocks ≥90 minutes). Simulates
removing each meeting on its own, one at a time, and reports the worst
offender plus the week's total: `Wednesday's 15:40 meeting: 0.3h long,
cost 1.3h of deep capacity` / `meeting fragmentation tax this week:
1.7h`. Needs a calendar synced (Tools menu); silent when the week's
total tax is negligible.

### Running-hot index (v8.41)

The trajectory line eventually notices a sleep-for-work trade — but only
after roughly a month of drift. This is the early-warning version: a
rolling check over your last 14 days vs the 60 before that, watching four
independent signals — sleep below your own recent norm, workout frequency
drop, late-night count, break-ratio compression. Speaks only when at
least **two** move together, as one line in the co-pilot greeting: `14
days running hot (sleep -1.0h/night vs norm, 3 late nights) — schedule
one flat day before your body schedules it`. One signal alone stays
silent (too many honest explanations); silent again the moment things
ease, with no memory of having spoken before.

### Backup integrity check (v8.40)

**Tools → Data doctor** now opens with one more line above the usual
housekeeping report, but only when it matters: `last backup: 15 days ago
(expected weekly) — the automation may have stopped`. The weekly
`backups/` csv copy has run silently since early versions with nothing
ever checking that it's actually still current — this closes that gap.
Silent when the newest backup is recent (a 10-day buffer over the 7-day
cadence, so normal use never sees it); speaks up only if backups have
genuinely stopped, or never started at all.

### Health-hub view (v8.36)

**View → Health × focus** gains a second table underneath the existing
one: mindful minutes, resting heart rate, HRV, weight and daylight hours
— all captured since v8.27/v8.28 but never shown as more than one header
line before now. Empty until you turn a column on (a health-export field,
or Tools → Daylight location for the last one) — the footer says exactly
how.

### Lens overlap check (v8.35)

Every percentage this app has ever shown you — alignment shares, signal
%, goal minutes — quietly assumes your SIGNAL/AVOID/goals/domains/
deadlines keywords are disjoint. Nothing ever checked. **View → Lens
overlap check** audits it: finds every pair of declared lenses that
actually matched the *same real tracked minutes*, not just a coincidental
keyword collision that never fired — `'run'/'training' both match Body
(goal) and Fitness (domain) — 5.0h counted toward both in the last 30d`.
Silent when everything's genuinely disjoint.

### Break budget (v8.34, weekday-specific in v8.39)

The totals line gains one more segment — a reframe, not a verdict. Instead
of judging each break, it learns a daily **allowance** from your own good
days: `breaks so far 45m · your typical by this hour 0m · full-day norm
~90m`. Budgets change behaviour where per-event nagging (the pull-back,
the doomscroll insight) doesn't reach — a number to plan around, not
another scold.

v8.39 makes the norm weekday-aware: once *today's own weekday* has enough
history of its own (10+ of that specific weekday), the norm switches from
an all-days blend to that weekday's median — `full-day norm ~50m (Mons)`
— since Friday afternoons and Tuesday mornings plausibly run genuinely
different real break patterns. Falls back to the old all-days blend until
a given weekday has its own history.

### Metrics shorthand (v8.33)

The METRICS line used to require `key=value` for everything. Now a bare
word logs itself as `1`: `METRICS: meditation, cold_shower` instead of
`meditation=1, cold_shower=1`. Mix and match freely — `METRICS:
meditation, water=6, cold_shower` all works on one line. Lower friction
for the yes/no habits that are most of what biohacking logging actually
is.

### Week ahead (v8.32)

Monday's file already reviews last week; it now also previews the next
one. **WEEK AHEAD** composes your calendar-aware capacity and your
deadlines' real-pace projections across the coming 7 days into one
block:

```
WEEK AHEAD: 14.0h free across the next 7 days · deadlines need ~40.0h
  (of which 97.0h already committed: Sleep 59.5h, Day job 37.5h)
  ⚠ overbooked by 26.0h before the week even starts
  tightest day: Thu 16.07 (1.0h free) — front-load elsewhere if something's due
  already behind at real pace: Thesis
```

Silent on a normal week — it only speaks when something's genuinely
worth flagging before the week starts, the same restraint as the daily
co-pilot line. The commitment line (v9.14) only appears alongside it,
never on its own — it names WHY the free-hours total is already
smaller than raw weekday capacity, it doesn't add a new reason to
speak.

### What today does to tomorrow (v8.31)

Every insight so far compares things on the SAME day. Three new checks
look a day ahead instead — the Insights now include whichever of these
clear a real, honest threshold:

- *"the day after a workout you average 5.0h of work vs 1.0h after a
  non-workout day — the gym looks like a productivity tool, not a cost"*
- *"the day AFTER a short-sleep night (<7h), output averages 1.0h vs
  5.0h after a full night — sleep debt doesn't clear in one day"*
- *"mornings after working past 21:00 you start 1.8h later on average"*
- *"the day after a 6+ switch day, 71% of your signal work lands in
  shallow blocks (<20m) vs 22% after a focused day — fragmentation
  carries over"* (v8.38)

Same honesty gates as everywhere else (real sample sizes, a real swing) —
just a new question: not "does X correlate with today," but "does X
still cost you tomorrow."

### Ask your diary (v8.30)

**Search all days** now has a second button: **Copy matching days for
AI**. Type any query — multiple words work as an OR search, ranked by
how many of them each day actually mentions, not just raw hit count — and
it copies the top 5 matching days' relevant lines (not whole files) to
your clipboard with date headers, ready to paste into an AI chat with
your real question on top. A year of day files becomes queryable, no API
key, same manual-copy-paste spirit as the existing weekly AI review.

### What's gone quiet (v8.37)

The mind-share insight (v8.29) only ever noticed words trending UP. Now
it also notices the opposite — a topic that was frequent and went quiet,
which often matters more than a new one appearing: *"words appearing
less lately: 'girlfriend' (20→0 mentions, last 30d vs prior 90d) — gone
quiet, worth noticing why."* Reported as its own separate line from the
increase insight.

### What's actually on your mind (v8.29)

A new Insight reads the diary text itself — not your tracked task labels,
the actual prose you've been writing the whole time. It compares word
frequency over the last 30 days against the 90 days before, and names
whatever is genuinely trending: *"words appearing more lately:
'apartment' (0→14 mentions, last 30d vs prior 90d) — what's actually on
your mind, separate from your tracked tasks."* Every structural line
(SIGNAL/AVOID/ENERGY/METRICS/timer lines) is excluded — only what you
actually typed counts. No new logging required; this was sitting in your
day files the whole time.

### Daylight (v8.28)

The only data source in the app that needs no export file, no typed
line, and no network — just a latitude. Tools → **Daylight location**,
type a number once (60.2 for Helsinki, -33.9 for Sydney), and every day
now carries its computed hours-of-daylight. Once your own history
actually spans a real season, an insight compares your shortest-daylight
days against your longest: *"shortest-daylight days (~6.1h sun, n=11):
2.3h work avg vs longest (~18.4h sun, n=9): 4.1h — less on the darker
days · energy: 2.4/5 dark vs 3.8/5 light."* Silent until a real seasonal
swing exists in your data — the whole point is to start capturing it
*now*, months before it can say anything.

### The health-hub pivot (v8.27)

**METRICS** — a new header line, right next to SIGNAL/AVOID/ENERGY: type
any personal metric as `key=value` pairs, whenever you want:

```
METRICS: meditation=10, water=6, mood=calm
```

No settings, no dialog, no new code per metric — one parser handles
whatever you invent. An Insight compares signal-share on days you logged
a given metric vs days you didn't, and names the one with the biggest
swing: *"days you logged 'meditation': signal 14 points higher (9d
logged vs 41d not) — worth tracking on purpose, not by accident."*

**Wider health import** — the health-folder parser now also picks up
mindful/meditation minutes, resting heart rate, HRV, and body weight from
the same Health Auto Export CSVs already recommended, including files
that export just ONE of these metrics on their own (previously silently
skipped). Mindful minutes show in the day header now; RHR/HRV/weight are
captured and waiting for a dedicated health view.

This is the concrete first step of the "health hub" direction: biohacking
habits get logged right next to the diary text they belong with — one
file, not a second app to maintain.

### Five more, same push (v8.22-v8.26)

- **Rescue block** — "What should I do now?" gets a mid-afternoon
  save: if it's 15:00-21:00 and today's gone sideways, *"salvage plan:
  one 45m block on Thesis before the day ends still makes it
  count."* Silent the moment real progress exists.
- **Mood ≠ energy** — `ENERGY: 3 anxious` now parses the word too.
  New insight names the mood with the biggest signal-share swing from
  your baseline.
- **App usage-pattern meter** — Tools > "Feature usage…" shows which
  of the View menu's 15+ windows you actually open.
- **Best-weeks retrospective** — the positive-framed insight: your top
  3 weeks, and which weekday carried most of the signal work.
- **Reallocation scenario** — when one deadline's genuinely capacity-
  starved and another has slack, one concrete trade: *"cutting TUTA to
  0.0h/day would free 0.5h/day for Thesis."*

### Six in one push (v8.16-v8.21)

- **Declared short day** — type `TODAY: 4h` (or `TODAY: sick`, no
  number) into today's own file and tomorrow's verdict judges against
  that declared cap instead of the usual bar: *"short day as declared
  — 2.0h tracked, plan honored"* — never "what stole it?" for a day
  you already flagged honestly. Streaks bridge through it too.
- **First-hour audit** (Insights) — *"days you open with signal work
  end 3.0h heavier than days you open with something else — the first
  hour is a lever, not a warm-up."*
- **Task-thrash meter** (Insights + status bar) — high-switch days vs
  low-switch days compared on signal share; the status bar also
  quietly counts today's switches once you pass 4.
- **Shallow-work ratio** (Insights) — *"62% of today's signal hours
  came in blocks under 20m — that reads as busy, not deep."*
- **Library graveyard sweep** — once a month, names Task-library items
  sitting untouched 60+ days in the week-review block. Never
  auto-deletes.
- **Task-library commitment density** — the Tasks/Library window now
  shows total signal-priority volume undated at a glance.

### Your natural focus cycle (v8.15)

A new Insight buckets your work blocks by length and compares the
break that follows each bucket:

*"blocks past ~60m are followed by 4.0x longer breaks (20m vs 5m) —
your natural cycle looks like ~60m, box accordingly."*

Your own personal pomodoro, from your own history — not a borrowed
25-minute rule. Start a SIGNAL task without typing a `[Xm]` box and
the status bar now quietly suggests one from the same curve; type
your own box and the suggestion stays out of the way.

### Behind-pace root cause: capacity vs. choice (v8.14)

The burn-down window's real-pace line says WHEN you'll land; now a
second line, when you're behind, says WHY — so you fix the right thing:

*"Thesis is behind pace — but you had 18h free this week and only put
1h into it. Not a capacity problem."*

vs.

*"Thesis is behind pace — and you only had 1.5h free this week. A
capacity problem: something else has to give."*

Capacity problems need something cut; choice problems need
reallocating, not more hours. Only speaks from Wednesday on, once the
week's a fair sample.

### AVOID — the inverse lens (v8.13)

SIGNAL names what matters today; a new `AVOID: news, email` line in the
header names what you're trying to shed. Same keyword lens, inverted —
and it carries forward day to day just like SIGNAL:

```
(yesterday: 4h30m work / 0h30m breaks, signal 67%, avoid 12% ↓)
```

The arrow is a quiet week-over-week read (this week so far vs. all of
last week) — silent until there's enough real data on both sides to
say something honest.

### Which task do you flee from? (v8.12)

The Insights now spot **aversion's signature**: starts on a task that die
within 10 minutes into a break, again and again. When one task crosses
the line (6+ starts, half of them bounces), it gets named:

*"you bounce off 'thesis: intro' within 10 min on 75% of starts (6 of 8)
— that's not laziness, the task is too big; cut it into [30m] pieces."*

The pull-back handles the moment of procrastination; this finds the task
that keeps causing it — and the fix is decomposition, not discipline.

### Re-entry ramp (v8.11)

Coming back after a 30-minute-plus break, the status line offers the
smallest concrete way back in:

```
Working — thesis: ch4 · start small: 'thesis: fix table 3' (0.2h)
```

It picks the tiniest estimated task related to what you're resuming (then
the smallest signal-priority item, then today's first TODO bullet). The
pull-back gets you to click; the ramp makes the first minute cost almost
nothing — which is the whole battle.

### Breaks get teeth (v8.10)

Two answers to "I might just be procrastinating":

**Break pull-back** — if a break interrupts a **signal** task and runs
past your threshold (Tools → Break pull-back, default 20 min), the gentle
coffee pill transforms: `⚑ 23 min off 'thesis: ch4' — click: the first
minute is the whole battle`, with a beep and a jump to the front; at
double the threshold it hardens further. Breaks off admin keep the old
quiet pill. It's deliberately the strongest thing short of a lock — a
lock you'd alt-tab past anyway; this makes ignoring it a conscious
decision, which is the part that actually works.

**The doomscroll tax, measured** — the break notes you've been typing for
years now pay out: *"after a moving break your next work block averages
41m; after a scroll break 19m."* Walk vs scroll, settled by your own
data, in the Insights.

### Where you left off (v8.9)

Start (or switch to) any task you've worked before and the status bar
hands you back **the last thing you wrote about it**:

```
Working — thesis: ch4 · last time (08.07): "stuck on regression table, try clustered SEs next"
```

The biggest hidden cost of resuming a task is re-finding the thread; now
your own note from last time is waiting at the exact moment you need it.
Read-only — it just reads the old day file, nothing is changed.

### Energy-aware scheduling (v8.8)

The morning schedule got smart. Instead of dropping each deadline into the
earliest free gap, it now places work by **when you're actually sharpest** —
learned from 60 days of your own history. Your hardest, most-behind
deadline claims your **peak hours**; admin and low-focus work drift to the
troughs:

```
suggested schedule today (hardest work steered to your peak hours):
  13:00-15:00 Thesis (2.0h) ⚠ behind pace     ← your peak, not the first gap
  09:00-10:00 email/admin (1.0h)
```

Blocks stay contiguous (no scattered fragments), and with too little
history it falls back to the old earliest-first placement unchanged. This
is an upgrade to the planner itself, not another view to open.

### What should I do now? (v8.7)

View → **What should I do now?** answers the moment-to-moment question the
morning schedule can't: it's 2pm, you've got 90 minutes — what's the best
use of them? It reads the **current hour against your learned deep-focus
window** (the 3-hour block your work actually lands in, from 60 days of
history), which deadline is most behind at real pace, and today's energy:

- *inside your deep-focus window (09–12) — spend it on Thesis (~22d behind), not admin*
- *past your deep window (09–12) — good slot for admin/email; protect Thesis for tomorrow's peak*
- *19–21 fatigue window — move or rest, don't grind*
- *…Energy's 2/5 today — a lighter or shorter task beats forcing the hard one*

It protects your best hours for your hardest work and steers the rest
where it belongs.

### The co-pilot greets you (v8.6)

The app stops waiting to be opened. Every new day file now opens with a
**`co-pilot:`** line — the single most important thing right now, picked
for you: an actionable risk when there is one (*"Main risk: Thesis lands
~22d late — add ~1h/day or move the date now"*), otherwise the sharpest
**anomaly vs your own baseline**:

- *worst sleep week in 10 weeks — 5h30m/night vs your 7h30m norm*
- *20 days since any Finnish — drifting from something you flagged as mattering*
- *3 straight tracked days at ~0% signal — the work's happening, just not on what you named*

It's measured against *your* history, not an ideal, and stays silent when
there's genuinely nothing to flag. The full list lives under **UNUSUAL**
in the Life review. This is the app becoming *attentive* — noticing, and
speaking first.

### Life review — the whole picture, synthesized (v8.5)

The one that makes every other view speak with a single voice. **View →
Life review** assembles this week's numbers, your **values alignment**,
the **outlook** on what's coming, the months-scale **trajectory**, and the
top **patterns** — then closes with a **bottom line** that reconciles them
into one action instead of five things to read:

```
BOTTOM LINE
  You're behind on Thesis (~22d late at real pace) AND under-investing in
  Growth (-14 pts below your aim). Same fix, not two: the FIRST block of
  each day goes to Growth/Thesis before the urgent small stuff eats the
  morning.
```

It reads Foresight (are deadlines slipping) and Alignment (is a valued
area starving) *together* — the thing no single view can see. **Copy for
AI second opinion** puts the whole briefing on the clipboard. This is the
"AI analyst," done rule-based and keyless — the co-pilot's weekly brief.

### Life alignment — time vs your values (v8.4)

The reframe from *time* tracker to *life* management. **Tools → Life
domains** lets you name a few life areas — Work, Body, Growth, People,
Rest — each with the task keywords that belong to it and an optional
target share of your time. **View → Life alignment** then shows where your
hours *actually* went over 8 weeks against what you *said* should matter:

```
LIFE ALIGNMENT — last 8 weeks, 43h of tracked time by domain:
  Work    40.0h  93%   aim 60%  (+33 pts)
  Body     2.0h   5%   aim 15%  (-10 pts)
  Growth   1.0h   2%   aim 20%  (-18 pts)
→ widest say-do gap: Growth — getting 18 points less of your time than
  you said it should
```

Domains sit one level above goals (a goal is *why this project*; a domain
is *why the projects at all*) and use the same keyword matching under the
hood. This is the platform's core question in one view: **is your time
flowing where you say it should?**

### Outlook — the weeks ahead (v8.3)

View → **Outlook — weeks ahead** is the first view that looks *forward*
instead of back. It simulates every scoped deadline at once at the pace
you've *actually* kept (not your theoretical capacity) and tells you what's
going to go wrong before it does: *"1 of 2 deadlines land LATE — ⚠ Thesis:
due 22.07, lands ~13.08 (22d late) at 2.7h/wk actual · +1h/day → 23d
sooner,"* plus the one aggregate lever that clears everything (*"needs
about +0.8h/day more than you're averaging"*). Prediction and prescription,
not just a mirror of the past. Deadlines with too little recent tracking to
project are named as such rather than guessed at.

### Trajectory — the months-scale read (v8.2)

Every other insight looks at the last few weeks. This one (in the
dashboard's Insights, `Ctrl+D`) splits the **last 8 weeks in half** and
compares them across domains, then names the trade-off you're actually
making: *"8-week trajectory: work 5.0→15.0h/wk ↑, sleep 7.5→6.2h ↓ → you're
buying work hours with sleep — a sprint move, not a season."* It stays
quiet unless something genuinely moved (both halves need real history).
The first feature that looks at your life at the scale of **months**, not
the current week — the seed of a bigger trajectory/life-memory direction.

### Finish-date projection (v8.1)

The burn-down window (View → Burn-down) now ends with one blunt line: not
just *how many hours a day you need*, but **where you actually land at the
pace you've kept**. "at your real pace (2.0h on active days, active 19% of
days) you land ~13.08 — 21d late (due 23.07). +1h/day from now → 23d
sooner." It reads your real trailing pace — average hours on the days you
actually touched it, times how often you touch it — so "2h/active-day,
active 40% of the time" honestly becomes 0.8h/day, not 2. Shows only once
there's enough real history (5+ sessions in the last three weeks) and only
for deadlines with an hours scope. Red when late, green when early.

### Data sovereignty (v7.0)

**Tools → Rebuild sessions.csv from day files…** — the day file has always
been described as the true record and the csv as a derived index; this
makes it literally true. Reconstructs every work/break row straight from
your day files' own `Start;`/`Stop;`/`--- Task:` lines. Lose or corrupt
`sessions.csv` and it's fully recoverable as long as the day files survive.
Backs up the current csv first; a confirmation dialog, not routine
maintenance.

**File → Import life record (JSON)…** — restores goals/deadlines/capacity
(merged by name — never replaces what you already have configured) and day
files (only ones missing locally — never overwrites current work) from a
previous export. Pair it with the csv rebuild above: import brings the day
files back, rebuild regenerates the session log from them — full, lossless
recovery on a new machine or after a lost install.

### Life dashboard — now a tabbed home (v7.0)

`Ctrl+D` opens three tabs (Today & Week / Deadlines & Goals / Insights)
instead of one long scroll, plus a row of buttons linking straight to every
detail view — Weekly, Monthly, Trend, Health, Heatmap, Burn-down. Nothing
was retired; each still holds detail the condensed tabs don't repeat.

### Tasks link to deadlines too (v7.0)

Not just goals — the Tasks/Library window has a Deadline column and dropdown
now, same pattern as Goal. **Right-click any row** to set or change its
goal or deadline after the fact — needed for TODO:/SOMEDAY: items that
auto-captured with neither set.

### Deadlines linked to goals (v6.7)

Tools → Deadline countdowns has a Goal column now — pick one, and that
goal's one-line "why" shows up next to the deadline wherever you see it
countdown (Life dashboard, burn-down chart title). Seeing "Thesis — 5d
left (finish before the fall offer starts)" is a different feeling than
just "5d left."

### Faster inputs (v6.6)

Right-click the timeline to set last night's sleep: bed/wake times now
accept `1`, `01`, `0120`, `120` or `1:20` — no colon, no leading zero, no
minutes needed if you don't care. In Tasks / Library, adding a task with
an estimate no longer needs `[2h]` typed inline — there's a plain "est h"
box and a priority picker right there (typing brackets in the name still
works, if that's faster for you).

### "Actually working, not resting" (v6.6)

File → **Add past session…** has a new checkbox: *"carved out of a
break"*. Check it, and the minutes you log as work are also subtracted
from the break they came out of — so realizing 10 of those 23 "break"
minutes were spent replying to something task-related doesn't inflate
your break total while under-counting your work.

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
