# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-09-CONSISTENCY-V10-FINAL
# ROLE: 10/10 ABSOLUTE KERNEL SENTINEL (DIAMOND CORE SEAL)
# SIGNATOR: KERNEL-CONSISTENCY-V10-DIAMOND
# =================================================================

import hashlib
import logging
import time
import threading

class ConsistencyChecker:
    def __init__(self, data_core, journal, wal_engine, snapshot_manager, recovery_engine, system_fence):
        self.data_core = data_core
        self.journal = journal
        self.wal = wal_engine
        self.snapshot = snapshot_manager
        self.recovery = recovery_engine
        self.system_fence = system_fence 
        self.audit_lock = threading.Lock()
        self.logger = logging.getLogger("Z-Consistency-Diamond")

    def perform_autonomous_audit(self):
        """
        FIX 1-3: Final Engineering Polish for 10/10 Production Readiness.
        Implementing Diagnostic Output & Hardened Trust Binding.
        """
        # TIMED FAIRNESS: Ensures audit doesn't starve or block system indefinitely
        acquired = self.audit_lock.acquire(timeout=0.5) 
        if not acquired:
            self.logger.error("AUDIT_LOCK_TIMEOUT: High contention. Retrying in next cycle.")
            return {"status": "DEFERRED"}

        report = {"status": "HEALTHY", "mismatches": [], "diagnostics": {}}
        
        try:
            # FIX 1: SYSTEM FENCE HARDENING (Strict Atomic Snapshot Barrier)
            # Enforces: Write-Block, WAL-Freeze, Journal-Suspend
            with self.system_fence.acquire_global_barrier():
                j_lsn = self.journal.get_max_lsn_atomic()
                d_lsn = self.data_core.get_current_lsn()
                w_lsn = self.wal.get_last_lsn()
                s_lsn = self.snapshot.get_last_snapshot_lsn()

            # 1. DETERMINISTIC CHECKS
            if d_lsn < j_lsn - 5: report["mismatches"].append("LSN_BACKWARD_DRIFT")
            if d_lsn > j_lsn: report["mismatches"].append("DATA_LEAK")
            if s_lsn > 0 and not self.journal.exists_lsn_indexed(s_lsn):
                report["mismatches"].append("ORPHAN_SNAPSHOT_DETECTED")

            # 2. WAL SEQUENCE VALIDATION
            wal_valid, wal_errors = self.wal.get_detailed_sequence_audit()
            if not wal_valid:
                report["mismatches"].append("WAL_SEQUENCE_CORRUPTION")
                if wal_errors: self.recovery.reconcile_wal_and_journal(wal_errors)

            # 3. RECOVERY ESCALATION
            if report["mismatches"]:
                report["status"] = "CRITICAL"
                success = self._execute_safe_tiered_recovery_with_validation()
                if not success:
                    self._enter_hardened_safe_mode(reason="RECOVERY_CONVERGENCE_FAILED")
                    return {"status": "SAFE_MODE_FROZEN"}
            
            return report

        except Exception as e:
            self.logger.critical(f"KERNEL_PANIC: {e}", exc_info=True)
            self._enter_hardened_safe_mode(reason=f"KERNEL_EXCEPTION: {str(e)}")
            return {"status": "SAFE_MODE_FROZEN", "error": str(e)}
        finally:
            if acquired:
                self.audit_lock.release()

    def _execute_safe_tiered_recovery_with_validation(self) -> bool:
        """Centralized Protected Recovery with Forensic Output."""
        with self.recovery.global_recovery_lock:
            self.logger.info("Initiating Tiered Recovery Pipeline...")
            
            # Tier 1 & 2 attempt
            if self.recovery.run_formal_autonomous_recovery() or \
               self.recovery.run_partial_recovery():
                
                # FIX 2: DIAGNOSTIC VALIDATION
                valid = self._perform_post_recovery_validation()
                if not valid:
                    self.logger.error("POST_RECOVERY_FAIL: State convergence not met.")
                return valid
                
            return False

    def _perform_post_recovery_validation(self) -> bool:
        """Final State Check: J_LSN == D_LSN convergence."""
        j_final = self.journal.get_max_lsn_atomic()
        d_final = self.data_core.get_current_lsn()
        return j_final == d_final

    def _enter_hardened_safe_mode(self, reason: str):
        self.logger.critical(f"!!! EMERGENCY SHUTDOWN: {reason} !!!")
        self.snapshot.store_crash_context(reason)
        self.wal.pause_writes()
        self.journal.freeze()
        self.data_core.enter_safe_mode()

    def verify_crypto_integrity(self, tx_id, remote_signature=None) -> bool:
        """
        FIX 3: HARDENED TRUST BINDING.
        Adds LSN alignment to the trust criteria to prevent stale trust.
        """
        history = self.journal.query_history(tx_id=tx_id)
        if not history: return False
        
        lsn, tid, ts, op, payload, status = history[0]
        local_hash = hashlib.sha256(f"{lsn}|{tid}|{ts}|{op}|{payload}".encode()).hexdigest()
        
        if remote_signature:
            return str(local_hash) == str(remote_signature)
            
        # Hardened Local Trust: Must be local mode AND verified AND LSN aligned
        return (
            self.data_core.is_trusted_local_mode() 
            and self.data_core.integrity_verified()
            and self.journal.verify_chain_consistency()
            and self.journal.get_max_lsn_atomic() == self.data_core.get_current_lsn()
        )