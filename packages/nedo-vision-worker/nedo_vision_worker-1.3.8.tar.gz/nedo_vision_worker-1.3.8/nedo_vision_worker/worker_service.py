import time
import multiprocessing
import signal
import sys
import logging

try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

from .worker.WorkerManager import WorkerManager
from .config.ConfigurationManagerInterface import ConfigurationManagerInterface
from .services.GrpcClientBase import set_auth_failure_callback

class WorkerService:
    """
    Main worker service class that manages the worker agent lifecycle.
    Uses hardware ID-based authentication and configuration management.
    """
    
    def __init__(
        self,
        configuration_manager: ConfigurationManagerInterface,
        server_host: str = "be.vision.sindika.co.id",
        token: str = "",
        system_usage_interval: int = 30,
        rtmp_server: str = "rtmp://live.vision.sindika.co.id:1935/live",
        storage_path: str = "data",
        server_port: int = 50051,
    ):
        """
        Initialize the worker service.
        
        Args:
            server_host: Manager server host (default: 'be.vision.sindika.co.id')
            token: Authentication token for the worker (obtained from frontend)
            system_usage_interval: Interval for system usage reporting (default: 30)
            rtmp_server: RTMP server URL for video streaming
            storage_path: Storage path for databases and files (default: 'data')
            server_port: gRPC server port (default: 50051)
        """
        
        self._configuration_manager = configuration_manager
        self.logger = self._setup_logging()
        self.worker_manager = None
        self.running = False
        self.server_host = server_host
        self.token = token
        self.system_usage_interval = system_usage_interval
        self.rtmp_server = rtmp_server
        self.storage_path = storage_path
        self.server_port = server_port
        self.config = None
        self.auth_failure_detected = False
        
        # Register authentication failure callback
        set_auth_failure_callback(self._on_authentication_failure)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _on_authentication_failure(self):
        """Called when an authentication failure is detected."""
        if not self.auth_failure_detected:
            self.auth_failure_detected = True
            self.logger.error("🔑 [APP] Authentication failure detected. Shutting down service...")
            self.stop()

    def _setup_logging(self):
        """Configure logging settings (allows inline emojis)."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Only show warnings and errors
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("pika").setLevel(logging.WARNING)
        logging.getLogger("grpc").setLevel(logging.FATAL)
        logging.getLogger("ffmpeg").setLevel(logging.FATAL)
        logging.getLogger("subprocess").setLevel(logging.FATAL)
        
        return logging.getLogger(__name__)

    def initialize(self) -> bool:
        """
        Initialize the worker service components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Worker service initialization started")
            
            # Initialize configuration
            self.config = self._configuration_manager.get_all_configs()
            print(self.config)
            if self.config is None:
                raise RuntimeError("Failed to initialize configuration")

            # Initialize WorkerManager
            self.worker_manager = WorkerManager(self.config)

            self.logger.info("Worker service initialization completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize worker service: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def start(self):
        """Start the worker service"""
        if not self.running:
            self.running = True
            self.logger.info("Worker service started")
            try:
                # Start all workers via WorkerManager
                self.worker_manager.start_all()
                # Block main thread to keep process alive
                while self.running and not self.auth_failure_detected:
                    time.sleep(1)
                
                # If authentication failure was detected, exit with error code
                if self.auth_failure_detected:
                    self.logger.error("🔑 [APP] Service terminated due to authentication failure")
                    sys.exit(1)
            except Exception as e:
                self.logger.error(f"Error in worker service: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                self.stop()
        else:
            self.logger.info("Service already running.")
    
    def stop(self):
        """Stop the worker service"""
        if self.running:
            self.running = False
            self.logger.info("Worker service stopping...")
            try:
                # Stop all workers via WorkerManager
                if hasattr(self, 'worker_manager'):
                    self.worker_manager.stop_all()
                self.logger.info("Worker service stopped")
            except Exception as e:
                self.logger.error(f"Error stopping worker service: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
        else:
            self.logger.info("Service already stopped.")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def run(self):
        """Run the worker service"""
        if self.initialize():
            self.start()
        else:
            self.logger.error("Failed to initialize worker service")
            sys.exit(1)


def main():
    """Main entry point for the worker service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nedo Vision Worker Service")
    parser.add_argument(
        "--server-host", 
        default="be.vision.sindika.co.id",
        help="Manager server host (default: be.vision.sindika.co.id)"
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=50051,
        help="gRPC server port (default: 50051)"
    )
    parser.add_argument(
        "--system-usage-interval",
        type=int,
        default=30,
        help="System usage reporting interval in seconds (default: 30)"
    )
    args = parser.parse_args()
    
    # Create and run worker service
    # service = WorkerService(
    #     server_host=args.server_host,
    #     server_port=args.server_port,
    #     system_usage_interval=args.system_usage_interval
    # )
    # service.run()


if __name__ == "__main__":
    main()