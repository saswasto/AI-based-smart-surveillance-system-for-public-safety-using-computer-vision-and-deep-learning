from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: tuple


class MotionDetector:
    def __init__(self, min_area=1500):
        self.min_area = min_area
        self.background = None

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.background is None:
            self.background = gray.astype("float")
            return []

        background_uint8 = cv2.convertScaleAbs(self.background)
        delta = cv2.absdiff(background_uint8, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        motion_boxes = []
        for contour in contours:
            if cv2.contourArea(contour) < self.min_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            motion_boxes.append((x, y, x + w, y + h))

        cv2.accumulateWeighted(gray, self.background, 0.05)
        return motion_boxes


class PersonDetector:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.mode = "hog"

        if config["detection"]["use_yolo_if_available"]:
            try:
                from ultralytics import YOLO

                self.model = YOLO("yolov8n.pt")
                self.mode = "yolo"
            except Exception:
                self.model = None

        if self.model is None:
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, frame):
        if self.mode == "yolo":
            return self._detect_yolo(frame)
        return self._detect_hog(frame)

    def _detect_yolo(self, frame):
        results = self.model.predict(
            source=frame,
            conf=self.config["detection"]["confidence_threshold"],
            verbose=False,
        )

        detections = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                label = result.names.get(cls_id, str(cls_id))
                if label != "person":
                    continue

                conf = float(box.conf[0].item())
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                detections.append(Detection("person", conf, (x1, y1, x2, y2)))
        return detections

    def _detect_hog(self, frame):
        rects, weights = self.hog.detectMultiScale(
            frame,
            winStride=tuple(self.config["detection"]["hog_stride"]),
            padding=tuple(self.config["detection"]["hog_padding"]),
            scale=self.config["detection"]["hog_scale"],
        )

        detections = []
        for (x, y, w, h), weight in zip(rects, weights):
            detections.append(
                Detection("person", float(weight), (x, y, x + w, y + h))
            )
        return self._non_max_suppression(detections)

    def _non_max_suppression(self, detections):
        if not detections:
            return []

        boxes = np.array([det.bbox for det in detections], dtype=np.float32)
        scores = np.array([det.confidence for det in detections], dtype=np.float32)

        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]

        keep = []
        threshold = self.config["detection"]["nms_threshold"]

        while order.size > 0:
            i = order[0]
            keep.append(int(i))

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            overlap = (w * h) / areas[order[1:]]

            inds = np.where(overlap <= threshold)[0]
            order = order[inds + 1]

        return [detections[i] for i in keep]