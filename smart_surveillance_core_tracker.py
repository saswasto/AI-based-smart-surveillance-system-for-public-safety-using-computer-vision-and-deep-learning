import math


class CentroidTracker:
    def __init__(self, max_disappeared=25, max_distance=60):
        self.next_object_id = 1
        self.objects = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid, bbox):
        object_id = self.next_object_id
        self.objects[object_id] = {"centroid": centroid, "bbox": bbox}
        self.disappeared[object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id):
        self.objects.pop(object_id, None)
        self.disappeared.pop(object_id, None)

    def update(self, rects):
        if not rects:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        input_centroids = []
        for (x1, y1, x2, y2) in rects:
            cx = int((x1 + x2) / 2.0)
            cy = int((y1 + y2) / 2.0)
            input_centroids.append((cx, cy))

        if not self.objects:
            for centroid, rect in zip(input_centroids, rects):
                self.register(centroid, rect)
            return self.objects

        object_ids = list(self.objects.keys())
        object_centroids = [item["centroid"] for item in self.objects.values()]

        used_rows = set()
        used_cols = set()

        distances = []
        for i, old_centroid in enumerate(object_centroids):
            row = []
            for new_centroid in input_centroids:
                row.append(math.dist(old_centroid, new_centroid))
            distances.append(row)

        while True:
            min_distance = None
            min_pos = None

            for row_idx, row in enumerate(distances):
                if row_idx in used_rows:
                    continue
                for col_idx, distance in enumerate(row):
                    if col_idx in used_cols:
                        continue
                    if min_distance is None or distance < min_distance:
                        min_distance = distance
                        min_pos = (row_idx, col_idx)

            if min_pos is None or min_distance is None:
                break
            if min_distance > self.max_distance:
                break

            row_idx, col_idx = min_pos
            object_id = object_ids[row_idx]
            self.objects[object_id] = {
                "centroid": input_centroids[col_idx],
                "bbox": rects[col_idx],
            }
            self.disappeared[object_id] = 0
            used_rows.add(row_idx)
            used_cols.add(col_idx)

        unused_rows = set(range(len(object_ids))) - used_rows
        unused_cols = set(range(len(input_centroids))) - used_cols

        for row_idx in unused_rows:
            object_id = object_ids[row_idx]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)

        for col_idx in unused_cols:
            self.register(input_centroids[col_idx], rects[col_idx])

        return self.objects