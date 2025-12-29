from pydantic import BaseModel
from datetime import date
from typing import List, Optional

from app.schemas.product import Product
from app.schemas.warehouse import Warehouse
from app.schemas.supplier import Supplier
from app.schemas.staff import Staff

# 進貨明細
class InboundDetailBase(BaseModel):
    ProductID: int
    idQuantity: int
    WarehouseID: int

class InboundDetail(InboundDetailBase):
    InboundID: int

# 進貨主單
class InboundOrderBase(BaseModel):
    ioDate: date
    SupplierID: int
    StaffID: int

class InboundOrderCreate(InboundOrderBase):
    details: List[InboundDetailBase]  # 建立單據時同時傳入多筆明細

class InboundOrder(InboundOrderBase):
    InboundID: int
    details: List[InboundDetail] = []

    class Config:
        from_attributes = True

class InboundDetailRead(InboundDetailBase):
    InboundID: int
    product: Optional[Product] = None
    warehouse: Optional[Warehouse] = None

class InboundOrderRead(InboundOrderBase):
    InboundID: int
    # 覆蓋 details，使用新的 DetailRead
    details: List[InboundDetailRead] = []
    
    # 這裡額外增加物件節點
    supplier: Optional[Supplier] = None
    staff: Optional[Staff] = None

    class Config:
        from_attributes = True