from pydantic import BaseModel
from typing import Optional

class WarehouseBase(BaseModel):
    waName: str
    waLocation: Optional[str] = None

class WarehouseCreate(WarehouseBase):
    pass

class Warehouse(WarehouseBase):
    WarehouseID: int

    class Config:
        from_attributes = True