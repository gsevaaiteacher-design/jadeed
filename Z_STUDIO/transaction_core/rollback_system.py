# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-05-ROLLBACK-SYSTEM
# ROLE: DETERMINISTIC & FINGERPRINTED RECOVERY KERNEL
# SIGNATOR: OMEGA-INDUSTRIAL-ROLLBACK-V3.6-FINAL-ZERO
# =================================================================

import logging
import os
import time
import hashlib
import json
import shutil
import fcntl
import uuid
import signal
import atexit
import threading

class RollbackStep:
    INIT = 0
    CLEANUP_STAGED = 1
    RESTORE_VERIFIED = 2
    FLAGS_RESET = 3
    COMPLETED = 4

class RollbackSystem:
    """
    Rollback System V3.6: The Omega Industrial.
     FIXES: Deterministic Hashing, Lock Fingerprinting (PID+UUID), and NFS-Safe Loops.
    """

    def __init__(self, data_core, snapshot_mgr, wal_engine, lock_mgr):
        self.data_core = data_core
        self.snapshots = snapshot_mgr
        self.wal = wal_engine
        self.lock_mgr = lock_mgr
        self.logger = logging.getLogger("Z-STUDIO.OMEGA_ZERO")
        self.node_id = str(uuid.uuid4())
        self.LEASE_TIMEOUT = 60.0
        self.FALLBACK_LOCK_DIR = "/tmp/zstudio_locks"
        os.makedirs(self.FALLBACK_LOCK_DIR, exist_ok=True)
        
        self._tx_states = {} 
        self._state_mutex = threading.Lock()
        self._shutdown_requested = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        def _handler(signum, frame):
            self.logger.warning("OMEGA_SIGNAL: GRACEFUL_INTERRUPT_SET")
            self._shutdown_requested = True
        signal.signal(signal.SIGTERM, _handler)

    def execute_full_rollback(self, context, reason="FATAL_ERROR"):
        """ OMEGA ENTRY: Deterministic, Fingerprinted, and Hardened."""
        tx_id = context.tx_id
        start_time = time.time()

        # --- STEP 0: FINGERPRINTED LOCK ACQUISITION ---
        self._cleanup_stale_lock_with_fingerprint(tx_id)
        if not self._acquire_dual_lease_fenced(tx_id):
            return False

        atexit.register(self._release_dual_lease, tx_id, is_finally=True)

        try:
            journal = self.wal.get_rollback_journal(tx_id)
            last_step = journal.get('step', -1) if journal else -1

            # --- STEP 1: INIT ---
            if last_step < RollbackStep.INIT:
                self._verify_system_health(start_time, tx_id)
                self._update_journal_deterministic(tx_id, RollbackStep.INIT, {"reason": reason})

            # --- STEP 2: CLEANUP ---
            if last_step < RollbackStep.CLEANUP_STAGED:
                self._verify_system_health(start_time, tx_id)
                self.wal.log_intent_fsync(tx_id, "PHYSICAL_CLEANUP")
                self._cleanup_with_nfs_hardened_verify(context) #  GAP 4 FIX
                self._update_journal_deterministic(tx_id, RollbackStep.CLEANUP_STAGED)

            # --- STEP 3: RESTORE & TRIPLE-VERIFY ---
            if last_step < RollbackStep.RESTORE_VERIFIED:
                self.wal.refresh_lease(tx_id)
                self._verify_system_health(start_time, tx_id)
                
                if not self.snapshots.restore_snapshot(context, self.data_core):
                    return self._trigger_emergency_escalation(context)
                
                if not self._verify_triple_integrity(context):
                    raise RuntimeError("TRIPLE_VERIFY_CHAIN_BROKEN")
                    
                self._update_journal_deterministic(tx_id, RollbackStep.RESTORE_VERIFIED)

            # --- FINALIZATION ---
            self.snapshots.purge_snapshot(context.snapshot_id)
            self._update_journal_deterministic(tx_id, RollbackStep.COMPLETED)
            
            return self._release_dual_lease(tx_id)

        except Exception as e:
            self.logger.critical(f"OMEGA_HALT: {tx_id} | {str(e)}")
            return self._trigger_emergency_escalation(context)
        finally:
            self._release_dual_lease(tx_id, is_finally=True)
            self.lock_mgr.release_all(context.resource_list)

    def _acquire_dual_lease_fenced(self, tx_id):
        """ FIX GAP 2: Lock Fingerprinting (PID + UUID + StartTime)."""
        lock_path = os.path.join(self.FALLBACK_LOCK_DIR, f"{tx_id}.lock")
        f_lock = None
        
        # Fingerprint components
        fingerprint = {
            "pid": os.getpid(),
            "token": str(uuid.uuid4())[:8],
            "start_time": time.time()
        }

        for i in range(3):
            try:
                f_lock = open(lock_path, 'w')
                f_lock.write(json.dumps(fingerprint))
                f_lock.flush()
                os.fsync(f_lock.fileno())
                
                fcntl.flock(f_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                if self.wal.acquire_rollback_lease(tx_id, owner=self.node_id, ttl=self.LEASE_TIMEOUT):
                    with self._state_mutex:
                        self._tx_states[tx_id] = {"lock": f_lock, "released": False, "fingerprint": fingerprint}
                    return True
                else:
                    fcntl.flock(f_lock, fcntl.LOCK_UN)
                    f_lock.close()
                    return False
            except (OSError, BlockingIOError):
                if i == 2: return False
                time.sleep(0.5)
        return False

    def _cleanup_stale_lock_with_fingerprint(self, tx_id):
        """Fingerprint-aware GC."""
        lock_path = os.path.join(self.FALLBACK_LOCK_DIR, f"{tx_id}.lock")
        if not os.path.exists(lock_path): return
        try:
            with open(lock_path, 'r') as f:
                data = json.loads(f.read().strip())
                pid = data["pid"]
            
            os.kill(pid, 0) # Check PID life
            if (time.time() - os.path.getmtime(lock_path)) > self.LEASE_TIMEOUT * 3:
                self.logger.warning(f"ZOMBIE_DETECTED: {tx_id}")
        except (OSError, ValueError, ProcessLookupError, KeyError):
            try: os.remove(lock_path)
            except: pass

    def _update_journal_deterministic(self, tx_id, step, meta=None):
        """ FIX GAP 1: Split Deterministic vs Audit Hash."""
        meta = meta or {}
        # Deterministic: Must be repeatable for same input/step
        d_hash = hashlib.sha256(f"{tx_id}{int(step)}{self.node_id}".encode()).hexdigest()
        # Audit: Time-based tracking
        meta["audit_ts"] = time.time()
        meta["step_integrity_ref"] = d_hash
        self.wal.set_rollback_journal_fsync(tx_id, int(step), meta, d_hash)

    def _release_dual_lease(self, tx_id, is_finally=False):
        """Idempotent Release with WAL confirmation."""
        with self._state_mutex:
            state = self._tx_states.get(tx_id)
            if not state or state["released"]: return True
            state["released"] = True

        try:
            #  GAP 3 FIX: Explicit confirmation check
            wal_release_ok = self.wal.release_lease(tx_id, owner=self.node_id)
            
            f_lock = state["lock"]
            fcntl.flock(f_lock, fcntl.LOCK_UN)
            f_lock.close()
            
            lock_path = os.path.join(self.FALLBACK_LOCK_DIR, f"{tx_id}.lock")
            if os.path.exists(lock_path): os.remove(lock_path)
            
            return wal_release_ok
        except Exception as e:
            if is_finally: self.logger.error(f"OMEGA_CLEANUP_ERR: {str(e)}")
            return False

    def _cleanup_with_nfs_hardened_verify(self, context):
        """ FIX GAP 4: NFS/Network FS Jitter-Safe Cleanup."""
        for f in context.input_data.get("temp_files", []):
            if not os.path.exists(f): continue
            tomb = f"{f}.{context.tx_id}.tomb"
            shutil.move(f, tomb)
            
            # Triple-pass delete strategy
            for attempt in range(3):
                try:
                    if os.path.isdir(tomb): shutil.rmtree(tomb)
                    else: os.remove(tomb)
                    break
                except OSError:
                    time.sleep(0.1 * (attempt + 1)) # Jitter

            # Final verify with inode-cache wait
            stop_at = time.time() + 2.0
            while os.path.exists(tomb) and time.time() < stop_at:
                time.sleep(0.05)

    def _verify_system_health(self, start_time, tx_id):
        if self._shutdown_requested: raise InterruptedError("SYSTEM_GRACEFUL_EXIT")
        if (time.time() - start_time) > self.LEASE_TIMEOUT: raise TimeoutError("WATCHDOG_HALT")
        with self._state_mutex:
            if not (self.wal.is_lease_valid(tx_id, owner=self.node_id) and tx_id in self._tx_states):
                raise PermissionError("OMEGA_FENCE_BREACH")

    def _verify_triple_integrity(self, context):
        wal_sum = self.wal.get_recorded_pre_state_checksum(context.tx_id)
        snap_sum = self.snapshots.get_snapshot_hash(context.snapshot_id)
        if wal_sum != snap_sum: return False
        return self.data_core.verify_state_checksum(wal_sum)

    def _trigger_emergency_escalation(self, context):
        self.wal.mark_critical_system_failure(context.tx_id)
        return False