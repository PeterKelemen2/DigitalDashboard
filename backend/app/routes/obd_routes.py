from typing import List
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.models.obd_data import OBDData, ConnectionStatus
from app.services.bluetooth_service import BluetoothService
from app.services.obd_service import obd_service

router = APIRouter(prefix="/obd", tags=["OBD"])


@router.post("/connect", response_model=ConnectionStatus)
async def connect(port: str = None):
    """Connect to OBD interface"""
    success = obd_service.connect(port)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to connect to OBD interface")
    return obd_service.get_status()


@router.post("/disconnect")
async def disconnect():
    """Disconnect from OBD interface"""
    obd_service.disconnect()
    return {"message": "Disconnected successfully"}


@router.get("/status", response_model=ConnectionStatus)
async def get_status():
    """Get connection status"""
    return obd_service.get_status()


@router.get("/commands", response_model=List[str])
async def get_available_commands():
    """Get list of available OBD commands"""
    try:
        return obd_service.get_available_commands()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/query/{command_name}", response_model=OBDData)
async def query_command(command_name: str):
    """Query a specific OBD command"""
    try:
        return obd_service.query_command(command_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stream")
async def stream_obd_data():
    if not obd_service.is_connected():
        try:
            obd_success = obd_service.connect()
            if not obd_success:
                raise HTTPException(status_code=500, detail="Failed to connect to OBD interface")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def event_generator():
        while obd_service.is_connected():
            data = obd_service.get_latest_data()
            payload = json.dumps(data)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(obd_service.poll_interval)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/stream_all_sensors_dummy")
async def stream_all_sensors_dummy():
    async def event_generator():
        while True:
            await asyncio.sleep(settings.poll_interval)
            yield f"data: {json.dumps(obd_service.query_all_sensors_dummy())}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/stream_all_sensors")
async def stream_all_sensors():
    async def event_generator():
        while True:
            await asyncio.sleep(settings.poll_interval)

            sensor_data = obd_service.query_all_sensors()

            yield f"data: {json.dumps(sensor_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/connect_obd")
async def connect_obd():
    try:
        obd_success = obd_service.connect()
        return {"success": obd_success}
    except Exception as e:
        return {"error": str(e)}


@router.get("/get_bt_devices")
async def get_bt_devices():
    try:
        bt_devices = await BluetoothService.scan_ble()
    except Exception as e:
        return {"error": str(e)}

    return {"devices": bt_devices}
