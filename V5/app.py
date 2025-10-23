# V5 - Final Version: Professional layout + login + 30s auto logout
from flask import Flask, request, redirect, url_for, send_from_directory, session, Response
import sqlite3, os, io, csv, time

app = Flask(__name__)
app.secret_key = "super_secure_secret_v5"

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ROOMSORTING.db'))

# ---------- Database Helpers ----------
def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS beds (
        bed_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        ward TEXT,
        gender TEXT,
        isolation INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        isolation INTEGER DEFAULT 0,
        surgeon_pref TEXT,
        bed_id INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS assign_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        bed_id INTEGER,
        ts INTEGER
    )""")
    conn.commit()
    conn.close()

init_db()

# ---------- Session Timeout ----------
@app.before_request
def check_session():
    allowed = {'login', 'static'}
    if request.endpoint not in allowed:
        if 'user' not in session:
            return redirect(url_for('login'))
        last_active = session.get('last_active', 0)
        now = int(time.time())
        if now - last_active > 30:  # 30-second timeout
            session.clear()
            return redirect(url_for('login'))
        session['last_active'] = now

# ---------- Routes ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Any username works
        username = request.form.get('username', 'User')
        session['user'] = username
        session['last_active'] = int(time.time())
        return redirect(url_for('home'))
    return send_from_directory('.', 'login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form.get('name', 'Patient')
    age = int(request.form.get('age', '0') or 0)
    gender = request.form.get('gender', 'M')
    isolation = int(request.form.get('isolation', '0') or 0)
    surgeon_pref = request.form.get('surgeon_pref', '')
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO patients (name, age, gender, isolation, surgeon_pref) VALUES (?, ?, ?, ?, ?)',
              (name, age, gender, isolation, surgeon_pref))
    pid = c.lastrowid

    # Auto assign bed
    taken = set([r['bed_id'] for r in c.execute('SELECT bed_id FROM patients WHERE bed_id IS NOT NULL') if r['bed_id']])
    chosen = None
    for b in c.execute('SELECT * FROM beds ORDER BY bed_id').fetchall():
        if b['bed_id'] in taken: continue
        if isolation and b['isolation'] == 0: continue
        if b['gender'] != 'Any' and b['gender'] != gender: continue
        chosen = b['bed_id']
        break

    if chosen:
        c.execute('UPDATE patients SET bed_id=? WHERE patient_id=?', (chosen, pid))
        c.execute('INSERT INTO assign_history (patient_id, bed_id, ts) VALUES (?, ?, ?)', (pid, chosen, int(time.time())))

    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/add_bed', methods=['POST'])
def add_bed():
    name = request.form.get('name', 'Bed')
    ward = request.form.get('ward', 'General')
    gender = request.form.get('gender', 'Any')
    isolation = int(request.form.get('isolation', '0') or 0)
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO beds (name, ward, gender, isolation) VALUES (?, ?, ?, ?)',
              (name, ward, gender, isolation))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/assignments')
def assignments():
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute('SELECT * FROM assign_history ORDER BY ts DESC').fetchall()
    conn.close()
    html = "<h1>Assignment History</h1><table border='1' cellpadding='5'><tr><th>ID</th><th>Patient</th><th>Bed</th><th>Time</th></tr>"
    for r in rows:
        html += f"<tr><td>{r['id']}</td><td>{r['patient_id']}</td><td>{r['bed_id']}</td><td>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r['ts']))}</td></tr>"
    html += "</table><p><a href='/'>Back</a></p>"
    return html

@app.route('/export')
def export():
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute('SELECT patient_id, name, age, gender, bed_id FROM patients').fetchall()
    conn.close()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Patient ID', 'Name', 'Age', 'Gender', 'Bed'])
    for r in rows:
        cw.writerow([r['patient_id'], r['name'], r['age'], r['gender'], r['bed_id']])
    output = si.getvalue()
    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=patients.csv'})

if __name__ == '__main__':
    print("Running Hospital Management V5 on http://127.0.0.1:5005")
    app.run(debug=True, port=5005)
