import os
import sys
import json
import logging
import time
from datetime import datetime

# =========================
# 🔥 PROJECT ROOT FIX
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =========================
# 🔥 LICENSE CORE MUST BE SEPARATE ROOT
# =========================
LICENSE_ROOT = os.path.join(PROJECT_ROOT, "license_core")
if LICENSE_ROOT not in sys.path:
    sys.path.insert(0, LICENSE_ROOT)

from license_core.key_validator import ZStudioSecurity


class ZStudioBootloader:
    def __init__(self):
        self.start_time = datetime.now()
        self.boot_state = "INIT"
        self.runtime_config = None
        self.CURRENT_VERSION = "1.0.0"

        # =========================
        # INSTALLER CORE (ONLY THESE 2 STAY HERE)
        # =========================
        self.installer_core = os.path.join(PROJECT_ROOT, "installer_core")
        self.state_file = os.path.join(self.installer_core, "boot_state.json")

        # 🔥 PYTHONPATH STABILITY
        os.environ["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + os.environ.get("PYTHONPATH", "")

        self.setup_logging()

        # SECURITY INIT (NOW FROM LICENSE ROOT)
        try:
            self.security = ZStudioSecurity()
        except Exception as e:
            print("SECURITY MODULE FAILED:", e)
            sys.exit(1)

        print("STATE FILE PATH:", self.state_file)

        self.paths = {
            "config": os.path.join(self.installer_core, "init_config.json"),
            "registry_dir": os.path.join(self.installer_core, "model_storage", "external_path_registry"),
            "registry_file": os.path.join(self.installer_core, "model_storage", "external_path_registry", "path_map.json"),
            "registry_lock": os.path.join(self.installer_core, "model_storage", "external_path_registry", "registry.lock")
        }

    def setup_logging(self):
        log_dir = os.path.join(self.installer_core, "logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            filename=os.path.join(log_dir, "boot_master.log"),
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] ST_%(message)s"
        )

    def create_state_file(self, status="OK"):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

            data = {
                "heartbeat": time.time(),
                "health": status,
                "schema_ver": self.CURRENT_VERSION,
                "boot_state": self.boot_state
            }

            tmp_file = self.state_file + ".tmp"

            with open(tmp_file, "w") as f:
                json.dump(data, f, indent=4)

            os.replace(tmp_file, self.state_file)

        except Exception as e:
            print("STATE FILE ERROR:", e)
            logging.error(f"State file error: {e}")

    def _atomic_registry_init(self, force_rebuild=False):
        if os.path.exists(self.paths["registry_lock"]):
            time.sleep(0.5)

        needs_init = not os.path.exists(self.paths["registry_file"])

        if not needs_init and not force_rebuild:
            try:
                with open(self.paths["registry_file"], "r") as f:
                    json.load(f)
            except:
                needs_init = True

        if needs_init:
            open(self.paths["registry_lock"], "w").close()

            try:
                os.makedirs(self.paths["registry_dir"], exist_ok=True)

                data = {
                    "registry_info": {
                        "status": "fresh_boot",
                        "version": self.CURRENT_VERSION
                    },
                    "external_paths": {
                        "manual_mapped_paths": [],
                        "dynamic_detected_locations": []
                    }
                }

                tmp = self.paths["registry_file"] + ".tmp"

                with open(tmp, "w") as f:
                    json.dump(data, f, indent=4)

                if os.path.exists(self.paths["registry_file"]):
                    os.remove(self.paths["registry_file"])

                os.rename(tmp, self.paths["registry_file"])

            finally:
                if os.path.exists(self.paths["registry_lock"]):
                    os.remove(self.paths["registry_lock"])

    def validate_config(self):
        if not os.path.exists(self.paths["config"]):
            return False, "MISSING_CONFIG"

        try:
            with open(self.paths["config"], "r") as f:
                config = json.load(f)

            if config.get("config_version") != self.CURRENT_VERSION:
                return False, "VERSION_MISMATCH"

            if not self.security.verify_integrity(config):
                return False, "CONFIG_TAMPERED"

            required = ["system_identity", "boot_paths", "execution_params"]

            for k in required:
                if k not in config:
                    return False, f"INVALID_STRUCTURE_{k}"

            return True, config

        except Exception as e:
            logging.error(f"Config error: {e}")
            return False, "CORRUPTED_CONFIG"

    def initialize_system(self):
        print(f"🚀 Z-STUDIO V8 | STATE: {self.boot_state}")

        try:
            self.create_state_file("STARTING")

            self.boot_state = "VALIDATING"

            # ONLY CHECK installer_core FOLDERS
            for folder in ["embedded_runtime", "model_storage"]:
                path = os.path.join(self.installer_core, folder)
                if not os.path.exists(path):
                    raise Exception(f"CORE_DIRECTORY_MISSING_{folder.upper()}")

            # LICENSE CHECK FROM SEPARATE ROOT
            license_path = LICENSE_ROOT
            if not os.path.exists(license_path):
                raise Exception("CORE_DIRECTORY_MISSING_LICENSE_CORE")

            self.boot_state = "SECURING"
            print("🔐 STATE: SECURING")

            sec = self.security.check_license()
            if sec["status"] != "AUTHORIZED":
                raise Exception(f"AUTH_FAILED_{sec['status']}")

            self.boot_state = "INDEXING"
            print("📂 STATE: INDEXING")

            ok, cfg = self.validate_config()
            if not ok:
                raise Exception(cfg)

            self._atomic_registry_init()

            self.create_state_file("OK")

            self.boot_state = "READY"
            t = (datetime.now() - self.start_time).total_seconds()

            print(f"✅ STATE: READY | Boot: {t:.2f}s")
            logging.info("BOOT SUCCESS")

            return True, cfg

        except Exception as e:
            self.boot_state = "FAILED"
            self.create_state_file("FAILED")

            err = str(e)
            logging.critical(f"BOOT FAILED: {err}")

            print("BOOT ERROR:", err)
            return False, err


if __name__ == "__main__":
    bootloader = ZStudioBootloader()
    success, result = bootloader.initialize_system()

    if not success:
        print(f"\n❌ BOOT_CRASH | STATE: {bootloader.boot_state} | ERROR: {result}")
        sys.exit(1)

    print("\n--- PHASE 0 TOTAL LOCK | STANDBY FOR PHASE 1 ---")
    import time
print("🟢 SYSTEM STABLE: Engine Running")
try:
    while True:
        time.sleep(10) # Ye engine ko zinda rakhega
except KeyboardInterrupt:
    pass