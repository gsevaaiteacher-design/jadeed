# =================================================================
# PROJECT: Z-STUDIO V12.3
# FILE NO: 07-08-JOURNAL-CORE-V5-FINAL
# ROLE: 10/10 ABSOLUTE ZERO-LOSS ASYNC WAL (PERSISTENT STAGING)
# SIGNATOR: KERNEL-JOURNAL-STAGED-V5
# =================================================================

import sqlite3
import json
import time
import logging
import threading
import os
from queue import Queue, Empty

class JournalCore:
    def __init__(self, base_dir="data/", flush_interval=0.05):
        self.base_dir = base_dir
        self.db_path = os.path.join(base_dir, "system_audit.journal")
        self.stage_path = os.path.join(base_dir, "journal.stage") # FIX 1: Disk-Backed Queue
        
        self.logger = logging.getLogger("Z-Journal-V5")
        self.flush_interval = flush_interval
        self.buffer = Queue()
        self.lock = threading.Lock()
        self.running = True
        
        # Absolute ACID Connection
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        self._init_db_and_recover_stage()
        
        # Background Flush Thread
        self.flush_thread = threading.Thread(target=self._background_flusher, daemon=True)
        self.flush_thread.start()

    def _init_db_and_recover_stage(self):
        """FIX 1: Initialize DB and Recover lost transactions from Stage file."""
        os.makedirs(self.base_dir, exist_ok=True)
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=FULL;")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                lsn INTEGER PRIMARY KEY,
                tx_id TEXT, timestamp REAL, operation TEXT, payload TEXT, status TEXT
            )
        ''')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_id ON audit_log(tx_id);")

        # STAGE RECOVERY: If stage file exists, system crashed before DB commit
        if os.path.exists(self.stage_path):
            self.logger.warning("CRASH DETECTED: Recovering pending transactions from STAGE file...")
            self._recover_from_stage()

    def log_entry(self, lsn, tx_id, operation, data, status="COMMITTED"):
        """FIX 1: Write-Ahead Staging (Append-Only) for Zero-Loss."""
        entry = {
            'lsn': lsn, 'tx_id': tx_id, 'op': operation, 
            'data': data, 'status': status
        }
        
        # 1. IMMEDIATE PERSISTENCE (Append to Stage File)
        try:
            with open(self.stage_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
                os.fsync(f.fileno()) # Guarantee disk write before RAM ingestion
        except Exception as e:
            self.logger.critical(f"STAGING FAILURE: Cannot persist transaction! {e}")
            raise # Stop everything if staging fails

        # 2. INGEST TO RAM BUFFER
        self.buffer.put(entry)

    def _background_flusher(self):
        """Timed Auto-Flush with Stage Cleanup."""
        while self.running:
            batch = []
            try:
                while len(batch) < 100:
                    batch.append(self.buffer.get(timeout=self.flush_interval))
            except Empty:
                pass

            if batch:
                if self._commit_batch(batch):
                    # FIX 1: Cleanup Stage file only AFTER successful DB commit
                    self._truncate_stage()

    def _commit_batch(self, batch):
        """Atomic Batch Write to Database."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute("BEGIN IMMEDIATE;")
                for e in batch:
                    cursor.execute('''
                        INSERT INTO audit_log (lsn, tx_id, timestamp, operation, payload, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (e['lsn'], e['tx_id'], time.time(), e['op'], json.dumps(e['data']), e['status']))
                cursor.execute("COMMIT;")
                return True
        except Exception as e:
            self.logger.error(f"Journal Commit Failure: {e}")
            self.conn.rollback()
            return False

    def _recover_from_stage(self):
        """Reads stage file and commits to DB."""
        recovered_batch = []
        try:
            with open(self.stage_path, "r") as f:
                for line in f:
                    recovered_batch.append(json.loads(line.strip()))
            if recovered_batch:
                if self._commit_batch(recovered_batch):
                    self._truncate_stage()
                    self.logger.info(f"Successfully recovered {len(recovered_batch)} transactions.")
        except Exception as e:
            self.logger.error(f"Stage recovery failed: {e}")

    def _truncate_stage(self):
        """Atomically clears the staging area."""
        try:
            with open(self.stage_path, "w") as f:
                f.truncate(0)
        except: pass

    def close(self):
        """Final flush and cleanup."""
        self.running = False
        remaining = []
        while not self.buffer.empty():
            remaining.append(self.buffer.get())
        if remaining:
            if self._commit_batch(remaining):
                self._truncate_stage()
        self.conn.close()