from pathlib import Path
from typing import List
from pydantic import BaseModel
import json

from app.models.obd_data import OBDPID

# Load JSON file
json_path = Path("app/data/sensors.json")
with json_path.open("r", encoding="utf-8") as f:
    raw_pids = json.load(f)

# Convert dicts to OBDPID instances
ALL_PIDS: List[OBDPID] = [OBDPID(**pid_dict) for pid_dict in raw_pids]
