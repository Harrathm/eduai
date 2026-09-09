"""Hybrid retrieval service — lexical (TF-IDF char_wb) + semantic (MiniLM).

Dense embeddings from ``paraphrase-multilingual-MiniLM-L12-v2`` provide true
semantic similarity across Arabic and French, while a parallel TF-IDF
``char_wb`` (ngram 2-4) branch catches exact official terms (ex: "Cellules de
Leydig") that embeddings may miss. ``similarity_search`` fuses both branches.
"""

import os
import re
import json
import logging
from collections import defaultdict
from typing import List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retrieval hybride — constantes de fusion
# ---------------------------------------------------------------------------
# Chaque signal (lexical TF-IDF / sémantique MiniLM) produit un Top-10.
# La fusion utilise le Reciprocal Rank Fusion (RRF) : score = Σ 1/(K + rank).
# Un chunk présent dans LES DEUX listes obtient donc un score supérieur.
_RRF_CONSTANT = 60.0
_LEXICAL_TOP_K = 10
_SEMANTIC_TOP_K = 10

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
    """Hybrid retrieval service — semantic (MiniLM) + lexical (TF-IDF char_wb).

    Stores dense vectors (normalized) per chunk in the JSON docstore alongside
    the text content and metadata.  The in-memory cache holds the full
    embeddings matrix per school_id for fast cosine search.  A parallel
    TF-IDF char_wb branch (ngram 2-4) recovers exact scientific terms that
    semantic embeddings may miss.  ``similarity_search`` fuses both branches
    with Reciprocal Rank Fusion (dedup + Top-15).
    """

    def __init__(self, index_path: str = "data/faiss_indexes", **kwargs):
        self.index_path = index_path
        os.makedirs(index_path, exist_ok=True)
        # school_id -> np.ndarray of shape (n_chunks, embedding_dim)
        self._embeddings_cache: dict[int, np.ndarray] = {}
        self._doc_hashes: dict[int, int] = {}
        self._doc_mtimes: dict[int, float] = {}
        # Clé (hash du corpus) -> (TfidfVectorizer, matrix csr) pour la branche lexicale
        self._tfidf_cache: dict[int, tuple] = {}

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

        if raw_docs is not None:
            # Les vecteurs vivent dans le .npy (school_<id>_embeddings.npy),
            # PAS dans le JSON : retirer la clé "embedding" évite de conserver
            # ~700 Mo d'objets Python flottants en mémoire à chaque chargement
            # (source de MemoryError sur les gros index).
            for d in raw_docs:
                if isinstance(d, dict):
                    d.pop("embedding", None)
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

        # Rebuild de la matrice complète depuis les textes (les documents
        # chargés par _load_docs n'embarquent plus de vecteurs).
        all_texts = [d["page_content"] for d in existing] + texts
        all_embeddings = np.array(_encode_texts(all_texts), dtype=np.float32)
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
    # Lexical retrieval — TF-IDF char_wb (ngram 2-4), branché EN PARALLÈLE
    # de la recherche sémantique MiniLM pour rattraper les noms scientifiques
    # exacts (ex: "Cellules de Leydig") que les embeddings peuvent manquer.
    # ------------------------------------------------------------------
    def _get_lexical_model(self, texts: List[str]):
        """Build (or fetch from cache) the TF-IDF model + matrix for a corpus."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        corpus_key = hash(tuple(texts))
        cached = self._tfidf_cache.get(corpus_key)
        if cached is not None:
            return cached
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            max_features=10000,
        )
        tfidf = vectorizer.fit_transform(texts)  # rows L2-normalized by default
        self._tfidf_cache[corpus_key] = (vectorizer, tfidf)
        logger.debug("Built TF-IDF model for %d chunks (char_wb, ngram 2-4)", len(texts))
        return vectorizer, tfidf

    def _lexical_similarity(self, texts: List[str], query: str) -> np.ndarray:
        """Cosine similarity between the query and every text (TF-IDF char_wb).

        Returns an array of shape (len(texts),) in the SAME order as ``texts``.
        """
        vectorizer, tfidf = self._get_lexical_model(texts)
        q_vec = vectorizer.transform([query])
        scores = (tfidf @ q_vec.T).toarray().ravel()
        return scores.astype(np.float64)

    def _jaccard_similarity(self, texts: List[str], query: str) -> np.ndarray:
        """Similarité Jaccard (intersection / union des mots) — aucune dépendance.

        Fallback utilisé quand ni torch (embeddings) ni scikit-learn (TF-IDF)
        ne sont disponibles. Gère les tokens arabes (séparés par espaces).
        """
        _punct = re.compile(r"[^\w\s]", re.UNICODE)
        q_tokens = set(
            t for t in _punct.sub(" ", query).lower().split() if t
        )
        scores = np.zeros(len(texts), dtype=np.float64)
        if not q_tokens:
            return scores
        for i, text in enumerate(texts):
            if not text:
                continue
            d_tokens = set(
                t for t in _punct.sub(" ", text).lower().split() if t
            )
            if not d_tokens:
                continue
            inter = len(q_tokens & d_tokens)
            union = len(q_tokens | d_tokens)
            if union:
                scores[i] = inter / union
        return scores

    # ------------------------------------------------------------------
    # Fused hybrid ranking (lexical TF-IDF + semantic MiniLM) — RRF
    # ------------------------------------------------------------------
    @staticmethod
    def _merge_rankings(
        docs: List["Document"],
        semantic_scores: np.ndarray,
        lexical_scores: np.ndarray,
        semantic_ok: bool,
        lexical_ok: bool,
        k: int,
    ) -> List["Document"]:
        """Fuse les Top-10 lexicaux et sémantiques via Reciprocal Rank Fusion.

        - Déduplique les chunks présents dans les deux listes (même position
          dans ``docs``) — ils cumulent les deux contributions RRF.
        - Enrichit chaque document avec ``_score`` (RRF), ``_semantic_score``
          et ``_lexical_score`` pour le reranking côté RAGService.
        - Retourne le Top-k global sur l'union des deux listes.
        """

        def _top_positions(scores: np.ndarray, use: bool, cutoff: float) -> List[int]:
            if not use:
                return []
            order = np.argsort(scores)[::-1]
            out = []
            for pos in order:
                if float(scores[pos]) <= cutoff:
                    continue
                out.append(int(pos))
                if len(out) >= _SEMANTIC_TOP_K:
                    break
            return out

        sem_positions = _top_positions(semantic_scores, semantic_ok, 0.0)
        lex_positions = _top_positions(lexical_scores, lexical_ok, 0.0)

        if not sem_positions and not lex_positions:
            return []

        rrf: dict[int, float] = defaultdict(float)
        for rank, pos in enumerate(sem_positions):
            rrf[pos] += 1.0 / (_RRF_CONSTANT + rank)
        for rank, pos in enumerate(lex_positions):
            rrf[pos] += 1.0 / (_RRF_CONSTANT + rank)

        ordered = sorted(rrf, key=lambda p: rrf[p], reverse=True)[:k]

        results: List[Document] = []
        for pos in ordered:
            doc = docs[pos]
            doc.metadata["_score"] = float(rrf[pos])
            doc.metadata["_semantic_score"] = float(semantic_scores[pos]) if semantic_ok else 0.0
            doc.metadata["_lexical_score"] = float(lexical_scores[pos]) if lexical_ok else 0.0
            results.append(doc)
        return results

    # ------------------------------------------------------------------
    # Semantic similarity search
    # ------------------------------------------------------------------
    def similarity_search(
        self,
        school_id: int,
        query: str,
        k: int = 15,
        niveau_scolaire: Optional[str] = None,
        matiere: Optional[str] = None,
    ) -> List[Document]:
        """Retrieval HYBRIDE : lexical (TF-IDF char_wb ngram 2-4) + sémantique (MiniLM).

        1. Pré-filtre métadonnées (niveau_scolaire / matiere).
        2. Recherche sémantique  -> Top-10 (cosinus sur embeddings normalisés).
        3. Recherche lexicale    -> Top-10 (cosinus TF-IDF char_wb).
        4. Fusion RRF des deux listes (déduplication des chunks identiques),
           retour du Top-k global (k=15 par défaut).
        """
        raw_docs = self._load_docs(school_id)
        if not raw_docs:
            return []

        # --- Metadata filtering (pre-filter before hybrid retrieval) ---
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
                "Hybrid search school_id=%d: 0 chunks match filters "
                "(niveau_scolaire=%r, matiere=%r)",
                school_id, niveau_scolaire, matiere,
            )
            return []

        n_filtered = len(docs)
        semantic_scores = np.zeros(n_filtered, dtype=np.float64)
        lexical_scores = np.zeros(n_filtered, dtype=np.float64)
        semantic_ok = False
        lexical_ok = False

        # --- 1) Semantic branch (MiniLM embeddings) ---
        try:
            embeddings_matrix = self._get_embeddings_matrix(school_id, raw_docs)
            if embeddings_matrix is not None:
                filtered_matrix = embeddings_matrix[filtered_indices]
                query_vec = _encode_query(query)
                # Cosine similarity (L2-normalized → dot product = cosine)
                semantic_scores = filtered_matrix @ query_vec  # shape (n_filtered,)
                semantic_ok = True
        except Exception as e:
            logger.warning("Semantic branch failed (embeddings unavailable): %s", e)

        # --- 2) Lexical branch (TF-IDF char_wb, ngram 2-4) ---
        try:
            lexical_scores = self._lexical_similarity([d.page_content for d in docs], query)
            lexical_ok = True
        except Exception as e:
            logger.warning("Lexical branch failed (sklearn TfidfVectorizer unavailable): %s", e)

        # --- 3) Hybrid fusion (RRF) or degraded fallback ---
        if not semantic_ok and not lexical_ok:
            # Ni embeddings ni TF-IDF (dépendances absentes) : Jaccard
            # (intersection/union mots) — aucune dépendance requise.
            jacc = self._jaccard_similarity(
                [d.page_content for d in docs], query,
            )
            for d, s in zip(docs, jacc):
                d.metadata["_semantic_score"] = 0.0
                d.metadata["_lexical_score"] = float(s)
                d.metadata["_fallback"] = True
                d.metadata["_score"] = float(s)
            ranked = sorted(
                zip(docs, jacc), key=lambda x: x[1], reverse=True,
            )[:k]
            logger.warning(
                "Hybrid search school_id=%d: BOTH branches failed — "
                "Jaccard fallback (%d chunks, best=%.4f)",
                school_id, len(jacc), max(jacc) if jacc else 0.0,
            )
            return [d for d, _ in ranked]

        results = self._merge_rankings(
            docs, semantic_scores, lexical_scores,
            semantic_ok, lexical_ok, k,
        )
        if not results:
            return docs[:k]

        top_score = float(results[0].metadata.get("_score", 0.0))
        logger.info(
            "Hybrid search school_id=%d: %d fused results, top_rrf=%.4f "
            "(semantic=%.4f, lexical=%.4f, filtered %d/%d chunks)",
            school_id, len(results), top_score,
            float(np.max(semantic_scores)) if semantic_ok else 0.0,
            float(np.max(lexical_scores)) if lexical_ok else 0.0,
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

        # --- Rebuild: encode all chunks from scratch ---
        # Les vecteurs sont persistés dans le .npy uniquement ; le JSON
        # docstore porte page_content + metadata (ne PAS réécrire la clé
        # "embedding", sinon le fichier re-dégrade vers ~700 Mo).
        logger.info(
            "Encoding %d chunks from scratch for school_id=%d "
            "(no pre-computed embeddings found)",
            len(raw_docs), school_id,
        )
        texts = [d.get("page_content", "") for d in raw_docs]
        matrix = _encode_texts(texts)
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
            "retrieval": "hybrid_tfidf_embeddings",
            "has_persisted_embeddings": has_embeddings,
        }

    def save_index(self, school_id: int, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        self.add_to_index(school_id, texts, metadatas)
