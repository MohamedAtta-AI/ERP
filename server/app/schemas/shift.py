from datetime import time
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ShiftBase(BaseModel):
    name: str
    start_time: time
    end_time: time

class ShiftCreate(ShiftBase):
    pass

class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class ShiftRead(ShiftBase):
    id: UUID
    
    class Config:
        from_attributes = True
