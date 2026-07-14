"""
Z-STUDIO V19.0  SECURITY CORE (IDENTITY LAYER)
Author/Brand: ZYNQUAR ATELIER
Role: Apex Hardware Identity (Enforced Anti-VM, Zero-False-Positive)
-----------------------------------------------------------------------
"""

import subprocess
import hashlib
import sys
import getpass
import re
import uuid
import platform
import os

try:
    from logger_core import logger
except ImportError:
    import logging
    logger = logging.getLogger("Z_HWID_LOCK")

class ZStudioHWIDLock:
    """
     ROLE: The Unbreakable Machine Binder.
     Zero False Positive: "Microsoft" string risk removed.
     Multi-Layer Entropy: CPU + MAC + Disk + Board Fusion.
     Hard Enforcement: Strict block on VM/Spoofed environments.
    """

    def __init__(self):
        #  MASTER SEED (From V8 Core)
        self._INTERNAL_IV = "Z-STUDIO-V8-X99-HARDENING-CORE-2026"
        self._is_vm = False
        self._raw_profile = self._generate_apex_profile()
        
        #  ENFORCEMENT 1: VM BLOCK
        if self._is_vm:
            logger.critical("[SECURITY] VIRTUAL_ENVIRONMENT_DENIED")
            sys.exit("Critical Error: Z-Studio cannot run in a Virtual Machine for security reasons.")

        #  ENFORCEMENT 2: ENTROPY SHIELD (No Weak IDs)
        # If more than 1 core component is "NA", it's a spoof or failure.
        if self._raw_profile.count("NA") > 1:
            logger.critical("[SECURITY] INSUFFICIENT_HARDWARE_ENTROPY")
            sys.exit("Critical Error: Unreliable hardware signature detected.")

        self._secure_id = self._hash_hwid(self._raw_profile)

    def _normalize(self, val: str) -> str:
        """Strict alphanumeric normalization and garbage filtering."""
        if not val or len(val) < 4: return "NA"
        val = val.strip().upper()
        # Explicit VM vendors only (Removed 'Microsoft' to avoid false positives)
        garbage = ["TO BE FILLED", "NONE", "UNKNOWN", "00000000", "DEFAULT", "VMWARE", "VIRTUAL", "XEN", "QEMU", "VBOX"]
        if any(g in val for g in garbage): return "NA"
        return re.sub(r'[^A-Z0-9]', '', val)

    def _safe_query(self, cmd: list) -> str:
        """Stealth system query."""
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, creationflags=0x08000000)
            lines = [l.strip() for l in output.decode(errors="ignore").splitlines() if l.strip()]
            return lines[1] if len(lines) > 1 else "NA"
        except:
            return "NA"

    def _detect_vm(self, cpu: str, board: str) -> bool:
        """Targeted VM detection (Vendor Specific)."""
        # 1. Vendor check (Removed 'Microsoft' & 'Hyper-V' for stability)
        vm_vendors = ["VMWARE", "VIRTUALBOX", "VBOX", "QEMU", "XEN", "PARALLELS"]
        bios = self._safe_query(["wmic", "bios", "get", "serialnumber"]).upper()
        
        is_vm = any(v in cpu or v in board or v in bios for v in vm_vendors)
        
        # 2. Driver check (Hardware-level paths)
        vm_indicators = [
            "C:\\windows\\System32\\Drivers\\VBoxMouse.sys",
            "C:\\windows\\System32\\Drivers\\vmmouse.sys",
            "C:\\windows\\System32\\Drivers\\vboxguest.sys",
            "C:\\windows\\System32\\Drivers\\vmhgfs.sys"
        ]
        if any(os.path.exists(d) for d in vm_indicators):
            is_vm = True
            
        return is_vm

    def _generate_apex_profile(self) -> str:
        """Highest entropy profile generation."""
        # Hardware Layer
        cpu = self._normalize(self._safe_query(["wmic", "cpu", "get", "processorid"]))
        board = self._normalize(self._safe_query(["wmic", "baseboard", "get", "serialnumber"]))
        
        # Native Python Layer (Stable Fallback)
        mac_node = hex(uuid.getnode()).upper() if uuid.getnode() != 0xffffffffffff else "NA"
        
        # OS Layer
        os_serial = self._normalize(self._safe_query(["wmic", "os", "get", "serialnumber"]))

        # Check for VM before sealing
        if self._detect_vm(cpu, board):
            self._is_vm = True

        # FUSION (V8 Logic)
        # Structure: ZYN - CPU - BOARD - MAC - OS - USER - QUAR
        return f"ZYN-{cpu}-{board}-{mac_node}-{os_serial}-{getpass.getuser().upper()}-QUAR"

    def _hash_hwid(self, raw_id: str) -> str:
        """Salted SHA-256 (Master Bond)."""
        master_string = f"{self._INTERNAL_IV}:{raw_id}:{self._INTERNAL_IV}"
        return hashlib.sha256(master_string.encode()).hexdigest().upper()

    def get_current_hwid(self) -> str:
        return self._secure_id

    def validate_machine(self, authorized_hwid: str) -> bool:
        if not authorized_hwid: return False
        return self.get_current_hwid() == authorized_hwid.strip().upper()

# EXPORT SINGLETON (lazy initialization)
hwid_lock = None

def get_hwid_lock():
    global hwid_lock
    if hwid_lock is None:
        hwid_lock = ZStudioHWIDLock()
    return hwid_lock

#  ZYNQUAR ATELIER  [PHASE 4 - FILE 1: APEX LOCKED]