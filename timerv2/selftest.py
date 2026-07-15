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
       "day_length_hours"}
METH = {"_dl_progress", "_dl_velocity", "_dl_projection", "_projection_line",
        "_match_kws", "_trajectory_lines", "_outlook_lines",
        "_alignment_lines", "_domain_minutes", "_review_bottom_line",
        "_life_review_lines", "_anomaly_lines", "_copilot_note",
        "_recommend_now", "_deep_window", "_hour_quality", "_energy_place",
        "_last_context", "_break_insight", "_pull_level", "_reentry_opener",
        "_procrastination_insight", "_metrics_from_text", "_day_metrics",
        "_metrics_insight", "_daylight_h", "_daylight_insight",
        "_diary_word_counts", "_word_drift_insight",
        "_diary_rank_days", "_matching_days_text",
        "_lag_workout_line", "_lag_sleep_debt_line", "_day_start_late_map",
        "_lag_evening_start_line", "_lag_insight", "_week_ahead_lines",
        "_break_budget_line"}
STATIC = {"_match_kws", "_pull_level"}  # extraction drops @staticmethod
CLASS_ATTRS = {"_BREAK_MOVE", "_BREAK_SCROLL", "METRICS_RE",
               "METRICS_BARE_RE", "_LINE_TAG_RULES", "_WORD_RE",
               "_WORD_STOPWORDS"}

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
          "SESSIONS_CSV": os.path.join(tmp, "sessions.csv"),
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
            _day_signal=lambda day, *a, **k: (5, 60))
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
            f.write(filler + "\n")
    for rd in recent_days:
        with open(os.path.join(tmp, rd.isoformat() + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(filler + " apartment moving apartment search\n")
    out = D._word_drift_insight(d)
    assert out and "'apartment'" in out[0], out
    assert "(0→20 mentions, last 30d vs prior 90d)" in out[0], out

    # ---- silence gate: too little total volume either side ----
    d2 = _mk(D, today=dt.date(2099, 1, 1),
             diary_path=lambda dd: os.path.join(tmp, dd.isoformat() + ".txt"))
    assert D._word_drift_insight(d2) == []


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

    # ---- composition: all three fire, in order, none crash on missing data ----
    seed(ns, rows2)
    out = D._lag_insight(d, 90)
    assert len(out) >= 1 and any("10:00" in x for x in out), out

    # ---- silence: too few pairs on one side ----
    seed(ns, [row("2026-06-01", 60, "x")])
    d2 = _mk(D, today=dt.date(2026, 6, 2))
    d2._health_data = lambda: {}
    d2._sleep_h = lambda iso: None
    assert D._lag_workout_line(d2, 90) is None
    assert D._lag_sleep_debt_line(d2, 90) is None
    assert D._lag_evening_start_line(d2, 90) is None
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
          ("break-budget", suite_break_budget)]


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
