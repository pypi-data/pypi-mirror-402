import logging
from typing import Optional

from .ConfigurationManagerInterface import ConfigurationManagerInterface

class DummyConfigurationManager(ConfigurationManagerInterface):
    """
    A class to manage local and remote configuration stored in the 'config' database.
    """

    def __init__(
        self,
        worker_id: str,
        worker_token: str,
        server_host: str,
        server_port: str,
        rtmp_server_url: str,
        rabbitmq_host: str,
        rabbitmq_port: str,
        rabbitmq_username: str,
        rabbitmq_password: str,
        logger: logging.Logger
    ):
        self._logger = logger
        self._worker_id = worker_id
        self._worker_token = worker_token
        self._server_host = server_host
        self._server_port = server_port
        self._rtmp_server_url = rtmp_server_url
        self._rabbitmq_host = rabbitmq_host
        self._rabbitmq_port = rabbitmq_port
        self._rabbitmq_username = rabbitmq_username
        self._rabbitmq_password = rabbitmq_password

        self._config = {
            "worker_id": self._worker_id,
            "token": self._worker_token,
            "server_host": self._server_host,
            "server_port": str(self._server_port),
            "rtmp_server": self._rtmp_server_url,
            "rabbitmq_host": self._rabbitmq_host,
            "rabbitmq_port": self._rabbitmq_port,
            "rabbitmq_username": self._rabbitmq_username,
            "rabbitmq_password": self._rabbitmq_password,
        }

        
    def get_config(self, key: str) -> str:
        return self._config[key]
    
    def get_all_configs(self) -> Optional[dict]:
        return self._config