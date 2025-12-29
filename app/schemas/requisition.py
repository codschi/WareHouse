from pydantic import BaseModel
from datetime import date
from typing import List, Optional

from app.schemas.product import Product
from app.schemas.warehouse import Warehouse
from app.schemas.staff import Staff

# --- 領料明細 (ReqDetail) ---
class ReqDetailBase(BaseModel):
    ProductID: int
    rdQuantity: int
    WarehouseID: int

class ReqDetail(ReqDetailBase):
    ReqID: int
    
    class Config:
        from_attributes = True

# --- 領料主單 (Requisition) ---
class RequisitionBase(BaseModel):
    reDate: date
    reReason: str
    StaffID: int

class RequisitionCreate(RequisitionBase):
    details: List[ReqDetailBase]  # 建立時傳入明細列表

class Requisition(RequisitionBase):
    ReqID: int
    details: List[ReqDetail] = []

    class Config:
        from_attributes = True


class ReqDetailRead(ReqDetailBase):
    ReqID: int
    product: Optional[Product] = None
    warehouse: Optional[Warehouse] = None

class RequisitionRead(RequisitionBase):
    ReqID: int
    details: List[ReqDetailRead] = [] # 覆蓋
    staff: Optional[Staff] = None     # 新增

    class Config:
        from_attributes = True