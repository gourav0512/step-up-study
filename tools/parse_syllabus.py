"""Parse AKTU syllabus PDFs (2nd, 3rd, 4th year formats) into data/aktu_syllabus_raw.json.
Usage: python tools/parse_syllabus.py <pdf> <label>  (prints summary; writes data/raw_<label>.json)"""
import sys, re, json, pdfplumber

ROM = {'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6}
HEAD = re.compile(r'^\s*(?:(R[A-Z]{2,3}-\d{3}|[A-Z]{3}\d{3})\s*[:\-]\s*(.+?)|(.+?)\s*\(\s*([A-Z]{3}-?\d{3})\s*\))\s*(?:\d-\d-\d|3.?[-‐]\d[-‐]\d)?\s*$')

def clean(s): return re.sub(r'\s+',' ',(s or '').replace('\n',' ')).strip()

def parse(pdf_path):
    subjects = []; cur = None
    with pdfplumber.open(pdf_path) as pdf:
        for pn, page in enumerate(pdf.pages):
            lines = [l.strip() for l in (page.extract_text() or '').split('\n')]
            for l in lines:
                m = HEAD.match(l)
                if m and 'LAB' not in l.upper():
                    code = m.group(1) or m.group(4); name = clean(m.group(2) or m.group(3))
                    if len(name) > 3 and not name.lower().startswith(('course','unit')):
                        cur = {'code': code.replace('--','-'), 'name': name, 'page': pn+1, 'units': {}}
                        subjects.append(cur)
            for t in page.extract_tables():
                for row in t:
                    cells = [clean(c) for c in row if c is not None]
                    cells = [c for c in cells if c != '']
                    if len(cells) >= 2 and cells[0] in ROM and len(cells[1]) > 25 and cur is not None:
                        cur['units'].setdefault(ROM[cells[0]], cells[1])
    return [s for s in subjects if s['units']]

if __name__ == '__main__':
    subs = parse(sys.argv[1])
    json.dump(subs, open(f'data/raw_{sys.argv[2]}.json','w'), indent=1, ensure_ascii=False)
    for s in subs: print(s['code'], '|', s['name'], '| p', s['page'], '| units', sorted(s['units']))
