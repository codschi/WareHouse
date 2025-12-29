from typing import List, Optional
from datetime import date
from sqlmodel import Field, SQLModel, Relationship
from app.schemas.inboundorder import InboundOrderBase, InboundDetailBase

from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.supplier import Supplier
from app.models.staff import Staff

class InboundDetail(InboundDetailBase, SQLModel, table=True):
    # (Composite Primary Key): InboundID + ProductID
    InboundID: int = Field(primary_key=True, foreign_key="inboundorder.InboundID")
    ProductID: int = Field(primary_key=True, foreign_key="product.ProductID")
    
    # Warehouse (雖是 FK，但這裡只需存 ID，若需關聯物件可再加 Relationship)
    WarehouseID: int = Field(foreign_key="warehouse.WarehouseID")

    # 反向關聯回主單 (Optional, 方便操作)
    order: "InboundOrder" = Relationship(back_populates="details")

    product: Optional[Product] = Relationship() 
    warehouse: Optional[Warehouse] = Relationship()

# --- 進貨主單 Table ---
class InboundOrder(SQLModel, table=True):
    InboundID: Optional[int] = Field(default=None, primary_key=True)
    ioDate: date
    SupplierID: int = Field(foreign_key="supplier.SupplierID")
    StaffID: int = Field(foreign_key="staff.StaffID")
    Status: str = Field(default="Completed")

    # 建立與明細的關聯 (One-to-Many)
    details: List[InboundDetail] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"} 
    )

    supplier: Optional[Supplier] = Relationship()
    staff: Optional[Staff] = Relationship()