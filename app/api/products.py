from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func

from app.schemas.product import Product as ProductSchema, ProductCreate
from app.models.product import Product as ProductModel
from app.models.inbound_order import InboundDetail, InboundOrder
from app.models.requisition import ReqDetail, Requisition
from app.core.database import get_db
from sqlalchemy.exc import IntegrityError
from app.schemas.error import HTTPError

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[ProductSchema])
async def get_products(
    skip: int = Query(0, ge=0, description="跳過前 N 筆"),
    limit: int = Query(10, le=100, description="限制回傳 N 筆"),
    q: Optional[str] = Query(None, description="搜尋產品名稱或分類"),
    db: AsyncSession = Depends(get_db)
):
    statement = select(ProductModel)
    if q:
        statement = statement.where(
            (ProductModel.prName.contains(q)) | (ProductModel.prCategory.contains(q))
        )
    
    if limit > 0:
        statement = statement.offset(skip).limit(limit)
    
    result = await db.exec(statement)
    products = result.all()

    # Calculate Stock for these products
    # Note: For strict pagination accuracy we should calc for *only* these IDs, 
    # but for simplicity and small scale, fetching agg for all or just these is fine.
    # Let's fetch agg for all (easier query) or filtered by these IDs if list is large.
    # Given requirements, simple approach is OK.
    
    # 1. Get Inbound Sum
    from app.models.inbound_order import InboundDetail, InboundOrder
    from app.models.requisition import ReqDetail, Requisition
    from sqlalchemy import func

    # We need to turn SQLModel objects into Pydantic models to add field
    output = []
    
    # Batch strategy: Get all stock info in one go (or for visible IDs)
    product_ids = [p.ProductID for p in products]
    if not product_ids:
        return []

    in_stmt = select(InboundDetail.ProductID, func.sum(InboundDetail.idQuantity))\
              .join(InboundOrder)\
              .where(InboundOrder.Status == 'Completed')\
              .where(InboundDetail.ProductID.in_(product_ids))\
              .group_by(InboundDetail.ProductID)

    out_stmt = select(ReqDetail.ProductID, func.sum(ReqDetail.rdQuantity))\
               .join(Requisition)\
               .where(Requisition.Status == 'Completed')\
               .where(ReqDetail.ProductID.in_(product_ids))\
               .group_by(ReqDetail.ProductID)
               
    in_data = (await db.exec(in_stmt)).all()
    out_data = (await db.exec(out_stmt)).all()
    
    in_map = {row[0]: row[1] for row in in_data}
    out_map = {row[0]: row[1] for row in out_data}
    
    for p in products:
        p_schema = ProductSchema.model_validate(p)
        stock = in_map.get(p.ProductID, 0) - out_map.get(p.ProductID, 0)
        p_schema.current_stock = stock
        output.append(p_schema)
        
    return output

@router.get("/{product_id}/distribution")
async def get_product_distribution(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get stock distribution by warehouse"""
    from app.models.warehouse import Warehouse
    
    # 1. Inbound by Warehouse (only Completed)
    in_stmt = select(InboundDetail.WarehouseID, func.sum(InboundDetail.idQuantity))\
              .join(InboundOrder, InboundDetail.InboundID == InboundOrder.InboundID)\
              .where(InboundDetail.ProductID == product_id)\
              .where(InboundOrder.Status == 'Completed')\
              .group_by(InboundDetail.WarehouseID)
              
    # 2. Outbound by Warehouse (only Completed)
    out_stmt = select(ReqDetail.WarehouseID, func.sum(ReqDetail.rdQuantity))\
               .join(Requisition, ReqDetail.ReqID == Requisition.ReqID)\
               .where(ReqDetail.ProductID == product_id)\
               .where(Requisition.Status == 'Completed')\
               .group_by(ReqDetail.WarehouseID)

    in_res = (await db.exec(in_stmt)).all()
    out_res = (await db.exec(out_stmt)).all()
    
    stock_map = {} # {warehouse_id: stock}
    
    for row in in_res:
        stock_map[row[0]] = stock_map.get(row[0], 0) + row[1]
    for row in out_res:
        stock_map[row[0]] = stock_map.get(row[0], 0) - row[1]
        
    # Remove zero or negative (if any logic error) entries? Keep for transparency.
    # We need Warehouse Names
    results = []
    
    if not stock_map:
         return []

    # Fetch Warehouse Names
    wh_ids = list(stock_map.keys())
    warehouses = (await db.exec(select(Warehouse).where(Warehouse.WarehouseID.in_(wh_ids)))).all()
    wh_name_map = {w.WarehouseID: w.waName for w in warehouses}
    
    for wid, qty in stock_map.items():
        if qty != 0: # Only show non-zero
            results.append({
                "warehouse": wh_name_map.get(wid, f"Unknown ({wid})"),
                "stock": qty
            })
            
    return results

@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(ProductModel, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    new_product = ProductModel.model_validate(product)
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, updated_product: ProductCreate, db: AsyncSession = Depends(get_db)):
    db_product = await db.get(ProductModel, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    data = updated_product.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_product, key, value)
        
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.delete(
    "/{product_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": HTTPError, "description": "Integrity Error: Staff has linked orders"},
    }
)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    db_product = await db.get(ProductModel, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        await db.delete(db_product)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無法刪除：該商品尚有庫存紀錄或存在於交易單據中(如進貨單、領料單)。"
        )
    return None