import asyncio
from datetime import datetime
import random
from pprint import pformat

import obd
import time
from typing import Dict, Optional, Any
import logging

from app.core.config import settings
from app.data.obd_sensors import ALL_PIDS
from app.services.bluetooth_service import BluetoothService

log_filename = f"obd_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # or DEBUG if you want more detail

file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


class OBDService:
    def __init__(self):
        self.connection: Optional[obd.OBD] = None
        self.latest_data: Dict[str, Dict[str, Any]] = {}
        self.running = False

    async def connect(self, port: Optional[str] = None) -> bool:
        """Attempt to connect to OBD interface with retries"""

        # Determine which port to use
        obd_port = port if port else settings.connection_port
        # Treat empty string as None
        if not obd_port:
            obd_port = None

        if not obd_port:
            logger.warning("No OBD port specified, attempting auto-detection")

        for attempt in range(1, settings.obd_retry_count + 1):
            try:
                # Optional: Scan for Bluetooth devices to log/verify
                bt_devices = await BluetoothService.scan_ble()
                logger.info(f"BLE devices nearby: {bt_devices}")

                # Attempt to connect to OBD (classic Bluetooth serial)
                self.connection = obd.OBD(
                    portstr=obd_port,
                    fast=settings.connection_fast,
                    timeout=settings.connection_timeout
                )

                if self.connection.is_connected():
                    logger.info(f"Connected to OBD on attempt {attempt} using port {obd_port}")
                    return True
                else:
                    logger.warning(f"Attempt {attempt}: OBD not connected on port {obd_port}")

            except Exception as e:
                logger.error(f"Attempt {attempt}: Failed to connect to OBD: {e}")

            # Wait before retrying
            if attempt < settings.obd_retry_count:
                logger.info(f"Retrying in {settings.obd_retry_delay}s...")
                await asyncio.sleep(settings.obd_retry_delay)

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
    def log_sensor_data(data: dict):
        pretty_data = pformat(data, indent=2)
        logger.info(f"Sensor data:\n{pretty_data}")

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

        OBDService.log_sensor_data(data)

        return data

    # Untested
    async def query_all_sensors(self) -> Dict[str, dict]:
        """Query all supported sensors from the OBD interface (async-safe)."""
        if not self.is_connected():
            con_success = await self.connect()
            if not con_success:
                raise Exception("Not connected to OBD interface")

        if self.connection is None:
            raise Exception("OBD connection is not initialized")

        data = {}

        for pid in ALL_PIDS:
            # Get the command from obd.commands
            cmd = getattr(obd.commands, pid.name, None)
            if cmd is None:
                # command not available
                data[pid.name] = {"value": None, "unit": pid.unit}
                continue

            # Run the query in a thread to avoid blocking the event loop
            response = await asyncio.to_thread(self.connection.query, cmd)

            if response.is_null() or response.value is None:
                value = None
            elif hasattr(response.value, "magnitude"):
                value = response.value.magnitude
            else:
                value = str(response.value)

            # Determine the unit, fallback to PID unit if missing
            unit = str(response.value.units) if hasattr(response.value, "units") else pid.unit

            data[pid.name] = {"value": value, "unit": unit}

        self.log_sensor_data(data)
        return data

    async def query_sensors(self) -> Dict[str, dict]:
        if not self.is_connected():
            con_success = await self.connect()
            if not con_success:
                raise Exception("Not connected to OBD interface")

        if self.connection is None:
            raise Exception("OBD connection is not initialized")

        response = self.connection.query(obd.commands.RPM)
        rpm = None if response.is_null() else response.value.magnitude  # numeric
        unit = str(response.value.units) if hasattr(response.value, "units") else "rpm"

        data = {"rpm": {"value": rpm, "unit": unit}}

        return data


# Singleton
obd_service = OBDService()
