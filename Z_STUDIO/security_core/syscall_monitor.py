"""
ROLE: 8/9 - SYSCALL MONITOR (OS WATCHDOG)
VERSION: 1.2.0 (DIAMOND  GRANULAR AUDIT & STORM CONTROL)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
-----------------------------------------------------------------------
STRICT DOMAIN: Granular OS Interaction Monitoring & Anti-Storm Escalation.
-----------------------------------------------------------------------
"""
import os, sys, threading, time, psutil

class ZStudioSyscallMonitor:
    def __init__(self):
        #  ZYNQUAR BRANDING
        self.SIGNATURE = "ZYNQUAR ATELIER  SYSCALL WATCHDOG"
        self._lock = threading.Lock()
        
        #  GRANULAR DEFINITIONS
        self.SENSITIVE_PATHS = ["C:\\WINDOWS\\SYSTEM32", "C:\\WINDOWS\\SYSWOW64", "\\ETC\\PASSWD"]
        self.DANGEROUS_EXT = [".EXE", ".BAT", ".PS1", ".VBS", ".REG", ".SH"]
        
        #  WHITELIST (Refined)
        self.ALLOWED_IPS = ["127.0.0.1", "localhost"]
        self.ALLOWED_PORTS = [443, 80] # Standard Secure Update Ports
        
        self.IS_ACTIVE = False
        self.audit_buffer = []
        self._stop_event = threading.Event()
        self._proc = psutil.Process(os.getpid())
        self._alert_count_window = 0 # Storm protection

    def initialize(self, callback=None):
        """Activates Diamond-Level OS Monitoring."""
        try:
            self.callback = callback
            threading.Thread(target=self._watchdog_loop, daemon=True).start()
            self.IS_ACTIVE = True
            return True
        except: return False

    def _watchdog_loop(self):
        """ STAGE 8: High-Precision OS Surveillance."""
        while not self._stop_event.is_set():
            try:
                self._alert_count_window = 0 # Reset storm counter
                self._audit_io_behavior()
                self._audit_network_boundary()
                self._audit_process_spawns()
            except: pass
            time.sleep(3) 

    def _audit_io_behavior(self):
        """Granular File Handle Audit."""
        try:
            for f in self._proc.open_files():
                path = f.path.upper()
                if any(sp in path for sp in self.SENSITIVE_PATHS):
                    self._report_threat("CRITICAL", "OS_FILE_ACCESS", path)
        except: pass

    def _audit_network_boundary(self):
        """ FIX: Port-Level Granular Filtering."""
        try:
            for conn in self._proc.connections(kind='inet'):
                if conn.status == 'ESTABLISHED':
                    remote_ip = conn.raddr.ip if hasattr(conn.raddr, 'ip') else ""
                    remote_port = conn.raddr.port if hasattr(conn.raddr, 'port') else 0
                    
                    if remote_ip and remote_ip not in self.ALLOWED_IPS:
                        if remote_port not in self.ALLOWED_PORTS:
                            self._report_threat("MEDIUM", "NETWORK_EGRESS_UNAUTHORIZED", f"{remote_ip}:{remote_port}")
        except: pass

    def _audit_process_spawns(self):
        """ FIX: Command-Line & PID Integrity Audit."""
        try:
            for child in self._proc.children(recursive=True):
                name = child.name().upper()
                cmdline = " ".join(child.cmdline())
                if any(ext in name for ext in self.DANGEROUS_EXT) or "POWERSHELL" in cmdline.upper():
                    self._report_threat("HIGH", "EXECUTION_SPAWN_DETECTED", f"PID:{child.pid} | CMD:{cmdline}")
        except: pass

    def _report_threat(self, severity, t_type, details):
        """ FIX: Storm-Protected Reporting."""
        with self._lock:
            if self._alert_count_window > 20: return # Throttle if too many alerts in 3s
            self._alert_count_window += 1

            entry = {"ts": time.strftime("%H:%M:%S"), "sev": severity, "type": t_type, "data": details}
            self.audit_buffer.append(entry)
            if len(self.audit_buffer) > 100: self.audit_buffer.pop(0)
            
            if self.callback:
                threading.Thread(target=self.callback, args=(f"WATCHDOG_{severity}", entry), daemon=True).start()

    def get_status(self):
        with self._lock:
            return {"active": self.IS_ACTIVE, "alerts_in_buffer": len(self.audit_buffer)}

    def shutdown(self):
        self._stop_event.set()
        self.IS_ACTIVE = False

def get_instance():
    return ZStudioSyscallMonitor()