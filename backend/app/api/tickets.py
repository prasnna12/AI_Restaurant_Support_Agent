"""Support ticket endpoints."""
import math, hashlib
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.models import AdminUser, Customer, Order, TicketTimeline
from app.repositories.ticket_repo import (
    create_ticket, get_ticket_by_id, get_tickets_paginated,
    update_ticket_status, check_idempotency, get_next_ticket_id
)
from app.schemas.schemas import (
    PaginatedTickets, TicketCreateRequest, TicketListItem,
    TicketOut, TicketStatusUpdate, TicketTimelineOut
)

router = APIRouter(prefix="/api/support/tickets", tags=["tickets"])


def _ticket_to_list_item(ticket) -> TicketListItem:
    return TicketListItem(
        id=ticket.id,
        ticket_id=ticket.ticket_id,
        title=ticket.title,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        assigned_team=ticket.assigned_team,
        customer_name=ticket.customer.name if ticket.customer else None,
        order_reference=ticket.order.order_id if ticket.order else None,
        created_at=ticket.created_at,
    )


def _ticket_to_detail(ticket) -> TicketOut:
    timeline = [TicketTimelineOut(actor=t.actor, action=t.action, details=t.details, created_at=t.created_at) for t in ticket.timeline]
    return TicketOut(
        id=ticket.id,
        ticket_id=ticket.ticket_id,
        title=ticket.title,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        assigned_team=ticket.assigned_team,
        customer_name=ticket.customer.name if ticket.customer else None,
        order_reference=ticket.order.order_id if ticket.order else None,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        timeline=timeline,
    )


@router.get("", response_model=PaginatedTickets)
def list_tickets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    items, total = get_tickets_paginated(db, page, per_page, status, priority, category, search)
    return PaginatedTickets(
        items=[_ticket_to_list_item(t) for t in items],
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 1,
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return _ticket_to_detail(ticket)


@router.post("", response_model=TicketOut, status_code=201)
def create_new_ticket(req: TicketCreateRequest, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    # Idempotency
    ikey = req.idempotency_key or hashlib.sha256(f"{req.order_reference}-{req.category}-{req.description[:50]}".encode()).hexdigest()[:32]
    existing = check_idempotency(db, ikey)
    if existing:
        return _ticket_to_detail(existing)

    customer_id = None
    order_id = None
    if req.order_reference:
        order = db.query(Order).filter(Order.order_id == req.order_reference).first()
        if order:
            order_id = order.id
            customer_id = order.customer_id

    ticket_id = get_next_ticket_id(db)
    ticket = create_ticket(db, {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "order_id": order_id,
        "title": req.title,
        "description": req.description,
        "category": req.category,
        "priority": req.priority,
        "status": "Open",
        "assigned_team": {"Payment": "Payments Team", "Refund": "Refund Team", "Delivery": "Delivery Team", "Technical": "Tech Team"}.get(req.category, "Support Team"),
        "idempotency_key": ikey,
    })
    return _ticket_to_detail(ticket)


@router.put("/{ticket_id}/status", response_model=TicketOut)
def update_status(
    ticket_id: str,
    req: TicketStatusUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    ticket = update_ticket_status(db, ticket, req.status, req.comment, actor=admin.name)
    return _ticket_to_detail(ticket)
