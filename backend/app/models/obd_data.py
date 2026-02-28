from pydantic import BaseModel
from typing import Optional


class OBDData(BaseModel):
    """Model for OBD data response"""
    command: str
    value: Optional[float] = None
    unit: Optional[str] = None
    timestamp: str


class ConnectionStatus(BaseModel):
    """Model for connection status"""
    connected: bool
    port: Optional[str] = None
    protocol: Optional[str] = None
