import logging
import grpc
from typing import Optional
from ..models.config import ConfigEntity  # ORM model for server_config
from ..database.DatabaseManager import DatabaseManager  # DatabaseManager for managing sessions

from ..util.HardwareID import HardwareID
from ..services.ConnectionInfoClient import ConnectionInfoClient
from .ConfigurationManagerInterface import ConfigurationManagerInterface

class ConfigurationManager(ConfigurationManagerInterface):
    """
    A class to manage local and remote configuration stored in the 'config' database.
    """

    def __init__(self, worker_token: str, server_host: str, server_port: int, rtmp_server_url: str, logger: logging.Logger):
        try:
            self._logger = logger
            self._worker_token = worker_token
            self._server_host = server_host
            self._server_port = server_port
            self._rtmp_server_url = rtmp_server_url

            self._initialize_remote_configuration()

            logging.info("✅ [APP] Configuration database initialized successfully.")
        except Exception as e:
            logging.exception("❌ [APP] Failed to initialize the configuration database.")
            raise RuntimeError("Database initialization failed.") from e
        
    def get_config(self, key: str) -> str:
        """
        Retrieve the value of a specific configuration key from the 'config' database.

        Args:
            key (str): The configuration key.

        Returns:
            str: The configuration value, or None if the key does not exist.
        """
        if not key or not isinstance(key, str):
            raise ValueError("⚠️ The 'key' must be a non-empty string.")

        session = None
        try:
            session = DatabaseManager.get_session("config")
            logging.info(f"🔍 [APP] Retrieving configuration key: {key}")
            config = session.query(ConfigEntity).filter_by(key=key).first()
            if config:
                logging.info(f"✅ [APP] Configuration key '{key}' retrieved successfully.")
                return config.value
            else:
                logging.warning(f"⚠️ [APP] Configuration key '{key}' not found.")
                return ""
        except Exception as e:
            logging.exception(f"❌ [APP] Failed to retrieve configuration key '{key}': {e}")
            raise RuntimeError(f"Failed to retrieve configuration key '{key}'") from e
        finally:
            if session:
                session.close()
    
    def get_all_configs(self) -> Optional[dict]:
        """
        Retrieve all configuration key-value pairs from the 'config' database.

        Returns:
            dict: A dictionary of all configuration key-value pairs.
        """
        session = None
        try:
            session = DatabaseManager.get_session("config")
            logging.info("🔍 [APP] Retrieving all configuration keys.")
            configs = session.query(ConfigEntity).all()
            if configs:
                logging.info("✅ [APP] All configuration keys retrieved successfully.")
                return {config.key: config.value for config in configs}
            else:
                logging.info("⚠️ [APP] No configuration keys found.")
                return None
        except Exception as e:
            logging.exception("❌ [APP] Failed to retrieve all configuration keys.")
            raise RuntimeError("Failed to retrieve all configuration keys.") from e
        finally:
            if session:
                session.close()

    def _initialize_remote_configuration(self):
        """
        Initialize the application configuration using the provided token
        and saving configuration data locally.
        """
        try:
            # Get hardware ID
            hardware_id = HardwareID.get_unique_id()

            self._logger.info(f"🖥️ [APP] Detected Hardware ID: {hardware_id}")
            self._logger.info(f"🌐 [APP] Using Server Host: {self._server_host}")

            # Check if token is provided
            if not self._worker_token:
                raise ValueError("Token is required for worker initialization. Please provide a token obtained from the frontend.")

            # Get connection info using the ConnectionInfoClient
            connection_client = ConnectionInfoClient(self._server_host, self._server_port, self._worker_token)
            connection_result = connection_client.get_connection_info()
            
            if not connection_result["success"]:
                logging.error(f"Device connection info failed: {connection_result['message']}")
                raise ValueError(f"Initializing remote config failed, reason: {connection_result['message']}")

            worker_id = connection_result.get('id')
            if not worker_id:
                raise ValueError("No worker_id returned from connection info!")

            self._set_config_batch({
                "worker_id": worker_id,
                "server_host": self._server_host,
                "rtmp_server": self._rtmp_server_url,
                "server_port": str(self._server_port),
                "token": self._worker_token,
                "rabbitmq_host": connection_result['rabbitmq_host'],
                "rabbitmq_port": str(connection_result['rabbitmq_port']),
                "rabbitmq_username": connection_result['rabbitmq_username'],
                "rabbitmq_password": connection_result['rabbitmq_password']
            })
            self._print_config()
        
        except ValueError as ve:
            logging.error(f"Validation error: {ve}")
        except grpc.RpcError as ge:
            logging.error(f"Grpc Error: {ge}")
        except Exception as e:
            logging.error(f"Unexpected error during initialization: {e}")

    def _set_config_batch(self, configs: dict):
        """
        Set or update multiple configuration key-value pairs in the 'config' database in a batch operation.

        Args:
            configs (dict): A dictionary containing configuration key-value pairs.
        """
        if not isinstance(configs, dict) or not configs:
            raise ValueError("⚠️ [APP] The 'configs' parameter must be a non-empty dictionary.")

        session = None
        try:
            session = DatabaseManager.get_session("config")
            logging.info(f"🔄 [APP] Attempting to set {len(configs)} configuration keys in batch.")

            existing_configs = session.query(ConfigEntity).filter(ConfigEntity.key.in_(configs.keys())).all()
            existing_keys = {config.key: config for config in existing_configs}

            for key, value in configs.items():
                if key in existing_keys:
                    logging.info(f"🔄 [APP] Updating configuration key: {key}")
                    existing_keys[key].value = value
                else:
                    logging.info(f"➕ [APP] Adding new configuration key: {key}")
                    new_config = ConfigEntity(key=key, value=value)
                    session.add(new_config)

            session.commit()
            logging.info("✅ [APP] All configuration keys set successfully.")
        except Exception as e:
            if session:
                session.rollback()
            logging.exception(f"❌ [APP] Failed to set batch configuration keys: {e}")
            raise RuntimeError("Failed to set batch configuration keys.") from e
        finally:
            if session:
                session.close()

    def _print_config(self):
        """
        Print all configuration key-value pairs to the console.
        """
        try:
            configs = self.get_all_configs()
            if configs:
                print("📄 Current Configuration:")
                for key, value in configs.items():
                    # Mask sensitive information completely
                    if key.lower() in ['token', 'password']:
                        print(f"  🔹 {key}: ***")
                    else:
                        print(f"  🔹 {key}: {value}")
            else:
                print("⚠️ No configuration found. Please initialize the configuration.")
        except Exception as e:
            logging.exception("❌ Failed to print configuration keys.")
            raise RuntimeError("Failed to print configuration keys.") from e
