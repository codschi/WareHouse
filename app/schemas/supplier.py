from pydantic import BaseModel
from typing import Optional

class SupplierBase(BaseModel):
    suName: str
    suPhone: str
    suAddress: str

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    SupplierID: int

    class Config:
        from_attributes = True