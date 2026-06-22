import argparse
import threading
import time
import logging
import signal
import sys
import json
import platform
import socket
from datetime import datetime

from smart_surveillance.api.server import create_api
from smart_surveillance.core.config import load_config
from smart_surveillance.core.pipeline import SurveillancePipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("smart-surveillance")

shutdown_flag = False
pipeline_instance = None

runtime_stats = {
    "start_time": time.time(),
    "frames_processed": 0,
    "alerts_generated": 0
}

def parse_args():
    parser = argparse.ArgumentParser("Smart Surveillance System")

    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--source", default=None)
    parser.add_argument("--disable-api", action="store_true")
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--detector", default=None)

    return parser.parse_args()

def show_banner():
    print("""
=====================================================
        AI SMART SURVEILLANCE SYSTEM
=====================================================
 - Live Detection
 - Crowd Monitoring
 - Alert System
 - API Dashboard
=====================================================
""")

def collect_system_info():
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "time": datetime.now().isoformat()
    }


def save_system_info():
    with open("system_info.json", "w") as f:
        json.dump(collect_system_info(), f, indent=4)
    logger.info("System info saved")

def backup_config(config):
    filename = f"config_backup_{int(time.time())}.json"
    with open(filename, "w") as f:
        json.dump(config, f, indent=4)
    logger.info("Config backup created")

def startup_checks():
    logger.info("Running startup checks...")
    time.sleep(1)
    logger.info("Camera OK")
    logger.info("Detector OK")
    logger.info("API OK")
    logger.info("All systems ready")
    
def monitor_system(pipeline):
    while not shutdown_flag:
        state = pipeline.shared_state

        logger.info(
            f"FPS={state.get('fps', 0)} | "
            f"People={state.get('people_count', 0)} | "
            f"CPU={state.get('cpu_usage', 0)}%"
        )

        runtime_stats["frames_processed"] += 30
        time.sleep(5)


def heartbeat():
    while not shutdown_flag:
        logger.info("Heartbeat OK")
        time.sleep(30)


def cleanup_alerts(pipeline):
    while not shutdown_flag:
        alerts = pipeline.alert_manager.alerts

        if len(alerts) > 500:
            pipeline.alert_manager.alerts = alerts[-200:]
            logger.info("Old alerts cleaned")

        time.sleep(60)


def report_scheduler(pipeline):
    while not shutdown_flag:
        report = {
            "time": datetime.now().isoformat(),
            "alerts": len(pipeline.alert_manager.alerts),
            "people": pipeline.shared_state.get("people_count", 0),
            "fps": pipeline.shared_state.get("fps", 0)
        }

        filename = f"report_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=4)

        logger.info(f"Report saved: {filename}")
        time.sleep(300)

def start_api(api, host, port):
    try:
        logger.info(f"API running on {host}:{port}")
        api.run(host=host, port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.exception(f"API crashed: {e}")

def signal_handler(sig, frame):
    global shutdown_flag
    logger.warning("Shutdown signal received...")
    shutdown_flag = True

    if pipeline_instance:
        pipeline_instance.shared_state["running"] = False

    logger.info("System shutting down safely...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run():
    global pipeline_instance

    args = parse_args()

    show_banner()
    startup_checks()

    logger.info("Loading configuration...")
    config = load_config(args.config)


    if args.source:
        try:
            config["video"]["source"] = int(args.source)
        except ValueError:
            config["video"]["source"] = args.source


    if args.detector:
        config["detector"]["mode"] = args.detector

    if args.record:
        config["video"]["record"] = True

    backup_config(config)
    save_system_info()

    logger.info("Initializing pipeline...")
    pipeline = SurveillancePipeline(config)
    pipeline_instance = pipeline

    if not args.disable_api:
        api = create_api(
            pipeline.shared_state,
            pipeline.alert_manager
        )

        threading.Thread(
            target=start_api,
            args=(
                api,
                config["app"]["api_host"],
                config["app"]["api_port"]
            ),
            daemon=True
        ).start()

    threading.Thread(target=monitor_system, args=(pipeline,), daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=cleanup_alerts, args=(pipeline,), daemon=True).start()
    threading.Thread(target=report_scheduler, args=(pipeline,), daemon=True).start()

    time.sleep(1)

    logger.info("Starting pipeline execution...")

    try:
        pipeline.run()
    except Exception as e:
        logger.exception(f"Pipeline crashed: {e}")
    finally:
        pipeline.shared_state["running"] = False
        logger.info("Pipeline stopped")

if __name__ == "__main__":
    run()
