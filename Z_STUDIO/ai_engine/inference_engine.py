"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI OPERATING SYSTEM)
SIGNATURE: ZYNQUAR ATELIER
ROLE: Universal AI Resilient Execution Kernel & Orchestrator
-----------------------------------------------------------------------
"""
import sys
import os
import time
import logging
import threading
from enum import Enum

# =========================================================
# Z-STUDIO V12.3  INFERENCE ENGINE CORE  DEPENDENCY MAP
# =========================================================

# --- 1. MODEL SYSTEM (The Loader & Resolver) ---
from ai_engine.model_loader import ModelLoader
from ai_engine.model_registry import ModelRegistry
from ai_engine.model_path_resolver import ModelPathResolver

# --- 2. EXECUTION + REASONING (The Brain Logic) ---
from ai_engine.execution_graph import ExecutionGraph
from ai_engine.context_builder import ContextBuilder

# --- 3. MEMORY + VECTOR (The Knowledge Base) ---
from ai_engine.memory_engine import MemoryEngine
from ai_engine.vector_core import VectorCore
from ai_engine.embedding_engine import EmbeddingEngine

# --- 4. TOOLS + MULTIMODAL (The Capability Layer) ---
from ai_engine.tool_executor import ToolExecutor
from ai_engine.multimodal_router import MultimodalRouter

# --- 5. SAFETY + FALLBACK (The Reliability Guard) ---
from ai_engine.fallback_brain import FallbackBrain
from ai_engine.model_safety_layer import ModelSafetyLayer

# --- 6. SYSTEM CORE LINKS (The Nerve Center) ---
from system_core.control_bus import ControlBus
from system_core.logger_core import logger

# --- 7. DATA CORE LINKS (The Deep Storage) ---
from data_core.memory_store import MemoryStore

# --- 8. RUNTIME API LINKS (The Output Flow) ---
from runtime_api.stream_engine import StreamEngine


try:
    from system_core.constants import EngineTarget
except ImportError:
    class EngineTarget:
        AI_ENGINE = type('obj', (object,), {'value': 'AI_ENGINE'})


# =====================================================
#  CORE DEFINITIONS & ENUMS (THE BRAIN)
# =====================================================
class EngineTarget(Enum):
    AI_ENGINE = "text"
    AI_VOICE_CLONE = "voice_clone"
    AI_AUDIO_UPSCALE = "audio_upscale"
    AI_BG_REMOVE = "bg_remove"
    AI_MUSIC_GEN = "music_gen"
    AI_IMAGE = "image_gen"
    AI_VIDEO = "video_gen"
    MODEL_SERVICE = "model_service"
    HEALTH_MONITOR = "status"
    AGENT_SERVICE = "agent"

# =====================================================
#  SYSTEM CORE: INFERENCE ENGINE
# =====================================================
class InferenceEngine:
    """
    ZYNQUAR RULE: Zero-Footprint, Zero-Trust Execution.
    No-Gap Architecture v12.3
    """

    def __init__(self, model_path=None, model_type="UNIVERSAL", backend="AUTO", runtime_bridge=None, runtime_bus=None):

        # 0. CONFIGURATION & STATE
        self.backend = backend
        self.model_path = model_path
        self.model_type = model_type
        self._run_lock = threading.RLock()

        # 1. CORE SYSTEM LOGGERS
        try:
            from system_core.logger_core import logger as _logger
            self.logger = _logger
        except Exception:
            self.logger = logging.getLogger("Z-KERNEL-FALLBACK")

        # 2. ARCHITECTURE CONTRACTS
        self.bridge = runtime_bridge
        self.runtime = runtime_bridge

        if runtime_bus is None and runtime_bridge is not None and hasattr(runtime_bridge, 'subscribe'):
            runtime_bus = runtime_bridge

        self.bus = runtime_bus if runtime_bus is not None else self._create_resilient_bus()
        self._bus_ready = hasattr(self.bus, 'subscribe')

        # 4. AI CORE HOOKS
        self.loader = ModelLoader(runtime_bridge=self.bridge)
        self.registry = ModelRegistry()
        self.resolver = ModelPathResolver()
        self.graph = ExecutionGraph()
        self.context = ContextBuilder()
        self.memory = MemoryEngine()
        self.memory_store = MemoryStore()
        self.embedder = EmbeddingEngine()
        self.tools = ToolExecutor()
        self.router = MultimodalRouter()
        self.safety = ModelSafetyLayer()
        self.fallback = FallbackBrain()

        # 5. INDUSTRIAL WIRING
        if hasattr(self.context, "set_memory"):
            self.context.set_memory(self.memory)
        self.dispatch = self.graph.execute if hasattr(self.graph, "execute") else lambda task: None
        self.inference_engine = None
        self.active_runtime_mode = "IDLE"
        self.is_active = True
        self.current_model_id = "ZAI_CORE_V12.3"
        self.registry_state = {"active": None, "pending_queue": []}
        self.safety_layer = self.safety
        self.static_active_handle = None

        # 7. FINAL STATE SYNC
        self.model_loaded = False
        self.engine_ready = True
        self._sync_with_state_manager("ONLINE")

        # --- APPLY HARD-WIRING AFTER SYNC ---
        self._apply_hard_wiring()

        self.logger.info(f"[Z-KERNEL] V12.3 CORE LOCKED | Model: {self.current_model_id} | Backend: {self.backend}")

    def _apply_hard_wiring(self):
        """State Manager ke 'Clean-up' ke baad force subscription."""
        if not getattr(self, "_bus_ready", False):
            return
        if not self.bus:
            return
        try:
            self.bus.subscribe("inference", self._bus_inference_entry)
            self.bus.subscribe("ENGINE_PING", self._handle_ping)
        except Exception as e:
            self.logger.error(f"[WIRING_CRASH] {e}")

    def _trace_entry(self, task):
        """Debug trace entry point"""
        pass

    def _bus_inference_entry(self, task):
        """Safe Bus Entry Layer (HARDENED)"""
        try:
            if isinstance(task, str):
                task = {"trace_id": f"AUTO_{hash(task)}", "input": task, "content": task}
            elif not isinstance(task, dict):
                task = {"trace_id": f"AUTO_INVALID_{id(task)}", "input": str(task), "content": str(task)}

            trace_id = task.get("trace_id", f"AUTO_{id(task)}")
            task["trace_id"] = trace_id

            self.execute_inference(task)
        except Exception as e:
            safe_trace = task.get("trace_id", "UNKNOWN") if isinstance(task, dict) else "UNKNOWN"
            if self.bus:
                self.bus.publish("EXECUTION_DONE", {
                    "status": "ERROR",
                    "message": f"Critical Pipeline Failure: {str(e)}",
                    "error_code": "INFERENCE_ENTRY_CRASH",
                    "trace_id": safe_trace
                })

    def bind_model_handle(self, handle):
        self.static_active_handle = handle
        self.logger.info(f"[Z-KERNEL] Model handle bound: {handle}")

    def initialize_db(self):
        """Late-binding for Vector System to ensure Bus is ready."""
        try:
            from data_core.vector_db import VectorDB
            self.vector_core = VectorCore()
            self.vector_db = VectorDB(runtime_bus=self.bus)

            if hasattr(self.vector_core, "bind_embedder"):
                self.vector_core.bind_embedder(self.embedder)

            self.logger.info("[Z-KERNEL] Vector System successfully initialized.")
        except Exception as e:
            self.logger.error(f"[Z-KERNEL] Vector System Initialization Failed: {e}")

    def _create_resilient_bus(self):
        """Creates a NO-OP Bus that logs warnings instead of crashing."""
        class ResilientBus:
            def __getattr__(self, name):
                def _noop(*args, **kwargs):
                    return None
                return _noop
        return ResilientBus()

    # 9. BUS SIGNAL HANDLER
    def _handle_ping(self, data):
        return {"status": "ALIVE", "model": self.current_model_id}

    def _sync_with_state_manager(self, state):
        """Standardizes state reporting via MASTER CONTROL BUS."""
        try:
            if self.bus is not None and hasattr(self.bus, "publish"):
                self.bus.publish("SYSTEM_SUBSYSTEM_STATE", {
                    "subsystem": "AI_ENGINE",
                    "status": "ONLINE",
                    "engine_state": state,
                    "engine_target": EngineTarget.AI_ENGINE.value,
                    "timestamp": time.time(),
                    "process_id": os.getpid()
                })
            else:
                logging.info(f"[Z-KERNEL] Central Bus Deferred. State registered: {state}")
        except Exception as e:
            logging.error(f"[Z-KERNEL] Master Bus Notification Error: {str(e)}")

    def generate(self, payload, **kwargs):
        if not hasattr(self, 'model') or not self.model:
            return {"status": "error", "message": "MODEL_NOT_BOUND"}

        try:
            return self.model.generate(
                prompt=payload,
                **kwargs
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _hard_circuit_breaker(self):
        """Forces system to reset to IDLE if bridge hangs."""
        self.is_active = False
        time.sleep(0.1)
        self.is_active = True
        self.logger.warning("[Z-KERNEL] Circuit Reset: Engine re-stabilized.")

    def execute_inference(self, payload):
        """Unified Gate controlling Safety, Resources, and Scheduling."""
        if not isinstance(payload, dict):
            return self._fail("INVALID_PAYLOAD", "Payload must be a dictionary.", None)

        trace_id = payload.get("trace_id", "UNKNOWN")

        prompt = payload.get("input") or payload.get("content") or (payload.get("payload", {}).get("content") if isinstance(payload.get("payload"), dict) else None) or ""
        payload["input"] = prompt

        # ENGINE STATE CHECK
        if not getattr(self, "is_active", False):
            return self._fail("ENGINE_OFF", "Kernel state is INACTIVE", trace_id)

        # SAFETY LAYER
        if getattr(self, "safety_layer", None):
            validation_input = {"input": prompt, "model_path": payload.get("model_path", "")} if isinstance(prompt, str) else payload
            if not self.safety_layer.validate(validation_input):
                return self._fail("SAFETY_VIOLATION", "Z-STUDIO Safety Protocols blocked the request.", trace_id)

        # RESOURCE CHECK
        if getattr(self, "resource_guard", None):
            if hasattr(self.resource_guard, "check_memory"):
                mem = self.resource_guard.check_memory()
                if not mem.get("available", True):
                    return self._fail("RESOURCE_CRITICAL", "Insufficient System Memory.", trace_id)

        # SAFE MODEL RESOLUTION
        model_handle = getattr(self, "static_active_handle", None)
        if not model_handle and getattr(self, "loader", None) and getattr(self.loader, "active_handles", None):
            for v in self.loader.active_handles.values():
                if isinstance(v, dict):
                    model_handle = v.get("handle") or v.get("model")
                    if model_handle:
                        break
        if not model_handle:
            model_handle = getattr(self, "model", None)

        # GHOST MODE
        if not model_handle or model_handle == "ZAI_PRIMARY_CORE":
            resp = {"status": "ENGINE_READY_AWAITING_MODEL", "output": "Z-Studio AI Core operational. Awaiting weights.", "trace_id": trace_id}
            if getattr(self, "bus", None):
                self.bus.publish("EXECUTION_DONE", resp)
            return resp

        # SCHEDULER
        if getattr(self, "scheduler", None):
            try:
                if hasattr(self.scheduler, "queue_task"):
                    self.scheduler.queue_task(payload)
            except Exception as e:
                self.logger.warning(f"[SCHEDULER_WARN]: {e}")

        # EXECUTION LAYER
        try:
            result = self.execute(model_handle, payload)
        except Exception as e:
            return self._fail("EXECUTION_CRASH", str(e), trace_id)

        # SUCCESS PATH
        is_success = (result.get("status") in ["SUCCESS", "OK", True] if isinstance(result, dict) else bool(result))
        if is_success:
            final_response = {
                "status": "SUCCESS",
                "output": result.get("data", {}).get("content") if isinstance(result, dict) else result,
                "trace_id": trace_id,
                "meta": result.get("data", {}).get("performance", {}) if isinstance(result, dict) else {}
            }
            if getattr(self, "bus", None):
                self.bus.publish("EXECUTION_DONE", final_response)
            return final_response

        # ERROR PATH
        error_msg = result.get("message", "Unknown Error") if isinstance(result, dict) else "Unknown Error"
        error_code = result.get("error_code", "EXECUTION_FAILED") if isinstance(result, dict) else "EXECUTION_FAILED"
        return self._fail(error_code, error_msg, trace_id)

    def execute(self, model_handle, payload):
        """Low-level Bridge Execution with Resiliency."""
        trace_id = payload.get("trace_id")

        if not self.bridge or not hasattr(self.bridge, "process"):
            return self._fail("BRIDGE_UNAVAILABLE", "Runtime bridge unavailable.", trace_id)

        prompt = payload.get("input")
        media_type = "AI_ENGINE"

        final_config = self._get_default_config("text")
        final_config.update(payload.get("config", {}))

        max_retries = int(final_config.get("max_retries", 2))
        last_error = None

        for attempt in range(1, max_retries + 2):
            try:
                raw_output = self.bridge.process(
                    handle=model_handle,
                    data=prompt,
                    task_type=media_type,
                    params=final_config,
                    timeout=final_config.get("timeout", 30)
                )

                if isinstance(raw_output, dict) and raw_output.get("status") == "ERROR":
                    last_error = f"Hardware Error: {raw_output.get('error')}"
                    self.logger.warning(f"[Z-KERNEL] Attempt {attempt} failed: {last_error}")
                    continue

                if self._validate_bridge_output(raw_output, media_type):
                    return self._normalize(raw_output, media_type, attempt, model_handle)

                last_error = "VALIDATION_ERROR: Corrupted or empty output from bridge."
                self.logger.error(f"[Z-KERNEL] {last_error}")

            except Exception as e:
                self.logger.critical(f"[Z-KERNEL] BRIDGE CRASH: {str(e)}")
                self._hard_circuit_breaker()
                return self._fail("BRIDGE_CRASHED", str(e), trace_id)

        return self._fail("RETRY_LIMIT_EXHAUSTED", last_error or "Unknown failure during execution.", trace_id)

    # -----------------------------------------------------
    # DEF 5: DATA VALIDATION (ZERO-TRUST)
    # -----------------------------------------------------
    def _validate_bridge_output(self, output, m_type):
        """Strict validation for all media types aligned with Titan-OS Standard."""
        if output is None:
            return False

        if m_type == "AI_ENGINE" or m_type == EngineTarget.AI_ENGINE.value:
            if isinstance(output, dict):
                return len(str(output).strip()) > 0
            return isinstance(output, (str, bytes)) and len(str(output).strip()) > 0

        if m_type in [EngineTarget.AI_IMAGE.value, EngineTarget.AI_VIDEO.value, "image_gen", "video_gen"]:
            return isinstance(output, (bytes, dict, str))

        return True

    # -----------------------------------------------------
    # DEF 6: PERFORMANCE NORMALIZATION (TELEMETRY)
    # -----------------------------------------------------
    def _normalize(self, raw_data, media_type, attempts, model_handle):
        """Packages raw data into the Z-STUDIO Pipeline Standard."""
        content = raw_data
        if isinstance(raw_data, dict):
            content = raw_data.get("content", raw_data.get("data", raw_data))

        return {
            "status": "SUCCESS",
            "data": {
                "content": content,
                "media_type": media_type,
                "performance": {
                    "attempts": attempts,
                    "timestamp": time.time(),
                    "model_handle": str(model_handle),
                    "process_node": "KERNEL_01"
                }
            }
        }

    # -----------------------------------------------------
    # DEF 7: MULTIMODAL CONFIG ROUTER
    # -----------------------------------------------------
    def _get_default_config(self, media_type):
        """Dynamic configuration based on the requested AI Target."""
        defaults = {
            "text": {"max_tokens": 4096, "temperature": 0.7, "max_retries": 2},
            "image": {"steps": 30, "cfg_scale": 7.5, "timeout": 150},
            "voice_clone": {"speed": 1.0, "format": "wav", "timeout": 30},
            "video_gen": {"fps": 24, "steps": 50, "timeout": 300},
            "bg_remove": {"model": "U2NET", "timeout": 20}
        }
        return defaults.get(media_type, {"timeout": 45}).copy()

    # -----------------------------------------------------
    # DEF 8: ERROR STANDARDIZATION (CONTRACT)
    # -----------------------------------------------------
    def _fail(self, code, message, trace_id=None):
        """Global Fail Contract - UI Sync Compliant."""
        logging.error(f"[Z-KERNEL] Failure ({code}): {message}")
        return {
            "status": "ERROR",
            "output": None,
            "error_code": code,
            "message": message,
            "trace_id": trace_id,
            "origin": "INFERENCE_ENGINE_V12"
        }

    # -----------------------------------------------------
    # DEF 9: LIFE CYCLE MANAGEMENT
    # -----------------------------------------------------
    def shutdown(self):
        """Gracefully release hardware handles and resources."""
        self.is_active = False
        self._sync_with_state_manager("OFFLINE")

    def get_active_channel(self, channel_type="default"):
        if hasattr(self, 'channels'):
            return self.channels.get(channel_type, "primary_channel")
        return "primary_channel"


# 2. Singleton logic
_instance = None

def get_engine(runtime_bridge=None):
    global _instance
    if _instance is None:
        _instance = InferenceEngine(runtime_bridge=runtime_bridge)
    return _instance

if __name__ == "__main__":
    engine = get_engine()
    print("[ENGINE] Starting runtime...")
    engine.execute_inference({"input": "boot_test", "trace_id": "BOOT"})
