from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    obd_retry_count: int = 5
    obd_retry_delay: int = 10  # seconds

    class Config:
        env_file = ".env"

settings = Settings()