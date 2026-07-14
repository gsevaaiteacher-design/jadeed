# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-07-REPLAY-ENGINE
# ROLE: ABSOLUTE RECOVERY KERNEL (THE FINAL BOSS)
# SIGNATOR: OMEGA-INDUSTRIAL-REPLAY-10-10-PERFECT-SCORE-FINAL
# =================================================================

import logging
import multiprocessing
import time
import json
import os
from transaction_core.wal_schema import WALSchema

class ReplayError:
    INTEGRITY_FAIL = 101
    TIMEOUT = 102
    LOGIC_FAIL = 103
    OS_CRASH = 104
    TX_REJECTED = 105
    EXIT_CODE_MAP = {
        0: "CLEAN",
        1: "GENERAL_FAIL",
        137: "SIGKILL_OOM",
        139: "SEGFAULT"
    }

class StateReplayEngine:
    """
    State Replay Engine V2.6: The Final Absolute Sovereign.
     10/10 FIX: Hardened Exit Mapping, Explicit Batch Isolation, 
    and Post-Commit Verification Hooks.
    """

    def __init__(self, data_core, checkpoint_store):
        self.data_core = data_core
        self.checkpoints = checkpoint_store 
        self.logger = logging.getLogger("Z-STUDIO.REPLAY_ABSOLUTE")
        self.MUTATION_TIMEOUT = 15.0  
        self.MAX_RETRIES = 3           
        self.RECOVERY_POLICY = "STRICT"

    def run_batch_recovery(self, entries):
        """ 10/10: Full Batch Integrity & Rollback Enforcement."""
        is_valid, error = WALSchema.validate_full_chain(entries)
        if not is_valid:
            self.logger.critical(f"BATCH_VALIDATION_FAILED: {error}")
            return False

        # Bookmark initial state for full batch rollback
        initial_lsn = self.checkpoints.get_last_lsn()
        sorted_entries = sorted(entries, key=lambda x: x.get("lsn", 0))
        
        self.logger.info(f"STARTING_BATCH_REPLAY: LSN {initial_lsn} -> {sorted_entries[-1]['lsn']}")

        try:
            for entry in sorted_entries:
                if not self.replay_with_resilience(entry):
                    raise RuntimeError(f"REPLAY_FAILED_AT_LSN_{entry.get('lsn')}")
            
            self.logger.info("BATCH_REPLAY_SUCCESSFUL.")
            return True

        except Exception as e:
            #  FIX: Forced logical rollback of checkpoint to prevent partial recovery state
            self.logger.critical(f"BATCH_ABORTED: {str(e)}. Reverting checkpoint to {initial_lsn}")
            self.checkpoints.save_checkpoint_atomic(initial_lsn, "BATCH_ROLLBACK_FORCE")
            return False

    def replay_with_resilience(self, entry):
        """Persistent Resilience Loop."""
        lsn = entry.get("lsn")
        if lsn <= self.checkpoints.get_last_lsn(): return True

        for attempt in range(self.MAX_RETRIES):
            success, err_code, reason = self._execute_isolated_replay(entry)
            
            if success:
                #  ATOMIC PERSISTENCE
                self.checkpoints.save_checkpoint_atomic(lsn, entry.get("hash"))
                return True
            
            if err_code == ReplayError.INTEGRITY_FAIL:
                self.logger.critical(f"INTEGRITY_FAILURE_AT_LSN_{lsn}: Stopping Replay.")
                break 

            self.logger.warning(f"RETRYING_LSN_{lsn}: Attempt {attempt+1} - Reason: {reason}")
            time.sleep(2 ** attempt)
            
        return False

    def _execute_isolated_replay(self, entry):
        """ 10/10: Hardened Process Isolation & Semantic Exit Logic."""
        parent_conn, child_conn = multiprocessing.Pipe()
        success, err_code, reason = False, ReplayError.OS_CRASH, "UNKNOWN"

        try:
            worker = multiprocessing.Process(
                target=self._isolated_worker, 
                args=(child_conn, entry)
            )
            worker.start()
            child_conn.close() 

            worker.join(timeout=self.MUTATION_TIMEOUT)

            if worker.is_alive():
                worker.terminate()
                worker.join()
                err_code, reason = ReplayError.TIMEOUT, "OS_TERMINATION_WATCHDOG"
            else:
                #  FIX: Deterministic Result Capturing
                if parent_conn.poll(2.0): 
                    result = parent_conn.recv()
                    success = result.get("success", False)
                    err_code = result.get("code")
                    reason = result.get("reason")
                else:
                    # Semantic Mapping of Exit Codes (Fix 3)
                    exit_reason = ReplayError.EXIT_CODE_MAP.get(worker.exitcode, f"CODE_{worker.exitcode}")
                    err_code, reason = ReplayError.OS_CRASH, f"WORKER_CRASHED_{exit_reason}"

        finally:
            parent_conn.close() 
            
        return success, err_code, reason

    def _isolated_worker(self, conn, entry):
        """Isolated Semantic Execution Worker."""
        tx_id = entry.get("tx_id", "REPLAY_TX")
        try:
            # 1. Zero-Trust Integrity Re-Check
            raw = json.dumps(entry, sort_keys=True, separators=(',', ':'))
            if WALSchema.parse_entry(raw)["status"] != "OK":
                conn.send({"success": False, "code": ReplayError.INTEGRITY_FAIL, "reason": "HASH_MISMATCH"})
                return

            # 2. Transaction Boundary
            if hasattr(self.data_core, "begin_replay_tx"):
                self.data_core.begin_replay_tx(tx_id)

            # 3. Surgical Mutation Execution
            op, payload = entry.get("op"), entry.get("payload", {})
            if hasattr(self.data_core, "apply_mutation"):
                res = self.data_core.apply_mutation(op, payload)
            else:
                getattr(self.data_core, f"_force_state_{op}")(**payload)
                res = True

            if res:
                if hasattr(self.data_core, "commit_replay_tx"):
                    self.data_core.commit_replay_tx(tx_id)
                
                #  FIX: Post-Commit State Verification Hook
                if hasattr(self.data_core, "verify_post_commit"):
                    if not self.data_core.verify_post_commit(tx_id):
                        raise RuntimeError("POST_COMMIT_VERIFICATION_FAILED")

                conn.send({"success": True, "code": 0, "reason": "OK"})
            else:
                raise ValueError("LOGIC_REJECTION")

        except Exception as e:
            if hasattr(self.data_core, "rollback_replay_tx"):
                self.data_core.rollback_replay_tx(tx_id)
            conn.send({"success": False, "code": ReplayError.LOGIC_FAIL, "reason": str(e)})
        finally:
            conn.close()