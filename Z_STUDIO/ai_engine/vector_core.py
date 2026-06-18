"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 9: vector_core.py
ROLE: Memory Similarity Search Engine (SAFE + NORMALIZED + STABLE)
STATUS: WIRED + PRODUCTION READY CORE
"""

import math
import threading


class VectorCore:
    """
     ROLE:
    AI memory retrieval system (semantic similarity engine)

     RULE:
    - No corruption allowed
    - No vector mismatch allowed
    - Deterministic similarity only
    """

    def __init__(self):

        # Simulated vector DB (replaceable with FAISS/Chroma/Qdrant)
        self._vector_db = []

        # THREAD SAFETY (IMPORTANT FOR ORCHESTRATOR PARALLEL CALLS)
        self._lock = threading.RLock()

    # =====================================================
    # SEARCH ENGINE
    # =====================================================
    def search(self, query_vector, top_k=3):
        """
         INPUT: query_vector (list[float])
         OUTPUT: top matching memory chunks
        """

        if not self._is_valid_vector(query_vector):
            return []

        with self._lock:

            if not self._vector_db:
                return []

            scored = []

            for item in self._vector_db:

                stored_vec = item.get("vector")

                if not self._is_valid_vector(stored_vec):
                    continue

                score = self._cosine_similarity(query_vector, stored_vec)

                scored.append((score, item.get("content", "")))

            # Sort high similarity first
            scored.sort(key=lambda x: x[0], reverse=True)

            return [c for _, c in scored[:top_k]]

    # =====================================================
    # VECTOR ADDITION
    # =====================================================
    def add_to_index(self, vector, content):

        if not self._is_valid_vector(vector):
            return False

        with self._lock:

            self._vector_db.append({
                "vector": self._normalize(vector),
                "content": str(content)
            })

        return True

    # =====================================================
    # COSINE SIMILARITY CORE
    # =====================================================
    def _cosine_similarity(self, a, b):

        if len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    # =====================================================
    # VECTOR NORMALIZATION (CRITICAL FIX)
    # =====================================================
    def _normalize(self, vector):

        norm = math.sqrt(sum(x * x for x in vector))

        if norm == 0:
            return vector

        return [x / norm for x in vector]

    # =====================================================
    # VALIDATION GUARD (ANTI CRASH)
    # =====================================================
    def _is_valid_vector(self, vec):

        if not isinstance(vec, (list, tuple)):
            return False

        if len(vec) == 0:
            return False

        return all(isinstance(x, (int, float)) for x in vec)