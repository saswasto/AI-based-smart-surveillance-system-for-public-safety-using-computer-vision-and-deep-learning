from flask import Flask, jsonify


def create_api(shared_state, alert_manager):
    app = Flask(__name__)

    @app.get("/")
    def index():
        latest_alerts = alert_manager.latest(limit=10)
        alerts_html = "".join(
            [
                (
                    "<li><strong>{event}</strong> - {message}"
                    "<br><small>timestamp: {timestamp}</small></li>"
                ).format(
                    event=alert["event_type"],
                    message=alert["message"],
                    timestamp=alert["timestamp"],
                )
                for alert in latest_alerts
            ]
        ) or "<li>No alerts yet.</li>"

        return f"""
        <html>
          <head>
            <title>Smart Surveillance Dashboard</title>
            <style>
              body {{
                font-family: Georgia, serif;
                background: linear-gradient(135deg, #0b172a, #16324f);
                color: #f5f7fb;
                margin: 0;
                padding: 32px;
              }}
              .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 16px;
              }}
              .card {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 18px;
                padding: 20px;
                backdrop-filter: blur(8px);
              }}
              h1 {{
                margin-top: 0;
              }}
              code {{
                color: #9bd1ff;
              }}
              ul {{
                padding-left: 20px;
              }}
            </style>
          </head>
          <body>
            <h1>AI-Based Smart Surveillance System</h1>
            <p>Real-time public-safety monitoring with person detection, motion analysis, tracking, and alerts.</p>
            <div class="grid">
              <div class="card">
                <h3>System Status</h3>
                <p>Running: <strong>{shared_state['running']}</strong></p>
                <p>Detector: <strong>{shared_state['detector_mode'].upper()}</strong></p>
                <p>People Count: <strong>{shared_state['people_count']}</strong></p>
                <p>FPS: <strong>{shared_state['fps']}</strong></p>
              </div>
              <div class="card">
                <h3>API Endpoints</h3>
                <p><code>/health</code></p>
                <p><code>/api/status</code></p>
                <p><code>/api/alerts</code></p>
              </div>
              <div class="card">
                <h3>Recent Alerts</h3>
                <ul>{alerts_html}</ul>
              </div>
            </div>
          </body>
        </html>
        """

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy"})

    @app.get("/api/status")
    def status():
        return jsonify(shared_state)

    @app.get("/api/alerts")
    def alerts():
        return jsonify(alert_manager.latest(limit=50))

    return app