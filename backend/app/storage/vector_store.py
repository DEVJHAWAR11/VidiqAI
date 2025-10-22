# app/storage/vector_store.py

from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.services.embeddings import get_embeddings
from app.config import config
import os
import re

# ---- CLEAN TRANSCRIPT UTILS ----

# ...existing code...
import logging
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Generic wrapper around an underlying vector DB client.
    - Call `add_embeddings` to persist vectors.
    - Call `search` to retrieve nearest neighbors.
    This wrapper ensures results are deduplicated (preserve order).
    Adapt client initialization to your project's real client in __init__.
    """

    def __init__(self, client: Optional[Any] = None, namespace: Optional[str] = None):
        """
        If `client` is provided, this wrapper will delegate to it.
        Otherwise you must set `self._client` later to an object exposing compatible methods.
        """
        self._client = client
        self.namespace = namespace

    # -- Helper: dedupe results preserving order --------------------------------
    @staticmethod
    def _dedupe_results(results: Sequence[Dict], key_fields: Optional[Sequence[str]] = None, top_k: Optional[int] = None) -> List[Dict]:
        """
        Deduplicate a sequence of result dicts preserving order.
        Default dedupe key: result['id'] if present, else result.get('meta', {}).get('chunk_id'), else result.get('text')
        Returns at most top_k items if top_k provided.
        """
        seen = set()
        out = []
        for r in results:
            # Compose primary key candidates
            key = None
            if isinstance(r, dict):
                key = r.get("id")
                if not key:
                    meta = r.get("meta") or {}
                    key = meta.get("chunk_id")
                if not key:
                    key = r.get("text")
            else:
                key = str(r)

            if key in seen:
                continue
            seen.add(key)
            out.append(r)
            if top_k and len(out) >= top_k:
                break
        return out

    # -- Add embeddings ----------------------------------------------------------
    def add_embeddings(self, ids: Sequence[str], vectors: Sequence[Sequence[float]], metadatas: Optional[Sequence[Dict]] = None):
        """
        Persist embeddings into the underlying client.
        Expects:
            ids: list of string ids (eg. chunk ids)
            vectors: list of numeric vectors aligned with ids
            metadatas: optional list of metadata dicts aligned with ids
        Adapt to your client's API: this generic implementation will attempt common method names.
        """
        if self._client is None:
            raise RuntimeError("VectorStore client not configured")

        try:
            # Common client API: add / upsert
            if hasattr(self._client, "upsert"):
                # chroma-like / vectordb clients
                self._client.upsert(ids=ids, embeddings=vectors, metadatas=metadatas, namespace=self.namespace)
                return
            if hasattr(self._client, "add"):
                # faiss/persisted-store wrappers
                self._client.add(ids, vectors, metadatas)
                return
            # Fallback: try generic attribute names
            if hasattr(self._client, "persist"):
                self._client.persist(ids=ids, vectors=vectors, metadatas=metadatas)
                return
        except Exception:
            logger.exception("Failed to add embeddings to vector store")
            raise

        raise RuntimeError("Underlying client does not expose a supported add/upsert API")

    # -- Search / similarity retrieval -------------------------------------------
    def search(self, query_vector: Sequence[float], top_k: int = 10, filter: Optional[Dict] = None) -> List[Dict]:
        """
        Search the vector DB. Returns a list of result dicts:
          [{"id": <id>, "score": <score>, "text": <text>, "meta": {...}}, ...]
        This wrapper will deduplicate the returned results (by id/text) preserving order.
        """
        if self._client is None:
            raise RuntimeError("VectorStore client not configured")

        raw_results = None
        try:
            # Try a few common client search signatures:
            if hasattr(self._client, "query") and callable(getattr(self._client, "query")):
                # chroma-like: client.query(query_embeddings=[query_vector], n_results=top_k, where=filter)
                try:
                    resp = self._client.query(query_embeddings=[query_vector], n_results=top_k, where=filter, namespace=self.namespace)
                    # Normalize response into list of dicts
                    raw_results = self._normalize_query_response(resp)
                except TypeError:
                    # fallback signature
                    resp = self._client.query(query_vector, top_k)
                    raw_results = self._normalize_query_response(resp)
            elif hasattr(self._client, "search") and callable(getattr(self._client, "search")):
                # FAISS/other wrappers: client.search(query_vector, top_k, filter=...)
                resp = self._client.search(query_vector, top_k, filter=filter, namespace=self.namespace)
                raw_results = self._normalize_query_response(resp)
            else:
                # Try generic method names
                if hasattr(self._client, "get_nearest_neighbors"):
                    resp = self._client.get_nearest_neighbors(query_vector, top_k)
                    raw_results = self._normalize_query_response(resp)
                else:
                    raise RuntimeError("Underlying client does not expose a supported search/query API")
        except Exception:
            logger.exception("Vector store search failed")
            raise

        # Ensure raw_results is a list of dict-like results
        if not isinstance(raw_results, list):
            logger.debug("Normalizing single search response to list")
            raw_results = list(raw_results) if raw_results is not None else []

        # Deduplicate results preserving order and cap to top_k
        deduped = self._dedupe_results(raw_results, top_k=top_k)
        return deduped

    # -- Response normalization -------------------------------------------------
    @staticmethod
    def _normalize_query_response(resp: Any) -> List[Dict]:
        """
        Convert common response formats into a list of dicts with keys:
          'id', 'score', 'text', 'meta'
        The exact structure depends on the client; this helper attempts reasonable mappings.
        """
        out = []

        if resp is None:
            return out

        # choma-like: resp['ids'], resp['distances'], resp['metadatas'], resp['documents']
        try:
            if isinstance(resp, dict):
                # chroma-python query format
                if "ids" in resp and isinstance(resp["ids"], list):
                    # chroma returns lists of lists when multiple queries provided
                    ids_list = resp["ids"]
                    docs_list = resp.get("documents") or resp.get("documents", [])
                    metas_list = resp.get("metadatas") or resp.get("metadatas", [])
                    dists_list = resp.get("distances") or resp.get("distances", [])
                    # take first query's results if nested
                    ids = ids_list[0] if ids_list and isinstance(ids_list[0], list) else ids_list
                    docs = docs_list[0] if docs_list and isinstance(docs_list[0], list) else docs_list
                    metas = metas_list[0] if metas_list and isinstance(metas_list[0], list) else metas_list
                    dists = dists_list[0] if dists_list and isinstance(dists_list[0], list) else dists_list

                    for i, idv in enumerate(ids):
                        out.append({"id": idv, "score": None if not dists else dists[i], "text": (docs[i] if docs and i < len(docs) else None), "meta": (metas[i] if metas and i < len(metas) else {})})
                    return out

                # If resp contains 'results' key that is a list
                if "results" in resp and isinstance(resp["results"], list):
                    for r in resp["results"]:
                        # try to extract known fields
                        out.append(
                            {
                                "id": r.get("id"),
                                "score": r.get("score") or r.get("distance") or r.get("score"),
                                "text": r.get("document") or r.get("text") or r.get("content"),
                                "meta": r.get("metadata") or r.get("meta") or {},
                            }
                        )
                    return out
        except Exception:
            logger.debug("Chroma-like normalization failed, trying other formats", exc_info=True)

        # If resp is an iterable of tuples (id, score, text, meta)
        try:
            if isinstance(resp, (list, tuple)):
                for item in resp:
                    if isinstance(item, dict):
                        out.append({"id": item.get("id"), "score": item.get("score") or item.get("distance"), "text": item.get("text") or item.get("document") or item.get("content"), "meta": item.get("meta") or item.get("metadata") or {}})
                    elif isinstance(item, (list, tuple)) and len(item) >= 2:
                        # (id, score) or (id, score, text)
                        idv = item[0]
                        score = item[1]
                        text = item[2] if len(item) > 2 else None
                        meta = item[3] if len(item) > 3 else {}
                        out.append({"id": idv, "score": score, "text": text, "meta": meta})
                    else:
                        out.append({"id": None, "score": None, "text": str(item), "meta": {}})
                return out
        except Exception:
            logger.debug("Iterable normalization failed", exc_info=True)

        # Last resort: wrap the resp as single result with text representation
        try:
            out.append({"id": None, "score": None, "text": str(resp), "meta": {}})
        except Exception:
            out = []

        return out
# ...existing code...

def remove_double_words(text):
    # FIXED: Correct regex to remove consecutive repeated words
    return re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)

def clean_transcript(text):
    # Remove duplicate lines, strip, and double words
    lines = text.split('\n')
    unique_lines = []
    prev_line = None
    
    for line in lines:
        line = line.strip()
        if not line or line == prev_line:
            continue
        
        cleaned = remove_double_words(line)
        if cleaned != prev_line:
            unique_lines.append(cleaned)
            prev_line = cleaned
    
    return ' '.join(unique_lines)

# ---- VECTORSTORE FUNCTIONS ----

_embeddings = get_embeddings()
FAISS_INDEX_PATH = config.CHROMA_DB_PATH.replace("chroma", "faiss")
os.makedirs(FAISS_INDEX_PATH, exist_ok=True)

_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
        if os.path.exists(index_file):
            try:
                _vectorstore = FAISS.load_local(
                    FAISS_INDEX_PATH,
                    _embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"✓ Loaded existing FAISS index from {FAISS_INDEX_PATH}")
            except Exception as e:
                print(f"⚠ Could not load existing index: {e}")
                _vectorstore = FAISS.from_texts(["initialization"], _embeddings)
        else:
            _vectorstore = FAISS.from_texts(["initialization"], _embeddings)
            print(f"✓ Created new FAISS index at {FAISS_INDEX_PATH}")
    
    return _vectorstore

def add_to_vectorstore(texts):
    vectorstore = get_vectorstore()
    vectorstore.add_texts(texts)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"✓ Added {len(texts)} texts to FAISS and saved to disk")

def clear_vectorstore():
    global _vectorstore
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    pkl_file = os.path.join(FAISS_INDEX_PATH, "index.pkl")
    
    if os.path.exists(index_file):
        os.remove(index_file)
    if os.path.exists(pkl_file):
        os.remove(pkl_file)
    
    _vectorstore = None
    print("✓ Cleared FAISS vectorstore")

def load_vectorstore_for_video(video_id: str):
    path = f"./data/faiss/{video_id}/"
    if not os.path.exists(path):
        raise FileNotFoundError(f"No vectorstore found for video ID: {video_id}")
    
    return FAISS.load_local(
        path,
        _embeddings,
        allow_dangerous_deserialization=True
    )

def create_vectorstore_for_video(video_id: str, transcript: str):
    # FIXED: Clean the transcript before processing
    transcript = clean_transcript(transcript)
    
    # Split transcript into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.split_text(transcript)
    
    # Create vectorstore from chunks
    vectorstore = FAISS.from_texts(
        texts=chunks,
        embedding=_embeddings
    )
    
    # Save to disk
    path = f"./data/faiss/{video_id}/"
    os.makedirs(path, exist_ok=True)
    vectorstore.save_local(path)
    
    print(f"✓ Created and saved vectorstore for video {video_id} with {len(chunks)} chunks (cleaned)")
    return vectorstore
