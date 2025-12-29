from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from datetime import date
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload # 用於預加載關聯

from app.schemas.requisition import Requisition as RequisitionSchema, RequisitionCreate, RequisitionRead
from app.models.requisition import Requisition, ReqDetail
from app.core.database import get_db

router = APIRouter(prefix="/requisitions", tags=["Requisitions"])

@router.get("/", response_model=List[RequisitionRead])
async def get_requisitions(
    re_date: Optional[date] = Query(None, description="篩選領料日期"),
    q: Optional[str] = Query(None, description="搜尋單號或領料原因"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db)
):
    statement = select(Requisition).options(
        selectinload(Requisition.details).options(
            selectinload(ReqDetail.product),
            selectinload(ReqDetail.warehouse)
        ),
        selectinload(Requisition.staff)
    )
    
    if re_date:
        statement = statement.where(Requisition.reDate == re_date)
    
    if q:
        # 搜尋 ID (轉字串) 或 原因
        # 注意: SQLModel 搜尋 ID 通常需轉型，這裡簡化搜尋 Reason 即可，若要搜 ID 需精確匹配
        statement = statement.where(Requisition.reReason.contains(q))
    
    # 排序：新單在後
    statement = statement.order_by(Requisition.ReqID.desc())
    if limit > 0:
        statement = statement.offset(skip).limit(limit)
    
    result = await db.exec(statement)
    return result.all()

@router.get("/{req_id}", response_model=RequisitionRead)
async def get_requisition(req_id: int, db: AsyncSession = Depends(get_db)):
    statement = select(Requisition).where(Requisition.ReqID == req_id).options(
        selectinload(Requisition.details).options(
            selectinload(ReqDetail.product),
            selectinload(ReqDetail.warehouse)
        ),
        selectinload(Requisition.staff)
    )

    result = await db.exec(statement)
    req = result.first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return req

@router.post("/", response_model=RequisitionSchema, status_code=status.HTTP_201_CREATED)
async def create_requisition(req_data: RequisitionCreate, db: AsyncSession = Depends(get_db)):
    # 1. 建立主單 (排除 details list)
    new_req = Requisition(**req_data.model_dump(exclude={'details'}))
    
    # 若需自動生成 ID，這裡不指定 ReqID，讓 DB 處理
    db.add(new_req)
    await db.flush() # 取得 new_req.ReqID
    await db.refresh(new_req)
    
    # 2. 建立明細
    for d in req_data.details:
        new_detail = ReqDetail(
            ReqID=new_req.ReqID,
            ProductID=d.ProductID,
            rdQuantity=d.rdQuantity,
            WarehouseID=d.WarehouseID
        )
        db.add(new_detail)
    
    await db.commit()
    
    # 重新讀取 (包含 details)
    statement = select(Requisition).where(Requisition.ReqID == new_req.ReqID).options(selectinload(Requisition.details))
    result = await db.exec(statement)
    return result.first()

@router.put("/{req_id}", response_model=RequisitionSchema)
async def update_requisition(req_id: int, req_data: RequisitionCreate, db: AsyncSession = Depends(get_db)):
    # 1. 撈取舊資料
    statement = select(Requisition).where(Requisition.ReqID == req_id).options(selectinload(Requisition.details))
    result = await db.exec(statement)
    req = result.first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")
    
    # 2. 更新主單欄位
    req.reDate = req_data.reDate
    req.reReason = req_data.reReason
    req.StaffID = req_data.StaffID
    db.add(req)
    
    # 3. 更新明細 (刪除舊的 -> 加入新的)
    for detail in req.details:
        await db.delete(detail)
        
    for d in req_data.details:
        new_detail = ReqDetail(
            ReqID=req_id,
            ProductID=d.ProductID,
            rdQuantity=d.rdQuantity,
            WarehouseID=d.WarehouseID
        )
        db.add(new_detail)
        
    await db.commit()
    await db.refresh(req)
    return req

@router.delete("/{req_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requisition(req_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(Requisition, req_id)
    if not result:
        raise HTTPException(status_code=404, detail="Requisition not found")
    
    # Cascade 設定會自動刪除明細
    await db.delete(result)
    await db.commit()
    return None