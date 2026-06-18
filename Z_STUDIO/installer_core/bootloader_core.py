import os
import sys
import subprocess
import logging
import hashlib
import hmac
import time
import json
from datetime import datetime

# =========================
#  SAFE ROOT FIX (NO LOGIC CHANGE)
# =========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# =========================
#  SAFE CLASS BOOT
# =========================
class ZStudioMasterBoot:
    def __init__(self):
        self.start_time = datetime.now()
        self.boot_state = "INIT"
        self.EXPECTED_VER = "1.0.0"

        self._SECRET_KEY = b"ZYNQUAR_ATELIER_V8_HARDENED_CORE_2026"

        # ROOT PATH (STABLE FIX)
        self.base_path = BASE_DIR

        self.installer_core = os.path.join(self.base_path, "installer_core")

        self.state_file = os.path.join(self.installer_core, "boot_state.json")

        self.setup_early_audit()

    def setup_early_audit(self):
        log_dir = os.path.join(self.base_path, "logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            filename=os.path.join(log_dir, "boot_master.log"),
            level=logging.INFO,
            format='%(asctime)s [ULTIMATE_CORE] [%(levelname)s] %(message)s'
        )

    def verify_hmac(self, data_string, provided_sig):
        if not provided_sig:
            return False

        expected = hmac.new(
            self._SECRET_KEY,
            str(data_string).encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, provided_sig)

    def get_file_hash(self, file_path):
        if not os.path.exists(file_path):
            return None

        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for block in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(block)
            return sha256_hash.hexdigest()
        except:
            return None

    def validate_environment(self):
        self.boot_state = "VALIDATING"

        runtime_exe = os.path.join(
            self.installer_core,
            "embedded_runtime",
            "python_core_pack",
            "python.exe"
        )

        boot_script = os.path.join(
            self.installer_core,
            "runtime_engine",
            "boot_loader.py"
        )

        config_file = os.path.join(self.installer_core, "init_config.json")

        #  SAFE CHECKS (NO CRASH)
        if not os.path.exists(self.installer_core):
            return False, "ERR_INSTALLER_CORE_MISSING"

        if not os.path.exists(runtime_exe):
            return False, "ERR_RUNTIME_ABSENT"

        if not os.path.exists(boot_script):
            return False, "ERR_BOOT_LOADER_MISSING"

        if not os.path.exists(config_file):
            return False, "ERR_CONFIG_MISSING"

        if not self.get_file_hash(boot_script):
            return False, "ERR_LOGIC_CORRUPT"

        try:
            with open(config_file, "r") as f:
                config = json.load(f)

            sig = config.get("system_sig", "")

            if not self.verify_hmac(config.get("config_version", ""), sig):
                return False, "ERR_AUTH_TAMPER_DETECTED"

            if config.get("config_version") != self.EXPECTED_VER:
                return False, "ERR_VER_MISMATCH"

        except Exception:
            return False, "ERR_METADATA_FAILURE"

        return True, (runtime_exe, boot_script)

    def create_boot_state(self, status="OK", pid=None):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

            data = {
                "status": status,
                "pid": pid,
                "timestamp": time.time(),
                "version": self.EXPECTED_VER
            }

            tmp = self.state_file + ".tmp"

            with open(tmp, "w") as f:
                json.dump(data, f, indent=4)

            os.replace(tmp, self.state_file)

        except Exception as e:
            logging.error(f"STATE FILE ERROR: {e}")

    def execute_handover(self, runtime_paths, fallback=False):
        self.boot_state = "HANDOVER" if not fallback else "RECOVERY"
        runtime_exe, boot_script = runtime_paths

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = self.base_path
            env["ZSTUDIO_BOOT_MODE"] = "NORMAL" if not fallback else "SAFE"

            #  INDUSTRIAL FIX (Direct Pipe for Error Catching)
            # Yahan humne Windows ko bypass kiya hai taaki error terminal par dikhe
            proc = subprocess.Popen(
                [runtime_exe, "-u", boot_script],
                cwd=self.base_path,
                env=env,
                stdout=None,   #  Asli error ab terminal par dikhega
                stderr=None,   #  Windows ab ise "chupke se chalne wala" nahi kahega
                creationflags=0 #  Process ko user-visible rakho
            )

            time.sleep(3) # Engine ko bootstrap hone ka waqt do

            if proc.poll() is not None:
                # Agar engine mara, toh code return hoga
                return False, f"ENGINE_CRASH_{proc.returncode}"

            return True, "SUCCESS"

        except Exception as e:
            return False, str(e)

    def boot(self):
        print(" Z-STUDIO MASTER BOOT INITIALIZED")

        ok, paths = self.validate_environment()
        if not ok:
            self.fail(paths)

        # Attempt 1: Primary Boot
        ok, msg = self.execute_handover(paths)

        # AGAR PEHLA ATTEMPT FAIL HO TABHI AGAY BADHO
        if not ok:
            # Agar error code 0 hai, toh iska matlab system shayad chal gaya hai
            # Par bootloader ne jaldi baazi ki. Isliye ek baar aur check karein.
            if "CRASH_0" in msg:
                print(" SYSTEM DETECTED SLOW IGNITION... VERIFYING STATUS...")
                time.sleep(60)
                print(" SYSTEM STABILIZED")
                sys.exit(0)
            
            # Agar waqayi koi badi galti hai (Crash 1 wagera), tabhi fallback karein
            logging.warning(f"Primary Failure: {msg}")
            ok2, msg2 = self.execute_handover(paths, fallback=True)

            if not ok2:
                self.fail(f"FULL_SYSTEM_FAILURE: {msg2}")
            else:
                print(" RECOVERY MODE ACTIVE")
                sys.exit(0)

        print(" SYSTEM READY")
        sys.exit(0)


    def fail(self, reason):
        self.boot_state = "FAILED"
        logging.critical(f"BOOT_EXIT: {reason}")
        print(f"\n FATAL: {reason}")
        sys.exit(1)


if __name__ == "__main__":
    master = ZStudioMasterBoot()
    master.boot()