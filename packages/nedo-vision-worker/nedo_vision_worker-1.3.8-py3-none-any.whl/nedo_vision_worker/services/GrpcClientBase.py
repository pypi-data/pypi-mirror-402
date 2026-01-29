import grpc
import logging
import time
from grpc import StatusCode
from typing import Callable, Optional, Any, Dict
from .GrpcConnection import GrpcConnection

logger = logging.getLogger(__name__)

_auth_failure_callback: Optional[Callable[[], None]] = None

def set_auth_failure_callback(callback: Callable[[], None]) -> None:
    global _auth_failure_callback
    _auth_failure_callback = callback

def _notify_auth_failure() -> None:
    if _auth_failure_callback:
        try:
            _auth_failure_callback()
        except Exception as e:
            logger.error(f"❌ Auth callback error: {e}")


class GrpcClientBase:
    ERROR_HANDLERS = {
        StatusCode.UNAVAILABLE: ("⚠️", "warning", "Server unavailable"),
        StatusCode.DEADLINE_EXCEEDED: ("⏳", "error", "Request timeout"),
        StatusCode.PERMISSION_DENIED: ("🚫", "error", "Permission denied"),
        StatusCode.UNAUTHENTICATED: ("🔑", "error", "Authentication failed"),
        StatusCode.INVALID_ARGUMENT: ("⚠️", "error", "Invalid argument"),
        StatusCode.NOT_FOUND: ("🔍", "error", "Resource not found"),
        StatusCode.INTERNAL: ("💥", "error", "Internal server error"),
        StatusCode.CANCELLED: ("🛑", "warning", "Request cancelled"),
        StatusCode.ALREADY_EXISTS: ("📁", "warning", "Resource exists"),
        StatusCode.RESOURCE_EXHAUSTED: ("🔋", "error", "Resources exhausted"),
        StatusCode.FAILED_PRECONDITION: ("⚡", "error", "Precondition failed"),
        StatusCode.ABORTED: ("🔄", "error", "Request aborted"),
        StatusCode.OUT_OF_RANGE: ("📏", "error", "Value out of range"),
        StatusCode.UNIMPLEMENTED: ("🚧", "error", "Method not implemented"),
        StatusCode.DATA_LOSS: ("💿", "critical", "Data loss detected"),
    }

    def __init__(self, server_host: str, server_port: int = 50051, max_retries: int = 3):
        self.stub = None
        self.server_address = f"{server_host}:{server_port}"
        self.channel: Optional[grpc.Channel] = None
        self.connected = False
        self.max_retries = max_retries

        self.connection = GrpcConnection(server_host, server_port)

    def connect(self, stub_class, retry_interval: int = 2) -> bool:
        conn = self.connection.get_connection()
        if conn is None:
            return False
        requested_stub = stub_class(conn)
        
        self.stub = requested_stub
        self.connected = True

        return True

    def _close_channel(self) -> None:
        try:
            if self.channel:
                self.channel.close()
        except Exception as e:
            logger.warning(f"⚠️ Error closing channel: {e}")
        finally:
            self.channel = None
            self.stub = None

    # MARK:
    def close(self) -> None:
        self._close_channel()
        self.connected = False
        logger.info("🔌 gRPC connection closed")

    def handle_rpc(self, rpc_call: Callable, *args, **kwargs) -> Optional[Any]:
        if not self.is_connected():
            logger.error("❌ Not connected. Cannot make RPC call")
            return None

        try:
            return rpc_call(*args, **kwargs)
        except grpc.RpcError as e:
            return self._handle_grpc_error(e, rpc_call, *args, **kwargs)
        except Exception as e:
            print(e)
            print(str(e) == "Cannot invoke RPC on closed channel!")
            if str(e) == "Cannot invoke RPC on closed channel!":
                self.connect(type(self.stub))

            logger.error(f"💥 Unexpected RPC error: {e}")
            return None

    def _handle_grpc_error(self, e: grpc.RpcError, rpc_call: Callable, *args, **kwargs) -> Optional[Any]:
        status_code = e.code()
        error_message = self._extract_error_message(e)
        
        emoji, log_level, description = self.ERROR_HANDLERS.get(
            status_code, ("❌", "error", f"Unhandled error (Code: {status_code})")
        )

        getattr(logger, log_level)(f"{emoji} {description}: {error_message}")

        if status_code == StatusCode.UNAVAILABLE:
            return self._handle_unavailable(rpc_call, *args, **kwargs)
        elif status_code in {StatusCode.UNAUTHENTICATED, StatusCode.PERMISSION_DENIED}:
            self._handle_auth_error(error_message)
        
        if status_code in {StatusCode.UNAVAILABLE, StatusCode.DEADLINE_EXCEEDED}:
            self.connected = False

        return None

    # MARK:
    # Should request for reconnection two times. Notify grpc connection to do reconnect
    def _handle_unavailable(self, rpc_call: Callable, *args, **kwargs) -> Optional[Any]:
        # self.connected = False
        self.connection.try_reconnect()
        
        if self.stub:
            stub_class = type(self.stub)
            logger.info("🔄 Reconnecting...")
            
            if self.connect(stub_class):
                logger.info("✅ Reconnected. Retrying...")
                try:
                    return rpc_call(*args, **kwargs)
                except Exception as e:
                    logger.error(f"❌ Retry failed: {e}")
        
        return None

    def _handle_auth_error(self, error_message: str) -> None:
        auth_keywords = ["authentication", "token", "unauthorized", "invalid token"]
        if any(keyword in error_message.lower() for keyword in auth_keywords):
            logger.error(f"🔑 Auth failure: {error_message}")
            _notify_auth_failure()

    def _extract_error_message(self, e: grpc.RpcError) -> str:
        error_message = getattr(e, "details", lambda: str(e))()
        return error_message.split("debug_error_string")[0].strip()

    def is_connected(self) -> bool:
        return self.connected and self.connection.get_connection() is not None and self.stub is not None

    def get_connection_info(self) -> Dict[str, Any]:
        return {
            "server_address": self.server_address,
            "connected": self.connected,
            "max_retries": self.max_retries,
            "has_channel": self.channel is not None,
            "has_stub": self.stub is not None
        }

    @staticmethod
    def get_error_message(response: Optional[Dict]) -> Optional[str]:
        if not response:
            return "Unknown error"
            
        if response.get("success"):
            return None
        
        message = response.get("message", "Unknown error")
        
        auth_keywords = ["Invalid authentication token", "authentication", "unauthorized"]
        if message and any(keyword in message for keyword in auth_keywords):
            logger.error(f"🔑 Auth failure in response: {message}")
            _notify_auth_failure()
        
        return message

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()