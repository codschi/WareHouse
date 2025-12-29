from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.staff import Staff as StaffSchema, StaffCreate
from app.models.staff import Staff as StaffModel
from app.core.database import get_db
from sqlalchemy.exc import IntegrityError
from app.schemas.error import HTTPError

router = APIRouter(prefix="/staff", tags=["Staff"])

@router.get("/", response_model=List[StaffSchema])
async def get_all_staff(
    q: Optional[str] = Query(None, description="搜尋員工姓名或部門"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=0, le=100),
    db: AsyncSession = Depends(get_db) # DI DB Session
):
    statement = select(StaffModel)
    
    if q:
        statement = statement.where(
            (StaffModel.stName.contains(q)) | (StaffModel.stDept.contains(q))
        )
    
    if limit > 0:
        statement = statement.offset(skip).limit(limit)
    
    result = await db.exec(statement)
    return result.all()

@router.get("/{staff_id}", response_model=StaffSchema)
async def get_staff(staff_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(StaffModel, staff_id)
    if not result:
        raise HTTPException(status_code=404, detail="Staff not found")
    return result

@router.post("/", response_model=StaffSchema, status_code=status.HTTP_201_CREATED)
async def create_staff(staff: StaffCreate, db: AsyncSession = Depends(get_db)):
    # 將 Schema 轉為 Model
    new_staff = StaffModel.model_validate(staff)
    
    db.add(new_staff)
    await db.commit()
    await db.refresh(new_staff) # 刷新以取得 DB 自動生成的 StaffID
    return new_staff

@router.put("/{staff_id}", response_model=StaffSchema)
async def update_staff(staff_id: int, updated_staff: StaffCreate, db: AsyncSession = Depends(get_db)):
    # 先查
    db_staff = await db.get(StaffModel, staff_id)
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Phase 5: Prevent demoting Super Admin
    if db_staff.username == "Admin":
        # Check if trying to remove manager rights
        staff_data = updated_staff.model_dump(exclude_unset=True)
        if "is_manager" in staff_data and not staff_data["is_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot revoke Manager rights from Super Admin."
            )
    
    # 更新欄位
    staff_data = updated_staff.model_dump(exclude_unset=True)
    for key, value in staff_data.items():
        setattr(db_staff, key, value)
        
    db.add(db_staff)
    await db.commit()
    await db.refresh(db_staff)
    return db_staff

@router.delete(
    "/{staff_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": HTTPError, "description": "Integrity Error: Staff has linked orders"},
    }
)
async def delete_staff(staff_id: int, db: AsyncSession = Depends(get_db)):
    db_staff = await db.get(StaffModel, staff_id)
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Phase 5: Prevent deleting Super Admin
    if db_staff.username == "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete the Super Admin account."
        )
        
    try:
        await db.delete(db_staff)
        await db.commit()
    except IntegrityError:
        # 捕捉資料庫的關聯錯誤 (Foreign Key Violation)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="無法刪除：該員工有正在經手的單據 (如進貨單、領料單)。"
        )
    
    return None