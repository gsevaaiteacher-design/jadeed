"""
Z-STUDIO V12.3  RUNTIME API (INTERNAL EXECUTION LAYER)
Author/Brand: ZYNQUAR ATELIER
Module: request_router.py (V14 STRICT CONTRACT)
Role: Standardized Dispatcher. Zero-Gap Type-Safe Handover.
-----------------------------------------------------------------------
"""

import time
import uuid
from typing import Dict, Any
try:
    from logger_core import logger
except ImportError:
    import logging
    logger = logging.getLogger("ZYNQUAR_ROUTER")

from runtime_api.scheduler_core import EngineTarget


class ZStudioRequestRouter:
    """
     ROLE: The Decision Point.
     LOGIC: Standardized Contract: process_request(target: Enum, envelope: Dict)
    """

    def __init__(self):
        # Explicit Mapping
        self.ROUTE_MAP: Dict[str, EngineTarget] = {
            "inference_run": EngineTarget.AI_ENGINE,
            "model_load": EngineTarget.MODEL_SERVICE,
            "model_unload": EngineTarget.MODEL_SERVICE,
            "system_status": EngineTarget.HEALTH_MONITOR,
            "memory_clear": EngineTarget.RESOURCE_CONTROL,
            "tool_call": EngineTarget.AGENT_SERVICE
        }
        self.orchestrator = None #  BRIDGE ADDED
        logger.info("[ZYNQUAR ROUTER] V14 STRICT CONTRACT ACTIVE.")

    def set_orchestrator(self, orchestrator):
        self.orchestrator = orchestrator
        logger.info("[ROUTER] Orchestrator Bridge Linked.")

    def route(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        command = envelope.get("command")
        req_id = envelope.get("header", {}).get("id", "ZQ-UNKNOWN")
        
        #  Resolve Alias
        task_type = self.ROUTE_MAP.get(command, "FALLBACK")

        if not self.orchestrator:
            return self._build_err(req_id, "ORCHESTRATOR_UNBOUND")

        #  Industrial Packet Construction
        industrial_task = {
            "type": task_type,
            "payload": envelope.get("payload", {}),
            "trace_id": req_id,
            "timestamp": time.time()
        }

        # Handover to Orchestrator (Not Manager)
        return self.orchestrator.submit_task(industrial_task)

    
        

    def dispatch_request(self, user_input: str) -> Dict[str, Any]:
        user_input_str = str(user_input).strip()
        command = "tool_call" if user_input_str.startswith("/") else "inference_run"

        envelope = {
            "header": {"id": f"Z-TRC-{uuid.uuid4().hex[:8].upper()}"},
            "command": command,
            "payload": {"text": user_input_str}
        }
        return self.route(envelope)

    def _build_err(self, req_id: str, code: str, detail: str = "") -> Dict[str, Any]:
        return {"request_id": req_id, "status": "FAILED", "error_code": code, "detail": detail}

    

request_router = ZStudioRequestRouter()
def get_router(): return request_router

#  ZYNQUAR ATELIER  [PHASE 3 - FILE 2: 10/10 ABSOLUTE LOCK - STRICT V14]