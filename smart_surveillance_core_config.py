from copy import deepcopy
from pathlib import Path

import yaml


DEFAULT_CONFIG = {
    "app": {
        "api_host": "127.0.0.1",
        "api_port": 5000,
        "frame_width": 960,
        "frame_height": 540,
        "display": True,
    },
    "video": {"source": 0, "skip_frames": 1},
    "detection": {
        "use_yolo_if_available": True,
        "confidence_threshold": 0.45,
        "nms_threshold": 0.35,
        "hog_stride": [8, 8],
        "hog_padding": [16, 16],
        "hog_scale": 1.05,
    },
    "rules": {
        "crowd_threshold": 5,
        "min_motion_area": 1500,
        "save_intrusion_snapshot": True,
        "restricted_zone": {
            "enabled": True,
            "points": [[620, 140], [930, 140], [930, 520], [620, 520]],
        },
    },
    "outputs": {
        "alerts_file": "smart_surveillance/outputs/alerts.json",
        "snapshots_dir": "smart_surveillance/outputs/snapshots",
    },
}


def _deep_merge(base, override):
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path):
    config_path = Path(path)
    if not config_path.exists():
        return deepcopy(DEFAULT_CONFIG)

    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file) or {}

    return _deep_merge(DEFAULT_CONFIG, raw_config)