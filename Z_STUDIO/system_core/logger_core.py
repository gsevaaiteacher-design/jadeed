import os
from datetime import datetime
import sys
import logging
import uuid
import threading
import queue
import traceback
import json


#  GLOBAL ENCODING GUARD (Prevents redundant reconfigure overhead)
if getattr(sys, "_z_studio_encoded", None) is None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    sys._z_studio_encoded = True


class SafeFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "req_id"):
            record.req_id = "SYS-" + uuid.uuid4().hex[:6]
        return super().format(record)

#  GLOBAL ROOT LOGGER PATCH (Hardened against duplicate import/reload risks)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    handler = logging.StreamHandler()
    formatter = SafeFormatter('%(asctime)s | %(levelname)s | [ID:%(req_id)s] | %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
else:
    for h in root_logger.handlers[:]:
        if not isinstance(h.formatter, SafeFormatter):
            root_logger.removeHandler(h)


class LoggerCore:
    """
     SYSTEM CORE  Logger Module (V4 AI INDUSTRIAL ENGINE)
     Provides Real-time Async Feed to UI Dashboard (Zero Blocking)
     Feeds Transaction Core for Crash Recovery with Auto-Snapshot Dump
     Multi-Process & Thread-Safe Non-Blocking Queue Pipeline
     Logic based on Z-STUDIO V12.3 Master Blueprint
    """
    def __init__(self, log_dir="core_assets/logs"):
        # Blueprint Path Compliance
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.snapshot_dir = os.path.join(self.log_dir, "crash_snapshots")
        os.makedirs(self.snapshot_dir, exist_ok=True)

        # Unique session log for Crash Recovery Core
        self.log_file = os.path.join(
            self.log_dir, 
            f"z_studio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        # internal engine setup
        self._internal_logger = logging.getLogger("Z-STUDIO-CORE")
        self._internal_logger.setLevel(logging.DEBUG)
        
        #  Logger Isolation Tag
        self._internal_logger.propagate = False

        #  Thread-Safety & Recursion Gates
        self._lock = threading.RLock()
        self._logging = False

        if not self._internal_logger.handlers:
            f_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = SafeFormatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s | req_id=%(req_id)s')
            f_handler.setFormatter(formatter)
            self._internal_logger.addHandler(f_handler)

        #  V4 ENTERPRISE ASYNC PIPELINE SETUP
        self._log_queue = queue.Queue(maxsize=10000)
        self._shutdown_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._async_worker, daemon=True, name="Z-Logger-Worker")
        self._worker_thread.start()

    def _async_worker(self):
        """Background daemon processor for zero-blocking log execution."""
        while not self._shutdown_event.is_set() or not self._log_queue.empty():
            try:
                try:
                    item = self._log_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                level, module, message, timestamp = item
                msg_payload = f"[{module}] {message}"
                lvl = level.upper()

                #  Exception-Safe Internal Dispatch
                try:
                    if lvl == "INFO": self._internal_logger.info(msg_payload)
                    elif lvl == "ERROR": self._internal_logger.error(msg_payload)
                    elif lvl == "DEBUG": self._internal_logger.debug(msg_payload)
                    elif lvl == "WARNING": self._internal_logger.warning(msg_payload)
                except Exception as internal_err:
                    sys.stderr.write(f"CRITICAL: Internal File Logger Core Fault -> {str(internal_err)}\n")
                    sys.stderr.flush()

                # LIVE BRIDGE: Safe Unicode Printing for UI Dashboard
                try:
                    line = f"LOG_EVENT >> {timestamp.strftime('%H:%M:%S')} | {lvl} | {msg_payload}\n"
                    sys.stdout.write(line)
                    sys.stdout.flush()
                except UnicodeEncodeError:
                    clean_line = line.encode('ascii', 'ignore').decode('ascii')
                    sys.stdout.write(clean_line)
                    sys.stdout.flush()

                self._log_queue.task_done()
            except Exception as worker_fault:
                sys.stderr.write(f"FATAL: Logger Async Worker Panic -> {str(worker_fault)}\n")
                sys.stderr.flush()

    def log(self, level, module, message):
        """Asynchronously enqueues the log request ensuring 0% UI block risk."""
        with self._lock:
            if self._logging:
                return
            self._logging = True

        try:
            # Enqueue task quickly along with current high-res timestamp
            self._log_queue.put_nowait((level, module, message, datetime.now()))
        except queue.Full:
            # Fallback if queue fills up under extreme backpressure
            sys.stderr.write(f" LOGGER QUEUE OVERFLOW: Drop prevented, printing directly -> [{module}] {message}\n")
            sys.stderr.flush()
        finally:
            with self._lock:
                self._logging = False

    def dump_crash_snapshot(self, context_name, exception=None):
        """ V4 AUTO SNAPSHOT DUMP ENGINE: Captures state payload on system panic."""
        snapshot_file = os.path.join(
            self.snapshot_dir,
            f"crash_{context_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "context": context_name,
                "error": str(exception) if exception else "Manual Trigger",
                "traceback": traceback.format_exc() if exception else None,
                "active_threads": [t.name for t in threading.enumerate()],
                "process_id": os.getpid()
            }
            with open(snapshot_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
            self.error(f" CRASH SNAPSHOT DUMPED SUCCESSFULLY -> {snapshot_file}", mod="RECOVERY-CORE")
            return snapshot_file
        except Exception as dump_err:
            sys.stderr.write(f"CRITICAL: Crash Snapshot Writer Failed -> {str(dump_err)}\n")
            sys.stderr.flush()
            return None

    # --- COMPATIBILITY LAYER FOR SYSTEM CORE MODULES (HARDENED) ---
    def info(self, msg, mod="CORE", *args, **kwargs): 
        self.log("INFO", mod, msg)

    def error(self, msg, mod="CORE", *args, **kwargs): 
        self.log("ERROR", mod, msg)

    def warning(self, msg, mod="CORE", *args, **kwargs): 
        self.log("WARNING", mod, msg)

    def debug(self, msg, mod="CORE", *args, **kwargs): 
        self.log("DEBUG", mod, msg)

    def get_last_logs(self, count=20):
        """Dashboard API for 'Execution Console' rendering."""
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.readlines()[-count:]
        except Exception:
            return []

    def shutdown(self):
        """Gracefully flushes the async queue before termination."""
        self._shutdown_event.set()
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        
    
#  MASTER INSTANCE (Single Object Strategy)
# This ensures every file in the Z-STUDIO chain uses the SAME logger instance.
logger = LoggerCore()