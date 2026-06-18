"""
Z-STUDIO V12.9  PRODUCTION API GATEWAY KERNEL (ZERO-GAP AUDIT)
Role: Fault-Tolerant, Uniform-Contract Gateway
"""

import time
import threading
import logging
from typing import Dict, Any, Optional
from enum import Enum
from typing import Dict, Any, Optional, Tuple, Callable
from runtime_api.request_router import get_router

logger = logging.getLogger("ZYNQUAR_KERNEL_CORE")

class KernelState(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"

class ZStudioExecutionManager:
    _manager_instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._manager_instance is None:
            with cls._instance_lock:
                if cls._manager_instance is None:
                    cls._manager_instance = super().__new__(cls)
        return cls._manager_instance

    def __init__(self):
        if getattr(self, '_initialized', False): return
        self._initialized = True
        
        # Core Infrastructure
        self.bus = None
        self.router = get_router()
        
        self.orchestrator = None
        self.live_bridge = None
        self.ai_brain = None
        self.locked_method = None
        self.is_ready = False
        self.lifecycle_state = KernelState.READY
        
        # Concurrency & Metrics
        self._active_transactions = 0
        self._max_capacity = 64
        self._backpressure_lock = threading.Lock()
        
        logger.info("[INIT] Router-Manager Link Secured.")
        
        # Telemetry Metrics (Window-based)
        self._metrics = {"total": 0, "success": 0, "fail": 0, "latency": 0.0}
        self._metrics_lock = threading.Lock()
        
        logger.info("[INIT] Z-STUDIO GATEWAY: ZERO-GAP BUILD ACTIVE.")

    def setup_bridge(self):
        #           
        if self.router and self.orchestrator:
            self.router.set_orchestrator(self.orchestrator)
            logger.info("[PIPELINE] Router-Orchestrator Bridge Linked.")

    def route_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        req_id = payload.get("header", {}).get("id") or f"ZQ-{int(time.time())}"
        
        # 1.   ,    (Non-blocking)
        #          
        def async_exec():
            try:
                raw_res = self.orchestrator.submit_task(payload)
                #     UI    
                if self.bus:
                    self.bus.publish("UI_RESPONSE_CHANNEL", {
                        "request_id": req_id,
                        "status": "success",
                        "output": raw_res,
                        "timestamp": time.time()
                    })
            except Exception as e:
                logger.error(f"[GATEWAY] Async execution failed: {e}")

        #   
        threading.Thread(target=async_exec, daemon=True).start()

        # 2.   ACK    UI   
        return {
            "request_id": req_id,
            "status": "DISPATCHED",
            "message": "Task accepted, processing in background."
        }

    def _validate_payload(self, p: Any) -> bool:
        return isinstance(p, dict) and "target" in p and ("header" in p or "request_id" in p)

    def _update_metrics(self, success: bool, latency: float):
        with self._metrics_lock:
            self._metrics["total"] += 1
            if success:
                self._metrics["success"] += 1
                self._metrics["latency"] = (self._metrics["latency"] + latency) / 2
            else:
                self._metrics["fail"] += 1
            
            # Ratio-based Degradation Logic (If failure > 20% of last 50 calls)
            if self._metrics["total"] >= 50:
                fail_ratio = self._metrics["fail"] / self._metrics["total"]
                self.lifecycle_state = KernelState.DEGRADED if fail_ratio > 0.2 else KernelState.READY
                # Reset window
                self._metrics = {"total": 0, "success": 0, "fail": 0, "latency": 0.0}

    def submit_task(self, raw_task: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        # 1.  ORCHESTRATOR_TASK   ,      
        channel = "ORCHESTRATOR_TASK"
        
        if self.bus and self.bus.has_channel(channel):
            #  Bus   
            response = self.bus.request(channel, raw_task)
            
            #   
            if response:
                return True, {"status": "SUCCESS", "data": response}
            else:
                return False, {"status": "ERROR", "msg": "Orchestrator returned None"}
        
        return False, {"status": "ERROR", "msg": "Channel ORCHESTRATOR_TASK not found"}


    def _finalize(self, req_id: str, status: str, output: Any) -> Dict[str, Any]:
        """UNIFORM CONTRACT GUARANTEE"""
        response = {
            "request_id": req_id,
            "status": status,
            "output": output,
            "timestamp": time.time()
        }
        if self.bus:
            try: self.bus.publish("UI_RESPONSE_CHANNEL", response)
            except: pass
        return response

    def bind_orchestrator(self, orch: Any):
        self.orchestrator = orch
        self.setup_bridge()

    def bind_bus(self, bus: Any):
        self.bus = bus
        if bus and hasattr(bus, "subscribe"):
            bus.subscribe("UI_REQUEST", self.route_request)

    def attach_bridge(self, bridge) -> bool:
        """Connects LiveBridge to ExecutionManager (bidirectional)."""
        self.live_bridge = bridge
        if hasattr(bridge, "execution_manager"):
            bridge.execution_manager = self
        logger.info("[ATTACHMENT] UI communication interface pipeline hooked.")
        return True

    def attach_ai(self, ai_brain: Any) -> None:
        """Binds AI inference engine to the gateway."""
        self.ai_brain = ai_brain
        if hasattr(ai_brain, "execute_inference"):
            self.locked_method = ai_brain.execute_inference
        elif hasattr(ai_brain, "generate"):
            self.locked_method = ai_brain.generate
        logger.info("[KERNEL] AI Brain inference method attached.")

    def set_messenger(self, messenger_proxy: Any):
        """Bridge for Launcher to pass communication proxy."""
        self.messenger = messenger_proxy
        logger.info("[INFRA] Execution Manager messenger proxy set.")

    def send(self, event, data=None):
        #      messenger  send  
        if hasattr(self.messenger, 'send'):
            return self.messenger.send(event, data)
        elif hasattr(self.messenger, 'emit'): # Bus   emit  
            return self.messenger.emit(event, data)
        return False

    def get_messenger(self):
        """Returns the current messenger proxy for the Launcher."""
        return getattr(self, 'messenger', None)
    
    def set_ready(self, status: bool):
        """System boot requirement."""
        self.is_ready = status
        self.lifecycle_state = KernelState.READY if status else KernelState.DEGRADED
        logger.info(f"[INFRA] Execution Manager ready state: {status}")

# Singleton Accessor (YE FILE KE BILKUL END MEIN HONA CHAHIYE)
def get_manager() -> ZStudioExecutionManager:
    return ZStudioExecutionManager()

# Backward compatibility alias
ExecutionManager = ZStudioExecutionManager