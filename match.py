#!/usr/bin/env python3
"""Resolve audit findings to real ERP students.

The previous matcher accepted any shared token, so a shared surname (KUMAR,
KUMARI, SINGH, JHA) was enough to bind a finding to the wrong child. Rules now:
  1. admission number, when the finding carries one that is on the roster
  2. exact normalised name within the class
  3. first-name match (exact or >=0.82 similar) AND a unique candidate
  4. otherwise UNMATCHED - never guessed
"""
import csv,json,re,unicodedata,os,difflib
from collections import defaultdict
OUT=os.path.expanduser("~/Downloads/nbv-report")
CL=['I','II','III','IV','V','VI','VII','VIII','IX','X']
# tokens too common to identify anybody on their own
COMMON={'KUMAR','KUMARI','SINGH','JHA','RAJ','MD','PRASAD','DEVI','LAL','SHARMA',
        'MANDAL','RAY','ROY','CHOUDHARY','CHAUDHARY','MISHRA','SAH','THAKUR','ARYA',
        'NARAYAN','AHMAD','AHMED','ISLAM','KHAN','ALI','PRIYA','ANAND','SAHU'}
def norm(n):
    n=unicodedata.normalize('NFKD',str(n)).encode('ascii','ignore').decode()
    return ' '.join(re.sub(r'[^A-Za-z ]',' ',n).upper().split())
def sim(a,b): return difflib.SequenceMatcher(None,a,b).ratio()

roster=[]
with open('roster_erp.csv',newline='',encoding='utf8') as f:
    for r in csv.DictReader(f):
        c=r['Class Name'].strip()
        if c not in CL: continue
        roster.append({"c":c,"sec":r['Section Name'].strip(),
            "adm":re.sub(r'^GDGPS-DBG-','',r['Admission No.'].strip()),
            "roll":str(r['Roll No.']).replace('.0',''),
            "name":' '.join(str(r['Student Name']).split())})
by_adm={s['adm']:s for s in roster}
by_key=defaultdict(list)
for s in roster: by_key[(s['c'],norm(s['name']))].append(s)
by_cls=defaultdict(list)
for s in roster: by_cls[s['c']].append(s)

def resolve(cls,name,adm):
    if adm and adm in by_adm and by_adm[adm]['c']==cls:
        return by_adm[adm],'adm'
    nn=norm(re.sub(r'\(.*?\)','',name))
    if len(by_key[(cls,nn)])==1: return by_key[(cls,nn)][0],'exact'
    toks=nn.split()
    if not toks: return None,'empty'
    first=toks[0]
    cands=[]
    for s in by_cls[cls]:
        rt=norm(s['name']).split()
        if not rt: continue
        # same first token, or a close spelling variant of it. Require the same
        # initial and a high ratio: 'ARTHA' must not match 'SARTHAK'.
        if rt[0]==first or (rt[0][0]==first[0] and sim(rt[0],first)>=0.88
                            and abs(len(rt[0])-len(first))<=2):
            cands.append(s)
    # a full-name near-match also counts
    if not cands:
        near=[s for s in by_cls[cls] if sim(norm(s['name']),nn)>=0.90
              and norm(s['name'])[0]==nn[0]]
        cands=near
    if len(cands)==1:
        # guard: if the only thing shared is a common surname, refuse
        shared=set(toks)&set(norm(cands[0]['name']).split())
        if shared and shared <= COMMON and cands[0]['name'].split()[0].upper()!=first:
            return None,'common-surname-only'
        return cands[0],'firstname'
    if len(cands)>1: return None,f'ambiguous({len(cands)})'
    return None,'no-candidate'

D=json.load(open(os.path.join(OUT,'data.json'),encoding='utf8'))
res={'adm':0,'exact':0,'firstname':0}; unmatched=[]; left=[]
mapping={}
for st in D['students']:
    nm=st['n']
    if re.match(r'^\d|^All\b|^\d+ ',nm) or 'unnamed' in nm or 'students' in nm.lower(): continue
    hit,how=resolve(st['c'],nm,st.get('adm'))
    if hit:
        res[how]=res.get(how,0)+1
        mapping[(st['c'],nm)]=hit['adm']
    else:
        adm=st.get('adm')
        if adm and adm not in by_adm: left.append(f"{st['c']} {nm} ({adm}) — on the sheets, not on today's ERP roster")
        else: unmatched.append(f"{st['c']} {nm} ({adm or 'no adm no.'}) — {how}")
json.dump(mapping if False else {f"{k[0]}||{k[1]}":v for k,v in mapping.items()},
          open('name_map.json','w'),indent=0)
if __name__=="__main__":
    print("MATCHED  by admission no.:",res.get('adm',0)," exact name:",res.get('exact',0)," first name (unique):",res.get('firstname',0))
    print(f"\nLEFT THE SCHOOL / not on roster ({len(left)}):")
    for x in left: print("   ",x)
    print(f"\nUNMATCHED, will NOT be guessed ({len(unmatched)}):")
    for x in unmatched: print("   ",x)
