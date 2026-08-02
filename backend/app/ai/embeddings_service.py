"""Embeddings service with TF-IDF fallback (no external API dependency)."""

import os
import json
import logging
from typing import List, Optional, Tuple
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    TFIDF_AVAILABLE = True
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None
    TFIDF_AVAILABLE = False


class Document(BaseModel):
    page_content: str
    metadata: dict = {}
    model_config = ConfigDict(arbitrary_types_allowed=True)


class EmbeddingsService:
    """TF-IDF based embeddings service. No external API required.

    Caches the fitted TfidfVectorizer and document matrix per school_id.
    The index is only rebuilt when new documents are ingested (add_to_index / delete_index).
    """

    def __init__(self, index_path: str = "data/faiss_indexes", **kwargs):
        self.index_path = index_path
        os.makedirs(index_path, exist_ok=True)
        self._vectorizers: dict = {}  # per-school vectorizers (kept for compat)
        self._index_cache: dict[int, tuple] = {}  # school_id -> (vectorizer, matrix, doc_count)
        self._doc_hashes: dict[int, int] = {}  # school_id -> hash of doc list (for invalidation)

    def _get_docstore_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.json")

    def _get_index_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.index")

    def _get_legacy_docstore_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.pkl")

    def _load_docs(self, school_id: int) -> Optional[List[dict]]:
        docstore_file = self._get_docstore_file(school_id)
        legacy_file = self._get_legacy_docstore_file(school_id)

        raw_docs = None
        if os.path.exists(docstore_file):
            try:
                with open(docstore_file, "r", encoding="utf-8") as f:
                    raw_docs = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        if raw_docs is None and os.path.exists(legacy_file):
            try:
                import pickle
                with open(legacy_file, "rb") as f:
                    raw_docs = pickle.load(f)
                migrated = []
                for d in raw_docs:
                    if hasattr(d, "page_content"):
                        migrated.append({"page_content": d.page_content, "metadata": getattr(d, "metadata", {}) or {}})
                    elif isinstance(d, dict):
                        migrated.append(d)
                raw_docs = migrated
                with open(docstore_file, "w", encoding="utf-8") as f:
                    json.dump(raw_docs, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        return raw_docs

    def _save_docs(self, school_id: int, docs: List[dict]) -> None:
        docstore_file = self._get_docstore_file(school_id)
        with open(docstore_file, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)

    def _build_vectorizer(self, texts: List[str]):
        if not TFIDF_AVAILABLE or not texts:
            return None, None
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 4),
            max_features=10000,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        return vectorizer, tfidf_matrix

    def add_to_index(
        self,
        school_id: int,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> None:
        if not texts:
            return

        existing = self._load_docs(school_id) or []

        new_docs = [
            {
                "page_content": text,
                "metadata": meta or {"source": "unknown", "school_id": school_id},
            }
            for text, meta in zip(texts, metadatas or [{}] * len(texts))
        ]
        existing.extend(new_docs)
        self._save_docs(school_id, existing)

        # Invalidate cached vectorizer — will be rebuilt on next search
        self._index_cache.pop(school_id, None)
        self._doc_hashes.pop(school_id, None)

        logger.info(f"Indexed {len(texts)} chunks for school_id={school_id} (total: {len(existing)})")

    def similarity_search(
        self,
        school_id: int,
        query: str,
        k: int = 10,
    ) -> List[Document]:
        raw_docs = self._load_docs(school_id)
        if not raw_docs:
            return []

        docs = []
        for d in raw_docs:
            if isinstance(d, dict):
                docs.append(Document(page_content=d["page_content"], metadata=d.get("metadata", {})))
            elif hasattr(d, "page_content"):
                docs.append(Document(page_content=d.page_content, metadata=getattr(d, "metadata", {}) or {}))

        if not docs:
            return []

        if not TFIDF_AVAILABLE:
            return docs[:k]

        try:
            corpus = [d.page_content for d in docs]
            doc_count = len(corpus)
            doc_hash = hash(tuple(corpus))

            # Use cached vectorizer + matrix if the document set hasn't changed
            cached = self._index_cache.get(school_id)
            if cached and self._doc_hashes.get(school_id) == doc_hash:
                vectorizer, tfidf_matrix, _ = cached
                logger.debug(f"TF-IDF cache hit for school_id={school_id} ({doc_count} docs)")
            else:
                vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), max_features=10000)
                tfidf_matrix = vectorizer.fit_transform(corpus)
                self._index_cache[school_id] = (vectorizer, tfidf_matrix, doc_count)
                self._doc_hashes[school_id] = doc_hash
                logger.info(f"TF-IDF index rebuilt for school_id={school_id} ({doc_count} docs)")

            query_vec = vectorizer.transform([query])
            scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
            top_indices = scores.argsort()[::-1][:k]
            results = [docs[i] for i in top_indices if scores[i] > 0.01]
            logger.info(f"TF-IDF search for school_id={school_id}: {len(results)} results, top_score={scores[top_indices[0]]:.4f}")
            return results
        except Exception as e:
            logger.warning(f"TF-IDF search failed: {e}")
            return docs[:k]

    def load_index(self, school_id: int):
        raw_docs = self._load_docs(school_id)
        if not raw_docs:
            return None
        docs = []
        for d in raw_docs:
            if isinstance(d, dict):
                docs.append(Document(page_content=d["page_content"], metadata=d.get("metadata", {})))
            elif hasattr(d, "page_content"):
                docs.append(Document(page_content=d.page_content, metadata=getattr(d, "metadata", {}) or {}))
        return (None, docs)

    def delete_index(self, school_id: int) -> None:
        for f in [self._get_docstore_file(school_id), self._get_index_file(school_id), self._get_legacy_docstore_file(school_id)]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
        # Invalidate cached vectorizer
        self._index_cache.pop(school_id, None)
        self._doc_hashes.pop(school_id, None)

    def get_stats(self, school_id: int) -> dict:
        raw_docs = self._load_docs(school_id)
        if not raw_docs:
            return {"indexed_docs": 0, "has_index": False}
        return {"indexed_docs": len(raw_docs), "has_index": True}

    def save_index(self, school_id: int, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        self.add_to_index(school_id, texts, metadatas)
