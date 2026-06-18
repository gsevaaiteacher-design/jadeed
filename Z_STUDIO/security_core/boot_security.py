"""
ROLE: 6/9 - BOOT SECURITY (MASTER ORCHESTRATOR)
VERSION: 2.7.0 (DIAMOND STABLE  ORDERED AUDIT & PERFORMANCE)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
-----------------------------------------------------------------------
STRICT DOMAIN: Fault-Tolerant Orchestration, Performance Metrics, Ordered Audit.
-----------------------------------------------------------------------
"""
import os, sys, time, importlib, threading, json

class ZStudioBootSecurity:
    def __init__(self):
        #  ZYNQUAR BRANDING
        self.SIGNATURE = "ZYNQUAR ATELIER  OMNI-DIAMOND CORE"
        self.PROJECT = "Z-STUDIO V8 (ULTIMATE)"
        self.BOOT_VER = "2.7.0"

        self._lock = threading.Lock()
        self.boot_health_score = 100
        self.telemetry_log = []
        self.session_id = time.strftime("%Y%m%d_%H%M%S")
        self.log_file = f"audit/boot_{self.session_id}.json"
        self._ensure_audit_dir()

        #  EXECUTION CHAIN (LOCKED BLUEPRINT)
        self.execution_chain = [
            {"name": "license_engine",    "code": 0x21, "w": 15, "critical": True},
            {"name": "hwid_lock",         "code": 0x22, "w": 15, "critical": True},
            {"name": "integrity_checker", "code": 0x23, "w": 10, "critical": True},
            {"name": "tamper_protection", "code": 0x24, "w": 10, "critical": True},
            {"name": "isolation_kernel",  "code": 0x31, "w": 5,  "critical": False},
            {"name": "sandbox_engine",    "code": 0x32, "w": 5,  "critical": False},
            {"name": "syscall_monitor",   "code": 0x33, "w": 5,  "critical": False}
        ]
        #  FIX: Ordered list with duplicate protection for audit clarity
        self.active_modules = []

    def initiate_secure_boot(self):
        """Triggers the Hardened Performance-Aware Security Chain."""
        boot_start = time.time()
        self._log("BOOT_INIT", {"ver": self.BOOT_VER, "sid": self.session_id})
        print(f"\n{'='*60}\n  {self.PROJECT} | {self.SIGNATURE}\n{'='*60}")

        if not self._validate_env():
            return self._safe_fail("ENVIRONMENT_REJECTION", 0x10)

        for module in self.execution_chain:
            m_name, m_code, m_w, is_critical = module["name"], module["code"], module["w"], module["critical"]
            
            success, attempt, diag, m_lat = False, 0, "PENDING", 0
            while attempt < 3 and not success:
                #  FIX: Performance/Latency Tracking
                m_start = time.time()
                success, diag = self._launch_module(m_name)
                m_lat = round((time.time() - m_start) * 1000, 2)
                
                if not success:
                    attempt += 1
                    penalty = (m_w // 2) if is_critical else (m_w // 4)
                    self.boot_health_score = max(0, self.boot_health_score - penalty)
                    self._log("MODULE_RETRY", {"mod": m_name, "diag": diag, "attempt": attempt, "lat_ms": m_lat})
                    time.sleep(min(1.5 ** attempt, 10))
                else:
                    if m_name not in self.active_modules:
                        self.active_modules.append(m_name)
                    self._log("MODULE_SUCCESS", {"mod": m_name, "lat_ms": m_lat, "h": self.boot_health_score})
                    break

            self._persist() # Incremental Save

            if not success:
                if is_critical:
                    return self._safe_fail(f"CRITICAL_FAIL: {m_name.upper()} | {diag}", m_code)
                else:
                    self.boot_health_score = max(0, self.boot_health_score - m_w)
                    print(f"[WARN] {m_name.upper():<20} | FAILED ({m_lat}ms) | CONTINUING...")
                    self._log("DEGRADED_CONTINUE", {"mod": m_name, "diag": diag})
                    continue

            print(f"[+] {m_name.upper():<20} | {m_lat:>7}ms | HEALTH: {self.boot_health_score}%")

        return self._success(boot_start)

    def _launch_module(self, name):
        """Strict Blueprint Loader with Strict Boolean Check."""
        try:
            path = f"security_core.{name}"
            if path in sys.modules: del sys.modules[path]
            mod = importlib.import_module(path)
            instance = mod.get_instance()
            
            if hasattr(instance, "initialize"):
                res = instance.initialize()
                #  FIX: Strict Boolean Enforcement (No truthy/string bypass)
                if res is True:
                    return True, "OK"
                return False, f"INIT_RETURNED_{type(res).__name__}"
            return False, "METHOD_MISSING"
        except Exception as e:
            return False, f"CRASH_{type(e).__name__}"

    def _validate_env(self):
        cwd = os.getcwd().upper()
        return not any(f in cwd for f in ["TEMP", "DOWNLOADS", "DESKTOP", "RECYCLE.BIN"])

    def _ensure_audit_dir(self):
        if not os.path.exists("audit"): os.makedirs("audit")

    def _log(self, event, data):
        with self._lock:
            self.telemetry_log.append({"ts": time.strftime("%H:%M:%S"), "ev": event, "data": data})

    def _persist(self):
        try:
            with self._lock:
                with open(self.log_file, "w") as f:
                    json.dump({"session": self.session_id, "logs": self.telemetry_log}, f, indent=4)
        except Exception:
            print("[!] AUDIT_WRITE_ERROR: Disk Busy or Restricted.")

    def _safe_fail(self, reason, code):
        self._log("FATAL_STOP", {"reason": reason, "code": hex(code)})
        self._persist()
        print(f"\n[!] FATAL: {reason} | ERROR: {hex(code)}")
        time.sleep(1)
        os._exit(code)

    def _success(self, start_time):
        total_time = round(time.time() - start_time, 2)
        state = {
            "status": "OPTIMAL" if self.boot_health_score > 90 else "DEGRADED",
            "health": self.boot_health_score,
            "duration_sec": total_time,
            "chain": self.active_modules
        }
        self._log("BOOT_COMPLETE", state)
        self._persist()
        print(f"\n[***] BOOT SUCCESS IN {total_time}s | STATE: {state['status']}")
        return state

# Global Access
boot_security = ZStudioBootSecurity()