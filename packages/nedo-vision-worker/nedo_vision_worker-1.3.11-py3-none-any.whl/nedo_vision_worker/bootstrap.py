import logging
from nedo_vision_worker.config.ConfigurationManager import ConfigurationManager
from nedo_vision_worker.database.DatabaseManager import set_storage_path, DatabaseManager
from nedo_vision_worker.worker_service import WorkerService


def start_worker(
    *,
    server_host: str,
    server_port: int,
    token: str,
    system_usage_interval: int,
    rtmp_server: str,
    storage_path: str,
    log_level: str = "INFO",
) -> WorkerService:
    # Logging (only once, force allowed)
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        force=True,
    )

    logger = logging.getLogger("nedo-worker")

    # Storage & DB
    set_storage_path(storage_path)
    DatabaseManager.init_databases()

    # Configuration
    configuration_manager = ConfigurationManager(
        worker_token=token,
        server_host=server_host,
        server_port=server_port,
        rtmp_server_url=rtmp_server,
        logger=logging.getLogger("configuration_manager"),
    )

    service = WorkerService(
        configuration_manager=configuration_manager,
        server_host=server_host,
        token=token,
        system_usage_interval=system_usage_interval,
        rtmp_server=rtmp_server,
        storage_path=storage_path,
    )

    logger.info("🚀 Starting Nedo Vision Worker Service")
    service.run()

    return service
