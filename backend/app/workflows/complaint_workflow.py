"""Automated complaint classification and ticket creation workflow."""
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import AutomationExecution
from app.tools.ticket_tools import create_support_ticket_tool

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


# ─── Deterministic Classification Rules ──────────────────────────────────────

CATEGORY_KEYWORDS = {
    "Payment": ["payment", "charged", "deducted", "double charge", "refund not received", "transaction", "card", "upi", "wallet"],
    "Order": ["wrong item", "missing item", "incorrect order", "not what i ordered", "order wrong", "item missing", "incomplete"],
    "Delivery": ["not delivered", "delivery late", "driver", "delivery person", "out for delivery", "delay", "waiting", "tracking"],
    "Refund": ["refund", "money back", "return", "get my money", "reimburse", "credit back"],
    "Technical": ["app crash", "app not working", "website down", "cannot login", "error", "bug", "technical issue", "not loading"],
}

URGENCY_KEYWORDS = {
    "high": ["urgent", "immediately", "emergency", "asap", "help me urgently", "please urgently", "very urgent", "critical"],
    "payment_failed": ["payment deducted", "charged but", "money taken", "amount deducted", "failed but charged", "payment failed but"],
    "no_delivery": ["not received", "order not arrived", "never delivered"],
}

NEGATIVE_SENTIMENT_WORDS = ["angry", "frustrated", "terrible", "awful", "horrible", "unacceptable", "disgusting", "worst", "scam"]


def classify_complaint(complaint_text: str) -> dict:
    """
    Deterministically classify complaint text into category, sentiment, urgency.
    This is application-side logic — no LLM needed for classification.
    """
    lower = complaint_text.lower()

    # Category detection
    category = "Other"
    max_matches = 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in lower)
        if matches > max_matches:
            max_matches = matches
            category = cat

    # Urgency score (0.0 to 1.0)
    urgency_score = 0.3  # baseline
    for key, keywords in URGENCY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            if key == "high":
                urgency_score = max(urgency_score, 0.9)
            else:
                urgency_score = max(urgency_score, 0.8)

    # Length signal
    if len(complaint_text) > 200:
        urgency_score = min(urgency_score + 0.1, 1.0)

    # Sentiment
    negative_count = sum(1 for w in NEGATIVE_SENTIMENT_WORDS if w in lower)
    exclamation_count = complaint_text.count("!")
    if negative_count >= 2 or exclamation_count >= 3:
        sentiment = "Highly Negative"
        urgency_score = min(urgency_score + 0.15, 1.0)
    elif negative_count >= 1 or exclamation_count >= 1:
        sentiment = "Negative"
        urgency_score = min(urgency_score + 0.05, 1.0)
    else:
        sentiment = "Neutral"

    # Priority based on urgency score and category
    if urgency_score >= 0.75 or category == "Payment":
        priority = "High"
    elif urgency_score >= 0.5 or category in ("Order", "Delivery"):
        priority = "Medium"
    else:
        priority = "Low"

    # Override: payment with failed order is always High
    if category == "Payment" and any(kw in lower for kw in URGENCY_KEYWORDS["payment_failed"]):
        priority = "High"
        urgency_score = max(urgency_score, 0.9)

    reasoning = (
        f"Category '{category}' detected with {max_matches} keyword match(es). "
        f"Sentiment: {sentiment} ({negative_count} negative words, {exclamation_count} exclamations). "
        f"Urgency score: {urgency_score:.2f}. Priority: {priority}."
    )

    return {
        "category": category,
        "sentiment": sentiment,
        "urgency_score": round(urgency_score, 2),
        "priority": priority,
        "reasoning": reasoning,
    }


def run_complaint_workflow(
    db: Session,
    complaint_text: str,
    order_reference: str | None = None,
    customer_email: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """
    End-to-end complaint processing workflow.
    Returns structured result with all steps recorded.
    """
    execution_id = str(uuid.uuid4())
    start = time.time()
    steps = []

    def add_step(step: str, status: str, detail: str):
        steps.append({
            "step": step,
            "status": status,
            "detail": detail,
            "timestamp": utcnow().isoformat(),
        })
        logger.info(f"[{execution_id}] Step '{step}': {status} — {detail}")

    # Step 1: Receive complaint
    add_step("receive_complaint", "success", f"Complaint received ({len(complaint_text)} chars)")

    # Step 2: Extract order reference
    if not order_reference:
        match = re.search(r"\bORD-\d+\b", complaint_text, re.IGNORECASE)
        if match:
            order_reference = match.group(0).upper()
    add_step("extract_references", "success", f"Order reference: {order_reference or 'None detected'}")

    # Step 3: Classify
    try:
        classification = classify_complaint(complaint_text)
        add_step("classify_complaint", "success",
                 f"Category: {classification['category']}, Priority: {classification['priority']}, Sentiment: {classification['sentiment']}")
    except Exception as e:
        add_step("classify_complaint", "failed", str(e))
        classification = {"category": "Other", "sentiment": "Neutral", "urgency_score": 0.5, "priority": "Medium", "reasoning": "Classification failed"}

    # Step 4: Priority validation (application-side enforcement)
    if classification["category"] == "Payment" or classification["urgency_score"] >= 0.85:
        if classification["priority"] != "High":
            classification["priority"] = "High"
            add_step("priority_validation", "success", "Priority escalated to High by deterministic rules")
        else:
            add_step("priority_validation", "success", "Priority High confirmed by deterministic rules")
    else:
        add_step("priority_validation", "success", f"Priority {classification['priority']} confirmed")

    # Step 5: Create support ticket
    ticket_result = None
    ticket_id = None
    ticket_created = False
    try:
        title = f"{classification['category']} Issue: {complaint_text[:80]}..."
        ticket_result = create_support_ticket_tool(
            db=db,
            title=title,
            description=complaint_text,
            category=classification["category"],
            priority=classification["priority"],
            order_reference=order_reference,
            customer_email=customer_email,
            idempotency_key=idempotency_key,
            correlation_id=execution_id,
        )
        ticket_id = ticket_result.get("ticket_id")
        ticket_created = ticket_result.get("created", False)
        if ticket_result.get("duplicate"):
            add_step("create_ticket", "duplicate", f"Existing ticket: {ticket_id}")
            ticket_created = True  # Consider it success for workflow
        elif ticket_result.get("created"):
            add_step("create_ticket", "success", f"Ticket {ticket_id} created and assigned")
        else:
            add_step("create_ticket", "failed", ticket_result.get("message", "Unknown error"))
    except Exception as e:
        add_step("create_ticket", "failed", str(e))

    # Step 6: Notification log (local — no external sends)
    notification_logged = False
    try:
        notification_msg = (
            f"[NOTIFICATION LOG]\n"
            f"Execution: {execution_id}\n"
            f"Category: {classification['category']} | Priority: {classification['priority']}\n"
            f"Ticket: {ticket_id or 'Not created'}\n"
            f"Order: {order_reference or 'N/A'}\n"
            f"Complaint: {complaint_text[:100]}...\n"
            f"Timestamp: {utcnow().isoformat()}"
        )
        logger.info(notification_msg)
        notification_logged = True
        add_step("notification_log", "success", f"Notification logged locally for ticket {ticket_id}")
    except Exception as e:
        add_step("notification_log", "failed", str(e))

    # Determine overall status
    overall_status = "success"
    if not ticket_created and not ticket_result:
        overall_status = "failed"
    elif not ticket_created:
        overall_status = "partial"

    duration_ms = (time.time() - start) * 1000

    # Persist execution record
    try:
        exec_record = AutomationExecution(
            execution_id=execution_id,
            complaint_text=complaint_text[:2000],
            order_reference=order_reference,
            category=classification["category"],
            sentiment=classification["sentiment"],
            urgency_score=classification["urgency_score"],
            priority=classification["priority"],
            ticket_id=ticket_id,
            ticket_created=ticket_created,
            notification_logged=notification_logged,
            status=overall_status,
            error_detail=None if overall_status == "success" else steps[-1].get("detail"),
            workflow_steps=json.dumps(steps),
            duration_ms=duration_ms,
        )
        db.add(exec_record)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to persist execution record: {e}")

    message = (
        f"Your complaint has been classified as a **{classification['category']}** issue with **{classification['priority']}** priority. "
        + (f"Support ticket **{ticket_id}** has been created." if ticket_created else "We encountered an issue creating your ticket. Please contact support directly.")
    )

    return {
        "execution_id": execution_id,
        "classification": classification,
        "ticket_id": ticket_id,
        "ticket_created": ticket_created,
        "notification_logged": notification_logged,
        "workflow_steps": steps,
        "status": overall_status,
        "message": message,
        "duration_ms": duration_ms,
    }
