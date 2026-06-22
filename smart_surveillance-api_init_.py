from flask import Flask, jsonify, request, send_file
from datetime import datetime
import threading
import random
import time
import csv
import io

app = Flask(__name__)

API_KEY = "smart123"

shared_state = {
    "running": True,
    "detector_mode": "yolo",
    "people_count": 0,
    "fps": 0,
    "cpu_usage": 0,
    "memory_usage": 0
}

alerts = []

cameras = [
    {"id": 1, "name": "Entrance Gate", "status": "online"},
    {"id": 2, "name": "Platform 1", "status": "online"},
    {"id": 3, "name": "Parking Zone", "status": "offline"}
]

logs = [
    "System initialized",
    "YOLO model loaded",
    "Camera stream active"
]


def add_alert(event_type, message, severity="low"):
    alert = {
        "id": len(alerts) + 1,
        "event_type": event_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    alerts.append(alert)


def latest_alerts(limit=10):
    return alerts[-limit:]


def authenticate():
    key = request.headers.get("X-API-KEY")
    return key == API_KEY


@app.before_request
def check_api_key():
    public_routes = ["/", "/health"]
    if request.path not in public_routes:
        if not authenticate():
            return jsonify({"error": "Unauthorized"}), 401


def monitor_system():
    while True:
        shared_state["people_count"] = random.randint(0, 50)
        shared_state["fps"] = round(random.uniform(24, 60), 2)
        shared_state["cpu_usage"] = random.randint(20, 90)
        shared_state["memory_usage"] = random.randint(30, 85)

        if shared_state["people_count"] > 40:
            add_alert(
                "Crowd Detection",
                "High crowd density detected",
                "high"
            )

        if shared_state["cpu_usage"] > 80:
            add_alert(
                "CPU Warning",
                "CPU usage is very high",
                "medium"
            )

        time.sleep(3)


@app.route("/")
def dashboard():
    latest = latest_alerts()

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
            for alert in latest
        ]
    ) or "<li>No alerts yet.</li>"

    return f"""
    <html>
    <head>
        <title>Smart Surveillance Dashboard</title>
        <style>
            body {{
                font-family: Arial;
                background: linear-gradient(135deg,#0b172a,#16324f);
                color:white;
                padding:30px;
            }}
            .grid {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
                gap:20px;
            }}
            .card {{
                background:rgba(255,255,255,0.08);
                padding:20px;
                border-radius:15px;
            }}
        </style>
    </head>
    <body>
        <h1>AI Smart Surveillance Dashboard</h1>
        <div class="grid">
            <div class="card">
                <h2>System Status</h2>
                <p>Running: {shared_state['running']}</p>
                <p>Detector: {shared_state['detector_mode']}</p>
                <p>People Count: {shared_state['people_count']}</p>
                <p>FPS: {shared_state['fps']}</p>
                <p>CPU Usage: {shared_state['cpu_usage']}%</p>
                <p>Memory Usage: {shared_state['memory_usage']}%</p>
            </div>

            <div class="card">
                <h2>API Endpoints</h2>
                <p>/health</p>
                <p>/api/status</p>
                <p>/api/alerts</p>
                <p>/api/cameras</p>
            </div>

            <div class="card">
                <h2>Recent Alerts</h2>
                <ul>{alerts_html}</ul>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "time": datetime.now().isoformat()
    })


@app.route("/api/status")
def status():
    return jsonify(shared_state)


@app.route("/api/alerts")
def get_alerts():
    severity = request.args.get("severity")

    if severity:
        filtered = [
            a for a in alerts
            if a["severity"] == severity
        ]
        return jsonify(filtered)

    return jsonify(alerts)


@app.route("/api/alerts", methods=["POST"])
def create_alert():
    data = request.json

    add_alert(
        data["event_type"],
        data["message"],
        data.get("severity", "low")
    )

    return jsonify({"message": "Alert added"})


@app.route("/api/cameras")
def get_cameras():
    return jsonify(cameras)


@app.route("/api/stats")
def stats():
    total_alerts = len(alerts)

    critical_alerts = len(
        [a for a in alerts if a["severity"] == "critical"]
    )

    high_alerts = len(
        [a for a in alerts if a["severity"] == "high"]
    )

    medium_alerts = len(
        [a for a in alerts if a["severity"] == "medium"]
    )

    low_alerts = len(
        [a for a in alerts if a["severity"] == "low"]
    )

    return jsonify({
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "high_alerts": high_alerts,
        "medium_alerts": medium_alerts,
        "low_alerts": low_alerts
    })


@app.route("/api/export")
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        ["ID", "Event", "Message", "Severity", "Timestamp"]
    )

    for alert in alerts:
        writer.writerow([
            alert["id"],
            alert["event_type"],
            alert["message"],
            alert["severity"],
            alert["timestamp"]
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

    if "detector_mode" in data:
        shared_state["detector_mode"] = data["detector_mode"]

    return jsonify({"message": "Config updated"})


@app.route("/api/logs")
def get_logs():
    return jsonify(logs)


@app.route("/api/system/start", methods=["POST"])
def start_system():
    shared_state["running"] = True
    logs.append("System started")
    return jsonify({"message": "System started"})


@app.route("/api/system/stop", methods=["POST"])
def stop_system():
    shared_state["running"] = False
    logs.append("System stopped")
    return jsonify({"message": "System stopped"})


@app.route("/api/search_alert")
def search_alert():
    keyword = request.args.get("keyword", "").lower()

    result = [
        a for a in alerts
        if keyword in a["message"].lower()
    ]

    return jsonify(result)


@app.route("/api/report")
def report():
    return jsonify({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_cameras": len(cameras),
        "online_cameras": len(
            [c for c in cameras if c["status"] == "online"]
        ),
        "offline_cameras": len(
            [c for c in cameras if c["status"] == "offline"]
        ),
        "total_alerts": len(alerts)
    })


if __name__ == "__main__":
    thread = threading.Thread(
        target=monitor_system,
        daemon=True
    )
    thread.start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
