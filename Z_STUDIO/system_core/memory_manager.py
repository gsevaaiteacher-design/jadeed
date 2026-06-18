"""
Z-STUDIO V12.3  SYSTEM CORE
Module: Launcher Core (Hardened Boot Sequence)
Status: INDUSTRIAL GRADE STABLE BOOTSTRAP
Audit: FINAL HARDENED PATCH (LOGGER SAFE + BUS GUARD + CLEAN STATE FLOW)
"""

import os
import sys
import time
import gc
import threading
import logging
from logging.handlers import RotatingFileHandler

# =========================
# CORE DEPENDENCIES
# =========================
try:
    from system_core.control_bus import ControlBus
    from system_core.system_state_manager import StateManager
    from system_core.config_core import ConfigCore
    from system_core.system_guard import SystemGuard
    from system_core.hardware_brain import HardwareBrain
    from system_core.runtime_engine import RuntimeEngine
except Exception as e:
    print(f"[FATAL BOOT FAILURE] Missing Dependency: {e}")
    sys.exit(1)


class MemoryManager:
    _boot_lock = threading.Lock()
    _state_lock = threading.Lock()
    _logger_initialized = False

    #  MODIFY THIS IN YOUR MEMORY MANAGER FILE:
    def __init__(self, config=None, state=None):
        self.start_time = time.time()
        self.version = "12.3.0"

        self._init_logging()

        try:
            # Agar launcher se config aur state aa rahe hain toh wahi use karo, nahi toh naya banao
            self.state = state or StateManager()
            self.config = config or ConfigCore()
            self.guard = SystemGuard()
            self.hw = HardwareBrain()
            self.engine = RuntimeEngine()
            self.bus = None
        except Exception as e:
            print(f"[FATAL INIT FAILURE] {e}")
            sys.exit(1)

    # =========================
    # SAFE LOGGING (FIXED DUPLICATION)
    # =========================
    def _init_logging(self):
        if getattr(self, "_logger_initialized", False):
            return

        os.makedirs("logs", exist_ok=True)

        log_file = "logs/system_boot.log"

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [T-%(thread)d] %(message)s"
        )

        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_handler.setFormatter(formatter)

        root = logging.getLogger()
        root.setLevel(logging.INFO)

        # FIX 1: prevent duplicate handlers cleanly
        if root.hasHandlers():
            root.handlers.clear()

        root.addHandler(file_handler)

        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(formatter)
        root.addHandler(stream)

        MemoryManager._logger_initialized = True

    # =========================
    # CLEANUP ENGINE
    # =========================
    def _cleanup(self):
        logging.info("RESOURCE_CLEANUP_STARTED")

        gc.collect()

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except Exception:
            pass

        logging.info("RESOURCE_CLEANUP_DONE")

    # =========================
    # BUS VALIDATION (HARDENED)
    # =========================
    def _validate_bus(self, bus) -> bool:
        try:
            if not bus:
                return False

            # FIX 2: safe initialization guard
            if getattr(bus, "_initialized", False):
                return True

            if not bus.initialize_hub():
                return False

            if hasattr(bus, "health_check"):
                try:
                    if not bus.health_check():
                        return False
                except Exception:
                    return False

            setattr(bus, "_initialized", True)
            return True

        except Exception:
            return False

    # =========================
    # SAFE FALLBACK
    # =========================
    def fail_safe(self, reason: str) -> bool:
        logging.warning(f"FAILSAFE_TRIGGERED: {reason}")

        self._cleanup()

        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

            # FIX 3: safe config access
            if hasattr(self.config, "lock_runtime_mode"):
                self.config.lock_runtime_mode(force_gpu=False)

            self.bus = ControlBus(self.config, self.state)

            if not self._validate_bus(self.bus):
                return False

            if not self.engine.ignite(self.bus):
                return False

            logging.info("FAILSAFE_RECOVERY_SUCCESS")
            return True

        except Exception as e:
            logging.error(f"FAILSAFE_ERROR: {e}")
            return False

    # =========================
    # SHUTDOWN
    # =========================
    def shutdown(self, reason: str):
        logging.critical(f"EMERGENCY_SHUTDOWN: {reason}")
        self._cleanup()
        sys.exit(1)

    # =========================
    # BOOT SEQUENCE
    # =========================
    def ignite_core(self) -> bool:
        with self._boot_lock:
            logging.info(f"Z-STUDIO V{self.version} BOOT START")

            try:
                with self._state_lock:
                    if not self.state.verify_integrity():
                        self.shutdown("STATE_CORRUPTION")

                self.config.load_initial_config()
                self.state.sync_last_known_state()

                engine_version = self.engine.get_version()
                if engine_version != self.version:
                    self.shutdown(f"VERSION_MISMATCH {engine_version}")

                gpu_ok = self.hw.validate_gpu_access()
                self.config.lock_runtime_mode(force_gpu=gpu_ok)

                self.bus = ControlBus(self.config, self.state)

                if not self._validate_bus(self.bus):
                    if not self.fail_safe("BUS_INIT_FAILURE"):
                        self.shutdown("BUS_FAILURE")

                if not self.engine.ignite(self.bus):
                    if not self.fail_safe("ENGINE_FAILURE"):
                        self.shutdown("ENGINE_FAILURE")

                self.state.mark_system_ready()

                boot_time = round(time.time() - self.start_time, 3)
                logging.info(f"SYSTEM_READY | BOOT_TIME={boot_time}s")

                return True

            except Exception as e:
                self.shutdown(f"RUNTIME_EXCEPTION: {e}")
                return False

    # =========================
    # LAUNCH
    # =========================
    def launch(self):
        if self.ignite_core():
            print("\n[Z-STUDIO STATUS: OPERATIONAL]\n")
        else:
            self.shutdown("LAUNCH_FAILED")


if __name__ == "__main__":
    launcher = MemoryManager()
    launcher.launch()

    try:
        print("[SYSTEM GUARD ACTIVE]")
    except Exception:
        pass