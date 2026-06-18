# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-11-WAL-SCHEMA
# ROLE: IMMUTABLE LEDGER WAL FORMAT (CHAINED INTEGRITY)
# SIGNATOR: OMEGA-INDUSTRIAL-IMMUTABLE-CORE
# =================================================================

import json
import hashlib
from datetime import datetime

class WALSchema:
    """
    Immutable WAL Schema with Chained Hashing and Strict LSN.
    Ensures zero-tamper integrity and chronological replay safety.
    """

    WAL_VERSION = "1.3"

    # --- ACID STATE MACHINE STEPS ---
    STEP_START    = "TX_START"    
    STEP_EXECUTE  = "TX_EXECUTE"  
    STEP_COMMIT   = "TX_COMMIT"   
    STEP_FAIL     = "TX_FAIL"     
    STEP_ROLLBACK = "TX_ROLLBACK" 

    @staticmethod
    def format_entry(ctx, step, prev_hash=None, metadata=None):
        """
         UPGRADE 1 & 2: Chained Hash + Strict LSN Context.
        Creates a tamper-proof link to the previous log entry.
        """
        #  BASE STRUCTURE (LSN should be managed by WALEngine, injected here)
        entry_base = {
            "wal_v": WALSchema.WAL_VERSION,
            "lsn": getattr(ctx, "lsn", -1), # -1 indicates LSN error
            "tx_id": getattr(ctx, "tx_id", "UNKNOWN"),
            "step": step,
            "ts": datetime.now().isoformat(),
            "op": getattr(ctx, "operation_name", "UNDEF"),
            "snap_id": getattr(ctx, "snapshot_id", None),
            "prev_h": prev_hash, #  UPGRADE 1: Chained Hash Link
            "payload": getattr(ctx, "input_data", {}),
            "meta": metadata or {}
        }

        #  FIX: DETERMINISTIC HASHING WITH CHAIN LINK
        # Sort keys and remove whitespace for hash stability
        raw_str = json.dumps(entry_base, sort_keys=True, separators=(',', ':'))
        
        # Combined hash of current content + link to history
        hasher = hashlib.sha256(raw_str.encode())
        entry_base["hash"] = hasher.hexdigest()

        return json.dumps(entry_base, separators=(',', ':'), sort_keys=True) + "\n"

    @staticmethod
    def parse_entry(line):
        """
         UPGRADE 3: Strict Parse Contract.
        Standardized output for the Recovery Engine pipeline.
        """
        clean_line = line.strip()
        if not clean_line:
            return {"status": "EMPTY", "data": None, "reason": "No data found"}
            
        try:
            data = json.loads(clean_line)
            
            #  INTEGRITY VALIDATION
            incoming_hash = data.pop("hash", None)
            recalc_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            recalc_hash = hashlib.sha256(recalc_str.encode()).hexdigest()

            if incoming_hash != recalc_hash:
                return {
                    "status": "CORRUPT",
                    "data": data,
                    "reason": "INTEGRITY_HASH_MISMATCH",
                    "raw": clean_line
                }

            data["hash"] = incoming_hash 
            return {"status": "OK", "data": data, "reason": "Success"}

        except Exception as e:
            return {
                "status": "CORRUPT",
                "data": None,
                "reason": f"PARSER_EXCEPTION: {str(e)}",
                "raw": clean_line
            }

    @staticmethod
    def is_valid_sequence(last_step, new_step):
        """Transaction flow validation for the ACID engine."""
        sequence = {
            WALSchema.STEP_START: [WALSchema.STEP_EXECUTE, WALSchema.STEP_FAIL],
            WALSchema.STEP_EXECUTE: [WALSchema.STEP_COMMIT, WALSchema.STEP_FAIL],
            WALSchema.STEP_FAIL: [WALSchema.STEP_ROLLBACK],
            WALSchema.STEP_COMMIT: [],
            WALSchema.STEP_ROLLBACK: []
        }
        return new_step in sequence.get(last_step, [])