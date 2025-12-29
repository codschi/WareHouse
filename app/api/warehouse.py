from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.warehouse import Warehouse as WarehouseSchema, WarehouseCreate
from app.models.warehouse import Warehouse as WarehouseModel
from app.core.database import get_db
from sqlalchemy.exc import IntegrityError
from app.schemas.error import HTTPError

router = APIRouter(prefix="/warehouse", tags=["Warehouse"])

@router.get("/", response_model=List[WarehouseSchema])
async def get_warehouses(
    q: Optional[str] = Query(None, description="搜尋倉庫名稱或地點"),
    skip: int = Query(0, ge=0, description="跳過前 N 筆"),
    limit: int = Query(10, le=100, description="限制回傳 N 筆"),
    db: AsyncSession = Depends(get_db)
):
    statement = select(WarehouseModel)
    
    # 搜尋邏輯: 搜尋 名稱 OR 地點
    if q:
        statement = statement.where(
            (WarehouseModel.waName.contains(q)) | (WarehouseModel.waLocation.contains(q))
        )
    
    # 分頁切片
    if limit > 0:
        statement = statement.offset(skip).limit(limit)
    
    result = await db.exec(statement)
    return result.all()

@router.get("/{warehouse_id}", response_model=WarehouseSchema)
async def get_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(WarehouseModel, warehouse_id)
    if not result:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return result

@router.post("/", response_model=WarehouseSchema, status_code=status.HTTP_201_CREATED)
async def create_warehouse(warehouse: WarehouseCreate, db: AsyncSession = Depends(get_db)):
    # 將 Schema 轉換為 Model
    new_warehouse = WarehouseModel.model_validate(warehouse)
    
    db.add(new_warehouse)
    await db.commit()
    await db.refresh(new_warehouse) # 取得自動生成的 ID
    return new_warehouse

@router.put("/{warehouse_id}", response_model=WarehouseSchema)
async def update_warehouse(warehouse_id: int, updated_warehouse: WarehouseCreate, db: AsyncSession = Depends(get_db)):
    # 1. 先查詢
    db_warehouse = await db.get(WarehouseModel, warehouse_id)
    if not db_warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # 2. 更新欄位
    data = updated_warehouse.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_warehouse, key, value)
        
    # 3. 儲存
    db.add(db_warehouse)
    await db.commit()
    await db.refresh(db_warehouse)
    return db_warehouse

@router.delete(
    "/{warehouse_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": HTTPError, "description": "Integrity Error: Staff has linked orders"},
    }
)
async def delete_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    db_warehouse = await db.get(WarehouseModel, warehouse_id)
    if not db_warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    try:
        await db.delete(db_warehouse)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無法刪除：該倉庫尚有庫存或交易紀錄關聯(如進貨單、領料單)。"
        )
    return None