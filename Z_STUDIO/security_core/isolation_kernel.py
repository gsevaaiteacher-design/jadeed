"""
ROLE: 7/9 - ISOLATION KERNEL (SYSTEM BOUNDARY)
VERSION: 2.4.0 (FINAL DIAMOND  PERSISTENT & STORM-PROTECTED)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
-----------------------------------------------------------------------
STRICT DOMAIN: Adaptive System Boundary, Non-Blocking Escalation.
-----------------------------------------------------------------------
"""
import os, sys, psutil, threading, time, gc, json

class ZStudioIsolationKernel:
    def __init__(self):
        self.SIGNATURE = "ZYNQUAR ATELIER  DIAMOND ISOLATION"
        self._lock = threading.Lock()
        
        #  BOUNDARY & STATE
        self.MEM_THRESHOLD_MB = 2048.0
        self.STATE = "INACTIVE"
        self.VIOLATION_COUNT = 0
        
        #  TELEMETRY & PERSISTENCE
        self.violation_log = [] 
        self._proc = psutil.Process(os.getpid())
        self._stop_event = threading.Event()
        self._callback_active = False # Thread Storm Protection

    def initialize(self, callback_hook=None):
        """Activates 10/10 Diamond-Level Isolation."""
        try:
            self.callback = callback_hook 
            if os.name == 'nt':
                self._proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            
            # Start Watchdog
            threading.Thread(target=self._enforcement_loop, daemon=True).start()
            
            self.STATE = "STABLE"
            return True
        except:
            return False

    def _enforcement_loop(self):
        """ STAGE 7: Diamond Enforcement (Self-Healing & Persistence)."""
        while not self._stop_event.is_set():
            try:
                mem_mb = self._proc.memory_info().rss / (1024 * 1024)
                
                # Self-Healing
                if mem_mb < self.MEM_THRESHOLD_MB and self.STATE == "DEGRADED":
                    self._transition_state("STABLE", "Automatic recovery")
                
                # Boundary Breach
                if mem_mb > self.MEM_THRESHOLD_MB:
                    self._handle_violation("MEM_BREACH", f"{mem_mb:.2f} MB")
                
                # Priority Guard
                if os.name == 'nt' and self._proc.nice() != psutil.BELOW_NORMAL_PRIORITY_CLASS:
                    self._proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                    self._handle_violation("PRIORITY_TAMPER", "Reset enforced")

            except: pass
            time.sleep(5)

    def _transition_state(self, new_state, reason):
        with self._lock:
            self.STATE = new_state
            self._log_and_persist("STATE_CHANGE", f"{new_state}: {reason}")

    def _handle_violation(self, v_type, details):
        with self._lock:
            self.VIOLATION_COUNT += 1
            gc.collect() 
            
            if self.VIOLATION_COUNT > 10: self.STATE = "CRITICAL"
            elif self.VIOLATION_COUNT > 3: self.STATE = "DEGRADED"

            entry = {"ts": time.strftime("%H:%M:%S"), "type": v_type, "data": details, "state": self.STATE}
            self._log_and_persist(v_type, details)
            
            #  FIX: Thread Storm Protection (Only 1 callback thread at a time)
            if self.callback and not self._callback_active:
                threading.Thread(target=self._safe_callback, args=(entry,), daemon=True).start()

    def _safe_callback(self, entry):
        self._callback_active = True
        try: self.callback(f"ISOLATION_{self.STATE}", entry)
        except: pass
        self._callback_active = False

    def _log_and_persist(self, event, data):
        """ FIX: Persistent Audit (No data loss on restart)."""
        entry = {"t": time.time(), "ev": event, "d": data, "s": self.STATE}
        self.violation_log.append(entry)
        if len(self.violation_log) > 50: self.violation_log.pop(0)
        
        # Save to disk for forensic audit
        try:
            os.makedirs("audit", exist_ok=True)
            with open("audit/isolation_audit.json", "a") as f:
                f.write(json.dumps(entry) + "\n")
        except: pass

    def get_status(self):
        with self._lock:
            return {"state": self.STATE, "violations": self.VIOLATION_COUNT}

    def shutdown(self):
        self._stop_event.set()
        self.STATE = "INACTIVE"

def get_instance():
    return ZStudioIsolationKernel()