from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from cryptography.fernet import Fernet
import sqlite3
import random
import string
import os

app = Flask(__name__)
app.secret_key = "rithika_mega_professional_2026"

# --- 1. Encryption Management ---
def load_key():
    if not os.path.exists("secret.key") or os.stat("secret.key").st_size == 0:
        key = Fernet.generate_key()
        with open("secret.key", "wb") as f: f.write(key)
    return open("secret.key", "rb").read()

cipher_suite = Fernet(load_key())

# --- 2. Database Handling ---
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # User Table
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, org TEXT, role TEXT, password TEXT)''')
        
        # Secure Chats Table - All necessary columns mapped correctly
        conn.execute('''CREATE TABLE IF NOT EXISTS secure_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            sender TEXT, 
            receiver TEXT, 
            handshake_msg TEXT, 
            actual_data TEXT, 
            secret_key TEXT, 
            dummy_text TEXT, 
            reply_msg TEXT, 
            reply_key TEXT,
            status TEXT DEFAULT 'Pending')''')
    print("Database Initialized Successfully!")

init_db()

# --- 3. Access Control & Auth ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        with get_db() as conn:
            conn.execute("INSERT INTO users (name, org, role, password) VALUES (?, ?, ?, ?)", 
                         (request.form['name'], request.form['org'], request.form['role'], request.form['password']))
            conn.commit()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if request.method == 'POST':
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE name=? AND password=? AND role=?", 
                                (request.form['name'], request.form['password'], role)).fetchone()
            if user:
                session['user'], session['org'], session['role'] = user['name'], user['org'], user['role']
                return jsonify({"status": "success"})
            else:
                return jsonify({"status": "error", "message": "Invalid Username or Password!"})
    return render_template('login.html', role=role)

# --- 4. Dashboard & Logic Flow ---

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('index'))
    with get_db() as conn:
        chats = conn.execute("SELECT * FROM secure_chats WHERE sender=? OR receiver=? ORDER BY id DESC", 
                             (session['user'], session['user'])).fetchall()
    return render_template('dashboard.html', chats=chats)

@app.route('/initiate_handshake', methods=['POST'])
def initiate_handshake():
    receiver = request.form['receiver']
    msg = request.form['message']
    with get_db() as conn:
        conn.execute("INSERT INTO secure_chats (sender, receiver, handshake_msg, status) VALUES (?, ?, ?, ?)", 
                     (session['user'], receiver, msg, 'Pending'))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/accept_request/<int:cid>')
def accept_request(cid):
    with get_db() as conn:
        conn.execute("UPDATE secure_chats SET status='Accepted' WHERE id=?", (cid,))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/push_data/<int:cid>', methods=['POST'])
def push_data(cid):
    raw_data = request.form['data']
    enc_data = cipher_suite.encrypt(raw_data.encode()).decode()
    s_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    dummy_options = [
        "Are you busy right now? 📩",
        "System Check: Connection Stable ✅",
        "Waiting for your response... 🕒",
        "Meeting scheduled for tomorrow 📅",
        "Urgent: Please check the logs 🚨",
        "Data Packet #0017-X Transferred",
        "Did you eat lunch? 🍲",
        "New security update available 🛡️",
        "File sharing initiated successfully",
        "Hello! Are you there? 👋"
    ]
    dummy = random.choice(dummy_options)
    
    with get_db() as conn:
        conn.execute("UPDATE secure_chats SET actual_data=?, secret_key=?, dummy_text=?, status='Data Sent' WHERE id=?", 
                     (enc_data, s_key, dummy, cid))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/send_reply/<int:cid>', methods=['POST'])
def send_reply(cid):
    reply_raw = request.form['reply_text']
    enc_reply = cipher_suite.encrypt(reply_raw.encode()).decode()
    r_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    with get_db() as conn:
        conn.execute("UPDATE secure_chats SET reply_msg=?, reply_key=?, status='Replied' WHERE id=?", 
                     (enc_reply, r_key, cid))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/get_key/<int:cid>')
def get_key(cid):
    with get_db() as conn:
        row = conn.execute("SELECT secret_key, reply_key, status FROM secure_chats WHERE id=?", (cid,)).fetchone()
    key = row['reply_key'] if row['status'] == 'Replied' else row['secret_key']
    return jsonify({"key": key})

@app.route('/unlock_and_read', methods=['POST'])
def unlock_and_read():
    cid = request.form['id']
    user_key = request.form['key']
    with get_db() as conn:
        row = conn.execute("SELECT actual_data, secret_key, reply_msg, reply_key, status FROM secure_chats WHERE id=?", (cid,)).fetchone()
        
        if row['status'] == 'Replied' and row['reply_key'] == user_key:
            dec = cipher_suite.decrypt(row['reply_msg'].encode()).decode()
            conn.execute("UPDATE secure_chats SET status='Read' WHERE id=?", (cid,))
            conn.commit()
            return jsonify({"status": "success", "msg": dec})
        elif row['secret_key'] == user_key:
            dec = cipher_suite.decrypt(row['actual_data'].encode()).decode()
            conn.execute("UPDATE secure_chats SET status='Read' WHERE id=?", (cid,))
            conn.commit()
            return jsonify({"status": "success", "msg": dec})
            
    return jsonify({"status": "error", "message": "Invalid Key!"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)