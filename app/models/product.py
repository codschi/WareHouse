from typing import Optional
from sqlmodel import Field, SQLModel
from app.schemas.product import ProductBase

class Product(ProductBase, SQLModel, table=True):
    # 對應 ER 圖 ProductID (PK)
    ProductID: Optional[int] = Field(default=None, primary_key=True)