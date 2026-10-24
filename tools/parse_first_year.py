"""Parse the AKTU 1st-year CSE stream syllabus (2026-27) into data/raw_y1.json."""
import re, json, pdfplumber
PDF = '/mnt/user-data/uploads/aktu_syllabus_1st_year.pdf'
THEORY = {  # first code -> (title, [(code, semester), ...])
 'AAS101E': ('Quantum Physics and Applications', [('AAS101E',1),('AAS201E',2)]),
 'AAS102D': ('Applied Chemistry for Smart Systems', [('AAS102D',1),('AAS202D',2)]),
 'AAS103D': ('Calculus and Linear Algebra', [('AAS103D',1)]),
 'AAS203D': ('Numerical Methods', [('AAS203D',2)]),
 'AEE101A': ('Fundamentals of Electrical Engineering', [('AEE101A',1),('AEE201A',2)]),
 'AEC101A': ('Fundamentals of Electronics Engineering', [('AEC101A',1),('AEC201A',2)]),
 'ACS101':  ('Programming Languages', [('ACS101',1)]),
 'ACS201':  ('Essentials of Data Structure', [('ACS201',2)]),
 'AAS104':  ('Introduction to Indian Knowledge System', [('AAS104',1),('AAS204',2)]),
 'AAS105':  ('Professional Communication and Technical Writing', [('AAS105',1),('AAS205',2)]),
 'AAI101':  ('Introduction to AI and Prompt Engineering', [('AAI101',1),('AAI201',2)]),
 'AME101A': ('Fundamentals of Mechanical Engineering', [('AME101A',1),('AME201A',2)]),
}
clean = lambda s: re.sub(r'\s+', ' ', (s or '').replace('\n', ' ')).strip()
out = {}; cur = None; in_content = False
with pdfplumber.open(PDF) as pdf:
    for pn, page in enumerate(pdf.pages):
        txt = page.extract_text() or ''
        m = re.search(r'Course Code\s+([A-Z]{3}\d{3}[A-Z]?)', txt)
        if m:
            cur = m.group(1); in_content = cur in ('AAS104', 'AAS105')  # these pages have no 'Course Content' label
        if cur not in THEORY: continue
        if 'Course Content' in txt: in_content = True
        if not in_content: continue
        for t in page.extract_tables():
            for row in t:
                cells = [clean(c) for c in row if c is not None and clean(c) != '']
                if cells and re.match(r'(Teaching|COs$|CO/PO|Evaluation)', cells[0]): in_content = False
                if not in_content: continue
                if len(cells) >= 3 and re.fullmatch(r'\d\.?', cells[0]) and re.fullmatch(r'\d{1,2}\s*%?', cells[-1]):
                    rawcells = [c for c in row if c and c.strip()]
                    desc = max(cells[1:-1], key=len)
                    first_line = clean(max(rawcells[1:-1], key=len).split('\n')[0]) if len(rawcells) > 2 else ''
                    lang = cells[1] if len(cells) == 4 and len(cells[1]) < 15 else None
                    out.setdefault(cur, {}).setdefault(int(cells[0].strip('.')), {'text': desc, 'first_line': first_line, 'weight': int(cells[-1].strip('% ')), 'lang': lang})
res = []
for first, (title, offered) in THEORY.items():
    units = out.get(first, {})
    res.append({'first_code': first, 'title': title, 'offered': offered, 'units': {str(k): v for k, v in sorted(units.items())}})
    print(first, title, '| units', sorted(units), '| weights', [units[k]['weight'] for k in sorted(units)])
json.dump(res, open('data/raw_y1.json', 'w'), indent=1, ensure_ascii=False)
