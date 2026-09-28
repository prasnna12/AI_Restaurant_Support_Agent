"""Knowledge base endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.models import AdminUser, KnowledgeDocument
from app.rag import pipeline as rag
from app.schemas.schemas import DocumentCreateRequest, DocumentOut, KnowledgeSearchRequest, KnowledgeSearchResponse, KnowledgeSearchResult

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def _doc_to_out(doc: KnowledgeDocument) -> DocumentOut:
    return DocumentOut(
        id=doc.id, doc_id=doc.doc_id, title=doc.title,
        category=doc.category, source=doc.source, is_indexed=doc.is_indexed,
        created_at=doc.created_at, updated_at=doc.updated_at,
        content_preview=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
    )


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    docs = db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).all()
    return [_doc_to_out(d) for d in docs]


@router.post("/documents", response_model=DocumentOut, status_code=201)
def add_document(req: DocumentCreateRequest, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    doc = KnowledgeDocument(
        doc_id=str(uuid.uuid4())[:8],
        title=req.title,
        content=req.content,
        category=req.category,
        source=req.source or "Manual entry",
        is_indexed=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _doc_to_out(doc)


@router.post("/reindex")
def reindex(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    result = rag.build_index(db)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Indexing failed"))
    return {"message": f"Index rebuilt successfully. {result['indexed']} documents, {result.get('chunks', 0)} chunks."}


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(req: KnowledgeSearchRequest, _: AdminUser = Depends(get_current_admin)):
    index_available = rag.is_index_available()
    if not index_available:
        return KnowledgeSearchResponse(query=req.query, results=[], index_available=False)
    results = rag.search(req.query, top_k=req.top_k)
    out = [
        KnowledgeSearchResult(
            doc_id=r["doc_id"], title=r["title"],
            content_snippet=r["content"][:300] + "..." if len(r["content"]) > 300 else r["content"],
            score=r["score"], source=r.get("source")
        ) for r in results
    ]
    return KnowledgeSearchResponse(query=req.query, results=out, index_available=True)
