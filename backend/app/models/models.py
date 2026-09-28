"""SQLAlchemy ORM models for the restaurant support agent."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, 
    Integer, String, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    orders = relationship("Order", back_populates="customer")
    tickets = relationship("SupportTicket", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    order_id = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(
        Enum("pending", "confirmed", "preparing", "out_for_delivery", "delivered", "cancelled", "failed", name="order_status"),
        default="pending",
    )
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    grand_total = Column(Float, nullable=False, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tickets = relationship("SupportTicket", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(
        Enum("Payment", "Order", "Delivery", "Refund", "Technical", "Other", name="ticket_category"),
        default="Other",
    )
    priority = Column(Enum("Low", "Medium", "High", name="ticket_priority"), default="Medium")
    status = Column(
        Enum("Open", "In Progress", "Resolved", "Escalated", name="ticket_status"),
        default="Open",
    )
    assigned_team = Column(String(100), default="Support Team")
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    resolved_at = Column(DateTime, nullable=True)
    customer = relationship("Customer", back_populates="tickets")
    order = relationship("Order", back_populates="tickets")
    timeline = relationship("TicketTimeline", back_populates="ticket", cascade="all, delete-orphan")


class TicketTimeline(Base):
    __tablename__ = "ticket_timeline"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    actor = Column(String(100), default="System")
    action = Column(String(255), nullable=False)
    details = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    ticket = relationship("SupportTicket", back_populates="timeline")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(Enum("user", "assistant", "system", name="message_role"), nullable=False)
    content = Column(Text, nullable=False)
    tool_calls = Column(Text)  # JSON string of tool calls made
    sources = Column(Text)     # JSON string of RAG sources
    is_fallback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    conversation = relationship("Conversation", back_populates="messages")


class AutomationExecution(Base):
    __tablename__ = "automation_executions"
    id = Column(Integer, primary_key=True)
    execution_id = Column(String(100), unique=True, nullable=False, index=True)
    complaint_text = Column(Text, nullable=False)
    order_reference = Column(String(20))
    category = Column(String(50))
    sentiment = Column(String(50))
    urgency_score = Column(Float)
    priority = Column(String(20))
    ticket_id = Column(String(20))
    ticket_created = Column(Boolean, default=False)
    notification_logged = Column(Boolean, default=False)
    status = Column(Enum("success", "partial", "failed", name="exec_status"), default="success")
    error_detail = Column(Text)
    workflow_steps = Column(Text)  # JSON
    duration_ms = Column(Float)
    created_at = Column(DateTime, default=utcnow)


class AgentToolLog(Base):
    __tablename__ = "agent_tool_logs"
    id = Column(Integer, primary_key=True)
    correlation_id = Column(String(100), index=True)
    tool_name = Column(String(100), nullable=False)
    arguments = Column(Text)   # JSON - sanitized
    result_summary = Column(Text)
    success = Column(Boolean, default=True)
    duration_ms = Column(Float)
    error_detail = Column(Text)
    created_at = Column(DateTime, default=utcnow)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id = Column(Integer, primary_key=True)
    doc_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), default="General")
    source = Column(String(255))
    is_indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
