import logging
import os
import threading
import time

from ..repositories.RestrictedAreaRepository import RestrictedAreaRepository
from ..services.RestrictedAreaClient import RestrictedAreaClient

logger = logging.getLogger(__name__)

def safe_join_thread(thread, timeout=5):
    """Safely join a thread, avoiding RuntimeError when joining current thread."""
    if thread and thread != threading.current_thread():
        thread.join(timeout=timeout)
    elif thread == threading.current_thread():
        logging.info("🛑 [APP] Thread stopping from within itself, skipping join.")

class RestrictedAreaManager:
    def __init__(self, server_host: str, worker_id: str, worker_source_id: str, token: str):
        """
        Handles restricted area violation monitoring and reporting.

        Args:
            server_host (str): The gRPC server host.
            worker_id (str): Unique worker ID (passed externally).
            worker_source_id (str): Unique worker source ID (passed externally).
            token (str): Authentication token for the worker.
        """
        if not worker_id or not worker_source_id:
            raise ValueError("⚠️ [APP] 'worker_id' and 'worker_source_id' cannot be empty.")
        if not token:
            raise ValueError("⚠️ [APP] 'token' cannot be empty.")

        self.client = RestrictedAreaClient(server_host)
        self.server_host = server_host
        self.worker_id = worker_id
        self.worker_source_id = worker_source_id
        self.token = token
        self.violations_data = []
        self.stop_event = threading.Event()
        self.violation_thread = None
        self.repo = RestrictedAreaRepository()

        self._start_violation_monitoring()

    def _start_violation_monitoring(self):
        """Starts a background thread to monitor and collect restricted area violations."""
        if self.violation_thread and self.violation_thread.is_alive():
            logger.warning("⚠️ [APP] Restricted area violation thread already running.")
            return

        logger.info("📡 [APP] Restricted area violation monitoring started.")

    def _calculate_batch_by_size(self, all_violations: list, max_size_mb: int = 40) -> list:
        """
        Calculates batch based on actual image file sizes to stay within gRPC limit.
        
        Args:
            all_violations (list): All pending violations
            max_size_mb (int): Maximum batch size in MB (default 40MB for 50MB limit with margin)
            
        Returns:
            list: Violations that fit within size limit
        """
        batch = []
        total_size = 0
        max_size_bytes = max_size_mb * 1024 * 1024
        
        for violation in all_violations:
            try:
                image_size = os.path.getsize(violation['image']) if os.path.exists(violation['image']) else 0
                tile_size = os.path.getsize(violation['image_tile']) if os.path.exists(violation['image_tile']) else 0
                violation_size = image_size + tile_size
                
                if total_size + violation_size > max_size_bytes:
                    if batch:
                        break
                    else:
                        logger.warning(f"⚠️ Single violation exceeds {max_size_mb}MB, skipping")
                        continue
                
                batch.append(violation)
                total_size += violation_size
                
            except Exception as e:
                logger.error(f"❌ Error checking file size: {e}")
                continue
        
        return batch

    def send_violation_batch(self):
        """Sends a batch of collected violation data to the server with fixed 5 violation batch size."""
        try:
            pending_count = self.repo.get_total_pending_count()
            
            if pending_count == 0:
                return
            
            # Fixed batch size of 5 to prevent storage rate limits
            all_violations = self.repo.get_latest_violations(5)
            
            if not all_violations:
                return

            self.violations_data = self._calculate_batch_by_size(all_violations)
            
            if not self.violations_data:
                logger.warning("⚠️ [APP] No valid violations within size limit")
                return

            batch_size_mb = sum(
                os.path.getsize(v['image']) + os.path.getsize(v['image_tile']) 
                for v in self.violations_data if os.path.exists(v['image']) and os.path.exists(v['image_tile'])
            ) / (1024 * 1024)
            
            logger.info(f"📤 [APP] Sending {len(self.violations_data)} violations (~{batch_size_mb:.1f}MB, {pending_count} pending)")

            response = self.client.send_upsert_batch(
                worker_id=self.worker_id,
                worker_source_id=self.worker_source_id,
                violation_data=self.violations_data,
                token=self.token
            )

            if response.get("success"):
                logger.info(f"✅ [APP] Successfully sent {len(self.violations_data)} violations")
                self.violations_data.clear()
            else:
                logger.error(f"❌ [APP] Failed to send restricted area violation batch: {response.get('message')}")

        except Exception as e:
            logger.error("🚨 [APP] Error sending restricted area violation batch.", exc_info=True)

    def close(self):
        """Closes the violation client and stops the monitoring thread."""
        self.stop_event.set()

        if self.violation_thread and self.violation_thread.is_alive():
            safe_join_thread(self.violation_thread)
            logger.info("🔌 [APP] Restricted area violation monitoring thread stopped.")

        if self.client:
            logger.info("✅ [APP] Restricted Area Violation Client closed.")
