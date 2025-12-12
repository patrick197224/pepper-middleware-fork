module.exports = RED => {
    const sqlite3 = require("sqlite3").verbose();

    function RemoveAppointmentNode(config) {
        RED.nodes.createNode(this, config);
        const node = this;

        const dbPath = config.dbpath || "appointments.db";
        const db = new sqlite3.Database(dbPath);

        
        db.run(`CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            patient TEXT NOT NULL,
            notes TEXT
        );`);

        node.on("input", msg => {
            const appt = msg.payload;

            if (!appt || !appt.date || !appt.time || !appt.patient) {
                node.error("Invalid payload. Expected {date, time, patient}");
                return;
            }

            const query = `
                DELETE FROM appointments
                WHERE date = ? AND time = ? AND patient = ?
            `;

            const params = [appt.date, appt.time, appt.patient];

            db.run(query, params, function (err) {
                if (err) {
                    node.error("Appointment deletion failed: " + err);
                    return;
                }

                msg.deleted_count = this.changes;  
                node.send(msg);
            });
        });

        node.on("close", () => {
            db.close();
        });
    }

    RED.nodes.registerType("remove appointment", RemoveAppointmentNode);
};
