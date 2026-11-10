#!/usr/bin/env python3
"""Deutsch am Abend - weekly stats + Excel dashboard.
Usage:
  python3 report.py stats DUMP_DIR TODAY            -> prints JSON stats
  python3 report.py excel DUMP_DIR TODAY PLAN.json OUT.xlsx
DUMP_DIR holds lessons/, progress/, words/ with one JSON file per document.
"""
import json, os, sys, datetime as dt
from collections import defaultdict

TYPE = {"verb": "Verb", "noun": "Nomen", "adj": "Adjektiv"}
SECTORS = ["Alltag", "IT & Technik", "Business & Büro"]


def load(d, coll):
    out = {}
    p = os.path.join(d, coll)
    if os.path.isdir(p):
        for f in sorted(os.listdir(p)):
            if f.endswith(".json"):
                with open(os.path.join(p, f), encoding="utf-8") as fh:
                    out[f[:-5]] = json.load(fh)
    return out


def compute(dump, today):
    lessons = {v.get("date", k): v for k, v in load(dump, "lessons").items()}
    progress = {v.get("date", k): v for k, v in load(dump, "progress").items()}
    words = {v.get("key", k): v for k, v in load(dump, "words").items()}
    per_word, days = {}, []
    by_skill = defaultdict(lambda: [0, 0])
    by_topic = defaultdict(lambda: [0, 0])
    by_sector = defaultdict(lambda: [0, 0])
    for date in sorted(progress):
        p = progress[date]
        L = lessons.get(date, {})
        exs = {e.get("id"): e for e in L.get("exercises", [])}
        topic = (L.get("grammar") or {}).get("topic", "")
        r = w = 0
        for eid, a in (p.get("answers") or {}).items():
            if not a or a.get("flagged") or a.get("correct") is None:
                continue
            ok = bool(a["correct"])
            r += ok; w += (not ok)
            skill = a.get("skill") or (exs.get(eid) or {}).get("skill") or "?"
            by_skill[skill][0 if ok else 1] += 1
            if skill == "grammatik" and topic:
                by_topic[topic][0 if ok else 1] += 1
            if L.get("sector"):
                by_sector[L["sector"]][0 if ok else 1] += 1
            k = a.get("wordKey")
            if k:
                s = per_word.setdefault(k, {"right": 0, "wrong": 0, "last": None, "lastDate": ""})
                s["right" if ok else "wrong"] += 1
                if date >= s["lastDate"]:
                    s["last"], s["lastDate"] = ok, date
        if r + w:
            days.append({"date": date, "right": r, "wrong": w, "rate": round(w / (r + w), 3), "done": bool(p.get("done"))})

    def status(k):
        s = per_word.get(k)
        if not s:
            return "Neu"
        return "Gelernt" if s["last"] and s["right"] > s["wrong"] else "Übt noch"

    t = dt.date.fromisoformat(today)
    since7 = (t - dt.timedelta(days=6)).isoformat()
    r7 = sum(d["right"] for d in days if d["date"] >= since7)
    w7 = sum(d["wrong"] for d in days if d["date"] >= since7)
    rall = sum(d["right"] for d in days); wall = sum(d["wrong"] for d in days)
    streak, cur = 0, t
    if not (progress.get(cur.isoformat()) or {}).get("done"):
        cur -= dt.timedelta(days=1)
    while (progress.get(cur.isoformat()) or {}).get("done"):
        streak += 1; cur -= dt.timedelta(days=1)
    lessons7 = [d for d in sorted(lessons) if d >= since7]
    done7 = [d for d in lessons7 if (progress.get(d) or {}).get("done")]

    def group(field, keys, label):
        rows = []
        for k in keys:
            ks = [w_["key"] if "key" in w_ else kk for kk, w_ in words.items() if w_.get(field) == k]
            rows.append({"label": label(k), "seen": len(ks), "learned": sum(status(x) == "Gelernt" for x in ks)})
        return rows

    def rate(pair):
        return round(pair[1] / sum(pair), 3) if sum(pair) else None

    hard = sorted([(k, s) for k, s in per_word.items() if s["wrong"] and k in words],
                  key=lambda x: (-(x[1]["wrong"] - x[1]["right"]), -x[1]["wrong"]))[:10]
    return {
        "today": today,
        "lessons": lessons, "progress": progress, "words": words, "per_word": per_word, "status": status,
        "summary": {
            "words_seen": len(words),
            "words_learned": sum(status(k) == "Gelernt" for k in words),
            "error_rate_7d": round(w7 / (r7 + w7), 3) if r7 + w7 else None,
            "error_rate_all": round(wall / (rall + wall), 3) if rall + wall else None,
            "answers_7d": r7 + w7,
            "lessons_last_7d": len(lessons7), "lessons_done_last_7d": len(done7),
            "lessons_done_total": sum(1 for p in progress.values() if p.get("done")),
            "streak_days": streak,
            "error_rate_by_skill": {k: rate(v) for k, v in by_skill.items()},
            "answers_by_skill": {k: sum(v) for k, v in by_skill.items()},
            "error_rate_by_grammar_topic": {k: rate(v) for k, v in by_topic.items()},
            "error_rate_by_sector": {k: rate(v) for k, v in by_sector.items()},
            "words_by_type": group("type", ["verb", "noun", "adj"], lambda k: TYPE[k]),
            "words_by_sector": group("sector", SECTORS, lambda k: k),
            "hardest_words": [{"key": k, "de": words[k].get("de"), "type": words[k].get("type"),
                               "right": s["right"], "wrong": s["wrong"], "last_correct": s["last"]} for k, s in hard],
            "days": days[-30:],
        },
    }


def stats_cmd(dump, today):
    c = compute(dump, today)
    print(json.dumps(c["summary"], ensure_ascii=False, indent=1))


def excel_cmd(dump, today, plan_path, out):
    from openpyxl import Workbook
    from openpyxl.chart import LineChart, BarChart, Reference
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    c = compute(dump, today)
    S = c["summary"]
    plan = {}
    if plan_path and os.path.exists(plan_path):
        with open(plan_path, encoding="utf-8") as fh:
            plan = json.load(fh)
    INK, MARK, SOFT = "191C20", "F1C232", "E8EAE4"
    H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor=INK)
    wb = Workbook()

    def table(ws, headers, rows, start_row=1):
        for j, h in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=j, value=h); cell.font = H; cell.fill = HF
        for i, r in enumerate(rows, start_row + 1):
            for j, v in enumerate(r, 1):
                ws.cell(row=i, column=j, value=v)
        for j, h in enumerate(headers, 1):
            width = max([len(str(h))] + [len(str(r[j - 1])) for r in rows if r[j - 1] is not None] + [8])
            ws.column_dimensions[get_column_letter(j)].width = min(width + 2, 60)
        ws.freeze_panes = ws.cell(row=start_row + 1, column=1)

    # data sheets first (charts reference them)
    wsd = wb.active; wsd.title = "Pro Tag"
    table(wsd, ["Datum", "Richtig", "Falsch", "Fehlerquote"],
          [[d["date"], d["right"], d["wrong"], d["rate"]] for d in S["days"]])
    for row in wsd.iter_rows(min_row=2, min_col=4, max_col=4):
        for cell in row: cell.number_format = "0%"

    wsw = wb.create_sheet("Wörter")
    wrows = []
    for k, w in sorted(c["words"].items(), key=lambda x: (x[1].get("firstDate") or "", x[1].get("de") or "")):
        s = c["per_word"].get(k, {"right": 0, "wrong": 0})
        wrows.append([w.get("de"), w.get("article") or "", w.get("plural") or "", w.get("forms") or "", TYPE.get(w.get("type"), ""),
                      w.get("sector") or "", w.get("meaning") or "", w.get("es") or "", w.get("example") or "",
                      w.get("firstDate") or "", s["right"], s["wrong"], c["status"](k)])
    table(wsw, ["Wort", "Artikel", "Plural", "Formen", "Wortart", "Bereich", "Bedeutung", "Spanisch", "Beispiel",
                "Erstmals", "Richtig", "Falsch", "Status"], wrows)

    wsl = wb.create_sheet("Lektionen")
    lrows = []
    for d in sorted(c["lessons"]):
        L = c["lessons"][d]; p = c["progress"].get(d, {}); sc = p.get("score") or {}
        r, w = sc.get("right", 0), sc.get("wrong", 0)
        lrows.append([d, L.get("sector", ""), L.get("theme", ""), (L.get("grammar") or {}).get("topic", ""),
                      len(L.get("exercises", [])), r, w, (w / (r + w)) if r + w else None, "ja" if p.get("done") else "nein"])
    table(wsl, ["Datum", "Bereich", "Thema", "Grammatik", "Aufgaben", "Richtig", "Falsch", "Fehlerquote", "Erledigt"], lrows)
    for row in wsl.iter_rows(min_row=2, min_col=8, max_col=8):
        for cell in row: cell.number_format = "0%"

    wsg = wb.create_sheet("Gruppen")
    table(wsg, ["Wortart", "Gesehen", "Gelernt"], [[g["label"], g["seen"], g["learned"]] for g in S["words_by_type"]])
    table(wsg, ["Bereich", "Gesehen", "Gelernt"], [[g["label"], g["seen"], g["learned"]] for g in S["words_by_sector"]], start_row=7)
    wsg.freeze_panes = None

    # dashboard
    ws = wb.create_sheet("Dashboard", 0)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 2
    for col in "BCDEFGHIJKLM":
        ws.column_dimensions[col].width = 14
    ws["B2"] = "Deutsch am Abend"; ws["B2"].font = Font(bold=True, size=20, color=INK)
    ws["B3"] = f"Wochenbericht · Stand {today}"; ws["B3"].font = Font(color="59616A")
    pct = lambda v: "–" if v is None else f"{round(v * 100)} %"
    kpis = [("Wörter gesehen", S["words_seen"]), ("Gelernt", S["words_learned"]), ("Fehlerquote 7 Tage", pct(S["error_rate_7d"])),
            ("Fehlerquote gesamt", pct(S["error_rate_all"])), ("Lektionen (7 Tage)", f'{S["lessons_done_last_7d"]} / {S["lessons_last_7d"]}'),
            ("Serie", f'{S["streak_days"]} Tage')]
    for i, (label, val) in enumerate(kpis):
        col = 2 + i * 2
        lc = ws.cell(row=5, column=col, value=label); lc.font = Font(size=9, bold=True, color="59616A")
        vc = ws.cell(row=6, column=col, value=val); vc.font = Font(size=18, bold=True, color=INK)
        for r_ in (5, 6):
            ws.cell(row=r_, column=col).fill = PatternFill("solid", fgColor=SOFT)
            ws.cell(row=r_, column=col + 1).fill = PatternFill("solid", fgColor=SOFT)

    row = 8
    ws.cell(row=row, column=2, value="Plan für die nächste Woche").font = Font(bold=True, size=13)
    row += 1
    lines = []
    if plan.get("summary"): lines.append(plan["summary"])
    for a in plan.get("weakAreas", []) or []:
        lines.append(f'• {a.get("area", "")}: {a.get("detail", "")}')
    if plan.get("focusTopics"): lines.append("Grammatik im Fokus: " + ", ".join(plan["focusTopics"]))
    if plan.get("difficulty"): lines.append("Schwierigkeit: " + plan["difficulty"])
    if not lines: lines.append("Noch kein Plan vorhanden.")
    for ln in lines:
        cell = ws.cell(row=row, column=2, value=ln); cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=13)
        ws.row_dimensions[row].height = 15 * max(1, len(ln) // 120 + 1)
        row += 1
    row += 1

    if S["days"]:
        ch = LineChart(); ch.title = "Fehlerquote pro Tag"; ch.y_axis.title = "Fehler"; ch.y_axis.number_format = "0%"
        ch.y_axis.scaling.min = 0; ch.y_axis.scaling.max = 1; ch.legend = None; ch.height = 7.5; ch.width = 17
        n = len(S["days"])
        ch.add_data(Reference(wsd, min_col=4, min_row=1, max_row=n + 1), titles_from_data=True)
        ch.set_categories(Reference(wsd, min_col=1, min_row=2, max_row=n + 1))
        ch.series[0].graphicalProperties.line.solidFill = "3E5F8A"; ch.series[0].graphicalProperties.line.width = 22000
        ch.series[0].smooth = False
        ws.add_chart(ch, f"B{row}")
    else:
        ws.cell(row=row, column=2, value="Noch keine beantworteten Übungen: das Diagramm erscheint nach der ersten Lektion.")
    for i, (title, start) in enumerate([("Wörter nach Wortart", 1), ("Wörter nach Bereich", 7)]):
        bc = BarChart(); bc.type = "bar"; bc.title = title; bc.height = 6.5; bc.width = 11
        bc.add_data(Reference(wsg, min_col=2, max_col=3, min_row=start, max_row=start + 3), titles_from_data=True)
        bc.set_categories(Reference(wsg, min_col=1, min_row=start + 1, max_row=start + 3))
        bc.series[0].graphicalProperties.solidFill = "C9D3E0"; bc.series[1].graphicalProperties.solidFill = "3E5F8A"
        ws.add_chart(bc, f"{'B' if i == 0 else 'H'}{row + 16}")
    hr = row + 30
    ws.cell(row=hr, column=2, value="Schwierige Wörter").font = Font(bold=True, size=13)
    hrows = [[h["de"], TYPE.get(h["type"], ""), h["wrong"], h["right"]] for h in S["hardest_words"]]
    for j, h in enumerate(["Wort", "Wortart", "Falsch", "Richtig"], 2):
        cell = ws.cell(row=hr + 1, column=j, value=h); cell.font = H; cell.fill = HF
    for i, r in enumerate(hrows or [["Noch keine Fehler", "", "", ""]], hr + 2):
        for j, v in enumerate(r, 2):
            ws.cell(row=i, column=j, value=v)
    wb.save(out)
    print("saved", out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "stats":
        stats_cmd(sys.argv[2], sys.argv[3])
    elif cmd == "excel":
        excel_cmd(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        sys.exit("unknown command")
