import grpc
import logging
import time
import threading
from grpc import StatusCode
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)


class GrpcConnection:
    """
    Grpc connection management. Responsible for initiating connection with gRPC server that
    will be used across gRPC clients in the project.
    Expected to be initiated as a singleton.
    """
    
    _instance = None
    _init_done = False
    _lock = threading.Lock()
    _reconnectLock = threading.Lock()
    _reconnecting = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, server_host: str, server_port: int = 50051, max_retries: int = 3):
        if self.__class__._init_done:
            return  # prevent re-initialization
        self.__class__._init_done = True

        self.server_address = f"{server_host}:{server_port}"
        self.channel: Optional[grpc.Channel] = None
        self.connected = False
        self.max_retries = max_retries
        self.connect()

    def connect(self, retry_interval: int = 2) -> bool:
        attempts = 0
        while attempts < self.max_retries and not self.connected:
            try:
                if self.channel:
                    self._close_channel()
                
                self.channel = grpc.insecure_channel(self.server_address)
                
                future = grpc.channel_ready_future(self.channel)
                future.result(timeout=30)

                self.connected = True
                logger.info(f"🚀 Connected to gRPC server at {self.server_address}")
                return True

            except (grpc.RpcError, grpc.FutureTimeoutError, Exception) as e:
                attempts += 1
                self.connected = False
                error_msg = str(e)
                
                logger.error(f"⚠️ Connection failed ({attempts}/{self.max_retries}): {error_msg}")

                if attempts < self.max_retries:
                    sleep_time = retry_interval * (2 ** (attempts - 1))
                    logger.info(f"⏳ Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    logger.critical("❌ Max retries reached. Connection failed.")

        return False
    
    def get_connection(self):
        if self._reconnecting or not self.connected:
            return None
        
        return self.channel
    
    def _reconnect(self):
        logger.info(f"⏳ Reconnecting...")
        attempts = 0

        while not self.connected:
            try:
                if self.channel:
                    self._close_channel()
                
                self.channel = grpc.insecure_channel(self.server_address)
                
                future = grpc.channel_ready_future(self.channel)
                future.result(timeout=30)

                self.connected = True
                self._reconnecting = False
                logger.info(f"🚀 Connected to gRPC server at {self.server_address}")
                self._reconnectLock.release_lock()
            except (grpc.RpcError, grpc.FutureTimeoutError, Exception) as e:
                attempts += 1
                self.connected = False
                error_msg = str(e)
                
                logger.error(f"⚠️ Connection failed ({attempts}/{self.max_retries}): {error_msg}")

                sleep_time = 2 * (2 ** (attempts - 1))
                logger.info(f"⏳ Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
    
    def try_reconnect(self):
        if self._reconnecting:
            return
        
        if self._reconnectLock.acquire_lock(blocking=False):
            self._reconnecting = True
            self.connected = False
            self._reconnect()

    def _close_channel(self) -> None:
        try:
            if self.channel:
                self.channel.close()
            logger.info("🔌 gRPC connection closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing channel: {e}")
        finally:
            self.channel = None
            self.connected = False

    def close(self) -> None:
        if self.channel:
            self.channel.close()
        self.connected = False
        logger.info("🔌 gRPC connection closed")

    def is_connected(self) -> bool:
        return self.connected and self.channel is not None

    def get_connection_info(self) -> Dict[str, Any]:
        return {
            "server_address": self.server_address,
            "connected": self.connected,
            "max_retries": self.max_retries,
            "has_channel": self.channel is not None,
        }

    def __enter__(self):
        return self