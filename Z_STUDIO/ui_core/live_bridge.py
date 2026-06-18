"""
ROLE: 8/11 - LIVE BRIDGE (BACKEND-TO-UI STATE SYNCHRONIZER)
VERSION: 1.5.0 (STATE-MERGE FIX + HARDENED STABILITY)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
"""

import threading
import time
import hashlib  #  FIX: Isse loop se bahar yahan dalo
from PySide6.QtCore import QObject, Signal, Slot
#from ui_core.event_bus_ui import get_event_bus
#from control_bus import get_event_bus




class ZStudioLiveBridge(QObject):
    """
    THE DATA VALVE:
    Safe high-frequency pipeline between backend  UI renderer.
    """
    # =========================
    # SIGNALS (UI CONSUMERS)
    # =========================
    log_received = Signal(str, str)
    state_updated = Signal(dict)
    stream_chunk = Signal(str)
    monitor_stats = Signal(dict)

    def __init__(self, bus=None):
        super().__init__()

        # 1. State Guard (Double initialization se bachne ke liye)
        if getattr(self, '_initialized', False):
            return
        self._initialized = True

        # 2. Basic Setup
        self._emitting = False
        self._in_handler = False
        self._bridge_ready = False
        self.execution_manager = None

        # 3. Performance / Throttle setup
        self._lock = threading.RLock()
        self._min_interval = 0.016
        self._state_cache = {}
        self._last_state_str = ""
        self._last_state_emit = 0.0
        self._last_metrics_emit = 0.0
        self._adaptive_interval = {"low": 0.016, "medium": 0.05, "high": 0.1}

        # 4. Bus Injection (Optional)
        self.bus = None
        if bus is not None:
            self.set_bus(bus)


    def set_bus(self, bus):
        """Launcher isse call karke bus inject karega."""
        if self.bus is None and bus is not None:
            self.bus = bus
            print(f"[ENGINEERING_SUCCESS] Bridge force-linked to Bus ID: {id(self.bus)}")
            self._wire_subscriptions()


    def _wire_subscriptions(self):
        #  WIRING
        try:
            self.bus.subscribe("RUNTIME_READY", self._handle_runtime_ready)
            self.bus.subscribe("EXECUTION_DONE", self._handle_execution_done)
            self.bus.subscribe("EXECUTION_PROGRESS", self._handle_execution_progress)
            self.bus.subscribe("TASK_STATUS", self._handle_task_status)
            self.bus.subscribe("ENGINE_LOADED_SIGNAL", self._handle_engine_loaded)
            self.bus.subscribe("SYSTEM_STARTED", self._handle_runtime_ready)
           # self.bus.subscribe("inference", self._handle_inference_response)
            self._bridge_ready = True 
            print("[ENGINEERING_SUCCESS] Bridge Subscriptions Wired.")
        except Exception as e:
            print(f"[LIVE_BRIDGE] WIRING_FAIL: {e}")
            self._bridge_ready = False

    # =========================
    # LOG PIPE (UNTHROTTLED)
    # =========================
    @Slot(str, str)
    def pipe_log(self, message, level="INFO"):
        self._safe_emit(self.log_received, message, level)

    # =========================
    #  FIXED STATE PIPE (MERGE ENGINE WITH RECURSION GUARD)
    # =========================
    @Slot(dict)
    def pipe_state(self, state_data):
        """
        DASHBOARD UPDATE ENGINE:
        Filters noise, prevents UI flicker, and merges data with thread safety.
        """
        #  LOOP BREAK: Agar pehle se hi emission chal rahi hai toh yahin rok do
        if getattr(self, "_emitting", False):
            return  

        if not isinstance(state_data, dict):
            return

        try:
            self._emitting = True # Gate band karo

            with self._lock:
                # Update Cache
                for k, v in state_data.items():
                    if v is None:
                        continue
                    if isinstance(v, (dict, list, str, int, float, bool)):
                        self._state_cache[k] = v

                # Generate Digital Fingerprint
                state_string = str(sorted(self._state_cache.items())).encode()
                state_signature = hashlib.md5(state_string).hexdigest()

                # Anti-Spam Check
                if state_signature == self._last_state_str:
                    return

                self._last_state_str = state_signature

            # Final Dispatch to UI
            self._safe_emit(
                self.state_updated,
                dict(self._state_cache),
                throttled=True,
                channel="state"
            )

        finally:
            self._emitting = False # Kaam khatam hone par gate wapas kholo


    
    # =========================
    # STREAM PIPE (AI OUTPUT)
    # =========================
    @Slot(str)
    def pipe_stream(self, chunk):
        print(f"[UI_PIPE_DEBUG] Sending to UI: {chunk}")
        #  FIX: EMPTY / NONE / TYPE SAFETY
        if not chunk:
            return
        if not isinstance(chunk, str):
            chunk = str(chunk)
        self._safe_emit(self.stream_chunk, chunk)

    # =========================
    # METRICS PIPE (SYSTEM MONITOR)
    # =========================
    @Slot(dict)
    def pipe_metrics(self, stats):
        self._safe_emit(
            self.monitor_stats,
            stats,
            throttled=True,
            channel="metrics"
        )

    # =========================
    # CORE EMISSION ENGINE
    # =========================
    def _safe_emit(self, signal, *args, throttled=False, channel=None):
        """
         CORE EMISSION ENGINE (V8 HARDENED)
        Logic: Performance throttling + Critical Message Bypass.
        """
        with self._lock:
            now = time.time()
            
            # 1. SMART CRITICAL CHECK: 
            # Agar output mein 'success' ya 'error' hai, toh use throttle MAT karo.
            is_urgent = False
            if args and isinstance(args[0], dict):
                # Status check: success, error, done, failed
                status_val = str(args[0].get("status", "")).lower()
                if status_val in ["success", "error", "done", "failed", "critical"]:
                    is_urgent = True

            # 2. THROTTLE LOGIC: Sirf tab apply hoga jab message urgent NAHI hai
            if throttled and not is_urgent:
                if channel == "state":
                    if now - self._last_state_emit < self._min_interval:
                        return
                    self._last_state_emit = now

                elif channel == "metrics":
                    if now - self._last_metrics_emit < self._min_interval:
                        return
                    self._last_metrics_emit = now

            # 3. SAFE DISPATCH
            try:
                # Urgent messages hamesha yahan se pass honge
                signal.emit(*args)

            except Exception as e:
                # CRASH RECOVERY
                try:
                    if self.bus and hasattr(self.bus, "emit_ui_event"):
                        self.bus.emit_ui_event(
                            "BRIDGE_CRITICAL",
                            {"error": str(e), "channel": channel or "unknown"}
                        )
                    else:
                        print(f"[Z-BRIDGE] CRITICAL FAIL: {e}")
                except Exception:
                    pass
    # =========================
    # FULL RESET (SAFE REBOOT SUPPORT)
    # =========================
    def reset_bridge(self):

        with self._lock:
            #  FIX: COMPLETE RESET
            self._state_cache.clear()
            self._last_state_str = ""
            self._last_state_emit = 0.0
            self._last_metrics_emit = 0.0
            self._last_boot_event = None
    def _handle_runtime_ready(self, data):
        if not isinstance(data, dict):
            return

        #  RECURSION BREAK
        if getattr(self, "_in_handler", False) or data.get("_from_manager"):
            return

        try:
            self._in_handler = True # Entry block lock

            if getattr(self, "_last_boot_event", None) == data.get("status"):
                return

            self._last_boot_event = data.get("status")

            self.pipe_state({
                "engine": data.get("engine", "OFFLINE"),
                "backend": data.get("backend", "UNKNOWN"),
                "view_mode": data.get("view_mode", "MAIN_MENU"),
                "status_text": data.get("status_text", "SYSTEM READY"),
                "output": data.get("output", None)   
            })
        finally:
            self._in_handler = False # Lock release

    def inject_event(self, event_name, data=None):
        """
        BACKWARD COMPATIBILITY FIX:
        Legacy modules support.
        """
        try:
            if self.bus:
                # SAFE UNIFIED PATH
                if hasattr(self.bus, "emit_ui_event"):
                    self.bus.emit_ui_event(event_name, data or {})
                elif hasattr(self.bus, "emit"):
                    self.bus.emit(event_name, data or {})
        except Exception as e:
            print(f"[LIVE_BRIDGE] inject_event failed: {e}")

    def _handle_execution_done(self, data):
        """
        Omni-Resolver: Backend se aane wale nested aur direct dono response handle karega.
        """
        # 1. State Update
        self.pipe_state({
            "execution": "DONE",
            "status": "IDLE",
            "engine": True,
            "engine_connected": True
        })
        
        # 2. Universal Response extraction
        response_text = None
        
        if isinstance(data, dict):
            # A. Nested data check (InferenceEngine standard format)
            if "data" in data and isinstance(data["data"], dict):
                response_text = data["data"].get("content")
            
            # B. Root level check (Fallbacks)
            if not response_text:
                response_text = (
                    data.get("output") or 
                    data.get("content") or 
                    data.get("response") or 
                    data.get("result") or
                    data.get("message")
                )
            
            # C. Stream buffer check
            if not response_text and "stream_buffer" in data:
                response_text = data["stream_buffer"]
        else:
            # Agar data seedha string hai
            response_text = str(data)

        # 3. Stream to UI
        if response_text:
            print(f"[DEBUG] Bridge successfully resolved response: {response_text}")
            self.pipe_stream(response_text)
        else:
            print(f"[DEBUG] Bridge received unreadable response format: {data}")


    def _handle_inference_response(self, data):
        """
        Inference channel se direct output pakadne wala bridge.
        """
        response = None
        if isinstance(data, dict):
            response = (
                data.get("output") or data.get("content") or
                data.get("result") or data.get("response")
            )
        else:
            response = str(data)

        print(f"[UI_BRIDGE_TRACE] Got response: {response}")
        print(f"[DEBUG] Bridge received data from inference: {data}")

        if response:
            self.pipe_stream(response)
        
        # Status update (optional)
        self.pipe_state({"status": "IDLE", "execution": "DONE"})


    def _handle_execution_progress(self, data):
        self.pipe_state({
            "status": "PROCESSING",
            "progress": data.get("count", 0)
        })

    def _handle_task_status(self, data):
        self.pipe_state({
            "task_status": data.get("status", "IDLE")
        })

    def _handle_engine_loaded(self, data):
        if getattr(self, "_in_handler", False):
            return
            
        try:
            self._in_handler = True
            
            self.pipe_state({
                "engine_loaded": True,
                "model_handle": data.get("handle", ""),
                "backend": data.get("output", {}).get("backend", "UNKNOWN") if isinstance(data.get("output"), dict) else "UNKNOWN",
                "view_mode": "DASHBOARD_ACTIVE",
                "status_text": "ENGINE LOADED"
            })
        finally:
            self._in_handler = False

            
            
    def get_state(self):
        """Diagnostic tool ke liye current cache return karein."""
        with self._lock:
            return dict(self._state_cache)
        
    def send_task(self, task):
        print("STEP 2: execution_bridge reached")

        if not self.execution_manager:
            print(" execution_manager NOT CONNECTED")
            return

        return self.execution_manager.submit_task(task)
    
# ========================================================
#  TITAN BRIDGE SINGLETON GATEWAY (NO PYSIDE CLASH)
# ========================================================
_bridge_instance = None

def get_bridge():
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ZStudioLiveBridge()
    return _bridge_instance
    
__all__ = ["ZStudioLiveBridge"]

    