import threading
import time
import logging
from .RestrictedAreaManager import RestrictedAreaManager
from .SystemUsageManager import SystemUsageManager
from .PPEDetectionManager import PPEDetectionManager
from .DatasetFrameSender import DatasetFrameSender
from ..util.ImageUploader import ImageUploader
from ..services.ImageUploadClient import ImageUploadClient
from ..services.WorkerSourceUpdater import WorkerSourceUpdater

def safe_join_thread(thread, timeout=5):
    """Safely join a thread, avoiding RuntimeError when joining current thread."""
    if thread and thread != threading.current_thread():
        thread.join(timeout=timeout)
    elif thread == threading.current_thread():
        logging.info("🛑 [APP] Thread stopping from within itself, skipping join.")

logger = logging.getLogger(__name__)

class DataSenderWorker:
    def __init__(self, config: dict, send_interval=5, update_interval=10):
        """
        Initializes the Data Sender Worker.

        Args:
            config (dict): Configuration dictionary.
            send_interval (int): Interval (in seconds) for sending system usage & images.
            update_interval (int): Interval (in seconds) for updating worker sources.
        """
        if not isinstance(config, dict):
            raise ValueError("⚠️ [APP] config must be a dictionary.")

        self.config = config
        self.worker_id = self.config.get("worker_id")
        self.server_host = self.config.get("server_host")
        self.token = self.config.get("token")

        if not self.worker_id:
            raise ValueError("⚠️ [APP] Configuration is missing 'worker_id'.")
        if not self.server_host:
            raise ValueError("⚠️ [APP] Configuration is missing 'server_host'.")
        if not self.token:
            raise ValueError("⚠️ [APP] Configuration is missing 'token'.")
        
        self.should_update = True

        self.send_interval = send_interval
        self.update_interval = update_interval

        self.main_thread = None
        self.worker_update_thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        # Initialize services
        self.system_usage_manager = SystemUsageManager(self.server_host, self.worker_id, self.token)
        self.image_upload_client = ImageUploadClient(self.server_host)
        self.image_uploader = ImageUploader(self.image_upload_client, self.worker_id)
        self.ppe_detection_manager = PPEDetectionManager(self.server_host, self.worker_id, "worker_source_id", self.token) 
        self.restricted_area_manager = RestrictedAreaManager(self.server_host, self.worker_id, "worker_source_id", self.token)
        self.dataset_frame_sender = DatasetFrameSender(self.server_host, self.token)

        self.source_updater = WorkerSourceUpdater(self.worker_id, self.token)

    def start(self):
        """Start the Data Sender Worker threads."""
        with self.lock:
            if self.main_thread and self.main_thread.is_alive():
                logger.warning("⚠️ [APP] Data Sender Worker is already running.")
                return

            self.stop_event.clear()

            # ✅ Start the main worker thread (System usage + Image upload)
            self.main_thread = threading.Thread(target=self._run_main_worker, daemon=True)
            self.main_thread.start()

            # ✅ Start the worker source update thread
            self.worker_update_thread = threading.Thread(target=self._run_worker_source_updater, daemon=True)
            self.worker_update_thread.start()

            logger.info(f"🚀 [APP] Data Sender Worker started (Device: {self.worker_id}).")

    def stop(self):
        """Stop the Data Sender Worker and Worker Source Updater threads."""
        with self.lock:
            if not self.main_thread or not self.main_thread.is_alive():
                logger.warning("⚠️ [APP] Data Sender Worker is not running.")
                return

            self.stop_event.set()

            # ✅ Stop the main worker thread
            if self.main_thread:
                safe_join_thread(self.main_thread, timeout=5)

            # ✅ Stop the worker source update thread
            if self.worker_update_thread:
                safe_join_thread(self.worker_update_thread, timeout=5)

            self.main_thread = None
            self.worker_update_thread = None

            logger.info(f"🛑 [APP] Data Sender Worker stopped (Device: {self.worker_id}).")

    def start_updating(self):
        """Start updating worker sources."""
        self.should_update = True

    def stop_updating(self):
        """Stop updating worker sources."""
        self.should_update = False
        self.source_updater.stop_worker_sources()

    def _run_main_worker(self):
        """Main loop for sending system usage and uploading images."""
        try:
            while not self.stop_event.is_set():
                self.system_usage_manager.process_system_usage()
                
                ppe_pending = self._send_with_adaptive_interval(
                    self.ppe_detection_manager.send_ppe_detection_batch,
                    self.ppe_detection_manager.ppe_detection_repo.get_total_pending_count
                )
                
                violation_pending = self._send_with_adaptive_interval(
                    self.restricted_area_manager.send_violation_batch,
                    self.restricted_area_manager.repo.get_total_pending_count
                )
                
                self._process_image_upload()
                self._process_dataset_frames()
                
                sleep_time = self._calculate_sleep_interval(ppe_pending, violation_pending)
                if sleep_time < self.send_interval and (ppe_pending + violation_pending) > 0:
                    logger.debug(f"⚡ [APP] Catch-up mode: {ppe_pending + violation_pending} pending, sleeping {sleep_time}s")
                time.sleep(sleep_time)
        except Exception as e:
            logger.error("🚨 [APP] Unexpected error in main worker loop.", exc_info=True)

    def _send_with_adaptive_interval(self, send_func, count_func):
        """Send data with adaptive interval based on backlog."""
        try:
            pending = count_func()
            if pending > 0:
                send_func()
            return pending
        except Exception as e:
            logger.error(f"🚨 [APP] Error in adaptive sending: {e}", exc_info=True)
            return 0

    def _calculate_sleep_interval(self, ppe_pending: int, violation_pending: int) -> float:
        """
        Returns fixed sleep interval to prevent storage rate limits.
        
        Args:
            ppe_pending: Number of pending PPE detections
            violation_pending: Number of pending violations
            
        Returns:
            float: Sleep interval in seconds (fixed at 5s)
        """
        # Fixed 5 second interval to respect storage rate limits
        return self.send_interval

    def _run_worker_source_updater(self):
        """Dedicated loop for updating worker sources at a different interval."""
        try:
            while not self.stop_event.is_set():
                if self.should_update:
                    self._update_worker_sources()
                
                time.sleep(self.update_interval)
        except Exception as e:
            logger.error("🚨 [APP] Unexpected error in Worker Source Updater loop.", exc_info=True)

    def _process_image_upload(self):
        """Check and upload images to the server."""
        try:
            self.image_uploader.check_and_upload_images()
        except Exception as e:
            logger.error("🚨 [APP] Error uploading images.", exc_info=True)

    def _process_dataset_frames(self):
        """Send pending dataset frames to the server."""
        try:
            stats = self.dataset_frame_sender.send_pending_frames(max_batch_size=5)
            
            if stats:
                total_sent = sum(stats.values())
                logger.info(f"📤 [APP] Sent {total_sent} dataset frames")
            else:
                pending_count = self.dataset_frame_sender.get_pending_frame_count()
                if pending_count > 0:
                    logger.debug(f"📋 [APP] {pending_count} dataset frames pending")
                    
        except Exception as e:
            logger.error("🚨 [APP] Error processing dataset frames.", exc_info=True)

    def _update_worker_sources(self):
        """Synchronize and update worker sources."""
        try:
            self.source_updater.update_worker_sources()
        except Exception as e:
            logger.error("🚨 [APP] Error updating worker sources.", exc_info=True)
