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
       "parse_health_dir", "_parse_any_date", "_dur_minutes", "_num"}
METH = {"_dl_progress", "_dl_velocity", "_dl_projection", "_projection_line",
        "_match_kws", "_trajectory_lines", "_outlook_lines",
        "_alignment_lines", "_domain_minutes", "_review_bottom_line",
        "_life_review_lines", "_anomaly_lines", "_copilot_note",
        "_recommend_now", "_deep_window", "_hour_quality", "_energy_place",
        "_last_context", "_break_insight", "_pull_level", "_reentry_opener",
        "_procrastination_insight", "_metrics_from_text", "_day_metrics",
        "_metrics_insight"}
STATIC = {"_match_kws", "_pull_level"}  # extraction drops @staticmethod
CLASS_ATTRS = {"_BREAK_MOVE", "_BREAK_SCROLL", "METRICS_RE"}

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
          ("health-parse", suite_health_parse)]


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
