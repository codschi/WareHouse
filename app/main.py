from fastapi import FastAPI, Request
from app.api import products, requisitions, staffs, suppliers, inboundorders, warehouse, ai

from contextlib import asynccontextmanager
from app.core.database import init_db, get_db_session_context
from app.core.seed import create_initial_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時建立資料庫 Tables (SQLModel)
    await init_db()

    is_need_seed = True
    if is_need_seed:
        from app.core.database import engine
        from sqlmodel.ext.asyncio.session import AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            await create_initial_data(session)

    yield

app = FastAPI(title="物流倉儲管理系統 API", version="1.0.0", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api/v1")
app.include_router(suppliers.router, prefix="/api/v1")
app.include_router(staffs.router, prefix="/api/v1")
app.include_router(inboundorders.router, prefix="/api/v1")
app.include_router(warehouse.router, prefix="/api/v1")
app.include_router(requisitions.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
from app.api import dashboard
app.include_router(dashboard.router, prefix="/api/v1")
from app.api import auth
app.include_router(auth.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "WMS API is running", "auth_hint": "admin/admin"}