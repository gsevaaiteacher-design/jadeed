#  FILE_ID: ZS_SESSION_ENGINE_V31_V8_V8_FINAL_HARDENED_STABILIZED
#  ROLE: ABSOLUTE-BOUNDARY-SAFETY + STRICT-RECOVERY + ATOMIC-POINTER-LOCK
#  ZYNQUAR ATELIER (C) 2026  AUTHOR: RIJVAN ALI

import os
import json
import struct
import hashlib
import logging

logger = logging.getLogger("Z_SESSION_V31_V8_FINAL")

class WALCorruptionException(Exception):
    """Raised when the Circuit Breaker detects unrecoverable corruption."""
    pass

class SessionManager:
    def __init__(self, base_path: str = "core_assets/sessions/"):
        self.MAGIC = b"\x5A\x51\x41\x52"
        self.frame_struct = struct.Struct(">4sI32s")
        self.MAX_FRAME_SIZE = 50 * 1024 * 1024 
        
        self.ctx_path = os.path.join(base_path, "recovery_ctx.json")
        self.last_good_pos = 0
        self.last_good_epoch = 0
        
        # INDUSTRIAL RECOVERY STATE (Strict Mode)
        self.severity_score = 0
        self.THRESHOLD = 25000
        self.IS_QUARANTINED = False 
        
        self._load_recovery_context()

    def _load_recovery_context(self):
        if os.path.exists(self.ctx_path):
            try:
                with open(self.ctx_path, 'r') as f:
                    data = json.load(f)
                    self.last_good_pos = data.get("pos", 0)
                    self.last_good_epoch = data.get("epoch", 0)
            except: pass

    def _try_recover_from_quarantine(self):
        """ FIX 3: STRICT HARDENING (Higher safety threshold for recovery)."""
        if self.IS_QUARANTINED:
            # Recovery only under 5000 severity + verified history
            if self.severity_score < 5000 and self.last_good_pos > 0:
                self.IS_QUARANTINED = False
                logger.info("WAL RECOVERY: System passed strict integrity check. Quarantine lifted.")

    def _save_recovery_context(self, force=False):
        """Atomic Persistence + Exponential Smoothing."""
        if force or (self.severity_score == 0):
            tmp = f"{self.ctx_path}.tmp"
            try:
                with open(tmp, 'w') as f:
                    json.dump({"pos": self.last_good_pos, "epoch": self.last_good_epoch}, f)
                os.replace(tmp, self.ctx_path)
                
                # Industrial Exponential Decay
                self.severity_score = int(self.severity_score * 0.85)
                self._try_recover_from_quarantine()
            except Exception as e:
                logger.error(f"Checkpoint Write Fault: {e}")

    def _resync_iterative(self, f) -> bool:
        """Industrial Resync V8-Final: Atomic Alignment Scan."""
        window_size = len(self.MAGIC)
        attempts = 0

        while attempts < 5000:
            if self.severity_score > self.THRESHOLD:
                self.IS_QUARANTINED = True
                raise WALCorruptionException("Circuit breaker: Critical WAL failure.")

            base_pos = f.tell()
            chunk = f.read(131072) 
            if not chunk: return False

            idx = chunk.find(self.MAGIC)
            if idx != -1:
                target_pos = base_pos + idx
                
                #  FIX 2: SIMPLIFIED DETERMINISTIC PEEK
                f.seek(target_pos)
                peek_raw = f.read(self.frame_struct.size)
                f.seek(target_pos) # Strict restore
                
                if len(peek_raw) == self.frame_struct.size:
                    m, l, d = self.frame_struct.unpack(peek_raw)
                    # Absolute Heuristic Guard
                    if m == self.MAGIC and 0 < l <= self.MAX_FRAME_SIZE and d != b'\x00'*32:
                        return True
                
                # Failed match: Apply Bounded Stride
                self.severity_score += 50
                step = min(16, 1 + (self.severity_score // 1000))
                f.seek(target_pos + step)
                continue

            if len(chunk) >= window_size:
                f.seek(base_pos + len(chunk) - (window_size - 1))
            
            self.severity_score = max(0, self.severity_score - 1)
            attempts += 1
        return False

    def _calculate_stream_hash(self, f, length, payload_start):
        """Context-Safe Atomic Streaming Hash."""
        original_pos = f.tell()
        try:
            f.seek(payload_start)
            sha = hashlib.sha256()
            remaining = length
            while remaining > 0:
                chunk = f.read(min(remaining, 65536))
                if not chunk: break
                sha.update(chunk)
                remaining -= len(chunk)
            return sha.digest()
        finally:
            f.seek(original_pos)

    def _read_next_valid_frame(self, f):
        """Final Deterministic Replay Kernel."""
        if self.IS_QUARANTINED:
            self._try_recover_from_quarantine()
            if self.IS_QUARANTINED: raise WALCorruptionException("Kernel Locked.")

        while True:
            header_start = f.tell()
            header_raw = f.read(self.frame_struct.size)
            if not header_raw: return None

            try:
                if len(header_raw) < self.frame_struct.size:
                    f.seek(header_start + 1)
                    if not self._resync_iterative(f): return None
                    continue

                magic, length, digest_stored = self.frame_struct.unpack(header_raw)
                if magic != self.MAGIC or 0 == length or length > self.MAX_FRAME_SIZE:
                    self.severity_score += 100
                    f.seek(header_start + 1)
                    if not self._resync_iterative(f): return None
                    continue

                payload_offset = header_start + self.frame_struct.size
                
                # Integrity Check (Pointer-Safe)
                if self._calculate_stream_hash(f, length, payload_offset) != digest_stored:
                    self.severity_score += 500
                    #  FIX 1: ABSOLUTE BOUNDARY JUMP (Next potential frame start)
                    f.seek(payload_offset) 
                    if not self._resync_iterative(f): return None
                    continue

                # Extraction with state update
                f.seek(payload_offset) 
                payload = f.read(length)
                
                try:
                    data = json.loads(payload.decode('utf-8', errors='strict'))
                    self.last_good_pos = f.tell()
                    self.severity_score = int(self.severity_score * 0.90) # Healthy frames heal faster
                    self._save_recovery_context() 
                    return data
                except:
                    self.severity_score += 100
                    f.seek(header_start + 1)
                    if not self._resync_iterative(f): return None
                    continue

            except WALCorruptionException: raise
            except Exception as e:
                logger.error(f"Kernel Panic: {e}")
                self.severity_score += 200
                f.seek(header_start + 1)
                if not self._resync_iterative(f): return None
                continue
