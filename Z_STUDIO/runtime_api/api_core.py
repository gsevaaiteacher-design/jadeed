"""
Z-STUDIO V12.3  RUNTIME API (INTERNAL EXECUTION LAYER)
Author/Brand: ZYNQUAR ATELIER
Module: api_core.py (V10 HARDENED)
Role: Zero-Gap Entry Point with Command Validation & Security.
-----------------------------------------------------------------------
"""

import time
import uuid
from typing import Dict, Any, Optional, Set

#from runtime_api.request_router import request_router
from runtime_api.execution_manager import get_manager

try:
    from logger_core import logger
except ImportError:
    import logging
    logger = logging.getLogger("ZYNQUAR_API_CORE")

class ZStudioAPICore:
    """
     ROLE: UI requests ko Filter, Validate aur Route karna.
     LOGIC: Whitelist-based Command Execution & Schema Enforcement.
    """

    def __init__(self):
        self.active = True
        #  SECURITY: Only these commands are allowed to enter the engine
        self.COMMAND_WHITELIST: Set[str] = {
            "inference_run", "model_load", "model_unload", 
            "system_status", "memory_clear", "tool_call","default_chat"
        }
        logger.info("[ZYNQUAR API] HARDENED CORE ACTIVE. WHITELIST ENFORCED.")

    def handle_request(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
         INPUT: command, payload
         SECURITY: Command Whitelisting + Payload Integrity Check
        """
        req_id = self._generate_id()

        # 1. SYSTEM STATUS CHECK
        if not self.active:
            return self._build_err(req_id, "SERVICE_UNAVAILABLE", "API is in maintenance mode.")

        # 2. COMMAND VALIDATION (The Guard)
        if command not in self.COMMAND_WHITELIST:
            logger.warning(f"[ZYNQUAR API] BLOCKED: Unauthorized command '{command}' | ID: {req_id}")
            return self._build_err(req_id, "UNAUTHORIZED_COMMAND", f"Command '{command}' is not allowed.")

        # 3. PAYLOAD INTEGRITY
        if not isinstance(payload, dict) or len(payload) == 0:
            return self._build_err(req_id, "INVALID_PAYLOAD", "Payload must be a non-empty dictionary.")

        # 4. NORMALIZATION & WRAPPING
        logger.info(f"[ZYNQUAR API] PROCESSING: {command} | REQ: {req_id}")
        
        internal_envelope = {
            "header": {
                "id": req_id,
                "timestamp": time.time(),
                "priority": payload.get("priority", 5), # Default priority 5
                "origin": "DASHBOARD_UI"
            },
            "command": command,
            "payload": payload
        }

        # 5. DISPATCH TO ROUTER (Phase 3 - File 2)
        return self._dispatch_to_router(internal_envelope)
    
    
        

    def _dispatch_to_router(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        
        return get_manager().router.route(envelope)
    
    def _generate_id(self) -> str:
        """Traceable unique ID generation."""
        return f"ZQ-{uuid.uuid4().hex[:8].upper()}"

    def _build_err(self, req_id: str, code: str, msg: str) -> Dict[str, Any]:
        """Standardized Error Reporting."""
        logger.error(f"[ZYNQUAR API] ERROR: {code} | {msg}")
        return {
            "request_id": req_id,
            "status": "FAILED",
            "error_code": code,
            "message": msg,
            "timestamp": time.time()
        }

    def emergency_stop(self):
        """Instantly kill API entry point."""
        self.active = False
        logger.critical("[ZYNQUAR API] EMERGENCY STOP ACTIVATED.")

# GLOBAL SINGLETON
api_core = ZStudioAPICore()

#  ZYNQUAR ATELIER  [PHASE 3 - FILE 1: 10/10 HARDENED]