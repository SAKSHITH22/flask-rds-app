# app.py
from flask import Flask, render_template_string, request, redirect, session, url_for, jsonify
import mysql.connector
import bcrypt
import os
import time
import logging

# ----------------------------------------------------
# 🔧 Flask Configuration
# ----------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey123")

# ----------------------------------------------------
# 🧾 Logging Setup
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

# ----------------------------------------------------
# 🗄️ Database Connection Helper
# ----------------------------------------------------
def get_db_connection(retries=5, delay=3):
    """Attempt to connect to the MySQL database with retries."""
    host = os.environ.get("DB_HOST")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASS")
    database = os.environ.get("DB_NAME", "userdb")

    if not all([host, user, password, database]):
        logging.critical("❌ Missing required DB environment variables.")
        return None

    for attempt in range(1, retries + 1):
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                connect_timeout=10
            )
            logging.info(f"✅ Database connected successfully on attempt {attempt}")
            return conn
        except mysql.connector.Error as err:
            logging.error(f"❌ Database connection failed (Attempt {attempt}/{retries}): {err}")
            time.sleep(delay)

    logging.critical("🚨 All attempts to connect to database failed. Please check RDS settings.")
    return None

# ----------------------------------------------------
# 🧱 Ensure 'users' Table Exists
# ----------------------------------------------------
def init_db():
    """Create 'users' table if it doesn't exist."""
    conn = get_db_connection()
    if not conn:
        logging.error("❌ Cannot initialize DB — connection failed.")
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        """)
        conn.commit()
        logging.info("✅ Verified or created 'users' table in database.")
        return True
    except mysql.connector.Error as err:
        logging.error(f"❌ Error initializing DB: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

# ----------------------------------------------------
# 🧩 HTML Templates
# ----------------------------------------------------
login_html = """
<!DOCTYPE html>
<html>
<head>
<title>Login</title>
<style>
body {font-family: Arial; background:#f4f4f9; text-align:center;}
form {background:white; padding:25px; margin:auto; width:320px; border-radius:10px; box-shadow:0 0 10px gray;}
input, button {width:90%; margin:10px; padding:10px;}
a {color:#007BFF; text-decoration:none;}
</style>
</head>
<body>
<h2>🔐 Login</h2>
<form method="POST">
  <input type="text" name="username" placeholder="Username" required><br>
  <input type="password" name="password" placeholder="Password" required><br>
  <button type="submit">Login</button>
  <p>New user? <a href="/register">Register</a></p>
</form>
</body>
</html>
"""

register_html = """
<!DOCTYPE html>
<html>
<head>
<title>Register</title>
<style>
body {font-family: Arial; background:#f4f4f9; text-align:center;}
form {background:white; padding:25px; margin:auto; width:320px; border-radius:10px; box-shadow:0 0 10px gray;}
input, button {width:90%; margin:10px; padding:10px;}
</style>
</head>
<body>
<h2>📝 Create New Account</h2>
<form method="POST">
  <input type="text" name="username" placeholder="Username" required><br>
  <input type="password" name="password" placeholder="Password" required><br>
  <button type="submit">Register</button>
</form>
<p><a href="/">Back to Login</a></p>
</body>
</html>
"""

dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<title>Dashboard</title>
<style>
body {font-family: Arial; background:#f4f4f9; text-align:center;}
a {color:#007BFF; text-decoration:none;}
</style>
</head>
<body>
<h1>🎉 Welcome, {{username}}!</h1>
<p>You have successfully logged in.</p>
<a href="/logout">Logout</a>
</body>
</html>
"""

# ----------------------------------------------------
# 🧭 Routes
# ----------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    """User login route."""
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        if not conn:
            return "<h3>❌ Database connection failed. Check RDS or environment configuration.</h3>"

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "<h3>⚠️ Invalid username or password.</h3><a href='/'>Try again</a>"

    return render_template_string(login_html)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if len(username) < 3 or len(password) < 3:
            return "<h3>⚠️ Username and password must be at least 3 characters long.</h3><a href='/register'>Try again</a>"

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = get_db_connection()
        if not conn:
            return "<h3>❌ Database connection failed. Check RDS configuration.</h3>"

        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
            conn.commit()
            logging.info(f"👤 New user registered: {username}")
            return redirect('/')
        except mysql.connector.IntegrityError:
            return "<h3>⚠️ Username already exists.</h3><a href='/register'>Try Again</a>"
        except mysql.connector.Error as err:
            logging.error(f"❌ Database error during registration: {err}")
            return "<h3>❌ Failed to register user. Try again later.</h3>"
        finally:
            cursor.close()
            conn.close()

    return render_template_string(register_html)

@app.route('/dashboard')
def dashboard():
    """Protected user dashboard."""
    if 'username' in session:
        return render_template_string(dashboard_html, username=session['username'])
    return redirect('/')

@app.route('/logout')
def logout():
    """Logout route."""
    session.pop('username', None)
    return redirect('/')

# ----------------------------------------------------
# 🔍 Health & Debug Routes
# ----------------------------------------------------
@app.route('/testdb')
def testdb():
    """Quick test for DB connectivity."""
    conn = get_db_connection()
    if conn:
        conn.close()
        return "<h2>✅ Successfully connected to RDS MySQL!</h2>"
    return "<h2>❌ Failed to connect to database. Check pod logs or env vars.</h2>"

@app.route('/initdb')
def setup_database():
    """One-time setup route to create the 'users' table if missing."""
    if init_db():
        return "<h3>✅ Database initialized successfully.</h3>"
    return "<h3>❌ Database initialization failed.</h3>"

@app.route('/healthz')
def health():
    """Kubernetes health check endpoint."""
    return jsonify({"status": "ok"}), 200

# ----------------------------------------------------
# 🚀 Run the App
# ----------------------------------------------------
if __name__ == '__main__':
    logging.info("🚀 Starting Flask application...")
    # 🔧 Do not initialize DB before starting the server
    # init_db()  # comment this out
    app.run(host='0.0.0.0', port=5000)
