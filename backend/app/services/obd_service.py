import obd
from datetime import datetime
from threading import Thread
import time
from typing import Dict, Optional, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class OBDService:
    def __init__(self):
        self.connection: Optional[obd.OBD] = None
        self.latest_data: Dict[str, Dict[str, Any]] = {}
        self.polling_thread: Optional[Thread] = None
        self.running = False
        self.poll_interval = 1.0  # seconds

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
                    self.start_polling()
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
        self.stop_polling()
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        return self.connection is not None and self.connection.is_connected()

    def start_polling(self):
        if self.polling_thread and self.polling_thread.is_alive():
            return
        self.running = True

        def poll_loop():
            while self.running and self.is_connected():
                for cmd in self.connection.supported_commands:
                    try:
                        resp = self.connection.query(cmd)
                        if resp.value:
                            self.latest_data[cmd.name] = {
                                "value": getattr(resp.value, "magnitude", str(resp.value)),
                                "unit": getattr(resp.value, "units", None),
                                "timestamp": datetime.now().isoformat()
                            }
                    except Exception as e:
                        logger.warning(f"Failed to read {cmd.name}: {e}")
                time.sleep(self.poll_interval)

        self.polling_thread = Thread(target=poll_loop, daemon=True)
        self.polling_thread.start()

    def stop_polling(self):
        self.running = False
        if self.polling_thread:
            self.polling_thread.join()

    def get_latest_data(self) -> Dict[str, Dict[str, Any]]:
        return self.latest_data

# Singleton
obd_service = OBDService()