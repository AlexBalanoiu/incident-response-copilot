# target-app/app.py
from flask import Flask, jsonify
import pymysql
import os

app = Flask(__name__)
_leak_store = []  # intentional unbounded growth target for memory_leak scenario

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "mysql"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "changeme"),
    "database": os.environ.get("DB_NAME", "appdb"),
}


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/debug/leak")
def leak():
    # each call appends ~1MB, never freed - drives memory_leak scenario
    _leak_store.append(bytearray(1024 * 1024))
    return jsonify(leaked_mb=len(_leak_store))


@app.route("/db-query")
def db_query():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return jsonify(status="ok")
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)