import argparse
import threading
import time

from smart_surveillance.api.server import create_api
from smart_surveillance.core.config import load_config
from smart_surveillance.core.pipeline import SurveillancePipeline


def parse_args():
    parser = argparse.ArgumentParser(description="AI smart surveillance system")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    parser.add_argument(
        "--source",
        default=None,
        help="Video source. Use 0 for webcam or provide a video file path.",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    config = load_config(args.config)

    if args.source is not None:
        try:
            config["video"]["source"] = int(args.source)
        except ValueError:
            config["video"]["source"] = args.source

    pipeline = SurveillancePipeline(config)
    api = create_api(pipeline.shared_state, pipeline.alert_manager)

    api_thread = threading.Thread(
        target=lambda: api.run(
            host=config["app"]["api_host"],
            port=config["app"]["api_port"],
            debug=False,
            use_reloader=False,
        ),
        daemon=True,
    )
    api_thread.start()

    # Small delay keeps startup logs easier to read and avoids racey first queries.
    time.sleep(0.5)
    pipeline.run()