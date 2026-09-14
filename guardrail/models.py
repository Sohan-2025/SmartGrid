from pydantic import BaseModel
from typing import List, Optional

class Substation(BaseModel):
    node_id: str
    voltage: float
    frequency: float
    load_mw: float
    capacity_mw: float
    breaker_status: str
    is_overloaded: bool
    operator_note: str
    sanitized_note: Optional[str] = None
    is_flagged: bool = False
    flag_reason: Optional[str] = None

class TelemetryPayload(BaseModel):
    timestamp: float
    global_safe_to_process: bool = True
    substations: List[Substation]