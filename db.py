import os

import mysql.connector
from dotenv import load_dotenv
from flask import g


load_dotenv()


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("MYSQLHOST") or os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("MYSQLPORT") or os.getenv("DB_PORT", 3306)),
            user=os.getenv("MYSQLUSER") or os.getenv("DB_USER", ""),
            password=os.getenv("MYSQLPASSWORD") or os.getenv("DB_PASSWORD", ""),
            database=os.getenv("MYSQLDATABASE") or os.getenv("DB_NAME", "")
        )
    return g.db


def query(sql, params=None, one=False):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    rows = cursor.fetchall()
    cursor.close()
    return rows[0] if one and rows else rows


def execute(sql, params=None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return last_id


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
