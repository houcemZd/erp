from flask import Flask, render_template, request, redirect, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB = "sibec.db"

# =========================
def connect():
    return sqlite3.connect(DB)

# =========================
def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock(
        ref TEXT PRIMARY KEY,
        qty INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS movement(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref TEXT,
        qty INTEGER,
        type TEXT,
        date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS production(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref TEXT,
        qty INTEGER,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
@app.route("/")
def home():
    return render_template("dashboard.html")

# =========================
@app.route("/stock")
def stock():

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM stock")
    data = cur.fetchall()

    conn.close()

    return render_template("stock.html", data=data)

# =========================
@app.route("/movement", methods=["GET", "POST"])
def movement():

    if request.method == "POST":

        ref = request.form["ref"]
        qty = int(request.form["qty"])
        typ = request.form["type"]

        conn = connect()
        cur = conn.cursor()

        cur.execute("SELECT qty FROM stock WHERE ref=?", (ref,))
        row = cur.fetchone()

        if row:
            new_qty = row[0] + qty if typ == "ENTREE" else row[0] - qty
            cur.execute("UPDATE stock SET qty=? WHERE ref=?", (new_qty, ref))
        else:
            cur.execute("INSERT INTO stock VALUES (?,?)", (ref, qty))

        cur.execute("""
        INSERT INTO movement(ref, qty, type, date)
        VALUES (?,?,?,?)
        """, (ref, qty, typ, datetime.now()))

        conn.commit()
        conn.close()

        return redirect("/movement")

    return render_template("movement.html")

# =========================
@app.route("/production", methods=["GET", "POST"])
def production():

    if request.method == "POST":

        ref = request.form["ref"]
        qty = int(request.form["qty"])

        conn = connect()
        cur = conn.cursor()

        cur.execute("SELECT qty FROM stock WHERE ref=?", (ref,))
        row = cur.fetchone()

        if row:
            cur.execute("UPDATE stock SET qty=? WHERE ref=?",
                        (row[0] + qty, ref))
        else:
            cur.execute("INSERT INTO stock VALUES (?,?)", (ref, qty))

        cur.execute("""
        INSERT INTO production(ref, qty, date)
        VALUES (?,?,?)
        """, (ref, qty, datetime.now()))

        conn.commit()
        conn.close()

        return redirect("/production")

    return render_template("production.html")

# =========================
@app.route("/history")
def history():

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT ref, qty, type, date FROM movement")
    mov = cur.fetchall()

    cur.execute("SELECT ref, qty, 'PRODUCTION', date FROM production")
    prod = cur.fetchall()

    conn.close()

    return render_template("history.html",
                           mov=mov,
                           prod=prod)

# =========================
@app.route("/kpi")
def kpi():

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM stock")
    stock_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM movement")
    movement_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM production")
    production_count = cur.fetchone()[0]

    conn.close()

    return render_template("kpi.html",
                           stock_count=stock_count,
                           movement_count=movement_count,
                           production_count=production_count)

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0",
            port=5000,
            debug=True)