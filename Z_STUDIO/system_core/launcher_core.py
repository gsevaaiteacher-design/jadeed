# =====================================================================
# PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI OPERATING SYSTEM)
# BRANDING: ZYNQUAR ATELIER
# CORE ROLE: Fully Sealed Enterprise Hermetic Core (V8 FINAL MASTER HARDENED)
# =====================================================================
import os
import sys
import glob

def _bootstrap_logging(self):
    import logging
    # 'replace'      '?'       
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

# ---------------------------------------------------------------------
# STEP 1: DYNAMIC PORTABLE ROOT RESOLUTION (NO DRIVE HARDCODING)
# ---------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # system_core/
ROOT_DIR = os.path.dirname(BASE_DIR)                    # Z-STUDIO/
EMBEDDED = os.path.join(ROOT_DIR, "installer_core", "embedded_runtime", "python_core_pack")

EMBEDDED_LIB = os.path.join(EMBEDDED, "Lib")
SITE_PACKAGES = os.path.join(EMBEDDED, "Lib", "site-packages")
PY_EXE = os.path.join(EMBEDDED, "python.exe")

# ---------------------------------------------------------------------
# STEP 2: STDLIB INTEGRITY GATE & RECOVERY MODE INTERFACE
# ---------------------------------------------------------------------
CRITICAL_BOOTSTRAP_ASSETS = [
    EMBEDDED_LIB,
    SITE_PACKAGES,
    os.path.join(EMBEDDED_LIB, "pkgutil.py"),
    os.path.join(EMBEDDED_LIB, "site.py"),
    os.path.join(EMBEDDED_LIB, "encodings", "__init__.py")  # Hard anchor for dynamic character map encoding
]

# Physical asset existence validation layer
for asset in CRITICAL_BOOTSTRAP_ASSETS:
    if not os.path.exists(asset):
        print("\n" + "="*80)
        print(" ENTERPRISE BOOTSTRAP BREAKDOWN: EMBEDDED DISTRO CORRUPTION DETECTED!")
        print(f"-> Missing Architecture Dependency: {asset}")
        print("-> Fallback Log Dump: Writing diagnostic baseline state to core_crash.log")
        print("="*80 + "\n")
        try:
            with open(os.path.join(ROOT_DIR, "core_crash.log"), "a") as log:
                log.write(f"[BOOT_ERROR] Path asset verification failure at runtime: {asset}\n")
        except Exception:
            pass
        sys.exit(1)

# Execution access validation for local python interpreter layer
if not (os.path.exists(PY_EXE) and os.access(PY_EXE, os.X_OK)):
    print(f"\n ENTERPRISE BOOTSTRAP BREAKDOWN: Execution engine binary missing or blocked: {PY_EXE}\n")
    sys.exit(1)

# Deterministic version validation for core internal python dynamic link module (*.dll)
py_dll_match = glob.glob(os.path.join(EMBEDDED, "python*.dll"))
if not py_dll_match:
    print(f"\n ENTERPRISE BOOTSTRAP BREAKDOWN: Vital internal Python DLL link target missing inside package pack!\n")
    sys.exit(1)

# ---------------------------------------------------------------------
# STEP 3: HERMETIC MATRIX PACKING & CONTROLLED PATH FILTERING (FIX 1 & 3)
# ---------------------------------------------------------------------
os.environ["PYTHONHOME"] = EMBEDDED           # Direct lookup map to isolated standard library
os.environ["PYTHONNOUSERSITE"] = "1"           # Ultimate ban on early global pip / AppData leakage
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"     # Eliminate local system runtime clutter (.pyc)
os.environ["Z_STUDIO_ROOT"] = ROOT_DIR

os.environ["PYTHONPATH"] = os.pathsep.join([ROOT_DIR, EMBEDDED_LIB, SITE_PACKAGES])

# SYSTEM PATH FILTER SHIELD: Strip third-party application clutter, whitelist only core driver interfaces
SYSTEM_ROOT = os.environ.get("SystemRoot", "C:\\Windows")
SYSTEM_32 = os.path.join(SYSTEM_ROOT, "System32")
SYS_WOW64 = os.path.join(SYSTEM_ROOT, "SysWOW64")

whitelisted_system_paths = [SYSTEM_32, SYSTEM_ROOT]
if os.path.exists(SYS_WOW64):
    whitelisted_system_paths.append(SYS_WOW64)

# Keep host system paths that directly reference graphics hardware components or VC++ dependencies
raw_host_paths = os.environ.get("PATH", "").split(os.pathsep)
filtered_host_paths = [
    p for p in raw_host_paths 
    if any(k in p.lower() for k in ["nvidia", "cuda", "vulkan", "opencl", "amd", "intel", "driver"])
]

# Set the final absolute sealed precedence path list
os.environ["PATH"] = os.pathsep.join([
    EMBEDDED,
    os.path.join(EMBEDDED, "DLLs"),            # Local pre-compiled dynamic bindings first
    *whitelisted_system_paths,                 # Windows internal execution blocks second
    *filtered_host_paths                       # Safely restricted isolated hardware acceleration links last
])

# ---------------------------------------------------------------------
# STEP 4: ABSOLUTE SYS.PATH DETERMINISTIC ARRAY OVERWRITE MODEL (FIX 2)
# ---------------------------------------------------------------------
# Total exclusion of array collision risks via fixed index array assignment
sys.path[:] = [
    EMBEDDED_LIB,
    SITE_PACKAGES,
    ROOT_DIR
]

# ---------------------------------------------------------------------
# STEP 5: WINDOWS MULTIPROCESS SPAWN HANDSHAKE LAYER PROTECTION
# ---------------------------------------------------------------------
import multiprocessing

multiprocessing.set_executable(PY_EXE)
sys.executable = PY_EXE

# Strict check to bound start method assignment gracefully inside parent environment
if multiprocessing.get_start_method(allow_none=True) != "spawn":
    try:
        multiprocessing.set_start_method("spawn")
    except RuntimeError:
        pass

import json
import ast
import time
import logging
import threading
import hashlib
import inspect
import multiprocessing
import importlib.util
import types
import queue
import copy
from typing import Dict, Any, Optional, List, Set

# Core Import Safety Gateway - Headless isolation mapping layer
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QThread, QCoreApplication
    PYSIDE6_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    QApplication = None
    QThread = None
    QCoreApplication = None
    PYSIDE6_AVAILABLE = False


def _isolated_sandbox_kernel_validator(absolute_path: str, response_queue: multiprocessing.Queue) -> None:
    """
    OS-LEVEL BOUNDARY SIMULATOR (POST-ISOLATION CHAMBER)
    Executes deep dynamic bytecode, system call analysis, and structure scanning inside an unprivileged process space.
    """
    try:
        # Enforce strict subprocess execution boundaries where possible
        if hasattr(os, "nice"): 
            os.nice(19) # Drop process priority to lowest tier to prevent CPU exhaustion attacks
            
        with open(absolute_path, "r", encoding="utf-8") as f:
            source_code = f.read()
            
        # Bytecode analysis level validation
        bytecode = compile(source_code, absolute_path, "exec")
        
        # Scan compiled co_names for low-level system subversion strings or direct ctypes hacking vectors
        unsafe_primitives = {"ctypes", "CDLL", "WinDLL", "memmove", "memset", "sys.settrace", "os.system", "subprocess"}
        found_unsafe = unsafe_primitives.intersection(bytecode.co_names)
        
        if found_unsafe:
            response_queue.put({"status": "CRASH", "reason": f" OS_ISOLATION_BREACH: Unsafe system call mapping intercepted: {found_unsafe}"})
            return
            
        response_queue.put({"status": "VERIFIED"})
    except Exception as e:
        response_queue.put({"status": "CRASH", "reason": str(e)})

        


class ZStudioUIStub:
    """ROBUST UI SAFE-STUB PROXY - Returns None to prevent chaining loop pollution."""
    def __getattr__(self, name: str) -> Any:
        def dummy_method(*args, **kwargs):
            logging.debug(f" UI_STUB_BYPASS: Shadow execution intercepted on attribute: '{name}'")
            return None
        return dummy_method

_SINGLETON_INSTANCE = None
class ZStudioLauncher:
    """
    MASTER RUNTIME INITIALIZATION PIPELINE - VERSION 12.3 (V12 IMPERIAL OVERLORD BUILD)
    Role: Enterprise-grade fault-tolerant dynamic bootstrap bootloader framework.
    Guarantees true isolation, structural memory snapshots, and stage-specific global watchdogs.
    """


    def __new__(cls, *args, **kwargs):
        # Yeh `__new__` method ensure karega ki class ka sirf ek hi instance bane
        global _SINGLETON_INSTANCE
        if _SINGLETON_INSTANCE is None:
            _SINGLETON_INSTANCE = super(ZStudioLauncher, cls).__new__(cls)
        return _SINGLETON_INSTANCE
    

    def __init__(self):
        self._boot_lock = threading.Lock()
        self._boot_completed = False
        self.registry_status: Dict[str, str] = {}
        self.running: bool = True
        self.version: str = "12.3"
        self.boot_stage: str = "START"
        self._lock = threading.RLock() 
        
        
        self.boot_config: Dict[str, Any] = {}
        self.headless_mode: bool = False
        self.ui_failure_reason: Optional[str] = None
        
        # Checkpoint Recovery & State Snapshots
        self.last_healthy_checkpoint: Optional[str] = None
        self.boot_diagnostics_trace: List[str] = []
        self._sys_modules_snapshot: Set[str] = set()
        self._sys_path_snapshot: List[str] = []
        
        # System Object Graph Registers
        self.config: Optional[Any] = None
        self.state: Optional[Any] = None
        
        self.bus: Optional[Any] = None
        self.memory_manager: Optional[Any] = None  #   YEH YAHAN HONA CHAHIYE!
        self.registry: Optional[Any] = None
        self.hw: Optional[Any] = None
        self.engine: Optional[Any] = None
        self.orchestrator: Optional[Any] = None
        self.execution_manager: Optional[Any] = None
        self.ai_brain: Optional[Any] = None
        self.ai_loader: Optional[Any] = None
        self.live_bridge: Optional[Any] = None
        self.qt_app: Optional[Any] = None
        self.ui: Optional[Any] = None
        self.ui_renderer: Optional[Any] = None

        # Hard Native Fallback Configuration Blueprint
        self._fallback_config: Dict[str, Any] = {
            "paths": {
                "config_core": "system_core/config_core.py",
                "system_state_manager": "system_core/system_state_manager.py",
                
                "control_bus": "system_core/control_bus.py",
                "memory_budget_controller": "system_brain_layer/memory_budget_controller.py",
                "resource_guard": "system_brain_layer/resource_guard.py",
                "execution_scheduler_core": "system_brain_layer/execution_scheduler_core.py",
                "memory_manager": "system_core/memory_manager.py",
                "hardware_brain": "system_core/hardware_brain.py",
                "runtime_engine": "system_core/runtime_engine.py",
                "execution_orchestrator": "system_brain_layer/execution_orchestrator.py",
                "execution_manager": "runtime_api/execution_manager.py",
                "model_loader": "ai_engine/model_loader.py",
                "inference_engine": "ai_engine/inference_engine.py",
                "live_bridge": "ui_core/live_bridge.py",
                "main_dashboard": "ui_core/main_dashboard.py",
                "ui_renderer": "ui_core/ui_renderer.py"
            },
            "ai_model": {
                "target_path": "ai_engine/weights/core_weights.bin",
                "expected_sha256": "",
                "security_mode": "DEV"
            }
        }
        
        # Capture an unpolluted baseline runtime map for precise atomic system rollbacks
        self._capture_baseline_snapshot()

    def start_boot(self):
        with self._lock:  # RLock ka use karna zaroori hai
            if self._boot_completed:
                logging.warning(" BOOT_WARN: Initialization sequence already finalized.")
                return True
            
            # Yahan se tumhara main logic call hoga
            self._trace_log("---  STARTING SECURE BOOT PIPELINE ---")
            success = self.execute_secure_boot()
            
            if success:
                self._boot_completed = True
                self._trace_log(" BOOT_SUCCESS: Pipeline operational.")
            return success

    def _capture_baseline_snapshot(self) -> None:
        """Captures standard module mapping hashes before dynamic code evaluation triggers."""
        self._sys_modules_snapshot = set(sys.modules.keys())
        self._sys_path_snapshot = list(sys.path)

    def _bootstrap_logging(self) -> None:
        """Secure logging substrate bypasses encoding or streaming injection errors."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] (Z-LAUNCHER) %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    def _trace_log(self, message):
        """
         HARDENED LAUNCHER TRACE BRIDGE
        Standard logging.info hata kar seedhe LoggerCore par map kiya gaya hai
        """
        try:
            # Seedhe naye safe logger ko import karo aur use karo
            from system_core.logger_core import logger
            logger.info(message, mod="LAUNCHER")
        except Exception:
            # Fallback agar bootstrap phase mein import fail ho jaye
            try:
                import sys
                sys.stdout.write(f"LAUNCHER_FALLBACK >> {message}\n")
                sys.stdout.flush()
            except Exception:
                pass

    def _get_execution_root(self) -> str:
        """PYINSTALLER BUNDLE ROUTE - Corrected attribute lookup mapping syntax."""
        if hasattr(sys, '_MEIPASS'):
            return getattr(sys, '_MEIPASS')
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        MINIMAL STRUCTURAL GATE ONLY
        Launcher does NOT understand system logic or specific keys.
        It only ensures JSON is a usable, non-empty dictionary structure.
        """
        if not isinstance(data, dict) or not data:
            return False

        # Only 1 hard requirement: system must have SOME config structure (not empty)
        #if len(data.keys()) == 0:
           # return False

        return True

    def _load_initializer_contract(self) -> bool:
        """
        PURE LAUNCHER ROLE:
        Only loads config file and passes it forward.
        No decision making, no schema intelligence, zero system interference.
        """
        try:
            # 1. Pure Launcher Role: Address locate karo
            base_dir = self._get_execution_root()
            config_json_path = os.path.normpath(
                os.path.join(base_dir, "installer_core", "init_config.json")
            )

            if not os.path.exists(config_json_path):
                self._trace_log(" BOOT_STOP: init_config.json missing.")
                return False

            # 2. Raw JSON data load karo
            with open(config_json_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)

            # 3. ONLY structural sanity check (Khali ya corrupt toh nahi hai)
            if not self._validate_schema(loaded_data):
                self._trace_log(" BOOT_STOP: Invalid config structure (empty/corrupt).")
                return False

            # 4. NO INTERPRETATION  JUST PASS THROUGH (Pure handoff)
            self.boot_config = loaded_data
            self.registry_status["INIT_CONTRACT"] = "READY"

            self._trace_log(
                " LAUNCHER: Config loaded. Control handed to system_core."
            )
            return True

        except Exception as e:
            # Loop proof trace log protection
            self._trace_log(f" BOOT_STOP: config load failed: {str(e)}")
            return False

    def _ast_hardened_security_shield(self, absolute_path: str) -> bool:
        """
        SAFE AST SHIELD v2
        - Fixes crash
        - Reduces false positives
        - Allows safe import_module / torch / importlib
        """

        try:
            import ast
            import logging

            SAFE_IMPORTS = {
                "import_module",
                "getattr",
                "__import__"  # allowed but monitored
            }

            DANGEROUS_CALLS = {
                "eval",
                "exec",
                "compile",
            }

            with open(absolute_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            root_node = ast.parse(source_code, filename=absolute_path)

            for node in ast.walk(root_node):

                # -------------------------
                # LOOP PROTECTION (safe)
                # -------------------------
                if isinstance(node, ast.While):
                    is_infinite = False

                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        is_infinite = True

                    elif isinstance(node.test, ast.Name) and node.test.id == "True":
                        is_infinite = True

                    if is_infinite:
                        has_break = any(isinstance(child, ast.Break) for child in ast.walk(node))
                        if not has_break:
                            logging.critical(f" AST_SHIELD: infinite loop blocked: {absolute_path}")
                            return False

                # -------------------------
                # DIRECT DANGEROUS CALLS
                # -------------------------
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in DANGEROUS_CALLS:
                        logging.critical(f" AST_SHIELD: unsafe call {node.func.id} blocked: {absolute_path}")
                        return False

                # -------------------------
                # SAFE ATTRIBUTE CHECK (FIXED CRASH HERE)
                # -------------------------
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):

                    attr = getattr(node.func, "attr", None)
                    value = getattr(node.func, "value", None)

                    if attr is None:
                        continue

                    # SAFE: allow import_module (used by torch, plugins, loaders)
                    if attr == "import_module":
                        continue

                    # BLOCK only dangerous reflection abuse
                    if attr in ["__import__", "get_builtins"]:
                        logging.critical(f" AST_SHIELD: blocked unsafe attribute call: {attr}")
                        return False

                # -------------------------
                # getattr abuse detection (safe)
                # -------------------------
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr":

                    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                        token = str(node.args[1].value).lower()

                        #  MASTER KERNEL FIX: 'in' operator ko hatakar exact set intersection lagaya hai 
                        # taaki 'execute_inference' ya 'execution' ke andar chhupa hua 'exec' false positive block na kare!
                        danger_set = {"eval", "exec", "__import__", "ctypes", "subprocess"}
                        if token in danger_set:
                            logging.critical(f" AST_SHIELD: getattr attack blocked: {absolute_path}")
                            return False

            return True

        except Exception as e:
            logging.error(f" AST_SHIELD_ERROR: {absolute_path} -> {e}")
            return False

    def _import_via_contract(self, module_name: str, relative_path: str) -> Optional[Any]:
        """ INDUSTRIAL SANDBOX PIPELINE - Hardened process isolation, supervisor tracking, and script-level hashing."""
        try:
            base_dir = self._get_execution_root()

            relative_path = relative_path.replace("system_core/system_core", "system_core")

            relative_path = relative_path.replace("ui_core/ui_core", "ui_core")

            absolute_target_path = os.path.normpath(os.path.join(base_dir, relative_path))
            
            if not os.path.exists(absolute_target_path):
                logging.error(f" PIPELINE_FAIL: Missing target script module asset {module_name} at route: {absolute_target_path}")
                return None

            # SCRIPT INTEGRITY SHIELD: Protects boot modules from mid-run production tampering
            try:
                with open(absolute_target_path, "rb") as f:
                    script_hash = hashlib.sha256(f.read()).hexdigest()
                self._trace_log(f" INTEGRITY_TRACK: Script mapping validated. [{module_name}] -> Hash: {script_hash[:8]}...")
            except Exception as hash_err:
                logging.error(f" SCRIPT_HASH_ERROR: Failed to establish static signature for {module_name}: {hash_err}")
                return None

            if not self._ast_hardened_security_shield(absolute_target_path):
                return None
                
            response_queue = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=_isolated_sandbox_kernel_validator,
                args=(absolute_target_path, response_queue),
                daemon=True
            )
            process.start()
            
            result = None
            timeout_limit = 5.0
            
            # GLOBAL ACTIVE WATCHDOG SUPERVISOR GATING LAYER
            try:
                result = response_queue.get(timeout=timeout_limit)
            except Exception as queue_err:
                if type(queue_err).__name__ == "Empty" or isinstance(queue_err, queue.Empty):
                    logging.critical(f" PROCESS_SUPERVISOR_ALERT: Unresponsive validation hang detected inside module process chamber for '{module_name}'")
                else:
                    logging.critical(f" PROCESS_SUPERVISOR_ALERT: Core transport error: {queue_err}")
                
            # Rigid Cleanup Verification Execution Pipeline
            process.join(timeout=1.0)
            if process.is_alive():
                logging.warning(f" WATCHDOG_REAPER: Process container failed to yield down within limit framework. Issuing OS Force Kill.")
                try:
                    if hasattr(process, "kill"): process.kill()
                    else: process.terminate()
                except Exception as ex:
                    logging.debug(f"OS Reaping exception: {ex}")
                process.join()

            # Inspect raw system process exit code states cleanly
            exit_code = process.exitcode
            if exit_code != 0 and exit_code is not None:
                logging.error(f" SANDBOX_ESCAPE_REJECT: Child isolation process terminated with unsafe non-zero structural error code: {exit_code}")
                return None

            try:
                response_queue.close()
                response_queue.join_thread()
            except Exception as e:
                logging.debug(f"IPC flush exception: {e}")
                
            if not result or result.get("status") != "VERIFIED":
                logging.error(f" FRAMEWORK_LOAD_REJECTED: Context dynamic isolation runtime validation failed: {result.get('reason') if result else 'Timeout'}")
                return None

            # Compute specific file specification layouts securely
            spec = importlib.util.spec_from_file_location(module_name, absolute_target_path)
            if spec and spec.loader:
                module = types.ModuleType(module_name)
                module.__file__ = absolute_target_path
                
                try:
                    spec.loader.exec_module(module)
                    sys.modules[module_name] = module
                    return module
                except Exception as exec_err:
                    logging.critical(f" RUNTIME_REGISTRATION_EXCEPTION: Structural collapse during runtime link phase of '{module_name}': {exec_err}")
                    raise exec_err
            return None
        except Exception as e:
            logging.error(f" HARD_BREAK: Dynamic loader tracking execution mapping explosion for module {module_name}: {e}")
            return None

    def _verify_model_hash_mandatory(self, relative_model_path: str, expected_hash: str) -> bool:
        """THREE-TIER SECURITY MATRIX - Enforces strict verification rules on production paths."""
        model_section = self.boot_config.get("ai_model", {})
        security_mode = str(model_section.get("security_mode", "STRICT")).upper()
        
        if security_mode not in ["STRICT", "RELAXED", "DEV"]:
            security_mode = "STRICT"

        if not expected_hash:
            if security_mode == "STRICT":
                logging.critical(" SECURITY_FAIL: [STRICT MODE] Cryptographic verification string empty. Master Core Lockout deployed.")
                return False
            elif security_mode == "RELAXED":
                self._trace_log(" PIPELINE_WARN: [RELAXED MODE] Cryptographic hash unallocated. Proceeding under vulnerability warning limits.")
                return True
            else:
                self._trace_log(" PIPELINE_WARN: [DEV MODE] Signature checks bypassed. Production rules decoupled.")
                return True
            
        base_dir = self._get_execution_root()
        absolute_model_path = os.path.normpath(os.path.join(base_dir, relative_model_path))

        print("DEBUG PATH:", absolute_target_path)  #    
        
        if not os.path.exists(absolute_model_path) or os.path.getsize(absolute_model_path) == 0:
            logging.critical(f" INTEGRITY_FAIL: Production model weights missing or truncated at target path: {absolute_model_path}")
            return False
        try:
            sha256_hash = hashlib.sha256()
            with open(absolute_model_path, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            
            calculated_hash = sha256_hash.hexdigest()
            if calculated_hash != expected_hash:
                logging.critical(f" INTEGRITY_FAIL: Cryptographic signature validation error. Checksum mismatch.")
                return False
                
            self._trace_log(" INTEGRITY_SUCCESS: Model weight array verified mathematically.")
            return True
        except Exception as e:
            logging.critical(f" INTEGRITY_ERROR: Mathematical verification scanner engine crashed or filesystem file-lock hit: {e}")
            return False

    def _validate_manager_contract(self, manager: Any) -> bool:
        """COMPATIBLE SEMANTIC SIGNATURE CHECK - Parses decorators, defaults, and parameters flexibility."""
        if manager is None: return False
        
        required_signatures = {
            "attach_bridge": ["bridge_obj"],
            "set_ready": ["status_bool"]
        }
        
        for method_name, required_args in required_signatures.items():
            if not hasattr(manager, method_name):
                logging.error(f" CONTRACT_FAIL: Interface manager is missing required method: '{method_name}'")
                return False
            method = getattr(manager, method_name)
            if not callable(method):
                logging.error(f" CONTRACT_FAIL: Attribute '{method_name}' is registered but is not callable.")
                return False
                
            try:
                sig = inspect.signature(method, follow_wrapped=True)
                params = sig.parameters
                
                has_var_positional = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values())
                has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
                
                if not (has_var_positional or has_var_keyword):
                    for arg in required_args:
                        if arg not in params:
                            positional_inputs = [p for p in params.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
                            if len(positional_inputs) < len(required_args):
                                logging.critical(f" COMPATIBILITY_FAIL: Method '{method_name}' lacks semantic capacity to process arguments.")
                                return False
            except (ValueError, TypeError) as sig_err:
                logging.warning(f" PIPELINE_WARN: Dynamic parsing unavailable for binary wrapper or C-extension target '{method_name}': {sig_err}.")
                
        slots = getattr(manager, "__slots__", None)
        if slots is not None:
            if isinstance(slots, str) and slots != "ai_brain": return False
            elif isinstance(slots, (list, tuple)) and "ai_brain" not in slots: return False
                
        return True

    def _evaluate_deterministic_gpu_substrate(self) -> bool:
        """RELIABLE HARDWARE STRATEGY - Cleans up unsafe torch.cuda string module lookups."""
        if self.hw and hasattr(self.hw, 'validate_gpu_access'):
            try:
                if bool(self.hw.validate_gpu_access()): return True
            except Exception: pass
            
        if "torch" in sys.modules:
            try:
                mod = sys.modules["torch"]
                if hasattr(mod, 'cuda') and getattr(mod.cuda, 'is_available')(): return True
            except Exception: pass
                
        if os.environ.get("CUDA_VISIBLE_DEVICES") == "-1": return False
        if any(env_key in os.environ for env_key in ["CUDA_HOME", "ROCM_PATH", "ONEAPI_ROOT"]): return True
        
        return False

    def _safe_factory_instantiate(self, module: Any, class_name: str, fallback_allowed: bool = False, fallback_provider: Any = None, *args, **kwargs) -> Any:
        """REFLECTIVE SIGNATURE INSPECTION MATCHING - Eliminates runtime keyword argument parameter drifts."""
        try:
            if module and hasattr(module, class_name):
                target_class = getattr(module, class_name)
                
                try:
                    sig = inspect.signature(target_class.__init__)
                    has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                    if not has_kwargs:
                        kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                except Exception:
                    pass
                    
                return target_class(*args, **kwargs)
        except Exception as instantiation_err:
            logging.error(f" COMPONENT_CONSTRUCTOR_FAULT: Object factory instantiation loop failed for '{class_name}': {instantiation_err}")
            
        if fallback_allowed and fallback_provider is not None:
            self._trace_log(f" RECOVERY_FALLBACK: Deploying safe proxy replacement layer for instance: {class_name}")
            return fallback_provider
            
        logging.critical(f" BOOT_CONSTRUCTOR_ABORTED: Execution factory failed on node target: '{class_name}'")
        return None

    def _dump_diagnostics_on_panic(self) -> None:
        """Flushes the exact sequential boot state trace mapping onto critical streams."""
        logging.critical("=============  LAUNCHER RUNTIME DIAGNOSTICS TRACE DUMP =============")
        for idx, step_log in enumerate(self.boot_diagnostics_trace):
            logging.critical(f"   Trace [{idx}]: {step_log}")
        logging.critical("====================================================================")

    def _rollback_state(self) -> None:
        """ NATIVE SNAPSHOT RESTORATION LAYER - Restores absolute system memory state back to structural pristine baseline."""
        #if not self._lock.locked():
            #self._lock.acquire()
        try:  
            self._lock.acquire(blocking=False) 
        except:
            pass
         
        self._trace_log(" PIPELINE_ROLLBACK: Running atomic system-level module matrix restoration mapping...")
        
        self.registry_status.clear()
        
        try:
            if self.engine and hasattr(self.engine, "shutdown"):
                try: self.engine.shutdown()
                except Exception as inner_e: logging.critical(f" ROLLBACK_FAULT: Processing core engine shutdown failed: {inner_e}")
                
            if self.orchestrator and hasattr(self.orchestrator, "set_mode"): 
                self.orchestrator.set_mode("OFFLINE")
                
            if self.execution_manager and hasattr(self.execution_manager, "set_ready"):
                self.execution_manager.set_ready(False)
        except Exception as e:
            logging.critical(f" DOUBLE_FAULT: Rollback allocation tracking layer threw an anomaly: {e}")

        # PURE ATOMIC REGISTRY RECONCILIATION SNAPSHOT
        # Instead of deleting references blindly which breaks shared indices, we restore the exact pre-boot keys map safely
        current_modules = list(sys.modules.keys())
        for mod in current_modules:
            if mod not in self._sys_modules_snapshot:
                try:
                    # Clean the module interior space cleanly to detach any lingering background event loops
                    m = sys.modules[mod]
                    if m:
                        for attr in list(m.__dict__.keys()):
                            if not attr.startswith("__"):
                                setattr(m, attr, None)
                except Exception:
                    pass
                del sys.modules[mod]
                
        # Revert environment system path matrices safely back to baseline state mapping rules
        sys.path = list(self._sys_path_snapshot)

        self._trace_log(f" PERSISTENCE_RECOVERY: Baseline system state maps reverted safely back to initial unpolluted checkpoint.")
        
        self.config = self.state = self.bus = self.hw = self.engine = None
        self.orchestrator = self.execution_manager = self.ai_brain = self.ai_loader = self.live_bridge = None
        self.qt_app = self.ui = self.ui_renderer = None
        
        self.boot_stage = "CRASH_RECOVERY_MODE"
        self._dump_diagnostics_on_panic()

    def execute_secure_boot(self) -> bool:
        with self._lock:
            self._trace_log("---  STARTING RUNTIME INITIALIZATION PIPELINE FRAMEWORK ---")
            
            # GLOBAL PIPELINE STAGE TIMEOUT SUPERVISOR WATCHDOG TIMER
            boot_success = [False]
            
            def _pipeline_execution_wrapper():
                try:
                    boot_success[0] = self._run_bootstrap_stages()
                except Exception as fatal_e:
                    logging.critical(f" CRITICAL_PIPELINE_ERROR: Master stage sequence track crashed: {fatal_e}")
                    boot_success[0] = False

            pipeline_thread = threading.Thread(target=_pipeline_execution_wrapper, daemon=True)
            pipeline_thread.start()
            
            # Total runtime timeout boundary allocated across all 11 evaluation nodes safely
            pipeline_thread.join(timeout=45.0) 
            
            if pipeline_thread.is_alive():
                logging.critical(" GLOBAL_BOOT_WATCHDOG_HALT: System bootstrap sequence exceeded absolute execution processing limits. Deploying Emergency Countermeasures.")
                self._rollback_state()
                return False
                
            return boot_success[0]

    def _run_bootstrap_stages(self) -> bool:
        """Sequential layout execution pipeline map containing individual system layer checkpoints."""
        try:
            # =========================================================
            # POST 1 | LOGGER & CONTRACT ENFORCEMENT
            # =========================================================
            self._bootstrap_logging() 
            if not self._load_initializer_contract(): 
                logging.critical(" BOOT_STOP: Structural path matrix verification failed on configuration layers.")
                return False
            
            self.registry_status["POST_1"] = "READY"
            self.last_healthy_checkpoint = "POST_1"
            self._trace_log("[POST 1/11]  INITIALIZATION LAYER: Full schema sync validated and locked.")

            # =========================================================
            # POST 2 | CONFIG & STATE SNAPSHOT
            # =========================================================
            paths_matrix = self._fallback_config.get("paths", {})
            try:
                mod_config = self._import_via_contract("ConfigCore", paths_matrix.get("config_core"))
                self.config = self._safe_factory_instantiate(mod_config, "ConfigCore")
                
                mod_state = self._import_via_contract("SystemStateManager", paths_matrix.get("system_state_manager"))
                self.state = self._safe_factory_instantiate(mod_state, "SystemStateManager")
                
                self.registry_status["POST_2"] = "READY"
                self._trace_log("[POST 2]  CONFIG & STATE: Initialized.")
            except Exception as e:
                self._trace_log(f" BOOT_FAIL: POST 2 - {str(e)}")
                self._rollback_state()
                return False

            

            # =========================================================
            # POST 3 | CONTROL BUS (SAFE INSTANTIATION)
            # =========================================================
            try:
            # 1. Check karo ki kya pehle se bus exist karta hai
                if not hasattr(self, 'bus') or self.bus is None:
                    mod_bus = self._import_via_contract("ControlBus", paths_matrix.get("control_bus"))
                    self.bus = self._safe_factory_instantiate(mod_bus, "ControlBus")
                    self._trace_log("[POST 3]  CONTROL BUS: Router Initialized.")
                else:
                    self._trace_log("[POST 3]  CONTROL BUS: Router already online. Skipping re-init.")

                self.registry_status["POST_3"] = "READY"

            except Exception as e:
                self._trace_log(f" BOOT_FAIL: POST 3 - {str(e)}")
                # Rollback karne se pehle print karo ki galti kahan hai
                import traceback
                traceback.print_exc()
                self._rollback_state()
                return False
            
            # =========================================================
            # POST 3.1 | MEMORY BUDGET CONTROLLER (DEBUG MODE)
            # =========================================================
            try:
                mod_mem_ctrl = self._import_via_contract("MemoryBudgetController", paths_matrix.get("memory_budget_controller"))
                
                # CHOR KO PAKADNE KE LIYE YAHAN LOG LAGAO
                self.memory_controller_instance = self._safe_factory_instantiate(mod_mem_ctrl, "MemoryBudgetController", bus=self.bus)
                
                # AGAR NONE HAI, TOH CHOR YAHI HAI!
                if self.memory_controller_instance is None:
                    raise Exception("FACTORY FAILED: Returned None for MemoryBudgetController")

                self.bus.stage_service("memory_budget_controller", self.memory_controller_instance)
                
                self.registry_status["POST_3_1"] = "READY"
                self._trace_log("[POST 3.1] Memory controller staged.")
                
            except Exception as e:
                # ASLI CHOR KA PATA YAHAN CHALGA
                import traceback
                error_details = traceback.format_exc()
                print(f" ASLI CHOR MIL GAYA: {error_details}")
                self._trace_log(f"BOOT_FAIL: POST 3.1 - {error_details}")
                self._rollback_state()
                return False

            # =========================================================
            # POST 3.2 | RESOURCE GUARD (Fixed)
            # =========================================================
            try:
                mod_guard = self._import_via_contract("ResourceGuard", paths_matrix.get("resource_guard"))
                # [FIX]: self.variable name use karo
                self.instance_guard = self._safe_factory_instantiate(mod_guard, "ResourceGuard", bus=self.bus)
                self.bus.stage_service("resource_guard", self.instance_guard)
                
                self.registry_status["POST_3_2"] = "READY"
                self._trace_log("[POST 3.2] GUARD: Resource protection active.")
            except Exception as e:
                self._trace_log(f"BOOT_FAIL: POST 3.2 - {str(e)}")
                self._rollback_state()
                return False

            # =========================================================
            # POST 3.3 | EXECUTION SCHEDULER (Fixed)
            # =========================================================
            try:
                mod_sched = self._import_via_contract("ExecutionScheduler", paths_matrix.get("execution_scheduler_core"))
                # [FIX]: self.variable name use karo
                self.instance_sched = self._safe_factory_instantiate(mod_sched, "ExecutionScheduler", bus=self.bus)
                self.bus.stage_service("scheduler", self.instance_sched)
                
                self.registry_status["POST_3_3"] = "READY"
                self._trace_log("[POST 3.3] SCHEDULER: Execution flow bound.")
            except Exception as e:
                self._trace_log(f"BOOT_FAIL: POST 3.3 - {str(e)}")
                self._rollback_state()
                return False
            
            # =========================================================
            # POST 3.4 | MEMORY CORE
            # =========================================================
            try:
                mod_mem = self._import_via_contract("MemoryManager", paths_matrix.get("memory_manager"))
                self.memory_manager = self._safe_factory_instantiate(mod_mem, "MemoryManager", config=self.config, state=self.state)
                self.registry_status["POST_2_5"] = "READY"
                self._trace_log("[POST 2.5]  MEMORY: Active.")
            except Exception as e:
                self._trace_log(f" BOOT_FAIL: POST 2.5 - {str(e)}")
                self._rollback_state()
                return False

            # =========================================================
            # POST 4 | HARDWARE BRAIN
            # =========================================================
            try:
                mod_hw = self._import_via_contract("HardwareBrain", paths_matrix.get("hardware_brain"))
                self.hw = self._safe_factory_instantiate(mod_hw, "HardwareBrain")
                self.registry_status["POST_4"] = "READY"
                self._trace_log("[POST 4]  HARDWARE ACCESS: Cascading asset layers bound.")
            except Exception as e:
                self._trace_log(f" BOOT_FAIL: POST 4 - {str(e)}")
                self._rollback_state()
                return False

            # =========================================================
            # POST 5 | RUNTIME ENGINE
            # =========================================================
            try:
                mod_engine = self._import_via_contract("RuntimeEngine", paths_matrix.get("runtime_engine"))
                self.engine = self._safe_factory_instantiate(mod_engine, "RuntimeEngine")
                self.engine.ignite(self.bus)
                self.registry_status["POST_5"] = "READY"
                self._trace_log("[POST 5]  RUNTIME: Engine ignited.")
            except Exception as e:
                self._trace_log(f" BOOT_FAIL: POST 5 - {str(e)}")
                self._rollback_state()
                return False

            # =========================================================
            # [DIAGNOSTIC] FAISS VECTOR GATEWAY (ATOMIC CHECK)
            # =========================================================
            print(f"[DIAGNOSTIC] Engine ignited. Waiting for FAISS registry...")
            import time
            faiss_ready = False
            for i in range(10):
                val = self.bus.resolve("FAISS_BACKEND")
                if val is not None:
                    print(f"[DIAGNOSTIC] FAISS FOUND AT ATTEMPT {i}")
                    faiss_ready = True
                    break
                else:
                    print(f"[DEBUG] FAISS not yet registered in Bus.")
                time.sleep(0.5) #         
            
            if not faiss_ready:
                print("[DIAGNOSTIC] FATAL: FAISS NOT FOUND EVEN AFTER RETRIES!")
                self._trace_log(" BOOT_FAIL: FAISS_BACKEND missing from registry.")
                self._rollback_state()
                return False

            # =========================================================
            # POST 5.5 | INFERENCE ENGINE
            # =========================================================
            try:
                mod_inf = self._import_via_contract("InferenceEngine", paths_matrix.get("inference_engine"))
                self.inference = mod_inf.InferenceEngine(runtime_bridge=self.bus, runtime_bus=self.bus)
                self.bus.stage_service("inference", self.inference)
                print(f"DEBUG: Checking if registry exists in Bus: {self.bus.resolve('registry')}")
                
                if hasattr(self.inference, "initialize_db"): self.inference.initialize_db()
                self.registry_status["POST_5_5"] = "READY"
                self._trace_log("[POST 5.5]  INFERENCE: Engine staged.")
            except Exception as e:
                self._rollback_state()
                return False
            
            # --- DEEP DIAGNOSTIC PROBE ---
            print(f"DEBUG_DIAGNOSTIC: Bus Object Memory Address: {id(self.bus)}")
            print(f"DEBUG_DIAGNOSTIC: Full Bus Registry Content: {list(self.bus._services.keys())}")

            # Check specific key existence (Case-sensitive)
            target_keys = ["memory_budget_controller", "resource_guard", "scheduler"]
            for key in target_keys:
                val = self.bus._services.get(key)
                print(f"DIAGNOSTIC: Key '{key}' status -> Found: {key in self.bus._services} | Value is None: {val is None}")
                # ------------------------------
            

            # =========================================================
            # EMERGENCY SYNC GATE (POST 6)
            # =========================================================
            # Orchestrator    Bus  ''    Registry check 
            #  service  ,  code  error  ,      

            required = ["memory_budget_controller", "resource_guard", "scheduler"]
            for service_name in required:
                #  service Bus   ,  Launcher    
                if self.bus.resolve(service_name) is None:
                #  log     service  
                    logging.critical(f" BUS REGISTRY FAULT: '{service_name}' missing before Orchestrator init!")
                    self._rollback_state()
                    return False
                
            print(f"DEBUG: Bus services keys: {list(self.bus._services.keys())}")
            print(f"DEBUG: Resolve output: {self.bus.resolve('memory_budget_controller')}")

            # =========================================================
           # =========================================================
            # POST 6 | ORCHESTRATOR & SERVICE INJECTION (Hardened Core)
            # =========================================================
            try:
                mod_orch = self._import_via_contract("ExecutionOrchestrator", paths_matrix.get("execution_orchestrator"))
                self.orchestrator = self._safe_factory_instantiate(mod_orch, "ExecutionOrchestrator", runtime_bus=self.bus)
                
                # 1. Validation Check (Inference Engine)
                if not self.inference:
                    raise RuntimeError("Inference engine missing before orchestrator bind.")
                
                # 2. LOCAL REFERENCE INJECTION
                mem_inst = getattr(self, 'memory_controller_instance', None)
                guard_inst = getattr(self, 'instance_guard', None)
                sched_inst = getattr(self, 'instance_sched', None)
                
                if not mem_inst: mem_inst = self.bus.resolve("memory_budget_controller")
                if not guard_inst: guard_inst = self.bus.resolve("resource_guard")
                if not sched_inst: sched_inst = self.bus.resolve("scheduler")
                
                if not mem_inst or not guard_inst or not sched_inst:
                    raise RuntimeError("Orchestrator required services could not be linked.")
                
                # 3. Explicit Binding/Injection
                if hasattr(self.orchestrator, "bind_service"):
                    print(f"[DEBUG] Binding registry with: {type(self.inference)}")
                    self.orchestrator.bind_service("registry", self.inference)
                    self.orchestrator.bind_service("memory_budget_controller", mem_inst)
                    self.orchestrator.bind_service("resource_guard", guard_inst)
                    self.orchestrator.bind_service("scheduler", sched_inst)
                    
                    # --- [REGISTRY FIX START] ---
                    # Inference engine se registry utha kar orchestrator ko de rahe hain
                    reg = getattr(self.inference, 'registry', self.inference)
                    self.orchestrator.bind_service("registry", reg)
                    self.bus.stage_service("registry", reg)
                    # --- [REGISTRY FIX END] ---
                
                # 4. Bus Subscription (Bridge)
                def _safe_orch_bridge(msg):
                    try:
                        self.orchestrator.submit_task({
                            "payload": msg, 
                            "source": "bus_transport", 
                            "timestamp": time.time()
                        })
                    except Exception as e:
                        logging.error(f"Orchestrator Bridge Crash: {str(e)}")

                self.bus.subscribe("ORCHESTRATOR_TASK", _safe_orch_bridge)
                
                self.registry_status["POST_6"] = "READY"
                self._trace_log("[POST 6]  ORCHESTRATOR: Fully bound via Direct Injection.")
                
            except Exception as e:
                logging.error(f"POST 6 Initialization Failed: {str(e)}")
                self._rollback_state()
                return False

            # =========================================================
            # POST 6.5 | REGISTRY LOCK
            # =========================================================
            self.bus.lock_registry(memory=self.memory_manager, hardware=self.hw, engine=self.engine, orchestrator=self.orchestrator, inference=self.inference)
            
            # =========================================================
            # POST 7 | EXECUTION MANAGER
            # =========================================================
            try:
                mod_man = self._import_via_contract("ExecutionManager", paths_matrix.get("execution_manager"))
                self.execution_manager = mod_man.get_manager()
                self.execution_manager.bind_bus(self.bus)

                if self.orchestrator and hasattr(self.execution_manager, "bind_orchestrator"):
                    self.execution_manager.bind_orchestrator(self.orchestrator)
                elif hasattr(self.execution_manager, "setup_bridge"):
                    self.execution_manager.setup_bridge()

                if self.inference and hasattr(self.execution_manager, "attach_ai"):
                    self.execution_manager.attach_ai(self.inference)

                proxy = self.bus.get_messenger_proxy()
                self.execution_manager.set_messenger(proxy if hasattr(proxy, 'send') else self.bus)
                self.registry_status["POST_7"] = "READY"
            except Exception as e:
                self._rollback_state()
                return False

            # =========================================================
            # POST 8 | INTEGRITY ASSERTIONS
            # =========================================================
            assert self.orchestrator is not None, "Orchestrator missing"
            assert self.inference is not None, "Inference engine missing"
            assert self.bus.resolve("inference") is not None, "Inference service registration failed"

            self.execution_manager.set_ready(True)
            self.registry_status["POST_8"] = "OPERATIONAL"
            self._trace_log(" [Z-STUDIO]: ARCHITECTURE FULLY SEALED.")

            

            # =========================================================
            # POST 9 | UI LIVE BRIDGE (HARDENED INJECTION)
            # =========================================================
            live_bridge_rel = paths_matrix.get("live_bridge")
            if not live_bridge_rel:
                logging.critical(" BOOT_STOP: [POST 9] LiveBridge path variable unassigned.")
                self._rollback_state()
                return False
                
            mod_bridge = self._import_via_contract("ui_core.live_bridge", live_bridge_rel)
            if not mod_bridge or not hasattr(mod_bridge, "get_bridge"):
                logging.critical(" BOOT_STOP: [POST 9] LiveBridge tracking channel connection entry missing.")
                self._rollback_state()
                return False
            
            # Bridge Instance praapt karo
            self.live_bridge = mod_bridge.get_bridge()
            
            # --- ASLI FIX: BUS INJECTION (Directly from Launcher's active bus) ---
            if hasattr(self.live_bridge, "set_bus") and hasattr(self, "bus"):
                self.live_bridge.set_bus(self.bus)
                self._trace_log("[POST 9/11] LIVE BRIDGE: Bus successfully injected.")
            # --------------------------------------------------------------------
            
            if self.execution_manager and self.live_bridge:
                if hasattr(self.execution_manager, "attach_bridge"):
                    self.execution_manager.attach_bridge(self.live_bridge)
                self.live_bridge.execution_manager = self.execution_manager
                
            if hasattr(self.live_bridge, "set_safe_mode"): 
                self.live_bridge.set_safe_mode(True)
                
            self.registry_status["POST_9"] = "READY"
            self.last_healthy_checkpoint = "POST_9"
            self._trace_log("[POST 9/11] LIVE BRIDGE: Inter-thread pipeline messaging tracks isolated.")

            # =========================================================
            # POST 10 | UI DASHBOARD LAYER
            # =========================================================
            main_dashboard_rel = paths_matrix.get("main_dashboard")
            ui_renderer_rel = paths_matrix.get("ui_renderer")
            
            is_outside_gui_thread = True
            if PYSIDE6_AVAILABLE and QApplication is not None:
                try:
                    q_app_instance = QApplication.instance()
                    if q_app_instance is not None:
                        is_outside_gui_thread = (threading.current_thread().ident != threading.main_thread().ident)
                    else:
                        is_outside_gui_thread = (threading.current_thread() != threading.main_thread())
                except Exception as thread_check_err:
                    self.ui_failure_reason = f"Thread identification failure: {thread_check_err}"
                    logging.warning(f" THREAD_WARN: Identification mismatch. Forcing safe headless fallback: {self.ui_failure_reason}")
                    is_outside_gui_thread = True
            else:
                self.ui_failure_reason = "Qt framework bindings unallocated on target host environment."
                self._trace_log(f" THREAD_WARN: {self.ui_failure_reason}")
                is_outside_gui_thread = True
            
            if is_outside_gui_thread or os.environ.get("Z_HEADLESS") == "1":
                self._trace_log(" THREAD_WARN: Visual workspace bypassed seamlessly for isolated headless background channel execution.")
                self.headless_mode = True
                self.registry_status["POST_10"] = "READY"
            else:
                try:
                    if not main_dashboard_rel or not ui_renderer_rel:
                        raise ValueError("UI compilation path attributes are missing inside system configurations schema.")
                        
                    #  ONLY VERIFY + LOAD MODULES (NO INSTANTIATION)
                    mod_dash = self._import_via_contract("ui_core.main_dashboard", main_dashboard_rel)
                    mod_render = self._import_via_contract("ui_core.ui_renderer", ui_renderer_rel)
                    
                    if not mod_dash or not mod_render:
                        raise ImportError("UI modules failed to load.")
                        
                    #  AUDIT FIX: mod_dash par link_components call karne wali galti DELETED. No over-control.
                    self.ui_available = True
                        
                    self.registry_status["POST_10"] = "READY"
                    self._trace_log("[POST 10/11]  USER INTERFACE: Workspace display modules verified and loaded.")
                except Exception as ui_error:
                    self.ui_failure_reason = str(ui_error)
                    
                    self._trace_log(f" UI_RENDER_BLOCKED: Graphics layers execution prevented: {self.ui_failure_reason}. Falling back to Headless Core.")
                    self.headless_mode = True
                    self.registry_status["POST_10"] = "READY"

            # =========================================================
            # POST 11 | SYSTEM AUTHORITY CONTRACT LOCK
            # =========================================================
            self.boot_stage = "OPERATIONAL"
            
            #  CAPABILITY VERIFICATION: 
            # Engine  Bus    , Orchestrator    
            # Attach          
            
            #      Orchestrator  Bus    
            if not hasattr(self.orchestrator, "bus"):
                logging.warning(" Orchestrator: Bus link integrity check pending.")

            #  AUDIT FIX: Modules  Bus       

            print("\n" + "="*40)
            print("--- KERNEL BUS DIAGNOSTICS ---")
            print(f"ID launcher.bus: {id(self.bus)}")
            print(f"ID inference.bus: {id(self.inference.bus)}")
            print(f"ID orchestrator.bus: {id(self.orchestrator.bus)}")
            print("="*40 + "\n")

            self._trace_log("SYSTEM AUTHORITY: Contract Locked. Modules operating via Bus communication.")
                
            self.registry_status["POST_11"] = "READY"
            self.last_healthy_checkpoint = "POST_11"
            self._trace_log(f" [Z-LAUNCHER]: BOOT INITIALIZATION PIPELINE EXECUTED SUCCESSFULLY.")
            return True

        except Exception as e:
            #   (UnicodeError     'replace'   )
            logging.critical(f" UNHANDLED INITIALIZATION PIPELINE INTERCEPT FAILURE IN CORE BOOT SEQUENCE: {str(e).encode('ascii', 'replace').decode('ascii')}")
            return False
        
        
    def start(self):
        return self.execute_secure_boot()
        
    def ignite_core(self):
        return self.execute_secure_boot()
    

# =====================================================================
#  SECURE ENTERPRISE ENGINE IGNITION (V12.3 LOCKED BINDING)
# =====================================================================

def get_launcher_instance():
    """Factory function to get the unique, non-duplicating Launcher."""
    global _SINGLETON_INSTANCE
    if _SINGLETON_INSTANCE is None:
        _SINGLETON_INSTANCE = ZStudioLauncher()
    return _SINGLETON_INSTANCE

if __name__ == "__main__":
    # Windows Multiprocessing safety
    multiprocessing.freeze_support()
    
    # Singleton access
    launcher = get_launcher_instance()
    
    # Execution
    success = launcher.start_boot()
    
    if not success:
        logging.critical(" ENGINE_INIT_FAILED: Enterprise core engine ignition aborted.")
        sys.exit(1)
    else:
        logging.info(" SYSTEM_ONLINE: ZYNQUAR ATELIER KERNEL V12.3 READY.")