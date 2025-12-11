from flask import Flask, jsonify, request
import sqlite3

DB_NAME = "appointments.db"
app = Flask(__name__)

# opens connection to sqlite database and returns connection object
def get_database():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # rows become hybrid of tuple and dcitionary, access via name and index
    return conn

#returns all appointments in a given date range
@app.get("/appointments")
def list_appointments():

    # Extract date range from query string
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_database()
    cursor = conn.cursor()

    # query all apppointments between provided dates
    cursor.execute("""
        SELECT id, date, time, patient, notes
        FROM appointments
        WHERE date BETWEEN ? AND ?
        ORDER BY date, time;
    """, (start, end))

    # convert sqlite Row object into dictionary
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5001, debug=True)