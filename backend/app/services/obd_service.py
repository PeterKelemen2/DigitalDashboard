import random
import obd
import time
from typing import Dict, Optional, Any
import logging

from app.core.config import settings
from app.data.obd_sensors import ALL_PIDS

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

    @staticmethod
    def query_all_sensors_dummy() -> Dict[str, dict]:
        data = {}
        for pid in ALL_PIDS:
            # Treat numeric units (None-safe)
            numeric_units = {"rpm", "kph", "%", "°C", "g/s", "V"}
            if pid.unit in numeric_units:
                value = random.randint(0, 100)
            else:
                value = "N/A"
            data[pid.name] = {
                "value": value,
                "unit": pid.unit
            }
        return data

    # Untested
    @staticmethod
    def query_all_sensors(self) -> Dict[str, dict]:
        """Query all supported sensors from the OBD interface"""
        if not self.is_connected():
            raise Exception("Not connected to OBD interface")

        data = {}
        for pid in ALL_PIDS:
            # Skip unsupported/special if you want, or handle gracefully
            cmd = obd.commands.get(pid.name)  # get OBD command by name
            if not cmd:
                data[pid.name] = {"value": None, "unit": pid.unit}
                continue

            response = self.connection.query(cmd)
            if response.is_null():
                value = None
            elif hasattr(response.value, "magnitude"):
                value = response.value.magnitude  # numeric
            else:
                value = str(response.value) if response.value is not None else None

            unit = str(response.value.units) if hasattr(response.value, "units") else pid.unit

            data[pid.name] = {"value": value, "unit": unit}

        return data


# Singleton
obd_service = OBDService()
