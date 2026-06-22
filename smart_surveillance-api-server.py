from flask import Flask, jsonify, request, Response, send_file
from datetime import datetime
import csv
import io
import random
import threading
import time

class AlertManager:
    def __init__(self):
        self.alerts = []

    def add_alert(self, event_type, message, severity="low"):
        alert = {
            "id": len(self.alerts) + 1,
            "event_type": event_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.alerts.append(alert)

    def latest(self, limit=10):
        return self.alerts[-limit:]

    def all(self):
        return self.alerts

class CameraManager:
    def __init__(self):
        self.cameras = [
            {"id": 1, "name": "Entrance Gate", "status": "online"},
            {"id": 2, "name": "Platform 1", "status": "online"},
            {"id": 3, "name": "Parking Zone", "status": "offline"},
        ]

    def get_all(self):
        return self.cameras

shared_state = {
    "running": True,
    "detector_mode": "yolo",
    "people_count": 0,
    "fps": 0,
    "cpu_usage": 0,
    "memory_usage": 0,
}


def monitor_system(alert_manager):
    while True:
        shared_state["people_count"] = random.randint(0, 50)
        shared_state["fps"] = round(random.uniform(24, 60), 2)
        shared_state["cpu_usage"] = random.randint(20, 90)
        shared_state["memory_usage"] = random.randint(30, 85)

        if shared_state["people_count"] > 40:
            alert_manager.add_alert(
                "Crowd Detection",
                "High crowd density detected",
                "high"
            )

        time.sleep(3)


def create_api(shared_state, alert_manager, camera_manager):
    app = Flask(__name__)

    API_KEY = "secret123"

    def authenticate():
        key = request.headers.get("X-API-KEY")
        return key == API_KEY

    @app.before_request
    def check_api_key():
        public_routes = ["/", "/health"]
        if request.path not in public_routes:
            if not authenticate():
                return jsonify({"error": "Unauthorized"}), 401

    @app.get("/")
    def index():
        latest_alerts = alert_manager.latest(limit=10)

        alerts_html = "".join(
            [
                f"""
                <li>
                    <strong>{alert['event_type']}</strong> -
                    {alert['message']}
                    <br>
                    Severity: {alert['severity']}
                    <br>
                    <small>{alert['timestamp']}</small>
                </li>
                """
                for alert in latest_alerts
            ]
        ) or "<li>No alerts yet.</li>"

        return f"""
        <html>
        <head>
            <title>Smart Surveillance Dashboard</title>
            <style>
                body {{
                    background:#111;
                    color:white;
                    font-family:Arial;
                    padding:30px;
                }}
                .grid {{
                    display:grid;
                    grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
                    gap:20px;
                }}
                .card {{
                    background:#222;
                    padding:20px;
                    border-radius:15px;
                }}
            </style>
        </head>
        <body>
            <h1>AI Surveillance Dashboard</h1>

            <div class="grid">
                <div class="card">
                    <h2>System Status</h2>
                    <p>Running: {shared_state['running']}</p>
                    <p>Detector: {shared_state['detector_mode']}</p>
                    <p>People Count: {shared_state['people_count']}</p>
                    <p>FPS: {shared_state['fps']}</p>
                    <p>CPU: {shared_state['cpu_usage']}%</p>
                    <p>Memory: {shared_state['memory_usage']}%</p>
                </div>

                <div class="card">
                    <h2>Recent Alerts</h2>
                    <ul>{alerts_html}</ul>
                </div>
            </div>
        </body>
        </html>
        """

    @app.get("/health")
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })


    @app.get("/api/status")
    def status():
        return jsonify(shared_state)

    @app.get("/api/alerts")
    def alerts():
        severity = request.args.get("severity")
        alerts = alert_manager.all()

        if severity:
            alerts = [
                a for a in alerts if a["severity"] == severity
            ]

        return jsonify(alerts)

    @app.post("/api/alerts")
    def add_alert():
        data = request.json

        alert_manager.add_alert(
            data["event_type"],
            data["message"],
            data.get("severity", "low")
        )

        return jsonify({"message": "Alert added"})

    @app.get("/api/cameras")
    def cameras():
        return jsonify(camera_manager.get_all())

    @app.get("/api/stats")
    def stats():
        alerts = alert_manager.all()

        stats = {
            "total_alerts": len(alerts),
            "critical_alerts": len(
                [a for a in alerts if a["severity"] == "critical"]
            ),
            "high_alerts": len(
                [a for a in alerts if a["severity"] == "high"]
            ),
        }

        return jsonify(stats)

    @app.get("/api/export")
    def export_csv():
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["ID", "Type", "Message", "Severity", "Timestamp"])

        for alert in alert_manager.all():
            writer.writerow([
                alert["id"],
                alert["event_type"],
                alert["message"],
                alert["severity"],
                alert["timestamp"],
            ])

        mem = io.BytesIO()
        mem.write(output.getvalue().encode())
        mem.seek(0)

        return send_file(
            mem,
            as_attachment=True,
            download_name="alerts.csv",
            mimetype="text/csv"
        )

    @app.route("/api/config", methods=["GET", "POST"])
    def config():
        if request.method == "GET":
            return jsonify(shared_state)

        data = request.json
        shared_state["detector_mode"] = data.get(
            "detector_mode",
            shared_state["detector_mode"]
        )

        return jsonify({"message": "Config updated"})

    @app.get("/api/logs")
    def logs():
        logs = [
            "System initialized",
            "YOLO model loaded",
            "Camera stream active",
        ]
        return jsonify(logs)

    return app

if __name__ == "__main__":
    alert_manager = AlertManager()
    camera_manager = CameraManager()

    t = threading.Thread(
        target=monitor_system,
        args=(alert_manager,),
        daemon=True
    )
    t.start()

    app = create_api(
        shared_state,
        alert_manager,
        camera_manager
    )

    app.run(host="0.0.0.0", port=5000)
