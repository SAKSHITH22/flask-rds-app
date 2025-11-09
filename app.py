# app.py
from flask import Flask, render_template_string, request, redirect, session, url_for, jsonify
import mysql.connector
import bcrypt
import os
import time
import logging

# Flask Configuration
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey123")

# Logging Setup
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

# Database Connection Helper
def get_db_connection(retries=5, delay=3):
    """Attempt to connect to the MySQL database with retries."""
    host = os.environ.get("DB_HOST", "sakshith-mysql.cu9gmuueigg2.us-east-1.rds.amazonaws.com")
    user = os.environ.get("DB_USER", "sakshith")
    password = os.environ.get("DB_PASS", None)
    database = os.environ.get("DB_NAME", "userdb")

    if not password:
        logging.critical("DB_PASS environment variable not set")
        return None

    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                connect_timeout=10
            )
            logging.info("Database connected successfully")
            return conn
        except mysql.connector.Error as err:
            logging.error(f"Database connection failed (Attempt {attempt+1}/{retries}): {err}")
            time.sleep(delay)
    logging.critical("All attempts to connect to database failed.")
    return None

# HTML Templates (kept minimal)
login_html = """..."""   # keep your HTML strings here (omitted for brevity)
register_html = """..."""
dashboard_html = """..."""

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if not conn:
            return "<h3>Database connection failed. Check server logs or RDS configuration.</h3>"

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "<h3>Invalid username or password.</h3><a href='/'>Try again</a>"

    return render_template_string(login_html)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = get_db_connection()
        if not conn:
            return "<h3>Database connection failed. Check server logs or RDS configuration.</h3>"

        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
            conn.commit()
            logging.info(f"New user registered: {username}")
            return redirect('/')
        except mysql.connector.IntegrityError:
            return "<h3>Username already exists.</h3><a href='/register'>Try Again</a>"
        finally:
            cursor.close()
            conn.close()

    return render_template_string(register_html)

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template_string(dashboard_html, username=session['username'])
    else:
        return redirect('/')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/testdb')
def testdb():
    conn = get_db_connection()
    if conn:
        conn.close()
        return "<h2>Successfully connected to RDS MySQL!</h2>"
    else:
        return "<h2>Failed to connect to database. Check pod logs.</h2>"

@app.route('/healthz')
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
