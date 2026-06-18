"""
Z-STUDIO V12.3  SYSTEM BRAIN LAYER
MODULE: RESOURCE GUARD (FIXED)
ROLE: HARDWARE SAFETY + MEMORY + CPU/GPU STABILITY GATE
"""

import threading
import time
from typing import Dict, Any

# -------------------------
# SAFE PSUTIL IMPORT
# -------------------------
try:
    import psutil
except ImportError:
    psutil = None


class ResourceGuard:
    """
     SYSTEM SAFETY LAYER (FIXED PRODUCTION VERSION)

    RESPONSIBILITY:
    - RAM monitoring
    - CPU monitoring
    - system overload protection
    - safe model execution gating
    """

    def __init__(self):
        self._lock = threading.RLock()

        if psutil:
            psutil.cpu_percent(interval=None)

        # thresholds
        self.max_ram_percent = 85
        self.max_cpu_percent = 90
        self.critical_ram_percent = 92
        self.critical_cpu_percent = 95

        # state tracking
        self.last_status: Dict[str, Any] = {}
        self.blocked_state = False

    # ---------------------------
    # SYSTEM SNAPSHOT
    # ---------------------------
    def system_health(self) -> Dict[str, Any]:
        with self._lock:

            if psutil is None:
                status = {
                    "ram": 0,
                    "cpu": 0,
                    "blocked": False,
                    "timestamp": time.time()
                }
                self.last_status = status
                return status

            ram = psutil.virtual_memory().percent

            # NON-BLOCKING CPU READ (FIXED)
            cpu = psutil.cpu_percent(interval=None)

            status = {
                "ram": ram,
                "cpu": cpu,
                "blocked": self.blocked_state,
                "timestamp": time.time()
            }

            self.last_status = status
            return status

    # ---------------------------
    # EXECUTION GATE
    # ---------------------------
    def allow_execution(self, workload_type: str = "general") -> bool:
        status = self.system_health()

        ram = status["ram"]
        cpu = status["cpu"]

        with self._lock:
            if ram >= self.critical_ram_percent or cpu >= self.critical_cpu_percent:
                self.blocked_state = True
                return False

            if ram >= self.max_ram_percent or cpu >= self.max_cpu_percent:
                self.blocked_state = False
                return False

            self.blocked_state = False
            return True

    # ---------------------------
    # LOAD ESTIMATION (FIXED)
    # ---------------------------
    def estimate_load(
        self,
        model_size_mb: int,
        active_models: int = 1,
        status: Dict[str, Any] = None
    ) -> bool:

        if status is None:
            status = self.system_health()

        ram = status["ram"]

        # safe projection
        projected_ram = ram + (model_size_mb / 1024) * 2

        return not (
            projected_ram > self.critical_ram_percent
            or projected_ram > self.max_ram_percent
        )

    # ---------------------------
    # EMERGENCY STOP
    # ---------------------------
    def emergency_stop(self) -> bool:
        status = self.system_health()

        if status["ram"] > 95 or status["cpu"] > 98:
            with self._lock:
                self.blocked_state = True
            return True

        return False

    # ---------------------------
    # DEBUG REPORT
    # ---------------------------
    def debug_report(self) -> Dict[str, Any]:
        status = self.system_health()

        return {
            "resource_status": status,
            "max_ram_limit": self.max_ram_percent,
            "max_cpu_limit": self.max_cpu_percent,
            "critical_ram_limit": self.critical_ram_percent,
            "critical_cpu_limit": self.critical_cpu_percent,
            "blocked_state": self.blocked_state
        }