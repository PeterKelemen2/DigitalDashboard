from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    obd_retry_count: int = 5
    obd_retry_delay: int = 10  # seconds
    obd_port: Optional[str] = None
    obd_protocol: Optional[str] = "1"
    poll_interval: float = 1.0

    connection_port: Optional[str] = None
    connection_fast: Optional[bool] = True
    connection_timeout: Optional[float] = 30

    class Config:
        env_file = ".env"


settings = Settings()
