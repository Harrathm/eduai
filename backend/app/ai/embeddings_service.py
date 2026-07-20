import os
import json
import pickle
from typing import List, Optional, Tuple
from pydantic import BaseModel, ConfigDict

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False


class Document(BaseModel):
    page_content: str
    metadata: dict = {}

    model_config = ConfigDict(arbitrary_types_allowed = True)


class EmbeddingsService:
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        index_path: str = "data/faiss_indexes",
        dimension: int = 1536,
    ):
        try:
            from langchain_openai import OpenAIEmbeddings
            self.embeddings_model = OpenAIEmbeddings(model=model)
        except Exception:
            self.embeddings_model = None
        self.index_path = index_path
        self.dimension = dimension
        os.makedirs(index_path, exist_ok=True)

    def _get_index_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.index")

    def _get_docstore_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.json")

    def _get_legacy_docstore_file(self, school_id: int) -> str:
        return os.path.join(self.index_path, f"school_{school_id}.pkl")

    def create_embeddings(self, texts: List[str]) -> "np.ndarray":
        if not NUMPY_AVAILABLE:
            return []
        if not texts or self.embeddings_model is None:
            return np.zeros((len(texts), self.dimension), dtype="float32")
        vectors = self.embeddings_model.embed_documents(texts)
        return np.array(vectors).astype("float32")

    def query_embeddings(self, query_text: str) -> "np.ndarray":
        if not NUMPY_AVAILABLE or not FAISS_AVAILABLE:
            return []
        if self.embeddings_model is None:
            return np.zeros(self.dimension, dtype="float32")
        vec = self.embeddings_model.embed_query(query_text)
        vec = np.array(vec).astype("float32")
        faiss.normalize_L2(vec.reshape(1, -1))
        return vec

    def save_index(
        self,
        school_id: int,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> None:
        if not texts or not FAISS_AVAILABLE or not NUMPY_AVAILABLE:
            return

        vectors = self.create_embeddings(texts)
        if not isinstance(vectors, np.ndarray) or vectors.size == 0:
            return
        faiss.normalize_L2(vectors)
        dimension = vectors.shape[1]

        index = faiss.IndexFlatIP(dimension)
        index.add(vectors)

        faiss.write_index(index, self._get_index_file(school_id))

        docs = [
            {
                "page_content": text,
                "metadata": meta or {"source": "unknown", "school_id": school_id},
            }
            for text, meta in zip(texts, metadatas or [{}] * len(texts))
        ]
        with open(self._get_docstore_file(school_id), "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)
        
        # Clean up legacy pickle file if it exists
        legacy_file = self._get_legacy_docstore_file(school_id)
        if os.path.exists(legacy_file):
            try:
                os.remove(legacy_file)
            except OSError:
                pass

    def load_index(
        self, school_id: int
    ) -> Optional[Tuple[any, List[Document]]]:
        if not FAISS_AVAILABLE:
            return None
        index_file = self._get_index_file(school_id)
        docstore_file = self._get_docstore_file(school_id)
        legacy_docstore_file = self._get_legacy_docstore_file(school_id)

        if not os.path.exists(index_file):
            return None

        # Try JSON docstore first, then legacy pickle
        raw_docs = None
        if os.path.exists(docstore_file):
            try:
                with open(docstore_file, "r", encoding="utf-8") as f:
                    raw_docs = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        
        if raw_docs is None and os.path.exists(legacy_docstore_file):
            try:
                with open(legacy_docstore_file, "rb") as f:
                    raw_docs = pickle.load(f)
                # Convert LangChain Document objects to dicts for JSON serialization
                migrated = []
                for d in raw_docs:
                    if hasattr(d, "page_content"):
                        migrated.append({"page_content": d.page_content, "metadata": getattr(d, "metadata", {}) or {}})
                    elif isinstance(d, dict):
                        migrated.append(d)
                raw_docs = migrated
                # Migrate to JSON format
                with open(docstore_file, "w", encoding="utf-8") as f:
                    json.dump(raw_docs, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        if raw_docs is None:
            return None

        index = faiss.read_index(index_file)
        docs = []
        for d in raw_docs:
            if isinstance(d, dict):
                docs.append(Document(page_content=d["page_content"], metadata=d.get("metadata", {})))
            elif hasattr(d, "page_content"):
                docs.append(Document(page_content=d.page_content, metadata=getattr(d, "metadata", {}) or {}))
            else:
                continue

        return index, docs

    def add_to_index(
        self,
        school_id: int,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> None:
        if not FAISS_AVAILABLE or not NUMPY_AVAILABLE:
            return
        existing = self.load_index(school_id)

        if existing:
            index, docs = existing
            new_vectors = self.create_embeddings(texts)
            if not isinstance(new_vectors, np.ndarray) or new_vectors.size == 0:
                return
            faiss.normalize_L2(new_vectors)
            index.add(new_vectors)

            faiss.write_index(index, self._get_index_file(school_id))

            new_docs = [
                Document(
                    page_content=text,
                    metadata=meta or {"source": "unknown", "school_id": school_id},
                )
                for text, meta in zip(texts, metadatas or [{}] * len(texts))
            ]
            docs.extend(new_docs)
            serializable = [
                {"page_content": d.page_content, "metadata": d.metadata}
                for d in docs
            ]
            with open(self._get_docstore_file(school_id), "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        else:
            self.save_index(school_id, texts, metadatas)

    def similarity_search(
        self,
        school_id: int,
        query: str,
        k: int = 4,
    ) -> List[Document]:
        existing = self.load_index(school_id)

        if not existing:
            return []

        index, docs = existing
        query_vector = self.query_embeddings(query)
        if not isinstance(query_vector, np.ndarray) or query_vector.size == 0:
            return []
        query_vector = query_vector.reshape(1, -1)

        k_search = min(k, index.ntotal)
        if k_search == 0:
            return []

        distances, indices = index.search(query_vector, k_search)

        return [docs[i] for i in indices[0] if i < len(docs)]

    def delete_index(self, school_id: int) -> None:
        index_file = self._get_index_file(school_id)
        docstore_file = self._get_docstore_file(school_id)

        if os.path.exists(index_file):
            os.remove(index_file)
        if os.path.exists(docstore_file):
            os.remove(docstore_file)

    def get_stats(self, school_id: int) -> dict:
        existing = self.load_index(school_id)
        if not existing:
            return {"indexed_docs": 0, "has_index": False}
        index, docs = existing
        return {"indexed_docs": len(docs), "has_index": True}