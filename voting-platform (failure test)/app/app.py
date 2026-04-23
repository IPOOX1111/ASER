from flask import Flask, request, redirect, url_for, render_template_string, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "simple-key"

DB_HOSTS = os.getenv("DB_HOSTS").split(",")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
SERVER_NAME = os.getenv("SERVER_NAME")

# ---------------- DB FAILOVER ----------------
def get_db():
    for host in DB_HOSTS:
        try:
            return mysql.connector.connect(
                host=host.strip(),
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connection_timeout=2
            )
        except:
            continue
    raise Exception("No database available")

# ---------------- HTML ----------------
LOGIN_HTML = """
<h2>Login</h2>
<form method="post">
Username <input name="username" required><br><br>
Password <input name="password" type="password" required><br><br>
<button>Login</button>
</form>
<p style="color:red">{{ error }}</p>
<a href="/register">Register</a>
<p><small>Server: {{ server }}</small></p>
"""

REGISTER_HTML = """
<h2>Register</h2>
<form method="post">
Username <input name="username" required><br><br>
Password <input name="password" type="password" required><br><br>
<button>Register</button>
</form>
<p style="color:red">{{ error }}</p>
<a href="/login">Login</a>
<p><small>Server: {{ server }}</small></p>
"""

VOTE_HTML = """
<h2>Vote</h2>
<p>User: {{ user }}</p>

{% if voted %}
<p style="color:green">You already voted</p>
{% else %}
<form method="post">
<button name="choice" value="A">Vote A</button>
<button name="choice" value="B">Vote B</button>
</form>
{% endif %}

<a href="/results">Results</a> |
<a href="/logout">Logout</a>
<p><small>Server: {{ server }}</small></p>
"""

RESULT_HTML = """
<h2>Results</h2>
<p>A: {{ a }} votes ({{ pa }}%)</p>
<p>B: {{ b }} votes ({{ pb }}%)</p>
<p>Total: {{ t }}</p>
<a href="/vote">Back</a>
<p><small>Server: {{ server }}</small></p>
"""

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            db = get_db()
            cur = db.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (request.form["username"], request.form["password"])
            )
            user = cur.fetchone()
            cur.close(); db.close()

            if user:
                session["user"] = user["username"]
                return redirect("/vote")
            return render_template_string(LOGIN_HTML, error="Invalid login", server=SERVER_NAME)
        except:
            return "<h3>Database unavailable</h3>"

    return render_template_string(LOGIN_HTML, error="", server=SERVER_NAME)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                "INSERT INTO users VALUES (NULL,%s,%s)",
                (request.form["username"], request.form["password"])
            )
            db.commit()
            cur.close(); db.close()
            return redirect("/login")
        except:
            return render_template_string(
                REGISTER_HTML,
                error="User exists or DB down",
                server=SERVER_NAME
            )

    return render_template_string(REGISTER_HTML, error="", server=SERVER_NAME)

@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "user" not in session:
        return redirect("/login")

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM votes WHERE username=%s", (session["user"],))
        voted = cur.fetchone()

        if request.method == "POST" and not voted:
            cur.execute(
                "INSERT INTO votes(username,choice) VALUES (%s,%s)",
                (session["user"], request.form["choice"])
            )
            db.commit()

        cur.execute("SELECT * FROM votes WHERE username=%s", (session["user"],))
        voted = cur.fetchone()

        cur.close(); db.close()
        return render_template_string(
            VOTE_HTML,
            user=session["user"],
            voted=bool(voted),
            server=SERVER_NAME
        )
    except:
        return "<h3>Database unavailable</h3>"

@app.route("/results")
def results():
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT choice, COUNT(*) FROM votes GROUP BY choice")
        data = cur.fetchall()
        cur.close(); db.close()

        a = b = 0
        for c, n in data:
            if c == "A": a = n
            if c == "B": b = n

        t = a + b
        pa = round(a / t * 100, 1) if t else 0
        pb = round(b / t * 100, 1) if t else 0

        return render_template_string(
            RESULT_HTML,
            a=a, b=b, t=t, pa=pa, pb=pb, server=SERVER_NAME
        )
    except:
        return "<h3>Database unavailable</h3>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/health")
def health():
    try:
        db = get_db()
        db.close()
        return "OK", 200
    except:
        return "FAIL", 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
