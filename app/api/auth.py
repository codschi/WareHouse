from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from app.models.staff import Staff
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Plain text password check as requested
    statement = select(Staff).where(Staff.username == request.username).where(Staff.password == request.password)
    result = await db.exec(statement)
    user = result.first()

    if not user:
        # For security usually generic msg, but for internal dev specific is ok
        return LoginResponse(success=False, message="Invalid username or password")

    return LoginResponse(
        success=True,
        staff_id=user.StaffID,
        username=user.username,
        is_manager=user.is_manager,
        message="Login successful"
    )
