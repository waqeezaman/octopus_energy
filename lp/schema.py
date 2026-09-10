# schema.py
from pydantic import BaseModel, Field
from typing import List

class BatteryConfig(BaseModel):
    capacity_kwh: float = Field(gt=0, description="Max battery capacity")
    initial_soc_kwh: float = Field(default=0.0, ge=0)
    
    
class EnergyProfile(BaseModel):
    demand: List[float]
    renewable: List[float]
    grid_cost: List[float]