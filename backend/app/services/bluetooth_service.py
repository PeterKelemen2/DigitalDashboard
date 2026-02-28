import asyncio
from bleak import BleakScanner


class BluetoothService:
    @staticmethod
    async def scan_ble():
        devices = await BleakScanner.discover()
        return [(d.name, d.address, d.details) for d in devices]  # return list of devices

    @staticmethod
    def scan_ble_sync():
        # Runs async function in a temporary loop and returns results
        return asyncio.run(BluetoothService.scan_ble())
