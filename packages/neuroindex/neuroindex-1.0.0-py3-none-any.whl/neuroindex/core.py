"""
NeuroIndex - Production-Ready Hybrid Vector + Semantic Graph Memory System

🌟 OPEN SOURCE EDITION
======================

This is the community edition of NeuroIndex with the following limits:
- Max 10,000 documents
- 384-dimension embeddings only
- No semantic graph (vector search only)
- No batch operations
- No GPU support

For unlimited documents, any dimension, semantic graph, batch ops, and GPU:
→ Upgrade to NeuroIndex Pro: Contact umeshkumarpal667@gmail.com

Author: Umeshkumar Pal
License: MIT
Repository: https://github.com/Umeshkumar667/NeuroIndex
"""

import hashlib
import logging
import os
import pickle
import queue
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import faiss
import numpy as np

from .exceptions import (
    DimensionMismatchError,
    DocumentNotFoundError,
    IndexCorruptedError,
    InvalidInputError,
    NeuroIndexError,
    StorageError,
)
from .metrics import MetricsCollector

# Configure module logger
logger = logging.getLogger(__name__)

# ============================================
# OPEN SOURCE EDITION LIMITS
# ============================================
MAX_DOCUMENTS_FREE = 10_000
ALLOWED_DIMENSIONS_FREE = [384]  # Only 384 in free version
SEMANTIC_GRAPH_ENABLED = False   # Disabled in free version
BATCH_INSERT_ENABLED = False     # Disabled in free version
GPU_ENABLED = False              # Disabled in free version


def _check_pro_feature(feature_name: str):
    """Display upgrade message for Pro features."""
    logger.warning(
        f"\n"
        f"{'='*60}\n"
        f"⭐ {feature_name} is a NeuroIndex Pro feature!\n"
        f"\n"
        f"Upgrade to unlock:\n"
        f"  ✓ Unlimited documents (vs 10,000 limit)\n"
        f"  ✓ Any embedding dimension\n"
        f"  ✓ Semantic graph traversal\n"
        f"  ✓ Batch insert (15x faster)\n"
        f"  ✓ GPU acceleration\n"
        f"\n"
        f"→ Get Pro: Contact umeshkumarpal667@gmail.com\n"
        f"{'='*60}\n"
    )


# ---------------------------
# Search Result Dataclass
# ---------------------------
@dataclass
class SearchResult:
    """
    Represents a single search result.

    Attributes:
        node_id: Unique identifier for the document
        text: The document text content
        similarity: Cosine similarity score (0-1)
        metadata: User-provided metadata dict
        source: Where the result came from ('cache', 'faiss', 'graph')
    """

    node_id: str
    text: str
    similarity: float
    metadata: Dict[str, Any]
    source: str  # 'cache', 'faiss', 'graph'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "node_id": self.node_id,
            "text": self.text,
            "similarity": self.similarity,
            "metadata": self.metadata,
            "source": self.source,
        }


# ---------------------------
# Bloom Filter for duplicates
# ---------------------------
class BloomFilter:
    """
    Probabilistic data structure for fast duplicate detection.
    """

    def __init__(self, capacity: int = 1000000, error_rate: float = 0.01):
        self.capacity = capacity
        self.error_rate = error_rate
        self.bit_array_size = int(-capacity * np.log(error_rate) / (np.log(2) ** 2))
        self.hash_count = max(1, int(self.bit_array_size * np.log(2) / capacity))
        self.bit_array = np.zeros(self.bit_array_size, dtype=bool)
        self._lock = threading.Lock()

    def _hash(self, item: str, seed: int) -> int:
        return int(hashlib.md5(f"{item}_{seed}".encode()).hexdigest(), 16) % self.bit_array_size

    def add(self, item: str) -> None:
        with self._lock:
            for i in range(self.hash_count):
                self.bit_array[self._hash(item, i)] = True

    def contains(self, item: str) -> bool:
        with self._lock:
            return all(self.bit_array[self._hash(item, i)] for i in range(self.hash_count))

    def clear(self) -> None:
        with self._lock:
            self.bit_array.fill(False)


# ---------------------------
# RAM Cache (LRU)
# ---------------------------
class NeuroCache:
    """Thread-safe LRU cache for frequently accessed documents."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, Dict] = {}
        self.access_order: List[str] = []
        self._lock = threading.RLock()

    def add(self, node_id: str, node: Dict) -> None:
        with self._lock:
            if node_id in self.cache:
                self.access_order.remove(node_id)
            elif len(self.cache) >= self.max_size:
                oldest = self.access_order.pop(0)
                del self.cache[oldest]

            self.cache[node_id] = node
            self.access_order.append(node_id)

    def get(self, node_id: str) -> Optional[Dict]:
        with self._lock:
            if node_id in self.cache:
                self.access_order.remove(node_id)
                self.access_order.append(node_id)
                return self.cache[node_id]
        return None

    def remove(self, node_id: str) -> bool:
        with self._lock:
            if node_id in self.cache:
                del self.cache[node_id]
                self.access_order.remove(node_id)
                return True
        return False

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[SearchResult]:
        results = []
        query_norm = np.linalg.norm(query_vector)

        if query_norm == 0:
            return results

        with self._lock:
            for node_id, node in self.cache.items():
                node_vector = node["vector"]
                node_norm = np.linalg.norm(node_vector)

                if node_norm == 0:
                    continue

                similarity = float(np.dot(query_vector, node_vector) / (query_norm * node_norm))
                results.append(
                    SearchResult(
                        node_id=node_id,
                        text=node["text"],
                        similarity=similarity,
                        metadata=node["metadata"],
                        source="cache",
                    )
                )

        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:k]

    def clear(self) -> None:
        with self._lock:
            self.cache.clear()
            self.access_order.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self.cache)


# ---------------------------
# Persistent Storage (SQLite)
# ---------------------------
class PersistentStorage:
    """SQLite-based persistent storage for documents."""

    def __init__(self, path: str):
        self.path = path
        self.db_path = os.path.join(path, "nodes.db")
        self._local = threading.local()
        os.makedirs(path, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, timeout=30.0)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        c = conn.cursor()

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                vector BLOB NOT NULL,
                text TEXT NOT NULL,
                metadata BLOB,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL,
                creation_time REAL,
                importance_score REAL DEFAULT 1.0
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )

        c.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES ('version', '1.0.0')")
        c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_creation_time ON nodes(creation_time)")

        conn.commit()

    def add_node(self, node: Dict) -> None:
        conn = self._get_connection()
        c = conn.cursor()

        try:
            c.execute(
                """
                INSERT OR REPLACE INTO nodes
                (id, vector, text, metadata, access_count, last_accessed, creation_time, importance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    node["id"],
                    pickle.dumps(node["vector"], protocol=pickle.HIGHEST_PROTOCOL),
                    node["text"],
                    pickle.dumps(node.get("metadata", {}), protocol=pickle.HIGHEST_PROTOCOL),
                    node.get("access_count", 0),
                    node.get("last_accessed", time.time()),
                    node.get("creation_time", time.time()),
                    node.get("importance_score", 1.0),
                ),
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError(f"Failed to add node: {e}")

    def get_node(self, node_id: str) -> Optional[Dict]:
        conn = self._get_connection()
        c = conn.cursor()

        c.execute("SELECT * FROM nodes WHERE id=?", (node_id,))
        row = c.fetchone()

        if row:
            return {
                "id": row[0],
                "vector": pickle.loads(row[1]),
                "text": row[2],
                "metadata": pickle.loads(row[3]) if row[3] else {},
                "access_count": row[4],
                "last_accessed": row[5],
                "creation_time": row[6],
                "importance_score": row[7],
            }
        return None

    def delete_node(self, node_id: str) -> bool:
        conn = self._get_connection()
        c = conn.cursor()

        try:
            c.execute("DELETE FROM nodes WHERE id=?", (node_id,))
            conn.commit()
            return c.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError(f"Failed to delete node: {e}")

    def update_node(self, node_id: str, updates: Dict) -> bool:
        conn = self._get_connection()
        c = conn.cursor()

        set_clauses = []
        values = []

        if "text" in updates:
            set_clauses.append("text=?")
            values.append(updates["text"])

        if "vector" in updates:
            set_clauses.append("vector=?")
            values.append(pickle.dumps(updates["vector"], protocol=pickle.HIGHEST_PROTOCOL))

        if "metadata" in updates:
            set_clauses.append("metadata=?")
            values.append(pickle.dumps(updates["metadata"], protocol=pickle.HIGHEST_PROTOCOL))

        if not set_clauses:
            return False

        values.append(node_id)
        query = f"UPDATE nodes SET {', '.join(set_clauses)} WHERE id=?"

        try:
            c.execute(query, values)
            conn.commit()
            return c.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError(f"Failed to update node: {e}")

    def update_access(self, node_id: str) -> None:
        conn = self._get_connection()
        c = conn.cursor()

        try:
            c.execute(
                "UPDATE nodes SET access_count=access_count+1, last_accessed=? WHERE id=?",
                (time.time(), node_id),
            )
            conn.commit()
        except sqlite3.Error:
            pass

    def get_node_count(self) -> int:
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM nodes")
        return c.fetchone()[0]

    def iterate_all(self, batch_size: int = 1000):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT id, vector, text, metadata FROM nodes")

        while True:
            rows = c.fetchmany(batch_size)
            if not rows:
                break

            for row in rows:
                yield {
                    "id": row[0],
                    "vector": pickle.loads(row[1]),
                    "text": row[2],
                    "metadata": pickle.loads(row[3]) if row[3] else {},
                }

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# ---------------------------
# FAISS Index Manager
# ---------------------------
class FAISSIndexManager:
    """Manages FAISS index for fast vector similarity search."""

    def __init__(self, path: str, dim: int, use_gpu: bool = False):
        self.path = path
        self.dim = dim
        self.index_file = os.path.join(path, "faiss.index")
        self.mapping_file = os.path.join(path, "faiss_mapping.pkl")
        self.use_gpu = use_gpu

        self._lock = threading.RLock()
        self.index: Optional[faiss.Index] = None
        self.id_to_idx: Dict[str, int] = {}
        self.idx_to_id: Dict[int, str] = {}
        self._next_idx = 0

        self._load_or_create()

    def _load_or_create(self) -> None:
        with self._lock:
            if os.path.exists(self.index_file) and os.path.exists(self.mapping_file):
                try:
                    self.index = faiss.read_index(self.index_file)
                    with open(self.mapping_file, "rb") as f:
                        data = pickle.load(f)
                        self.id_to_idx = data["id_to_idx"]
                        self.idx_to_id = data["idx_to_id"]
                        self._next_idx = data["next_idx"]
                    logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
                except Exception as e:
                    logger.warning(f"Failed to load FAISS index: {e}. Creating new index.")
                    self._create_new_index()
            else:
                self._create_new_index()

    def _create_new_index(self) -> None:
        self.index = faiss.IndexFlatIP(self.dim)
        self.id_to_idx = {}
        self.idx_to_id = {}
        self._next_idx = 0
        logger.debug(f"Created new FAISS index with dim={self.dim}")

    def add(self, node_id: str, vector: np.ndarray) -> None:
        with self._lock:
            vector = vector.astype(np.float32)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            self.index.add(vector.reshape(1, -1))

            idx = self._next_idx
            self.id_to_idx[node_id] = idx
            self.idx_to_id[idx] = node_id
            self._next_idx += 1

    def remove(self, node_id: str) -> bool:
        with self._lock:
            if node_id in self.id_to_idx:
                idx = self.id_to_idx[node_id]
                del self.id_to_idx[node_id]
                del self.idx_to_id[idx]
                return True
        return False

    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        with self._lock:
            if self.index.ntotal == 0:
                return []

            query_vector = query_vector.astype(np.float32)
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm

            actual_k = min(k, self.index.ntotal)
            distances, indices = self.index.search(query_vector.reshape(1, -1), actual_k)

            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx in self.idx_to_id:
                    node_id = self.idx_to_id[idx]
                    similarity = float(distances[0][i])
                    results.append((node_id, similarity))

            return results

    def save(self) -> None:
        with self._lock:
            os.makedirs(self.path, exist_ok=True)

            try:
                faiss.write_index(self.index, self.index_file)
                with open(self.mapping_file, "wb") as f:
                    pickle.dump(
                        {
                            "id_to_idx": self.id_to_idx,
                            "idx_to_id": self.idx_to_id,
                            "next_idx": self._next_idx,
                        },
                        f,
                        protocol=pickle.HIGHEST_PROTOCOL,
                    )
                logger.debug(f"Saved FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                raise StorageError(f"Failed to save FAISS index: {e}")

    def rebuild(self, vectors: List[Tuple[str, np.ndarray]]) -> None:
        with self._lock:
            self._create_new_index()

            for node_id, vector in vectors:
                self.add(node_id, vector)

            logger.info(f"Rebuilt FAISS index with {len(vectors)} vectors")

    @property
    def size(self) -> int:
        with self._lock:
            return self.index.ntotal if self.index else 0


# ---------------------------
# NeuroIndex Main Class (Open Source Edition)
# ---------------------------
class NeuroIndex:
    """
    NeuroIndex - Open Source Edition
    
    ⚠️ LIMITATIONS (upgrade to Pro for full features):
    - Max 10,000 documents
    - 384-dimension embeddings only
    - No semantic graph traversal
    - No batch insert
    - No GPU support
    
    Upgrade: Contact umeshkumarpal667@gmail.com
    """

    VERSION = "1.0.0"
    EDITION = "Community"

    def __init__(
        self,
        path: str = "./neuroindex_data",
        dim: int = 384,
        cache_size: int = 10000,
        similarity_threshold: float = 0.7,
        log_level: str = "INFO",
    ):
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(f"{__name__}.NeuroIndex")

        # ============================================
        # OPEN SOURCE LIMITS CHECK
        # ============================================
        if dim not in ALLOWED_DIMENSIONS_FREE:
            _check_pro_feature(f"Embedding dimension {dim}")
            self.logger.warning(f"Dimension {dim} requires Pro. Using 384 instead.")
            dim = 384

        if dim <= 0:
            raise InvalidInputError(f"Dimension must be positive, got {dim}")

        if cache_size < 0:
            raise InvalidInputError(f"Cache size must be non-negative, got {cache_size}")

        self.path = Path(path)
        self.dim = dim
        self._lock = threading.RLock()

        # Initialize components
        self.cache = NeuroCache(max_size=cache_size)
        self.storage = PersistentStorage(str(self.path))
        self.faiss_index = FAISSIndexManager(str(self.path), dim)
        self.bloom = BloomFilter()
        self.metrics = MetricsCollector()

        # Background worker
        self.update_queue: queue.Queue = queue.Queue()
        self._running = True
        self._bg_thread = threading.Thread(target=self._bg_worker, daemon=True)
        self._bg_thread.start()

        self._rebuild_bloom_filter()

        # Check document limit
        doc_count = self.storage.get_node_count()
        if doc_count >= MAX_DOCUMENTS_FREE:
            self.logger.warning(
                f"\n⚠️ Document limit reached ({doc_count}/{MAX_DOCUMENTS_FREE})!\n"
                f"Upgrade to Pro for unlimited documents: umeshkumarpal667@gmail.com\n"
            )

        self.logger.info(
            f"NeuroIndex v{self.VERSION} ({self.EDITION}) initialized at {path} "
            f"(dim={dim}, docs={doc_count}/{MAX_DOCUMENTS_FREE})"
        )

    def _rebuild_bloom_filter(self) -> None:
        count = 0
        for node in self.storage.iterate_all():
            text_hash = hashlib.md5(node["text"].encode()).hexdigest()
            self.bloom.add(text_hash)
            count += 1

    def _bg_worker(self) -> None:
        while self._running:
            try:
                task = self.update_queue.get(timeout=1.0)
                if task[0] == "save":
                    self.faiss_index.save()
                self.update_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Background worker error: {e}")

    def _validate_vector(self, vector: Union[np.ndarray, list]) -> np.ndarray:
        if isinstance(vector, list):
            vector = np.array(vector, dtype=np.float32)

        if not isinstance(vector, np.ndarray):
            raise InvalidInputError(f"Vector must be numpy array or list, got {type(vector)}")

        vector = vector.astype(np.float32)

        if vector.shape[0] != self.dim:
            raise DimensionMismatchError(self.dim, vector.shape[0])

        if np.isnan(vector).any():
            raise InvalidInputError("Vector contains NaN values")

        if np.isinf(vector).any():
            raise InvalidInputError("Vector contains Inf values")

        return vector

    def _validate_text(self, text: str) -> str:
        if not isinstance(text, str):
            raise InvalidInputError(f"Text must be string, got {type(text)}")

        text = text.strip()
        if not text:
            raise InvalidInputError("Text cannot be empty")

        return text

    def add_document(
        self, text: str, vector: Union[np.ndarray, list], metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a document to the index."""
        with self.metrics.measure("add_document"):
            # ============================================
            # DOCUMENT LIMIT CHECK
            # ============================================
            current_count = self.storage.get_node_count()
            if current_count >= MAX_DOCUMENTS_FREE:
                _check_pro_feature("Unlimited documents")
                raise StorageError(
                    f"Document limit reached ({MAX_DOCUMENTS_FREE}). "
                    f"Upgrade to Pro: umeshkumarpal667@gmail.com"
                )

            text = self._validate_text(text)
            vector = self._validate_vector(vector)
            metadata = metadata or {}

            node_id = hashlib.sha256(f"{text}_{vector.tobytes()}".encode()).hexdigest()[:16]
            text_hash = hashlib.md5(text.encode()).hexdigest()

            if self.bloom.contains(text_hash):
                existing = self.storage.get_node(node_id)
                if existing:
                    return node_id

            self.bloom.add(text_hash)

            node = {
                "id": node_id,
                "text": text,
                "vector": vector,
                "metadata": metadata,
                "access_count": 0,
                "last_accessed": time.time(),
                "creation_time": time.time(),
                "importance_score": 1.0,
            }

            with self._lock:
                self.storage.add_node(node)
                self.faiss_index.add(node_id, vector)
                self.cache.add(node_id, node)

            self.update_queue.put(("save",))
            return node_id

    def add_documents_batch(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Batch insert - PRO FEATURE
        
        This feature requires NeuroIndex Pro.
        Upgrade: Contact umeshkumarpal667@gmail.com
        """
        _check_pro_feature("Batch insert")
        
        # Fallback to individual inserts (slower)
        self.logger.info("Using individual inserts (batch requires Pro)")
        ids = []
        for doc in documents:
            try:
                node_id = self.add_document(
                    text=doc["text"],
                    vector=doc["vector"],
                    metadata=doc.get("metadata", {})
                )
                ids.append(node_id)
            except StorageError:
                break  # Hit limit
        return ids

    def search(
        self,
        query_vector: Union[np.ndarray, list],
        k: int = 10,
        use_graph: bool = True,
        use_cache: bool = True,
        min_similarity: float = 0.0,
    ) -> List[SearchResult]:
        """Search for similar documents (vector search only in Community edition)."""
        with self.metrics.measure("search"):
            query_vector = self._validate_vector(query_vector)

            if k <= 0:
                raise InvalidInputError(f"k must be positive, got {k}")

            # ============================================
            # GRAPH DISABLED IN COMMUNITY EDITION
            # ============================================
            if use_graph and SEMANTIC_GRAPH_ENABLED is False:
                # Silently disable graph - don't spam logs
                use_graph = False

            results_dict: Dict[str, SearchResult] = {}

            # 1. Check cache first
            if use_cache and len(self.cache) > 0:
                cache_results = self.cache.search(query_vector, k=k)
                for r in cache_results:
                    if r.similarity >= min_similarity:
                        results_dict[r.node_id] = r
                        self.metrics.record_cache_hit()

            # 2. FAISS search
            faiss_results = self.faiss_index.search(query_vector, k=k * 2)
            self.metrics.record_faiss_search()

            for node_id, similarity in faiss_results:
                if similarity >= min_similarity and node_id not in results_dict:
                    node = self.storage.get_node(node_id)
                    if node:
                        results_dict[node_id] = SearchResult(
                            node_id=node_id,
                            text=node["text"],
                            similarity=similarity,
                            metadata=node["metadata"],
                            source="faiss",
                        )
                        self.cache.add(node_id, node)
                        self.storage.update_access(node_id)

            # 3. NO graph traversal in Community Edition

            results = list(results_dict.values())
            results.sort(key=lambda x: x.similarity, reverse=True)

            return results[:k]

    def search_text(
        self, text: str, embed_fn: Callable[[str], np.ndarray], k: int = 5, **kwargs
    ) -> List[SearchResult]:
        """Search using raw text."""
        vector = embed_fn(text)
        return self.search(query_vector=vector, k=k, **kwargs)

    def get_document(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        cached = self.cache.get(node_id)
        if cached:
            self.metrics.record_cache_hit()
            return cached

        self.metrics.record_cache_miss()

        node = self.storage.get_node(node_id)
        if node:
            self.cache.add(node_id, node)
            return node

        return None

    def delete_document(self, node_id: str) -> bool:
        """Delete a document."""
        with self.metrics.measure("delete_document"):
            with self._lock:
                deleted = self.storage.delete_node(node_id)

                if deleted:
                    self.cache.remove(node_id)
                    self.faiss_index.remove(node_id)
                    self.update_queue.put(("save",))

                return deleted

    def update_document(
        self,
        node_id: str,
        text: Optional[str] = None,
        vector: Optional[Union[np.ndarray, list]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update an existing document."""
        with self.metrics.measure("update_document"):
            updates = {}

            if text is not None:
                updates["text"] = self._validate_text(text)

            if vector is not None:
                updates["vector"] = self._validate_vector(vector)

            if metadata is not None:
                updates["metadata"] = metadata

            if not updates:
                return False

            with self._lock:
                existing = self.storage.get_node(node_id)
                if not existing:
                    return False

                success = self.storage.update_node(node_id, updates)

                if success:
                    cached = self.cache.get(node_id)
                    if cached:
                        cached.update(updates)
                        self.cache.add(node_id, cached)

                    if "vector" in updates:
                        self.faiss_index.remove(node_id)
                        self.faiss_index.add(node_id, updates["vector"])

                    self.update_queue.put(("save",))

                return success

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        doc_count = self.storage.get_node_count()
        return {
            "version": self.VERSION,
            "edition": self.EDITION,
            "total_documents": doc_count,
            "document_limit": MAX_DOCUMENTS_FREE,
            "documents_remaining": max(0, MAX_DOCUMENTS_FREE - doc_count),
            "faiss_vectors": self.faiss_index.size,
            "cache_size": len(self.cache),
            "graph_nodes": 0,  # Disabled in Community
            "graph_edges": 0,  # Disabled in Community
            "dimension": self.dim,
            "path": str(self.path),
            "features": {
                "semantic_graph": False,
                "batch_insert": False,
                "gpu_support": False,
            },
            "upgrade_url": "umeshkumarpal667@gmail.com",
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.summary()

    def rebuild_index(self) -> None:
        """Rebuild FAISS index from storage."""
        self.logger.info("Rebuilding FAISS index...")

        vectors = []
        for node in self.storage.iterate_all():
            vectors.append((node["id"], node["vector"]))

        self.faiss_index.rebuild(vectors)
        self.faiss_index.save()

        self.logger.info(f"Rebuilt FAISS index with {len(vectors)} vectors")

    def clear(self) -> None:
        """Clear all data."""
        self.logger.warning("Clearing all data from index...")

        import shutil

        with self._lock:
            self.cache.clear()
            self.bloom.clear()
            self.storage.close()

            self.faiss_index._create_new_index()
            self.faiss_index.save()

            if self.path.exists():
                try:
                    shutil.rmtree(self.path)
                except (PermissionError, OSError):
                    pass

            self.storage = PersistentStorage(str(self.path))
            self.faiss_index = FAISSIndexManager(str(self.path), self.dim)

        self.logger.info("Index cleared")

    def close(self) -> None:
        """Close the index."""
        self.logger.info("Closing NeuroIndex...")

        self._running = False
        self._bg_thread.join(timeout=5)

        self.faiss_index.save()
        self.storage.close()

        self.logger.info("NeuroIndex closed successfully")

    def __enter__(self) -> "NeuroIndex":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"NeuroIndex(path='{self.path}', dim={self.dim}, docs={self.storage.get_node_count()}, edition='{self.EDITION}')"
