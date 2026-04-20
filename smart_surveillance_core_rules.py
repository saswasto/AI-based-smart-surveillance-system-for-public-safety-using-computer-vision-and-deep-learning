import time

import cv2
import numpy as np


class RuleEngine:
    def __init__(self, config, alert_manager):
        self.config = config
        self.alert_manager = alert_manager
        self.last_alert_times = {}
        self.cooldown_seconds = 8
        self.zone_points = np.array(
            config["rules"]["restricted_zone"]["points"], dtype=np.int32
        )

    def evaluate(self, frame, tracked_objects, motion_boxes):
        people = list(tracked_objects.items())
        alerts = []

        if len(people) >= self.config["rules"]["crowd_threshold"]:
            alerts.append(
                self._emit(
                    "crowd_detected",
                    f"Crowd threshold exceeded: {len(people)} people detected.",
                    frame,
                    {"people_count": len(people)},
                )
            )

        if self.config["rules"]["restricted_zone"]["enabled"]:
            for object_id, obj in people:
                cx, cy = obj["centroid"]
                inside = cv2.pointPolygonTest(self.zone_points, (cx, cy), False) >= 0
                if inside:
                    alerts.append(
                        self._emit(
                            "zone_intrusion",
                            f"Object {object_id} entered the restricted zone.",
                            frame,
                            {"object_id": object_id, "centroid": [cx, cy]},
                        )
                    )

        if motion_boxes and not people:
            alerts.append(
                self._emit(
                    "suspicious_motion",
                    "Motion detected without a confirmed person track.",
                    frame,
                    {"motion_regions": len(motion_boxes)},
                )
            )

        return [alert for alert in alerts if alert is not None]

    def draw_zone(self, frame):
        if self.config["rules"]["restricted_zone"]["enabled"]:
            cv2.polylines(frame, [self.zone_points], True, (0, 0, 255), 2)
            cv2.putText(
                frame,
                "Restricted Zone",
                tuple(self.zone_points[0]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

    def _emit(self, event_type, message, frame, meta):
        now = time.time()
        last_time = self.last_alert_times.get(event_type, 0)
        if now - last_time < self.cooldown_seconds:
            return None

        self.last_alert_times[event_type] = now
        return self.alert_manager.create_alert(event_type, message, frame=frame, meta=meta)