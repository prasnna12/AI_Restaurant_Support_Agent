"""Dashboard summary and activity endpoints."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.models import AdminUser, Order, SupportTicket, Customer, AutomationExecution, Conversation
from app.schemas.schemas import DashboardSummary, DashboardActivity

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status.in_(["pending", "confirmed", "preparing"])).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "Open").count()
    high_priority = db.query(SupportTicket).filter(SupportTicket.priority == "High", SupportTicket.status != "Resolved").count()
    resolved_tickets = db.query(SupportTicket).filter(SupportTicket.status == "Resolved").count()
    escalated_tickets = db.query(SupportTicket).filter(SupportTicket.status == "Escalated").count()
    total_customers = db.query(Customer).count()
    total_conversations = db.query(Conversation).count()

    # Category distribution
    tickets = db.query(SupportTicket).all()
    category_dist = defaultdict(int)
    for t in tickets:
        category_dist[t.category] += 1

    return DashboardSummary(
        total_orders=total_orders,
        pending_orders=pending_orders,
        open_tickets=open_tickets,
        high_priority_tickets=high_priority,
        resolved_tickets=resolved_tickets,
        total_customers=total_customers,
        total_conversations=total_conversations,
        escalated_tickets=escalated_tickets,
        category_distribution=dict(category_dist),
    )


@router.get("/activity")
def get_activity(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    # Recent tickets
    recent_tickets = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(5).all()
    recent_execs = db.query(AutomationExecution).order_by(AutomationExecution.created_at.desc()).limit(5).all()
    recent_convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(5).all()

    # Chart data: tickets by date (last 7 days)
    chart_data = []
    for i in range(6, -1, -1):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59)
        count = db.query(SupportTicket).filter(
            SupportTicket.created_at >= day_start,
            SupportTicket.created_at <= day_end
        ).count()
        chart_data.append({"date": day.strftime("%b %d"), "tickets": count})

    return {
        "recent_tickets": [
            {"ticket_id": t.ticket_id, "title": t.title[:50], "priority": t.priority, "status": t.status, "created_at": t.created_at.isoformat()}
            for t in recent_tickets
        ],
        "recent_executions": [
            {"execution_id": e.execution_id, "short_id": e.execution_id[:8], "category": e.category, "priority": e.priority, "status": e.status, "created_at": e.created_at.isoformat()}
            for e in recent_execs
        ],
        "recent_conversations": [
            {"session_id": c.session_id, "short_id": c.session_id[:8], "title": c.title[:40], "updated_at": c.updated_at.isoformat()}
            for c in recent_convs
        ],
        "chart_data": chart_data,
        "sample_data_notice": "This dashboard displays sample/demo data for demonstration purposes.",
    }
