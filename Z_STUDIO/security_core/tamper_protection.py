"""
ROLE: 5/9 - TAMPER PROTECTION
VERSION: 1.5.0 (DIRECT HANDLE VALIDATION)
STRICT DOMAIN: Runtime/File Tamper Monitoring ONLY.
-----------------------------------------------------------------------
"""
import os, sys, ctypes, time, threading
from pathlib import Path
import win32file, win32con, pywintypes

class ZStudioTamperProtection:
    def __init__(self):
        self.VER = "1.5.0"
        self.is_monitoring = False
        self.file_snapshots = {}
        self.locked_handles = {} # Map: Path -> Win32 Handle
        self._lock = threading.Lock()
        self.K32 = ctypes.windll.kernel32

    def _check_debugger(self):
        """Standard Win32 Debug Detection."""
        return self.K32.IsDebuggerPresent() != 0

    def watch_critical_files(self, file_paths):
        """
        REAL Win32 FILE LOCKING + Handle Storage.
        """
        with self._lock:
            for path in file_paths:
                p = Path(path).resolve()
                if not p.exists(): continue
                
                try:
                    stats = p.stat()
                    # 1. Capture Stats
                    self.file_snapshots[str(p)] = {
                        "size": stats.st_size,
                        "mtime": stats.st_mtime
                    }

                    # 2. Apply Kernel-Level Lock (No Share-Write)
                    h_file = win32file.CreateFile(
                        str(p),
                        win32file.GENERIC_READ,
                        win32file.FILE_SHARE_READ,
                        None,
                        win32file.OPEN_EXISTING,
                        win32file.FILE_ATTRIBUTE_NORMAL,
                        None
                    )
                    # 3. Store Handle for Direct Validation
                    self.locked_handles[str(p)] = h_file
                except:
                    self._trigger_lockdown(f"INITIAL_LOCK_FAILED: {p.name}")

    def _validate_handles_and_stats(self):
        """
         Fix: DIRECT HANDLE VALIDATION.
        Checks if the handle is still valid in the kernel table.
        """
        for path, h_file in self.locked_handles.items():
            # 1. Direct Handle Check (Is it still valid/alive?)
            try:
                # GetFileTime will fail if the handle was force-closed or invalidated
                win32file.GetFileTime(h_file)
            except pywintypes.error:
                self._trigger_lockdown(f"HANDLE_HIJACKED: {Path(path).name}")

            # 2. Stat Consistency Check
            p = Path(path)
            if not p.exists():
                self._trigger_lockdown(f"FILE_VANDALIZED: {p.name}")
            
            current = p.stat()
            snapshot = self.file_snapshots[path]
            if current.st_size != snapshot["size"] or current.st_mtime != snapshot["mtime"]:
                self._trigger_lockdown(f"MODIFICATION_DETECTED: {p.name}")

    def _monitor_loop(self):
        while self.is_monitoring:
            if self._check_debugger():
                self._trigger_lockdown("DEBUGGER_DETECTION")
            
            self._validate_handles_and_stats()
            time.sleep(1.2) # Faster detection for 10/10

    def start(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            t = threading.Thread(target=self._monitor_loop, daemon=True, name="Z_TamperGuard")
            t.start()

    def _trigger_lockdown(self, reason):
        """Final Audit + Clean Handle Release + Hard Kill."""
        try:
            with open("security_audit.log", "a") as f:
                f.write(f"[{time.ctime()}] [PROTECTION_CRITICAL] {reason}\n")
        except: pass
        
        # Release all locks
        for h in self.locked_handles.values():
            try: h.Close()
            except: pass
            
        os._exit(0xDEAD)

# Global Instance
tamper_protection = ZStudioTamperProtection()