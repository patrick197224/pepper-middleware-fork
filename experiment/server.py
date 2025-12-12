from flask import Flask, jsonify, request, send_from_directory
import sqlite3

DB_NAME = "appointments.db"
app = Flask(__name__)


def init_database():
    """Initialize the database with the correct schema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if table exists and has correct columns
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if table has the correct columns
        cursor.execute("PRAGMA table_info(appointments)")
        columns = [row[1] for row in cursor.fetchall()]
        required = {'id', 'date', 'time', 'patient', 'notes'}
        if not required.issubset(set(columns)):
            # Table exists but has wrong schema, drop and recreate
            cursor.execute("DROP TABLE appointments")
            conn.commit()

    # Create the appointments table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            patient TEXT NOT NULL,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()

# opens connection to sqlite database and returns connection object
def get_database():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # rows become hybrid of tuple and dcitionary, access via name and index
    return conn




# Patient view
@app.get("/")
def index_patient():
    return send_from_directory("static", "calendar_patient.html")

# Employee view
@app.get("/employee")
def index_employee():
    return send_from_directory("static", "calendar_employee.html")



#returns all appointments in a given date range
@app.get("/appointments")
def list_appointments_range():
    start = request.args.get("start")
    end = request.args.get("end")

    if not start or not end:
        return jsonify({"error": "Provide ?start=YYYY-MM-DD&end=YYYY-MM-DD"}), 400

    conn = get_database()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM appointments
        WHERE date BETWEEN ? AND ?
        ORDER BY date, time
    """, (start, end))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(rows)


# returns all appointments (employee view)
@app.get("/appointments/all")
def get_all_appointments():
    conn = get_database()
    rows = conn.execute("SELECT * FROM appointments ORDER BY date, time").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# create appointment
@app.post("/appointments")
def create_appointment():
    data = request.get_json()
    conn = get_database()
    conn.execute("""
        INSERT INTO appointments (date, time, patient, notes)
        VALUES (?, ?, ?, ?)
    """, (data["date"], data["time"], data["patient"], data.get("notes")))
    conn.commit()
    conn.close()
    return jsonify({"status": "created"}), 201


# update appointment
@app.put("/appointments/<int:appt_id>")
def update_appointment(appt_id):
    data = request.get_json()
    conn = get_database()
    conn.execute("""
        UPDATE appointments
        SET date=?, time=?, patient=?, notes=?
        WHERE id=?
    """, (data["date"], data["time"], data["patient"], data.get("notes"), appt_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})


# delete appointment
@app.delete("/appointments/<int:appt_id>")
def delete_appointment(appt_id):
    conn = get_database()
    conn.execute("DELETE FROM appointments WHERE id=?", (appt_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=5001, debug=True)
