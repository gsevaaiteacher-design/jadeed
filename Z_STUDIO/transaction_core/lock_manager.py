# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-06-V5 (PATCHED)
# ROLE: LOCK MANAGER (V5 - ROLLBACK-SAFE & RECOVERY-AWARE)
# SIGNATOR: OMEGA-LOCK-V5-FINAL-FIX
# =================================================================

import threading
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List

# Setup Logger for the module
logger = logging.getLogger("Z-LockManager")

@dataclass
class LockObject:
    resource_id: str
    mutex: threading.Lock = field(default_factory=threading.Lock)
    owner_tx_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    wait_queue_count: int = 0

class LockManager:
    def __init__(self):
        self._global_lock = threading.Lock()
        self._registry: Dict[str, LockObject] = {}
        # Fixed: Ensuring class has access to logger
        self.logger = logger

    def acquire_multiple(self, resource_ids: List[str], tx_id: str, timeout: float = 10.0) -> bool:
        """
        FIX 1 & 2: ROLLBACK-SAFE ACQUISITION + GLOBAL DEADLINE.
        Sorted acquisition to prevent circular wait + cleanup on partial fail.
        """
        sorted_ids = sorted(list(set(resource_ids)))
        acquired_ids = []
        start_deadline = time.time()

        try:
            for res_id in sorted_ids:
                elapsed = time.time() - start_deadline
                remaining = timeout - elapsed
                
                if remaining <= 0:
                    raise RuntimeError(f"GLOBAL_TIMEOUT: TX_{tx_id} failed to secure all locks in {timeout}s")
                
                if self.acquire(res_id, tx_id, timeout=remaining):
                    acquired_ids.append(res_id)
            return True
        except Exception as e:
            # ROLLBACK: Release what was already taken
            self.logger.warning(f"PARTIAL_LOCK_FAILURE: TX_{tx_id} rolling back locks. Error: {str(e)}")
            for res_id in reversed(acquired_ids):
                self.release(res_id, tx_id)
            raise e

    def acquire(self, resource_id: str, tx_id: str, timeout: float = 10.0) -> bool:
        """Atomic Metadata Binding with Timeout Watchdog."""
        with self._global_lock:
            if resource_id not in self._registry:
                self._registry[resource_id] = LockObject(resource_id=resource_id)
            
            lock_obj = self._registry[resource_id]
            if lock_obj.owner_tx_id == tx_id:
                return True # Re-entrant safe
            
            lock_obj.wait_queue_count += 1

        # Real mutex wait outside global lock to prevent manager-wide hang
        success = lock_obj.mutex.acquire(timeout=timeout)
        
        with self._global_lock:
            lock_obj.wait_queue_count -= 1
            if success:
                lock_obj.owner_tx_id = tx_id
                lock_obj.timestamp = time.time()
                return True
        
        raise RuntimeError(f"LOCK_TIMEOUT: Resource {resource_id} is held by TX_{lock_obj.owner_tx_id}")

    def release(self, resource_id: str, tx_id: str):
        """Strict Ownership Release: Only owner can unlock."""
        with self._global_lock:
            lock_obj = self._registry.get(resource_id)
            if not lock_obj or lock_obj.owner_tx_id != tx_id:
                return

            lock_obj.owner_tx_id = None
            try:
                lock_obj.mutex.release()
            except RuntimeError:
                pass # Already unlocked

    def recover_orphan_locks(self):
        """
        CRASH RECOVERY: Reconciles mutex state with metadata.
        """
        with self._global_lock:
            for res_id, lock_obj in self._registry.items():
                # Bug Fix: Checked if locked but owner info lost in crash
                if lock_obj.mutex.locked() and lock_obj.owner_tx_id is None:
                    try:
                        lock_obj.mutex.release()
                        self.logger.info(f"RECOVERY_SUCCESS: Orphan lock on {res_id} released.")
                    except Exception as e:
                        self.logger.error(f"RECOVERY_ERROR: Could not release {res_id}: {str(e)}")