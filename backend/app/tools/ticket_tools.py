"""Agent tool for creating support tickets."""
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import AgentToolLog, SupportTicket, Customer, Order
from app.repositories.ticket_repo import check_idempotency, create_ticket, get_next_ticket_id


def _log_tool(db: Session, tool_name: str, args: dict, result_summary: str, success: bool, duration_ms: float, error: str | None = None, correlation_id: str | None = None):
    log = AgentToolLog(
        correlation_id=correlation_id,
        tool_name=tool_name,
        arguments=json.dumps(args),
        result_summary=result_summary[:500] if result_summary else None,
        success=success,
        duration_ms=duration_ms,
        error_detail=error,
    )
    db.add(log)
    db.commit()


def create_support_ticket_tool(
    db: Session,
    title: str,
    description: str,
    category: str,
    priority: str,
    order_reference: str | None = None,
    customer_email: str | None = None,
    idempotency_key: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    """Tool 3: Create a validated support ticket."""
    start = time.time()

    # Validate category and priority
    valid_categories = {"Payment", "Order", "Delivery", "Refund", "Technical", "Other"}
    valid_priorities = {"Low", "Medium", "High"}
    if category not in valid_categories:
        category = "Other"
    if priority not in valid_priorities:
        priority = "Medium"

    # Build idempotency key if not provided
    if not idempotency_key:
        raw = f"{order_reference or ''}-{category}-{description[:50]}"
        idempotency_key = hashlib.sha256(raw.encode()).hexdigest()[:32]

    # Check for duplicate
    existing = check_idempotency(db, idempotency_key)
    if existing:
        duration = (time.time() - start) * 1000
        _log_tool(db, "create_support_ticket", {"category": category, "priority": priority}, f"Duplicate: {existing.ticket_id}", True, duration, correlation_id=correlation_id)
        return {
            "created": False,
            "duplicate": True,
            "ticket_id": existing.ticket_id,
            "message": f"A ticket for this issue already exists: {existing.ticket_id}",
        }

    # Resolve customer and order
    customer_id = None
    order_id = None
    if customer_email:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
    if order_reference:
        order = db.query(Order).filter(Order.order_id == order_reference).first()
        if order:
            order_id = order.id
            if not customer_id and order.customer_id:
                customer_id = order.customer_id

    ticket_id = get_next_ticket_id(db)
    assigned_team = {
        "Payment": "Payments Team",
        "Refund": "Refund Team",
        "Delivery": "Delivery Team",
        "Technical": "Tech Team",
    }.get(category, "Support Team")

    try:
        ticket = create_ticket(db, {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "order_id": order_id,
            "title": title[:500],
            "description": description[:5000],
            "category": category,
            "priority": priority,
            "status": "Open",
            "assigned_team": assigned_team,
            "idempotency_key": idempotency_key,
        })
        duration = (time.time() - start) * 1000
        _log_tool(db, "create_support_ticket", {"category": category, "priority": priority}, f"Created: {ticket_id}", True, duration, correlation_id=correlation_id)
        return {
            "created": True,
            "duplicate": False,
            "ticket_id": ticket.ticket_id,
            "message": f"Support ticket {ticket.ticket_id} has been created and assigned to {assigned_team}.",
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        _log_tool(db, "create_support_ticket", {"category": category, "priority": priority}, "Error", False, duration, str(e), correlation_id=correlation_id)
        return {
            "created": False,
            "duplicate": False,
            "ticket_id": None,
            "message": "Failed to create support ticket due to a system error.",
        }
