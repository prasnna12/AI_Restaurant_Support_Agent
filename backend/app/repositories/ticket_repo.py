"""Repository for support ticket data access."""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.models import SupportTicket, TicketTimeline, Customer, Order


def get_next_ticket_id(db: Session) -> str:
    count = db.query(SupportTicket).count()
    return f"TKT-{count + 1:04d}"


def create_ticket(db: Session, data: dict) -> SupportTicket:
    ticket = SupportTicket(**data)
    db.add(ticket)
    db.flush()
    tl = TicketTimeline(
        ticket_id=ticket.id,
        actor="System",
        action="Ticket created",
        details=f"Ticket {ticket.ticket_id} created via {data.get('assigned_team', 'System')}",
    )
    db.add(tl)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket_by_id(db: Session, ticket_id: str) -> SupportTicket | None:
    return db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()


def get_tickets_paginated(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    search: str | None = None,
):
    q = db.query(SupportTicket)
    if status:
        q = q.filter(SupportTicket.status == status)
    if priority:
        q = q.filter(SupportTicket.priority == priority)
    if category:
        q = q.filter(SupportTicket.category == category)
    if search:
        q = q.filter(
            or_(
                SupportTicket.ticket_id.ilike(f"%{search}%"),
                SupportTicket.title.ilike(f"%{search}%"),
                SupportTicket.description.ilike(f"%{search}%"),
            )
        )
    total = q.count()
    items = q.order_by(SupportTicket.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def update_ticket_status(db: Session, ticket: SupportTicket, new_status: str, comment: str | None, actor: str) -> SupportTicket:
    old_status = ticket.status
    ticket.status = new_status
    ticket.updated_at = datetime.now(timezone.utc)
    if new_status == "Resolved":
        ticket.resolved_at = datetime.now(timezone.utc)
    tl = TicketTimeline(
        ticket_id=ticket.id,
        actor=actor,
        action=f"Status changed from {old_status} to {new_status}",
        details=comment or f"Status updated to {new_status}",
    )
    db.add(tl)
    db.commit()
    db.refresh(ticket)
    return ticket


def check_idempotency(db: Session, key: str) -> SupportTicket | None:
    return db.query(SupportTicket).filter(SupportTicket.idempotency_key == key).first()
