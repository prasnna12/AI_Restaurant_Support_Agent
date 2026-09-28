"""Automation and complaint workflow endpoints."""
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.models import AdminUser, AutomationExecution
from app.workflows.complaint_workflow import run_complaint_workflow
from app.schemas.schemas import (
    ComplaintRequest, ComplaintWorkflowResponse, ComplaintClassification,
    WorkflowStepResult, ExecutionOut
)
from datetime import datetime, timezone

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.post("/complaints", response_model=ComplaintWorkflowResponse)
def process_complaint(req: ComplaintRequest, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    result = run_complaint_workflow(
        db=db,
        complaint_text=req.complaint_text,
        order_reference=req.order_reference,
        customer_email=req.customer_email,
        idempotency_key=req.idempotency_key,
    )
    classification = ComplaintClassification(**result["classification"])
    steps = [WorkflowStepResult(
        step=s["step"], status=s["status"], detail=s["detail"],
        timestamp=datetime.fromisoformat(s["timestamp"])
    ) for s in result["workflow_steps"]]
    return ComplaintWorkflowResponse(
        execution_id=result["execution_id"],
        classification=classification,
        ticket_id=result.get("ticket_id"),
        ticket_created=result["ticket_created"],
        notification_logged=result["notification_logged"],
        workflow_steps=steps,
        status=result["status"],
        message=result["message"],
    )


@router.get("/executions", response_model=list[ExecutionOut])
def list_executions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    offset = (page - 1) * per_page
    execs = db.query(AutomationExecution).order_by(AutomationExecution.created_at.desc()).offset(offset).limit(per_page).all()
    return [ExecutionOut(
        id=e.id, execution_id=e.execution_id, complaint_text=e.complaint_text[:200],
        order_reference=e.order_reference, category=e.category, sentiment=e.sentiment,
        urgency_score=e.urgency_score, priority=e.priority, ticket_id=e.ticket_id,
        ticket_created=e.ticket_created, notification_logged=e.notification_logged,
        status=e.status, error_detail=e.error_detail, duration_ms=e.duration_ms, created_at=e.created_at
    ) for e in execs]


@router.get("/executions/{execution_id}")
def get_execution(execution_id: str, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    exec_rec = db.query(AutomationExecution).filter(AutomationExecution.execution_id == execution_id).first()
    if not exec_rec:
        raise HTTPException(status_code=404, detail="Execution not found")
    import json
    steps = []
    try:
        steps = json.loads(exec_rec.workflow_steps or "[]")
    except Exception:
        pass
    return {
        "id": exec_rec.id,
        "execution_id": exec_rec.execution_id,
        "complaint_text": exec_rec.complaint_text,
        "order_reference": exec_rec.order_reference,
        "category": exec_rec.category,
        "sentiment": exec_rec.sentiment,
        "urgency_score": exec_rec.urgency_score,
        "priority": exec_rec.priority,
        "ticket_id": exec_rec.ticket_id,
        "ticket_created": exec_rec.ticket_created,
        "notification_logged": exec_rec.notification_logged,
        "status": exec_rec.status,
        "error_detail": exec_rec.error_detail,
        "workflow_steps": steps,
        "duration_ms": exec_rec.duration_ms,
        "created_at": exec_rec.created_at.isoformat(),
    }
