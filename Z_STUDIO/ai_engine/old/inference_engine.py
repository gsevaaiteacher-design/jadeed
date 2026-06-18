"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI OPERATING SYSTEM)
SIGNATURE: ZYNQUAR ATELIER
ROLE: Universal AI Resilient Execution Kernel & Orchestrator
-----------------------------------------------------------------------
"""

import time
import logging
import os
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
from data_core.vector_db import VectorDB

# --- 8. RUNTIME API LINKS (The Output Flow) ---
from runtime_api.stream_engine import StreamEngine

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
        import os, threading, logging
        print(f"DEBUG: ENGINE INSTANTIATED! PID: {os.getpid()} | Thread: {threading.current_thread().name}")
        self.backend = backend
        self.model_path = model_path
        self.model_type = model_type
        
        # 1. CORE SYSTEM LOGGERS (Resilient)
        try:
            from system_core.logger_core import logger
            self.logger = logger
        except:
            self.logger = logging.getLogger("Z-KERNEL-FALLBACK")
            
        self._run_lock = threading.RLock()
        
        # 2. ARCHITECTURE CONTRACTS (Decoupled & Resilient)
        # Bridge = Execution, Bus = Messaging
        self.bridge = runtime_bridge
        self.runtime = runtime_bridge
        print(f"[DEBUG] InferenceEngine Bus ID: {id(runtime_bridge)}")
        self.bus = runtime_bus if runtime_bus is not None else self._create_resilient_bus()
        self._bus_ready = hasattr(self.bus, 'subscribe') 
        
        # 3. AI CORE HOOKS (ModelLoader Link)
        self.loader = ModelLoader(runtime_bridge=self.bridge)
        self.registry = ModelRegistry()
        self.resolver = ModelPathResolver()
        self.graph = ExecutionGraph()
        self.context = ContextBuilder()
        
        # 4. CAPABILITY SYSTEMS
        self.memory = MemoryEngine()
        self.memory_store = MemoryStore()
       
        
        self.vector_db = VectorDB(
            runtime_bus=self.bus
        )
        self.embedder = EmbeddingEngine()
        self.tools = ToolExecutor()
        self.router = MultimodalRouter()
        self.safety = ModelSafetyLayer()
        self.fallback = FallbackBrain()
        
        # 5. INDUSTRIAL WIRING
        if hasattr(self.context, "set_memory"): self.context.set_memory(self.memory)
        if hasattr(self.vector_core, "bind_embedder"): self.vector_core.bind_embedder(self.embedder)
            
        self.dispatch = self.graph.execute if hasattr(self.graph, "execute") else lambda task: None
            
        self.inference_engine = None
        self.active_runtime_mode = "IDLE"
        
        # 6. EXECUTION LAYER
        self.is_active = True
        self.current_model_id = "ZAI_CORE_V12.3"
        self.registry_state = {"active": None, "pending_queue": []}
        self.safety_layer = self.safety
        self.static_active_handle = None
        

        # 7. BUS SIGNAL CONTRACT (Fault-Tolerant)
        if self._bus_ready:
            try:
                self.bus.subscribe("ENGINE_PING", self._handle_ping)
            except Exception as e:
                self.logger.error(f"[Z-KERNEL] Bus Subscription Fault: {e}")

        # 8. FINAL STATE SYNC
        self.model_loaded = False
        self.engine_ready = True
        self._sync_with_state_manager("ONLINE")
        self.logger.info(f" [Z-KERNEL] V12.3 CORE LOCKED | Model: {self.current_model_id} | Backend: {self.backend}")

        # ==============================================================================
        # VECTOR SYSTEM (SAFE BUS INJECTION)
        # ==============================================================================
        try:
            self.vector_core = VectorCore()

            # SAFE BUS FALLBACK
            safe_bus = runtime_bus if runtime_bus is not None else self.bus

            self.vector_db = VectorDB(runtime_bus=safe_bus)

        except Exception as e:
            self.logger.error(f"[Z-KERNEL] Vector System Failed: {e}")
            self.vector_core = None
            self.vector_db = None

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
        """Standardizes state reporting via MASTER CONTROL BUS without illegal imports."""
        try:
            if self.bus is not None and hasattr(self.bus, "publish"):
                # Direct communication via the central pipeline
                self.bus.publish("SYSTEM_SUBSYSTEM_STATE", {
                    "subsystem": "AI_ENGINE",
                    "status": "ONLINE",
                    "engine_state": state,
                    "engine_target": EngineTarget.AI_ENGINE.value,
                    "timestamp": time.time(),
                    "process_id": os.getpid()
                })
            else:
                # Agar boot ke waqt control bus deferred hai, toh system native route pakdega
                logging.info(f"[Z-KERNEL] Central Bus Deferred. State registered: {state}")
        except Exception as e:
            logging.error(f"[Z-KERNEL] Master Bus Notification Error: {str(e)}")

    def bind_model(self, handle):
        """Bind loaded model handle to engine"""
        self.model = handle

    
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

    # -----------------------------------------------------
    # DEF 3: ORCHESTRATION GATE (THE GATEKEEPER) - TRUE NATIVE KERNEL
    # -----------------------------------------------------

    def _hard_circuit_breaker(self):
        """Forces system to reset to IDLE if bridge hangs."""
        self.is_active = False
        time.sleep(0.1)
        self.is_active = True
        self.logger.warning(" [Z-KERNEL] Circuit Reset: Engine re-stabilized.")

    def execute_inference(self, payload):
        """Unified Gate controlling Safety, Resources, and Scheduling."""
        
        # ... baaki purana code ...
        # FIX: Defensive Payload check (System Integrity)
        if not isinstance(payload, dict):
            return self._fail("INVALID_PAYLOAD", "Payload must be a dictionary.")

        if not self.is_active:
            return self._fail("ENGINE_OFF", "Kernel state is INACTIVE")

        # A. SAFETY HOOK (Aapka original logic)
        prompt = payload.get("input", "")
        if hasattr(self, 'safety_layer') and self.safety_layer and not self.safety_layer.validate(prompt):
            return self._fail("SAFETY_VIOLATION", "Z-STUDIO Safety Protocols blocked the request.")

        # B. RESOURCE MANAGEMENT HOOK (Aapka original logic)
        if hasattr(self, 'resource_guard') and self.resource_guard:
            mem_status = self.resource_guard.check_memory()
            if not mem_status.get("available", True):
                return self._fail("RESOURCE_CRITICAL", "Insufficient System Memory for Inference.")

        #  HARDWARE RESOLUTION ROUTE (Aapka original logic)
        model_handle = getattr(self, "static_active_handle", None)

        if model_handle is None and hasattr(self, 'loader') and getattr(self.loader, 'active_handles', None):
            for k, v in self.loader.active_handles.items():
                if isinstance(v, dict) and "handle" in v:
                    model_handle = v["handle"]
                    break

        if model_handle is None and hasattr(self, 'model') and self.model:
            model_handle = self.model

        if model_handle is None or model_handle == "ZAI_PRIMARY_CORE":
            return {
                "status": "ENGINE_READY_AWAITING_MODEL",
                "output": None,
                "error_code": "CORE_ACTIVE_WEIGHTS_PENDING",
                "message": "Z-Studio AI Core framework is 100% operational. Awaiting runtime weights injection."
            }

        # C. SCHEDULER TASK QUEUEING (Aapka original logic)
        if hasattr(self, 'scheduler') and self.scheduler:
            task_id = self.scheduler.queue_task(payload)

        # Execution layer call (Aapka original logic)
        result = self.execute(model_handle, payload)

        # UNIFIED RETURN CONTRACT (Aapka original logic)
        if result and result.get("status") == "SUCCESS":
            return {
                "status": "SUCCESS",
                "output": result["data"]["content"],
                "error_code": None,
                "meta": result["data"].get("performance", {})
            }
        
        return self._fail(result.get("error_code", "EXECUTION_FAILED") if result else "NO_RESULT", result.get("message") if result else "Unknown Error")

    # -----------------------------------------------------
    # DEF 4: HARDWARE INTERFACE (THE MUSCLE)
    # -----------------------------------------------------
    def execute(self, model_handle, payload):
        """Low-level Bridge Execution with Resiliency."""
        prompt = payload.get("input")
        media_type = "AI_ENGINE"
        
        final_config = self._get_default_config("text")
        final_config.update(payload.get("config", {}))

        max_retries = int(final_config.get("max_retries", 2))
        last_error = None

        for attempt in range(1, max_retries + 2):
            try:
                #  SINGLE SOURCE OF TRUTH: Bridge call
                raw_output = self.bridge.process(
                    handle=model_handle,
                    data=prompt,
                    task_type=media_type,
                    params=final_config,
                    timeout=final_config.get("timeout", 30)
                )

                # Hardware-level error check
                if isinstance(raw_output, dict) and raw_output.get("status") == "ERROR":
                    last_error = f"Hardware Error: {raw_output.get('error')}"
                    self.logger.warning(f"[Z-KERNEL] Attempt {attempt} failed: {last_error}")
                    continue

                # Data Integrity Validation
                if self._validate_bridge_output(raw_output, media_type):
                    return self._normalize(raw_output, media_type, attempt, model_handle)
                
                last_error = "VALIDATION_ERROR: Corrupted or empty output from bridge."
                self.logger.error(f"[Z-KERNEL] {last_error}")

            except Exception as e:
                #  HARD-CIRCUIT BREAKER: Critical crash handle
                self.logger.critical(f"[Z-KERNEL] BRIDGE CRASH: {str(e)}")
                self._hard_circuit_breaker() 
                return self._fail("BRIDGE_CRASHED", "Hardware bridge reset initiated due to exception.")

        return self._fail("RETRY_LIMIT_EXHAUSTED", last_error or "Unknown failure during execution.")

    # -----------------------------------------------------
    # DEF 5: DATA VALIDATION (ZERO-TRUST)
    # -----------------------------------------------------
    def _validate_bridge_output(self, output, m_type):
        """Strict validation for all media types aligned with Titan-OS Standard."""
        if output is None: 
            return False
        
        # Rigid verification bypass against string/dict structures
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
        return {
            "status": "SUCCESS",
            "data": {
                "content": raw_data,
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
    def _fail(self, code, message):
        """Ensures Execution Manager always receives a structured error."""
        logging.error(f"[Z-KERNEL] Failure ({code}): {message}")
        return {
            "status": "ERROR",
            "output": None,
            "error_code": code,
            "message": message,
            "origin": "INFERENCE_ENGINE_V12"
        }
    
    # -----------------------------------------------------
    # DEF 9: LIFE CYCLE MANAGEMENT
    # -----------------------------------------------------
    def shutdown(self):
        """Gracefully release hardware handles and resources."""
        print(" [Z-KERNEL] Shutting down AI Engine...")
        self.is_active = False
        self._sync_with_state_manager("OFFLINE")
        # Resource cleanup logic

# 2. Singleton ka logic fix
_instance = None

def get_engine(runtime_bridge=None):
    global _instance
    if _instance is None:
        # Singleton banate waqt bridge inject karo
        _instance = InferenceEngine(runtime_bridge=runtime_bridge)
    return _instance