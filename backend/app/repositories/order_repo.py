"""Repository for order data access."""
from sqlalchemy.orm import Session
from app.models.models import Order, Customer


def get_order_by_order_id(db: Session, order_id: str) -> Order | None:
    return db.query(Order).filter(Order.order_id == order_id).first()


def get_orders_paginated(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    search: str | None = None,
):
    q = db.query(Order).join(Order.customer, isouter=True)
    if status and status != "All statuses":
        q = q.filter(Order.status == status)
    if search:
        search_term = f"%{search}%"
        q = q.filter(
            (Order.order_id.ilike(search_term))
            | (Customer.name.ilike(search_term))
            | (Customer.phone.ilike(search_term))
        )
    total = q.count()
    items = (
        q.order_by(Order.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total


def update_order_status(db: Session, order: Order, new_status: str) -> Order:
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order
