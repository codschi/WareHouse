from typing import Optional
from sqlmodel import Field, SQLModel
from app.schemas.supplier import SupplierBase

class Supplier(SupplierBase, SQLModel, table=True):
    # SupplierID (PK)
    SupplierID: Optional[int] = Field(default=None, primary_key=True)