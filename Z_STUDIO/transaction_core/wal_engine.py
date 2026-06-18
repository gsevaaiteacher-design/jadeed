# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-03-V3
# ROLE: WAL ENGINE (V3 OMEGA ZERO-GAP)
# SIGNATOR: OMEGA-DURABILITY-FINALITY-LOCKED
# =================================================================

import os
import json
import time
import hashlib
import threading

class WALEngine:
    def __init__(self, log_dir="logs/wal/"):
        self.log_dir = log_dir
        self.log_path = os.path.join(self.log_dir, "active.wal")
        self._lock = threading.Lock()
        self._next_seq = 0
        
        os.makedirs(self.log_dir, exist_ok=True)
        self._recover_and_verify()

    def _generate_checksum(self, data_str):
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _recover_and_verify(self):
        """GAP 3 FIX: Strict Sequence Recovery & Corruption Pruning."""
        if os.path.exists(self.log_path):
            logs = self.read_logs() # Uses checksum-based filter
            if logs:
                # Ensure we only pick the highest VALID sequence
                self._next_seq = max([entry.get("seq", 0) for entry in logs]) + 1
            else:
                self._next_seq = 0

    def _write_entry(self, entry):
        """GAP 1 FIX: Torn-Write Detection via Double-Hash Footer."""
        with self._lock:
            entry["seq"] = self._next_seq
            self._next_seq += 1
            
            try:
                raw_data = json.dumps(entry)
                checksum = self._generate_checksum(raw_data)
                
                # FORMAT: [SEQ] | [TS] | [HASH] | [DATA] | [HASH_FOOTER]
                # Footer hash ensures that the line was not truncated during IO
                log_line = f"{entry['seq']} | {time.time()} | {checksum} | {raw_data} | {checksum}\n"
                
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(log_line)
                    f.flush()
                    os.fsync(f.fileno()) 
                return True
            except Exception:
                return False

    def log_start(self, tx_dict):
        """Block Wrapping: BEGIN"""
        return self._write_entry({
            "tx_id": tx_dict['tx_id'],
            "step": "BEGIN_TX",
            "op": tx_dict['operation_name'],
            "snap_id": tx_dict['snapshot_id'],
            "pld": tx_dict['input_data']
        })

    def log_commit(self, tx_id, version):
        """Block Wrapping: COMMIT"""
        return self._write_entry({
            "tx_id": tx_id,
            "step": "END_TX_COMMIT",
            "ver": version
        })

    def log_rollback(self, tx_id):
        """Block Wrapping: ROLLBACK"""
        return self._write_entry({
            "tx_id": tx_id,
            "step": "END_TX_ROLLBACK"
        })

    def read_logs(self):
        """Formal Replay Engine with Torn-Write Validation."""
        logs = []
        if not os.path.exists(self.log_path): return logs

        with open(self.log_path, 'r', encoding='utf-8') as f:
            last_seq = -1
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line: continue
                
                try:
                    parts = line.split(" | ")
                    if len(parts) != 5: continue # GAP 1 FIX: Discard partial/torn writes
                    
                    seq, ts, header_hash, raw_data, footer_hash = \
                        int(parts[0]), parts[1], parts[2], parts[3], parts[4]
                    
                    # VALIDATION 1: Hash Integrity (Header vs Data vs Footer)
                    actual_hash = self._generate_checksum(raw_data)
                    if header_hash != actual_hash or footer_hash != actual_hash:
                        continue # Torn write or corruption detected
                        
                    # VALIDATION 2: Monotonic Sequence Chain
                    if seq <= last_seq: continue
                        
                    last_seq = seq
                    logs.append(json.loads(raw_data))
                except Exception:
                    continue
        return logs

    def checkpoint_and_rotate(self):
        """Atomic Log Rotation (Staged Move)."""
        with self._lock:
            if not os.path.exists(self.log_path): return
            ts = int(time.time())
            archive = os.path.join(self.log_dir, f"wal.{ts}.bak")
            try:
                os.rename(self.log_path, archive)
                with open(self.log_path, 'w') as f:
                    f.write(f"# Z-STUDIO WAL V3 | OMEGA-FINAL | {ts}\n")
                    f.flush()
                    os.fsync(f.fileno())
                return True
            except OSError: return False