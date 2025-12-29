from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.supplier import Supplier as SupplierSchema, SupplierCreate
from app.models.supplier import Supplier as SupplierModel
from app.core.database import get_db
from sqlalchemy.exc import IntegrityError
from app.schemas.error import HTTPError

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

@router.get("/", response_model=List[SupplierSchema])
async def get_suppliers(
    q: Optional[str] = Query(None, description="搜尋供應商名稱"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db)
):
    statement = select(SupplierModel)
    if q:
        statement = statement.where(SupplierModel.suName.contains(q))
    
    if limit > 0:
        statement = statement.offset(skip).limit(limit)

    result = await db.exec(statement)
    return result.all()

@router.get("/{supplier_id}", response_model=SupplierSchema)
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(SupplierModel, supplier_id)
    if not result:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return result

@router.post("/", response_model=SupplierSchema, status_code=status.HTTP_201_CREATED)
async def create_supplier(supplier: SupplierCreate, db: AsyncSession = Depends(get_db)):
    new_supplier = SupplierModel.model_validate(supplier)
    db.add(new_supplier)
    await db.commit()
    await db.refresh(new_supplier)
    return new_supplier

@router.put("/{supplier_id}", response_model=SupplierSchema)
async def update_supplier(supplier_id: int, updated_supplier: SupplierCreate, db: AsyncSession = Depends(get_db)):
    db_supplier = await db.get(SupplierModel, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    data = updated_supplier.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_supplier, key, value)
        
    db.add(db_supplier)
    await db.commit()
    await db.refresh(db_supplier)
    return db_supplier

@router.delete(
    "/{supplier_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": HTTPError, "description": "Integrity Error: Staff has linked orders"},
    }
)
async def delete_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    db_supplier = await db.get(SupplierModel, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
        
    try:
        await db.delete(db_supplier)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無法刪除：該供應商尚有未結案的進貨單。"
        )
    return None