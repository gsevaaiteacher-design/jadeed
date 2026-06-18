import os
import sys
import subprocess
import time
import logging
import json
from datetime import datetime


class ZStudioGuardian:
    def __init__(self):
        # =========================
        # SAFE ROOT RESOLUTION
        # =========================
        self.app_root = os.path.dirname(os.path.abspath(__file__))

        self.installer_core = os.path.join(self.app_root, "installer_core")

        # =========================
        # RUNTIME EXECUTABLE
        # =========================
        self.runtime_exe = os.path.join(
            self.installer_core,
            "embedded_runtime",
            "python_core_pack",
            "python.exe"
        )

        # =========================
        # BOOT LOGIC (SAFE SELECTION)
        # =========================
        boot_a = os.path.join(self.installer_core, "bootloader_core.py")
        boot_b = os.path.join(self.installer_core, "runtime_engine", "boot_loader.py")

        if os.path.exists(boot_a):
            self.boot_logic = boot_a
        elif os.path.exists(boot_b):
            self.boot_logic = boot_b
        else:
            raise Exception("BOOT_LOGIC_NOT_FOUND")

        # =========================
        # STATE + LOG FILES
        # =========================
        self.state_file = os.path.join(self.installer_core, "boot_state.json")
        self.log_file = os.path.join(self.app_root, "logs", "wrapper_audit.log")

        self.EXPECTED_STATE_VER = "1.0.0"
        self.MAX_RETRIES = 3

        self.setup_logging()

    # =========================
    # LOGGING
    # =========================
    def setup_logging(self):
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s [GUARDIAN_MAX_V1] [%(levelname)s] %(message)s'
        )

    # =========================
    # PRE-LAUNCH VALIDATION
    # =========================
    def validate_pre_launch(self):
        logging.info("Validating environment")

        if not os.path.isfile(self.runtime_exe):
            return False, "RUNTIME_MISSING"

        if not os.path.isfile(self.boot_logic):
            return False, "BOOT_LOGIC_MISSING"

        return True, "READY"

    # =========================
    # HEARTBEAT MONITOR (STABLE)
    # =========================
    def monitor_heartbeat(self, process):
        logging.info("Heartbeat Monitor Started")

        last_valid_heartbeat = time.time()

        while True:
            exit_code = process.poll()

            # -------------------------
            # PROCESS EXIT CHECK
            # -------------------------
            if exit_code is not None:
                if exit_code == 0:
                    logging.info("Engine Exit OK (handover success)")
                    return True, "SUCCESS_HANDOVER"

                logging.error(f"Engine Crash Code: {exit_code}")
                return False, f"PROCESS_TERMINATED_{exit_code}"

            # -------------------------
            # STATE FILE READ
            # -------------------------
            if os.path.exists(self.state_file):
                try:
                    with open(self.state_file, "r", encoding="utf-8") as f:
                        state_data = json.load(f)

                    if isinstance(state_data, dict):
                        status = state_data.get("status")
                        health = state_data.get("health")

                        # SAFE CHECK (same logic, but stable grouping)
                        if status == "OK" or health == "OK":
                            logging.info("System Ready via state file")
                            return True, "SYSTEM_READY"

                        ts = state_data.get("heartbeat")
                        if isinstance(ts, (int, float)):
                            last_valid_heartbeat = float(ts)

                except Exception as e:
                    logging.warning(f"State read error: {e}")

            # -------------------------
            # FREEZE DETECTION
            # -------------------------
            if (time.time() - last_valid_heartbeat) > 15:
                logging.critical("ENGINE FREEZE DETECTED")
                try:
                    process.terminate()
                except:
                    pass
                return False, "HEARTBEAT_TIMEOUT_FREEZE"

            time.sleep(2)

    # =========================
    # LAUNCH ENGINE
    # =========================
    def launch_and_guard(self):
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except:
                pass

        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NO_WINDOW

        try:
            process = subprocess.Popen(
                [self.runtime_exe, self.boot_logic],
                creationflags=flags,
                cwd=self.app_root
            )
        except Exception as e:
            return False, f"PROCESS_SPAWN_FAILED: {e}"

        time.sleep(3)

        if not os.path.exists(self.state_file):
            logging.error("No state file created")
            try:
                process.terminate()
            except:
                pass
            return False, "IGNITION_HANDSHAKE_FAILED"

        return self.monitor_heartbeat(process)

    # =========================
    # MAIN RUNNER
    # =========================
    def run(self):
        logging.info("SESSION START")

        ok, msg = self.validate_pre_launch()
        if not ok:
            print(f" FATAL ERROR: {msg}")
            sys.exit(1)

        for attempt in range(1, self.MAX_RETRIES + 1):

            logging.info(f"Attempt {attempt}/{self.MAX_RETRIES}")

            success, reason = self.launch_and_guard()

            if success is True:
                print(" SYSTEM STABLE: Engine Running")
                sys.exit(0)

            logging.warning(f"Recovery Triggered: {reason}")
            print(f" RECOVERY: {reason} ({attempt}/{self.MAX_RETRIES})")

            time.sleep(2)

        logging.critical("ALL RECOVERY FAILED")
        print(" SYSTEM FAILURE: Check logs")
        sys.exit(1)


if __name__ == "__main__":
    guardian = ZStudioGuardian()
    guardian.run()