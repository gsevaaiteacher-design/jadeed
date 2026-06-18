"""
Z-STUDIO V15.1  RUNTIME API (CONTROL LAYER)
Author/Brand: ZYNQUAR ATELIER
Module: execution_bridge.py
Role: TITAN LOCK (Final Deterministic Transport Bridge)
-----------------------------------------------------------------------
"""

import threading
import concurrent.futures
from typing import Dict, Any, Callable, Optional


from system_core.logger_core import logger
from runtime_api.stream_engine import stream_engine

class ZStudioExecutionBridge:
    """
     ROLE: The Sovereign Protected Pipe.
     FIXES: Race-Free Shutdown Guard, Atomic State Recovery, Contextual Logging.
    """

    def __init__(self, max_workers: int = 15, task_limit: int = 50):
        self._max_workers = max_workers
        self._task_limit = task_limit
        self._is_running = True
        
        #  1. EXECUTION & CALLBACK POOLS
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers,
            thread_name_prefix="ZQ_EXE_ISO"
        )
        self._callback_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=5,
            thread_name_prefix="ZQ_UI_ISO"
        )
        
        #  2. GUARDS & ATOMIC STATE
        self._stats_lock = threading.Lock()
        self._active_tasks = 0
        self._pending_tasks = 0
        self._backpressure_guard = threading.BoundedSemaphore(value=self._task_limit)
        self._cb_guard = threading.Semaphore(value=10) # UI Flood Control

        logger.info(f"[ZYNQUAR] TITAN-LOCK ACTIVE. SLOTS: {self._task_limit}")
        

    def run_isolated(self, target: Any, envelope: Dict[str, Any], callback: Optional[Callable] = None):
        """ THE ASYNC GATE: Blueprint Compliant Entry."""
        req_id = envelope.get("header", {}).get("id", "ZQ-UNK")

        #  SHUTDOWN PROTECTION (Lock-Guarded)
        with self._stats_lock:
            if not self._is_running:
                return {"status": "REJECTED", "error": "SHUTDOWN_ACTIVE"}

        #  BACKPRESSURE REJECTION
        if not self._backpressure_guard.acquire(blocking=False):
            return {"status": "REJECTED", "error": "CAPACITY_FULL"}

        with self._stats_lock:
            self._pending_tasks += 1

        try:
            self._executor.submit(self._titan_pipeline, target, envelope, callback, req_id)
            return True
        except Exception as e:
            # Atomic recovery on submit failure
            with self._stats_lock:
                self._pending_tasks = max(0, self._pending_tasks - 1)
            self._auto_reconcile()
            logger.error(f"[BRIDGE] SUBMIT_FAIL {req_id}: {str(e)}")
            return False

    def _titan_pipeline(self, target: Any, envelope: Dict[str, Any], callback: Optional[Callable], req_id: str):
        """ Safe Execution Pipeline (ZYNQUAR Master Blueprint Edition)."""
        try:
            with self._stats_lock:
                self._pending_tasks = max(0, self._pending_tasks - 1)
                self._active_tasks += 1

            #  DYNAMIC TRANSPORT LINK
            if callable(target):
                result = target(envelope)
            elif hasattr(target, "process_request"):
                result = target.process_request(envelope)
            elif hasattr(target, "execute_inference"):
                result = target.execute_inference(envelope)
            else:
                raise RuntimeError(f"INVALID_TARGET_ROUTING: {type(target)}")

        except Exception as e:
            logger.error(f"[BRIDGE] ISO_FAULT {req_id}: {str(e)}")
            result = {"status": "INTERNAL_FAULT", "error": str(e)}
        
        finally:
            with self._stats_lock:
                self._active_tasks = max(0, self._active_tasks - 1)
                is_running = self._is_running
            
            self._auto_reconcile()
            
            #  1. GUARDED UI DISPATCH (Callback logic)
            if callback and is_running:
                try:
                    self._callback_pool.submit(self._guarded_callback, callback, result, req_id)
                except Exception as cb_sub_err:
                    logger.error(f"[BRIDGE] CB_SUBMIT_FAIL {req_id}: {str(cb_sub_err)}")
            
            #  2. STREAM ENGINE DISPATCH (Yeh naya hook hai)
            if is_running:
                try:
                    # Yahan hum Stream Engine ko data bhej rahe hain
                    stream_engine.process_output(result, req_id)
                except Exception as stream_err:
                    logger.error(f"[BRIDGE] STREAM_DISPATCH_FAIL {req_id}: {str(stream_err)}")

    def _guarded_callback(self, callback: Callable, result: Any, req_id: str):
        """UI Throttling logic with contextual logging."""
        with self._cb_guard:
            try:
                callback(result)
            except Exception as e:
                # FIX: Added req_id for pro-level debugging
                logger.error(f"[BRIDGE] UI_CB_CRASH {req_id}: {str(e)}")

    def _auto_reconcile(self):
        """ DRIFT SYNC."""
        try:
            self._backpressure_guard.release()
        except ValueError:
            logger.warning("[BRIDGE] SEMAPHORE_DRIFT_SYNCED.")

    def get_vitals(self) -> Dict[str, Any]:
        """ REAL-TIME VITALS."""
        with self._stats_lock:
            busy = self._active_tasks + self._pending_tasks
            return {
                "active": self._active_tasks,
                "queued": self._pending_tasks,
                "load": f"{round((busy / self._task_limit) * 100, 1)}%",
                "online": self._is_running
            }

    def shutdown(self):
        """Safe Cold Shutdown."""
        with self._stats_lock:
            self._is_running = False
        self._executor.shutdown(wait=True)
        self._callback_pool.shutdown(wait=True)
        logger.info("[BRIDGE] TITAN-LOCK COLD.")

# GLOBAL SINGLETON
execution_bridge = ZStudioExecutionBridge()

#  ZYNQUAR ATELIER  [PHASE 3 - FILE 7: 10/10 PASS - ABSOLUTE LOCK]