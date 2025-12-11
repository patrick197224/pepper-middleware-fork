module.exports = RED => {
    const sqlite3 = require("sqlite3").verbose();


    function SaveAppointmentNode(config) {
        RED.nodes.createNode(this, config);
        const node = this;


        const dbPath = config.dbpath || "appointments.db";
        const db = new sqlite3.Database(dbPath);


        // Ensure table exists
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
                node.error("Invalid appointment payload. Expected {date, time, patient, notes}");
                return;
            }


            const query = `INSERT INTO appointments (date, time, patient, notes) VALUES (?, ?, ?, ?)`;
            const params = [appt.date, appt.time, appt.patient, appt.notes || ""];


            db.run(query, params, function (err) {
                if (err) {
                    node.error("Database insert failed: " + err);
                    return;
                }


                msg.appointment_id = this.lastID;
                node.send(msg);
            });
        });


        node.on("close", () => {
            db.close();
        });
    }


    RED.nodes.registerType("save appointment", SaveAppointmentNode);
};