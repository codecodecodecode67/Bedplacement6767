# V1 - Basic: add/view beds & patients, simple auto-assign (first free bed)
from flask import Flask, request, redirect, url_for, send_from_directory
import sqlite3, os

app = Flask(__name__)
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ROOMSORTING.db'))
HTML = 'index.html'

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS beds (bed_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, ward TEXT, gender TEXT, isolation INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS patients (patient_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER, gender TEXT, isolation INTEGER DEFAULT 0, bed_id INTEGER)')
    conn.commit(); conn.close()

init_db()

def auto_assign(pid):
    conn = get_conn(); c = conn.cursor()
    taken = set([r['bed_id'] for r in c.execute('SELECT bed_id FROM patients WHERE bed_id IS NOT NULL').fetchall() if r['bed_id'] is not None])
    for b in c.execute('SELECT bed_id FROM beds ORDER BY bed_id').fetchall():
        if b['bed_id'] not in taken:
            c.execute('UPDATE patients SET bed_id=? WHERE patient_id=?', (b['bed_id'], pid))
            conn.commit()
            break
    conn.close()

@app.route('/')
def index():
    return send_from_directory('.', HTML)

@app.route('/data')
def data():
    conn = get_conn(); c = conn.cursor()
    beds = c.execute('SELECT * FROM beds').fetchall()
    patients = c.execute('SELECT * FROM patients').fetchall()
    conn.close()
    html = '<h1>Hospital V1 - Beds & Patients</h1>'
    html += '<h2>Beds</h2><ul>' + ''.join(f"<li>{b['bed_id']}: {b['name']} (ward:{b['ward']} gender:{b['gender']} iso:{b['isolation']})</li>" for b in beds) + '</ul>'
    html += '<h2>Patients</h2><ul>' + ''.join(f"<li>{p['patient_id']}: {p['name']} age:{p['age']} gender:{p['gender']} bed:{p['bed_id']}</li>" for p in patients) + '</ul>'
    html += '<p><a href="/">Back</a></p>'
    return html

@app.route('/add_bed', methods=['POST'])
def add_bed():
    name = request.form.get('name', 'Bed')
    ward = request.form.get('ward', 'General')
    gender = request.form.get('gender', 'Any')
    isolation = int(request.form.get('isolation', '0') or 0)
    conn = get_conn(); c = conn.cursor()
    c.execute('INSERT INTO beds (name, ward, gender, isolation) VALUES (?, ?, ?, ?)', (name, ward, gender, isolation))
    conn.commit(); conn.close()
    return redirect(url_for('index'))

@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form.get('name', 'Patient')
    age = int(request.form.get('age', '0') or 0)
    gender = request.form.get('gender', 'M')
    isolation = int(request.form.get('isolation', '0') or 0)
    conn = get_conn(); c = conn.cursor()
    c.execute('INSERT INTO patients (name, age, gender, isolation) VALUES (?, ?, ?, ?)', (name, age, gender, isolation))
    pid = c.lastrowid; conn.commit(); conn.close()
    auto_assign(pid)
    return redirect(url_for('index'))

if __name__ == '__main__':
    print('Running V1 on http://127.0.0.1:5001')
    app.run(debug=True, port=5001)
