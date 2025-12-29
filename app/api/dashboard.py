from fastapi import APIRouter, Depends
from sqlalchemy import func, case, text, select
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import date, datetime
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.product import Product
from app.models.inbound_order import InboundOrder, InboundDetail
from app.models.requisition import Requisition, ReqDetail
from app.models.staff import Staff

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    today = date.today()
    current_month_start = date(today.year, today.month, 1)

    # 1. KPIs
    # Total SKU
    sku_result = await db.exec(select(func.count(Product.ProductID)))
    total_sku = sku_result.one()

    # Monthly Inbound (Filter by ioDate >= first day of month)
    inbound_result = await db.exec(select(func.count(InboundOrder.InboundID)).where(InboundOrder.ioDate >= current_month_start))
    monthly_inbound = inbound_result.one()

    # Monthly Requisition
    req_result = await db.exec(select(func.count(Requisition.ReqID)).where(Requisition.reDate >= current_month_start))
    monthly_req = req_result.one()

    # 2. Low Stock Alerts (< 10)
    # Strategy: Fetch all Product IDs, then Aggregate In/Out separately to avoid complex massive joins/group-by issues in simple SQL
    
    # Get all products
    products = (await db.exec(select(Product))).all()
    
    # Aggregate Inbound by Product
    in_stmt = select(InboundDetail.ProductID, func.sum(InboundDetail.idQuantity))\
              .join(InboundOrder)\
              .where(InboundOrder.Status == 'Completed')\
              .group_by(InboundDetail.ProductID)
    in_data = (await db.exec(in_stmt)).all()
    in_map = {row[0]: row[1] for row in in_data} # {ProductID: TotalIn}

    # Aggregate Outbound by Product
    out_stmt = select(ReqDetail.ProductID, func.sum(ReqDetail.rdQuantity))\
               .join(Requisition)\
               .where(Requisition.Status == 'Completed')\
               .group_by(ReqDetail.ProductID)
    out_data = (await db.exec(out_stmt)).all()
    out_map = {row[0]: row[1] for row in out_data} # {ProductID: TotalOut}

    low_stock_items = []
    
    # Calculate Stock
    for p in products:
        total_in = in_map.get(p.ProductID, 0)
        total_out = out_map.get(p.ProductID, 0)
        current_stock = total_in - total_out
        
        if current_stock < 10:
            low_stock_items.append({
                "ProductID": p.ProductID,
                "prName": p.prName,
                "current_stock": current_stock,
                "warehouse_hint": "多倉堆放" # Simplified for dashboard view
            })

    # 3. Recent Activities (Top 5 Mixed)
    # Fetch Top 5 Inbound
    recent_inbounds = (await db.exec(select(InboundOrder).order_by(InboundOrder.ioDate.desc(), InboundOrder.InboundID.desc()).limit(5))).all()
    # Fetch Top 5 Requisitions
    recent_reqs = (await db.exec(select(Requisition).order_by(Requisition.reDate.desc(), Requisition.ReqID.desc()).limit(5))).all()

    # Normalize and Merge
    activities = []
    for i in recent_inbounds:
        activities.append({
            "date": i.ioDate,
            "type": "進貨單",
            "id": i.InboundID,
            "staff": f"Staff #{i.StaffID}", # In real app, join Staff to get name. But StaffID is ok for now or we lazy load
            "timestamp": datetime.combine(i.ioDate, datetime.min.time()).timestamp() # Approximate for sorting
        })
    
    for r in recent_reqs:
        activities.append({
            "date": r.reDate,
            "type": "領料單",
            "id": r.ReqID,
            "staff": f"Staff #{r.StaffID}",
            "timestamp": datetime.combine(r.reDate, datetime.min.time()).timestamp()
        })
    
    # Sort by Date descending
    activities.sort(key=lambda x: x['date'], reverse=True)
    activities = activities[:5]

    return {
        "kpi": {
            "total_sku": total_sku,
            "monthly_inbound": monthly_inbound,
            "monthly_req": monthly_req
        },
        "low_stock": low_stock_items,
        "activities": activities
    }
