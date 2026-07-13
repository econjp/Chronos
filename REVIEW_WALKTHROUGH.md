# Landing v8.1–v8.8 — walkthrough for the main machine

**What this is:** the branch `claude/finish-date-projection` holds 10
commits of reviewed-nowhere work built off master's v8.0. This file walks
the main-machine session (or you, by hand) through checking it, deciding
what makes sense, and landing it per the repo's standing policies (no
direct unreviewed merge to master; hand-audit; no trailers; no personal
data). **Delete this file in your cleanup commit after landing — it's
scaffolding, not documentation.** HANDOFF.md stays the permanent brain.

---

## 1 · What's waiting (newest last)

| # | commit | ver | what you get | kind | risk |
|---|--------|-----|--------------|------|------|
| 1 | ff64106 | 8.1 | burn-down footer: real-pace landing date + "+1h/day" lever | view | low |
| 2 | ac38259 | 8.2 | 8-week cross-domain trajectory + trade-off line (Insights) | view | low |
| 3 | 3fa78dd | 8.3 | Outlook window: all deadlines forward-simulated at real pace | view | low |
| 4 | e268956 | 8.4 | Life domains (values layer) + alignment view; new `domains` settings key | view+setting | med |
| 5 | 236c19d | 8.5 | Life review briefing + synthesized bottom line | view | low |
| 6 | f1a25cb | 8.6 | anomaly watch + "co-pilot:" line in NEW day headers | writes header line | med |
| 7 | 1cb04db | 8.7 | "What should I do now?" (learned deep-window recommender) | view | low |
| 8 | 2f74cad | 8.8 | scheduler places hardest work into your learned peak hours | behavior change | med |
| 9 | a3bf364 | — | `timerv2/selftest.py` (8 logic suites) + review kit + backlog | tooling/docs | none |
| 10 | e3ab8b0 | — | this walkthrough + backlog #24–27 | docs | none |
| 11 | 5d4fbe8 | 8.9 | "where you left off": task start shows your last note about it | view (status bar) | low |
| 12 | 4b3edcb | 8.10 | break pull-back (signal tasks, loud nudge not a lock) + doomscroll-tax insight | pill behavior + view | med |
| 13 | dd88c0c | 8.11 | re-entry ramp: "start small: …" opener after 30m+ breaks | view (status bar) | low |
| 14 | (tip) | 8.12 | procrastination map: names the task you bounce off, with the fix | view (insight) | low |

**Dependencies (corrected — the HANDOFF kit's first version understated
these):** 8.1, 8.2, 8.4, 8.8 and 8.9 are standalone. 8.3 and 8.7 need 8.1.
**8.5 needs 8.1+8.2+8.3+8.4** (it composes all of them). 8.6 needs 8.5.
Practical rule: either take the whole set, or if anything in 8.1–8.4
fails your audit, also drop 8.5 and 8.6. `selftest.py` expects the full
set (partial landings will show FAILs for the missing suites — expected,
not a defect).

## 2 · Pre-flight (5 minutes)

```
git fetch origin
git log --oneline master..origin/claude/finish-date-projection
git switch -c review-v8x origin/claude/finish-date-projection
python timerv2\selftest.py            # must print: 8/8 suites green
```

Policy compliance check (should show only `econjp`, and no trailers):

```
git log --format="%h %an <%ae>" master..review-v8x
git log master..review-v8x | findstr /i "co-authored claude-session"   # expect no output
git diff --stat master...review-v8x   # only timerv2/*.py, HANDOFF.md, README.md + this file
```

## 3 · Think-through, per commit (what to ask before taking each)

- **8.1 projection** — adds honesty next to "needs Xh/day". Question:
  none really; it's silent without 5+ recent sessions on a scoped
  deadline. Revert cost: trivial (one footer block).
- **8.2 trajectory** — first months-scale read. Question: do the arrows
  match your felt reality when you open Insights? If it misreads your
  history, that's signal about data quality (see backlog #23), not a
  reason to skip. Silent below 5 active days per half.
- **8.3 outlook** — forward simulation of ALL deadlines. Question: with
  your real deadline set, do the late/on-pace calls look sane? It uses
  a 21-day trailing pace — a vacation fortnight makes it pessimistic
  (stated, not hidden).
- **8.4 domains** — the one new *concept*. Questions: do you actually
  want a values layer, and are your task keywords disjoint enough for
  honest percentages? Adds only a `domains` key to settings.json (no
  migration, absent = feature off, everything else unaffected). If
  unsure: take it but don't configure domains yet — it's inert until
  Tools > Life domains is filled in.
- **8.5 life review** — pure composition of 8.1–8.4 + a rule-based
  bottom line. Question: read one real briefing — does the bottom line
  feel earned? It's the keyless stand-in for the LLM analyst (still
  ask-first per HANDOFF).
- **8.6 co-pilot header line** — the most opinionated change: it WRITES
  one line into new day headers when something is genuinely off (silent
  otherwise). Questions: are you OK with the app speaking first in your
  own diary? It never gates or nags (standing guardrail); revert = the
  3-line block in `_new_day_header`. If this one annoys you in week one,
  revert just it — nothing depends on it.
- **8.7 what-now** — status-bar one-liner on demand. Question: does its
  learned deep window (from your real 60-day history) match when you
  actually feel sharp? If not, that mismatch is itself interesting.
- **8.8 energy-aware scheduling** — the only change to something the app
  DOES: morning schedule steers hardest work into learned peak hours.
  Question: compare one morning's suggested schedule before/after (run
  once on master, once on the branch, same data). With <20h of history
  the output must be byte-identical to v8.0's earliest-first — verify
  that on a thin data copy if you want certainty.
- **9–10 tooling/docs** — selftest.py is the audit tool itself; take it
  first if you cherry-pick out of order.

## 4 · Landing

**Path A — master hasn't moved since v8.0 tip** (check:
`git merge-base master review-v8x` equals `master`):

```
git checkout master
git merge --ff-only origin/claude/finish-date-projection
```

Linear history, no merge commit, every commit individually revertable.

**Path B — master has moved:** cherry-pick in order (`git cherry-pick
ff64106^..a3bf364` or one at a time). Conflict hotspots are all
top-append points, resolve by keeping both sides, newest first:
the changelog top of `timer_diary_v5.py`'s docstring, the View-menu block
in `_build_menu`, HANDOFF's version-history top, README's top section.

**Partial landing:** respect the dependency rule in §1; note in
HANDOFF's version history which versions were skipped and why.

## 5 · Windows smoke test (~20 min, on a COPY of the real data folder)

1. Launch; start/stop/switch the timer — core loop untouched, must feel
   identical.
2. Burn-down on a scoped deadline → footer projection line (8.1).
3. Ctrl+D → Insights tab → trajectory line present or correctly silent (8.2).
4. View > Outlook (8.3), Life alignment (8.4 — configure two domains
   first), Life review + Copy button (8.5), What should I do now? (8.7).
5. Rename today's day file away → reopen app → new header: co-pilot line
   present/absent as data warrants (8.6), "suggested schedule" wording
   (8.8).
6. `python timerv2\selftest.py` on master after landing → 8/8 green.
7. `build_exe.bat`, run the exe once.

## 6 · After landing

- Delete this file (`git rm REVIEW_WALKTHROUGH.md`) in the cleanup commit.
- Delete the remote branch: `git push origin --delete claude/finish-date-projection`.
- If anything was skipped or reverted, one line in HANDOFF's version
  history saying so — the next session must not re-ship it blind.
- The ask-first item remains the auto-LLM analyst (credential decision);
  everything else in backlog #16–27 is keyless and pre-scoped.
