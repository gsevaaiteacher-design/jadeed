"""
Z-STUDIO V15.2  RUNTIME API (CONTROL LAYER)
Author/Brand: ZYNQUAR ATELIER
Module: resource_adapter.py
Role: SENTRY-ELITE (Zero-Stale Metrics & Clean Thread Lifecycle).
"""

import psutil
import os
import threading
import time
from typing import Dict, Any

try:
    from logger_core import logger
except ImportError:
    import logging
    logger = logging.getLogger("Z_RESOURCE_ADAPTER")

class ZStudioResourceAdapter:
    def __init__(self):
        self._state_lock = threading.Lock()
        self._cached_stats = {}
        self._is_running = True
        self.CPU_LIMIT = 90.0
        self.RAM_LIMIT = 85.0
        
        self._monitor_thread = threading.Thread(target=self._background_poll, name="ZQ_SENTRY", daemon=True)
        self._monitor_thread.start()
        
        logger.info("[ZYNQUAR] RESOURCE_ADAPTER 10/10 ACTIVE.")

    def _background_poll(self):
        """ Optimized Polling Loop (Hooked to Control Bus)."""
        try:
            #  HOOK: Accessing Global Bus
            from system_core.control_bus import ControlBus
            control_bus = ControlBus()
            
            process = psutil.Process(os.getpid())
            psutil.cpu_percent(interval=None) 
            
            while self._is_running:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                app_mem = process.memory_info().rss / (1024**2)
                is_healthy = cpu < self.CPU_LIMIT and mem.percent < self.RAM_LIMIT

                with self._state_lock:
                    self._cached_stats = {
                        "cpu_load": cpu,
                        "ram_percent": mem.percent,
                        "ram_used_gb": round(mem.used / (1024**3), 2),
                        "ram_total_gb": round(mem.total / (1024**3), 2),
                        "app_footprint_mb": round(app_mem, 2),
                        "timestamp": time.time(),
                        "healthy": is_healthy
                    }
                
                #  CRITICAL HOOK: Trigger Alert to Master Bus
                if not is_healthy:
                    control_bus.publish("SYSTEM_ALERT", {
                        "source": "RESOURCE_ADAPTER",
                        "status": "CRITICAL",
                        "vitals": self._cached_stats
                    })
                
                time.sleep(2) 
        except Exception as e:
            logger.error(f"[ADAPTER] SENTRY_FATAL_ERROR: {str(e)}")

    def get_system_vitals(self) -> Dict[str, Any]:
        with self._state_lock:
            return self._cached_stats or {"status": "WARMING_UP"}

    def check_safety_limit(self) -> bool:
        stats = self.get_system_vitals()
        return stats.get("healthy", False)

    def get_gpu_vitals(self) -> Dict[str, Any]:
        return {"gpu_status": "MONITORED_BY_AI_ENGINE"}

    def get_health_report(self) -> Dict[str, Any]:
        stats = self.get_system_vitals()
        cpu = stats.get("cpu_load", 0)
        ram = stats.get("ram_percent", 0)
        stability = 100 - (max(cpu, ram))
        return {
            "status": "STABLE" if stats.get("healthy") else "STRESSED",
            "stability_score": f"{round(stability, 1)}%",
            "vitals": stats
        }

    def shutdown(self):
        self._is_running = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        logger.info("[ADAPTER] SENTRY COLD.")

resource_adapter = ZStudioResourceAdapter()