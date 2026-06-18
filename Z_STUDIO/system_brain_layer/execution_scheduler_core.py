# =================================================================
# Z-STUDIO V31.2.5 (OMEGA KERNEL FINAL EXECUTION HARDENED - FIXED)
# =================================================================

import time, logging, threading, json, os, heapq, queue
from collections import OrderedDict, deque
import psutil
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional, Callable, Tuple
import queue
import threading
import time


class TaskState:
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    DEAD = "DEAD"


class ExecutionScheduler:

    def __init__(self, bus=None):

        self.bus = bus

        self.queue = queue.Queue() 
        self.active_tasks = []
        
        self.base_path = os.path.join(os.getcwd(), "data_core")
        os.makedirs(self.base_path, exist_ok=True)
        
        #       'data_core'   ,       
        # __file__           
        #project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        #self.base_path = os.path.join(project_root, "data_core")
        
        #      ,   'safe'  :
        #if not os.path.exists(self.base_path):
           # self.base_path = os.path.join(os.getcwd(), "data_core")
            
        #os.makedirs(self.base_path, exist_ok=True)

        self.persistence_file = os.path.join(self.base_path, "state.json")
        self.spill_dir = os.path.join(self.base_path, "spill_queue")
        self.processing_dir = os.path.join(self.base_path, "spill_processing")
        self.dead_file = os.path.join(self.base_path, "dead.jsonl")

        os.makedirs(self.spill_dir, exist_ok=True)
        os.makedirs(self.processing_dir, exist_ok=True)

        # Locks
        self._heap_lock = threading.RLock()
        self._active_lock = threading.RLock()
        self._io_lock = threading.Lock()

        # Execution engine
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Core state
        self._heap = []
        self._active = {}
        self._running = {}
        self._counter = 0
        self._stop = threading.Event()

        # Registry
        self._registry = OrderedDict()
        self._registry_limit = 50000

        # Limits (BACKPRESSURE FIX)
        self._heap_limit = 20000
        self._max_running = 100   #  FIX: execution pressure control
        self._choked = False

        # Event buffers (SPILL optimization FIX)
        self._spill_buffer = deque(maxlen=1000)

        self._persist_q = queue.Queue(maxsize=1)
        self._threads = []

        self._orphan_check = deque(maxlen=10000)

        # START THREADS
        self._start(self._watchdog)
        self._start(self._io_writer)
        self._start(self._pressure)
        self._start(self._spill_worker)
        self._start(self._orphan_reaper)
        self._start(self.execute)

    # execution_scheduler.py mein ye method add kar:

    def enqueue_and_wait(self, raw_task: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        KERNEL BRIDGE: Orchestrator ki emergency request ko handle karta hai.
        """
        # 1. Task ko internal queue mein dalo
        try:
            # Assuming self.queue tera internal queue object hai
            self.queue.put(raw_task, block=True, timeout=2.0)
            return True, {"status": "QUEUED", "trace_id": raw_task.get("trace_id")}
        except Exception as e:
            return False, {"status": "SCHEDULER_FULL", "error": str(e)}



    # scheduler.py   
    def set_orchestrator(self, orchestrator):
        self.orchestrator = orchestrator

    # -------------------------
    def _start(self, fn):
        t = threading.Thread(target=fn, daemon=True)
        t.start()
        self._threads.append(t)

    # -------------------------
    def _pressure(self):
        while not self._stop.is_set():
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            self._choked = cpu > 80 or ram > 85

            self._heap_limit = 5000 if self._choked else 20000
            self._max_running = 30 if self._choked else 100  #  FIX

            time.sleep(2)

    # -------------------------
    def _is_dead(self, task):
        return task and task.get("status") == TaskState.DEAD

    # -------------------------
    def push(self, task, restore=False):

        if self._is_dead(task):
            return False

        tid = task["id"]
        ver = task.get("_version", 0)

        with self._active_lock:

            old = self._registry.get(tid, -1)
            if ver < old:
                return False

            if not restore:
                self._active[tid] = task

            task["_age"] = time.time()

            with self._heap_lock:

                if len(self._heap) >= self._heap_limit and not restore:
                    self._spill_buffer.append(task)   #  FIX: buffered spill
                    return True

                heapq.heappush(
                    self._heap,
                    (-self._score(task), self._counter, task)
                )
                self._counter += 1

            self._registry[tid] = ver

            if len(self._registry) > self._registry_limit:
                self._registry.popitem(last=False)

            return True

    # -------------------------
    def _score(self, task):
        age = time.time() - task.get("_age", time.time())
        return task.get("priority", 100) + (age * 0.01)

    # -------------------------
    # EXECUTION ENGINE (BACKPRESSURE FIX)
    # -------------------------
    def execute(self):

        while not self._stop.is_set():

            with self._heap_lock:
                if not self._heap:
                    time.sleep(0.05)
                    continue

                if len(self._running) >= self._max_running:
                    time.sleep(0.01)
                    continue

                _, _, task = heapq.heappop(self._heap)

            if self._is_dead(task):
                continue

            tid = task["id"]

            task["status"] = TaskState.RUNNING
            self._running[tid] = task

            try:
                time.sleep(0.01)  # simulate work
                task["status"] = TaskState.DONE

            except Exception:
                task["status"] = TaskState.FAILED

            finally:
                self._running.pop(tid, None)
                self._active.pop(tid, None)

    # -------------------------
    # WATCHDOG (ORPHAN FIX)
    # -------------------------
    def _watchdog(self):

        while not self._stop.is_set():

            snapshot = dict(self._active)

            self._enqueue({
                "heap_size": len(self._heap),
                "active": len(snapshot),
                "running": len(self._running),
                "t": time.time()
            })

            for tid, t in snapshot.items():

                #  FIX: only QUEUED can become orphan
                if t.get("status") != TaskState.RUNNING:
                    if time.time() - t.get("_age", time.time()) > 60:
                        self._orphan_check.append(tid)

            time.sleep(1)

    # -------------------------
    def _orphan_reaper(self):

        while not self._stop.is_set():

            while self._orphan_check:
                tid = self._orphan_check.popleft()
                task = self._active.pop(tid, None)

                if task:
                    self.push(task, restore=True)

            time.sleep(2)

    # -------------------------
    # SPILL WORKER (BUFFERED EVENT MODEL FIX)
    # -------------------------
    def _spill_worker(self):

        while not self._stop.is_set():

            while self._spill_buffer:

                task = self._spill_buffer.popleft()

                try:
                    fname = os.path.join(self.spill_dir, f"{task['id']}.json")

                    with open(fname, "w") as f:
                        json.dump(task, f)

                except:
                    pass

            time.sleep(1)

    # -------------------------
    def _enqueue(self, state):
        try:
            if self._persist_q.full():
                self._persist_q.get_nowait()
            self._persist_q.put_nowait(state)
        except:
            pass

    # -------------------------
    def _io_writer(self):

        while not self._stop.is_set():
            try:
                state = self._persist_q.get(timeout=5)

                tmp = self.persistence_file + ".tmp"

                with open(tmp, "w") as f:
                    json.dump(state, f)

                os.replace(tmp, self.persistence_file)

            except queue.Empty:
                continue

    # -------------------------
    def shutdown(self):

        self._stop.set()

        for t in self._threads:
            t.join(timeout=2)

        self.executor.shutdown(wait=True)

        print("V31.2.5 SEALED FULLY FIXED EXECUTION KERNEL")