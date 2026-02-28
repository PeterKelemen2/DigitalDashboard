import obd
import time
from typing import Dict, Optional, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class OBDService:
    def __init__(self):
        self.connection: Optional[obd.OBD] = None
        self.latest_data: Dict[str, Dict[str, Any]] = {}
        self.running = False

    def connect(self, port: Optional[str] = None) -> bool:
        """Attempt to connect to OBD interface with retries"""
        for attempt in range(1, settings.obd_retry_count + 1):
            try:
                if port:
                    self.connection = obd.OBD(port)
                else:
                    self.connection = obd.OBD()

                if self.connection.is_connected():
                    logger.info(f"Connected to OBD on attempt {attempt}")
                    return True
                else:
                    logger.warning(f"Attempt {attempt}: OBD not connected")
            except Exception as e:
                logger.error(f"Attempt {attempt}: Failed to connect to OBD: {e}")

            if attempt < settings.obd_retry_count:
                logger.info(f"Waiting {settings.obd_retry_delay}s before retry...")
                time.sleep(settings.obd_retry_delay)

        logger.error("All connection attempts failed")
        return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from OBD")

    def is_connected(self) -> bool:
        return self.connection is not None and self.connection.is_connected()

    def get_latest_data(self) -> Dict[str, Dict[str, Any]]:
        return self.latest_data


# Singleton
obd_service = OBDService()
