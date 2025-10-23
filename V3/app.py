# V3 - adds rule-based assignment (gender/isolation/surgeon preference)
from flask import Flask, request, redirect, url_for, send_from_directory
import sqlite3, os, random

app = Flask(__name__)
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ROOMSORTING.db'))
HTML = 'index.html'
RULES_HTML = 'rules.html'

def get_conn():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row; return conn

def init_extra():
    conn = get_conn(); c = conn.cursor()
    try:
        c.execute("ALTER TABLE patients ADD COLUMN surgeon_pref TEXT")
        conn.commit()
    except Exception:
        pass
    conn.close()

init_extra()

def assign_with_rules(pid):
    conn = get_conn(); c = conn.cursor(); p = c.execute('SELECT * FROM patients WHERE patient_id=?', (pid,)).fetchone()
    if not p: conn.close(); return
    taken = set([r['bed_id'] for r in c.execute('SELECT bed_id FROM patients WHERE bed_id IS NOT NULL').fetchall() if r['bed_id'] is not None])
    candidates = []
    for b in c.execute('SELECT * FROM beds').fetchall():
        if b['bed_id'] in taken: continue
        if p['isolation'] == 1 and b['isolation'] == 0: continue
        if b['gender'] != 'Any' and b['gender'] != p['gender']: continue
        if p.get('surgeon_pref') and p['surgeon_pref'] in (b['name'] or ''):
            candidates.insert(0, b)
        else:
            candidates.append(b)
    if candidates:
        chosen = random.choice(candidates)
        c.execute('UPDATE patients SET bed_id=? WHERE patient_id=?', (chosen['bed_id'], pid)); conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('.', HTML)

@app.route('/rules')
def rules():
    return send_from_directory('.', RULES_HTML)

@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form.get('name','Patient'); age=int(request.form.get('age','0') or 0); gender=request.form.get('gender','M'); isolation=int(request.form.get('isolation','0') or 0); surgeon_pref = request.form.get('surgeon_pref','')
    conn = get_conn(); c = conn.cursor(); c.execute('INSERT INTO patients (name, age, gender, isolation, surgeon_pref) VALUES (?,?,?,?,?)', (name, age, gender, isolation, surgeon_pref)); pid=c.lastrowid; conn.commit(); conn.close()
    assign_with_rules(pid); return redirect(url_for('index'))

@app.route('/add_bed', methods=['POST'])
def add_bed():
    name = request.form.get('name','Bed'); ward=request.form.get('ward','General'); gender=request.form.get('gender','Any'); isolation=int(request.form.get('isolation','0') or 0)
    conn = get_conn(); c = conn.cursor(); c.execute('INSERT INTO beds (name, ward, gender, isolation) VALUES (?,?,?,?)', (name, ward, gender, isolation)); conn.commit(); conn.close(); return redirect(url_for('index'))

if __name__ == '__main__':
    print('Running V3 on http://127.0.0.1:5003')
    app.run(debug=True, port=5003)
