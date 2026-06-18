# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-04-V2
# ROLE: SNAPSHOT MANAGER (V2 SECURE VAULT)
# SIGNATOR: OMEGA-SECURITY-RECOVERY-FINAL
# =================================================================

import os
import json
import hashlib
import time
import lzma  # High compression for large states
import threading

class SnapshotManager:
    def __init__(self, snapshot_dir="storage/snapshots/"):
        self.snapshot_dir = snapshot_dir
        self.schema_version = "2.0.0" # GAP 2 FIX: Version Tracking
        self._lock = threading.Lock()
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def _generate_checksum(self, raw_bytes):
        return hashlib.sha256(raw_bytes).hexdigest()

    def create_snapshot(self, tx_id, data_dict):
        """
        GAP 1 & 4 FIX: Secure JSON-based Serialization + Metadata Index.
        """
        with self._lock:
            ts = int(time.time() * 1000)
            snapshot_id = f"SNAP_{tx_id}_{ts}"
            file_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.zsnap")
            
            try:
                # 1. Package with Metadata
                envelope = {
                    "v": self.schema_version,
                    "tx_id": tx_id,
                    "ts": ts,
                    "payload": data_dict
                }
                
                # GAP 1 FIX: Secure Serialization (No Pickle)
                serialized_data = json.dumps(envelope).encode('utf-8')
                # Optional: Add LZMA compression for GAP 5 (I/O Risk)
                compressed_data = lzma.compress(serialized_data)
                
                data_hash = self._generate_checksum(compressed_data)
                
                # 2. Atomic Write Chain
                temp_path = f"{file_path}.tmp"
                with open(temp_path, 'wb') as f:
                    f.write(compressed_data)
                    f.flush()
                    os.fsync(f.fileno())
                
                os.rename(temp_path, file_path)
                return snapshot_id, data_hash
                
            except Exception as e:
                return None, None

    def restore_snapshot(self, snapshot_id, expected_hash):
        """
        GAP 3 FIX: Full File State Integrity Revalidation.
        """
        file_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.zsnap")
        if not os.path.exists(file_path): return None
            
        try:
            with open(file_path, 'rb') as f:
                raw_compressed = f.read()
                
                # Integrity Re-check
                if self._generate_checksum(raw_compressed) != expected_hash:
                    return None
                
                # Decompress & Secure Load
                serialized_data = lzma.decompress(raw_compressed)
                envelope = json.loads(serialized_data.decode('utf-8'))
                
                # GAP 2 FIX: Version Validation
                if envelope.get("v") != self.schema_version:
                    raise RuntimeError("SNAPSHOT_VERSION_MISMATCH")
                
                return envelope["payload"]
        except Exception:
            return None

    def delete_snapshot(self, snapshot_id):
        file_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.zsnap")
        with self._lock:
            if os.path.exists(file_path):
                os.remove(file_path)

    def get_index(self):
        """GAP 4 FIX: Registry Indexing for Recovery Engine."""
        return [f for f in os.listdir(self.snapshot_dir) if f.endswith('.zsnap')]