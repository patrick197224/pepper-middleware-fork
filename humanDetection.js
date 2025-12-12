module.exports = RED => {
    const { spawn } = require('child_process');
    const path = require('path');

    // Try to load EventPubSub (Pepper middleware dependency)
    // If not available, the node will work without it
    let EventPubSub = null;
    let events = null;

    try {
        EventPubSub = require('node-red-contrib-base/eventPubSub');
        events = new EventPubSub();
    } catch (err) {
        // EventPubSub not available - running in standalone Node-RED
        // Node will work without state reset functionality
    }

    function HumanDetection(config) {
        RED.nodes.createNode(this, config);
        const node = this;

        let pythonProcess = null;
        let waitingNode = null;
        let timeoutId = null;

        function cleanup() {
            if (pythonProcess) {
                pythonProcess.kill();
                pythonProcess = null;
            }
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
            waitingNode = null;
            node.status({});
        }

        function timeoutHandler() {
            if (waitingNode !== null) {
                const output = [null, { payload: RED._("humanDetection.timeoutOutput") }];
                node.send(output);
                cleanup();
            }
        }

        node.on("input", msg => {
            // Cleanup any existing process
            cleanup();

            waitingNode = msg;
            node.status({ fill: "blue", shape: "dot", text: "humanDetection.detecting" });

            // Set timeout if specified
            if (config.timeout && config.timeout > 0) {
                timeoutId = setTimeout(timeoutHandler, config.timeout * 1000);
            }

            // Path to Python script
            const scriptPath = path.join(__dirname, 'detect_human.py');

            // Check for virtual environment, prefer it over system python
            const fs = require('fs');
            const venvPython = path.join(__dirname, 'venv', 'bin', 'python3');
            const pythonCmd = fs.existsSync(venvPython) ? venvPython : 'python3';

            // Build Python command arguments
            const args = [
                scriptPath,
                '--method', config.method || 'mobilenet',
                '--confidence', (config.confidence || 50) / 100,
                '--camera', config.camera || '0'
            ];

            if (!config.visualFeedback) {
                args.push('--no-display');
            }

            if (config.detectEmotion) {
                args.push('--emotion');
            }

            // Spawn Python process
            try {
                pythonProcess = spawn(pythonCmd, args);

                let dataBuffer = '';

                pythonProcess.stdout.on('data', (data) => {
                    dataBuffer += data.toString();

                    // Process complete JSON lines
                    const lines = dataBuffer.split('\n');
                    dataBuffer = lines.pop(); // Keep incomplete line in buffer

                    lines.forEach(line => {
                        if (line.trim()) {
                            try {
                                const result = JSON.parse(line);

                                if (result.error) {
                                    node.error(result.error);
                                    node.status({ fill: "red", shape: "ring", text: "humanDetection.error" });
                                    cleanup();
                                } else if (result.status === 'ready') {
                                    node.status({ fill: "blue", shape: "dot", text: "humanDetection.ready" });
                                } else if (result.status === 'detected' && result.count > 0) {
                                    // Human detected!
                                    if (waitingNode) {
                                        const outputMsg = Object.assign({}, waitingNode);
                                        outputMsg.payload = {
                                            count: result.count,
                                            humans: result.humans,
                                            timestamp: result.timestamp
                                        };

                                        node.send([outputMsg, null]);
                                        node.status({ fill: "green", shape: "dot", text: `humanDetection.detected: ${result.count}` });
                                        cleanup();
                                    }
                                }
                            } catch (e) {
                                // Not JSON, might be debug output
                                node.log(line);
                            }
                        }
                    });
                });

                pythonProcess.stderr.on('data', (data) => {
                    node.warn(`Python error: ${data.toString()}`);
                });

                pythonProcess.on('close', (code) => {
                    if (code !== 0 && code !== null) {
                        node.error(`Python process exited with code ${code}`);
                        node.status({ fill: "red", shape: "ring", text: "humanDetection.error" });
                    }
                    cleanup();
                });

                pythonProcess.on('error', (err) => {
                    node.error(`Failed to start Python process: ${err.message}`);
                    node.status({ fill: "red", shape: "ring", text: "humanDetection.error" });
                    cleanup();
                });

            } catch (err) {
                node.error(`Error spawning Python: ${err.message}`);
                node.status({ fill: "red", shape: "ring", text: "humanDetection.error" });
                cleanup();
            }
        });

        node.on("close", (removed, done) => {
            cleanup();
            done();
        });

        // Subscribe to state reset events if EventPubSub is available (Pepper middleware)
        if (events && EventPubSub) {
            events.subscribe(EventPubSub.RESET_NODE_STATE, () => {
                cleanup();
            });
        }
    }

    RED.nodes.registerType("Human Detection", HumanDetection);
};
