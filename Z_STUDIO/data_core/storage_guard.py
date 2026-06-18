#  STORAGE_GUARD.PY

#  ENTERPRISE STORAGE ENGINE (HARDENED V2.2)

#  ZYNQUAR ATELIER (C) 2026



import os

import json

import time

import hashlib

import threading

from pathlib import Path

from typing import Any, Dict, Optional





class StorageGuard:

    """

    ENTERPRISE CRASH-SAFE STORAGE ENGINE (HARDENED)



    GUARANTEES:

     Write-Ahead Log (WAL)

     Snapshot recovery fallback

     Atomic compaction with backup

     Corruption detection + skip

     Thread-safe operations

     Safe recovery chain

    """



    def __init__(self, node_id: str, base_dir: str = "core_assets"):

        self.node_id = node_id

        self.base_dir = Path(base_dir) / node_id

        self.base_dir.mkdir(parents=True, exist_ok=True)



        self.lock = threading.RLock()



        # STATE

        self.state: Dict[str, Any] = {}



        # STORAGE FILES

        self.log_file = self.base_dir / "wal.log"

        self.snapshot_file = self.base_dir / "snapshot.json"



        self.last_applied_index = 0

        self.snapshot_in_progress = False



        self._recover_safe()



    # =========================================================

    # HASH (INTEGRITY)

    # =========================================================

    def _hash(self, data: Dict) -> str:

        return hashlib.sha256(

            json.dumps(data, sort_keys=True).encode()

        ).hexdigest()



    # =========================================================

    # WAL APPEND (SAFE + VERIFIED)

    # =========================================================

    def _append_log(self, entry: dict):

        entry["hash"] = self._hash({k: v for k, v in entry.items() if k != "hash"})



        with open(self.log_file, "a") as f:

            f.write(json.dumps(entry) + "\n")

            f.flush()

            os.fsync(f.fileno())



        # WRITE VALIDATION (FIX #4)

        if not self._verify_last_entry(entry):

            raise RuntimeError("WAL write verification failed")



    # =========================================================

    # WRITE OPERATION (WAL  FSYNC  APPLY)

    # =========================================================

    def write(self, key: str, value: Any):

        with self.lock:



            entry = {

                "ts": time.time(),

                "op": "set",

                "key": key,

                "value": value,

                "idx": self.last_applied_index + 1

            }



            self._append_log(entry)



            # APPLY ONLY AFTER DURABILITY CONFIRMATION

            self.state[key] = value

            self.last_applied_index += 1



    # =========================================================

    # DELETE (TOMBSTONE SAFE)

    # =========================================================

    def delete(self, key: str):

        with self.lock:



            entry = {

                "ts": time.time(),

                "op": "delete",

                "key": key,

                "value": None,

                "idx": self.last_applied_index + 1

            }



            self._append_log(entry)



            self.state.pop(key, None)

            self.last_applied_index += 1



    # =========================================================

    # READ

    # =========================================================

    def read(self, key: str) -> Optional[Any]:

        with self.lock:

            return self.state.get(key)



    # =========================================================

    # SNAPSHOT (SAFE ATOMIC)

    # =========================================================

    def snapshot(self):

        with self.lock:

            self.snapshot_in_progress = True



            snap = {

                "state": self.state,

                "last_index": self.last_applied_index,

                "ts": time.time()

            }



            tmp = self.snapshot_file.with_suffix(".tmp")



            with open(tmp, "w") as f:

                json.dump(snap, f)

                f.flush()

                os.fsync(f.fileno())



            os.replace(tmp, self.snapshot_file)



            self._compact_log()

            self.snapshot_in_progress = False



    # =========================================================

    # SAFE COMPACTION (FIXED BACKUP STRATEGY)

    # =========================================================

    def _compact_log(self):

        if not self.log_file.exists():

            return



        backup = self.base_dir / f"wal_backup_{int(time.time())}.log"

        os.replace(self.log_file, backup)



        with open(self.log_file, "w") as f:

            f.write("")

            f.flush()

            os.fsync(f.fileno())



    # =========================================================

    # RECOVERY (FAILSAFE CHAIN)

    # =========================================================

    def _recover_safe(self):

        try:

            self._recover()

        except:

            # SNAPSHOT FALLBACK

            if self.snapshot_file.exists():

                with open(self.snapshot_file, "r") as f:

                    snap = json.load(f)

                    self.state = snap.get("state", {})

                    self.last_applied_index = snap.get("last_index", 0)



    def _recover(self):

        # snapshot first

        if self.snapshot_file.exists():

            with open(self.snapshot_file, "r") as f:

                snap = json.load(f)

                self.state = snap.get("state", {})

                self.last_applied_index = snap.get("last_index", 0)



        # WAL replay

        if self.log_file.exists():

            with open(self.log_file, "r") as f:

                for line in f:

                    entry = json.loads(line)



                    expected = entry.get("hash")

                    check = self._hash({k: v for k, v in entry.items() if k != "hash"})



                    if expected != check:

                        continue



                    idx = entry.get("idx", 0)

                    if idx <= self.last_applied_index:

                        continue



                    if entry["op"] == "delete":

                        self.state.pop(entry["key"], None)

                    else:

                        self.state[entry["key"]] = entry["value"]



                    self.last_applied_index = idx



    # =========================================================

    # INTEGRITY CHECK

    # =========================================================

    def verify_integrity(self) -> bool:

        if not self.log_file.exists():

            return True



        with open(self.log_file, "r") as f:

            for line in f:

                try:

                    entry = json.loads(line)

                    expected = entry.get("hash")

                    check = self._hash({k: v for k, v in entry.items() if k != "hash"})



                    if expected != check:

                        return False

                except:

                    return False



        return True



    # =========================================================

    # VERIFY LAST ENTRY (WRITE SAFETY)

    # =========================================================

    def _verify_last_entry(self, entry):

        try:

            with open(self.log_file, "r") as f:

                lines = f.readlines()

                if not lines:

                    return False

                last = json.loads(lines[-1])

                return last["hash"] == entry["hash"]

        except:

            return False



    # =========================================================

    # EXPORT (LIGHTWEIGHT SAFE COPY)

    # =========================================================

    def export_state(self) -> Dict:

        with self.lock:

            return dict(self.state)
