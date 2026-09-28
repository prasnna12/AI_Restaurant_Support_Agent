"""AI agent chat endpoints."""
import json, uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.models import AdminUser, Conversation, ConversationMessage
from app.agents.restaurant_agent import run_agent
from app.schemas.schemas import ChatRequest, ChatResponse, ToolCallInfo, ConversationOut, ConversationDetailOut, MessageOut

router = APIRouter(prefix="/api/agent", tags=["agent"])


def utcnow():
    return datetime.now(timezone.utc)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    # Get or create conversation
    conv = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.session_id == req.conversation_id).first()

    if not conv:
        conv = Conversation(session_id=str(uuid.uuid4()), title=req.message[:50] + "...")
        db.add(conv)
        db.flush()

    # Build history
    msgs = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conv.id
    ).order_by(ConversationMessage.created_at).limit(20).all()
    history = [{"role": m.role, "content": m.content} for m in msgs]

    # Run agent
    result = run_agent(req.message, history, db, correlation_id=str(uuid.uuid4()))

    # Save user message
    user_msg = ConversationMessage(
        conversation_id=conv.id, role="user", content=req.message
    )
    db.add(user_msg)

    # Save assistant message
    asst_msg = ConversationMessage(
        conversation_id=conv.id,
        role="assistant",
        content=result["response"],
        tool_calls=json.dumps(result.get("tool_calls", [])),
        sources=json.dumps(result.get("sources", [])),
        is_fallback=result.get("is_fallback", False),
    )
    db.add(asst_msg)
    conv.updated_at = utcnow()
    db.commit()

    tool_calls = [ToolCallInfo(**tc) for tc in result.get("tool_calls", [])]
    return ChatResponse(
        message=result["response"],
        conversation_id=conv.session_id,
        tool_calls=tool_calls,
        sources=result.get("sources", []),
        is_fallback=result.get("is_fallback", False),
        timestamp=utcnow(),
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(50).all()
    return [ConversationOut(id=c.id, session_id=c.session_id, title=c.title, created_at=c.created_at, updated_at=c.updated_at) for c in convs]


@router.get("/conversations/{session_id}", response_model=ConversationDetailOut)
def get_conversation(session_id: str, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conv.id
    ).order_by(ConversationMessage.created_at).all()
    conv_out = ConversationOut(id=conv.id, session_id=conv.session_id, title=conv.title, created_at=conv.created_at, updated_at=conv.updated_at)
    msgs_out = [MessageOut(id=m.id, role=m.role, content=m.content, tool_calls=m.tool_calls, sources=m.sources, is_fallback=m.is_fallback, created_at=m.created_at) for m in msgs]
    return ConversationDetailOut(conversation=conv_out, messages=msgs_out)
