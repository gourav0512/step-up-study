"""Combine raw parser output into data/aktu_cse_syllabus.json (subjects -> units -> topics)."""
import json, re
W = lambda s: len(s.split())
HEAD = re.compile(r"(?:^|(?<=[.;)])\s+)([A-Z][A-Za-z0-9&/,\-’' ()]{2,75}?):\s+")

BAD = ('real connect', 'note', 'e.g', 'example', 'case study', 'case studies', 'activity', 'activities')

def short(t, n=70):
    t = re.sub(r'\s+', ' ', t).strip(' :-,.')
    if len(t) <= n: return t
    return t[:n].rsplit(' ', 1)[0].strip(' ,') + '…'

def split_topics(text, first_line=None):
    marks = []
    for m in HEAD.finditer(text):
        a, name = m.start(1), m.group(1).strip()
        if re.search(r'\)\s+[A-Z]', name):                       # "...(ADT) Arrays" -> heading is "Arrays"
            k = re.search(r'\)\s+(?=[A-Z])', name).end()
            a += name.index(name[k:]) if name[k:] in name else 0
            name = name[k:].strip()
        name = re.sub(r'\s*Real connect$', '', name).strip()
        if name.lower().startswith(BAD) or re.match(r'A\s', name) or (',' in name and len(name.split()) > 4): continue
        marks.append((a, name))
    if not marks:
        clause = re.split(r'[.:]\s', first_line or text, 1)[0]
        return [(short(clause, 60), text)]
    out = []
    if marks[0][0] > 0 and text[:marks[0][0]].strip():
        out.append((short(re.split(r'[.:]\s', text[:marks[0][0]], 1)[0], 60), text[:marks[0][0]].strip()))
    for i, (a, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((short(name, 80), text[a:end].strip()))
    return out

def difficulty(details):
    n = W(details)
    return 'easy' if n <= 25 else 'medium' if n <= 60 else 'hard'

def title_case(s):
    if s.isupper() or s.islower():
        s = s.title().replace(' And ', ' and ').replace(' Of ', ' of ').replace('&', '&')
    return re.sub(r'\bIot\b', 'IoT', s)

def unit_obj(no, text, first_line=None, weight=None):
    tops, seen = [], set()
    for name, det in split_topics(text, first_line):
        name = name.strip() or short(det, 50)
        n = name; k = 2
        while n.lower() in seen: n = f'{name} ({k})'; k += 1
        seen.add(n.lower())
        tops.append({'name': n, 'details': det, 'difficulty': difficulty(det)})
    title = tops[0]['name'] if len(tops) == 1 else ' · '.join(t['name'] for t in tops)[:95]
    return {'no': no, 'title': title, 'weightage': weight, 'topics': tops}

subjects = []
# ---- 1st year (scheme 2026-27) ----
OPTIONAL_Y1 = {'AAS101E','AAS201E','AAS102D','AAS202D','AEE101A','AEE201A','AEC101A','AEC201A','AAS104','AAS204','AAS105','AAS205','AAI101','AAI201','AME101A','AME201A'}
for c in json.load(open('data/raw_y1.json')):
    for code, sem in c['offered']:
        subjects.append({'code': code, 'name': c['title'], 'semester': sem, 'scheme': '2026-27', 'source': 'aktu_syllabus_1st_year.pdf',
            'optional': code in OPTIONAL_Y1,
            'units': [unit_obj(int(k), u['text'], u['first_line'], u['weight']) for k, u in c['units'].items()]})
# ---- 2nd/3rd/4th year ----
def add(raw, scheme, source, sem_of, elective_of=lambda c: None):
    for s in json.load(open(raw)):
        sem = sem_of(s['code'])
        if sem is None: continue
        el = elective_of(s['code']); name = title_case(s['name'])
        if el: name += f' ({el})'
        subjects.append({'code': s['code'], 'name': name, 'semester': sem, 'scheme': scheme, 'source': source, 'optional': bool(el),
            'units': [unit_obj(int(k), t) for k, t in sorted(s['units'].items(), key=lambda x: int(x[0]))]})
add('data/raw_y2.json', '2019-20', 'aktu_syllabus_2nd_year.pdf', lambda c: 3 if c.startswith('KCS3') else 4 if c.startswith('KCS4') else None)
add('data/raw_y3.json', '2018-19', 'aktu_syllabus_3rd_year.pdf', lambda c: 5 if c in ('RCS-501','RCS-502','RCS-503','RIT-051','RIT-052','RCS-051','RCS-052') else 6,
    lambda c: 'Dept. Elective-1' if c in ('RIT-051','RIT-052','RCS-051','RCS-052') else 'Dept. Elective-2' if c in ('RIT-061','RIT-062','RCS-061','RCS-062') else None)
add('data/raw_y4.json', '2025-26', 'aktu_syllbus_4th_year.pdf', lambda c: 7,
    lambda c: 'Dept. Elective-IV' if c.startswith('BCS07') else None)
subjects.sort(key=lambda s: (s['semester'], s['optional'], s['code']))
json.dump({'note': 'Parsed from AKTU syllabus PDFs supplied by the user. Difficulty is a content-size estimate, not an official rating.', 'subjects': subjects},
          open('data/aktu_cse_syllabus.json', 'w'), indent=1, ensure_ascii=False)
tot = 0
for s in subjects:
    n = sum(len(u['topics']) for u in s['units']); tot += n
    print(f"Sem{s['semester']} {s['code']:9} {'OPT' if s['optional'] else '   '} {s['scheme']} {s['name'][:46]:46} units={len(s['units'])} topics={n}")
print('subjects', len(subjects), 'topics', tot)
