"""
Z-STUDIO V12.3  SYSTEM CORE
Module: Hardware Brain (Self-Healing Sensory Layer)
Status: 100/100 INDUSTRIAL LOCKED  PHASE 1 COMPLETE
Audit: FINAL LOCK V7.4 (EMBEDDED RUNTIME FIX + GPU AUTO DETECT + NO PIPE)
"""

import os
import sys
import json
import logging
import psutil
import threading
import hashlib
import platform
import importlib.util


# =========================
# EMBEDDED LIB PATH FIX (WIRE SAFE)
# =========================
_EMBEDDED_LIB = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "installer_core",
        "embedded_runtime",
        "python_core_pack",
        "lib",
        "site-packages"
    )
)

if os.path.exists(_EMBEDDED_LIB) and _EMBEDDED_LIB not in sys.path:
    sys.path.insert(0, _EMBEDDED_LIB)


# =========================
# SAFE LOGGER
# =========================
class SafeFormatter(logging.Formatter):
    def format(self, record):
        try:
            msg = super().format(record)
            return msg.encode("ascii", "ignore").decode("ascii")
        except Exception:
            return "LOG_ERROR"


logger = logging.getLogger("HW_BRAIN")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        SafeFormatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class HardwareBrain:
    def __init__(self, version="12.3.0"):
        self.version = version
        self.log_dir = "logs"
        self.snapshot_path = os.path.join(self.log_dir, "hw_snapshot.json")
        self.bus = None
        self._torch_cache = None
        self.GPU_AVAILABLE = False
        self.RUNTIME_MODE = "CPU"

        os.makedirs(self.log_dir, exist_ok=True)

        self.capabilities = {
            "has_gpu": False,
            "gpu_name": "NONE",
            "vram_total": 0,
            "ram_total": round(psutil.virtual_memory().total / (1024**3), 2),
            "cpu_cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "os_node": platform.node(),
            "compute_mode": "CPU",
            "integrity_hash": ""
        }

        self._hw_lock = threading.Lock()
        self._torch_checked = False
        self.system_ready = False
        self.hardware_ready = False

        psutil.cpu_percent(interval=None)
        logger.info(f"[HW_BRAIN] Sensory Core V{self.version} Initialized.")
        print("DEBUG: HW_BRAIN_INIT_DONE") # Ye line add karein

    # =========================
    # BUS LINK (WIRE SAFE)
    # =========================
    def link_bus(self, bus_instance):
        with self._hw_lock:
            self.bus = bus_instance
            logger.info("[HW_BRAIN] Control Bus Linked.")

    def _emit_signal(self, event_type, payload):
        try:
            if self.bus and hasattr(self.bus, "emit"):
                self.bus.emit(event_type, payload=payload)
        except Exception:
            pass

    # =========================
    # HASH
    # =========================
    def _generate_integrity_hash(self, data):
        fingerprint = (
            f"{data.get('gpu_name')}:"
            f"{data.get('ram_total')}:"
            f"{data.get('os_node','unknown')}:"
            f"{self.version}"
        )
        return hashlib.sha256(fingerprint.encode()).hexdigest()

    # =========================
    # SNAPSHOT SAVE
    # =========================
    # =========================
    # SNAPSHOT SAVE (FINAL HARDENED)
    # =========================
    def _save_snapshot(self):
        """Asli Ilaaj: No nested lock + Async Atomic Write"""
        def perform_write(data, path):
            try:
                import json
                temp_path = f"{path}.tmp"
                data["integrity_hash"] = self._generate_integrity_hash(data)
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                if os.path.exists(path):
                    os.replace(temp_path, path)
                else:
                    os.rename(temp_path, path)
                print("[HW_BRAIN] Hardware Signature Persisted.")
            except Exception as e:
                print(f"[HW_BRAIN_ERROR] Snapshot Failed: {e}")

        data_copy = self.capabilities.copy()
        threading.Thread(target=perform_write, args=(data_copy, self.snapshot_path), daemon=True).start()
        return True

    # =========================
    # SAFE GPU CHECK
    # =========================
    def _safe_cuda_check(self):
        result = {"gpu": False, "name": None, "vram": 0}

        try:
            import torch

            if torch.cuda.is_available():
                result["gpu"] = True
                result["name"] = torch.cuda.get_device_name(0)
                result["vram"] = round(
                    torch.cuda.get_device_properties(0).total_memory / (1024**3), 2
                )
        except Exception:
            pass

        return result

    # =========================
    # GPU VALIDATION (WIRE SAFE FLOW)
    # =========================
    def validate_gpu_access(self):
        if self._torch_checked:
            return self.capabilities["has_gpu"]

        with self._hw_lock:
            # 1. SNAPSHOT CHECK (With Integrity Fix to avoid circular hash crash)
            if os.path.exists(self.snapshot_path):
                try:
                    with open(self.snapshot_path, "r") as f:
                        cached = json.load(f)
                    
                    # Clean copy check: integrity hash match logic
                    clean_cache = dict(cached)
                    clean_cache.pop("integrity_hash", None)
                    if cached.get("integrity_hash") == self._generate_integrity_hash(clean_cache):
                        self.capabilities.update(cached)
                        self._torch_checked = True
                        self.hardware_ready = True
                        self.system_ready = True
                        logger.info("[HW_BRAIN] Snapshot Verified - Safety Lock Active.")
                        self._emit_signal("SYSTEM_READY", {
                            "status": "READY",
                            "hardware_ready": True,
                            "mode": self.capabilities["compute_mode"]
                        })
                        self._emit_signal("HW_GPU_UPDATE", self.capabilities)
                        return self.capabilities["has_gpu"]
                except Exception:
                    pass

            logger.info("[HW_BRAIN] Initiating Safe Neural Hardware Probe...")

            # 2. ZERO-CRASH DISCOVERY (Using sys.modules to prevent Torch re-import crash)
            try:
                import sys
                # Agar torch pehle se hai toh wahi uthao, warna import karo
                torch_mod = sys.modules.get("torch")
                if not torch_mod and importlib.util.find_spec("torch"):
                    torch_mod = importlib.import_module("torch")
                
                if torch_mod:
                    self._torch_cache = torch_mod
                    # Safe CUDA call - zero trust execution
                    has_cuda = False
                    try:
                        has_cuda = bool(torch_mod.cuda.is_available())
                    except:
                        has_cuda = False

                    if has_cuda:
                        # Deep wrap for device info (prevents crash on old drivers)
                        g_name = "UNKNOWN"
                        v_total = 0
                        try:
                            g_name = torch_mod.cuda.get_device_name(0)
                            v_total = round(torch_mod.cuda.get_device_properties(0).total_memory / (1024**3), 2)
                        except: pass

                        self.capabilities.update({
                            "has_gpu": True,
                            "gpu_name": g_name,
                            "vram_total": v_total,
                            "compute_mode": "CUDA"
                        })
                        logger.info(f"[HW_BRAIN] CUDA ONLINE: {g_name}")
                    else:
                        self.capabilities.update({"has_gpu": False, "gpu_name": "NONE", "compute_mode": "CPU"})
                        logger.info("[HW_BRAIN] CPU MODE ACTIVE")
                else:
                    self.capabilities.update({"has_gpu": False, "gpu_name": "NONE", "compute_mode": "CPU"})
                    logger.info("[HW_BRAIN] TORCH NOT FOUND - CPU MODE")

            except Exception as e:
                logger.error(f"[HW_BRAIN] Probe Error: {e}")
                self.capabilities.update({"has_gpu": False, "compute_mode": "CPU"})
            self.GPU_AVAILABLE = self.capabilities["has_gpu"]
            self.RUNTIME_MODE = self.capabilities["compute_mode"]

            self._torch_checked = True
            
            # 3. ATOMIC SNAPSHOT SAVE (Safety wrap around thread save)
            try:
                self._save_snapshot()
            except Exception as e:
                logger.warning(f"[HW_BRAIN] Snapshot Skip: {e}")

            self._emit_signal("HW_GPU_UPDATE", self.capabilities)
            return self.capabilities["has_gpu"]