from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    database: str
    timestamp: datetime
    services: Dict[str, Any]

