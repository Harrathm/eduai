"""Embeddings service with semantic embeddings (sentence-transformers).

Replaces the legacy TF-IDF char_wb approach with dense embeddings from
``paraphrase-multilingual-MiniLM-L12-v2`` for true semantic similarity
across Arabic and French.
"""

import os
import json
import logging
from typing import List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sentence-transformers model (lazy loaded — only once per process)
# ---------------------------------------------------------------------------
_ST_MODEL = None
_ST_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def _get_st_model():
    """Lazy-load the multilingual sentence-transformer model."""
    global _ST_MODEL
    if _ST_MODEL is not None:
        return _ST_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _ST_MODEL = SentenceTransformer(_ST_MODEL_NAME)
        logger.info("Semantic embeddings model loaded: %s", _ST_MODEL_NAME)
    except Exception as exc:
        logger.error("Failed to load sentence-transformers model: %s", exc)
        _ST_MODEL = None
    return _ST_MODEL


def _encode_texts(texts: List[str], batch_size: int = 256) -> np.ndarray:
    """Encode a list of texts into dense embedding vectors."""
    model = _get_st_model()
    if model is None:
        raise RuntimeError(
            "Semantic embeddings model unavailable. "
            "Install sentence-transformers: pip install sentence-transformers"
        )
    return model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,   # unit vectors → dot product = cosine
    )


def _encode_query(query: str) -> np.ndarray:
    """Encode a single query string into a dense embedding vector."""
    model = _get_st_model()
    if model is None:
        raise RuntimeError(
            "Semantic embeddings model unavailable. "
            "Install sentence-transformers: pip install sentence-transformers"
        )
    return model.encode(
        [query],
        normalize_embeddings=True,
    )[0]  # shape (dim,)


class Document(BaseModel):
    page_content: str
    metadata: dict = {}
    model_config = ConfigDict(arbitrary_types_allowed=True)


class EmbeddingsService:
    """Semantic embeddings service backed by sentence-transformers.

    Stores dense vectors (normalized) per chunk in the JSON docstore alongside
    the text content and metadata.  The in-memory cache holds the full
    embeddings matrix per school_id for fast cosine search.
    """

    def __init__(self, index_path: str = "data/faiss_indexes", **kwargs):
        self.index_path = index_path
        os.makedirs(index_path, exist_ok=True)
        # school_id -> np.ndarray of shape (n_chunks, embedding_dim)
        self._embeddings_cache: dict[int, np.ndarray] = {}
        self._doc_hashes: dict[int, int] = {}
        self._doc_mtimes: dict[int, float] = {}

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------
    def _get_docstore_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.json")

    def _get_index_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.index")

    def _get_legacy_docstore_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.pkl")

    # ------------------------------------------------------------------
    # Load / Save docstore (JSON, includes "embedding" key per chunk)
    # ------------------------------------------------------------------
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
                        migrated.append({
                            "page_content": d.page_content,
                            "metadata": getattr(d, "metadata", {}) or {},
                        })
                    elif isinstance(d, dict):
                        migrated.append(d)
                raw_docs = migrated
                # Save migrated JSON
                with open(docstore_file, "w", encoding="utf-8") as f:
                    json.dump(raw_docs, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        return raw_docs

    def _save_docs(self, school_id: int, docs: List[dict]) -> None:
        docstore_file = self._get_docstore_file(school_id)
        with open(docstore_file, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Embeddings persistence (separate .npy per school for fast load)
    # ------------------------------------------------------------------
    def _get_embeddings_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}_embeddings.npy")

    def _save_embeddings(self, school_id: int, embeddings: np.ndarray) -> None:
        npy_path = self._get_embeddings_file(school_id)
        np.save(npy_path, embeddings.astype(np.float32))

    def _load_embeddings(self, school_id: int) -> Optional[np.ndarray]:
        npy_path = self._get_embeddings_file(school_id)
        if not os.path.exists(npy_path):
            return None
        try:
            return np.load(npy_path)
        except Exception as e:
            logger.warning("Failed to load embeddings for school %d: %s", school_id, e)
            return None

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------
    def add_to_index(
        self,
        school_id: int,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> None:
        if not texts:
            return

        existing = self._load_docs(school_id) or []

        # Compute embeddings for the new chunks
        new_embeddings = _encode_texts(texts)

        new_docs = []
        for text, meta, emb in zip(texts, metadatas or [{}] * len(texts), new_embeddings):
            new_docs.append({
                "page_content": text,
                "metadata": meta or {"source": "unknown", "school_id": school_id},
                "embedding": emb.tolist(),
            })
        existing.extend(new_docs)

        self._save_docs(school_id, existing)

        # Rebuild the full embeddings matrix and persist it
        all_embeddings = np.array([d["embedding"] for d in existing], dtype=np.float32)
        self._save_embeddings(school_id, all_embeddings)

        # Invalidate in-memory cache so next search picks up the new .npy
        self._embeddings_cache.pop(school_id, None)
        self._doc_hashes.pop(school_id, None)
        self._doc_mtimes.pop(school_id, None)

        logger.info(
            "Indexed %d chunks (semantic) for school_id=%d (total: %d)",
            len(texts), school_id, len(existing),
        )

    def delete_index(self, school_id: int) -> None:
        for f in [
            self._get_docstore_file(school_id),
            self._get_index_file(school_id),
            self._get_legacy_docstore_file(school_id),
            self._get_embeddings_file(school_id),
        ]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
        self._embeddings_cache.pop(school_id, None)
        self._doc_hashes.pop(school_id, None)
        self._doc_mtimes.pop(school_id, None)

    # ------------------------------------------------------------------
    # Metadata filter
    # ------------------------------------------------------------------
    @staticmethod
    def _metadata_matches(
        meta: dict,
        niveau_scolaire: Optional[str],
        matiere: Optional[str],
    ) -> bool:
        def _norm(v) -> str:
            import unicodedata as _ud
            s = str(v or "").strip()
            s = "".join(c for c in _ud.normalize("NFKD", s) if not _ud.combining(c))
            return s.lower()

        if not niveau_scolaire and not matiere:
            return True
        doc_niveau = _norm(meta.get("niveau_scolaire"))
        doc_matiere = _norm(meta.get("matiere"))
        if niveau_scolaire and doc_niveau and doc_niveau != _norm(niveau_scolaire):
            return False
        if matiere and doc_matiere and doc_matiere != _norm(matiere):
            return False
        return True

    # ------------------------------------------------------------------
    # Semantic similarity search
    # ------------------------------------------------------------------
    def similarity_search(
        self,
        school_id: int,
        query: str,
        k: int = 10,
        niveau_scolaire: Optional[str] = None,
        matiere: Optional[str] = None,
    ) -> List[Document]:
        raw_docs = self._load_docs(school_id)
        if not raw_docs:
            return []

        # --- Metadata filtering (pre-filter before embedding search) ---
        filtered_indices: List[int] = []
        docs: List[Document] = []
        for i, d in enumerate(raw_docs):
            if isinstance(d, dict):
                doc = Document(
                    page_content=d["page_content"],
                    metadata=d.get("metadata", {}),
                )
            elif hasattr(d, "page_content"):
                doc = Document(
                    page_content=d.page_content,
                    metadata=getattr(d, "metadata", {}) or {},
                )
            else:
                continue
            if self._metadata_matches(doc.metadata, niveau_scolaire, matiere):
                filtered_indices.append(i)
                docs.append(doc)

        if not docs:
            logger.info(
                "Semantic search school_id=%d: 0 chunks match filters "
                "(niveau_scolaire=%r, matiere=%r)",
                school_id, niveau_scolaire, matiere,
            )
            return []

        # --- Load or rebuild the embeddings matrix ---
        try:
            embeddings_matrix = self._get_embeddings_matrix(school_id, raw_docs)
        except Exception as e:
            logger.warning("Semantic search failed (embeddings unavailable): %s", e)
            # Fallback: return filtered docs without ranking
            return docs[:k]

        if embeddings_matrix is None or len(filtered_indices) == 0:
            return docs[:k]

        # Subset the matrix to only filtered chunks
        filtered_matrix = embeddings_matrix[filtered_indices]

        # --- Encode query and compute cosine similarity ---
        try:
            query_vec = _encode_query(query)
        except Exception as e:
            logger.warning("Query encoding failed: %s", e)
            return docs[:k]

        # Cosine similarity (both vectors are L2-normalized → dot product = cosine)
        scores = filtered_matrix @ query_vec  # shape (n_filtered,)

        # Sort descending and take top-k
        top_local_indices = scores.argsort()[::-1][:k]

        results: List[Document] = []
        for local_idx in top_local_indices:
            score = float(scores[local_idx])
            if score <= 0.01:
                continue
            doc = docs[local_idx]
            doc.metadata["_score"] = score
            results.append(doc)

        top_score = float(scores[top_local_indices[0]]) if len(top_local_indices) > 0 else 0.0
        logger.info(
            "Semantic search school_id=%d: %d results, top_score=%.4f "
            "(filtered %d/%d chunks)",
            school_id, len(results), top_score,
            len(filtered_indices), len(raw_docs),
        )
        return results

    def _get_embeddings_matrix(self, school_id: int, raw_docs: List[dict]) -> Optional[np.ndarray]:
        """Return the cached or freshly-built embeddings matrix.

        Rebuilds from docstore on cache miss or when the file on disk changed.
        """
        doc_hash = hash(tuple(d.get("page_content", "") for d in raw_docs))
        try:
            file_mtime = os.path.getmtime(self._get_docstore_file(school_id))
        except OSError:
            file_mtime = None

        cache_stale = (
            file_mtime is not None
            and self._doc_mtimes.get(school_id) is not None
            and file_mtime > self._doc_mtimes[school_id] + 1e-6
        )

        cached = self._embeddings_cache.get(school_id)
        if (
            cached is not None
            and self._doc_hashes.get(school_id) == doc_hash
            and not cache_stale
            and cached.shape[0] == len(raw_docs)
        ):
            logger.debug("Embeddings cache hit for school_id=%d (%d docs)", school_id, len(raw_docs))
            return cached

        # --- Try loading persisted .npy first ---
        npy_emb = self._load_embeddings(school_id)
        if npy_emb is not None and npy_emb.shape[0] == len(raw_docs):
            self._embeddings_cache[school_id] = npy_emb
            self._doc_hashes[school_id] = doc_hash
            if file_mtime is not None:
                self._doc_mtimes[school_id] = file_mtime
            logger.info(
                "Embeddings loaded from .npy for school_id=%d (%d docs, dim=%d)",
                school_id, npy_emb.shape[0], npy_emb.shape[1],
            )
            return npy_emb

        # --- Rebuild: check if any docs have stored embeddings, else encode all ---
        has_embeddings = all("embedding" in d for d in raw_docs)
        if has_embeddings:
            matrix = np.array(
                [d["embedding"] for d in raw_docs], dtype=np.float32
            )
        else:
            logger.info(
                "Encoding %d chunks from scratch for school_id=%d "
                "(no pre-computed embeddings found)",
                len(raw_docs), school_id,
            )
            texts = [d.get("page_content", "") for d in raw_docs]
            matrix = _encode_texts(texts)
            # Persist embeddings back into docstore and .npy
            for d, emb in zip(raw_docs, matrix):
                d["embedding"] = emb.tolist()
            self._save_docs(school_id, raw_docs)
            self._save_embeddings(school_id, matrix)

        self._embeddings_cache[school_id] = matrix
        self._doc_hashes[school_id] = doc_hash
        if file_mtime is not None:
            self._doc_mtimes[school_id] = file_mtime

        logger.info(
            "Embeddings index built for school_id=%d (%d docs, dim=%d)",
            school_id, matrix.shape[0], matrix.shape[1] if matrix.ndim == 2 else 0,
        )
        return matrix

    # ------------------------------------------------------------------
    # Legacy helpers (kept for backward compatibility)
    # ------------------------------------------------------------------
    def load_index(self, school_id: int):
        raw_docs = self._load_docs(school_id)
        if not raw_docs:
            return None
        docs = []
        for d in raw_docs:
            if isinstance(d, dict):
                docs.append(Document(
                    page_content=d["page_content"],
                    metadata=d.get("metadata", {}),
                ))
            elif hasattr(d, "page_content"):
                docs.append(Document(
                    page_content=d.page_content,
                    metadata=getattr(d, "metadata", {}) or {},
                ))
        return (None, docs)

    def get_stats(self, school_id: int) -> dict:
        raw_docs = self._load_docs(school_id)
        if not raw_docs:
            return {"indexed_docs": 0, "has_index": False}
        has_embeddings = os.path.exists(self._get_embeddings_file(school_id))
        return {
            "indexed_docs": len(raw_docs),
            "has_index": True,
            "embedding_model": _ST_MODEL_NAME,
            "has_persisted_embeddings": has_embeddings,
        }

    def save_index(self, school_id: int, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        self.add_to_index(school_id, texts, metadatas)
