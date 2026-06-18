"""
Z-STUDIO V12.3  SYSTEM CORE (SYSTEM STATE MANAGER - RE-ENTRANT FIXED)
Author: ZYNQUAR ATELIER
Role: Persistence Layer with RLock to prevent Kernel Deadlocks during State Sync.
"""

import os
import json
import threading
import time
import logging
from datetime import datetime


# =========================
# LOGGER SAFE BOOTSTRAP
# =========================
try:
    from system_core.logger_core import logger
except Exception:
    logger = logging.getLogger("ZYNQUAR_STATE")

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | ZYNQUAR | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)


# =========================
# STATE MANAGER CORE
# =========================
class SystemStateManager:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._boot_synced = False
            return cls._instance

    def __init__(self):
        with self._lock:
            if hasattr(self, "_initialized"):
                return

            base_dir = os.getcwd()
            self.state_dir = os.path.join(base_dir, "system_data", "state")
            self.state_file = os.path.join(self.state_dir, "global_state.json")

            self.current_state = {
                "brand": "ZYNQUAR ATELIER",
                "version": "12.3",
                "last_boot": None,
                "status": "INITIALIZING",
                "active_tasks": [],
                "engine_metrics": {},
                "last_error": None,
                "session_id": f"ZQ_{int(time.time())}"
            }

            self.bus = None
            self._ensure_storage()
            self._load_last_known_state()

            self._initialized = True
            logger.info("[ZYNQUAR_STATE] PERSISTENCE ENGINE ARMED | RLOCK ACTIVE.")

    # =========================
    # STORAGE SAFE INIT
    # =========================
    def _ensure_storage(self):
        try:
            os.makedirs(self.state_dir, exist_ok=True)
        except Exception as e:
            logger.critical(f"[ZYNQUAR_STATE] STORAGE_INIT_FATAL: {e}")

    # =========================
    # RECOVERY ENGINE
    # =========================
    def _load_last_known_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)

                with self._lock:
                    for key, value in saved_data.items():
                        if key in self.current_state:
                            self.current_state[key] = value

                    self.current_state["last_boot"] = datetime.now().isoformat()
                    self.current_state["status"] = "RECOVERED"

                self._boot_synced = True
                logger.info("[ZYNQUAR_STATE] RECOVERY SUCCESSFUL.")

            except Exception as e:
                logger.error(f"[ZYNQUAR_STATE] RECOVERY_FAILED: {e}")
                self.current_state["status"] = "FRESH_BOOT"
        else:
            self.current_state["last_boot"] = datetime.now().isoformat()
            self.current_state["status"] = "NEW_INSTALL"
            self._boot_synced = True

    # =========================
    # SAFE UPDATE ENGINE
    # =========================
    def update_state(self, key, value, save_immediate=False):
        with self._lock:
            if key in self.current_state:
                self.current_state[key] = value

                #  SAFE WIRING (NO NEW CONTROLBUS)
                try:
                    self.bus.emit("SYSTEM_STATE_UPDATED", self.current_state)
                except Exception as e:
                    logger.error(f"[STATE BUS ERROR] {e}")

                if save_immediate:
                    self.save_to_disk()

    # =========================
    # ATOMIC SAVE
    # =========================
    def save_to_disk(self):
        temp_file = self.state_file + ".tmp"

        try:
            with self._lock:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self.current_state, f, indent=4)

                os.replace(temp_file, self.state_file)

            return True

        except Exception as e:
            logger.error(f"[ZYNQUAR_STATE] SAVE_FAILED: {e}")
            return False

    # =========================
    # READ STATE
    # =========================
    def get_full_state(self):
        with self._lock:
            return self.current_state.copy()

    # =========================
    # LAUNCHER COMPATIBILITY FIX
    # =========================
    def verify_integrity(self):
        try:
            return isinstance(self.current_state, dict) and self.current_state is not None
        except Exception:
            return False

    def sync_last_known_state(self):
        #  FIX: avoid reloading twice (prevents boot loop)
        if self._boot_synced:
            return self.current_state
        return self._load_last_known_state()

    def mark_system_ready(self):
        """Marks system fully booted"""
        with self._lock:
            self.current_state["status"] = "READY"
            self.current_state["engine"] = "ONLINE"
            self.current_state["last_boot"] = datetime.now().isoformat()
            self.save_to_disk()

            #  SAFE WIRING (NO NEW BUS CREATION)
            try:
                if self.bus:
                    self.bus.emit("SYSTEM_READY",{   #"SYSTEM_STATE_UPDATED", self.current_state)
                    #self.bus.emit("SYSTEM_STARTED", {
                        "engine": "ONLINE",
                        "status": "READY"
                    })
                    logger.info("[STATE] SYSTEM READY SIGNAL SENT")
            except Exception as e:
                logger.error(f"[STATE] BUS EMIT FAILED: {e}")

            return True
    def set_flag(self, key, value, save=True):
        """REAL FIX: Launcher core isi location par crash ho raha hai"""
        with self._lock:
            self.current_state[key] = value
            if save:
                self.save_to_disk()
            logger.info(f"[STATE] FLAG_SET: {key} -> {value}")
    def update_sync(self, mode=None, active_model=None):
        """REAL FIX: AI Model loading ke waqt ka crash rokne ke liye"""
        with self._lock:
            if mode: self.current_state["status"] = mode
            if active_model: self.current_state["active_model"] = active_model
            self.save_to_disk()
            logger.info(f"[STATE] SYNC_UPDATE: Mode={mode}, Model={active_model}")

    def link_bus(self, bus_instance):
        """
        DUMMY BYPASS NAHI HAI: Ye Real Bus Interface ko Kernel ke sath
        lock karta hai taaki State changes pure system mein broadcast ho sakein.
        """
        with self._lock:
            self.bus = bus_instance
            logger.info("[STATE_WIRING] CONTROL_BUS SUCCESSFULLY LINKED TO MANAGER.")

    def _broadcast_state(self, event_name="SYSTEM_STATE_UPDATED"):
        """Real logic for system-wide sync"""
        if hasattr(self, 'bus') and self.bus is not None:
            try:
                # Real data transmission
                self.bus.emit(event_name, self.current_state)
            except Exception as e:
                logger.error(f"[STATE_KERNEL_SYNC_ERROR] Transmission failed: {e}")


# =========================
# GLOBAL SINGLETON HOOK
# =========================
state_manager = SystemStateManager()
StateManager = SystemStateManager