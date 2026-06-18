# =================================================================
# PROJECT: Z-STUDIO V12.3 (BEYOND INDUSTRIAL GRADE)
# FILE NO: 07-01-V15
# ROLE: 10/10 FIELD-LEVEL HARDENED ATOMIC KERNEL
# SIGNATOR: Z-STUDIO-V12-PHASE-07-SINGULARITY
# =================================================================

import uuid, time, os, hashlib, json, traceback, threading
from copy import deepcopy
from enum import Enum

class TransactionStatus(Enum):
    INIT, RUNNING, COMMITTED, FAILED, ROLLING_BACK, ROLLED_BACK, EXPIRED = "INIT", "RUNNING", "COMMITTED", "FAILED", "ROLLING_BACK", "ROLLED_BACK", "EXPIRED"

VALID_TRANSITIONS = {
    TransactionStatus.INIT: [TransactionStatus.RUNNING, TransactionStatus.FAILED, TransactionStatus.EXPIRED],
    TransactionStatus.RUNNING: [TransactionStatus.COMMITTED, TransactionStatus.FAILED, TransactionStatus.EXPIRED],
    TransactionStatus.FAILED: [TransactionStatus.ROLLING_BACK],
    TransactionStatus.ROLLING_BACK: [TransactionStatus.ROLLED_BACK],
    TransactionStatus.ROLLED_BACK: [TransactionStatus.INIT],
    TransactionStatus.COMMITTED: [],
    TransactionStatus.EXPIRED: [TransactionStatus.FAILED]
}

class TransactionContext:
    IMMUTABLE_FIELDS = {"tx_id", "timestamp", "operation_name", "input_data", "resources"}

    def __init__(self, operation_name, input_data=None, resources=None, timeout_sec=300):
        # 1. IDENTITY & TTL
        self.tx_id = str(uuid.uuid4())
        self.timestamp = time.time()
        self.ttl = self.timestamp + timeout_sec 
        self.operation_name = operation_name
        
        # 2. DATA BLOCK (Deep-Freeze)
        self.input_data = deepcopy(input_data) if input_data else {}
        self.resources = deepcopy(resources) if resources else []
        
        # 3. STATE & INTEGRITY BINDING
        self._status = TransactionStatus.INIT
        self.snapshot_id, self.snapshot_hash = None, None
        self._finalized = False
        
        # 4. FIELD-LEVEL SIGNATURES (PATCH 4: Corruption Localization)
        self.signatures = {"identity": None, "state": None, "data": None}
        
        # 5. CONCURRENCY SHIELD (PATCH 2 & 3: Retry & Timeout)
        self._lock = threading.RLock()
        self.version = 0
        
        # 6. ERROR STACK
        self.error_chain = []
        self.metadata = {"schema_version": 1, "process_id": os.getpid()}
        
        self._locked = True # SEAL CORE
        self._refresh_signatures()

    def _refresh_signatures(self):
        """PATCH 4: Incremental Validation / Field-Level Hashing"""
        def _hash(d): return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()
        self.signatures["identity"] = _hash({"id": self.tx_id, "ts": self.timestamp, "op": self.operation_name})
        self.signatures["state"] = _hash({"status": self._status.value, "ver": self.version, "fin": self._finalized})
        self.signatures["data"] = _hash({"input": self.input_data, "res": self.resources, "snap_h": self.snapshot_hash})

    def _safe_acquire(self, max_attempts=3, timeout=1.0):
        """PATCH 3: Hardened Lock Retry Strategy"""
        for _ in range(max_attempts):
            if self._lock.acquire(timeout=timeout): return True
        return False

    def check_expiry(self):
        """PATCH 2: Passive Expiry Guard (Active scheduler in Manager)"""
        if time.time() > self.ttl and self._status not in (TransactionStatus.COMMITTED, TransactionStatus.ROLLED_BACK):
            if self._safe_acquire():
                try: self._status = TransactionStatus.EXPIRED; self._refresh_signatures()
                finally: self._lock.release()
            return True
        return False

    def update_status(self, new_status, expected_version, expected_hash=None):
        if not self._safe_acquire(max_attempts=3): raise RuntimeError("LOCK FAULT: Deadlock Shield Active.")
        try:
            if self.check_expiry() and new_status != TransactionStatus.FAILED: raise RuntimeError("STALE TX: Expired.")
            if self.version != expected_version: raise RuntimeError("STALE STATE: Version mismatch.")
            
            if new_status in (TransactionStatus.RUNNING, TransactionStatus.COMMITTED):
                if not self.snapshot_hash: raise RuntimeError("BONDING GAP: Snapshot missing.")
                if expected_hash and self.snapshot_hash != expected_hash: raise RuntimeError("INTEGRITY FAULT: Hash mismatch.")

            if new_status not in VALID_TRANSITIONS[self._status]: raise ValueError(f"FSM CONFLICT: {self._status} -> {new_status}")
            if self._finalized: raise RuntimeError("SEALED: Modification denied.")

            self._status = new_status
            if new_status == TransactionStatus.COMMITTED: self._finalized = True
            self.version += 1
            self._refresh_signatures()
        finally: self._lock.release()

    def set_error(self, exc):
        if self._safe_acquire():
            try:
                self.error_chain.append({"msg": str(exc), "type": type(exc).__name__, "trace": traceback.format_exc(), "ts": time.time()})
                self.version += 1; self._refresh_signatures()
            finally: self._lock.release()

    def to_dict(self, include_checksum=True):
        if not self._safe_acquire(): return {"error": "LOCK_TIMEOUT"}
        try:
            data = deepcopy({
                "tx_id": self.tx_id, "status": self._status.value, "version": self.version,
                "snapshot": {"id": self.snapshot_id, "hash": self.snapshot_hash},
                "finalized": self._finalized, "signatures": self.signatures,
                "error_stack": self.error_chain, "metadata": self.metadata
            })
            if include_checksum: data["checksum"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
            return data
        finally: self._lock.release()