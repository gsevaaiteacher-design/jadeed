# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-01-ATOMIC
# ROLE: INDUSTRIAL FAST-PATH EXECUTION GATEWAY (V12.FINAL)
# SIGNATOR: OMEGA-INDUSTRIAL-FAST-PATH-KERNEL-SEAL
# =================================================================

import copy
import threading
import uuid
import logging

class AtomicEngine:
    def __init__(self, data_core, allowed_ops):
        if not allowed_ops:
            raise ValueError("allowed_ops must be explicitly defined")
            
        self.data_core = data_core
        self.allowed_ops = set(allowed_ops)
        self._exec_lock = threading.Lock() 
        self.logger = logging.getLogger("Z-STUDIO.ATOMIC")
        
        #  THREAD-LOCAL & REGISTRY
        self._local = threading.local()
        self._active_threads = set() 

    def get_active_threads(self):
        """ Watchdog: Returns a list of all currently alive execution threads."""
        return [t for t in self._active_threads if t.is_alive()]

    def active_count(self):
        """ FIX 2: Useful metric for monitoring execution pressure."""
        return len(self.get_active_threads())

    def has_zombie_threads(self):
        """ Returns True if any timed-out threads are still running in background."""
        return any(t.is_alive() for t in self._active_threads)

    def get_current_state(self):
        """ Isolation: Deepcopy is the mechanical necessity for snapshot safety."""
        return copy.deepcopy(self.data_core.export_state())

    def restore_state(self, state_dict):
        """Restores the data_core to a previous known-good state."""
        if not isinstance(state_dict, dict):
            raise ValueError("INVALID_SNAPSHOT_STATE")
        self.data_core.import_state(state_dict)

    def _validate_input(self, op, data):
        """Strict validation against operation schemas to prevent silent corruption."""
        schema = getattr(self.data_core, f"{op}_schema", None)
        if schema:
            for key, typ in schema.items():
                if key not in data: raise ValueError(f"MISSING: {key}")
                if not isinstance(data[key], typ): raise TypeError(f"TYPE_ERR: {key}")
            for key in data:
                if key not in schema: raise ValueError(f"UNEXPECTED: {key}")

    def _execute_internal(self, context, exec_id):
        #  MID-EXECUTION SAFETY GATE: Stop if system flipped while waiting for lock
        if hasattr(self.data_core, "is_unstable") and self.data_core.is_unstable():
            raise RuntimeError(f"ABORTED: System unstable at execution start {exec_id}")

        op = context.operation_name
        data = context.input_data or {}
        self._local.exec_id = exec_id 
        
        if not isinstance(data, dict): raise TypeError("INPUT_NOT_DICT")
        if op not in self.allowed_ops: raise PermissionError(f"FORBIDDEN: {op}")
        if not hasattr(self.data_core, op): raise AttributeError(f"NOT_FOUND: {op}")

        self._validate_input(op, data)
        func = getattr(self.data_core, op)
        return func(**data)

    def execute(self, context, timeout=None):
        """
         INDUSTRIAL FAST-PATH: High-performance execution gateway.
         TRUTH: Python threads are non-terminable. Timeout only unblocks the caller.
        """
        #  PRE-EXECUTION CIRCUIT BREAKER
        if hasattr(self.data_core, "is_unstable") and self.data_core.is_unstable():
            raise RuntimeError("SYSTEM_LOCKED: Instability detected. Execution blocked.")

        result_container = {}
        exec_id = str(uuid.uuid4())

        def target():
            try:
                with self._exec_lock:
                    result_container["result"] = self._execute_internal(context, exec_id)
            except Exception as e:
                result_container["error"] = e
            finally:
                self._local.exec_id = None

        t = threading.Thread(target=target, daemon=True)
        self._active_threads.add(t) 
        
        try:
            t.start()
            t.join(timeout)

            if t.is_alive():
                #  FIX 1: CRITICAL LOGGING for Zombie visibility
                error_msg = f"CRITICAL: ZOMBIE_THREAD_ACTIVE | ID: {exec_id} | OP: {context.operation_name}"
                self.logger.critical(error_msg) 
                
                if hasattr(self.data_core, "mark_unstable"):
                    self.data_core.mark_unstable() # Trigger System-Wide Block
                
                raise TimeoutError(error_msg)

            if "error" in result_container:
                raise RuntimeError(f"FAILED: {str(result_container['error'])}") from result_container["error"]

            return result_container.get("result")
        finally:
            self._active_threads.discard(t)