"""
Z-STUDIO V12.3  SYSTEM CORE (HEALTH ENGINE - HARDENED)
Module: Health Core
Role: Real-time hardware diagnostics with stabilized baseline.
"""

import psutil
import torch
import time
import threading
import logging # Internal standard for logger_core (File 12) compatibility

class HealthCore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'): return
        
        self.active = True
        self.health_metrics = {
            "cpu_usage": 0.0,
            "ram_usage": 0.0,
            "vram_usage": 0.0,
            "system_status": "BOOTING",
            "stress_score": 0.0
        }
        
        # Performance Thresholds
        self.CRITICAL_THRESHOLD = 92.0
        self.WARNING_THRESHOLD = 80.0
        
        # FIX (A): CPU Warm-up (Baseline stabilization)
        psutil.cpu_percent(interval=None) 
        
        # Start Background Pulse
        self.monitor_thread = threading.Thread(target=self._pulse_engine, daemon=True)
        self.monitor_thread.start()
        
        self._initialized = True
        print("[HEALTH_CORE] MONITORING HARDENED. SYSTEM STABLE.")

    def _pulse_engine(self):
        """Internal daemon with stabilized metrics and error visibility."""
        while self.active:
            try:
                # 1. CPU & RAM (Stabilized)
                self.health_metrics["cpu_usage"] = psutil.cpu_percent(interval=None)
                self.health_metrics["ram_usage"] = psutil.virtual_memory().percent
                
                # 2. GPU VRAM tracking (Multi-device aware aggregation)
                if torch.cuda.is_available():
                    total_allocated = 0
                    total_capacity = 0
                    for i in range(torch.cuda.device_count()):
                        total_allocated += torch.cuda.memory_allocated(i)
                        total_capacity += torch.cuda.get_device_properties(i).total_memory
                    
                    self.health_metrics["vram_usage"] = (total_allocated / total_capacity) * 100
                
                # 3. Stress Score (0.5 VRAM + 0.3 RAM + 0.2 CPU)
                self.health_metrics["stress_score"] = (
                    (self.health_metrics["vram_usage"] * 0.5) +
                    (self.health_metrics["ram_usage"] * 0.3) +
                    (self.health_metrics["cpu_usage"] * 0.2)
                )
                
                self._evaluate_status()
                
            except Exception as e:
                # FIX (C): Log exception for internal diagnostics (File 12 bridge)
                self.health_metrics["system_status"] = "DIAGNOSTIC_ERR"
                # In production, this would bridge to logger_core
                print(f"[HEALTH_CORE_CRITICAL] Internal Error: {str(e)}")
            
            time.sleep(1.0)

    def _evaluate_status(self):
        score = self.health_metrics["stress_score"]
        if score > self.CRITICAL_THRESHOLD:
            self.health_metrics["system_status"] = "CRITICAL"
        elif score > self.WARNING_THRESHOLD:
            self.health_metrics["system_status"] = "WARNING"
        else:
            self.health_metrics["system_status"] = "STABLE"

    def get_vitals(self):
        return self.health_metrics

    def is_safe_to_execute(self):
        """Safety gate for execution_orchestrator.py"""
        return self.health_metrics["system_status"] != "CRITICAL"

    def shutdown(self):
        self.active = False
        print("[HEALTH_CORE] STOPPED.")

# Global Hook
system_health = HealthCore()
