"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ─── Auth ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminProfile(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Orders ─────────────────────────────────────────────────────────────────

class OrderItemOut(BaseModel):
    name: str
    quantity: int
    unit_price: float
    total_price: float
    model_config = {"from_attributes": True}


class OrderStatusOut(BaseModel):
    order_id: str
    status: str
    updated_at: datetime
    found: bool = True


class OrderDetailOut(BaseModel):
    order_id: str
    status: str
    customer_name: str
    items: list[OrderItemOut]
    subtotal: float
    tax: float
    grand_total: float
    notes: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class OrderListItem(BaseModel):
    order_id: str
    customer_name: str
    status: str
    grand_total: float
    item_count: int
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedOrders(BaseModel):
    items: list[OrderListItem]
    total: int
    page: int
    per_page: int
    pages: int


# ─── Support Tickets ─────────────────────────────────────────────────────────

class TicketCreateRequest(BaseModel):
    customer_name: Optional[str] = None
    order_reference: Optional[str] = None
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10, max_length=5000)
    category: str = Field(..., pattern="^(Payment|Order|Delivery|Refund|Technical|Other)$")
    priority: str = Field(..., pattern="^(Low|Medium|High)$")
    idempotency_key: Optional[str] = None

    @field_validator("description")
    @classmethod
    def no_sql_injection(cls, v: str) -> str:
        dangerous = ["DROP TABLE", "DELETE FROM", "INSERT INTO", "EXEC(", "--", "/*"]
        upper = v.upper()
        for d in dangerous:
            if d in upper:
                raise ValueError("Invalid characters in description")
        return v


class TicketStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(Open|In Progress|Resolved|Escalated)$")
    comment: Optional[str] = Field(None, max_length=1000)


class TicketTimelineOut(BaseModel):
    actor: str
    action: str
    details: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class TicketOut(BaseModel):
    id: int
    ticket_id: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    assigned_team: str
    customer_name: Optional[str]
    order_reference: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    timeline: list[TicketTimelineOut] = []
    model_config = {"from_attributes": True}


class TicketListItem(BaseModel):
    id: int
    ticket_id: str
    title: str
    category: str
    priority: str
    status: str
    assigned_team: str
    customer_name: Optional[str]
    order_reference: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedTickets(BaseModel):
    items: list[TicketListItem]
    total: int
    page: int
    per_page: int
    pages: int


# ─── Agent Chat ───────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        # Basic prompt injection defense
        injection_patterns = [
            "ignore previous instructions",
            "ignore all previous",
            "you are now",
            "system prompt",
            "jailbreak",
            "disregard your instructions",
        ]
        lower = v.lower()
        for pat in injection_patterns:
            if pat in lower:
                raise ValueError("Message contains disallowed content")
        return v.strip()


class ToolCallInfo(BaseModel):
    tool_name: str
    success: bool
    summary: str


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    tool_calls: list[ToolCallInfo] = []
    sources: list[str] = []
    is_fallback: bool = False
    timestamp: datetime


class ConversationOut(BaseModel):
    id: int
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    tool_calls: Optional[str]
    sources: Optional[str]
    is_fallback: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ConversationDetailOut(BaseModel):
    conversation: ConversationOut
    messages: list[MessageOut]


# ─── Knowledge Base ───────────────────────────────────────────────────────────

class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    content: str = Field(..., min_length=10, max_length=50000)
    category: str = Field(default="General", max_length=100)
    source: Optional[str] = Field(None, max_length=255)


class DocumentOut(BaseModel):
    id: int
    doc_id: str
    title: str
    category: str
    source: Optional[str]
    is_indexed: bool
    created_at: datetime
    updated_at: datetime
    content_preview: str = ""
    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=4, ge=1, le=10)


class KnowledgeSearchResult(BaseModel):
    doc_id: str
    title: str
    content_snippet: str
    score: float
    source: Optional[str]


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchResult]
    index_available: bool


# ─── Automation ───────────────────────────────────────────────────────────────

class ComplaintRequest(BaseModel):
    complaint_text: str = Field(..., min_length=10, max_length=3000)
    order_reference: Optional[str] = Field(None, pattern=r"^ORD-\d+$")
    customer_email: Optional[str] = None
    idempotency_key: Optional[str] = None


class ComplaintClassification(BaseModel):
    category: str
    sentiment: str
    urgency_score: float = Field(..., ge=0.0, le=1.0)
    priority: str
    reasoning: str


class WorkflowStepResult(BaseModel):
    step: str
    status: str
    detail: str
    timestamp: datetime


class ComplaintWorkflowResponse(BaseModel):
    execution_id: str
    classification: ComplaintClassification
    ticket_id: Optional[str]
    ticket_created: bool
    notification_logged: bool
    workflow_steps: list[WorkflowStepResult]
    status: str
    message: str


class ExecutionOut(BaseModel):
    id: int
    execution_id: str
    complaint_text: str
    order_reference: Optional[str]
    category: Optional[str]
    sentiment: Optional[str]
    urgency_score: Optional[float]
    priority: Optional[str]
    ticket_id: Optional[str]
    ticket_created: bool
    notification_logged: bool
    status: str
    error_detail: Optional[str]
    duration_ms: Optional[float]
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_orders: int
    pending_orders: int
    open_tickets: int
    high_priority_tickets: int
    resolved_tickets: int
    total_customers: int
    total_conversations: int
    escalated_tickets: int
    category_distribution: dict[str, int]
    sample_data_notice: str = "This dashboard uses sample/demo data for demonstration purposes."


class ActivityItem(BaseModel):
    id: str
    type: str
    description: str
    timestamp: datetime
    metadata: dict[str, Any] = {}


class DashboardActivity(BaseModel):
    recent_tickets: list[dict]
    recent_executions: list[dict]
    recent_conversations: list[dict]
    chart_data: list[dict]


# ─── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
    ai_provider: str
    rag_index: str
    timestamp: datetime
