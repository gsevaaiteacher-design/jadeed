"""
ROLE: 9/9 - INTEGRITY CHECKER (THE FINAL ROOT)
VERSION: 1.4.0 (STRICT SHA256 UNIFORMITY  DIAMOND LOCKED)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
-----------------------------------------------------------------------
STRICT DOMAIN: Unified SHA256 Hard-Anchoring, Fail-Closed, Root Trust.
-----------------------------------------------------------------------
"""
import os, hashlib, threading, time

class ZStudioIntegrityChecker:
    def __init__(self):
        #  ZYNQUAR BRANDING
        self.SIGNATURE = "ZYNQUAR ATELIER  DIAMOND INTEGRITY ROOT"
        self._lock = threading.Lock()
        
        #  UNIFIED GOLDEN HASH ANCHORS ( FIX: Strict SHA256 Only)
        # All hashes below are mandatory SHA256 (64-character hex strings)
        self.GOLDEN_MANIFEST = {
            "main_engine.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 
            "security_core/boot_security.py": "f72297193b2a543666d6d84f88106963249007f300c14f04905d4df192994e48",
            "security_core/hwid_lock.py": "7665793081e699564619923832791656847427ae41e4649b934ca495991b7852" 
        }
        
        self.IS_ACTIVE = False
        self.VIOLATION_DETECTED = False
        self.audit_log = []
        self.callback = None

    def initialize(self, callback_hook=None, strict_mode=True):
        """ FIX: Absolute Integrity Gate  Unified Crypto Standard."""
        try:
            self.callback = callback_hook
            results = self.verify_all()
            self.IS_ACTIVE = True
            
            if not all(results.values()):
                self.VIOLATION_DETECTED = True
                self._escalate_breach("ROOT_TRUST_COMPROMISED", "SHA256 Mismatch in Core Manifest.")
                if strict_mode:
                    return False #  TERMINATE BOOT PROCESS
            
            return True
        except Exception as e:
            self._escalate_breach("INIT_FATAL_FAILURE", str(e))
            return False

    def calculate_hash(self, file_path):
        """Unified SHA256 Engine with OS-Path Normalization."""
        sha256_hash = hashlib.sha256()
        try:
            # Normalize path for cross-OS compatibility
            norm_path = os.path.normpath(file_path)
            if not os.path.exists(norm_path): return "PATH_NOT_FOUND"
            
            with open(norm_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""): # 64KB Buffer
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except: return "READ_ERROR"

    def verify_all(self):
        """ FIX: Strict Uniform Verification (No MD5/Mixed Gaps)."""
        with self._lock:
            status = {}
            for path, golden_hash in self.GOLDEN_MANIFEST.items():
                actual_hash = self.calculate_hash(path)
                
                # Enforce SHA256 Equality
                is_valid = (actual_hash == golden_hash)
                status[path] = is_valid
                
                if not is_valid:
                    self._escalate_breach("INTEGRITY_MISMATCH", f"F: {path} | H: {actual_hash}")
                    
            return status

    def _log_audit(self, event, msg):
        entry = {"ts": time.time(), "ev": event, "m": msg}
        self.audit_log.append(entry)
        if len(self.audit_log) > 20: self.audit_log.pop(0)

    def _escalate_breach(self, error_type, details):
        """ FIX: Async Root-Alert Pipeline."""
        self._log_audit(error_type, details)
        if self.callback:
            threading.Thread(target=self.callback, args=(f"ROOT_ALERT_{error_type}", details), daemon=True).start()

    def get_status(self):
        with self._lock:
            return {
                "active": self.IS_ACTIVE,
                "trust_root": "VERIFIED" if not self.VIOLATION_DETECTED else "BREACHED",
                "audit": self.audit_log[-3:]
            }

def get_instance():
    return ZStudioIntegrityChecker()