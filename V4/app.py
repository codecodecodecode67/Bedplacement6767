# V4 - adds profile, search, delete features
from flask import Flask, request, redirect, url_for, send_from_directory
import sqlite3, os

app = Flask(__name__)
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ROOMSORTING.db'))

def get_conn():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row; return conn

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/profile')
def profile():
    return send_from_directory('.', 'profile.html')

@app.route('/search')
def search():
    q = request.args.get('q','').strip()
    conn = get_conn(); c = conn.cursor()
    patients = c.execute('SELECT * FROM patients WHERE name LIKE ?', (f'%{q}%',)).fetchall(); conn.close()
    out = '<h1>Search results</h1><ul>' + ''.join(f"<li>{p['patient_id']}: {p['name']} bed:{p['bed_id']} <a href='/delete_patient?id={p['patient_id']}'>[delete]</a></li>" for p in patients) + '</ul><p><a href="/">Back</a></p>'
    return out

@app.route('/delete_patient')
def delete_patient():
    pid = int(request.args.get('id',0))
    conn = get_conn(); c = conn.cursor(); c.execute('DELETE FROM patients WHERE patient_id=?',(pid,)); conn.commit(); conn.close(); return redirect(url_for('index'))

@app.route('/add_bed', methods=['POST'])
def add_bed():
    name = request.form.get('name','Bed'); ward = request.form.get('ward','General'); gender = request.form.get('gender','Any'); isolation = int(request.form.get('isolation','0') or 0)
    conn = get_conn(); c = conn.cursor(); c.execute('INSERT INTO beds (name, ward, gender, isolation) VALUES (?,?,?,?)', (name, ward, gender, isolation)); conn.commit(); conn.close(); return redirect(url_for('index'))

@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form.get('name','Patient'); age=int(request.form.get('age','0') or 0); gender=request.form.get('gender','M'); isolation=int(request.form.get('isolation','0') or 0); surgeon_pref=request.form.get('surgeon_pref','')
    conn = get_conn(); c = conn.cursor(); c.execute('INSERT INTO patients (name, age, gender, isolation, surgeon_pref) VALUES (?,?,?,?,?)', (name, age, gender, isolation, surgeon_pref)); pid=c.lastrowid; conn.commit(); conn.close()
    conn = get_conn(); c = conn.cursor(); taken = set([r['bed_id'] for r in c.execute('SELECT bed_id FROM patients WHERE bed_id IS NOT NULL').fetchall() if r['bed_id'] is not None])
    for b in c.execute('SELECT * FROM beds').fetchall():
        if b['bed_id'] in taken: continue
        if isolation and b['isolation']==0: continue
        if b['gender']!='Any' and b['gender']!=gender: continue
        c.execute('UPDATE patients SET bed_id=? WHERE patient_id=?', (b['bed_id'], pid)); conn.commit(); break
    conn.close(); return redirect(url_for('index'))

if __name__ == '__main__':
    print('Running V4 on http://127.0.0.1:5004')
    app.run(debug=True, port=5004)
