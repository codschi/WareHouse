from typing import Optional
from sqlmodel import Field, SQLModel
from app.schemas.warehouse import WarehouseBase

class Warehouse(WarehouseBase, SQLModel, table=True):
    WarehouseID: Optional[int] = Field(default=None, primary_key=True)