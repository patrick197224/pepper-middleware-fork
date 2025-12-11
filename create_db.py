import sqlite3

DB_NAME = "appointments.db"

# creates appointment table if not already existing
def create_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, -- YYY-MM-DD
            time TEXT NOT NULL, -- HH:MM
            patient TEXT NOT NULL,
            notes TEXT
        );
    """)

    conn.commit()

def insert_appointments(conn):
    # example appointments for now
    sample_data= [
        ("2026-01-05", "09:00", "Hans Werner", "Check-up"),
        ("2026-01-06", "08:00", "Peter Müller", "Follow-up"),
        ("2026-01-07", "11:00", "Christian Schmitt", "Consultation"),
        ("2026-01-08", "13:00", "Hans Peter", "Consultation"),
        ("2026-01-08", "14:00", "Tom Wendt", "Follow-up"),
        ("2026-01-09", "13:00", "Peter Schneider", "Consultation")
    ]

    cursor = conn.cursor()
    # inserting each appointment into teh table
    for date, time, patient, notes in sample_data:
        cursor.execute("""
            INSERT INTO appointments (date, time, patient, notes)
            VALUES (?, ?, ?, ?);
        """, (date, time, patient, notes))

    conn.commit()

def main():
    conn = sqlite3.connect(DB_NAME)
    create_table(conn)
    insert_appointments(conn)
    print("database created: ", DB_NAME)
    conn.close()

if __name__ == "__main__":
    main()