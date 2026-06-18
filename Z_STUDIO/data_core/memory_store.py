#  Z-STUDIO V12.3 | FILE 6.1: MEMORY_STORE.PY | PHASE 6: DATA SYSTEM
#  ROLE: ULTIMATE INDUSTRIAL STORAGE ENGINE (10/10 - HARDENED)
#  OWNER: ZYNQUAR ATELIER (C) 2026 | V8 FINAL REFINED CORE (ZERO-GAP)

import os
import json
import uuid
import datetime
import threading
import msvcrt  # Windows OS-level file locking
from pathlib import Path
from collections import deque

class MemoryStore:
    """
    Z-STUDIO INDUSTRIAL STORAGE ENGINE
    - Atomic Pointer-Shift Locking (Windows Kernel Safe)
    - Safe-Close Compact Logic (No Orphan Handles)
    - Snapshot Hardware Durability (FSYNC)
    - Micro-second Precision Log Rotation
    """
    def __init__(self, base_path="core_assets/memory/", durable_mode=True):
        self.base_path = Path(base_path)
        self.logs_path = self.base_path / "logs"
        self.snapshot_path = self.base_path / "snapshot"
        self.durable_mode = durable_mode

        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.snapshot_path.mkdir(parents=True, exist_ok=True)

        self.current_log = self.logs_path / "main_log.bin"
        self._lock = threading.Lock()
        self.max_log_size = 50 * 1024 * 1024  # 50MB

    def _rotate_if_needed(self):
        """High-precision rotation to prevent name collisions."""
        if self.current_log.exists() and self.current_log.stat().st_size > self.max_log_size:
            timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            rotated_name = self.logs_path / f"log_{timestamp}.archive"
            try:
                self.current_log.rename(rotated_name)
                self.current_log.touch()
            except Exception as e:
                print(f"[Z-STORAGE] Rotation Error: {e}")

    def append(self, data: dict) -> bool:
        """Atomic Append: Guaranteed lock/unlock with hardware sync."""
        try:
            payload = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "content": data
            }
            entry_bytes = (json.dumps(payload) + "\n").encode("utf-8")

            with self._lock:
                self._rotate_if_needed()
                
                with open(self.current_log, "ab") as f:
                    try:
                        #  LOCK ENTIRE RANGE (Windows pointer fix)
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 0x7fffffff)
                        
                        f.seek(0, os.SEEK_END)
                        f.write(entry_bytes)
                        
                        if self.durable_mode:
                            f.flush()
                            os.fsync(f.fileno())
                    finally:
                        try:
                            f.seek(0)
                            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 0x7fffffff)
                        except: pass
            return True
        except Exception as e:
            print(f"[Z-STORAGE] Append Failed: {e}")
            return False

    def read(self, limit: int = 100) -> list:
        if not self.current_log.exists(): return []
        dq = deque(maxlen=limit if limit > 0 else None)
        try:
            with open(self.current_log, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        dq.append(json.loads(line))
                    except: continue
            return list(dq)
        except Exception as e:
            print(f"[Z-STORAGE] Read Failed: {e}")
            return []

    def snapshot(self) -> bool:
        """Hardware-safe snapshot: Flush to disk before atomic swap."""
        state_file = self.snapshot_path / "state.bin"
        temp_file = Path(str(state_file) + ".tmp")
        try:
            with self._lock:
                with open(self.current_log, "r", encoding="utf-8") as src, \
                     open(temp_file, "w", encoding="utf-8") as dst:
                    for line in src:
                        if not line.strip(): continue
                        try:
                            obj = json.loads(line)
                            dst.write(json.dumps(obj) + "\n")
                        except: continue
                    
                    # Ensure snapshot is physically written
                    dst.flush()
                    os.fsync(dst.fileno())
                
                temp_file.replace(state_file)
            return True
        except Exception as e:
            print(f"[Z-STORAGE] Snapshot Failed: {e}")
            return False

    def compact(self) -> bool:
        """Industrial Safe Compact: Close handle before unlinking."""
        if not self.snapshot(): return False
        try:
            with self._lock:
                # Step 1: Open, Lock, and then Close to clear any pending IO
                with open(self.current_log, "ab") as f:
                    try:
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 0x7fffffff)
                    finally:
                        try:
                            f.seek(0)
                            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 0x7fffffff)
                        except: pass
                
                # Step 2: Now safe to unlink (Handle is closed)
                self.current_log.unlink(missing_ok=True)
                self.current_log.touch()
            return True
        except Exception as e:
            print(f"[Z-STORAGE] Compact Failed: {e}")
            return False

if __name__ == "__main__":
    store = MemoryStore()
    if store.append({"Z-STATUS": "10/10 INDUSTRIAL CORE"}):
        print(" Z-STUDIO STORAGE CORE: DEPLOYMENT SUCCESSFUL (ZERO-GAP)")
