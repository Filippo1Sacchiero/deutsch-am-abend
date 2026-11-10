"""Prepare the data rows for the "Deutsch am Abend" Google Sheet.

Usage: python3 sheets.py DUMP_DIR TODAY PLAN.json OUT.json
Imports compute() from report.py (same folder) and writes OUT.json:
{"ranges": {"'Pro Tag'!A2": [[...]], ...}, "clear": [...], "counts": {...}}
Only raw data is written; every derived number in the Sheet is a formula.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report import compute, TYPE  # noqa: E402


def txt(v):
    """Keep text as text when Sheets would parse it as a number, date or formula."""
    if v is None:
        return ""
    if isinstance(v, (int, float, bool)):
        return v
    s = str(v)
    if s and (s[0] in "=+-@'" or s.replace(".", "", 1).replace(",", "", 1).isdigit()):
        return "'" + s
    return s


def main(dump, today, plan_path, out):
    c = compute(dump, today)
    S = c["summary"]
    plan = {}
    if plan_path and os.path.exists(plan_path):
        with open(plan_path, encoding="utf-8") as fh:
            plan = json.load(fh) or {}

    # Pro Tag: Datum | Richtig | Falsch | Erledigt   (E = Fehlerquote, formula in the sheet)
    days = []
    for d in sorted(c["progress"]):
        p = c["progress"][d]
        r = w = 0
        for a in (p.get("answers") or {}).values():
            if not a or a.get("flagged") or a.get("correct") is None:
                continue
            if a["correct"]:
                r += 1
            else:
                w += 1
        if r + w:
            days.append([d, r, w, "ja" if p.get("done") else "nein"])

    # Wörter: A..M
    words = []
    for k, w in sorted(c["words"].items(), key=lambda kv: (kv[1].get("firstDate") or "", kv[1].get("de") or "")):
        s = c["per_word"].get(k, {"right": 0, "wrong": 0})
        words.append([
            txt(w.get("de")), txt(w.get("article")), txt(w.get("plural")), txt(w.get("forms")),
            TYPE.get(w.get("type"), ""), txt(w.get("sector")), txt(w.get("meaning") or w.get("definition")),
            txt(w.get("es") or w.get("spanish")), txt(w.get("example")),
            w.get("firstDate") or "", s["right"], s["wrong"], c["status"](k),
        ])

    # Lektionen: Datum | Bereich | Thema | Grammatik | Aufgaben | Richtig | Falsch | Erledigt  (I = formula)
    lessons = []
    for d in sorted(c["lessons"]):
        L = c["lessons"][d]
        p = c["progress"].get(d) or {}
        sc = p.get("score") or {}
        lessons.append([d, txt(L.get("sector")), txt(L.get("theme")), txt((L.get("grammar") or {}).get("topic")),
                        len(L.get("exercises", [])), sc.get("right", 0), sc.get("wrong", 0),
                        "ja" if p.get("done") else "nein"])

    # Wochenplan: fixed rows, column B holds the values
    weak = [f'{a.get("area", "")}: {a.get("detail", "")}' for a in (plan.get("weakAreas") or [])][:5]
    strong = [str(x) for x in (plan.get("strengths") or [])][:5]
    wp = [
        ["Stand", today],
        ["Woche ab", plan.get("weekOf") or ""],
        ["Schwierigkeit", txt(plan.get("difficulty") or "")],
        ["Serie (Tage)", S["streak_days"]],
        ["Zusammenfassung", txt(plan.get("summary") or "Noch kein Plan vorhanden.")],
        ["Grammatik im Fokus", txt(", ".join(plan.get("focusTopics") or []))],
        ["", ""],
    ]
    for i in range(5):
        wp.append([f"Schwachpunkt {i + 1}", txt(weak[i]) if i < len(weak) else ""])
    for i in range(5):
        wp.append([f"Stärke {i + 1}", txt(strong[i]) if i < len(strong) else ""])

    res = {
        "ranges": {
            "'Pro Tag'!A2": days,
            "'Wörter'!A2": words,
            "'Lektionen'!A2": lessons,
            "'Wochenplan'!A1": wp,
        },
        # rows below the new data, cleared after writing (in case a table got shorter)
        "clear": [
            f"'Pro Tag'!A{len(days) + 2}:D",
            f"'Wörter'!A{len(words) + 2}:M",
            f"'Lektionen'!A{len(lessons) + 2}:H",
        ],
        "counts": {"days": len(days), "words": len(words), "lessons": len(lessons),
                   "words_learned": S["words_learned"], "streak": S["streak_days"]},
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False)
    print(json.dumps(res["counts"]))


if __name__ == "__main__":
    main(*sys.argv[1:5])
