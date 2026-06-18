"""
Z-STUDIO V12.3  RUNTIME API (INTERNAL EXECUTION LAYER)
Author/Brand: ZYNQUAR ATELIER
Module: scheduler_core.py (POLISHED)
Role: Industrial Grade Priority Queue with Memory Protection.
-----------------------------------------------------------------------
"""

import time
import heapq
import threading
from typing import Dict, Any, List, Optional

try:
    from logger_core import logger
except ImportError:
    import logging
    logger = logging.getLogger("ZYNQUAR_SCHEDULER")

from enum import Enum

class EngineTarget(Enum):
    AI_ENGINE = "ai_engine"
    MODEL_SERVICE = "model_service"
    HEALTH_MONITOR = "health_monitor"
    RESOURCE_CONTROL = "resource_control"
    AGENT_SERVICE = "agent_service"

class SchedulerCore:
    """
     ROLE: The Polished Traffic Signal. 
     LOGIC: Priority Heap + Memory Guard + Execution Control.
    """

    def __init__(self, parent_context=None): # <--- Ye bracket ke andar wala hissa add karein
        self.parent = parent_context
        self._task_queue = []
        self._lock = threading.Lock()
        self.is_active = True
        self.MAX_QUEUE_SIZE = 1000
        logger.info("[ZYNQUAR SCHEDULER] POLISHED ENGINE ACTIVE. MEMORY GUARD ENABLED.")
        
    def add_to_queue(self, envelope: Dict[str, Any]) -> bool:
        header = envelope.get("header", {})
        req_id = header.get("id", "ZQ-UNKNOWN")
        priority = header.get("priority", 5)

        with self._lock:
            #  YAHAN LAGAO HOOK (Overflow Check)
            if len(self._task_queue) >= self.MAX_QUEUE_SIZE:
                try:
                    from system_core.control_bus import control_bus
                    control_bus.publish("SYSTEM_ALERT", {
                        "source": "SCHEDULER", 
                        "status": "OVERFLOW", 
                        "req_id": req_id
                    })
                except:
                    pass # Bus abhi load nahi hui toh chup raho
                
                logger.error(f"[ZYNQUAR SCHEDULER] OVERFLOW! Dropping request: {req_id}")
                return False

            entry = (priority, time.time(), envelope)
            heapq.heappush(self._task_queue, entry)
            q_size = len(self._task_queue)
        
        logger.info(f"[ZYNQUAR SCHEDULER] QUEUED: {req_id} | PRIO: {priority} | Q-SIZE: {q_size}")
        return True

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
         OUTPUT: Highest Priority Task.
        """
        with self._lock:
            if not self.is_active:
                return None
                
            if not self._task_queue:
                # POLISH 2: Debug log for empty state
                logger.debug("[ZYNQUAR SCHEDULER] Queue Idle.")
                return None
            
            _, _, envelope = heapq.heappop(self._task_queue)
            
        logger.info(f"[ZYNQUAR SCHEDULER] DISPATCHING: {envelope['header']['id']}")
        return envelope

    def set_status(self, active: bool):
        """POLISH 1: External control for the scheduler flow."""
        with self._lock:
            self.is_active = active
            status = "RESUMED" if active else "PAUSED"
            logger.warning(f"[ZYNQUAR SCHEDULER] SYSTEM {status}")

    def get_queue_status(self) -> Dict[str, Any]:
        """Real-time monitoring stats."""
        with self._lock:
            return {
                "pending": len(self._task_queue),
                "capacity": f"{(len(self._task_queue)/self.MAX_QUEUE_SIZE)*100}%",
                "active": self.is_active
            }

    def clear_queue(self):
        """Emergency Wipe."""
        with self._lock:
            self._task_queue.clear()
            logger.warning("[ZYNQUAR SCHEDULER] EMERGENCY PURGE COMPLETE.")
    # 1.  ATOMIC HEALTH CHECK
    def is_alive(self) -> bool:
        """Safe runtime state check without false-positive lock testing."""
        return getattr(self, "is_active", False)

    # 2.  TYPE-SAFE PRE-EXECUTION
    def pre_execute(self, payload: Any) -> Dict[str, Any]:
        """
        Ensures DOWNSTREAM CONSISTENCY.
        Always returns a dictionary so InferenceEngine never crashes.
        """
        try:
            if payload is None:
                logger.error("[SCHEDULER] Null payload blocked.")
                return {"input": "", "type": "text", "error": "EMPTY_RENDER"}
            
            # Agar payload dict nahi hai (sirf string hai), to use structure mein dalo
            if not isinstance(payload, dict):
                return {"input": str(payload), "type": "text", "auto_wrapped": True}
            
            logger.info(f"[SCHEDULER] Pipeline Gate: {payload.get('type', 'generic')}")
            return payload

        except Exception as e:
            logger.error(f"[SCHEDULER_PRE_FATAL] {str(e)}")
            return {"input": str(payload), "error": "FALLBACK_ACTIVE"}

    # 3.  RESOURCE CLEANUP
    def post_execute(self, output: Any) -> Any:
        """Strict validation of output presence."""
        try:
            status = "SUCCESS" if output is not None else "EMPTY_OUTPUT"
            logger.info(f" [SCHEDULER] Execution Cycle Finished | Status: {status}")
            return output
        except Exception as e:
            logger.error(f"[SCHEDULER_POST_ERROR] {e}")
            return output
    def process_schedule(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Gateway for Router"""
        if self.add_to_queue(envelope):
            return {"status": "QUEUED", "request_id": envelope.get("header", {}).get("id")}
        return {"status": "FAILED", "error": "QUEUE_OVERFLOW"}

scheduler = SchedulerCore()    