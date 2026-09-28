"""Order endpoints."""
import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.models import AdminUser, Customer
from app.repositories.order_repo import get_order_by_order_id, get_orders_paginated
from app.schemas.schemas import OrderDetailOut, OrderListItem, OrderStatusOut, PaginatedOrders

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=PaginatedOrders)
def list_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    items, total = get_orders_paginated(db, page, per_page, status)
    result = []
    for o in items:
        result.append(OrderListItem(
            order_id=o.order_id,
            customer_name=o.customer.name if o.customer else "Unknown",
            status=o.status,
            grand_total=o.grand_total,
            item_count=len(o.items),
            created_at=o.created_at,
        ))
    return PaginatedOrders(items=result, total=total, page=page, per_page=per_page, pages=math.ceil(total / per_page))


@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(order_id: str, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    order = get_order_by_order_id(db, order_id.upper())
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    from app.schemas.schemas import OrderItemOut
    items = [OrderItemOut(name=i.name, quantity=i.quantity, unit_price=i.unit_price, total_price=i.total_price) for i in order.items]
    return OrderDetailOut(
        order_id=order.order_id,
        status=order.status,
        customer_name=order.customer.name if order.customer else "Unknown",
        items=items,
        subtotal=order.subtotal,
        tax=order.tax,
        grand_total=order.grand_total,
        notes=order.notes or "",
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/{order_id}/status", response_model=OrderStatusOut)
def get_order_status_endpoint(order_id: str, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    order = get_order_by_order_id(db, order_id.upper())
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return OrderStatusOut(order_id=order.order_id, status=order.status, updated_at=order.updated_at, found=True)
