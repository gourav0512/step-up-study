// Loads the real AKTU CSE syllabus (parsed from the official PDFs) from data/aktu_cse_syllabus.json.
const fs = require('fs');
const path = require('path');
const FILE = path.join(__dirname, '..', 'data', 'aktu_cse_syllabus.json');

function loadSyllabus(db, { removeDemo = true } = {}) {
  const data = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  const insSub = db.prepare(`INSERT INTO subjects(code,name,semester,academic_session,is_demo,is_optional,source_url,verification_status)
    VALUES (@code,@name,@semester,@scheme,0,@optional,@source,'unverified')
    ON CONFLICT(code,semester) DO UPDATE SET name=excluded.name, academic_session=excluded.academic_session,
      is_optional=excluded.is_optional, source_url=excluded.source_url, is_demo=0`);
  const insUnit = db.prepare(`INSERT INTO syllabus_units(subject_id,unit_no,title) VALUES (?,?,?)
    ON CONFLICT(subject_id,unit_no) DO UPDATE SET title=excluded.title`);
  const insTopic = db.prepare(`INSERT INTO topics(unit_id,subject_id,name,difficulty,details) VALUES (?,?,?,?,?)
    ON CONFLICT(unit_id,name) DO UPDATE SET difficulty=excluded.difficulty, details=excluded.details`);
  let topics = 0;
  db.transaction(() => {
    if (removeDemo) db.prepare('DELETE FROM subjects WHERE is_demo=1').run();
    for (const s of data.subjects) {
      insSub.run({ code: s.code, name: s.name, semester: s.semester, scheme: s.scheme, optional: s.optional ? 1 : 0, source: s.source });
      const sid = db.prepare('SELECT id FROM subjects WHERE code=? AND semester=?').get(s.code, s.semester).id;
      for (const u of s.units) {
        insUnit.run(sid, u.no, u.title);
        const uid = db.prepare('SELECT id FROM syllabus_units WHERE subject_id=? AND unit_no=?').get(sid, u.no).id;
        for (const t of u.topics) { insTopic.run(uid, sid, t.name, t.difficulty, t.details); topics++; }
      }
    }
  })();
  return { subjects: data.subjects.length, topics };
}

module.exports = { loadSyllabus };

if (require.main === module) {
  require('dotenv').config();
  const db = require('./db');
  console.log('Loaded real AKTU syllabus:', loadSyllabus(db));
}
