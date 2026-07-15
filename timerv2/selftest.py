"""Self-test for timer_diary_v5.py's pure logic. stdlib only, no GUI.

Runs on ANY OS (Linux CI-style checks or the Windows dev machine):
functions are lifted out of the app file via ast, so tkinter/ctypes are
never imported and the real %APPDATA% data dir is never touched — every
suite runs against its own throwaway csv in a temp dir.

Usage:  python selftest.py        (exit code 0 = all suites green)

Covers the v8.1–v8.8 logic tier: deadline projection, trajectory,
outlook, alignment, life-review synthesis, anomaly watch, right-now
recommender, energy-aware placement. Add a suite here in the same commit
as any new pure-logic feature — this file is the durable form of the
"verify without Windows" pattern described in HANDOFF.md.
"""
import ast
import csv
import json
import math
import os
import re
import sys
import tempfile
import textwrap
import datetime as dt
from datetime import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "timer_diary_v5.py")

TOP = {"read_rows", "day_index", "task_matches", "matched_minutes",
       "fmt_sleep", "_time_span_hours", "_add_hours",
       "parse_health_dir", "_parse_any_date", "_dur_minutes", "_num",
       "day_length_hours", "backup_integrity_line",
       "_free_from_busy", "_deep_capacity_minutes", "_merge_time_intervals",
       "_pinned_after_add", "_pinned_after_remove", "day_totals",
       "load_settings", "save_settings", "_deadline_revisions_after_save",
       "_pick_one_less", "_parse_milestones"}
METH = {"_dl_progress", "_dl_velocity", "_dl_projection", "_projection_line",
        "_match_kws", "_trajectory_lines", "_outlook_lines",
        "_alignment_lines", "_domain_minutes", "_review_bottom_line",
        "_life_review_lines", "_anomaly_lines", "_copilot_note",
        "_recommend_now", "_deep_window", "_hour_quality", "_energy_place",
        "_last_context", "_break_insight", "_pull_level", "_reentry_opener",
        "_procrastination_insight", "_metrics_from_text", "_day_metrics",
        "_metrics_insight", "_daylight_h", "_daylight_insight",
        "_diary_word_counts", "_word_drift_insight",
        "_diary_rank_days", "_matching_days_text", "_word_drift_counts",
        "_word_fade_insight",
        "_lag_workout_line", "_lag_sleep_debt_line", "_day_start_late_map",
        "_lag_evening_start_line", "_lag_insight", "_week_ahead_lines",
        "_day_switches", "_shallow_threshold", "_day_shallow_frac",
        "_decay_cycle", "_lag_fragmentation_line",
        "_break_budget_line", "_lens_registry", "_lens_overlap_lines",
        "_health_extras_lines", "_running_hot_line",
        "_day_fragmentation_tax", "_meeting_fragmentation_lines",
        "_year_rhythm_grid", "_energy_forecast_line",
        "_experiment_from_file", "_week_metric_totals",
        "_experiment_review_line", "_scan_decisions",
        "_carry_year", "_on_this_day_line", "_lifetime_ledger_line",
        "_due_capsules", "_capsule_lines", "_commit_from_text",
        "_commitment_reliability", "_commitment_reliability_line",
        "_protected_intervals", "_milestone_progress_line",
        "_waiting_on_lines", "_cost_of_yes_line", "_status_update_text",
        "_status_update_all",
        "_estimate_factor", "_deadline_postmortem_lines",
        "_run_deadline_postmortems", "_deadline_renegotiation_line",
        "_one_less_candidates", "_one_less_line", "_sensor_health_lines",
        "_planned_hours_from_file", "_planner_realism_factor"}
STATIC = {"_match_kws", "_pull_level"}  # extraction drops @staticmethod
CLASS_ATTRS = {"_BREAK_MOVE", "_BREAK_SCROLL", "METRICS_RE",
               "METRICS_BARE_RE", "_LINE_TAG_RULES", "_WORD_RE",
               "_WORD_STOPWORDS", "_DECAY_BUCKETS", "_CAPSULE_RE",
               "_COMMIT_RE"}

_text = open(SRC, encoding="utf-8").read()
_tree = ast.parse(_text)
_top_nodes = [n for n in _tree.body
              if isinstance(n, ast.FunctionDef) and n.name in TOP]
_meth_src = {}
_attr_src = {}
for _node in _tree.body:
    if isinstance(_node, ast.ClassDef) and _node.name == "App":
        for _s in _node.body:
            if isinstance(_s, ast.FunctionDef) and _s.name in METH:
                _meth_src[_s.name] = ast.get_source_segment(_text, _s)
            elif (isinstance(_s, ast.Assign) and len(_s.targets) == 1
                    and isinstance(_s.targets[0], ast.Name)
                    and _s.targets[0].id in CLASS_ATTRS):
                _attr_src[_s.targets[0].id] = ast.get_source_segment(_text, _s)

_missing = (TOP - {n.name for n in _top_nodes}) | (METH - set(_meth_src))
if _missing:
    sys.exit(f"selftest: functions missing from app file: {_missing}")


def fresh():
    """(D, ns): a stub class carrying the extracted methods + a namespace
    with its own temp csv and cache — full isolation per suite."""
    tmp = tempfile.mkdtemp()
    ns = {"csv": csv, "os": os, "dt": dt, "re": re, "math": math,
          "json": json,
          "SESSIONS_CSV": os.path.join(tmp, "sessions.csv"),
          "SETTINGS_JSON": os.path.join(tmp, "settings.json"),
          "CSV_HEADER": ["date", "type", "start", "end", "minutes",
                         "task", "note"],
          "_ROWS_CACHE": {"key": None, "rows": [], "idx_key": None,
                          "days": {}},
          "data_dir": lambda: tmp}
    for n in _top_nodes:
        exec(compile(ast.Module([n], []), SRC, "exec"), ns)

    class D:
        pass
    for name, src in _meth_src.items():
        exec(compile("class _T:\n" + textwrap.indent(src, "    "),
                     SRC, "exec"), ns)
        fn = ns["_T"].__dict__[name]
        setattr(D, name, staticmethod(fn) if name in STATIC else fn)
    for name, src in _attr_src.items():
        loc = {}
        exec(src, ns, loc)
        setattr(D, name, loc[name])
    return D, ns


def seed(ns, rows):
    with open(ns["SESSIONS_CSV"], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(ns["CSV_HEADER"])
        w.writerows(rows)
    ns["_ROWS_CACHE"].update(key=None, idx_key=None)


def row(d0, mins, task):
    return [d0, "work", "09:00", "10:00", str(mins), task, ""]


# thesis: 6 intervals / 4 active days / 8h, inside a 21d window of 07-13
THESIS = [row(d0, m, "thesis: ch4") for d0, m in
          [("2026-07-06", 60), ("2026-07-06", 60), ("2026-07-08", 180),
           ("2026-07-10", 60), ("2026-07-13", 60), ("2026-07-13", 60)]]


def _due(days):
    return (dt.date.today() + dt.timedelta(days=days)).isoformat()


def _mk(D, **attrs):
    d = D()
    d.today = dt.date(2026, 7, 13)
    for k, v in attrs.items():
        setattr(d, k, v)
    return d


def suite_projection():
    D, ns = fresh()
    seed(ns, THESIS + [["2026-07-09", "break", "12:00", "12:30", "30", "",
                        "lunch"], row("2026-07-07", 60, "email")])
    d = _mk(D)
    dl = {"name": "Thesis", "match": "thesis", "date": "2026-07-23",
          "total_h": 20}
    v = D._dl_velocity(d, dl)
    assert v and abs(v["avg_active_h"] - 2.0) < 1e-9, v
    assert v["active_days"] == 4 and v["window"] == 21, v
    p = D._dl_progress(d, dl)
    assert abs(p["done_h"] - 8.0) < 1e-9, p
    pr = D._dl_projection(d, dl)
    rate = 2.0 * 4 / 21
    d1 = math.ceil(12.0 / rate)
    assert abs(pr["rate"] - rate) < 1e-9, pr
    assert pr["land"] == dt.date.today() + dt.timedelta(days=d1), pr
    assert pr["sooner"] == d1 - math.ceil(12.0 / (rate + 1)) > 0, pr
    assert "you land" in D._projection_line(d, dl)
    d.today = dt.date(2026, 7, 6)          # only 2 intervals in window
    assert D._dl_velocity(d, dl) is None and D._dl_projection(d, dl) is None
    d.today = dt.date(2026, 7, 13)
    assert D._dl_projection(d, {"match": "thesis",
                                "date": "2026-07-23"}) is None  # no scope


def suite_trajectory():
    D, ns = fresh()
    prior = [dt.date(2026, 5, 20) + dt.timedelta(days=i) for i in range(10)]
    recent = [dt.date(2026, 6, 16) + dt.timedelta(days=i) for i in range(20)]
    seed(ns, [row(x.isoformat(), 120, "thesis") for x in prior]
         + [row(x.isoformat(), 180, "thesis") for x in recent])
    d = _mk(D, _day_signal=lambda day, *a, **k: (0, 0),
            _sleep_h=lambda iso: 7.5 if iso < "2026-06-16" else 6.2)
    out = D._trajectory_lines(d)
    assert out[0] == ("8-week trajectory: work 5.0→15.0h/wk ↑, "
                      "sleep 7.5→6.2h ↓"), out
    assert "buying work hours with sleep" in out[1], out
    flat = [dt.date(2026, 5, 20) + dt.timedelta(days=i) for i in range(20)]
    seed(ns, [row(x.isoformat(), 120, "t") for x in flat + recent])
    d._sleep_h = lambda iso: 7.0
    assert D._trajectory_lines(d) == [], "must stay quiet when nothing moved"


def suite_outlook():
    D, ns = fresh()
    rows = list(THESIS)
    for i in range(6):
        rows.append(row((dt.date(2026, 7, 8)
                         + dt.timedelta(days=i)).isoformat(), 90, "tuta"))
    seed(ns, rows)
    d = _mk(D, deadlines=lambda: [
        {"name": "Thesis", "match": "thesis", "date": _due(10), "total_h": 20},
        {"name": "TUTA", "match": "tuta", "date": _due(30), "total_h": 10},
        {"name": "New", "match": "newthing", "date": _due(15), "total_h": 5}])
    out = D._outlook_lines(d)
    blob = "\n".join(out)
    assert "1 of 2 tracked deadline(s) land LATE" in blob, blob
    assert any(l.startswith("  ⚠ Thesis") for l in out), blob
    assert any(l.startswith("  ✓ TUTA") for l in out), blob
    assert any("too little recent" in l for l in out), blob
    assert any("h/day more than you're averaging" in l for l in out), blob
    d.deadlines = lambda: [{"name": "X", "match": "x", "date": _due(5)}]
    assert D._outlook_lines(d) == []


def suite_alignment():
    D, ns = fresh()
    rows = [row((dt.date(2026, 6, 1) + dt.timedelta(days=i)).isoformat(),
                120, "thesis: ch4") for i in range(20)]
    rows += [row("2026-07-06", 120, "run"), row("2026-07-07", 60, "finnish")]
    seed(ns, rows)
    doms = [{"name": "Work", "match": "thesis, tuta", "target_pct": 60},
            {"name": "Body", "match": "run, gym", "target_pct": 15},
            {"name": "Growth", "match": "finnish", "target_pct": 20}]
    d = _mk(D, domains=lambda: doms)
    out = D._alignment_lines(d)
    blob = "\n".join(out)
    assert "43h of tracked time by domain" in blob, blob
    assert any("Work" in l and "93%" in l for l in out), blob
    assert "widest say-do gap: Growth" in blob, blob
    d.domains = lambda: []
    assert D._alignment_lines(d) == []
    seed(ns, [])
    d.domains = lambda: doms
    assert "No tracked work" in D._alignment_lines(d)[0]


def suite_review():
    D, ns = fresh()
    seed(ns, THESIS + [row("2026-07-07", 30, "finnish")])
    late = [{"name": "Thesis", "match": "thesis", "date": _due(10),
             "total_h": 20}]
    doms = [{"name": "Work", "match": "thesis", "target_pct": 60},
            {"name": "Growth", "match": "finnish", "target_pct": 20}]
    d = _mk(D, deadlines=lambda: late, domains=lambda: doms)
    a = D._review_bottom_line(d)[0]
    assert "behind on Thesis" in a and "under-investing in Growth" in a, a
    d.domains = lambda: []
    assert D._review_bottom_line(d)[0].startswith("Main risk: Thesis")
    d.deadlines = lambda: []
    d.domains = lambda: doms
    assert "below where you said" in D._review_bottom_line(d)[0]
    d.domains = lambda: []
    assert "boring good state" in D._review_bottom_line(d)[0]
    # composition: sections appear, insights capped at 3
    d.deadlines = lambda: late
    d.domains = lambda: doms
    d._anomaly_lines = lambda: []
    d._alignment_lines = lambda: ["  Work 90%"]
    d._outlook_lines = lambda: ["  Thesis late"]
    d._trajectory_lines = lambda: []
    d._insight_lines = lambda: ["x", "y", "z", "w"]
    d._day_signal = lambda day, *a, **k: (0, 0)
    d._sleep_h = lambda iso: None
    L = D._life_review_lines(d)
    assert L[0].startswith("LIFE REVIEW — week of"), L
    assert "BOTTOM LINE" in L and "VALUES — are you living them?" in L, L
    assert sum(1 for x in L if x.startswith("  · ")) == 3, L


def suite_anomaly():
    D, ns = fresh()
    rows = THESIS + [row((dt.date(2026, 7, 13)
                          - dt.timedelta(days=20)).isoformat(), 60, "finnish")]
    seed(ns, rows)
    d = _mk(D, goals=lambda: [],
            domains=lambda: [{"name": "Finnish", "match": "finnish"},
                             {"name": "Work", "match": "thesis"}],
            _sleep_h=lambda iso: 5.5 if iso >= "2026-07-13" else 7.5,
            _day_signal=lambda day, *a, **k: (5, 60),
            _health_data=lambda: {})   # _copilot_note now also checks
                                       # _running_hot_line; keep it silent
                                       # here so this suite's assertions
                                       # about the OTHER co-pilot sources
                                       # stay unaffected
    an = D._anomaly_lines(d)
    assert "worst sleep week" in an[0], an          # severity ranks first
    assert any("20 days since any Finnish" in x for x in an), an
    assert not any("since any Work" in x for x in an), an
    d.deadlines = lambda: []
    note = D._copilot_note(d)
    assert note.startswith("co-pilot: ") and "worst sleep week" in note, note
    d.deadlines = lambda: [{"name": "Thesis", "match": "thesis",
                            "date": _due(10), "total_h": 20}]
    assert "Main risk: Thesis" in D._copilot_note(d)
    # signal drought
    seed(ns, rows + [row("2026-07-11", 60, "admin"),
                     row("2026-07-12", 60, "admin")])
    d.deadlines = lambda: []
    d.domains = lambda: []
    d._day_signal = lambda day, *a, **k: (0, 60)
    d._sleep_h = lambda iso: 7.0
    an2 = D._anomaly_lines(d)
    assert any("straight tracked days at ~0% signal" in x for x in an2), an2


def suite_recommend_now():
    D, ns = fresh()
    rows = list(THESIS)
    rows += [row((dt.date(2026, 6, 1) + dt.timedelta(days=i)).isoformat(),
                 60, "reading") for i in range(20)]
    seed(ns, rows)
    d = _mk(D, _signal_kws=lambda day=None: [],
            _day_energy=lambda day=None: None,
            deadlines=lambda: [{"name": "Thesis", "match": "thesis",
                                "date": _due(10), "total_h": 20}])
    assert D._deep_window(d) == (9, 12)

    def at(h):
        return D._recommend_now(d, dt.datetime(2026, 7, 13, h, 0))
    assert "deep-focus window (09–12)" in at(10) and "Thesis" in at(10)
    assert "Past your deep-focus window" in at(14)
    assert "fatigue window" in at(20)
    assert "sleep is the highest-leverage" in at(23)
    d._day_energy = lambda day=None: 2
    assert "Energy's 2/5" in at(10)


def suite_energy_place():
    D, ns = fresh()
    d = D()
    slots = [(time(9, 0), time(11, 0)), (time(13, 0), time(15, 0))]
    items = [("Thesis", 5, 2.0, True), ("Admin", 10, 1.0, False)]
    q = [0.0] * 24
    q[9] = q[10] = 0.1
    q[13] = q[14] = 1.0
    pl, _left = D._energy_place(d, items, slots, q)
    by = {name: placed for name, _b, placed, _s in pl}
    assert by["Thesis"][0][0] == time(13, 0), by    # urgent claims the peak
    assert by["Admin"][0][0] == time(9, 0), by      # admin gets the trough
    pl2, _ = D._energy_place(d, items, slots, None)
    by2 = {name: placed for name, _b, placed, _s in pl2}
    assert by2["Thesis"][0][0] == time(9, 0), by2   # no profile = v8.0 order
    pl3, _ = D._energy_place(d, [("Big", 3, 6.0, True)], slots, q)
    assert abs(pl3[0][3] - 2.0) < 1e-9, pl3         # 6h need, 4h free
    d.today = dt.date(2026, 7, 13)
    seed(ns, [row((dt.date(2026, 6, 1) + dt.timedelta(days=i)).isoformat(),
                  60, "x") for i in range(20)])
    hq = D._hour_quality(d)
    assert hq[9] == 1.0 and hq[12] == 0.0, hq


def suite_last_context():
    D, ns = fresh()
    seed(ns, THESIS)                       # last thesis day: 2026-07-13
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    day = "2026-07-13"
    with open(os.path.join(tmp, day + ".txt"), "w", encoding="utf-8") as f:
        f.write("=== Monday 13.07.2026 ===\n"
                "SIGNAL: thesis\n"
                "random earlier note\n"
                "--- Task: thesis: ch4\n"
                "Start;2026-07-13;09:00:00;0;0;0\n"
                "stuck on regression table, try clustered SEs next\n"
                "Stop;2026-07-13;10:00:00;0;0;3600\n")
    d = _mk(D, diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"),
            _LINE_TAG_RULES=[(re.compile(p), None) for p in
                             (r"^---", r"^(?:Start|Stop|Reset);", r"^===",
                              r"^SIGNAL:", r"^ENERGY:")])
    d.today = dt.date(2026, 7, 14)         # so 07-13 is "the last time"
    ctx = D._last_context(d, "thesis: ch4")
    assert ctx and ctx[0] == dt.date(2026, 7, 13), ctx
    assert ctx[1] == "stuck on regression table, try clustered SEs next", ctx
    assert D._last_context(d, "never-worked") is None
    assert D._last_context(d, "") is None
    os.remove(os.path.join(tmp, day + ".txt"))     # file gone -> None
    assert D._last_context(d, "thesis: ch4") is None


def suite_break_pull():
    D, ns = fresh()
    pl = D._pull_level
    assert pl(19 * 60, 20, True) == 0          # under threshold
    assert pl(20 * 60, 20, True) == 1          # pull-back
    assert pl(40 * 60, 20, True) == 2          # hard pull-back
    assert pl(90 * 60, 20, False) == 0         # not a signal task
    assert pl(90 * 60, 0, True) == 0           # feature off
    rows = []
    for i in range(6):
        d0 = (dt.date(2026, 7, 1) + dt.timedelta(days=i)).isoformat()
        rows += [
            [d0, "work", "09:00", "10:00", "60", "thesis", ""],
            [d0, "break", "10:00", "10:15", "15", "", "walk outside"],
            [d0, "work", "10:15", "10:55", "40", "thesis", ""],
            [d0, "break", "11:30", "11:45", "15", "", "scroll puhelin"],
            [d0, "work", "11:45", "12:05", "20", "thesis", ""]]
    seed(ns, rows)
    d = _mk(D)
    out = D._break_insight(d)
    assert out and "40m (6 samples)" in out[0], out
    assert "20m (6)" in out[0] and "doomscroll tax" in out[0], out
    seed(ns, rows[:10])                        # 2 days -> n<5 -> silent
    assert D._break_insight(d) == []


def suite_reentry():
    D, ns = fresh()

    class FakeDiary:
        def __init__(self, text):
            self._t = text

        def get(self, _a, _b):
            return self._t

    d = _mk(D, diary=FakeDiary("TODO:\n- call landlord\n--- Task: x\n"))
    d.settings = {"tasks": [
        {"name": "thesis: fix table 3", "est_h": 0.2, "priority": "signal"},
        {"name": "thesis: rewrite ch5", "est_h": 3},
        {"name": "email sweep", "est_h": 0.1}]}
    # related to the active task wins, smallest estimate first
    assert D._reentry_opener(d, "thesis: ch4") == "'thesis: fix table 3' (0.2h)"
    # unrelated active task: signal-priority item beats a smaller other
    assert D._reentry_opener(d, "banana") == "'thesis: fix table 3' (0.2h)"
    # backlog #44: a blocked item is excluded from the candidate pool
    # entirely, even though it would otherwise win
    d.settings = {"tasks": [
        {"name": "thesis: fix table 3", "est_h": 0.2, "priority": "signal",
         "blocked_by": "advisor reply"},
        {"name": "thesis: rewrite ch5", "est_h": 3},
        {"name": "email sweep", "est_h": 0.1}]}
    assert D._reentry_opener(d, "banana") == "'email sweep' (0.1h)"
    d.settings = {"tasks": [
        {"name": "thesis: fix table 3", "est_h": 0.2, "priority": "signal"},
        {"name": "thesis: rewrite ch5", "est_h": 3},
        {"name": "email sweep", "est_h": 0.1}]}
    # no estimated items -> today's first TODO bullet (machine lines skipped)
    d.settings = {"tasks": []}
    assert D._reentry_opener(d, "x") == "'call landlord'"
    d.diary = FakeDiary("no bullets at all\n--- Break duration: 0:31:0\n")
    assert D._reentry_opener(d, "x") is None


def suite_procrastination():
    D, ns = fresh()
    rows = []
    for i in range(8):
        d0 = (dt.date(2026, 7, 1) + dt.timedelta(days=i)).isoformat()
        if i < 6:      # 6 bounces: 5 min on intro, then a break
            rows += [[d0, "work", "09:00", "09:05", "5", "thesis: intro", ""],
                     [d0, "break", "09:05", "09:25", "20", "", "scroll"]]
        else:          # 2 real runs: no bounce
            rows += [[d0, "work", "09:00", "10:00", "60", "thesis: intro", ""]]
        rows += [[d0, "work", "10:30", "11:30", "60", "email", ""]]  # healthy
    seed(ns, rows)
    d = _mk(D)
    out = D._procrastination_insight(d)
    assert out and "'thesis: intro'" in out[0], out
    assert "75% of starts (6 of 8)" in out[0], out
    assert "email" not in out[0]
    seed(ns, rows[:8])              # too few starts -> silent
    assert D._procrastination_insight(d) == []


def suite_metrics():
    D, ns = fresh()

    # ---- pure parser: numbers, labels, case/space tolerance, no line ----
    mf = D._metrics_from_text
    assert mf(D, "METRICS: water=6, meditation=10") == {
        "water": 6.0, "meditation": 10.0}, mf(D, "METRICS: water=6, meditation=10")
    assert mf(D, "METRICS: mood=calm, water=6") == {"mood": "calm", "water": 6.0}
    assert mf(D, "no metrics line here") == {}
    assert mf(D, "metrics:  KEY = 5 ") == {"key": 5.0}

    # ---- shorthand: a bare word with no '=' implicitly logs word=1 ----
    assert mf(D, "METRICS: meditation, cold_shower") == {
        "meditation": 1.0, "cold_shower": 1.0}
    assert mf(D, "METRICS: meditation, water=6, cold_shower") == {
        "meditation": 1.0, "water": 6.0, "cold_shower": 1.0}   # mixed forms
    assert mf(D, "METRICS: 5bad, water=6") == {"water": 6.0}   # invalid bare token skipped

    # ---- _day_metrics: live diary text (today) vs a past day file ----
    class FakeDiary:
        def __init__(self, text):
            self._t = text

        def get(self, _a, _b):
            return self._t

    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    with open(os.path.join(tmp, "2026-07-10.txt"), "w", encoding="utf-8") as f:
        f.write("=== Friday 10.07.2026 ===\nMETRICS: meditation=15\n")
    d = _mk(D, diary=FakeDiary("METRICS: water=8\n"),
            diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"))
    assert D._day_metrics(d) == {"water": 8.0}                       # today
    assert D._day_metrics(d, dt.date(2026, 7, 10)) == {"meditation": 15.0}
    assert D._day_metrics(d, dt.date(2099, 1, 1)) == {}               # no file

    # ---- insight: a logged metric with a real signal-share swing ----
    days = [dt.date(2026, 6, 1) + dt.timedelta(days=i) for i in range(20)]
    seed(ns, [row(dd.isoformat(), 60, "thesis") for dd in days])
    d2 = _mk(D, today=dt.date(2026, 6, 20))
    d2._signal_kws = lambda day=None: ["thesis"]
    med_days = {dd.isoformat() for dd in days[:8]}

    def fake_signal(day, kws=None, rows=None):
        pct = 0.9 if day.isoformat() in med_days else 0.4
        return int(round(pct * 60)), 60
    d2._day_signal = fake_signal
    d2._day_metrics = lambda day=None: (
        {"meditation": 10} if (day or d2.today).isoformat() in med_days else {})
    out = D._metrics_insight(d2)
    assert out and "'meditation'" in out[0] and "higher" in out[0], out
    assert "8d logged vs 12d not" in out[0], out

    # below the 5-per-side gate -> silent
    med_days = {dd.isoformat() for dd in days[:3]}
    assert D._metrics_insight(d2) == []


def suite_health_parse():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    hdir = os.path.join(tmp, "health")
    os.makedirs(hdir, exist_ok=True)

    # one combined export: sleep + the new opportunistic columns
    with open(os.path.join(hdir, "export.csv"), "w", newline="",
              encoding="utf-8") as f:
        f.write("Date,Sleep Analysis [Asleep] (hr),"
                "Resting Heart Rate (count/min),"
                "Heart Rate Variability (ms),Mindful Minutes (min),"
                "Weight (lb)\n")
        f.write("2026-07-10,7.5,58,42,12,154\n")
    data = ns["parse_health_dir"](hdir)
    rec = data["2026-07-10"]
    assert abs(rec["sleep_h"] - 7.5) < 1e-9, rec
    assert rec["rhr"] == 58, rec
    assert rec["hrv"] == 42, rec
    assert rec["mindful_min"] == 12, rec
    assert abs(rec["weight_kg"] - 154 * 0.453592) < 1e-6, rec

    # a file with ONLY a metric Health Auto Export ships as its own CSV
    # (no sleep/workout column at all) must NOT be silently skipped —
    # this is the actual gap the widened skip-gate fixes
    with open(os.path.join(hdir, "mindfulness_only.csv"), "w", newline="",
              encoding="utf-8") as f:
        f.write("Date,Mindful Minutes (min)\n2026-07-11,20\n")
    data2 = ns["parse_health_dir"](hdir)
    assert data2["2026-07-11"]["mindful_min"] == 20, data2

    # a file with no recognisable columns at all is safely ignored
    with open(os.path.join(hdir, "unrelated.csv"), "w", newline="",
              encoding="utf-8") as f:
        f.write("Name,Value\nx,1\n")
    ns["parse_health_dir"](hdir)   # must not raise


def suite_daylight():
    D, ns = fresh()

    # ---- pure formula: reference points (see the sanity check that
    # motivated this feature — matches real-world day lengths within the
    # expected few-minutes approximation error) ----
    dlh = ns["day_length_hours"]
    assert abs(dlh(dt.date(2026, 3, 20), 0.0) - 12.0) < 0.05      # equinox, equator
    assert abs(dlh(dt.date(2026, 7, 1), 0.0) - 12.0) < 0.05       # equator, any day
    summer = dlh(dt.date(2026, 6, 21), 60.2)                      # Helsinki solstices
    winter = dlh(dt.date(2026, 12, 21), 60.2)
    assert 17 < summer < 20, summer
    assert 4 < winter < 8, winter
    assert summer > winter + 10                                    # a real swing

    # ---- _daylight_h: off by default, reads settings when set ----
    d = _mk(D, settings={})
    assert D._daylight_h(d, dt.date(2026, 6, 21)) is None
    d.settings = {"daylight_lat": 60.2}
    assert abs(D._daylight_h(d, dt.date(2026, 6, 21)) - summer) < 1e-9

    # ---- insight: no lat -> silent regardless of history ----
    d2 = _mk(D, today=dt.date(2026, 7, 1), settings={})
    assert D._daylight_insight(d2) == []

    # ---- insight: lat set but too little history -> silent ----
    d2.settings = {"daylight_lat": 60.2}
    d2._day_energy = lambda day=None: None
    seed(ns, [row("2026-06-25", 60, "x")])
    assert D._daylight_insight(d2) == []

    # ---- insight: real history but no seasonal swing (20 consecutive
    # June days) -> silent, not a false 'season' out of noise ----
    june_days = [dt.date(2026, 6, 1) + dt.timedelta(days=i) for i in range(20)]
    seed(ns, [row(x.isoformat(), 120, "x") for x in june_days])
    assert D._daylight_insight(d2) == []

    # ---- insight: a real winter (short-daylight, low-output) vs summer
    # (long-daylight, high-output) split fires with the right numbers ----
    dec_days = [dt.date(2025, 12, 1) + dt.timedelta(days=i) for i in range(20)]
    seed(ns, [row(x.isoformat(), 120, "x") for x in dec_days]     # 2h/day, dark
         + [row(x.isoformat(), 300, "x") for x in june_days])     # 5h/day, light
    d2._day_energy = lambda day=None: (
        2 if day.month == 12 else 4 if day.month == 6 else None)
    out = D._daylight_insight(d2)
    assert out and "less on the darker days" in out[0], out
    assert "2.0h work avg" in out[0] and "5.0h" in out[0], out
    assert "energy: 2.0/5 dark vs 4.0/5 light" in out[1], out


def suite_word_drift():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    d = _mk(D, today=dt.date(2026, 7, 13),
            diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"))

    # ---- _diary_word_counts: structural lines excluded, stopwords out ----
    # (a date well outside either window the drift sub-test below uses,
    # so the two sub-tests' files in the same tmp dir can't cross-count)
    p = os.path.join(tmp, "2020-01-01.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("=== Wednesday 01.01.2020 ===\n"
                "SIGNAL: apartment, thesis\n"
                "METRICS: water=6\n"
                "Start;2020-01-01;09:00:00;0;0;0\n"
                "--- Task: thesis: ch4\n"
                "wrote about the apartment search downtown quietly\n"
                "TODO:\n- call landlord about apartment\n")
    counts, total = D._diary_word_counts(d, dt.date(2020, 1, 1), dt.date(2020, 1, 1))
    # only the free-prose line and the TODO bullet's own text count — the
    # ===/SIGNAL/METRICS/Start/Task/"TODO:" header lines contribute nothing
    assert counts.get("apartment") == 2, counts     # once per surviving line
    assert "about" not in counts, counts             # stopword
    assert "thesis" not in counts, counts    # only appeared inside skipped lines
    assert total == 8, (counts, total)

    # ---- word-drift insight: a real recent-only word beats steady filler ----
    # today=2026-07-13, default windows: recent=[06-14..07-13], prior=
    # [03-16..06-13] — both file batches must fall inside their own window
    filler = "thesis chapter regression models economics dataset variable estimate"
    prior_days = [dt.date(2026, 4, 1) + dt.timedelta(days=i) for i in range(10)]
    recent_days = [dt.date(2026, 6, 20) + dt.timedelta(days=i) for i in range(10)]
    for pd in prior_days:
        with open(os.path.join(tmp, pd.isoformat() + ".txt"), "w",
                  encoding="utf-8") as f:
            # "girlfriend" only ever appears in the PRIOR window (2x/day,
            # so it clearly beats other candidates for the fade check) —
            # never mentioned in the recent files below at all
            f.write(filler + " girlfriend girlfriend\n")
    for rd in recent_days:
        with open(os.path.join(tmp, rd.isoformat() + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(filler + " apartment moving apartment search\n")
    out = D._word_drift_insight(d)
    assert out and "'apartment'" in out[0], out
    assert "(0→20 mentions, last 30d vs prior 90d)" in out[0], out

    # ---- fade direction: a word frequent before, silent now ----
    fade = D._word_fade_insight(d)
    assert fade and "'girlfriend'" in fade[0], fade
    assert "(20→0 mentions, last 30d vs prior 90d)" in fade[0], fade
    assert "gone quiet" in fade[0], fade

    # ---- silence gate: too little total volume either side ----
    d2 = _mk(D, today=dt.date(2099, 1, 1),
             diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"))
    assert D._word_drift_insight(d2) == []
    assert D._word_fade_insight(d2) == []


def suite_ask_diary():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    d = _mk(D, diary_dir=lambda: tmp)

    # day A: 5 hits but only 1 DISTINCT term ("thesis") -> breadth 1
    with open(os.path.join(tmp, "2026-01-01.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(["thesis progress notes"] * 5))
    # day B: 2 hits, 2 DISTINCT terms ("thesis" + "interview") -> breadth 2
    with open(os.path.join(tmp, "2026-01-02.txt"), "w", encoding="utf-8") as f:
        f.write("thesis update\ninterview scheduled next week\n")
    # a day with no match at all
    with open(os.path.join(tmp, "2026-01-03.txt"), "w", encoding="utf-8") as f:
        f.write("unrelated content about groceries\n")

    ranked = D._diary_rank_days(d, "thesis interview")
    assert len(ranked) == 2, ranked
    # breadth (distinct terms matched) beats raw hit count
    assert ranked[0][0] == dt.date(2026, 1, 2), ranked
    assert ranked[0][1] == 2, ranked
    assert ranked[1][0] == dt.date(2026, 1, 1), ranked
    assert ranked[1][1] == 1 and len(ranked[1][2]) == 5, ranked

    assert D._diary_rank_days(d, "groceries") and \
        D._diary_rank_days(d, "groceries")[0][0] == dt.date(2026, 1, 3)
    assert D._diary_rank_days(d, "xyznonexistent") == []
    assert D._diary_rank_days(d, "") == []       # no usable terms

    text = D._matching_days_text(d, "thesis interview")
    assert 'Diary search: "thesis interview"' in text, text
    assert "2026-01-02" in text and "2026-01-01" in text, text
    # day B (higher-ranked) must appear before day A in the excerpt text
    assert text.index("2026-01-02") < text.index("2026-01-01"), text
    assert D._matching_days_text(d, "nothingmatchesthis") is None


def suite_lag():
    D, ns = fresh()
    TODAY = dt.date(2026, 6, 15)     # cutoff (today-90) = 2026-03-17

    # ---- workout day -> next-day output ----
    wo_days = [dt.date(2026, 4, 1) + dt.timedelta(days=i) for i in range(10)]
    now_days = [dt.date(2026, 5, 1) + dt.timedelta(days=i) for i in range(10)]
    rows = ([row((d + dt.timedelta(days=1)).isoformat(), 300, "x") for d in wo_days]
           + [row((d + dt.timedelta(days=1)).isoformat(), 60, "x") for d in now_days])
    seed(ns, rows)
    d = _mk(D, today=TODAY)
    wo_set = {x.isoformat() for x in wo_days}
    d._health_data = lambda: {iso: {"workout_min": 30} for iso in wo_set}
    line = D._lag_workout_line(d, 90)
    assert line and "5.0h of work vs 1.0h" in line and "productivity tool" in line, line

    # ---- short-sleep night -> the day AFTER that (not same-day) ----
    seed(ns, rows)     # same next-day work pattern, reused for this sub-test
    # now_days' next-day work was seeded low (60m) -> make THOSE the
    # short-sleep nights, so short_next collects the low values (a=1.0h)
    # and wo_days (next-day work 300m) become the full-sleep nights (b=5.0h)
    short_set = {x.isoformat() for x in now_days}
    d._sleep_h = lambda iso: 5.5 if iso in short_set else 7.5
    line2 = D._lag_sleep_debt_line(d, 90)
    assert line2 and "1.0h" in line2 and "5.0h" in line2, line2
    assert "doesn't clear in one day" in line2, line2

    # ---- late-evening work -> next morning's first-session start time ----
    late_days = [dt.date(2026, 4, 1) + dt.timedelta(days=i) for i in range(5)]
    normal_days = [dt.date(2026, 5, 1) + dt.timedelta(days=i) for i in range(5)]
    rows2 = []
    for x in late_days:
        rows2.append(row(x.isoformat(), 30, "x"))
        rows2[-1][2] = "21:30"                                    # late start
        nxt = x + dt.timedelta(days=1)
        rows2.append(row(nxt.isoformat(), 30, "x"))
        rows2[-1][2] = "10:00"                                     # slow next morning
    for x in normal_days:
        rows2.append(row(x.isoformat(), 30, "x"))
        rows2[-1][2] = "09:00"
        nxt = x + dt.timedelta(days=1)
        rows2.append(row(nxt.isoformat(), 30, "x"))
        rows2[-1][2] = "07:00"                                     # early next morning
    seed(ns, rows2)
    line3 = D._lag_evening_start_line(d, 90)
    assert line3 and "10:00" in line3 and "07:00" in line3, line3
    assert "later" in line3, line3

    # ---- fragmentation: a 6+ switch day -> shallower next day ----
    d._signal_kws = lambda day=None: ["x"]
    d._decay_cycle = lambda: None              # force the flat 20m threshold
    high_days = [dt.date(2026, 4, 10) + dt.timedelta(days=i) for i in range(5)]
    low_days = [dt.date(2026, 5, 10) + dt.timedelta(days=i) for i in range(5)]
    rows4 = []
    for x in high_days:
        # 7 rows alternating x/y 10 min apart = 6 switches that day
        for i, task in enumerate(["x", "y"] * 3 + ["x"]):
            r = row(x.isoformat(), 10, task)
            r[2] = f"{9 + i // 6:02d}:{(i * 10) % 60:02d}"
            rows4.append(r)
        nxt = (x + dt.timedelta(days=1)).isoformat()
        # next day: FOUR separate 15m blocks (distinct task strings so
        # they don't merge into one run), all < the 20m threshold, total
        # 60m clears the _day_shallow_frac minimum -> 100% shallow
        for k, sub in enumerate(("xa", "xb", "xc", "xd")):
            r2 = row(nxt, 15, sub)
            r2[2] = f"{9 + k:02d}:00"
            rows4.append(r2)
    for x in low_days:
        rows4.append(row(x.isoformat(), 30, "x"))          # 0 switches
        nxt = (x + dt.timedelta(days=1)).isoformat()
        rows4.append(row(nxt, 60, "x"))         # next day: one 60m block, deep
    seed(ns, rows4)
    frag = D._lag_fragmentation_line(d, 90)
    assert frag and "100%" in frag and "0%" in frag, frag
    assert "fragmentation carries over" in frag, frag

    # ---- composition: all four fire, none crash on missing data ----
    seed(ns, rows2)
    d._signal_kws = lambda day=None: []          # no signal -> frag check silent
    out = D._lag_insight(d, 90)
    assert len(out) >= 1 and any("10:00" in x for x in out), out

    # ---- silence: too few pairs on one side ----
    seed(ns, [row("2026-06-01", 60, "x")])
    d2 = _mk(D, today=dt.date(2026, 6, 2))
    d2._health_data = lambda: {}
    d2._sleep_h = lambda iso: None
    d2._signal_kws = lambda day=None: []
    assert D._lag_workout_line(d2, 90) is None
    assert D._lag_sleep_debt_line(d2, 90) is None
    assert D._lag_evening_start_line(d2, 90) is None
    assert D._lag_fragmentation_line(d2, 90) is None
    assert D._lag_insight(d2, 90) == []


def suite_week_ahead():
    D, ns = fresh()
    d = _mk(D, today=dt.date(2026, 7, 13))   # a Monday

    # ---- overbooked: aggregate need exceeds aggregate capacity ----
    d.deadlines = lambda: [{"name": "Thesis"}, {"name": "TUTA"}]
    d._day_capacity = lambda dd: 2.0                          # 14h/week total
    d._dl_progress = lambda dl: {"total_h": 20, "left": 30,
                                 "remaining_h": 20, "needed_per_day": 4.0}
    d._dl_projection = lambda dl: None                         # not "behind"
    out = D._week_ahead_lines(d)
    assert out and out[0] == "" and "WEEK AHEAD: 14.0h free" in out[1], out
    assert any("overbooked" in x for x in out), out

    # ---- one genuinely tight day among otherwise-roomy ones ----
    tight_day = d.today + dt.timedelta(days=3)
    d._day_capacity = lambda dd: 1.0 if dd == tight_day else 6.0
    d._dl_progress = lambda dl: {"total_h": 10, "left": 30,
                                 "remaining_h": 2.0, "needed_per_day": 0.3}
    out2 = D._week_ahead_lines(d)
    assert out2 and any("tightest day" in x for x in out2), out2
    assert not any("overbooked" in x for x in out2), out2   # not ALSO overbooked

    # ---- a deadline behind at real pace gets named ----
    d._day_capacity = lambda dd: 6.0                           # uniform, roomy
    d._dl_projection = lambda dl: {"delta": 5}                 # behind
    out3 = D._week_ahead_lines(d)
    assert out3 and any("already behind at real pace" in x and "Thesis" in x
                        for x in out3), out3

    # ---- silence: no deadlines with real remaining scope at all ----
    d.deadlines = lambda: []
    assert D._week_ahead_lines(d) == []

    # ---- silence: a normal week — slack, no tight day, ahead of pace ----
    d.deadlines = lambda: [{"name": "Thesis"}]
    d._dl_projection = lambda dl: {"delta": -2}                # ahead
    assert D._week_ahead_lines(d) == []


def suite_break_budget():
    D, ns = fresh()
    TODAY = dt.date(2026, 4, 20)

    def work_break(iso, brk_min, brk_hour):
        # end time is a placeholder — _break_budget_line only reads the
        # break's start hour (field 2) and minutes (field 4)
        return [[iso, "work", "09:00", "12:00", "180", "x", ""],
                [iso, "break", f"{brk_hour:02d}:00", "23:59",
                 str(brk_min), "", ""]]

    rows = []
    early_days = [dt.date(2026, 4, 1) + dt.timedelta(days=i) for i in range(3)]
    late_days = [dt.date(2026, 4, 4) + dt.timedelta(days=i) for i in range(12)]
    for x in early_days:
        rows += work_break(x.isoformat(), 200, 9)      # big break, EARLY (09:00)
    for x in late_days:
        rows += work_break(x.isoformat(), 10, 15)      # small break, LATE (15:00)
    rows += [["2026-04-20", "break", "08:00", "08:45", "45", "", ""]]  # today
    seed(ns, rows)

    d = _mk(D, today=TODAY)
    line = D._break_budget_line(d, 60, 11)   # now_hour=11: before the 15:00 breaks
    assert line is not None, line
    assert "breaks so far 45m" in line, line
    # full-day norm: median of ALL 15 days' totals ([200]*3 + [10]*12) = 10
    assert "full-day norm ~10m" in line, line
    # typical-by-11am: the 12 late-break days have accrued NOTHING yet by
    # 11am (their break is at 15:00) and must count as 0, not be absent —
    # median of ([0]*12 + [200]*3) = 0. Getting this right is the actual
    # point of the test: omitting the zero days would wrongly give 200.
    assert "your typical by this hour 0m" in line, line

    # ---- silence: not enough real-workday history ----
    seed(ns, rows[:6])     # only the 3 early days survive
    assert D._break_budget_line(d, 60, 11) is None

    # ---- v2 (backlog #72): weekday-specific norm once today's weekday
    # has its own n>=10, overriding the all-days blend ----
    D2, ns2 = fresh()
    TODAY2 = dt.date(2026, 4, 20)          # a Monday
    assert TODAY2.weekday() == 0, TODAY2.weekday()
    mondays = [TODAY2 - dt.timedelta(weeks=i) for i in range(1, 11)]   # 10 Mondays
    tuesdays = [TODAY2 - dt.timedelta(weeks=i) + dt.timedelta(days=1)
                for i in range(1, 11)]                                 # 10 Tuesdays
    rows2 = []
    for x in mondays:
        rows2 += work_break(x.isoformat(), 50, 20)    # Mondays: big breaks
    for x in tuesdays:
        rows2 += work_break(x.isoformat(), 10, 20)    # Tuesdays: small breaks
    rows2 += [["2026-04-20", "break", "08:00", "08:45", "45", "", ""]]  # today
    seed(ns2, rows2)
    d2 = _mk(D2, today=TODAY2)
    line2 = D2._break_budget_line(d2, 90, 11)
    assert line2 is not None, line2
    # 10 Mondays >= n>=10 -> weekday-specific median (50m), not the
    # all-days blend (median of [50]*10 + [10]*10 = 30m)
    assert "full-day norm ~50m (Mons)" in line2, line2

    # ---- v2 fallback: today's weekday doesn't have its own n>=10 yet ----
    d3 = _mk(D2, today=dt.date(2026, 4, 21))   # a Tuesday
    wednesdays = [TODAY2 - dt.timedelta(weeks=i) + dt.timedelta(days=2)
                  for i in range(1, 11)]                               # 10 Wednesdays
    rows3 = []
    for x in mondays:
        rows3 += work_break(x.isoformat(), 50, 20)         # 10 Mondays: big breaks
    for x in tuesdays[:9]:
        rows3 += work_break(x.isoformat(), 10, 20)         # only 9 Tuesdays: n<10
    for x in wednesdays:
        rows3 += work_break(x.isoformat(), 10, 20)         # 10 Wednesdays: small breaks
    seed(ns2, rows3)
    line3 = D2._break_budget_line(d3, 90, 11)
    assert line3 is not None, line3
    assert "(Tues)" not in line3, line3     # 9 Tuesdays < n>=10 -> no per-weekday tag
    # all-days blend: 29 values = ten 50s + nineteen 10s -> median (index 14) = 10m
    assert "full-day norm ~10m" in line3, line3


def suite_lens_overlap():
    D, ns = fresh()
    d = _mk(D, today=dt.date(2026, 7, 13))
    d._match_kws = lambda spec: [k.strip().lower()
                                 for k in (spec or "").split(",") if k.strip()]

    # ---- registry: empty-match deadline excluded, others included ----
    d.goals = lambda: [{"name": "Body", "match": "run, gym"}]
    d.domains = lambda: [{"name": "Growth", "match": "finnish"}]
    d.deadlines = lambda: [{"name": "Thesis", "match": "thesis"},
                          {"name": "Everything", "match": ""}]
    reg = D._lens_registry(d)
    names = {n for _c, n, _k in reg}
    assert names == {"Body", "Growth", "Thesis"}, reg   # "Everything" excluded

    # ---- real double-count via DIFFERENT keywords, no shared string ----
    days = [dt.date(2026, 6, 1) + dt.timedelta(days=i) for i in range(5)]
    rows = [row(x.isoformat(), 60, "morning run training") for x in days]
    seed(ns, rows)
    d.goals = lambda: [{"name": "Body", "match": "run"}]
    d.domains = lambda: [{"name": "Fitness", "match": "training"}]
    d.deadlines = lambda: []
    out = D._lens_overlap_lines(d, 60)
    assert out, "same task matched by two disjoint-string keywords must fire"
    assert "Body" in out[0] and "Fitness" in out[0] and "5.0h" in out[0], out

    # ---- keyword-STRING overlap that never matches a real task -> silent ----
    d.goals = lambda: [{"name": "A", "match": "unicorn"}]
    d.domains = lambda: [{"name": "B", "match": "unicorn"}]
    seed(ns, [row("2026-06-01", 60, "email")])   # no task ever mentions it
    assert D._lens_overlap_lines(d, 60) == []

    # ---- no real overlap at all ----
    d.goals = lambda: [{"name": "Body", "match": "run"}]
    d.domains = lambda: [{"name": "Growth", "match": "finnish"}]
    seed(ns, [row("2026-06-01", 60, "run"), row("2026-06-02", 60, "finnish")])
    assert D._lens_overlap_lines(d, 60) == []

    # ---- fewer than 2 declared lenses -> [] ----
    d.goals = lambda: [{"name": "Body", "match": "run"}]
    d.domains = lambda: []
    assert D._lens_overlap_lines(d, 60) == []


def suite_health_extras():
    D, ns = fresh()
    d = _mk(D, today=dt.date(2026, 7, 13))

    # ---- nothing configured/captured -> the explanatory footer ----
    d._health_data = lambda: {}
    d._daylight_h = lambda day: None
    out = D._health_extras_lines(d)
    assert any("Nothing here yet" in x for x in out), out

    # ---- real data on one day -> exact column formatting ----
    target = d.today.isoformat()
    d._health_data = lambda: {target: {"mindful_min": 12, "rhr": 58,
                                       "hrv": 42, "weight_kg": 70.5}}
    d._daylight_h = lambda day: 8.3 if day == d.today else None
    out2 = D._health_extras_lines(d)
    assert not any("Nothing here yet" in x for x in out2), out2
    row_line = next(x for x in out2 if x.startswith(f" {d.today:%a %d.%m}"))
    assert "12m" in row_line and "58" in row_line and "42" in row_line, row_line
    assert "70.5" in row_line and "8.3h" in row_line, row_line
    # a day with nothing at all still renders as dashes, not a crash
    other_line = out2[3]     # second data row (index 2 is the first date)
    assert "-" in other_line


def suite_backup_integrity():
    D, ns = fresh()
    fn = ns["backup_integrity_line"]
    TODAY = dt.date(2026, 7, 14)

    # ---- silence: no sessions.csv yet at all (nothing to protect) ----
    assert fn(TODAY) is None

    seed(ns, [])   # creates sessions.csv (header only)
    bdir = os.path.join(ns["data_dir"](), "backups")

    # ---- silence: no backups dir/files yet, but sessions.csv exists ----
    # (backup_if_due hasn't run yet this session — reported, not silent,
    # since a brand-new install has an empty backups/ by design and that's
    # a different situation from one that WAS working and stopped; still,
    # both should be visible on a Data doctor run)
    assert fn(TODAY) == ("no backup found yet — the weekly automation "
                         "may not have run")

    os.makedirs(bdir, exist_ok=True)

    # ---- silence: a recent backup (3 days old) — healthy, no line ----
    open(os.path.join(bdir, "sessions_2026-07-11.csv"), "w").close()
    assert fn(TODAY) is None

    # ---- silence: right at the edge (10 days old, the buffer) ----
    open(os.path.join(bdir, "sessions_2026-07-04.csv"), "w").close()
    assert fn(TODAY) is None      # (2026-07-11 is still newest, 3d old)

    # ---- speaks: newest backup is stale (15 days old) ----
    for fname in os.listdir(bdir):
        os.remove(os.path.join(bdir, fname))
    open(os.path.join(bdir, "sessions_2026-06-29.csv"), "w").close()
    line = fn(TODAY)
    assert line == ("last backup: 15 days ago (expected weekly) — the "
                    "automation may have stopped"), line

    # ---- picks the NEWEST of several backup files, not the oldest ----
    open(os.path.join(bdir, "sessions_2026-07-08.csv"), "w").close()  # 6d old
    assert fn(TODAY) is None      # newest (6d) is healthy even though a
                                  # 15d-old file also sits in backups/


def suite_running_hot():
    D, ns = fresh()
    TODAY = dt.date(2026, 7, 13)
    recent_lo = TODAY - dt.timedelta(days=13)                 # 2026-06-30
    prior_hi = recent_lo - dt.timedelta(days=1)                # 2026-06-29
    prior_lo = prior_hi - dt.timedelta(days=59)                # 2026-05-01
    recent_isos = {(recent_lo + dt.timedelta(days=i)).isoformat()
                   for i in range(14)}
    prior_isos = {(prior_lo + dt.timedelta(days=i)).isoformat()
                  for i in range(60)}

    def wb(iso, work_min, brk_min, start="09:00"):
        end = f"{int(start[:2]) + 1:02d}:{start[3:]}"
        return [[iso, "work", start, end, str(work_min), "x", ""],
                [iso, "break", "12:00", "12:30", str(brk_min), "", ""]]

    # ---- speaks: sleep debt + late nights (2 signals) ----
    rows = []
    for iso in prior_isos:
        rows += wb(iso, 100, 20)
    for iso in recent_isos:
        rows += wb(iso, 100, 20)          # same ratio both sides: no break flag
    late_isos = ["2026-07-01", "2026-07-03", "2026-07-05"]
    for iso in late_isos:
        rows += [[iso, "work", "21:30", "22:00", "30", "y", ""]]
    seed(ns, rows)
    d = _mk(D, today=TODAY, _health_data=lambda: {},
            _sleep_h=lambda iso: 6.5 if iso in recent_isos else
                                 (7.5 if iso in prior_isos else None))
    line = D._running_hot_line(d, 14, 60)
    assert line is not None, line
    assert line.startswith("14 days running hot ("), line
    assert "sleep -1.0h/night vs norm" in line, line
    assert "3 late nights" in line, line
    assert "breaks compressed" not in line, line
    assert "schedule one flat day before your body schedules it" in line, line

    # ---- silence: only ONE signal (sleep alone) never speaks ----
    d2 = _mk(D, today=TODAY, _health_data=lambda: {},
             _sleep_h=lambda iso: 6.5 if iso in recent_isos else
                                  (7.5 if iso in prior_isos else None))
    rows_silent = []
    for iso in prior_isos | recent_isos:
        rows_silent += wb(iso, 100, 20)   # same ratio both sides, no late rows
    seed(ns, rows_silent)
    assert D._running_hot_line(d2, 14, 60) is None

    # ---- silence: sparse sleep data can't clear the n>=5/n>=10 gate ----
    d3 = _mk(D, today=TODAY, _health_data=lambda: {},
             _sleep_h=lambda iso: 5.0 if iso == max(recent_isos) else None)
    assert D._running_hot_line(d3, 14, 60) is None

    # ---- speaks: workouts stopped + break-ratio compression (2 signals) ----
    rows2 = []
    for iso in prior_isos:
        rows2 += wb(iso, 100, 20)          # prior ratio 20/100 = 0.20
    for iso in recent_isos:
        rows2 += wb(iso, 100, 5)           # recent ratio 5/100 = 0.05 <= 0.6*0.20
    seed(ns, rows2)
    d4 = _mk(D, today=TODAY, _sleep_h=lambda iso: 7.0,
             _health_data=lambda: {iso: {"workout_min": 30} for iso in prior_isos})
    line2 = D._running_hot_line(d4, 14, 60)
    assert line2 is not None, line2
    assert "workouts stopped" in line2, line2
    assert "breaks compressed" in line2, line2
    assert "sleep" not in line2.split("(")[1].split(")")[0], line2


def suite_meeting_fragmentation():
    D, ns = fresh()
    win_start, win_end = time(9, 0), time(17, 0)
    d = _mk(D, today=dt.date(2026, 7, 13))

    # ---- pure helpers, hand-verified ----
    free = ns["_free_from_busy"](win_start, win_end, [(time(12, 0), time(13, 0))])
    assert free == [(time(9, 0), time(12, 0)), (time(13, 0), time(17, 0))], free
    # both sides of a 1h midday meeting stay >=90m -> both count
    assert ns["_deep_capacity_minutes"](free) == 180 + 240, free

    # a meeting near the END of the window strands a <90m sliver after
    # it — that sliver stops counting as deep capacity at all
    meetings = [(time(15, 40), time(16, 0))]      # 20-minute meeting
    tax = D._day_fragmentation_tax(d, meetings, win_start, win_end)
    assert len(tax) == 1, tax
    s, e, cost = tax[0]
    assert (s, e) == (time(15, 40), time(16, 0)), tax
    # WITH: only the 09:00-15:40 (400m) block qualifies (16:00-17:00 is
    # 60m, under the 90m floor). WITHOUT: the whole 09:00-17:00 (480m)
    # qualifies as one block. cost = (480-400)/60 = 1.333h -> "1.3"
    assert abs(cost - 80 / 60) < 1e-9, cost

    # ---- composition: silent with no calendar configured ----
    d = _mk(D, today=dt.date(2026, 7, 13))
    d._busy_intervals = lambda: {}
    d._work_window = lambda: (win_start, win_end)
    assert D._meeting_fragmentation_lines(d) == []

    # ---- composition: silent when the week's total tax is negligible ----
    d._busy_intervals = lambda: {"2026-07-10": [(time(12, 0), time(12, 20))]}
    assert D._meeting_fragmentation_lines(d) == []   # 0.3h < the 0.5h floor

    # ---- composition: speaks — worst offender + week total ----
    d._busy_intervals = lambda: {
        "2026-07-08": [(time(15, 40), time(16, 0))],   # Wednesday, 1.333h tax
        "2026-07-10": [(time(12, 0), time(12, 20))],   # Friday, 0.333h tax
    }
    out = D._meeting_fragmentation_lines(d)
    assert len(out) == 2, out
    assert out[0] == ("Wednesday's 15:40 meeting: 0.3h long, cost 1.3h "
                      "of deep capacity"), out
    assert out[1] == "meeting fragmentation tax this week: 1.7h", out

    # ---- honesty: a day outside the 7-day window doesn't count ----
    d._busy_intervals = lambda: {
        "2026-06-01": [(time(15, 40), time(16, 0))],   # long ago
        "2026-07-10": [(time(12, 0), time(12, 20))],
    }
    assert D._meeting_fragmentation_lines(d) == []      # only 0.3h left


def suite_year_rhythm():
    D, ns = fresh()
    TODAY = dt.date(2026, 7, 15)      # a Wednesday, week-of-Monday 07-13
    assert TODAY.weekday() == 2, TODAY.weekday()

    rows = [
        # week 0 (containing today): two rows in the SAME (week, hour)
        # cell, on different days — must sum, not overwrite
        ["2026-07-15", "work", "09:05", "09:25", "20", "x", ""],
        ["2026-07-13", "work", "09:40", "10:05", "25", "y", ""],
        # week 1 (one week back): a BREAK row — breaks count here,
        # unlike _heatmap which skips them
        ["2026-07-06", "break", "14:00", "14:50", "50", "", ""],
        # week 3 (the oldest week in a weeks=4 window): right at the edge
        ["2026-06-22", "work", "08:00", "08:15", "15", "z", ""],
        # one day OUTSIDE the weeks=4 window: must be excluded entirely
        ["2026-06-21", "work", "08:00", "08:15", "999", "old", ""],
        # a future date: must be excluded (never counted, not just
        # clamped)
        ["2026-07-20", "work", "09:00", "09:15", "999", "future", ""],
    ]
    seed(ns, rows)
    d = _mk(D, today=TODAY)
    grid = D._year_rhythm_grid(d, 4)
    assert grid == {(0, 9): 45, (1, 14): 50, (3, 8): 15}, grid


def suite_energy_forecast():
    D, ns = fresh()
    TODAY = dt.date(2026, 7, 14)      # a Tuesday
    days = 70
    cutoff = TODAY - dt.timedelta(days=days)

    tuesdays = []
    dcur = cutoff
    while dcur < TODAY:
        if dcur.weekday() == 1:
            tuesdays.append(dcur)
        dcur += dt.timedelta(days=1)
    assert len(tuesdays) == 10, tuesdays
    rest_tues, debt_tues = tuesdays[:5], tuesdays[5:]

    sleep = {}
    dcur = cutoff - dt.timedelta(days=5)
    while dcur <= TODAY + dt.timedelta(days=1):
        sleep[dcur.isoformat()] = 7.5          # broad default: the norm
        dcur += dt.timedelta(days=1)
    for t in rest_tues:
        for i in range(3):
            sleep[(t - dt.timedelta(days=i)).isoformat()] = 8.5   # rested
    for t in debt_tues:
        for i in range(3):
            sleep[(t - dt.timedelta(days=i)).isoformat()] = 5.5   # in debt
    for i in range(3):
        sleep[(TODAY - dt.timedelta(days=i)).isoformat()] = 5.5   # today: debt

    rows = []
    for t in rest_tues:
        rows.append([t.isoformat(), "work", "09:00", "14:00", "300", "x", ""])
    for t in debt_tues:
        rows.append([t.isoformat(), "work", "09:00", "11:00", "120", "x", ""])
    seed(ns, rows)
    d = _mk(D, today=TODAY, _sleep_h=lambda iso: sleep.get(iso))

    line = D._energy_forecast_line(d, days)
    assert line is not None, line
    # norm (median of 70 days, mostly 7.5h) = 7.5h; today's own 3-night
    # rolling average is 5.5h (<norm) -> "running on debt"; the 5 debt
    # Tuesdays all tracked exactly 2.0h -> the matched band collapses
    # to a single value, hand-verified
    assert line == ("today smells like a 2.0-2.0h day (Tuesday, running "
                    "on debt, n=5) — plan the must-do inside that"), line

    # ---- silence: no usable rolling reading for today (all 3 of the
    # last nights unknown, not just one) ----
    blank_recent = {TODAY.isoformat(),
                    (TODAY - dt.timedelta(days=1)).isoformat(),
                    (TODAY - dt.timedelta(days=2)).isoformat()}
    d2 = _mk(D, today=TODAY, _sleep_h=lambda iso: None
             if iso in blank_recent else sleep.get(iso))
    assert D._energy_forecast_line(d2, days) is None

    # ---- silence: not enough sleep history to trust a personal norm ----
    d3 = _mk(D, today=TODAY, _sleep_h=lambda iso: 7.5
             if iso == TODAY.isoformat() else None)
    assert D._energy_forecast_line(d3, days) is None


def suite_experiment_engine():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    monday = dt.date(2026, 7, 13)          # a Monday
    assert monday.weekday() == 0, monday.weekday()

    def week_days(mon):
        return [mon + dt.timedelta(days=i) for i in range(7)]

    rows, sleep = [], {}
    # 4 baseline weeks (the 4 weeks BEFORE the experiment week): 6 normal
    # days + a Sunday work block starting 22:00 (late), 7.0h sleep/night
    for w in range(1, 5):
        for i, day in enumerate(week_days(monday - dt.timedelta(weeks=w))):
            sleep[day.isoformat()] = 7.0
            if i == 6:
                rows.append([day.isoformat(), "work", "22:00", "23:00",
                            "60", "x", ""])
            else:
                rows.append([day.isoformat(), "work", "09:00", "12:20",
                            "200", "x", ""])
    # the experiment week itself: same total minutes (Sunday's block
    # just moved earlier, off the late-evening hours), 7.5h sleep/night
    for i, day in enumerate(week_days(monday)):
        sleep[day.isoformat()] = 7.5
        if i == 6:
            rows.append([day.isoformat(), "work", "18:00", "19:00",
                        "60", "x", ""])
        else:
            rows.append([day.isoformat(), "work", "09:00", "12:20",
                        "200", "x", ""])
    seed(ns, rows)

    def write_day_file(day, text):
        with open(os.path.join(tmp, day.isoformat() + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(text)

    write_day_file(monday, "=== Monday 13.07.2026 ===\nSIGNAL: thesis\n"
                           "EXPERIMENT: no work after 21:00\n")
    d = _mk(D, diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"),
            _sleep_h=lambda iso: sleep.get(iso))

    line = D._experiment_review_line(d, monday)
    assert line is not None, line
    # baseline: 6*200+60=1260m work, 60m late, 7.0h sleep, every week
    # experiment week: 1260m work (unchanged), 0m late, 7.5h sleep
    assert line == ("  EXPERIMENT 'no work after 21:00': late-evening "
                    "-1.0h vs baseline; sleep +0.5h/night vs baseline; "
                    "output +0.0h vs baseline"), line

    # ---- silence: no EXPERIMENT line declared that week ----
    write_day_file(monday, "=== Monday 13.07.2026 ===\nSIGNAL: thesis\n")
    assert D._experiment_review_line(d, monday) is None

    # ---- silence: declared, but too little real baseline history ----
    write_day_file(monday, "EXPERIMENT: no work after 21:00\n")
    seed(ns, [r for r in rows if r[0] >= (monday - dt.timedelta(weeks=1)).isoformat()])
    assert D._experiment_review_line(d, monday) is None


def suite_pinned_searches():
    D, ns = fresh()
    add, remove = ns["_pinned_after_add"], ns["_pinned_after_remove"]

    # ---- adding: newest goes to the front ----
    pins = add([], "advisor")
    assert pins == ["advisor"], pins
    pins = add(pins, "landlord")
    assert pins == ["landlord", "advisor"], pins

    # ---- re-adding an existing pin re-surfaces it at the front,
    # doesn't duplicate ----
    pins = add(pins, "advisor")
    assert pins == ["advisor", "landlord"], pins

    # ---- capped at 5: the OLDEST drops, not the newest ----
    pins = ["e", "d", "c", "b", "a"]     # already full, "a" is oldest... no,
                                         # front = most-recent, so "a" (back)
                                         # is the LEAST recently used
    pins = add(pins, "f")
    assert pins == ["f", "e", "d", "c", "b"], pins   # "a" fell off the end

    # ---- blank query: a no-op, returns a copy unchanged ----
    same = add(["x", "y"], "   ")
    assert same == ["x", "y"], same

    # ---- removing ----
    after = remove(["x", "y", "z"], "y")
    assert after == ["x", "z"], after
    assert remove(["x"], "not-there") == ["x"]


def suite_decision_log():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])

    def write(day, text):
        with open(os.path.join(tmp, day + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(text)

    write("2026-07-01", "=== Wednesday 01.07.2026 ===\n"
                       "SIGNAL: thesis\n"
                       "DECIDED: apartment — staying another year\n"
                       "random note that mentions decided: in passing\n")
    write("2026-07-10", "=== Friday 10.07.2026 ===\n"
                       "DECIDED: advisor — switching to weekly check-ins\n")
    write("2026-07-05", "=== Monday 05.07.2026 ===\n"
                       "no decisions in this one\n")
    d = _mk(D, diary_dir=lambda: tmp)

    out = D._scan_decisions(d)
    # newest file first (filename sort, reverse=True), blank/false
    # positives excluded, only genuine header-line hits counted
    assert out == [
        ("2026-07-10", "advisor — switching to weekly check-ins"),
        ("2026-07-01", "apartment — staying another year"),
    ], out

    # ---- silence: no DECIDED: lines anywhere ----
    for fn in os.listdir(tmp):
        os.remove(os.path.join(tmp, fn))
    write("2026-07-01", "SIGNAL: thesis\n")
    assert D._scan_decisions(d) == []


def suite_annual_theme():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    TODAY = dt.date(2026, 7, 15)
    yday = TODAY - dt.timedelta(days=1)
    last_year = dt.date(2025, 7, 15)

    def write(day, text):
        with open(os.path.join(tmp, day.isoformat() + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(text)

    d = _mk(D, today=TODAY,
            diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"))

    # ---- _carry_year: carries yesterday's YEAR: line forward ----
    write(yday, "=== Tuesday 14.07.2026 ===\nSIGNAL: thesis\n"
               "YEAR: finish the thesis\n")
    assert D._carry_year(d) == "finish the thesis"

    # ---- _carry_year: no YEAR: line yesterday -> blank, no fallback ----
    write(yday, "=== Tuesday 14.07.2026 ===\nSIGNAL: thesis\n")
    assert D._carry_year(d) == ""

    # ---- _carry_year: no file at all yesterday -> blank ----
    os.remove(os.path.join(tmp, yday.isoformat() + ".txt"))
    assert D._carry_year(d) == ""

    # ---- _on_this_day_line: work + snippet + a YEAR: theme, all three ----
    seed(ns, [["2025-07-15", "work", "09:00", "10:30", "90", "thesis", ""]])
    write(last_year, "=== Tuesday 15.07.2025 ===\nYEAR: finish the thesis\n"
                    "SIGNAL: thesis\n"
                    "felt good about the outline today\n")
    line = D._on_this_day_line(d)
    assert line is not None, line
    assert line.startswith("on this day, 2025: 1h30m work — "), line
    assert "felt good about the outline today" in line, line
    assert ("that year's theme: 'finish the thesis' — still true?"
           in line), line

    # ---- _on_this_day_line: no YEAR: line last year -> no theme suffix ----
    write(last_year, "=== Tuesday 15.07.2025 ===\nSIGNAL: thesis\n"
                    "felt good about the outline today\n")
    line2 = D._on_this_day_line(d)
    assert line2 is not None and "theme" not in line2, line2

    # ---- silence: no file for last year at all ----
    os.remove(os.path.join(tmp, last_year.isoformat() + ".txt"))
    seed(ns, [])
    assert D._on_this_day_line(d) is None


def suite_lifetime_ledger():
    D, ns = fresh()
    TODAY = dt.date(2026, 7, 15)
    d = _mk(D, today=TODAY)
    kws = ["thesis"]

    # ---- no start_iso: falls back to the earliest matching row ----
    rows = [["2026-07-05", "work", "09:00", "10:00", "60", "thesis: ch1", ""],
            ["2026-07-08", "work", "09:00", "11:00", "120", "thesis: ch2", ""],
            ["2026-07-12", "work", "09:00", "12:00", "180", "thesis: ch3", ""],
            # excluded: a break row (even if it somehow matched) and a
            # work row on a genuinely different task
            ["2026-07-09", "break", "12:00", "12:30", "500", "", ""],
            ["2026-07-09", "work", "09:00", "10:00", "500", "email", ""]]
    seed(ns, rows)
    line = D._lifetime_ledger_line(d, "Thesis", kws)
    # total 60+120+180=360m=6h, 3 sessions, earliest 2026-07-05,
    # days=(2026-07-15 - 2026-07-05)=10, avg=(360/60)/10=0.6h/day
    assert line == ("Thesis: 6h across 3 session(s) since 2026-07-05 "
                    "(10 days — 0.6h/day lifetime average)"), line

    # ---- with start_iso: anchors "since" AND filters out earlier rows ----
    rows2 = [["2026-07-01", "work", "09:00", "10:00", "999", "thesis: old", ""],
             ["2026-07-12", "work", "09:00", "11:30", "150", "thesis: ch3", ""],
             ["2026-07-13", "work", "09:00", "10:40", "100", "thesis: ch4", ""]]
    seed(ns, rows2)
    line2 = D._lifetime_ledger_line(d, "Thesis", kws, "2026-07-10")
    # 2026-07-01 row excluded (before start_iso) despite matching;
    # total 150+100=250m -> floor 250//60=4h, 2 sessions,
    # since=start_iso (declared, not the earliest matched row),
    # days=(2026-07-15 - 2026-07-10)=5, avg=(250/60)/5=0.8333 -> "0.8"
    assert line2 == ("Thesis: 4h across 2 session(s) since 2026-07-10 "
                     "(5 days — 0.8h/day lifetime average)"), line2

    # ---- silence: no keywords ----
    assert D._lifetime_ledger_line(d, "Thesis", []) is None

    # ---- silence: keywords given but nothing ever matched ----
    assert D._lifetime_ledger_line(d, "Nope", ["xyznomatch"]) is None


def suite_deadline_postmortem():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    TODAY = dt.date(2026, 8, 1)      # well after the deadline below
    dl = {"name": "Thesis", "date": "2026-07-15", "total_h": 40,
         "match": "thesis", "start": "2026-06-01"}

    rows = []
    # phase 1: 06-04..06-24, 60 min/day (the as-of trailing window
    # _dl_velocity's math would have seen 21 days before the due date)
    d0 = dt.date(2026, 6, 4)
    while d0 <= dt.date(2026, 6, 24):
        rows.append([d0.isoformat(), "work", "09:00", "10:00", "60",
                     "thesis: writing", ""])
        d0 += dt.timedelta(days=1)
    # phase 2: 06-25..07-04, 120 min/day (scope crosses 40h on 07-04)
    d0 = dt.date(2026, 6, 25)
    while d0 <= dt.date(2026, 7, 4):
        rows.append([d0.isoformat(), "work", "09:00", "11:00", "120",
                     "thesis: writing", ""])
        d0 += dt.timedelta(days=1)
    seed(ns, rows)

    with open(os.path.join(tmp, "2026-07-05.txt"), "w",
              encoding="utf-8") as f:
        f.write("--- Done: thesis: ch1 (est 5h, actual 6h)\n"
               "--- Done: thesis: ch2 (est 4h, actual 5.2h)\n"
               "--- Done: thesis: ch3 (est 10h, actual 14h)\n")
    d = _mk(D, today=TODAY, diary_dir=lambda: tmp)

    lines = D._deadline_postmortem_lines(d, dl)
    assert lines is not None, lines
    assert lines[0] == "DEADLINE POST-MORTEM — Thesis (due 15.07.2026):", lines
    # 41h logged (60*21 + 120*10 minutes) / 40h declared = 102%
    assert "scope 40h declared, 41.0h actually logged (102%)" in lines[1], lines
    # ratios sorted [1.2, 1.3, 1.4] -> median 1.3 -> "ran long"
    assert any("estimate factor on this project: 1.30x (n=3) — ran long"
              in ln for ln in lines), lines
    # projection made 21d before due (2026-06-24) extrapolates the
    # 1.0h/day trailing pace seen by then to 2026-07-13; scope actually
    # crossed 40h on 2026-07-04 -> predicted ran 9 days pessimistic
    assert any("predicted 13.07, actually finished 04.07 — ran 9d "
              "pessimistic" in ln for ln in lines), lines
    # 31 active days out of 44 since 2026-06-01, avg 1.3h/active day
    assert any("pace kept: 1.3h on active days, active 70% of the 44 "
              "day(s) since 01.06.2026" in ln for ln in lines), lines

    # ---- silence: unscoped deadline (no total_h) ----
    dl2 = dict(dl)
    del dl2["total_h"]
    assert D._deadline_postmortem_lines(d, dl2) is None

    # ---- silence: due date hasn't passed yet ----
    d3 = _mk(D, today=dt.date(2026, 7, 1), diary_dir=lambda: tmp)
    assert D._deadline_postmortem_lines(d3, dl) is None

    # ---- _run_deadline_postmortems: write-once guard ----
    d4 = _mk(D, today=TODAY, diary_dir=lambda: tmp)
    ns["_ROWS_CACHE"].update(key=None, idx_key=None)
    settings = {"deadlines": [dict(dl)]}
    d4.settings = settings
    d4.deadlines = lambda: settings["deadlines"]
    out1 = D._run_deadline_postmortems(d4)
    assert out1 and out1[0].startswith("DEADLINE POST-MORTEM"), out1
    assert settings["deadlines"][0]["postmortem_written"] is True
    out2 = D._run_deadline_postmortems(d4)
    assert out2 == [], out2      # already marked -> never repeats


def suite_deadline_renegotiation():
    D, ns = fresh()
    revise = ns["_deadline_revisions_after_save"]

    # ---- first edit: history starts, carrying the OLD values ----
    old = [{"name": "Thesis", "date": "2026-07-15", "total_h": 20}]
    new = [{"name": "Thesis", "date": "2026-08-01", "total_h": 20}]
    out = revise(old, new, "2026-07-01")
    assert out[0]["history"] == [
        {"date": "2026-07-15", "total_h": 20, "as_of": "2026-07-01"}], out

    # ---- second edit: appends, doesn't overwrite the first entry ----
    out2 = revise(out, [{"name": "Thesis", "date": "2026-08-15",
                         "total_h": 30}], "2026-07-20")
    assert out2[0]["history"] == [
        {"date": "2026-07-15", "total_h": 20, "as_of": "2026-07-01"},
        {"date": "2026-08-01", "total_h": 20, "as_of": "2026-07-20"}], out2

    # ---- a no-op save (nothing actually changed): history carries
    # forward unchanged, no phantom third entry ----
    out3 = revise(out2, [{"name": "Thesis", "date": "2026-08-15",
                         "total_h": 30}], "2026-08-01")
    assert out3[0]["history"] == out2[0]["history"], out3

    # ---- a brand-new deadline (no matching name in the old list):
    # no history key at all ----
    out4 = revise(old, [{"name": "New thing", "date": "2026-09-01",
                        "total_h": 10}], "2026-07-01")
    assert "history" not in out4[0], out4

    D2, _ = fresh()
    d = _mk(D2)

    # ---- silence: fewer than 2 revisions ----
    dl1 = {"name": "Thesis", "date": "2026-08-15", "total_h": 30,
          "history": [{"date": "2026-07-15", "total_h": 20,
                       "as_of": "2026-07-01"}]}
    assert D2._deadline_renegotiation_line(d, dl1) is None

    # ---- speaks: both date and scope moved ----
    dl2 = {"name": "Thesis", "date": "2026-07-16", "total_h": 45,
          "history": [{"date": "2026-06-01", "total_h": 20,
                       "as_of": "2026-06-29"},
                      {"date": "2026-06-20", "total_h": 30,
                       "as_of": "2026-07-05"}]}
    line = D2._deadline_renegotiation_line(d, dl2)
    # date: 2026-06-01 -> 2026-07-16 = 45 days later (June has 30 days:
    # 30 to reach 07-01, +15 to reach 07-16); scope: first entry's 20h
    # -> current 45h
    assert line == ("this deadline has moved 2 time(s) since 2026-06-29 "
                    "— due date is now 45d later than first set, scope "
                    "grew from 20h to 45h"), line

    # ---- speaks: only scope moved, date unchanged ----
    dl3 = {"name": "Thesis", "date": "2026-06-01", "total_h": 45,
          "history": [{"date": "2026-06-01", "total_h": 20,
                       "as_of": "2026-06-29"},
                      {"date": "2026-06-01", "total_h": 30,
                       "as_of": "2026-07-05"}]}
    line3 = D2._deadline_renegotiation_line(d, dl3)
    assert line3 == ("this deadline has moved 2 time(s) since 2026-06-29 "
                     "— scope grew from 20h to 45h"), line3

    # ---- silence: malformed history entry ----
    dl4 = {"name": "Thesis", "date": "2026-06-01", "total_h": 45,
          "history": [{"total_h": 20, "as_of": "2026-06-29"},
                      {"date": "2026-06-01", "total_h": 30,
                       "as_of": "2026-07-05"}]}
    assert D2._deadline_renegotiation_line(d, dl4) is None


def suite_one_less():
    D, ns = fresh()
    pick = ns["_pick_one_less"]

    # ---- pure selection rule ----
    cands = [("a", "textA"), ("b", "textB")]
    assert pick(cands, None) == ("a", "textA")        # no history -> first
    assert pick(cands, "a") == ("b", "textB")          # avoid repeating "a"
    assert pick(cands, "b") == ("a", "textA")          # avoid repeating "b"
    assert pick([("a", "textA")], "a") == ("a", "textA")  # only option: repeats
    assert pick([], "x") is None

    # ---- composition: candidates wired in priority order, with framing ----
    d = _mk(D)
    d._meeting_fragmentation_lines = lambda: []
    d._procrastination_insight = lambda: []
    d._lag_evening_start_line = lambda: None
    assert D._one_less_candidates(d) == []
    d.settings = {}
    assert D._one_less_line(d) is None

    d._meeting_fragmentation_lines = lambda: ["Wed's meeting cost 1.3h",
                                              "week total 1.7h"]
    d._procrastination_insight = lambda: ["you bounce off 'admin' 80% of "
                                          "the time"]
    d._lag_evening_start_line = lambda: ("mornings after working past "
                                         "21:00 you start 1.2h later")
    assert D._one_less_candidates(d) == [
        ("meeting_fragmentation", "the meeting that fragments your day — "
                                  "Wed's meeting cost 1.3h"),
        ("procrastination", "the task you keep bouncing off — you bounce "
                            "off 'admin' 80% of the time"),
        ("late_evening", "the after-21:00 work — mornings after working "
                         "past 21:00 you start 1.2h later"),
    ], D._one_less_candidates(d)

    # ---- _one_less_line: picks the first candidate, remembers the key ----
    d.settings = {}
    line = D._one_less_line(d)
    assert line == ("  THIS WEEK, TRY ONE LESS: the meeting that fragments "
                    "your day — Wed's meeting cost 1.3h"), line
    assert d.settings["one_less_last_key"] == "meeting_fragmentation"

    # ---- rotates: same qualifying set, different candidate next time ----
    line2 = D._one_less_line(d)
    assert "the task you keep bouncing off" in line2, line2
    assert d.settings["one_less_last_key"] == "procrastination"

    # ---- only one candidate now qualifies: repeats, doesn't go silent ----
    d._meeting_fragmentation_lines = lambda: []
    d._lag_evening_start_line = lambda: None
    line3 = D._one_less_line(d)
    assert "the task you keep bouncing off" in line3, line3


def suite_sensor_health():
    D, ns = fresh()
    TODAY = dt.date(2026, 7, 15)
    tmp = os.path.dirname(ns["SESSIONS_CSV"])

    # ---- weekly baseline: 5 distinct Mondays, 300m (5h) each ----
    rows = []
    for w in range(1, 6):
        monday = dt.date(2026, 7, 13) - dt.timedelta(weeks=w)
        rows.append([monday.isoformat(), "work", "09:00", "14:00", "300",
                    "x", ""])
    seed(ns, rows)

    # ---- sleep: 15 consecutive days, all well outside the 30-day
    # coverage window (last seen 30 days ago) -> 0% coverage, alarm ----
    hd = {(dt.date(2026, 6, 1) + dt.timedelta(days=i)).isoformat():
          {"sleep_h": 7.0} for i in range(15)}

    # ---- calendar: file exists but hasn't been touched in 20 days ----
    ics_path = os.path.join(tmp, "cal.ics")
    open(ics_path, "w").close()
    old_ts = dt.datetime.combine(
        TODAY - dt.timedelta(days=20), dt.time()).timestamp()
    os.utime(ics_path, (old_ts, old_ts))

    # ---- ENERGY: only one day logged in the last 30, 6 days ago ----
    energy_days = {"2026-07-09"}

    d = _mk(D, today=TODAY, settings={"ics_path": ics_path},
            _health_data=lambda: hd,
            _day_energy=lambda day: 3 if day.isoformat() in energy_days
                                    else None)
    lines = D._sensor_health_lines(d)
    assert lines[0] == "SENSOR HEALTH:", lines
    assert ("  sleep import: last seen 2026-06-15 (30d ago), 0% coverage "
           "— the phone automation may have stopped" in lines), lines
    assert ("  calendar: export file last updated 20d ago — may have "
           "gone stale" in lines), lines
    assert ("  ENERGY: last typed 2026-07-09 (6d ago), 3% coverage — "
           "you've stopped logging it" in lines), lines
    assert "  your normal sleep: 7.0h (median, n=15)" in lines, lines
    assert ("  your normal week: 5.0h tracked (median, n=5 weeks)"
           in lines), lines

    # ---- healthy path: no alarms fire when everything's recent ----
    hd2 = {(TODAY - dt.timedelta(days=i)).isoformat(): {"sleep_h": 7.0}
          for i in range(15)}
    d2 = _mk(D, today=TODAY, settings={"ics_path": ics_path},
             _health_data=lambda: hd2,
             _day_energy=lambda day: 3 if day == TODAY else None)
    fresh_ts = dt.datetime.combine(TODAY, dt.time()).timestamp()
    os.utime(ics_path, (fresh_ts, fresh_ts))     # updated "today"
    lines2 = D._sensor_health_lines(d2)
    assert not any("may have stopped" in ln or "gone stale" in ln
                  or "stopped logging" in ln for ln in lines2), lines2

    # ---- silence-ish: nothing configured/typed/imported at all ----
    d3 = _mk(D, today=TODAY, settings={}, _health_data=lambda: {},
             _day_energy=lambda day: None)
    seed(ns, [])
    lines3 = D._sensor_health_lines(d3)
    assert "  sleep import: no data seen yet" in lines3, lines3
    assert "  calendar: not configured" in lines3, lines3
    assert "  ENERGY: never typed" in lines3, lines3
    assert not any("your normal" in ln for ln in lines3), lines3


def suite_planner_realism():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    TODAY = dt.date(2026, 7, 15)

    def write(day, body):
        with open(os.path.join(tmp, day + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(body)

    d = _mk(D, today=TODAY,
            diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"))

    # ---- _planned_hours_from_file: sums placement lines, excludes
    # the "uncommitted" free-time line ----
    write("2026-07-14",
         "suggested schedule today:\n"
         "  09:00-11:00 Thesis (2.0h)\n"
         "  14:00-17:00 uncommitted (3.0h free today total)\n")
    assert D._planned_hours_from_file(d, "2026-07-14") == 2.0

    # ---- silence: no schedule block in the file at all ----
    write("2026-07-13", "SIGNAL: thesis\njust a normal day\n")
    assert D._planned_hours_from_file(d, "2026-07-13") is None

    # ---- silence: no file for that date ----
    assert D._planned_hours_from_file(d, "2026-01-01") is None

    # ---- _planner_realism_factor: 6 days, hand-verified median ----
    # (planned, actual) -> ratio, capped at 1.0 for overshoot
    days = [
        ("2026-07-14", 2.0, 1.0),   # 0.5
        ("2026-07-13", 4.0, 4.0),   # 1.0
        ("2026-07-12", 2.0, 3.0),   # 1.5 -> capped 1.0
        ("2026-07-11", 5.0, 2.5),   # 0.5
        ("2026-07-10", 3.0, 1.8),   # 0.6
        ("2026-07-09", 1.0, 0.9),   # 0.9
    ]
    rows = []
    for iso, planned, actual in days:
        n = 1
        lines = ["suggested schedule today:"]
        rem = planned
        while rem > 1e-9:
            chunk = min(rem, 2.0)
            lines.append(f"  09:00-11:00 task{n} ({chunk:.1f}h)")
            rem -= chunk
            n += 1
        write(iso, "\n".join(lines) + "\n")
        rows.append([iso, "work", "09:00", "10:00", str(round(actual * 60)),
                    "x", ""])
    seed(ns, rows)
    factor = D._planner_realism_factor(d, 60)
    assert factor is not None, factor
    ratio, n = factor
    # sorted ratios: [0.5, 0.5, 0.6, 0.9, 1.0, 1.0] -> median (index 3) = 0.9
    assert n == 6 and abs(ratio - 0.9) < 1e-9, factor

    # ---- silence: fewer than 5 days with a real written schedule ----
    d2 = _mk(D, today=TODAY,
            diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"))
    seed(ns, rows[:4])
    for iso, *_r in days[4:]:
        write(iso, "SIGNAL: thesis\n")   # no schedule block these two days
    assert D._planner_realism_factor(d2, 60) is None


def suite_time_capsule():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    TODAY = dt.date(2026, 8, 15)

    def write(day, body):
        with open(os.path.join(tmp, day + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(body)

    # written 45 days before today, due today
    write("2026-07-01", "=== Wednesday 01.07.2026 ===\nSIGNAL: thesis\n"
                       "CAPSULE: 2026-08-15 | message A\n")
    # a second capsule due today from a different day
    write("2026-08-01", "CAPSULE: 2026-08-15 | message B\n")
    # due on a DIFFERENT date -> excluded
    write("2026-07-10", "CAPSULE: 2026-09-01 | message C\n")
    # malformed (no pipe) -> regex never matches, safely ignored
    write("2026-07-15", "CAPSULE: 2026-08-15 no pipe here\n")
    d = _mk(D, today=TODAY, diary_dir=lambda: tmp)

    caps = D._due_capsules(d)
    assert caps == [("2026-07-01", "message A"),
                    ("2026-08-01", "message B")], caps

    lines = D._capsule_lines(d)
    assert lines == ["a note from 45 days ago: message A",
                     "a note from 14 days ago: message B"], lines

    # ---- silence: nothing due today ----
    for fn in os.listdir(tmp):
        os.remove(os.path.join(tmp, fn))
    write("2026-07-10", "CAPSULE: 2026-09-01 | message C\n")
    assert D._due_capsules(d) == []
    assert D._capsule_lines(d) == []

    # ---- a capsule can't reference itself: written today, due today
    # is excluded (today's own file isn't "the past" yet) ----
    write("2026-08-15", "CAPSULE: 2026-08-15 | same-day\n")
    assert D._due_capsules(d) == []


def suite_commitment_reliability():
    D, ns = fresh()
    tmp = os.path.dirname(ns["SESSIONS_CSV"])
    TODAY = dt.date(2026, 8, 15)
    d = _mk(D, today=TODAY,
            diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"))

    # ---- _commit_from_text: parsing ----
    assert D._commit_from_text(d, "COMMIT: thesis 4h\n") == ("thesis", 4.0)
    assert D._commit_from_text(d, "COMMIT: 4h\n") == ("", 4.0)
    assert D._commit_from_text(d, "COMMIT: thesis, writing 2.5h\n") == (
        "thesis, writing", 2.5)
    assert D._commit_from_text(d, "SIGNAL: thesis\nno commit here\n") is None
    assert D._commit_from_text(d, "COMMIT: not a number\n") is None

    # ---- _commitment_reliability: 5 real commitments, 3 hits ----
    def write(day, body):
        with open(os.path.join(tmp, day + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(body)

    write("2026-08-14", "COMMIT: thesis 4h\n")     # 5h delivered -> hit
    write("2026-08-13", "COMMIT: thesis 4h\n")     # 2h delivered -> miss
    write("2026-08-12", "COMMIT: 3h\n")             # 3h total -> hit (exact)
    write("2026-08-11", "COMMIT: 3h\n")             # 1h total -> miss
    write("2026-08-10", "COMMIT: admin 1h\n")       # 1h admin -> hit
    write("2026-08-09", "SIGNAL: thesis\n")          # no COMMIT -> not counted
    seed(ns, [
        ["2026-08-14", "work", "09:00", "14:00", "300", "thesis: ch1", ""],
        ["2026-08-13", "work", "09:00", "11:00", "120", "thesis: ch2", ""],
        ["2026-08-12", "work", "09:00", "12:00", "180", "admin", ""],
        ["2026-08-11", "work", "09:00", "10:00", "60", "admin", ""],
        ["2026-08-10", "work", "09:00", "10:00", "60", "admin task", ""],
        ["2026-08-09", "work", "09:00", "17:00", "999", "x", ""],
    ])
    stat = D._commitment_reliability(d, 30)
    assert stat is not None, stat
    rate, hits, n = stat
    assert (hits, n) == (3, 5) and abs(rate - 0.6) < 1e-9, stat

    line = D._commitment_reliability_line(d, 30)
    assert line == ("  you hit your morning commitment 3 of the last 5 "
                    "day(s) — you reliably deliver ~60% of what you "
                    "promise yourself; promise that and mean it"), line

    # ---- silence: fewer than 5 real commitments ----
    write("2026-08-09", "SIGNAL: thesis\n")   # keep it COMMIT-less
    write("2026-08-10", "SIGNAL: thesis\n")   # remove one more commitment
    assert D._commitment_reliability(d, 30) is None
    assert D._commitment_reliability_line(d, 30) is None


def suite_protected_windows():
    D, ns = fresh()
    d = _mk(D, settings={"protected_windows": [
        {"label": "lunch", "start": "12:00", "end": "13:00"},
        {"label": "wind-down", "start": "21:00", "end": "22:00"},
        {"label": "bad range", "start": "15:00", "end": "14:00"},   # s >= e
        {"label": "bad format", "start": "not-a-time", "end": "13:00"},
        {"label": "", "start": "10:00", "end": "11:00"},   # off (empty label
                                                            # doesn't matter to
                                                            # the parser itself,
                                                            # only the UI skips
                                                            # it on save — this
                                                            # still parses fine)
    ]})
    out = D._protected_intervals(d)
    assert out == [(time(12, 0), time(13, 0)), (time(21, 0), time(22, 0)),
                   (time(10, 0), time(11, 0))], out

    # ---- silence: nothing configured ----
    d2 = _mk(D, settings={})
    assert D._protected_intervals(d2) == []

    # ---- a missing key is skipped, not a crash ----
    d3 = _mk(D, settings={"protected_windows": [{"label": "half"}]})
    assert D._protected_intervals(d3) == []


def suite_milestones():
    D, ns = fresh()

    # ---- _parse_milestones: parsing ----
    ms = ns["_parse_milestones"]("ch4 [15h]*, ch5 [20h], revisions [10h]")
    assert ms == [
        {"name": "ch4", "h": 15.0, "done": True},
        {"name": "ch5", "h": 20.0, "done": False},
        {"name": "revisions", "h": 10.0, "done": False},
    ], ms
    assert ns["_parse_milestones"]("") == []
    assert ns["_parse_milestones"]("just text, no brackets") == []

    # ---- _milestone_progress_line: hours accrue in milestone order ----
    TODAY = dt.date(2026, 8, 15)
    dl = {"name": "Thesis", "match": "thesis", "start": "2026-01-01",
         "milestones": "ch4 [15h]*, ch5 [20h], revisions [10h]"}
    # 27h matched total: 15h already covers the DONE ch4, leaving 12h
    # credited to ch5 (the first not-done milestone) -> 12/20 = 60%;
    # revisions gets no credit yet (35h would be needed to reach it)
    seed(ns, [["2026-03-01", "work", "09:00", "18:00", "1620",
              "thesis: writing", ""]])
    d = _mk(D, today=TODAY)
    line = D._milestone_progress_line(d, dl)
    assert line == ("  milestones: ch4 done, ch5 at 60% of its hours, "
                    "revisions at 0% of its hours"), line

    # ---- silence: no milestones field ----
    assert D._milestone_progress_line(d, {"name": "X", "match": "x"}) is None
    assert D._milestone_progress_line(
        d, {"name": "X", "match": "x", "milestones": ""}) is None


def suite_waiting_on():
    D, ns = fresh()

    d = _mk(D, settings={"tasks": [
        {"name": "ch4 draft", "blocked_by": "advisor reply"},
        {"name": "email sweep"},
        {"name": "ch5 draft", "blocked_by": "landlord response"},
    ]})
    out = D._waiting_on_lines(d)
    assert out == [
        "WAITING ON:",
        "  ch4 draft — blocked by: advisor reply",
        "  ch5 draft — blocked by: landlord response",
    ], out

    # ---- silence: nothing blocked ----
    d2 = _mk(D, settings={"tasks": [{"name": "email sweep"}]})
    assert D._waiting_on_lines(d2) == []

    # ---- silence: no tasks at all ----
    d3 = _mk(D, settings={})
    assert D._waiting_on_lines(d3) == []


def suite_cost_of_yes():
    D, ns = fresh()
    TODAY = dt.date(2026, 8, 1)

    # ---- no existing deadlines: plain before/after, no "give up" clause ----
    d = _mk(D, today=TODAY, _avail_hours=lambda until: 15.0)
    line = D._cost_of_yes_line(d, {"name": "NewProj", "date": "2026-08-20",
                                   "total_h": 10}, [])
    assert line == ("committing to 'NewProj' would push slack from "
                    "+15.0h to +5.0h"), line

    # ---- an existing deadline gets named as the one to give ground ----
    def fake_progress(dl):
        return {"left": 10, "total_h": 20, "remaining_h": 20,
               "due": dt.date(2026, 8, 20)}
    d2 = _mk(D, today=TODAY, _avail_hours=lambda until: 25.0,
             _dl_progress=fake_progress)
    existing = [{"name": "Thesis", "date": "2026-08-20", "total_h": 20}]
    line2 = D._cost_of_yes_line(
        d2, {"name": "NewProj", "date": "2026-08-15", "total_h": 15}, existing)
    # avail=25 (stubbed), req_before=20 -> slack_before=+5; req_after=35 ->
    # slack_after=-10; Thesis (only item) gives up min(20,10)=10h over its
    # own 10 days left -> 1.0h/day
    assert line2 == ("committing to 'NewProj' would push slack from "
                     "+5.0h to -10.0h — Thesis would need to give up "
                     "1.0h/day to make room"), line2

    # ---- silence: no scope (total_h missing/zero) ----
    d3 = _mk(D, today=TODAY, _avail_hours=lambda until: 15.0)
    assert D._cost_of_yes_line(
        d3, {"name": "X", "date": "2026-08-20", "total_h": 0}, []) is None
    assert D._cost_of_yes_line(
        d3, {"name": "X", "date": "2026-08-20"}, []) is None

    # ---- silence: due date already in the past ----
    assert D._cost_of_yes_line(
        d3, {"name": "X", "date": "2026-07-01", "total_h": 5}, []) is None

    # ---- silence: unparseable date ----
    assert D._cost_of_yes_line(
        d3, {"name": "X", "date": "not-a-date", "total_h": 5}, []) is None


def suite_status_update():
    D, ns = fresh()
    TODAY = dt.date(2026, 7, 15)      # Wednesday, week-of-Monday 07-13
    dl = {"name": "Thesis", "match": "thesis", "date": "2026-08-01",
         "total_h": 40}

    rows = []
    for iso, m in [("2026-07-07", 120), ("2026-07-08", 120),
                  ("2026-07-09", 120), ("2026-07-10", 120)]:   # 8h last week
        rows.append([iso, "work", "09:00", "11:00", str(m),
                    "thesis: writing", ""])
    for iso, m in [("2026-07-13", 240), ("2026-07-14", 240),
                  ("2026-07-15", 240)]:                        # 12h this week
        rows.append([iso, "work", "09:00", "13:00", str(m),
                    "thesis: writing", ""])
    seed(ns, rows)

    # ---- behind pace, no blockers ----
    d = _mk(D, today=TODAY, settings={},
            _dl_progress=lambda dl: {"total_h": 40, "due": dt.date(2026, 8, 1)},
            _dl_projection=lambda dl: {"delta": 3, "land": dt.date(2026, 8, 4)})
    text = D._status_update_text(d, dl)
    assert text == ("Progress update — Thesis: 12h this week (up from 8h "
                    "last). Currently projected 3d behind pace, landing "
                    "August 04. No blockers."), text

    # ---- on pace, with a blocker linked via v8.60's blocked_by ----
    d2 = _mk(D, today=TODAY, settings={"tasks": [
                {"name": "ch5 draft", "deadline": "Thesis",
                 "blocked_by": "advisor reply"},
                {"name": "unrelated", "deadline": "Other"}]},
            _dl_progress=lambda dl: {"total_h": 40, "due": dt.date(2026, 8, 1)},
            _dl_projection=lambda dl: {"delta": 0, "land": dt.date(2026, 8, 1)})
    text2 = D._status_update_text(d2, dl)
    assert text2 == ("Progress update — Thesis: 12h this week (up from 8h "
                     "last). On pace to finish by August 01. Blocked on: "
                     "ch5 draft."), text2

    # ---- silence: unscoped deadline (no total_h) ----
    d3 = _mk(D, today=TODAY, settings={}, _dl_progress=lambda dl: {})
    assert D._status_update_text(d3, {"name": "X"}) is None

    # ---- _status_update_all: joins scoped deadlines, skips unscoped ----
    d4 = _mk(D, today=TODAY, settings={"tasks": [
                {"name": "ch5 draft", "deadline": "Thesis",
                 "blocked_by": "advisor reply"}]},
            deadlines=lambda: [
                {"name": "Thesis", "match": "thesis", "date": "2026-08-01",
                 "total_h": 40},
                {"name": "Unscoped", "match": "x", "date": "2026-09-01"}],
            _dl_progress=lambda dl: ({"total_h": 40, "due": dt.date(2026, 8, 1)}
                                     if dl["name"] == "Thesis" else {}),
            _dl_projection=lambda dl: {"delta": 0, "land": dt.date(2026, 8, 1)})
    combined = D._status_update_all(d4)
    assert combined == text2, combined     # only Thesis, Unscoped skipped
    assert combined.count("Progress update") == 1, combined


SUITES = [("projection", suite_projection), ("trajectory", suite_trajectory),
          ("outlook", suite_outlook), ("alignment", suite_alignment),
          ("review", suite_review), ("anomaly", suite_anomaly),
          ("recommend-now", suite_recommend_now),
          ("energy-place", suite_energy_place),
          ("last-context", suite_last_context),
          ("break-pull", suite_break_pull),
          ("reentry", suite_reentry),
          ("procrastination", suite_procrastination),
          ("metrics", suite_metrics),
          ("health-parse", suite_health_parse),
          ("daylight", suite_daylight),
          ("word-drift", suite_word_drift),
          ("ask-diary", suite_ask_diary),
          ("lag", suite_lag),
          ("week-ahead", suite_week_ahead),
          ("break-budget", suite_break_budget),
          ("lens-overlap", suite_lens_overlap),
          ("health-extras", suite_health_extras),
          ("backup-integrity", suite_backup_integrity),
          ("running-hot", suite_running_hot),
          ("meeting-fragmentation", suite_meeting_fragmentation),
          ("year-rhythm", suite_year_rhythm),
          ("energy-forecast", suite_energy_forecast),
          ("experiment-engine", suite_experiment_engine),
          ("pinned-searches", suite_pinned_searches),
          ("decision-log", suite_decision_log),
          ("annual-theme", suite_annual_theme),
          ("lifetime-ledger", suite_lifetime_ledger),
          ("deadline-postmortem", suite_deadline_postmortem),
          ("deadline-renegotiation", suite_deadline_renegotiation),
          ("one-less", suite_one_less),
          ("sensor-health", suite_sensor_health),
          ("planner-realism", suite_planner_realism),
          ("time-capsule", suite_time_capsule),
          ("commitment-reliability", suite_commitment_reliability),
          ("protected-windows", suite_protected_windows),
          ("milestones", suite_milestones),
          ("waiting-on", suite_waiting_on),
          ("cost-of-yes", suite_cost_of_yes),
          ("status-update", suite_status_update)]


def main():
    import py_compile
    py_compile.compile(SRC, doraise=True)
    failed = 0
    for name, fn in SUITES:
        try:
            fn()
            print(f"  {name:<14} OK")
        except Exception as e:                        # noqa: BLE001
            failed += 1
            print(f"  {name:<14} FAIL — {e.__class__.__name__}: {e}")
    print(f"{len(SUITES) - failed}/{len(SUITES)} suites green")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
