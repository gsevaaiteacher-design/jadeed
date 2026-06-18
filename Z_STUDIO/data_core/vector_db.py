#  Z-STUDIO V12.3 | VECTOR_DB.PY | PHASE 6: DATA SYSTEM
#  ROLE: BUS-CONTROLLED SEMANTIC ENGINE (FAISS WRAPPER - HARDENED)
#  OWNER: ZYNQUAR ATELIER (C) 2026 | PRODUCTION SAFE CORE

from pathlib import Path
import threading

class VectorDB:

    def __init__(
        self,
        runtime_bus=None,
        base_path="core_assets/memory/vectors/",
        dimension=384
    ):

        # ==============================================================================
        # BUS VALIDATION
        # ==============================================================================

        if runtime_bus is None:
            raise RuntimeError("[VECTOR_DB][FATAL] runtime_bus is missing")

        if not hasattr(runtime_bus, "request"):
            raise RuntimeError("[VECTOR_DB][FATAL] runtime_bus missing request()")

        self.bus = runtime_bus

        # ==============================================================================
        # STORAGE PATHS
        # ==============================================================================

        self.base_path = Path(base_path)
        self.index_path = self.base_path / "index.faiss"
        self.map_path = self.base_path / "id_map.json"

        self.dimension = dimension

        self.base_path.mkdir(parents=True, exist_ok=True)

        # ==============================================================================
        # THREAD SAFETY
        # ==============================================================================

        self._lock = threading.Lock()

        # ==============================================================================
        # MEMORY MAP
        # ==============================================================================

        self.id_map = []

        # ==============================================================================
        # FAISS BACKEND (BUS ONLY)
        # ==============================================================================
        self.faiss = self.bus.resolve("FAISS_BACKEND")

        if self.faiss is None:
            raise RuntimeError(
                "[VECTOR_DB][FATAL] FAISS_BACKEND not registered in runtime_bus."
            )
        
        print(f"[DEBUG] Bus services available: {list(self.bus._services.keys())}")

        # IMPORTANT: FAISS MUST BE MODULE STYLE (NOT DICT)
        if not hasattr(self.faiss, "IndexFlatL2"):
            raise RuntimeError(
                "[VECTOR_DB][FATAL] Invalid FAISS backend (expected faiss module)"
            )

        # ==============================================================================
        # INDEX INIT
        # ==============================================================================

        self.index = self.faiss.IndexFlatL2(self.dimension)

        # load existing data
        self.load()

    # =========================================================
    # NORMALIZATION
    # =========================================================

    def _normalize(self, vector):
        v = np.array([vector], dtype="float32")
        norm = np.linalg.norm(v) + 1e-10
        return v / norm

    # =========================================================
    # ADD VECTOR
    # =========================================================

    def add(self, vector: list, data_id: str) -> bool:

        if not vector or len(vector) != self.dimension:
            return False

        try:
            vec = self._normalize(vector)

            with self._lock:

                before = self.index.ntotal
                self.index.add(vec)
                after = self.index.ntotal

                if after != before + 1:
                    raise RuntimeError("FAISS index mismatch (ntotal broken)")

                self.id_map.append(data_id)

            return True

        except Exception as e:
            print(f"[VECTOR_DB][ADD_ERROR] {e}")
            return False

    # =========================================================
    # SEARCH VECTOR
    # =========================================================

    def search(self, query_vector: list, top_k: int = 5) -> list:

        if not query_vector or self.index.ntotal == 0:
            return []

        try:
            q = self._normalize(query_vector)

            with self._lock:
                distances, indices = self.index.search(q, top_k)

            results = []

            for i, idx in enumerate(indices[0]):

                if idx == -1:
                    continue

                if idx >= len(self.id_map):
                    continue

                dist = float(distances[0][i])
                score = 1.0 / (1.0 + dist)

                results.append({
                    "id": self.id_map[idx],
                    "score": round(score, 4)
                })

            return results

        except Exception as e:
            print(f"[VECTOR_DB][SEARCH_ERROR] {e}")
            return []

    # =========================================================
    # SAVE INDEX
    # =========================================================

    def save(self) -> bool:

        try:
            with self._lock:

                self.faiss.write_index(
                    self.index,
                    str(self.index_path)
                )

                with open(self.map_path, "w", encoding="utf-8") as f:
                    json.dump(self.id_map, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"[VECTOR_DB][SAVE_ERROR] {e}")
            return False

    # =========================================================
    # LOAD INDEX
    # =========================================================

    def load(self) -> bool:

        try:
            if not self.index_path.exists() or not self.map_path.exists():
                return False

            with self._lock:

                idx = self.faiss.read_index(str(self.index_path))

                if idx.d != self.dimension:
                    raise RuntimeError("Dimension mismatch detected")

                self.index = idx

                with open(self.map_path, "r", encoding="utf-8") as f:
                    self.id_map = json.load(f)

            return True

        except Exception as e:
            print(f"[VECTOR_DB][LOAD_ERROR] {e}")
            return False

    # =========================================================
    # CLEAR DB
    # =========================================================

    def clear(self):

        with self._lock:

            self.index = self.faiss.IndexFlatL2(self.dimension)
            self.id_map = []

            if self.index_path.exists():
                self.index_path.unlink()

            if self.map_path.exists():
                self.map_path.unlink()

    # =========================================================
    # STATUS
    # =========================================================

    def status(self):

        return {
            "vectors": self.index.ntotal,
            "dimension": self.dimension,
            "faiss_backend": self.faiss is not None
        }