import json
import time
from pathlib import Path

import cv2


class AlertManager:
    def __init__(self, alerts_file, snapshots_dir):
        self.alerts_file = Path(alerts_file)
        self.snapshots_dir = Path(snapshots_dir)
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.alerts = []
        self._load()

    def _load(self):
        if not self.alerts_file.exists():
            self._persist()
            return

        try:
            self.alerts = json.loads(self.alerts_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.alerts = []
            self._persist()

    def _persist(self):
        self.alerts_file.write_text(
            json.dumps(self.alerts[-200:], indent=2), encoding="utf-8"
        )

    def create_alert(self, event_type, message, frame=None, meta=None):
        timestamp = int(time.time())
        snapshot_path = None

        if frame is not None:
            snapshot_name = f"{event_type}_{timestamp}.jpg"
            snapshot_path = str(self.snapshots_dir / snapshot_name)
            cv2.imwrite(snapshot_path, frame)

        alert = {
            "id": len(self.alerts) + 1,
            "event_type": event_type,
            "message": message,
            "timestamp": timestamp,
            "snapshot_path": snapshot_path,
            "meta": meta or {},
        }
        self.alerts.append(alert)
        self._persist()
        return alert

    def latest(self, limit=20):
        return list(reversed(self.alerts[-limit:]))