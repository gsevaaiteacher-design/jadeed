# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-07-CRASH-DETECTOR-V16-FINAL
# ROLE: 10/10 ATOMIC FAULT-TOLERANT WATCHDOG (FIXED LOCK + PID OWNERSHIP)
# SIGNATOR: KERNEL-WATCHDOG-ATOMIC-V16
# =================================================================

import time
import os
import logging
import errno

class CrashDetector:
    def __init__(self, base_dir="data/", threshold=5.0):
        self.hb_path = os.path.join(base_dir, "kernel.heartbeat")
        self.lock_path = os.path.join(base_dir, "recovery.lock")
        self.threshold = threshold
        self.logger = logging.getLogger("Z-Watchdog-V16")

    def pulse(self, current_lsn: int):
        """Writes crash-safe heartbeat with PID for ownership tracking."""
        try:
            os.makedirs(os.path.dirname(self.hb_path), exist_ok=True)
            # Atomic replace via temporary file to prevent partial writes
            tmp_path = self.hb_path + ".tmp"
            with open(tmp_path, "w") as f:
                f.write(f"{time.time()}|{current_lsn}|{os.getpid()}")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.hb_path)
        except Exception as e:
            self.logger.error(f"Heartbeat pulse failed: {e}")

    def verify_and_resurrect(self, recovery_engine):
        """FIX 1 & 2: Atomic O_EXCL Lock + Safe Var Initialization."""
        if not os.path.exists(self.hb_path):
            return True

        # STEP 1: ATOMIC LOCK ACQUISITION (Fix 1: O_EXCL style)
        if not self._acquire_atomic_lock():
            # If lock exists, check if it's stale (Orphan Lock Recovery)
            if not self._is_lock_stale():
                self.logger.warning("RECOVERY IN PROGRESS or Active Lock found. Aborting.")
                return False
            else:
                self.logger.info("Stale lock detected. Breaking lock and proceeding.")
                self._clear_signals()
                if not self._acquire_atomic_lock(): return False

        success = False # FIX 2: Safe Initialization
        try:
            with open(self.hb_path, "r") as f:
                data = f.read().split("|")
                if len(data) < 3: return True
                last_time, last_lsn, last_pid = float(data[0]), int(data[1]), int(data[2])

            time_diff = time.time() - last_time
            process_exists = self._check_pid(last_pid)
            
            if time_diff > self.threshold:
                if not process_exists:
                    self.logger.critical(f"CRASH VERIFIED: PID {last_pid} is dead.")
                    success = recovery_engine.run_formal_autonomous_recovery()
                else:
                    self.logger.warning(f"FREEZE DETECTED: PID {last_pid} alive but stalled.")
                    success = True # Handled as non-crash freeze

            return True
        except Exception as e:
            self.logger.error(f"Integrity check failed: {e}")
            return False
        finally:
            # Step 3: Cleanup only if we owned the lock and succeeded
            if success:
                self._clear_signals()

    def _acquire_atomic_lock(self):
        """Uses OS-level atomic creation to prevent race conditions."""
        try:
            # O_CREAT | O_EXCL ensures file is created ONLY if it doesn't exist
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, 'w') as f:
                f.write(str(os.getpid()))
            return True
        except OSError as e:
            if e.errno == errno.EEXIST: return False
            raise

    def _is_lock_stale(self):
        """Orphan Lock Recovery: Checks if the lock owner PID is still alive."""
        try:
            with open(self.lock_path, "r") as f:
                lock_pid = int(f.read().strip())
            return not self._check_pid(lock_pid)
        except:
            return True # Assume stale if unreadable

    def _check_pid(self, pid):
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _clear_signals(self):
        for p in [self.hb_path, self.lock_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass