"""Repository for order data access."""
from sqlalchemy.orm import Session
from app.models.models import Order, Customer


def get_order_by_order_id(db: Session, order_id: str) -> Order | None:
    return db.query(Order).filter(Order.order_id == order_id).first()


def get_orders_paginated(db: Session, page: int = 1, per_page: int = 20, status: str | None = None):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    total = q.count()
    items = q.order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return items, total
