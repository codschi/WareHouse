from typing import List, Optional
from datetime import date
from sqlmodel import Field, SQLModel, Relationship
from app.schemas.requisition import RequisitionBase, ReqDetailBase

from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.staff import Staff

# --- 領料明細 Table ---
class ReqDetail(ReqDetailBase, SQLModel, table=True):
    # 複合主鍵: ReqID + ProductID
    ReqID: int = Field(primary_key=True, foreign_key="requisition.ReqID")
    ProductID: int = Field(primary_key=True, foreign_key="product.ProductID")
    
    # 倉庫 FK
    WarehouseID: int = Field(foreign_key="warehouse.WarehouseID")

    # 反向關聯回主單
    requisition: "Requisition" = Relationship(back_populates="details")

    product: Optional[Product] = Relationship()
    warehouse: Optional[Warehouse] = Relationship()

# --- 領料主單 Table ---
class Requisition(RequisitionBase, SQLModel, table=True):
    # PK
    ReqID: Optional[int] = Field(default=None, primary_key=True)
    reDate: date
    StaffID: int = Field(foreign_key="staff.StaffID")
    Status: str = Field(default="Completed")

    # 建立與明細的關聯 (One-to-Many)
    # cascade="all, delete-orphan": 刪除主單時，明細自動刪除
    details: List[ReqDetail] = Relationship(
        back_populates="requisition",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"} 
    )

    staff: Optional[Staff] = Relationship()