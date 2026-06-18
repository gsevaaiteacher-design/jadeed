"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 3: model_safety_layer.py
ROLE: Model safety aur integrity verify karna (THE SHIELD)
-----------------------------------------------------------------------
"""

import os
import hashlib

class SecurityError(Exception):
    """Raised when a model fails safety/security protocols."""
    pass

class ModelSafetyLayer:
    """
    ZYNQUAR RULE: Shield Layer only.
    No model loading, no inference, no side effects.
    """
    def __init__(self, runtime_bridge=None, debug_mode=False):
        self.runtime = runtime_bridge
        self.debug_mode = debug_mode
        # Trusted SHA256 hashes (Populated by Phase 1 Registry)
        self.security_manifest = {}

    # YE WALA METHOD ADD KARO (Bridge)
    def validate(self, task):
        """
        Engine Compatibility Bridge: Maps 'validate' call to 'verify_integrity'.
        """
        # Engine ke task se arguments extract karo
        model_handle = getattr(self, 'static_active_handle', None) # Engine se handle lo
        model_path = task.get("model_path", "")
        model_id = task.get("model_id", "ZAI_CORE_V12.3")
        
        # Asli logic call karo
        return self.verify_integrity(model_handle, model_path, model_id)

    def verify_integrity(self, model_handle, absolute_path, model_id=None):
        """
         INPUT: model_handle, absolute_path, model_id
         LOGIC: Physical Check -> Runtime Validation -> Hash Check
         OUTPUT: bool (Safe or Unsafe)
        """
        if not model_handle:
            return False

        try:
            # 1. Physical Integrity Check (Size & Presence)
            if not os.path.exists(absolute_path) or os.path.getsize(absolute_path) == 0:
                return False

            # 2. Runtime Handle Validation
            # Checks if the model object is actually active in VRAM/RAM
            if self.runtime and hasattr(self.runtime, 'validate_handle'):
                if not self.runtime.validate_handle(model_handle):
                    raise SecurityError("[ZYNQUAR_SAFETY] Model handle invalid.")

            # 3. Cryptographic Tamper Detection
            if model_id and model_id in self.security_manifest:
                expected_hash = self.security_manifest[model_id]
                actual_hash = self.get_file_hash(absolute_path)
                
                # Check for empty or failed hash reading
                if not actual_hash:
                    return False
                    
                if expected_hash != actual_hash:
                    raise SecurityError(f"[ZYNQUAR_SAFETY] Hash mismatch for {model_id}")

            return True

        except Exception as e:
            # Silent failure for Phase 2 pipeline stability
            # Logging is handled by Phase 1 via return signal
            if self.debug_mode:
                # Polished Debug Hook
                print(f"[SHIELD_DEBUG] {str(e)}")
            return False

    def get_file_hash(self, path):
        """
        Helper: Memory-efficient SHA256 integrity calculation.
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                # 4KB blocks to keep memory footprint low
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except (IOError, OSError):
            return None

#  ZYNQUAR ATELIER  [FILE 3: POLISHED & LOCKED]
