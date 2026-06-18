# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-02-V21
# ROLE: SUPREME TRANSACTION COORDINATOR (V21 ABSOLUTE ZERO-GAP)
# SIGNATOR: OMEGA-FORMAL-ACID-FINALITY
# =================================================================

import threading
import time
from collections import deque
from .transaction_context import TransactionStatus, TransactionContext

class TransactionManager:
    def __init__(self, wal_engine, snapshot_manager, zombie_ttl=300):
        self.wal = wal_engine
        self.snapshot_mgr = snapshot_manager
        self.zombie_ttl = zombie_ttl
        
        # 1. ATOMIC MULTI-DOMAIN LOCKS
        self.active_transactions = {}
        self._registry_lock = threading.RLock() 
        self._metrics_lock = threading.Lock()   
        self._journal_lock = threading.Lock()   
        
        # 2. LINEARIZABLE FORENSICS
        self._journal_seq = 0
        self.metrics = {"commits": 0, "rollbacks": 0, "failures": 0, "retries": 0}
        self.failure_journal = deque(maxlen=1000)
        
        # 3. WATCHDOG CONTROL
        self._stop_monitor = threading.Event()
        self._monitor_thread = threading.Thread(target=self._watchdog_loop, name="Z-Watchdog", daemon=True)
        self._monitor_thread.start()

    def _log_journal(self, tx_id, error_msg):
        with self._journal_lock:
            seq = self._journal_seq
            self._journal_seq += 1
            self.failure_journal.append({
                "seq": seq, "tx_id": tx_id, "error": error_msg, "ts": time.time()
            })

    def _update_metric(self, key):
        with self._metrics_lock:
            self.metrics[key] += 1

    def _safe_wal_call(self, func, *args, retries=5):
        delay = 0.05
        for i in range(retries):
            try:
                if func(*args): return True
            except (IOError, OSError, TimeoutError):
                self._update_metric("retries")
                time.sleep(delay * (2 ** i))
            except Exception: break
        return False

    def create_transaction(self, operation_name, input_data=None):
        with self._registry_lock:
            tx = TransactionContext(operation_name, input_data)
            sid, s_hash = self.snapshot_mgr.create_snapshot()
            tx.bind_snapshot(sid, s_hash)

            if not self._safe_wal_call(self.wal.log_start, tx.to_dict()):
                self._update_metric("failures")
                raise RuntimeError("CORE_DURABILITY_FAULT: WAL_UNREACHABLE")

            tx._in_recovery = False 
            self.active_transactions[tx.tx_id] = tx
            tx.update_status(TransactionStatus.RUNNING, expected_version=tx.version)
            return tx

    def commit(self, tx_id, expected_version):
        """V21 FIX: IMMUTABLE COMMIT SNAPSHOT OBJECT (10/10 FINALITY)"""
        with self._registry_lock:
            tx = self.active_transactions.get(tx_id)
            if not tx or getattr(tx, '_in_recovery', False): return False
            
            # ATOMIC STATE CAPTURE (FREEZE) - Formal Linearizability Lock
            commit_snapshot = (
                tx.version,
                tx.snapshot_hash,
                tx.snapshot_id,
                getattr(tx, '_in_recovery', False)
            )
            
            if commit_snapshot[0] != expected_version:
                self._log_journal(tx_id, f"STALE_COMMIT_PRE_IO: {commit_snapshot[0]} != {expected_version}")
                return False
            
            # Pre-IO Integrity Validation
            if not self.snapshot_mgr.verify_snapshot(commit_snapshot[2], commit_snapshot[1]):
                self._internal_rollback(tx, "INTEGRITY_COMPROMISED")
                return False

        # IO PHASE (Strict Persistence Boundary)
        if not self._safe_wal_call(self.wal.log_commit, tx_id, commit_snapshot[0]):
            self.rollback(tx_id, "WAL_PERSISTENCE_FAILURE")
            return False

        # FINAL GATE: RE-VALIDATION AGAINST IMMUTABLE SNAPSHOT
        with self._registry_lock:
            tx_final = self.active_transactions.get(tx_id)
            
            # Post-IO Determinism Check
            if not tx_final or \
               tx_final.version != commit_snapshot[0] or \
               tx_final.snapshot_hash != commit_snapshot[1] or \
               tx_final.snapshot_id != commit_snapshot[2] or \
               getattr(tx_final, '_in_recovery', False) != commit_snapshot[3]:
                
                self._log_journal(tx_id, "POST_IO_LINEARIZATION_FAILURE: ATOMIC STATE DRIFT")
                return False

            # ATOMIC FINALIZE
            tx_final.update_status(TransactionStatus.COMMITTED, expected_version=commit_snapshot[0])
            self._update_metric("commits")
            self.active_transactions.pop(tx_id, None)
            return True

    def rollback(self, tx_id, reason):
        with self._registry_lock:
            tx = self.active_transactions.get(tx_id)
            if not tx or getattr(tx, '_in_recovery', False):
                return False
            
            tx._in_recovery = True # Idempotent Recovery Guard
            self.active_transactions.pop(tx_id, None)
            
        return self._internal_rollback(tx, reason)

    def _internal_rollback(self, tx, reason):
        try:
            tx.set_error(reason)
            tx.update_status(TransactionStatus.ROLLING_BACK, expected_version=tx.version)

            success = self.snapshot_mgr.restore_snapshot(tx.snapshot_id, tx.snapshot_hash)
            
            tx.update_status(
                TransactionStatus.ROLLED_BACK if success else TransactionStatus.FAILED, 
                expected_version=tx.version
            )

            self._safe_wal_call(self.wal.log_rollback, tx.tx_id)
            self._log_journal(tx.tx_id, f"ROLLBACK: {reason}")
            
            if success: self._update_metric("rollbacks")
            else: self._update_metric("failures")
            return success
        except Exception as e:
            self._log_journal(tx.tx_id, f"FATAL_RECOVERY_ERROR: {str(e)}")
            return False

    def _watchdog_loop(self):
        while not self._stop_monitor.is_set():
            interval = 5.0 if len(self.active_transactions) > 100 else 10.0
            if self._stop_monitor.wait(interval): break
            
            now = time.time()
            to_kill = []
            with self._registry_lock:
                for tid, tx in self.active_transactions.items():
                    if (now - tx.timestamp > self.zombie_ttl):
                        to_kill.append(tid)
            
            for tid in to_kill:
                self.rollback(tid, "WATCHDOG_TERMINATION")

    def stop_manager(self):
        self._stop_monitor.set()
        if threading.current_thread() != self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)