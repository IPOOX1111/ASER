from flask import Flask, request, jsonify, render_template
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def create_app():
    app = Flask(__name__, template_folder='templates')

    DB_PRIMARY = os.environ.get('DB_PRIMARY_HOST', 'postgres-primary')
    DB_REPLICA = os.environ.get('DB_REPLICA_HOST', 'postgres-replica')
    DB_USER = os.environ.get('POSTGRES_USER', 'voter')
    DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'voterpass')
    DB_NAME = os.environ.get('POSTGRES_DB', 'votingdb')

    def get_conn(read_only=False):
        host = DB_REPLICA if read_only else DB_PRIMARY
        conn = psycopg2.connect(host=host, database=DB_NAME, user=DB_USER, password=DB_PASS)
        return conn

    @app.route('/health')
    def health():
        return "OK", 200

    @app.route('/')
    def index():
        conn = get_conn(read_only=True)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, option_text, votes FROM options ORDER BY id;")
        options = cur.fetchall()
        cur.close(); conn.close()
        return render_template('index.html', options=options)

    @app.route('/vote', methods=['POST'])
    def vote():
        voter_id = request.form.get('voter_id')
        option_id = request.form.get('option_id')

        conn = get_conn(read_only=False)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM votes WHERE voter_id=%s", (voter_id,))
        if cur.fetchone():
            conn.rollback()
            cur.close(); conn.close()
            return "Already voted", 409

        cur.execute("INSERT INTO votes (voter_id, option_id) VALUES (%s,%s)",
                    (voter_id, option_id))
        cur.execute("UPDATE options SET votes = votes + 1 WHERE id=%s", (option_id,))
        conn.commit()
        cur.close(); conn.close()

        return "OK"

    @app.route('/results')
    def results():
        conn = get_conn(read_only=True)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM options ORDER BY id;")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify(rows)

    return app
