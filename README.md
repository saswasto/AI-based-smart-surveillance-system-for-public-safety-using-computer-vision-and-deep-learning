# AI-based-smart-surveillance-system-for-public-safety-using-computer-vision-and-deep-learning
The rapid expansion of urban environments and increasing population density, ensuring public safety has become a critical challenge.

 This project is a practical smart-surveillance MVP built with Python, OpenCV, and Flask.
It supports:

- Real-time video monitoring from webcam or video file
- Person detection using YOLOv8 if available, with OpenCV HOG fallback
- Motion detection
- Restricted-zone intrusion alerts
- Crowd threshold alerts
- Alert logging with image snapshots
- Lightweight REST API for recent alerts and system status

## Project Structure

```text
smart_surveillance/
  api/
  core/
  data/
  outputs/
  ui/
main.py
config.yaml
requirements.txt
```

## Quick Start

1. Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the system:

```bash
python main.py
```

3. Optional arguments:

```bash
python main.py --source 0
python main.py --source sample.mp4
python main.py --config config.yaml
```

4. Open the dashboard API:

```text
http://127.0.0.1:5000
```

## Optional Deep-Learning Upgrade

If you want stronger detection, install YOLO support:

```bash
pip install ultralytics
```

The app automatically switches to YOLOv8 when `ultralytics` is available.

## Features

- `MotionDetector`: detects scene motion
- `PersonDetector`: uses YOLOv8 or OpenCV HOG
- `CentroidTracker`: lightweight multi-object tracking
- `RuleEngine`: triggers alerts for intrusion, crowding, and suspicious motion
- `AlertManager`: stores alerts and snapshots
- `Flask API`: exposes alerts and live system state

## Suggested Extensions

- Face recognition for watchlists
- Weapon detection model
- Loitering-duration analysis
- Database storage with PostgreSQL or MongoDB
- WebSocket live streaming dashboard
- Email/SMS alert integrations

## Note

This is an academic/demo-friendly implementation. For production public-safety deployments, add:

- stronger detection models
- identity/privacy controls
- secure storage and encryption
- audit logging
- model evaluation and bias review
- human-in-the-loop verification
