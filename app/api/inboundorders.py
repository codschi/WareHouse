from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from datetime import date
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from app.schemas.inboundorder import InboundOrder as InboundOrderSchema, InboundOrderCreate, InboundOrderRead
from app.models.inbound_order import InboundOrder, InboundDetail
from app.core.database import get_db

router = APIRouter(prefix="/inbound", tags=["Inbound Orders"])

@router.get("/", response_model=List[InboundOrderRead])
async def get_inbound_orders(
    io_date: Optional[date] = Query(None, description="篩選進貨日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db)
):
    statement = select(InboundOrder).options(
        selectinload(InboundOrder.details).options(
            selectinload(InboundDetail.product),
            selectinload(InboundDetail.warehouse)
        ),
        selectinload(InboundOrder.supplier),
        selectinload(InboundOrder.staff)
    )
    
    if io_date:
        statement = statement.where(InboundOrder.ioDate == io_date)
    
    # 排序：新單在後 (或依 ID 倒序)
    statement = statement.order_by(InboundOrder.InboundID.desc())
    if limit > 0:
        statement = statement.offset(skip).limit(limit)
    
    result = await db.exec(statement)
    return result.all()

@router.get("/{inbound_id}", response_model=InboundOrderRead)
async def get_inbound_order(inbound_id: int, db: AsyncSession = Depends(get_db)):
    statement = select(InboundOrder).where(InboundOrder.InboundID == inbound_id).options(
        selectinload(InboundOrder.details).options(
            selectinload(InboundDetail.product),
            selectinload(InboundDetail.warehouse)
        ),
        selectinload(InboundOrder.supplier),
        selectinload(InboundOrder.staff)
    )

    result = await db.exec(statement)
    order = result.first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/", response_model=InboundOrderSchema, status_code=status.HTTP_201_CREATED)
async def create_inbound_order(order_data: InboundOrderCreate, db: AsyncSession = Depends(get_db)):
    # 1. 建立主單物件
    # 注意：exclude={'details'} 因為 schema 裡的 details 是 List[BaseModel]，
    # 但 model 裡的 details 是 Relationship，我們需要手動處理
    new_order = InboundOrder(**order_data.model_dump(exclude={'details'}))
    
    # 簡單的 ID 生成策略 (若未啟用 AutoIncrement)
    # 實務上建議用 DB Sequence 或 UUID，這裡維持模擬邏輯: MAX + 1
    # 但為了原子性，最好讓 DB 處理。這裡我們先假設 InboundID 是 AutoIncrement 或 Optional
    # 如果要保留 "2025..." 這種格式，需要另外寫邏輯。
    # 這裡我們先讓它 Null，由 DB 決定 (或是我們手動查最大值 + 1，但有併發風險)
    
    db.add(new_order)
    await db.flush() # 取得 new_order.InboundID (如果是 AutoIncrement)
    await db.refresh(new_order) # 確保拿到 ID

    # 2. 建立明細物件
    for d in order_data.details:
        new_detail = InboundDetail(
            InboundID=new_order.InboundID,
            ProductID=d.ProductID,
            idQuantity=d.idQuantity,
            WarehouseID=d.WarehouseID
        )
        db.add(new_detail)
    
    await db.commit()
    # 重新讀取以包含 details
    statement = select(InboundOrder).where(InboundOrder.InboundID == new_order.InboundID).options(selectinload(InboundOrder.details))
    result = await db.exec(statement)
    return result.first()

@router.put("/{inbound_id}", response_model=InboundOrderSchema)
async def update_inbound_order(inbound_id: int, order_data: InboundOrderCreate, db: AsyncSession = Depends(get_db)):
    # 1. 撈取舊資料 (含明細)
    statement = select(InboundOrder).where(InboundOrder.InboundID == inbound_id).options(selectinload(InboundOrder.details))
    result = await db.exec(statement)
    order = result.first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # 2. 更新主單
    order.ioDate = order_data.ioDate
    order.SupplierID = order_data.SupplierID
    order.StaffID = order_data.StaffID
    db.add(order)
    
    # 3. 更新明細 (策略: 刪除舊的 -> 加入新的)
    # 找出目前所有明細並刪除
    for detail in order.details:
        await db.delete(detail)
        
    # 加入新明細
    for d in order_data.details:
        new_detail = InboundDetail(
            InboundID=inbound_id,
            ProductID=d.ProductID,
            idQuantity=d.idQuantity,
            WarehouseID=d.WarehouseID
        )
        db.add(new_detail)
        
    await db.commit()
    await db.refresh(order)
    return order

@router.delete("/{inbound_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inbound_order(inbound_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(InboundOrder, inbound_id)
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # 由於設定了 cascade="all, delete-orphan"，刪除主單會自動刪除明細
    await db.delete(result)
    await db.commit()
    return None