from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class SiteBase(BaseModel):
    name: str
    street_address: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

class SiteCreate(SiteBase):
    pass

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    street_address: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

class SiteRead(SiteBase):
    id: UUID
    
    class Config:
        from_attributes = True
