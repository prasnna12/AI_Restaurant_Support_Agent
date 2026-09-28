"""RAG pipeline using FAISS and sentence-transformers."""
import json
import logging
import os
import pickle
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import KnowledgeDocument

logger = logging.getLogger(__name__)

# Will be lazily initialized
_rag_index = None
_rag_chunks = None
_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            _embedding_model = None
    return _embedding_model


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
        if i >= len(words):
            break
    return chunks if chunks else [text]


def build_index(db: Session) -> dict:
    """Build FAISS index from knowledge documents in the database."""
    global _rag_index, _rag_chunks

    model = _get_embedding_model()
    if not model:
        return {"success": False, "error": "Embedding model not available", "indexed": 0}

    try:
        import faiss
        import numpy as np

        docs = db.query(KnowledgeDocument).all()
        if not docs:
            return {"success": False, "error": "No documents in knowledge base", "indexed": 0}

        all_chunks = []
        all_metadata = []

        for doc in docs:
            if not doc.content or len(doc.content.strip()) < 10:
                continue
            chunks = chunk_text(doc.content, settings.RAG_CHUNK_SIZE, settings.RAG_CHUNK_OVERLAP)
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadata.append({
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "source": doc.source,
                    "category": doc.category,
                })

        if not all_chunks:
            return {"success": False, "error": "No valid document content to index", "indexed": 0}

        embeddings = model.encode(all_chunks, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype="float32")

        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        _rag_index = index
        _rag_chunks = list(zip(all_chunks, all_metadata))

        # Persist
        store_path = Path(settings.VECTOR_STORE_PATH)
        store_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(store_path / "index.faiss"))
        with open(store_path / "chunks.pkl", "wb") as fh:
            pickle.dump(_rag_chunks, fh)

        # Mark docs as indexed
        for doc in docs:
            doc.is_indexed = True
        db.commit()

        logger.info(f"RAG index built: {len(all_chunks)} chunks from {len(docs)} documents")
        return {"success": True, "indexed": len(docs), "chunks": len(all_chunks)}

    except Exception as e:
        logger.error(f"Index build failed: {e}")
        return {"success": False, "error": str(e), "indexed": 0}


def load_index() -> bool:
    """Load existing FAISS index from disk."""
    global _rag_index, _rag_chunks
    try:
        import faiss
        store_path = Path(settings.VECTOR_STORE_PATH)
        idx_file = store_path / "index.faiss"
        chunks_file = store_path / "chunks.pkl"
        if idx_file.exists() and chunks_file.exists():
            _rag_index = faiss.read_index(str(idx_file))
            with open(chunks_file, "rb") as fh:
                _rag_chunks = pickle.load(fh)
            logger.info(f"RAG index loaded: {len(_rag_chunks)} chunks")
            return True
    except Exception as e:
        logger.warning(f"Could not load RAG index: {e}")
    return False


def search(query: str, top_k: int = 4) -> list[dict]:
    """Search the RAG index for relevant chunks."""
    global _rag_index, _rag_chunks

    if _rag_index is None:
        load_index()

    if _rag_index is None or not _rag_chunks:
        return []

    model = _get_embedding_model()
    if not model:
        return []

    try:
        import numpy as np
        q_emb = model.encode([query], show_progress_bar=False)
        q_emb = np.array(q_emb, dtype="float32")
        distances, indices = _rag_index.search(q_emb, min(top_k, len(_rag_chunks)))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(_rag_chunks):
                continue
            chunk_text, metadata = _rag_chunks[idx]
            score = float(1 / (1 + dist))
            results.append({
                "content": chunk_text,
                "score": score,
                "doc_id": metadata["doc_id"],
                "title": metadata["title"],
                "source": metadata["source"],
                "category": metadata["category"],
            })
        return results
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return []


def is_index_available() -> bool:
    """Check if the RAG index is loaded or can be loaded."""
    global _rag_index
    if _rag_index is not None:
        return True
    return load_index()
