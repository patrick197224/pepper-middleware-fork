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
        required_columns = {'id', 'date', 'time', 'patient', 'notes'}
        if not required_columns.issubset(set(columns)):
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



# homepage with two buttons to route to either patient or employee view
@app.get("/")
def home():
    """Homepage of the robot receptionist."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Appointment Calendar</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding-top: 60px;
            }
            h1 {
                margin-bottom: 40px;
            }
            a.button {
                display: inline-block;
                padding: 15px 30px;
                margin: 15px;
                font-size: 20px;
                color: white;
                background: #4CAF50;
                border-radius: 8px;
                text-decoration: none;
            }
            a.button:hover {
                background: #45a049;
            }
            a.secondary {
                background: #2196F3;
            }
            a.secondary:hover {
                background: #1E88E5;
            }
        </style>
    </head>
    <body>
        <h1>Select Calendar View</h1>
        <a class="button secondary" href="/patient">Patient View</a>
        <a class="button" href="/employee">Employee View</a>
    </body>
    </html>
    """

@app.get("/employee")
def employee_calendar():
    return send_from_directory("static", "calendar_employee.html")

@app.get("/patient")
def patient_calendar():
    return send_from_directory("static", "calendar_patient.html")


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
    init_database()
    app.run(host="0.0.0.0", port=5001, debug=True)
