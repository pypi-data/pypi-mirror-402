import argparse
import signal
import sys
import logging
from typing import NoReturn

from nedo_vision_worker.bootstrap import start_worker


class NedoWorkerCLI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_signal_handlers()
        self._service = None

    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> NoReturn:
        self.logger.info("🛑 Shutdown signal received")
        if self._service and hasattr(self._service, "stop"):
            self._service.stop()
        sys.exit(0)

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Nedo Vision Worker Service")

        parser.add_argument("--version", action="version", version="nedo-vision-worker 1.2.1")

        subparsers = parser.add_subparsers(dest="command", required=True)

        subparsers.add_parser("doctor", help="Check system dependencies")

        run = subparsers.add_parser("run", help="Start worker")

        run.add_argument("--token", required=True)
        run.add_argument("--server-host", default="be.vision.sindika.co.id")
        run.add_argument("--server-port", type=int, default=50051)
        run.add_argument("--rtmp-server", default="rtmp://live.vision.sindika.co.id:1935/live")
        run.add_argument("--storage-path", default="data")
        run.add_argument("--system-usage-interval", type=int, default=30)
        run.add_argument("--log-level", default="INFO")

        return parser

    def run(self) -> int:
        parser = self.create_parser()
        args = parser.parse_args()

        if args.command == "doctor":
            from nedo_vision_worker.doctor import main as doctor_main
            return doctor_main()

        if args.command == "run":
            self._service = start_worker(
                server_host=args.server_host,
                server_port=args.server_port,
                token=args.token,
                system_usage_interval=args.system_usage_interval,
                rtmp_server=args.rtmp_server,
                storage_path=args.storage_path,
                log_level=args.log_level,
            )
            signal.pause()  # wait for signal

        return 0


def main() -> int:
    return NedoWorkerCLI().run()


if __name__ == "__main__":
    sys.exit(main())
