# V2 - adds login and 30s auto-logout; builds on V1
from flask import Flask, request, redirect, url_for, session, send_from_directory
import sqlite3, os, time

app = Flask(__name__)
app.secret_key = 'v2_secret'
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ROOMSORTING.db'))
HTML = 'index.html'

def get_conn():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row; return conn

@app.before_request
def refresh_session():
    if request.endpoint in ('login', 'static'): return
    if 'user' not in session:
        return redirect(url_for('login'))
    last = session.get('last_active', 0)
    now = int(time.time())
    if now - last > 30:
        session.clear()
        return redirect(url_for('login'))
    session['last_active'] = now

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('username','user')
        session['last_active'] = int(time.time())
        return redirect(url_for('index'))
    return send_from_directory('.', 'login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/')
def index():
    return send_from_directory('.', HTML)

@app.route('/data')
def data():
    conn = get_conn(); c = conn.cursor()
    beds = c.execute('SELECT * FROM beds').fetchall()
    pats = c.execute('SELECT * FROM patients').fetchall(); conn.close()
    html = f"<h1>Hospital V2 - Welcome {session.get('user')}</h1>"
    html += '<p><a href="/logout">Logout</a></p>'
    html += '<h2>Beds</h2><ul>' + ''.join(f"<li>{b['bed_id']}: {b['name']} (ward:{b['ward']})</li>" for b in beds) + '</ul>'
    html += '<h2>Patients</h2><ul>' + ''.join(f"<li>{p['patient_id']}: {p['name']} bed:{p['bed_id']}</li>" for p in pats) + '</ul>'
    html += '<p><a href="/">Back</a></p>'
    return html

@app.route('/add_bed', methods=['POST'])
def add_bed():
    if 'user' not in session: return redirect(url_for('login'))
    name = request.form.get('name','Bed'); ward = request.form.get('ward','General'); gender = request.form.get('gender','Any'); isolation = int(request.form.get('isolation','0') or 0)
    conn = get_conn(); c = conn.cursor(); c.execute('INSERT INTO beds (name, ward, gender, isolation) VALUES (?,?,?,?)', (name, ward, gender, isolation)); conn.commit(); conn.close()
    return redirect(url_for('index'))

@app.route('/add_patient', methods=['POST'])
def add_patient():
    if 'user' not in session: return redirect(url_for('login'))
    name = request.form.get('name','Patient'); age=int(request.form.get('age','0') or 0); gender = request.form.get('gender','M'); isolation=int(request.form.get('isolation','0') or 0)
    conn = get_conn(); c = conn.cursor(); c.execute('INSERT INTO patients (name, age, gender, isolation) VALUES (?,?,?,?)', (name,age,gender,isolation)); pid = c.lastrowid; conn.commit(); conn.close()
    conn = get_conn(); c = conn.cursor(); taken = set([r['bed_id'] for r in c.execute('SELECT bed_id FROM patients WHERE bed_id IS NOT NULL').fetchall() if r['bed_id'] is not None])
    for b in c.execute('SELECT * FROM beds ORDER BY bed_id').fetchall():
        if b['bed_id'] not in taken:
            c.execute('UPDATE patients SET bed_id=? WHERE patient_id=?', (b['bed_id'], pid)); conn.commit(); break
    conn.close(); return redirect(url_for('index'))

if __name__ == '__main__':
    print('Running V2 on http://127.0.0.1:5002')
    app.run(debug=True, port=5002)
