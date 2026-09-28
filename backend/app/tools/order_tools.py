"""Agent tools for order-related operations."""
import json
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.models import AgentToolLog
from app.repositories.order_repo import get_order_by_order_id


def _log_tool(db: Session, tool_name: str, args: dict, result_summary: str, success: bool, duration_ms: float, error: str | None = None, correlation_id: str | None = None):
    log = AgentToolLog(
        correlation_id=correlation_id,
        tool_name=tool_name,
        arguments=json.dumps({k: v for k, v in args.items() if k not in ("password", "token", "key")}),
        result_summary=result_summary[:500] if result_summary else None,
        success=success,
        duration_ms=duration_ms,
        error_detail=error,
    )
    db.add(log)
    db.commit()


def get_order_status(db: Session, order_id: str, correlation_id: str | None = None) -> dict:
    """Tool 1: Retrieve the current status of an order."""
    start = time.time()
    order_id = order_id.strip().upper()
    try:
        order = get_order_by_order_id(db, order_id)
        duration = (time.time() - start) * 1000

        if not order:
            result = {"found": False, "order_id": order_id, "message": f"Order {order_id} was not found in our system."}
            _log_tool(db, "get_order_status", {"order_id": order_id}, "Not found", True, duration, correlation_id=correlation_id)
            return result

        result = {
            "found": True,
            "order_id": order.order_id,
            "status": order.status,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        }
        _log_tool(db, "get_order_status", {"order_id": order_id}, f"Found: {order.status}", True, duration, correlation_id=correlation_id)
        return result
    except Exception as e:
        duration = (time.time() - start) * 1000
        _log_tool(db, "get_order_status", {"order_id": order_id}, "Error", False, duration, str(e), correlation_id=correlation_id)
        return {"found": False, "order_id": order_id, "message": "Unable to retrieve order status due to a system error. Please try again."}


def get_order_details(db: Session, order_id: str, correlation_id: str | None = None) -> dict:
    """Tool 2: Retrieve full order details."""
    start = time.time()
    order_id = order_id.strip().upper()
    try:
        order = get_order_by_order_id(db, order_id)
        duration = (time.time() - start) * 1000

        if not order:
            result = {"found": False, "order_id": order_id, "message": f"Order {order_id} was not found."}
            _log_tool(db, "get_order_details", {"order_id": order_id}, "Not found", True, duration, correlation_id=correlation_id)
            return result

        items = [
            {"name": i.name, "quantity": i.quantity, "unit_price": i.unit_price, "total_price": i.total_price}
            for i in order.items
        ]
        result = {
            "found": True,
            "order_id": order.order_id,
            "status": order.status,
            "customer_name": order.customer.name if order.customer else "Unknown",
            "items": items,
            "subtotal": order.subtotal,
            "tax": order.tax,
            "grand_total": order.grand_total,
            "notes": order.notes or "",
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        }
        _log_tool(db, "get_order_details", {"order_id": order_id}, f"Found with {len(items)} items", True, duration, correlation_id=correlation_id)
        return result
    except Exception as e:
        duration = (time.time() - start) * 1000
        _log_tool(db, "get_order_details", {"order_id": order_id}, "Error", False, duration, str(e), correlation_id=correlation_id)
        return {"found": False, "order_id": order_id, "message": "Unable to retrieve order details due to a system error."}
