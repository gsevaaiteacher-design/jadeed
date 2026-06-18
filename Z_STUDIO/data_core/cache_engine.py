#  Z-STUDIO V12.3 | FILE 6.3: CACHE_ENGINE.PY | PHASE 6: DATA SYSTEM
#  ROLE: INDUSTRIAL SPEED ACCELERATOR (SQLITE-BACKED CACHE)
#  OWNER: ZYNQUAR ATELIER (C) 2026 | V8 FINAL REFINED CORE (10/10)

import diskcache as dc
import logging
import sys
from pathlib import Path

# --- Z-STUDIO STANDARD LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Z-CACHE")

class CacheEngine:
    """
    Z-STUDIO SPEED BRAIN (ENTERPRISE GRADE)
    - Persistent SQLite-backed caching (diskcache)
    - Strict Key Normalization (Whitespace-safe)
    - Automated TTL & Storage Capping (500MB)
    - Multi-process Atomic Consistency
    """
    def __init__(self, base_path="core_assets/memory/cache/"):
        self.base_path = Path(base_path)
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            # size_limit protects disk from overflow
            self.cache = dc.Cache(str(self.base_path), size_limit=500 * 1024 * 1024)
            logger.info("Z-Cache Engine: Operational. Persistence layer locked.")
        except Exception as e:
            logger.critical(f"CACHE INITIALIZATION FAILURE: {e}")
            raise

    def _validate_key(self, key: str) -> str:
        """Internal helper to ensure keys are valid and normalized."""
        if not key or not isinstance(key, str) or not key.strip():
            return None
        return key.strip()

    def set(self, key: str, value: object, ttl: int = 3600) -> bool:
        """Atomic Set: Stores data with mandatory expiration (TTL)."""
        valid_key = self._validate_key(key)
        if not valid_key:
            logger.warning("Cache Set blocked: Invalid/Empty key provided.")
            return False
        
        try:
            self.cache.set(valid_key, value, expire=ttl)
            return True
        except Exception as e:
            logger.error(f"Cache set failed [Key: {valid_key}]: {e}")
            return False

    def get(self, key: str) -> object:
        """Fast Path Retrieval: Returns data or None on MISS."""
        valid_key = self._validate_key(key)
        if not valid_key:
            return None
        try:
            return self.cache.get(valid_key)
        except Exception as e:
            logger.error(f"Cache retrieval failed [Key: {valid_key}]: {e}")
            return None

    def invalidate(self, key: str) -> bool:
        """Manual Eviction: Removes specific key with normalization fix."""
        valid_key = self._validate_key(key)
        if not valid_key:
            return False
        try:
            #  FIX: Ensure return is boolean for API consistency
            return bool(self.cache.delete(valid_key))
        except Exception as e:
            logger.error(f"Cache invalidation failed [Key: {valid_key}]: {e}")
            return False

    def clear(self) -> bool:
        """Global Reset: Wipes all speed-layer data."""
        try:
            self.cache.clear()
            logger.warning("Z-Cache: Global clear-down command executed.")
            return True
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False

    def close(self):
        """Safely release SQLite handles for clean shutdown."""
        try:
            self.cache.close()
        except Exception as e:
            logger.error(f"Error during cache shutdown: {e}")

# --- PRODUCTION READINESS TEST ---
if __name__ == "__main__":
    speed_layer = CacheEngine()
    # Test with dirty key and structured object
    if speed_layer.set("  user_session_42  ", {"auth": True, "role": "admin"}, ttl=30):
        res = speed_layer.get("user_session_42") # Testing stripped retrieval
        logger.info(f"CACHE TEST STATUS: {res}")
