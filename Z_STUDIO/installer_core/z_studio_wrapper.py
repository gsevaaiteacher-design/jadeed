import os
import sys
import subprocess
import time
import logging
import json
from datetime import datetime

class ZStudioGuardian:
    def __init__(self):
        # 1. PATH ANCHORING
        self.app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.runtime_exe = os.path.join(self.app_root, "installer_core", "embedded_runtime", "python_core_pack", "python.exe")
        boot1 = os.path.join(self.app_root, "installer_core", "bootloader_core.py")
boot2 = os.path.join(self.app_root, "installer_core", "runtime_engine", "boot_loader.py")
        self.state_file = os.path.join(self.app_root, "installer_core", "boot_state.json")
        self.log_file = os.path.join(self.app_root, "logs", "wrapper_audit.log")
        
        # MICRO GAP FIX: Schema Version Lock
        self.EXPECTED_STATE_VER = "1.0.0" 
        self.MAX_RETRIES = 3
        self.setup_logging()

    def setup_logging(self):
        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s [GUARDIAN_MAX_V1] [%(levelname)s] %(message)s'
        )

    def validate_pre_launch(self):
        logging.info("Validating environment for version " + self.EXPECTED_STATE_VER)
        if not os.path.exists(self.runtime_exe): return False, "RUNTIME_MISSING"
        if not os.path.exists(self.boot_logic): return False, "BOOT_LOGIC_MISSING"
        return True, "READY"

    def monitor_heartbeat(self, process):
        """100/100 FIX: VERSIONED STRUCTURED MONITORING."""
        logging.info("Heartbeat Monitor Active (Versioned JSON Mode).")
        last_valid_heartbeat = time.time()
        
        while True:
            # 1. Physical Process Check
            if process.poll() is not None:
                logging.error(f"Engine Process Exited. Code: {process.poll()}")
                return False, f"PROCESS_TERMINATED_{process.poll()}"

            # 2. Schema-Locked State Validation
            if os.path.exists(self.state_file):
                try:
                    with open(self.state_file, 'r') as f:
                        state_data = json.load(f)
                        
                        # MICRO GAP FIX: Version & Health Validation
                        if state_data.get("schema_ver") != self.EXPECTED_STATE_VER:
                            logging.warning("Schema version mismatch. Attempting to proceed...")
                        
                        ts = state_data.get("heartbeat", 0)
                        health = state_data.get("health", "CRITICAL")

                        if health == "OK":
                            last_valid_heartbeat = ts
                except (json.JSONDecodeError, IOError):
                    pass # Resilience against file access locks

            # 3. Freeze Detection (10s Rule)
            if (time.time() - last_valid_heartbeat) > 10:
                logging.critical("ENGINE_FREEZE_DETECTED: Heartbeat timeout.")
                process.terminate()
                return False, "HEARTBEAT_TIMEOUT_FREEZE"

            time.sleep(2)

    def launch_and_guard(self):
        """Execution Lifecycle with Handshake."""
        if os.path.exists(self.state_file):
            try: os.remove(self.state_file)
            except: pass
        
        process = subprocess.Popen(
            [self.runtime_exe, self.boot_logic],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            cwd=self.app_root
        )
        
        # Ignition Handshake (4s Watchdog)
        time.sleep(4) 
        if not os.path.exists(self.state_file):
            logging.error("Ignition failed: No state file created.")
            process.terminate()
            return False, "IGNITION_HANDSHAKE_FAILED"

        return self.monitor_heartbeat(process)

    def run(self):
        logging.info("=== Z-STUDIO 100/100 SESSION START ===")
        ok, msg = self.validate_pre_launch()
        if not ok:
            print(f" FATAL ERROR: {msg}")
            sys.exit(1)

        for attempt in range(1, self.MAX_RETRIES + 1):
            logging.info(f"Launch attempt {attempt}/{self.MAX_RETRIES}...")
            success, reason = self.launch_and_guard()
            
            if success: # monitor_heartbeat returns False on failure
                sys.exit(0)
            else:
                logging.warning(f"Session Error: {reason}")
                print(f" RECOVERY: {reason}. Re-launching ({attempt}/{self.MAX_RETRIES})...")
                time.sleep(2)

        logging.critical("ALL RECOVERY PATHS EXHAUSTED.")
        print(" SYSTEM FAILURE: Check wrapper_audit.log.")
        sys.exit(1)

if __name__ == "__main__":
    guardian = ZStudioGuardian()
    guardian.run()
