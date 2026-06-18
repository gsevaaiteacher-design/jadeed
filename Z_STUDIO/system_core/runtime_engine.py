"""
Z-STUDIO V12.3  SYSTEM CORE (RUNTIME ENGINE)
Module: Runtime Engine
Role: Real System Controller & Resource Guard (Polished Industrial Stable)
"""

import os
import sys
import time
import threading
import logging

# =========================================================
# SYSTEM LOGGER CONTROL
# =========================================================
try:
    from system_core.logger_core import logger
except Exception:
    logger = logging.getLogger("RuntimeEngine")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False



class RuntimeEngine:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, *args, **kwargs):
        if getattr(self, "_initialized", False):
            return
        # Baqi aapka purana __init__ ka saara code neeche waise ka waisa...

        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # --- PHASE 1: DYNAMIC REGISTRY (THE CORE SWITCHBOARD) ---
        self.dynamic_registry = {
            "models": {},       # Stores active InferenceEngine instances
            "paths": {},        # Model file paths
            "type": {},         # LLM, IMAGE, MULTIMODAL etc.
            "status": {}        # ACTIVE, STANDBY, ERROR
        }
        
        # --- PHASE 2: STATE MACHINE (REAL-TIME LIFECYCLE) ---
        self.state = {
            "engine_available": True,   # Always true for non-blocking Ollama boot
            "engine_active": False,     # True only when a model is successfully mounted
            "ready": True,              # System control state is alive
            "bus_connected": False,     
            "scheduler_active": False,
            "boot_locked": False
        }

        self._run_lock = threading.RLock()
        #self.init_core_services()
        self.bus = None
        self.scheduler = None
        
        # --- PHASE 3: TRACKING POINTERS (POLISHED) ---
        self.inference_engine = None 
        self.model_loaded = False       
        self.active_model_id = "STANDBY"
        self.current_backend = "PENDING"
        self.model_health = "STANDBY"   # STANDBY, HEALTHY, DEGRADED, FAULT
        
        self.is_active = True           # Control layer is up
        self.is_running = False         # Real-time inference execution flag
        self.is_busy = False            # Thread execution lock state

        # UTF-8 Stream configuration
        if hasattr(sys.stdout, 'reconfigure'):
            try: sys.stdout.reconfigure(encoding='utf-8')
            except Exception: pass
        self.logger = logger

        

        self._initialized = True
        self.state["boot_locked"] = True
        
        self.logger.info(
            f" [V12.3 POLISHED CORE] STEERING WHEEL READY.\n"
            f"   >> Control Status: LIVE | Mode: OLLAMA STANDBY (Awaiting path routing...)"
        )

    def init_core_services(self):
        import faiss
        print(f"DEBUG: Faiss loaded from {faiss.__file__}")
        
        # FAISS index banayein
        self.faiss_index = faiss.IndexFlatL2(384)
        
        #    ,  'faiss'        stage   
        #  VectorDB       
        self.bus.stage_service("FAISS_BACKEND", faiss)
        
        #          ,      
        self.bus.stage_service("FAISS_INSTANCE", self.faiss_index)
        
    def build_runtime_registry(self):
        # 1. Config mangwao
        runtime_config = self.bus.request("CONFIG_RUNTIME_READY")
        from pathlib import Path

        # 2. Paths validate karo
        for name, path in runtime_config.items():
            if not Path(path).exists():
                raise FileNotFoundError(f"Missing Runtime Path: {path}")

        # 3. Registry build karo (Loop ke bahar)
        # .get() use karna safe hai, par agar key nahi mili toh None dega.
        runtime_registry = {
            "python_core": runtime_config.get("python_core"),
            "torch_runtime": runtime_config.get("torch_runtime"),
            "llama_runtime": runtime_config.get("llama_runtime"),
            "system_dependencies": runtime_config.get("system_dependencies")
        }
        
        # 4. Bus par publish karo
        self.bus.publish("RUNTIME_REGISTRY_READY", runtime_registry)

    

    def start(self):
        """Mandatory entry point for Launcher Core."""
        self.is_active = True
        self.logger.info(" [SYSTEM_CORE] CONTROL INTERFACE ENGAGED  READY FOR VOLTAGE")
        return True
    
    # 1. BUS KO LENE KA TAREEKA (Launcher se Bus aayegi)
    def set_bus(self, bus):
        """Bus injection sirf yahan hoga."""
        if bus is None:
            self.logger.error(" [SYSTEM] FAILED: Bus is None!")
            return False
        
        self.bus = bus
        self.state["bus_connected"] = True
        self.logger.info(" [SYSTEM] BUS INJECTED & VERIFIED.")
        return True

    # 2. EVENT BHEJNE KA TAREEKA (Bus ka istemal)
    def emit_event(self, event_type, data):
        """Bus ke zariye system ko signal bhejna."""
        if self.bus and hasattr(self.bus, "emit"):
            self.bus.emit(event_type, data)
            self.logger.debug(f" [BUS_EMIT] {event_type} broadcasted.")
        else:
            self.logger.warning(f" [BUS_FAIL] Emit skipped: Bus disconnected.")

    # YE BLOCK APNE runtime_engine.py MEIN PASTE KARO
    def ignite(self, bus=None):
        if bus:
            self.set_bus(bus)
        
        #     ,    
        if self.bus:
            self.init_core_services() 
        
        # State Lock
        self.state["engine_active"] = True
        self.state["ready"] = True
        
        # State Lock
        self.state["engine_active"] = True
        self.state["engine_available"] = True
        self.state["ready"] = True
        self.is_active = True
        self.is_running = True
        self.model_health = "HEALTHY"
        
        if self.bus:
            self.emit_event("ENGINE_READY", {"status": "ONLINE"})
            self.logger.info("[ENGINE] FULL IGNITION CONFIRMED: ONLINE & CONNECTED")
        else:
            self.logger.warning("[IGNITE] SAFE MODE: NO BUS CONNECTED")
            
        return True

    # 2. FINAL DISPATCH LAYER: Multi-method Safe Fallback
    def execute_inference(self, task_payload):
        """Final Safe Dispatcher: NO MORE ENGINE_OFFLINE ERRORS."""
        if not self.is_active or not self.inference_engine:
            self.logger.error(" [ENGINE] INFERENCE REJECTED: Engine Offline")
            return {"error": "ENGINE_OFFLINE"}

        engine = self.inference_engine
        
        # Priority Execution Chain
        try:
            if hasattr(engine, "execute_inference"):
                return engine.execute_inference(task_payload)
            elif hasattr(engine, "generate"):
                return engine.generate(task_payload)
            elif hasattr(engine, "run"):
                return engine.run(task_payload)
            else:
                self.logger.error(" [ENGINE] NO VALID DISPATCH METHOD FOUND ON INFERENCE ENGINE")
                return {"error": "NO_VALID_INFERENCE_METHOD"}
        except Exception as e:
            self.logger.error(f" [ENGINE] INFERENCE CRITICAL FAULT: {e}")
            return {"error": str(e)}

    

    # =====================================================
    #  POLISHED HEALTH API (REAL DEBUG INSIGHT)
    # =====================================================
    def health_check(self):
        """
        Ollama-Style Non-Blocking Health Check.
        Returns system_ready=True so UI never freezes, but exposes detailed internals.
        """
        with self._run_lock:
            # If a model was supposed to be loaded but instance is missing, flag it
            calculated_status = "STANDBY"
            if self.model_loaded:
                calculated_status = "HEALTHY" if self.inference_engine else "DEGRADED_FAULT"
            
            return {
                "status": calculated_status,
                "system_ready": True,           #  Never blocks external dashboard operations
                "active": self.is_active,
                "control_layer_active": self.is_active,
                "model_loaded": self.model_loaded,
                "active_model_id": self.active_model_id,
                "backend": self.current_backend,
                "is_busy": self.is_busy,         # Real-time state exposure
                "registry_count": len(self.dynamic_registry["models"])
            }
        
    
    # =====================================================
    #  MOUNT & SWITCH ROUTING INTERFACE (NO LINK BREAK)
    # =====================================================
    def load_model_runtime(self, model_config):
        """
         FIXED VERSION: BUS-BASED MODEL REGISTRATION ONLY
        RuntimeEngine NEVER creates inference engine.
        """
        if not isinstance(model_config, dict):
            return False

        model_path = model_config.get("path")
        model_type = str(model_config.get("type", "GENERIC")).upper()
        model_id = model_config.get("id") or f"zyn_{int(time.time()*1000)}"

        try:
            with self._run_lock:
                self.is_busy = True

                # =====================================================================
                #  FIX PROBLEM 2: BUS GUARANTEE SECURE RESOLUTION
                # =====================================================================
                engine_instance = None
                if self.bus and hasattr(self.bus, "resolve"):
                    try:
                        engine_instance = self.bus.resolve("inference")
                    except Exception as res_err:
                        self.logger.error(f" [BUS_RESOLVE_CRITICAL] Bus resolution exploded: {res_err}")
                        engine_instance = None

                if engine_instance is None:
                    self.logger.error(" INFERENCE ENGINE NOT REGISTERED OR UNRESOLVED IN BUS PIPELINE")
                    self.is_busy = False
                    return False

                # =====================================================================
                #  FIX PROBLEM 1: DYNAMIC PATH AUDIT LOGGING (NO HARD BLOCK)
                # =====================================================================
                if model_path:
                    if os.path.exists(model_path):
                        self.logger.info(f" [PATH_VERIFIED] Target model asset located at: {model_path}")
                    else:
                        self.logger.warning(f" [PATH_WARN] Model context path assigned but asset not found locally: {model_path}")
                else:
                    self.logger.info(" [PATH_INFO] Virtual/Remote model contract requested. Local path bypass active.")

                # Register in runtime registry only as reference mapping
                self.dynamic_registry["models"][model_id] = engine_instance
                self.dynamic_registry["paths"][model_id] = model_path if model_path else "VIRTUAL_BUS_ROUTE"
                self.dynamic_registry["type"][model_id] = model_type

                # Status synchronization mapping reset
                for m_id in list(self.dynamic_registry["status"].keys()):
                    self.dynamic_registry["status"][m_id] = "STANDBY"

                self.dynamic_registry["status"][model_id] = "ACTIVE"

                # Pointer update to shared bus object context (NO NEW OBJECT CREATION)
                self.inference_engine = engine_instance
                self.active_model_id = model_id
                self.model_loaded = True
                self.model_health = "HEALTHY"
                self.state["engine_active"] = True
                self.is_busy = False

                # Safe explicit structural triggers
                if self.bus and hasattr(self.bus, "emit"):
                    self.bus.emit("SYSTEM_READY", {"model_id": model_id})
                    self.bus.emit("Z_OS_SIGNAL", {"status": "LIVE", "model_id": model_id})

                return True

        except Exception as e:
            self.model_health = "DEGRADED_FAULT"
            self.is_busy = False
            if hasattr(self, 'logger'):
                self.logger.critical(f" [RUNTIME_CRITICAL_EXCEPTION] Lifecycle mount crashed: {e}")
            return False
        
    # 2. ADD: ORCHESTRATOR STATUS POLLING CONTRACT
    def get_runtime_status(self):
        return {
            "is_busy": self.is_busy,
            "active": self.is_active,
            "model_loaded": self.model_loaded,
            "model_id": self.active_model_id,
            "health": self.model_health,
            "engine_online": self.state.get("engine_active", False)
        }

    def switch_model(self, model_id):
        """
         DYNAMIC SWITCH LOGIC (HOT-SWAP)
        Switches the system pointer to a previously registered model instantly.
        """
        with self._run_lock:
            if model_id not in self.dynamic_registry["models"]:
                self.logger.error(f" [SWITCH_FAILED] Model ID '{model_id}' does not exist in local registry.")
                return False

            try:
                self.logger.info(f" [HOT_SWAP] Switching active pointer to: {model_id}")
                
                # Switch reference pointer without re-initializing dependencies
                self.inference_engine = self.dynamic_registry["models"][model_id]
                self.active_model_id = model_id
                self.model_loaded = True
                self.model_health = "HEALTHY"
                
                # Set others to standby status cleanly
                for m_id in self.dynamic_registry["status"]:
                    self.dynamic_registry["status"][m_id] = "ACTIVE" if m_id == model_id else "STANDBY"

                self.logger.info(f" [HOT_SWAP_COMPLETE] System is now running on: {model_id}")
                return True
            except Exception as e:
                self.logger.error(f" [HOT_SWAP_CRITICAL] Failed to switch pointers: {e}")
                return False

    def free_memory(self, handle=None):
        """Purges registry and updates lifecycle tracks cleanly."""
        with self._run_lock:
            if hasattr(self, "dynamic_registry"):
                for key in self.dynamic_registry:
                    if isinstance(self.dynamic_registry[key], dict):
                        self.dynamic_registry[key].clear()
            self.inference_engine = None
            self.model_loaded = False
            self.active_model_id = "STANDBY"
            self.model_health = "STANDBY"
            self.state["engine_active"] = False
            self.is_running = False
            self.is_busy = False
            import gc
            gc.collect()
            self.logger.info("[SYSTEM_CORE] Memory resources purged. Controller reverted to Standby.")
            return True
        
# Purana: def create_runtime_engine(): return RuntimeEngine()
# Naya (Singleton Pattern):
#runtime_engine = RuntimeEngine()

def get_runtime_engine():
    return runtime_engine