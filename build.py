#!/usr/bin/env python3
"""Build the public and private notebook-validation report pages from data.json."""
import json, html, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "data.json"), encoding="utf8"))
MX = json.load(open(os.path.join(HERE, "matrix.json"), encoding="utf8"))
M = D["meta"]
CLASSES = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

# Cell vocabulary for the class charts: code -> (short label, css class, plain meaning)
CELL = {
 "OK":            ("&#10003;",  "c-ok",   "Notebook produced and accepted"),
 "NS":            ("NS",        "c-bad",  "Not submitted / not brought"),
 "NOT-SUBMITTED": ("NS",        "c-bad",  "Section notebooks not submitted"),
 "NC":            ("NC",        "c-nc",   "NOT CHECKED by the subject teacher"),
 "NC + INC":      ("NC",        "c-nc",   "Not checked by the teacher, and incomplete"),
 "INC + NC":      ("NC",        "c-nc",   "Incomplete, and not checked by the teacher"),
 "INC":           ("INC",       "c-warn", "Incomplete work"),
 "INDEX":         ("IX",        "c-warn", "Index / date / page number missing"),
 "AB":            ("AB",        "c-ab",   "Student absent"),
 "NOT-VALIDATED": ("&#8212;",   "c-nov",  "Never validated — notebooks never reached the validator"),
 "NO-VERDICT":    ("?",         "c-unk",  "Sheet recorded no verdict for this child"),
 "UNCLEAR":       ("?",         "c-unk",  "Row left blank on the sheet"),
 "NO-REPORT":     ("&middot;",  "c-none", "Validation due — no report received"),
 "NOT-DUE":       ("",          "c-idle", "Scheduled Tue 4 August"),
 "NEW":           ("N",         "c-neut", "New student"),
 "LEFT":          ("L",         "c-neut", "Has left the school"),
}
PROBLEM = {"NS","NOT-SUBMITTED","NC","NC + INC","INC + NC","INC","INDEX","AB",
           "NOT-VALIDATED","NO-VERDICT","UNCLEAR","NO-REPORT"}

# Short column codes so the header sits directly over its cells.
ABBR = {
 "English":"Eng", "Hindi":"Hin", "Mathematics":"Math", "Science":"Sci",
 "General Knowledge":"GK", "Information Technology":"IT", "Social Science":"SST",
 "Financial Literacy":"Fin.Lit", "Sanskrit / Urdu":"Sans/Urd", "Sanskrit":"Sans",
 "Hindi / Urdu":"Hin/Urd", "Physics":"Phy", "Chemistry":"Chem", "Biology":"Bio",
}

def e(s): return html.escape(str(s), quote=False)

CSS = """
:root{
  --ground:#f6f6f3; --surface:#fff; --surface-2:#efefea; --line:#dedcd4;
  --ink:#1b1e21; --ink-2:#4c5257; --ink-3:#7c8288;
  --accent:#2f5d63; --accent-soft:#dfeceb;
  --ok:#2b7a55; --ok-bg:#e2f0e7;
  --warn:#9c6a12; --warn-bg:#f6ecd6;
  --bad:#a63c38; --bad-bg:#f7e2e0;
  --idle:#7c8288; --idle-bg:#e9e9e4;
  --shadow:0 1px 2px rgba(20,25,25,.06),0 4px 14px rgba(20,25,25,.05);
  --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:ui-sans-serif,-apple-system,"Segoe UI","Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --ground:#131518; --surface:#1b1e22; --surface-2:#23272c; --line:#31363c;
  --ink:#e9e8e4; --ink-2:#b0b5ba; --ink-3:#80868c;
  --accent:#7fb3b6; --accent-soft:#1e3134;
  --ok:#79c79b; --ok-bg:#17301f; --warn:#dfae5c; --warn-bg:#332714;
  --bad:#e18a85; --bad-bg:#361b1a; --idle:#80868c; --idle-bg:#24282c;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 4px 16px rgba(0,0,0,.3);}}
:root[data-theme="dark"]{
  --ground:#131518; --surface:#1b1e22; --surface-2:#23272c; --line:#31363c;
  --ink:#e9e8e4; --ink-2:#b0b5ba; --ink-3:#80868c;
  --accent:#7fb3b6; --accent-soft:#1e3134;
  --ok:#79c79b; --ok-bg:#17301f; --warn:#dfae5c; --warn-bg:#332714;
  --bad:#e18a85; --bad-bg:#361b1a; --idle:#80868c; --idle-bg:#24282c;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 4px 16px rgba(0,0,0,.3);}
:root[data-theme="light"]{
  --ground:#f6f6f3; --surface:#fff; --surface-2:#efefea; --line:#dedcd4;
  --ink:#1b1e21; --ink-2:#4c5257; --ink-3:#7c8288;
  --accent:#2f5d63; --accent-soft:#dfeceb;
  --ok:#2b7a55; --ok-bg:#e2f0e7; --warn:#9c6a12; --warn-bg:#f6ecd6;
  --bad:#a63c38; --bad-bg:#f7e2e0; --idle:#7c8288; --idle-bg:#e9e9e4;
  --shadow:0 1px 2px rgba(20,25,25,.06),0 4px 14px rgba(20,25,25,.05);}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px 96px}
h1,h2,h3{font-family:var(--serif);font-weight:600;text-wrap:balance;margin:0}
.eyebrow{font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);font-family:var(--sans);font-weight:600}
header.top{border-bottom:1px solid var(--line);background:var(--surface);padding:38px 0 30px;margin-bottom:30px}
header.top .wrap{padding-bottom:0}
h1{font-size:clamp(27px,4.2vw,40px);line-height:1.12;letter-spacing:-.015em;margin:10px 0 12px}
.sub{color:var(--ink-2);max-width:68ch;font-size:15.5px}
.meta{display:flex;flex-wrap:wrap;gap:8px 22px;margin-top:18px;font-family:var(--mono);font-size:12px;color:var(--ink-3)}
nav.toc{display:flex;flex-wrap:wrap;gap:6px;margin:22px 0 34px}
nav.toc a{font-size:12.5px;padding:5px 11px;border:1px solid var(--line);border-radius:2px;background:var(--surface);color:var(--ink-2);text-decoration:none}
nav.toc a:hover{border-color:var(--accent);color:var(--accent)}
nav.toc a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:14px;margin-bottom:34px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:3px;padding:16px 18px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.stat::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--c,var(--idle))}
.stat .n{font-family:var(--mono);font-size:30px;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums;color:var(--c,var(--ink));display:block;line-height:1.1}
.stat .l{font-size:12.5px;color:var(--ink-2);margin-top:3px}
section{margin-bottom:46px;scroll-margin-top:20px}
section>h2{font-size:22px;letter-spacing:-.01em;margin-bottom:6px}
section>.lede{color:var(--ink-2);max-width:72ch;margin-bottom:18px;font-size:14.5px}
.legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));border:1px solid var(--line);border-radius:3px;overflow:hidden;background:var(--surface)}
.legend div{padding:13px 16px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.legend b{display:block;font-family:var(--mono);font-size:12.5px;margin-bottom:2px}
.legend span{font-size:13px;color:var(--ink-2);line-height:1.45}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:3px;background:var(--surface);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:var(--surface-2);font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-2);font-weight:600;white-space:nowrap;position:sticky;top:0;z-index:2}
tbody tr:last-child td{border-bottom:0}
td.cls{font-family:var(--serif);font-size:17px;font-weight:600;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{font-family:var(--mono);font-size:11px;padding:3px 7px;border-radius:2px;border:1px solid transparent;white-space:nowrap}
.s-ok,.s-early{background:var(--ok-bg);color:var(--ok);border-color:color-mix(in srgb,var(--ok) 30%,transparent)}
.s-part{background:var(--warn-bg);color:var(--warn);border-color:color-mix(in srgb,var(--warn) 32%,transparent)}
.s-miss{background:var(--bad-bg);color:var(--bad);border-color:color-mix(in srgb,var(--bad) 32%,transparent)}
.s-idle{background:var(--idle-bg);color:var(--idle);border-color:color-mix(in srgb,var(--idle) 28%,transparent)}
.ratio{font-family:var(--mono);font-size:12.5px;white-space:nowrap}
.bar{display:block;height:4px;width:74px;background:var(--surface-2);border-radius:2px;margin-top:5px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--c,var(--accent))}
.card{background:var(--surface);border:1px solid var(--line);border-radius:3px;margin-bottom:12px;box-shadow:var(--shadow);overflow:hidden}
.card>summary{list-style:none;cursor:pointer;padding:15px 18px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.card>summary::-webkit-details-marker{display:none}
.card>summary:hover{background:var(--surface-2)}
.card>summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.card .tw{font-family:var(--serif);font-size:19px;font-weight:600;min-width:92px}
.card .who{color:var(--ink-2);font-size:13.5px;flex:1;min-width:170px}
.card .marker{font-family:var(--mono);font-size:11px;color:var(--ink-3);transition:transform .18s ease}
.card[open] .marker{transform:rotate(90deg)}
.card .body{border-top:1px solid var(--line)}
.subrow{display:grid;grid-template-columns:minmax(150px,1.15fr) 86px minmax(150px,1fr) minmax(210px,2.5fr);gap:14px;padding:13px 18px;border-bottom:1px solid var(--line);font-size:13.5px;align-items:start}
.subrow:last-child{border-bottom:0}
.subrow .sname{font-weight:600}
.subrow .sdate{font-family:var(--mono);font-size:11.5px;color:var(--ink-3);display:block;font-weight:400;margin-top:1px}
.subrow .counts{font-family:var(--mono);font-size:11.5px;font-variant-numeric:tabular-nums;color:var(--ink-2)}
.subrow .note{color:var(--ink-2);line-height:1.5}
.subrow .note b{color:var(--ink);font-weight:600}
.act{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--c,var(--accent));border-radius:3px;padding:14px 18px;box-shadow:var(--shadow);margin-bottom:10px}
.act h3{font-family:var(--sans);font-size:14.5px;font-weight:600;margin-bottom:4px;display:flex;gap:9px;align-items:baseline;flex-wrap:wrap}
.act h3 .sev{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--c)}
.act p{margin:0 0 5px;font-size:13.5px;color:var(--ink-2);line-height:1.5}
.act .to{font-family:var(--mono);font-size:11.5px;color:var(--ink-3);margin-top:7px;display:block}
.callout{background:var(--accent-soft);border:1px solid color-mix(in srgb,var(--accent) 28%,transparent);border-radius:3px;padding:16px 18px;font-size:14px;line-height:1.55}
.callout p{margin:0}.callout p+p{margin-top:8px}
.q{font-family:var(--serif);font-style:italic}
.corr{border-left:3px solid var(--ok)}
.tools{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;align-items:center}
.tools input,.tools select{font:inherit;font-size:13.5px;padding:7px 10px;border:1px solid var(--line);border-radius:2px;background:var(--surface);color:var(--ink);min-width:150px}
.tools input:focus-visible,.tools select:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.count{font-family:var(--mono);font-size:12px;color:var(--ink-3)}
.vd{display:inline-block;font-family:var(--mono);font-size:10.5px;padding:1px 5px;border-radius:2px;margin:1px 4px 1px 0}
.v-NC,.v-NS,.v-BLANK,.v-NO-RUN{background:var(--bad-bg);color:var(--bad)}
.v-INC,.v-AB,.v-INDEX{background:var(--warn-bg);color:var(--warn)}
.v-LEFT,.v-NEW{background:var(--idle-bg);color:var(--idle)}
.flags{display:flex;flex-direction:column;gap:3px}
.flags div{font-size:12.5px;color:var(--ink-2)}
.pill{display:inline-block;font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;border-radius:2px;background:var(--bad-bg);color:var(--bad);margin-left:8px;vertical-align:2px}
.pill.pub{background:var(--ok-bg);color:var(--ok)}
/* class charts */
.cellkey{display:grid;grid-template-columns:repeat(auto-fit,minmax(232px,1fr));gap:6px 16px;margin-bottom:16px;
  padding:14px 16px;border:1px solid var(--line);border-radius:3px;background:var(--surface);font-size:12.5px;color:var(--ink-2)}
.cellkey div{display:flex;align-items:center;gap:8px}
.chartwrap{max-height:74vh;overflow:auto}
/* fixed layout: the header cell and its column can never drift apart */
table.grid{font-size:12.5px;border-collapse:separate;border-spacing:0;table-layout:fixed;width:auto}
col.w-rno{width:72px}col.w-snm{width:196px}col.w-adm{width:86px}col.w-pc{width:34px}col.w-sub{width:56px}
table.grid th,table.grid td{border-bottom:1px solid var(--line);padding:5px 8px;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
table.grid thead th{position:sticky;top:0;z-index:3;background:var(--surface-2);vertical-align:bottom;
  font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;padding:9px 6px}
table.grid th.sub{text-align:center;font-weight:700;color:var(--ink);padding:9px 2px;
  border-left:1px solid var(--line)}
table.grid td.cell{border-left:1px solid var(--line)}
table.grid td.rno{font-family:var(--mono);font-size:11px;color:var(--ink-3)}
table.grid td.snm{font-weight:600}
table.grid td.adm{font-family:var(--mono);font-size:11px;color:var(--ink-3)}
table.grid td.pc{font-family:var(--mono);text-align:center;color:var(--ink-3);font-variant-numeric:tabular-nums}
table.grid td.pc.hi{color:var(--bad);font-weight:700}
table.grid tbody tr:hover td{background:color-mix(in srgb,var(--accent) 7%,transparent)}
/* NOTE: the inline-block form is for the legend swatches only. Applying it to a
   <td class="cell"> takes the cell out of table layout and the columns drift. */
span.cell{display:inline-block;min-width:26px;text-align:center;font-family:var(--mono);font-size:10.5px;
  font-weight:600;padding:2px 4px;border-radius:2px;line-height:1.35}
td.cell{display:table-cell;text-align:center;padding:4px 2px;font-family:var(--mono);
  font-size:10.5px;font-weight:600}
.c-ok{background:var(--ok-bg);color:var(--ok)}
.c-bad{background:var(--bad-bg);color:var(--bad)}
.c-nc{background:var(--bad);color:#fff}
.c-warn{background:var(--warn-bg);color:var(--warn)}
.c-ab{background:var(--idle-bg);color:var(--warn)}
.c-nov{background:repeating-linear-gradient(45deg,var(--bad-bg),var(--bad-bg) 4px,transparent 4px,transparent 8px);color:var(--bad)}
.c-unk{background:var(--surface-2);color:var(--ink-2);border:1px dashed var(--line)}
.c-none{background:transparent;color:var(--ink-3)}
.c-idle{background:repeating-linear-gradient(45deg,transparent,transparent 5px,var(--surface-2) 5px,var(--surface-2) 10px);color:var(--ink-3)}
.c-neut{background:var(--idle-bg);color:var(--idle)}
.chk{display:flex;align-items:center;gap:7px;font-size:13.5px;color:var(--ink-2);cursor:pointer}
.btn{font:inherit;font-size:13.5px;padding:7px 12px;border:1px solid var(--line);border-radius:2px;
  background:var(--surface);color:var(--ink);cursor:pointer}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn:focus-visible,.chk input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
footer{border-top:1px solid var(--line);margin-top:20px;padding-top:20px;font-size:12.5px;color:var(--ink-3);line-height:1.6}
@media(max-width:760px){.subrow{grid-template-columns:1fr;gap:5px}.legend div{border-right:0}}
"""

SEVC = {"critical":"var(--bad)","high":"var(--warn)","medium":"var(--accent)","low":"var(--accent)","resolved":"var(--ok)"}
LBL = {"ok":"reported","part":"incomplete","miss":"no report","idle":"not due","early":"done early"}

# ---- privacy guard -------------------------------------------------------
# Every student name and admission number that must never reach the public build.
_STOP = {"all", "students", "of", "and", "the", "unnamed", "defaulters", "section"}
STUDENT_NAMES = set()
for _s in D["students"]:
    _n = _s["n"]
    if re.match(r"^\d|^All\b|^\d+ students", _n):
        continue
    STUDENT_NAMES.add(_n)
ADM_RE = re.compile(r"\bAD-\d{5}\b")
# longest first so full names are redacted before their fragments
_NAME_RE = re.compile(
    r"(?<!Mr\. )(?<!Ms\. )(?<!Dr\. )(?<!Mrs\. )\b(" +
    "|".join(re.escape(n) for n in sorted(STUDENT_NAMES, key=len, reverse=True)) + r")\b")

PRIVATE = True  # flipped by page()

def redact(text):
    """Strip student names and admission numbers for the public build."""
    if PRIVATE:
        return text
    text = ADM_RE.sub("[adm. no. withheld]", text)
    text = _NAME_RE.sub("[student name withheld]", text)
    # collapse runs of consecutive redactions, e.g. lists of names
    text = re.sub(r"(\[student name withheld\](,| and|;)?\s*){2,}",
                  "[student names withheld] ", text)
    return text


def stat_band():
    s = [("ok", M["slots_reported"], f"Reports received of {M['slots_due']} due"),
         ("bad", M["slots_missing"], "Validations with no report"),
         ("warn", 11, "Whole sections never validated"),
         ("bad", 60, "Notebooks the teacher never checked"),
         ("idle", M["slots_not_due"], "Not yet due (Tue 4 Aug)")]
    return '<div class="stats">' + "".join(
        f'<div class="stat" style="--c:var(--{c})"><span class="n">{n}</span><span class="l">{e(l)}</span></div>'
        for c, n, l in s) + '</div>'


def legend():
    return ('<section id="legend"><h2>What the marks on the sheets mean</h2>'
            '<p class="lede">Reading a sheet correctly depends on this vocabulary — and on treating an empty box '
            'as a real signal rather than a pass.</p><div class="legend">'
            + "".join(f'<div><b>{e(k)}</b><span>{e(v)}</span></div>' for k, _, v in D["legend"])
            + '</div></section>')


def corrections():
    rows = "".join(
        f'<div class="act corr"><h3><span class="sev" style="color:var(--ok)">corrected</span>{e(t)}</h3><p>{e(p)}</p></div>'
        for t, p in D["corrections"])
    return ('<section id="corrections"><h2>Corrections to the first-pass check</h2>'
            '<p class="lede">This audit re-read the whole mailbox with no keyword filter. Three findings from the '
            'earlier internal check were wrong and are corrected here.</p>' + rows + '</section>')


def coverage():
    rows = []
    for v in D["validators"]:
        subs = [s for s in D["slots"] if s["c"] == v["cls"]]
        due = v["due"]; got = v["got"]
        pct = round(got / due * 100) if due else 0
        col = "var(--ok)" if pct >= 80 else "var(--warn)" if pct >= 45 else "var(--bad)"
        acted = v["acted"] + (' <span class="pill">substituted</span>' if v["sub"] else "")
        chips = "".join(f'<span class="chip s-{s["st"]}" title="{e(s["d"])} — {LBL[s["st"]]}">{e(s["s"])}</span>' for s in subs)
        rows.append(f'<tr><td class="cls">{e(v["cls"])}</td><td>{acted}</td>'
                    f'<td><span class="ratio" style="color:{col}">{got} / {due}</span>'
                    f'<span class="bar"><i style="width:{pct}%;--c:{col}"></i></span></td>'
                    f'<td><div class="chips">{chips}</div></td></tr>')
    return ('<section id="coverage"><h2>Coverage by class</h2>'
            '<p class="lede">One chip per planned class-subject validation. Green — reported. Amber — reported but the '
            'validation itself was incomplete (a section missing, a teacher absent). Red — due, nothing received. '
            'Grey — falls on Tue 4 August.</p><div class="tbl"><table>'
            '<thead><tr><th>Class</th><th>Validated by</th><th>Reported</th><th>Subject slots</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div></section>')


def by_class():
    out = []
    for v in D["validators"]:
        subs = [s for s in D["slots"] if s["c"] == v["cls"]]
        due, got = v["due"], v["got"]
        col = "var(--ok)" if got / due >= .8 else "var(--warn)" if got / due >= .45 else "var(--bad)"
        rows = [f'<div class="subrow" style="grid-template-columns:1fr"><div class="note">{v["note"]}</div></div>']
        for s in subs:
            cnt = []
            if s.get("t"): cnt.append(f'{s["t"]} total')
            if s.get("v") is not None: cnt.append(f'{s["v"]} validated')
            if s.get("np") is not None: cnt.append(f'{s["np"]} not produced')
            if s.get("ab") is not None: cnt.append(f'{s["ab"]} absent')
            rows.append(
                f'<div class="subrow"><div class="sname">{e(s["s"])}<span class="sdate">{e(s["d"])} · {e(s["by"])}</span></div>'
                f'<div><span class="chip s-{s["st"]}">{LBL[s["st"]]}</span></div>'
                f'<div class="counts">{" · ".join(cnt) or "&mdash;"}</div>'
                f'<div class="note">{redact(s.get("n","&mdash;"))}</div></div>')
        out.append(f'<details class="card"{" open" if got/due < .6 else ""}>'
                   f'<summary><span class="marker">&#9656;</span><span class="tw">Class {e(v["cls"])}</span>'
                   f'<span class="who">{e(v["acted"])}</span>'
                   f'<span class="ratio" style="color:{col}">{got} of {due} reported</span></summary>'
                   f'<div class="body">{"".join(rows)}</div></details>')
    return ('<section id="classes"><h2>Every validation, class by class</h2>'
            '<p class="lede">Counts are quoted exactly as written on the photographed sheet, including where they do '
            'not reconcile. Open a class to see each subject.</p>' + "".join(out) + '</section>')


def teachers():
    out = []
    for t in D["teachers"]:
        col = SEVC.get(t["sev"], "var(--accent)")
        ps = "".join(f"<p>{redact(e(x))}</p>" for x in t["findings"])
        why = f'<span class="to">&rarr; {redact(e(t["why"]))}</span>' if t.get("why") else ""
        out.append(f'<div class="act" style="--c:{col}"><h3><span class="sev">{e(t["sev"])}</span>{e(t["name"])}'
                   f'</h3><p style="color:var(--ink-3);font-family:var(--mono);font-size:11.5px">{e(t["subjects"])}</p>'
                   f'{ps}{why}</div>')
    return ('<section id="teachers"><h2>Teacher-wise findings</h2>'
            '<p class="lede">Ordered by severity. "Not checked" means the child did the work and the subject teacher '
            'never signed it — that is the finding this drive exists to surface.</p>' + "".join(out) + '</section>')


def validators_tbl():
    rows = []
    for v in D["validators"]:
        late = v["due"] - v["sameday"] if v["got"] else 0
        col = "var(--ok)" if v["sameday"] == v["got"] and v["got"] else "var(--warn)"
        rows.append(f'<tr><td class="cls">{e(v["cls"])}</td><td>{e(v["assigned"])}</td>'
                    f'<td>{e(v["acted"])}{" <span class=pill>substituted</span>" if v["sub"] else ""}</td>'
                    f'<td class="ratio">{v["got"]} / {v["due"]}</td>'
                    f'<td class="ratio" style="color:{col}">{v["sameday"]} same-day</td>'
                    f'<td style="color:var(--ink-2)">{e(v["note"])}</td></tr>')
    return ('<section id="validators"><h2>Validator-wise scorecard</h2>'
            '<p class="lede">Who was assigned, who actually did the work, how many reports arrived, and how many came '
            'the same day as the Office Order requires. Several validators were away on CBSE cluster and other duty; '
            'their substitutes are named here so credit and follow-up land on the right person.</p>'
            '<div class="tbl"><table><thead><tr><th>Class</th><th>Assigned</th><th>Actually validated</th>'
            '<th>Reported</th><th>Timeliness</th><th>Assessment</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div></section>')


def students_tbl():
    rows = []
    for s in D["students"]:
        flags = "".join(
            f'<div><span class="vd v-{f[2].split()[0].replace("+","")}">{e(f[2])}</span>'
            f'<b>{e(f[0])}</b> <span style="color:var(--ink-3)">{e(f[1])}</span> — {e(f[3])}</div>'
            for f in s["f"])
        blob = e(f'{s["n"]} {s.get("adm","")} {s["c"]} {s["sec"]} ' + " ".join(x[0] + " " + x[2] + " " + x[3] for x in s["f"]))
        rows.append(f'<tr data-b="{blob.lower()}" data-c="{e(s["c"])}" data-n="{len(s["f"])}">'
                    f'<td class="cls">{e(s["c"])}&#8202;{e(s["sec"])}</td>'
                    f'<td style="font-weight:600">{e(s["n"])}</td>'
                    f'<td class="ratio" style="color:var(--ink-3)">{e(s.get("adm") or "—")}</td>'
                    f'<td class="ratio">{len(s["f"])}</td>'
                    f'<td><div class="flags">{flags}</div></td></tr>')
    opts = "".join(f'<option value="{c}">Class {c}</option>' for c in
                   ["I","II","III","IV","V","VI","VII","VIII","IX","X"])
    return ('<section id="students"><h2>Student-wise findings<span class="pill">confidential</span></h2>'
            '<p class="lede">Every student named on a validation sheet, with each subject where something was wrong. '
            'Students whose notebooks passed are not listed. Sort by the flag count to find the children carrying '
            'problems across several subjects — those are the parent calls.</p>'
            f'<div class="tools"><input id="q" type="search" placeholder="Search name, admission no., subject, defect…" '
            f'aria-label="Search students"><select id="fc" aria-label="Filter by class"><option value="">All classes</option>{opts}</select>'
            '<select id="fv" aria-label="Filter by finding"><option value="">All findings</option>'
            '<option value="not checked">Not checked by teacher</option><option value="not submitted">Not submitted</option>'
            '<option value="incomplete">Incomplete work</option><option value="index">Index / date missing</option>'
            '<option value="absent">Absent</option></select>'
            '<button id="srt" style="font:inherit;font-size:13.5px;padding:7px 12px;border:1px solid var(--line);'
            'border-radius:2px;background:var(--surface);color:var(--ink);cursor:pointer">Sort by flags</button>'
            '<span class="count" id="cnt"></span></div>'
            '<div class="tbl"><table id="st"><thead><tr><th>Class</th><th>Student</th><th>Adm No.</th>'
            '<th>Flags</th><th>What the sheets record</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div></section>')


def charts():
    """One grid per class: every student on the ERP roster x every subject."""
    subs_by_cls = MX["subjects"]
    blocks = []
    for cls in CLASSES:
        rows = [r for r in MX["rows"] if r["c"] == cls]
        if not rows:
            continue
        subs = subs_by_cls[cls]
        cols = ('<colgroup><col class="w-rno"><col class="w-snm"><col class="w-adm"><col class="w-pc">'
                + f'<col class="w-sub">' * len(subs) + '</colgroup>')
        head = "".join(f'<th class="sub" title="{e(s)}">{e(ABBR.get(s, s))}</th>' for s in subs)
        body = []
        for r in rows:
            nprob = sum(1 for c in r["cells"] if c["v"] in PROBLEM)
            tds = []
            for s, c in zip(subs, r["cells"]):
                lab, cc, _ = CELL.get(c["v"], (c["v"], "c-unk", c["v"]))
                tds.append(f'<td class="cell {cc}" title="{e(s)} — {e(c["w"])}">{lab}</td>')
            body.append(
                f'<tr data-p="{nprob}" data-b="{e((r["name"]+" "+r["adm"]+" "+cls+" "+r["sec"]).lower())}">'
                f'<td class="rno">{e(r["sec"])}&#8202;/&#8202;{e(r["roll"])}</td>'
                f'<td class="snm">{e(r["name"])}</td>'
                f'<td class="adm">{e(r["adm"])}</td>'
                f'<td class="pc {"hi" if nprob >= 4 else ""}">{nprob}</td>'
                + "".join(tds) + '</tr>')
        blocks.append(
            f'<details class="card chart" data-cls="{e(cls)}"><summary>'
            f'<span class="marker">&#9656;</span><span class="tw">Class {e(cls)}</span>'
            f'<span class="who">{len(rows)} students &middot; {len(subs)} subjects</span></summary>'
            f'<div class="body"><div class="tbl chartwrap"><table class="grid">{cols}'
            f'<thead><tr><th class="rno">Sec/Roll</th><th class="snm">Student</th>'
            f'<th class="adm">Adm No.</th><th class="pc" title="Number of subjects with something wrong">&#9873;</th>'
            f'{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div></div></details>')

    key = "".join(
        f'<div><span class="cell {cc}">{lab or "&nbsp;"}</span> {e(meaning)}</div>'
        for code, (lab, cc, meaning) in CELL.items())
    return ('<section id="charts"><h2>Class-by-class chart &mdash; every student, every subject</h2>'
            '<p class="lede">Pulled fresh from the ERP on 3 August: 861 active students across 27 sections. '
            'Every subject the drive scheduled for that class is a column. Read across a row to see one child\'s '
            'whole term; read down a column to see one subject. The flag count sorts the worst cases to the top.</p>'
            f'<div class="cellkey">{key}</div>'
            '<div class="tools"><input id="cq" type="search" placeholder="Search a student, admission no. or section…" '
            'aria-label="Search the charts"><label class="chk"><input type="checkbox" id="conly"> '
            'Only students with something wrong</label>'
            '<button id="csrt" class="btn">Sort by flag count</button>'
            '<span class="count" id="ccnt"></span></div>'
            + "".join(blocks) + '</section>')


def actions():
    out = []
    for a in D["actions"]:
        col = SEVC.get(a["sev"], "var(--accent)")
        out.append(f'<div class="act" style="--c:{col}"><h3><span class="sev">{e(a["sev"])}</span>{e(a["t"])}</h3>'
                   + "".join(f"<p>{redact(e(p))}</p>" for p in a["p"])
                   + f'<span class="to">&rarr; {redact(e(a["to"]))}</span></div>')
    return ('<section id="actions"><h2>What needs a decision</h2>'
            '<p class="lede">Ordered by how many children are affected and how avoidable the cause was.</p>'
            + "".join(out) + '</section>')


def quality():
    rows = "".join(f'<tr><td style="font-weight:600">{e(a)}</td><td style="color:var(--ink-2)">{e(b)}</td>'
                   f'<td style="color:var(--ink-2)">{e(c)}</td></tr>' for a, b, c in D["quality"])
    return ('<section id="quality"><h2>Problems with the reports themselves</h2>'
            '<p class="lede">Separate from what the notebooks showed: how the reporting was done.</p>'
            '<div class="tbl"><table><thead><tr><th>Problem</th><th>Where</th><th>Why it matters</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div></section>')


SCRIPT = """
(function(){
 var q=document.getElementById('q'); if(!q) return;
 var fc=document.getElementById('fc'), fv=document.getElementById('fv'),
     cnt=document.getElementById('cnt'), tb=document.querySelector('#st tbody'),
     srt=document.getElementById('srt'), desc=true;
 var rows=[].slice.call(tb.rows);
 function apply(){
   var t=q.value.toLowerCase().trim(), c=fc.value, v=fv.value.toLowerCase(), n=0;
   rows.forEach(function(r){
     var ok=(!t||r.dataset.b.indexOf(t)>-1)&&(!c||r.dataset.c===c)&&(!v||r.dataset.b.indexOf(v)>-1);
     r.style.display=ok?'':'none'; if(ok)n++;
   });
   cnt.textContent=n+' of '+rows.length+' students shown';
 }
 [q,fc,fv].forEach(function(el){el.addEventListener('input',apply)});
 srt.addEventListener('click',function(){
   rows.sort(function(a,b){var d=b.dataset.n-a.dataset.n; return desc?d:-d;});
   desc=!desc; rows.forEach(function(r){tb.appendChild(r)}); apply();
 });
 apply();
})();

/* class charts: search, problems-only filter, sort by flag count */
(function(){
 var cq=document.getElementById('cq'); if(!cq) return;
 var only=document.getElementById('conly'), cnt=document.getElementById('ccnt'),
     btn=document.getElementById('csrt'), desc=true,
     tables=[].slice.call(document.querySelectorAll('table.grid'));
 var all=tables.map(function(t){
   return {t:t, card:t.closest('details'), rows:[].slice.call(t.tBodies[0].rows)};
 });
 function apply(){
   var q=cq.value.toLowerCase().trim(), po=only.checked, shown=0, flagged=0;
   all.forEach(function(g){
     var vis=0;
     g.rows.forEach(function(r){
       var ok=(!q||r.dataset.b.indexOf(q)>-1)&&(!po||+r.dataset.p>0);
       r.style.display=ok?'':'none';
       if(ok){vis++; if(+r.dataset.p>0) flagged++;}
     });
     shown+=vis;
     g.card.style.display=vis?'':'none';
     if((q||po)&&vis) g.card.open=true;
   });
   cnt.textContent=shown+' students shown · '+flagged+' with at least one problem';
 }
 cq.addEventListener('input',apply); only.addEventListener('change',apply);
 btn.addEventListener('click',function(){
   all.forEach(function(g){
     g.rows.sort(function(a,b){var d=b.dataset.p-a.dataset.p; return desc?d:-d;});
     var tb=g.t.tBodies[0]; g.rows.forEach(function(r){tb.appendChild(r)});
   });
   desc=!desc; btn.textContent=desc?'Sort by flag count':'Sort back to roll order'; apply();
 });
 apply();
})();
"""


def page(private):
    global PRIVATE
    PRIVATE = private
    title = "Term I Notebook Validation 2026-27 — Audit Report · G.D. Goenka School, Darbhanga"
    badge = '<span class="pill">contains student names &mdash; school record</span>'
    toc = [("legend","Marks"),("corrections","Corrections"),("coverage","Coverage"),
           ("charts","Class charts"),("students","Students"),("classes","By class"),
           ("validators","Validators"),("teachers","Teachers"),
           ("actions","Actions"),("quality","Reporting quality")]
    nav = '<nav class="toc">' + "".join(f'<a href="#{i}">{e(l)}</a>' for i, l in toc) + '</nav>'

    body = [legend(), corrections(), charts(), students_tbl(), coverage(), by_class(),
            validators_tbl(), teachers(), actions(), quality()]

    note = ("This page names individual students and admission numbers, published on the instruction of the Academic "
            "Coordinator so that every teacher, validator and member of management can see the same record. It is "
            "excluded from search-engine indexing. Please treat it as a school document and do not circulate it "
            "outside the school community.")

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="robots" content="noindex,nofollow">
<style>{CSS}</style></head><body>
<header class="top"><div class="wrap">
<p class="eyebrow">{e(M['school'])} &middot; {e(M['drive'])}</p>
<h1>Notebook Validation Drive &mdash; what the validators reported {badge}</h1>
<p class="sub">Every validation e-mail received between 29 July and 3 August was re-read with no keyword filter, every
photographed sheet rendered and read, and every mark interpreted against the plan of {M['planned_slots']} class-subject
validations. This is what those reports say, what they leave unsaid, and where notebooks are still unchecked.</p>
<div class="meta"><span>Audited {e(M['audited'])}</span><span>{e(M['sources'])}</span>
<span>{M['students']} students &middot; {M['sections']} sections &middot; {M['planned_checks']:,} planned checks</span></div>
</div></header>
<div class="wrap">
{nav}
{stat_band()}
<section><div class="callout"><p><strong>The one thing to take from this audit:</strong> a tick tells you a notebook was
<em>produced</em>. It does not tell you the subject teacher had checked it, whether the work was up to date, or when a
teacher last saw it. That gap is why Director Ma'am wrote on 29 July, <span class="q">&ldquo;the validation is not solving our
purpose&rdquo;</span>, and why Office Order GDGPSD/2026-27/OFFICE/042 was issued on 30 July adding <em>Last checked on (date)
/ unchecked</em> and <em>Complete / Incomplete</em> columns. Reports written before that date cannot answer those questions
retrospectively. Under her instruction of 30 July, <span class="q">&ldquo;Incomplete and not aligned with the requirements to be
considered as NOT SUBMITTED.&rdquo;</span></p></div></section>
{"".join(body)}
<footer><p>{e(note)}</p>
<p>Sources: the full mailbox for 28 July &ndash; 3 August 2026 ({e(M['sources'])}), read message by message with no keyword
filter. Counts are transcribed from the handwritten Defaulter Summary boxes and Remarks columns; where a validator left a
box blank, that is recorded as blank rather than inferred. Plan of record: Term I Notebook Validation 2026-27,
{M['planned_slots']} subject-dates across {M['sections']} sections.</p></footer>
</div><script>{SCRIPT}</script></body></html>"""


# Student names are published on the Academic Coordinator's explicit instruction
# (3 Aug 2026) so that staff, management and parents see one shared record.
# Both files are therefore identical; confidential.html is kept as the link
# already circulated to the Director.
full = page(True)
open(os.path.join(HERE, "index.html"), "w", encoding="utf8").write(full)
open(os.path.join(HERE, "confidential.html"), "w", encoding="utf8").write(full)

nflags = sum(len(s["f"]) for s in D["students"])
cells = sum(len(r["cells"]) for r in MX["rows"])
probs = sum(1 for r in MX["rows"] for c in r["cells"] if c["v"] in PROBLEM)
kids = sum(1 for r in MX["rows"] if any(c["v"] in PROBLEM for c in r["cells"]))
print(f"built index.html + confidential.html (identical — names published by instruction)")
print(f"charts: {len(MX['rows'])} students, {cells} cells, {probs} flagged, {kids} students with >=1 problem")
print(f"detail: {len(D['students'])} student records, {nflags} findings, "
      f"{len(D['teachers'])} teachers, {len(D['slots'])} slots")
