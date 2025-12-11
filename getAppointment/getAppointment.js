module.exports = RED => {
    const sqlite3 = require("sqlite3").verbose();


    function GetAppointmentNode(config) {
        RED.nodes.createNode(this, config);
        const node = this;


        const dbPath = config.dbpath || "appointments.db";
        const db = new sqlite3.Database(dbPath);


        node.on("input", msg => {
            const { patient, date, time } = msg.payload;


            if (!patient || !date || !time) {
                node.error("Invalid payload. Expected {patient, date, time}");
                return;
            }


            const query = `SELECT * FROM appointments WHERE patient = ? AND date = ? AND time = ?`;
            const params = [patient, date, time];


            db.get(query, params, (err, row) => {
                if (err) {
                    node.error("Database query failed: " + err);
                    return;
                }


                msg.payload = row || null; // null if not found
                node.send(msg);
            });
        });


        node.on("close", () => {
            db.close();
        });
    }


    RED.nodes.registerType("get appointment", GetAppointmentNode);
};