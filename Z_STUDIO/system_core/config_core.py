import json, os, threading, logging, copy, typing
import json
from pathlib import Path

Any = typing.Any


class ConfigCore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, external_path=None):
        if hasattr(self, "_init"):
            return

        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ROOT_DIR = self.root
        self.VERSION = "12.3"
        self.DEGRADED_MODE = False

        #  Dual config sources
        self.internal_path = os.path.join(self.root, "installer_core", "init_config.json")
        self.external_path = external_path

        #  FULL LAYER SYSTEM
        self.registry = {
            "defaults": {},
            "internal": {},
            "external": {},
            "runtime": {}
        }

        #  path tokens
        self.tokens = {
            "__ROOT__": self.root.replace("\\", "/"),
            "__RESOLVED_APP_DIR__": self.root.replace("\\", "/"),
        }

        self._rw_lock = threading.RLock()
        self._init = True

        #  SAFE BOOTSTRAP
        self.bootstrap()

    # ---------------------------
    #  BOOTSTRAP ENGINE
    # ---------------------------
    def bootstrap(self):
        with self._rw_lock:

            # 1. INTERNAL LOAD (MANDATORY SAFE FALLBACK)
            self.registry["internal"] = self._safe_load(self.internal_path, source="internal")

            # 2. EXTERNAL LOAD (OPTIONAL OVERRIDE)
            if self.external_path:
                self.registry["external"] = self._safe_load(self.external_path, source="external")

            # 3. DEFAULT SAFETY PATCH (GUARANTEE NON-EMPTY STATE)
            if not self.registry["internal"] and not self.registry["external"]:
                self.registry["defaults"] = {
                    "system": {
                        "mode": "safe",
                        "status": "fallback_active"
                    }
                }

    # ---------------------------
    #  SAFE LOADER
    # ---------------------------
    def _safe_load(self, path, source="unknown"):
        if not path or not os.path.exists(path):
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                return data
            else:
                logging.error(f"[{source}] Invalid schema (not dict)")
                return {}

        except Exception as e:
            logging.error(f"[{source}] Load failed: {e}")
            return {}

    # ---------------------------
    #  ACTIVE CONFIG BUILDER
    # ---------------------------
    def get_active(self):
        with self._rw_lock:
            active = {}

            # priority order
            active.update(self.registry["defaults"])
            active.update(self.registry["internal"])
            active.update(self.registry["external"])
            active.update(self.registry["runtime"])

            return self._recursive_resolve(active)

    # ---------------------------
    #  RECURSIVE RESOLVE ENGINE
    # ---------------------------
    def _recursive_resolve(self, data):
        if isinstance(data, dict):
            return {k: self._recursive_resolve(v) for k, v in data.items()}

        if isinstance(data, list):
            return [self._recursive_resolve(i) for i in data]

        if isinstance(data, str):
            for t, p in self.tokens.items():
                data = data.replace(t, p)
            return os.path.normpath(data).replace("\\", "/")

        return data

    # ---------------------------
    #  QUERY ENGINE
    # ---------------------------
    def get(self, query: str, default=None):
        data = self.get_active()

        for k in query.split("."):
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default

        return data

    # ---------------------------
    #  RUNTIME SET
    # ---------------------------
    def set_runtime(self, query: str, value: Any):
        with self._rw_lock:
            keys = query.split(".")
            target = self.registry["runtime"]

            for k in keys[:-1]:
                target = target.setdefault(k, {})

            target[keys[-1]] = value

    # ---------------------------
    #  EXTERNAL WRITE (SAFE)
    # ---------------------------
    def set_disk(self, query: str, value: Any):
        if not self.external_path:
            return

        with self._rw_lock:
            keys = query.split(".")
            target = self.registry["external"]

            for k in keys[:-1]:
                target = target.setdefault(k, {})

            target[keys[-1]] = value

            self._flush()

    # ---------------------------
    #  CRASH SAFE FLUSH
    # ---------------------------
    def _flush(self):
        if not self.external_path:
            return

        tmp = self.external_path + ".tmp"

        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.registry["external"], f, indent=4)
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp, self.external_path)

        except Exception as e:
            logging.error(f"[flush] write failed: {e}")

            # cleanup safety
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except:
                    pass
                
    def load_runtime_config(self):
        config_path = Path("installer_core/init_config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        runtime_paths = config.get("runtime_paths", {})

        self.bus.publish(
            "CONFIG_RUNTIME_READY",
            runtime_paths
        )

    # ---------------------------
    #  LEGACY COMPATIBILITY API
    # ---------------------------
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls()
        return cls._instance

    def load_initial_config(self) -> bool:
        """Boot-time config loader (legacy API)."""
        self.bootstrap()
        return bool(self.registry.get("internal") or self.registry.get("external"))

    def get_active_config(self) -> dict:
        """Returns merged config with legacy key names for older modules."""
        active = self.get_active()
        storage = active.get("storage_logic", {}).get("models", {})
        text_dir = storage.get("text_models", {}).get("core", "")
        text_model = storage.get("text_models", {}).get("active_model", "")

        active_text = None
        if text_dir and text_model:
            active_text = os.path.join(text_dir, text_model).replace("\\", "/")

        return {
            **active,
            "ROOT_DIR": self.ROOT_DIR,
            "ACTIVE_TEXT_MODEL": active_text,
            "REGISTRY": active.get("registry", []),
            "runtime_mode": active.get("runtime_mode", "AUTO"),
        }

    def lock_runtime_mode(self, force_gpu: bool = False) -> str:
        """Locks runtime to GPU or CPU based on hardware availability."""
        mode = "GPU" if force_gpu else "CPU"
        self.DEGRADED_MODE = not force_gpu
        self.set_runtime("runtime_mode", mode)
        return mode


config = ConfigCore.get_instance()