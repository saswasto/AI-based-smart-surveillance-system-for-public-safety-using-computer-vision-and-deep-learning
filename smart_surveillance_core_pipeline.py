import time

import cv2

from smart_surveillance.core.alerts import AlertManager
from smart_surveillance.core.detectors import MotionDetector, PersonDetector
from smart_surveillance.core.rules import RuleEngine
from smart_surveillance.core.tracker import CentroidTracker


class SurveillancePipeline:
    def __init__(self, config):
        self.config = config
        self.detector = PersonDetector(config)
        self.motion_detector = MotionDetector(config["rules"]["min_motion_area"])
        self.tracker = CentroidTracker()
        self.alert_manager = AlertManager(
            config["outputs"]["alerts_file"], config["outputs"]["snapshots_dir"]
        )
        self.rule_engine = RuleEngine(config, self.alert_manager)
        self.shared_state = {
            "running": False,
            "fps": 0.0,
            "detector_mode": self.detector.mode,
            "people_count": 0,
            "last_alert": None,
            "frame_size": {
                "width": config["app"]["frame_width"],
                "height": config["app"]["frame_height"],
            },
        }

    def run(self):
        source = self.config["video"]["source"]
        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            raise RuntimeError(f"Unable to open video source: {source}")

        self.shared_state["running"] = True
        frame_counter = 0
        last_time = time.time()
        skip_frames = max(1, int(self.config["video"]["skip_frames"]))

        while True:
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.resize(
                frame,
                (
                    self.config["app"]["frame_width"],
                    self.config["app"]["frame_height"],
                ),
            )

            frame_counter += 1
            motion_boxes = self.motion_detector.detect(frame)

            if frame_counter % skip_frames == 0:
                detections = self.detector.detect(frame)
            else:
                detections = []

            rects = [detection.bbox for detection in detections]
            tracked_objects = self.tracker.update(rects)
            alerts = self.rule_engine.evaluate(frame, tracked_objects, motion_boxes)

            self._draw_overlay(frame, detections, tracked_objects, motion_boxes)

            self.shared_state["people_count"] = len(tracked_objects)
            if alerts:
                self.shared_state["last_alert"] = alerts[-1]

            current_time = time.time()
            fps = 1.0 / max(current_time - last_time, 1e-6)
            last_time = current_time
            self.shared_state["fps"] = round(fps, 2)

            if self.config["app"]["display"]:
                cv2.imshow("Smart Surveillance", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        self.shared_state["running"] = False
        cap.release()
        cv2.destroyAllWindows()

    def _draw_overlay(self, frame, detections, tracked_objects, motion_boxes):
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 0), 2)
            cv2.putText(
                frame,
                f"{detection.label}: {detection.confidence:.2f}",
                (x1, max(25, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 220, 0),
                2,
            )

        for object_id, obj in tracked_objects.items():
            x1, y1, x2, y2 = obj["bbox"]
            cx, cy = obj["centroid"]
            cv2.putText(
                frame,
                f"ID {object_id}",
                (x1, y2 + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                2,
            )
            cv2.circle(frame, (cx, cy), 4, (255, 255, 0), -1)

        for x1, y1, x2, y2 in motion_boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 140, 0), 2)

        self.rule_engine.draw_zone(frame)

        cv2.putText(
            frame,
            f"People: {len(tracked_objects)}",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"FPS: {self.shared_state['fps']:.2f}",
            (15, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"Detector: {self.shared_state['detector_mode'].upper()}",
            (15, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )