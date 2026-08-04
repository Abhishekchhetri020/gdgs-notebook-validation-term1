#!/usr/bin/env python3
"""Join the fresh ERP roster to the audit findings -> per-class student x subject matrix."""
import csv, json, re, unicodedata, os
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.expanduser("~/Downloads/nbv-report")
D=json.load(open(os.path.join(OUT,"data.json"),encoding="utf8"))

CL=['I','II','III','IV','V','VI','VII','VIII','IX','X']
# subject columns per class, in the order the drive scheduled them
SUBS={}
for s in D["slots"]:
    SUBS.setdefault(s["c"],[])
    if s["s"] not in SUBS[s["c"]]: SUBS[s["c"]].append(s["s"])

SLOT={(s["c"],s["s"]):s for s in D["slots"]}

def norm(n):
    n=unicodedata.normalize('NFKD',str(n)).encode('ascii','ignore').decode()
    n=re.sub(r'[^A-Za-z ]',' ',n).upper()
    return ' '.join(n.split())

# ---- roster ----
students=[]
with open('roster_erp.csv',newline='',encoding='utf8') as f:
    for r in csv.DictReader(f):
        c=r['Class Name'].strip()
        if c not in CL: continue
        students.append({"c":c,"sec":r['Section Name'].strip(),
            "adm":re.sub(r'^GDGPS-DBG-','',r['Admission No.'].strip()),
            "roll":str(r['Roll No.']).replace('.0',''),
            "name":' '.join(str(r['Student Name']).split()),
            "opt":str(r.get('Optional Subjects') or '').strip()})
students.sort(key=lambda s:(CL.index(s["c"]),s["sec"],int(s["roll"]) if s["roll"].isdigit() else 999))

# ---- section-level rules: whole groups with no individual verdict ----
# (class, subject, {sections} or None=all) -> (code, why)
SECTION_RULE=[
 ("IV","Hindi",{"A","B"},"NOT-VALIDATED","Subject teacher on leave — notebooks never produced"),
 ("V","Hindi",{"B"},"NOT-VALIDATED","Notebooks not handed to the validator by the subject teacher"),
 ("IX","English",{"A","B"},"NOT-VALIDATED","Subject teacher on long leave — notebooks never produced"),
 ("IX","Hindi / Urdu",{"A"},"NOT-VALIDATED","Subject teacher on leave — section not validated"),
 ("VII","Mathematics",{"A"},"NOT-SUBMITTED","Section notebooks not submitted on the day; re-run arranged, report awaited"),
 ("VII","Sanskrit / Urdu",{"A","B"},"NOT-SUBMITTED","Sanskrit notebooks not submitted for validation"),
 ("VIII","General Knowledge",{"A"},"NOT-SUBMITTED","Whole section marked NS — advance collection not handed over"),
 ("VI","General Knowledge",{"C"},"INC","Every row in the section marked incomplete"),
 ("IX","Sanskrit",None,"NO-VERDICT","Sheet records only 12 validated of 114 with an empty defaulter box"),
 ("V","Science",None,"NO-VERDICT","Sheet records only 17 validated of 80 with no explanation for the rest"),
 ("II","Mathematics",{"B"},"UNCLEAR","11 rows left blank on the sheet — cannot be established whether seen"),
 ("X","Hindi / Urdu",None,"NOT-VALIDATED","Hindi teacher absent — all Hindi notebooks unvalidated (Urdu students of X A were validated)"),
]
def section_rule(c,sub,sec):
    for rc,rs,secs,code,why in SECTION_RULE:
        if rc==c and rs==sub and (secs is None or sec in secs): return code,why
    return None

# ---- individual findings, resolved by the STRICT matcher in match.py ----
# adm number -> exact name -> unique first name. Never a shared surname.
import match as MATCH   # runs the resolver and exposes resolve()/by_adm

IND={}          # roster adm no. -> {subject: (code, why)}
unmatched=[]; left_school=[]; moved=[]
for st in D["students"]:
    nm=st["n"]
    if re.match(r'^\d|^All\b|^\d+ ',nm) or 'unnamed' in nm or 'students' in nm.lower():
        continue
    hit,how = MATCH.resolve(st["c"], nm, st.get("adm"))
    if hit:
        for sub,date,code,why in st["f"]:
            IND.setdefault(hit["adm"],{})[sub]=(code,why)
    else:
        adm=st.get("adm")
        if adm and adm in MATCH.by_adm and MATCH.by_adm[adm]["c"]!=st["c"]:
            r=MATCH.by_adm[adm]
            moved.append(f'{nm} ({adm}) appears on the Class {st["c"]} sheets but the ERP now has this student in Class {r["c"]}-{r["sec"]}')
        elif adm and adm not in MATCH.by_adm:
            left_school.append(f'{nm} ({adm}) is named on the Class {st["c"]} sheets but is no longer on the ERP roster')
        else:
            unmatched.append(f'Class {st["c"]} — "{nm}" ({how})')

# ---- ADMISSION-NUMBER vs NAME CHECK ---------------------------------------
# An admission number transcribed from a sheet can be wrong. If the roster name
# for that number is a different person, the number must not be trusted.
# (Caught 'Kartik Aryan' carrying Kanishk Kushan's number, and 'Rishav'
#  carrying Reyansh Kumar's.)
import difflib
adm_conflicts=[]
for st in D["students"]:
    nm=st["n"]; adm=st.get("adm")
    if not adm or re.match(r'^\d|^All\b|^\d+ ',nm): continue
    r=MATCH.by_adm.get(adm)
    if not r: continue
    a=norm(re.sub(r'\(.*?\)','',nm)); b=norm(r["name"])
    if a==b or (set(a.split())&set(b.split())) or difflib.SequenceMatcher(None,a,b).ratio()>=0.72:
        continue
    adm_conflicts.append(f'"{nm}" carries admission no. {adm}, which the ERP says is {r["name"]}')
if adm_conflicts:
    raise SystemExit("REFUSING TO BUILD - admission number contradicts the name:\n  "
                     + "\n  ".join(adm_conflicts))

# ---- INTEGRITY GUARD -------------------------------------------------------
# The bug this prevents: two different names on the sheets silently resolving to
# the SAME child, so one student inherits another's record. Purvika Singh's
# "left the school" landed on Aanya Singh this way; four Class VI girls landed
# on Aarohi Kumari and four boys on Ankur Kumar.
_seen={}; _collide=[]
for st in D["students"]:
    nm=st["n"]
    if re.match(r'^\d|^All\b|^\d+ ',nm) or 'unnamed' in nm or 'students' in nm.lower():
        continue
    hit,_how = MATCH.resolve(st["c"], nm, st.get("adm"))
    if not hit: continue
    prev=_seen.get(hit["adm"])
    if prev and norm(prev)!=norm(nm):
        _collide.append(f'{hit["name"]} ({hit["adm"]}) <- both "{prev}" and "{nm}"')
    _seen[hit["adm"]]=nm
merged=_collide   # surfaced on the page so a human can confirm each merge

SUBALIAS={"Sanskrit":"Sanskrit / Urdu","Sanskrit/Urdu":"Sanskrit / Urdu","Hindi / Urdu":"Hindi / Urdu",
          "Hindi":"Hindi","Physics":"Physics"}

matrix=[]
for s in students:
    found=IND.get(s["adm"],{})
    cells=[]
    for sub in SUBS[s["c"]]:
        slot=SLOT[(s["c"],sub)]
        # 1. individual finding wins
        hit=None
        for fsub,(code,why) in found.items():
            fs=SUBALIAS.get(fsub,fsub)
            if fs==sub or fsub==sub or (sub.startswith(fs) and fs!="Hindi"):
                hit=(code,why); break
        if hit: cells.append({"v":hit[0],"w":hit[1]}); continue
        # 2. slot not run at all
        if slot["st"]=="idle": cells.append({"v":"NOT-DUE","w":"Scheduled Tue 4 August"}); continue
        if slot["st"]=="miss": cells.append({"v":"NO-REPORT","w":"Validation due — no report received"}); continue
        # 3. section-level rule
        sr=section_rule(s["c"],sub,s["sec"])
        if sr: cells.append({"v":sr[0],"w":sr[1]}); continue
        # 4. otherwise the sheet showed no defect for this child
        cells.append({"v":"OK","w":"Notebook produced and accepted"})
    matrix.append({**s,"cells":cells})

json.dump({"subjects":SUBS,"rows":matrix,"unmatched":unmatched,"left_school":left_school,"moved":moved,"merged":merged},open(os.path.join(OUT,"matrix.json"),"w"),indent=0)
from collections import Counter
cc=Counter(c["v"] for r in matrix for c in r["cells"])
print(f"students={len(matrix)}  cells={sum(len(r['cells']) for r in matrix)}")
for k,v in cc.most_common(): print(f"  {k:14s} {v:5d}")
print(f"\nfindings matched to roster: {len(IND)}")
if unmatched:
    print(f"UNMATCHED findings ({len(unmatched)}) — kept out of the matrix:")
    for u in unmatched: print("   ",u)
