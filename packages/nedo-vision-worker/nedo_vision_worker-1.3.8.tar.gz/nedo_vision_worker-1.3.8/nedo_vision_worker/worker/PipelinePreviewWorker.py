import threading
import logging
import json
from datetime import datetime
from ..database.DatabaseManager import DatabaseManager
from ..models.worker_source_pipeline import WorkerSourcePipelineEntity
from .RabbitMQListener import RabbitMQListener

logger = logging.getLogger(__name__)

def safe_join_thread(thread, timeout=5):
    """Safely join a thread, avoiding RuntimeError when joining current thread."""
    if thread and thread != threading.current_thread():
        thread.join(timeout=timeout)
    elif thread == threading.current_thread():
        logging.info("🛑 [APP] Thread stopping from within itself, skipping join.")

class PipelinePreviewWorker:
    def __init__(self, config: dict):
        """
        Initialize Pipeline Preview Worker.
        
        This worker listens for pipeline preview requests and updates the
        last_preview_request_at timestamp in the database. The worker core
        will check this timestamp to decide whether to publish RTMP streams.

        Args:
            config (dict): Configuration object containing settings.
        """
        if not isinstance(config, dict):
            raise ValueError("⚠️ [APP] config must be a dictionary.")

        self.config = config
        self.worker_id = self.config.get("worker_id")

        if not self.worker_id:
            raise ValueError("⚠️ [APP] Configuration is missing 'worker_id'.")

        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        # Initialize RabbitMQ listener
        self.listener = RabbitMQListener(
            self.config, self.worker_id, self.stop_event, self._process_pipeline_preview_message
        )

    def start(self):
        """Start the Pipeline Preview Worker."""
        with self.lock:
            if self.thread and self.thread.is_alive():
                logger.warning("⚠️ [APP] Pipeline Preview Worker is already running.")
                return

            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info(f"🚀 [APP] Pipeline Preview Worker started (Device: {self.worker_id}).")

    def stop(self):
        """Stop the Pipeline Preview Worker."""
        with self.lock:
            if not self.thread or not self.thread.is_alive():
                logger.warning("⚠️ [APP] Pipeline Preview Worker is not running.")
                return

            self.stop_event.set()
            self.listener.stop_listening()

            safe_join_thread(self.thread)
            self.thread = None
            logger.info(f"🛑 [APP] Pipeline Preview Worker stopped (Device: {self.worker_id}).")

    def _run(self):
        """Main loop to manage RabbitMQ listener."""
        try:
            while not self.stop_event.is_set():
                logger.info("📡 [APP] Starting pipeline preview message listener...")
                self.listener.start_listening(
                    exchange_name="nedo.worker.pipeline.preview", 
                    queue_name=f"nedo.worker.pipeline.preview.{self.worker_id}"
                )
                
                # Wait for the listener thread to finish (connection lost or stop requested)
                while not self.stop_event.is_set() and self.listener.listener_thread and self.listener.listener_thread.is_alive():
                    self.listener.listener_thread.join(timeout=5)
                
                if not self.stop_event.is_set():
                    logger.warning("⚠️ [APP] Pipeline preview listener disconnected. Attempting to reconnect in 10 seconds...")
                    self.stop_event.wait(10)
                else:
                    logger.info("📡 [APP] Pipeline preview listener stopped.")
                    break
                    
        except Exception as e:
            logger.error("🚨 [APP] Unexpected error in Pipeline Preview Worker loop.", exc_info=True)

    def _process_pipeline_preview_message(self, message):
        """
        Process messages related to pipeline preview streaming.
        Updates the last_preview_request_at timestamp for the specified pipeline.
        """
        try:
            data = json.loads(message)
            worker_id = data.get("workerId")
            pipeline_id = data.get("pipelineId")

            logger.info(f"📡 [APP] Received pipeline preview message ({data})")

            # Validate required fields
            if not pipeline_id:
                logger.error(f"⚠️ [APP] Missing pipelineId in message")
                return

            if worker_id != self.worker_id:
                logger.warning(f"⚠️ [APP] Worker ID mismatch: expected {self.worker_id}, got {worker_id}")
                return

            # Update the last_preview_request_at timestamp in database
            self._update_pipeline_preview_timestamp(pipeline_id)

        except json.JSONDecodeError:
            logger.error("⚠️ [APP] Invalid JSON message format.")
        except Exception as e:
            logger.error("🚨 [APP] Error processing pipeline preview message.", exc_info=True)

    def _update_pipeline_preview_timestamp(self, pipeline_id: str):
        """
        Update the last_preview_request_at timestamp for the specified pipeline.
        
        Args:
            pipeline_id (str): The ID of the pipeline to update.
        """
        session = None
        try:
            session = DatabaseManager.get_session("config")
            
            # Find the pipeline
            pipeline = session.query(WorkerSourcePipelineEntity).filter_by(
                id=pipeline_id,
                worker_id=self.worker_id
            ).first()

            if not pipeline:
                logger.error(f"⚠️ [APP] Pipeline not found: {pipeline_id}")
                return

            # Update timestamp
            pipeline.last_preview_request_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"✅ [APP] Updated preview timestamp for pipeline {pipeline_id} ({pipeline.name})")

        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"🚨 [APP] Error updating pipeline preview timestamp: {e}", exc_info=True)
        finally:
            if session:
                session.close()
