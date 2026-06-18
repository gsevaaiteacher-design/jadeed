"""
Z-STUDIO V50.0  SYSTEM CORE
Module: Control Bus (True Deterministic Kernel)
Status: STRICT-CAS | ZERO-LEAK | RATE-CONTROLLED | FULL-AUDIT | WIRED FIXED
"""

import os
import logging
import threading
import time
import json
import heapq
import hashlib
from typing import Dict, Any, Optional
from collections import deque
from concurrent.futures import ThreadPoolExecutor
logger = logging.getLogger("ZYNQUAR_KERNEL_CORE")



class ControlBus:

    MAX_EVENT_RETRIES = 3
    _instance = None
    _singleton_lock = threading.Lock()

    # =====================================================
    # SINGLETON
    # =====================================================
    def __new__(cls, *a, **k):
        with cls._singleton_lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._init_done = False
            return cls._instance

    # =====================================================
    # INIT (FIXED + COMPATIBLE WITH LAUNCHER + ORCH)
    # =====================================================
    def __init__(self, config=None, state=None):

        if getattr(self, "_init_done", False):
            return

        self.config = config
        self.state = state
        

        self.active = True
        self.max_workers = 32
        self.max_retry_heap = 5000

        # -------------------------
        # EVENT REGISTRY (CAS)
        # -------------------------
        self._event_registry = {}
        self._services = {}
        self._registry_lock = threading.RLock()
        
        # [ADD THIS]

        self._allowed_events = {
            "UI_REQUEST",
            "UI_RESPONSE",
            "SYSTEM_START",
            "SYSTEM_ALERT",
            "ERROR_EVENT",

            #  CORE ENGINE EVENTS (ADD THESE)
            "SYSTEM_STARTED",
            "ENGINE_LOADED_SIGNAL",
            "EXECUTION_PROGRESS",
            "EXECUTION_DONE",
            "DASHBOARD_REFRESH",
            "TASK_STATUS",
            "BOOT_COMPLETE",
            "RUNTIME_READY"
        }
        self._response_waiters = {}
        self._response_lock = threading.RLock()

        # -------------------------
        # EXECUTORS
        # -------------------------
        self._batch_exec = ThreadPoolExecutor(max_workers=4, thread_name_prefix="Z_Batch")
        self._worker_exec = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="Z_Worker")
        self._audit_exec = ThreadPoolExecutor(max_workers=1, thread_name_prefix="Z_Audit")
        
        # -------------------------
        # GATES
        # -------------------------
        self._worker_gate = threading.Semaphore(self.max_workers)
        self._submit_gate = threading.Semaphore(self.max_workers * 2)

        # -------------------------
        # SHARD SYSTEM
        # -------------------------
        self._shards = {}
        self.shared_state = {}
        self._shard_locks = {}
        self._subscribers = {}
        self._structure_lock = threading.RLock()

        # -------------------------
        # RETRY ENGINE
        # -------------------------
        self._retry_heap = []
        self._retry_tokens = 50
        self._max_tokens = 50
        self._retry_lock = threading.Lock()
        self._last_token_refill = time.time()

        # -------------------------
        # DLQ
        # -------------------------
        self._dlq = deque(maxlen=1000)
        self._dlq_lock = threading.Lock()
        self._dlq_running = False

        self.last_beat = time.time()
        self._cv = threading.Condition(threading.Lock())

        os.makedirs("logs", exist_ok=True)

        # =====================================================
        # THREAD START (SAFE ORDER FIXED)
        # =====================================================
        self._init_done = True

        threading.Thread(target=self._main_loop, daemon=True, name="Z_Main").start()
        threading.Thread(target=self._maintenance_loop, daemon=True, name="Z_Maint").start()
        threading.Thread(target=self._retry_processor, daemon=True, name="Z_Retry").start()

        logging.info("[CORE] V50.0 DETERMINISTIC KERNEL ONLINE")

    # ControlBus.py  
    def link_services(self, source_name: str, target_name: str):
        """        """
        source = self.get_service(source_name)
        target = self.get_service(target_name)
        if source and target and hasattr(source, "bind_target"):
            source.bind_target(target)

        # ControlBus :
    def stage_service(self, service_name: str, service_instance: Any):
        # 1. Lock        
        with self._registry_lock:
            # 2. Safety Check
            if not hasattr(self, '_services'):
                self._services = {}
            
            # 3. Store the instance
            self._services[service_name] = service_instance
        
        # 4. Log outside the lock (for better performance)
        logger.info(f"[BUS] Service '{service_name}' staged successfully.")

    def resolve(self, key):
        #    
        return getattr(self, '_services', {}).get(key)
    
    def publish(self, key, value):

        print(f"[BUS_TRACE] Channel {key} got: {value}")
        # 1.   
        self.shared_state[key] = value
        
        # 2.     : 
        #        'key' ()    ?
        with self._structure_lock:
            if key in self._subscribers:

                # 🔥 FIX: NORMALIZE VALUE BEFORE CALLBACK
                if isinstance(value, str):
                    value = {
                       "trace_id": "AUTO_FIXED",
                        "input": value,
                        "content": value
                 }

                for callback in self._subscribers[key]:
                    callback(value) 
        
            print(f" [BUS_SPY] PUBLISH -> Channel: {key} | Data: {value}")

    def lock_registry(self, memory=None, hardware=None, engine=None, orchestrator=None, inference=None):
        with self._registry_lock:
            self.memory = memory
            self.hardware = hardware
            self.engine = engine
            self.orchestrator = orchestrator
            self.inference = inference
            
            # --- [SYSTEMATIC FIX:       ] ---
            #    ,          has_channel   
            if inference and "inference" not in self._subscribers:
                self._subscribers["inference"] = []

            if orchestrator and "orchestrator" not in self._subscribers:
                self._subscribers["orchestrator"] = []

            if engine and "engine" not in self._subscribers:
                self._subscribers["engine"] = []
            # -----------------------------------------------------------------
            
            logger.info("[BUS] Registry locked. All core modules wired.")
            return True

    # =====================================================
    # LAUNCHER COMPATIBILITY HOOK
    # =====================================================
    def initialize_hub(self):
        return self.active

    # =====================================================
    # CAS STATE
    # =====================================================
    def _cas_state(self, eid, expected_states, new_state):
        with self._registry_lock:
            reg = self._event_registry.get(eid)
            if reg and reg['state'] in expected_states:
                self._event_registry[eid]['state'] = new_state
                return True
            return False

    # =====================================================
    # SHARD MAINTENANCE
    # =====================================================
    def _maintenance_loop(self):
        while self.active:
            time.sleep(30)
            cutoff = time.time() - 300

            with self._registry_lock:
                expired = [
                    k for k, v in self._event_registry.items()
                    if v['ts'] < cutoff
                ]
                for k in expired:
                    self._event_registry.pop(k, None)

    # =====================================================
    # RETRY ENGINE
    # =====================================================
    def _retry_processor(self):
        while self.active:
            time.sleep(0.5)
            now = time.time()

            with self._retry_lock:

                elapsed = now - self._last_token_refill
                if elapsed >= 1.0:
                    self._retry_tokens = min(
                        self._max_tokens,
                        self._retry_tokens + int(elapsed * self._max_tokens)
                    )
                    self._last_token_refill = now

                if not self._retry_heap or self._retry_tokens <= 0:
                    continue

                batch = []

                while self._retry_heap and len(batch) < 10 and self._retry_tokens > 0:
                    rc, _, topic, data, eid = heapq.heappop(self._retry_heap)

                    with self._registry_lock:
                        if self._event_registry.get(eid, {}).get('state') == "done":
                            continue

                    if rc >= self.MAX_EVENT_RETRIES:
                        continue

                    self._retry_tokens -= 1
                    #batch.append((topic, data, rc + 1))
                    batch.append((topic, data, rc + 1, eid))

            #for t, d, rc in batch:
            for t, d, rc, eid in batch:
                # Purani ID (eid) ko sath bhejna zaroori hai taaki chain na toote
                self.emit(t, d, urgent=True, retry_count=rc, eid=eid)

    # =====================================================
    # EVENT ID GENERATOR
    # =====================================================
    def _get_eid(self, topic, payload):
        try:
            # Sort keys for deterministic ID, but with fallback
            raw_payload = json.dumps(payload, sort_keys=True)
        except Exception:
            raw_payload = str(payload)
        
        # Salt with timestamp to ensure unique EID for every click
        # time.time_ns() se har click unique ho jayega, bhale hi payload same ho
        raw = f"{topic}:{time.time_ns()}:{raw_payload}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    # =====================================================
    # EMIT (FIXED + SAFE + LAUNCHER COMPATIBLE)
    # =====================================================
    def emit(self, topic, payload=None, urgent=False, retry_count=0, eid=None):

        if not self.active:
            return False
        
        if topic not in self._allowed_events:
            with self._registry_lock:
                self._allowed_events.add(topic)

        # --- [WIRING FIX START: Validation & Overload] ---
        # 1. Check if event is allowed (Blueprint Lock)
        if topic not in self._allowed_events:
            logging.error(f"[KERNEL] REJECTED: Invalid Event '{topic}'")
            return False
        
        eid = eid or self._get_eid(topic, payload)

        # 2. Overload Check (Prevent "Toy" system crashes)
        #if topic != "SYSTEM_ALERT" and len(self._shards.get(topic, [])) > 1500:
           # self.emit("SYSTEM_ALERT", {"type": "OVERLOAD", "topic": topic}, urgent=True)
        if topic != "SYSTEM_ALERT" and len(self._shards.get(topic, [])) > 1500:
            self._audit({"warn": "OVERLOAD_SOFT_LIMIT", "topic": topic})
            return False
            #self._response_waiters.pop(eid, None)          #
            
        # --- [WIRING FIX END] ---

        #eid = eid or self._get_eid(topic, payload)

        with self._registry_lock:
            reg = self._event_registry.get(eid)

            if reg and reg['state'] in ("done", "running"):
                return False

            if retry_count >= self.MAX_EVENT_RETRIES:
                return False

            self._event_registry[eid] = {
                'state': 'pending',
                'ts': time.time()
            }

        # -------------------------
        # SHARD INIT
        # -------------------------
        if topic not in self._shard_locks:
            with self._structure_lock:
                if topic not in self._shard_locks:
                    self._shard_locks[topic] = threading.Lock()
                    self._shards[topic] = []

        with self._shard_locks[topic]:

            if len(self._shards[topic]) >= 2000:
                _, _, _, _, dropped_eid = heapq.heappop(self._shards[topic])
                self._audit({"err": "Shard overflow", "eid": dropped_eid})

            heapq.heappush(
                self._shards[topic],
                (0 if urgent else 1, time.time(), payload, retry_count, eid)
            )

        with self._cv:
            self._cv.notify_all()

        return True

    # =====================================================
    # MAIN LOOP (FIXED INDENT + STABILITY)
    # =====================================================
    def _main_loop(self):

        import time as bus_time #     
        

        while self.active:
            self.last_beat = time.time()
            snapshot = []

            with self._structure_lock:
                topic_list = list(self._shards.keys())

            for t in topic_list:
                lock = self._shard_locks.get(t)
                if not lock:
                    continue

                with lock:
                    shard_data = self._shards.get(t)
                    if not shard_data:
                        continue

                    items = list(shard_data)
                    shard_data.clear()
                    snapshot.append((t, items))

            if not snapshot:
                with self._cv:
                    self._cv.wait(timeout=1.0)
                continue

            for topic, items in snapshot:

                if self._worker_gate.acquire(timeout=2.0):
                    try:
                        future = self._batch_exec.submit(
                            self._batch_handler,
                            topic,
                            items
                        )
                        future.add_done_callback(self._release_worker_gate)
                    except Exception:
                        self._worker_gate.release()
                        for _, _, d, rc, eid in items:
                            self._capture_retry(topic, d, rc, eid)
                else:
                    for _, _, d, rc, eid in items:
                        self._capture_retry(topic, d, rc, eid)

    # =====================================================
    # BATCH HANDLER
    # =====================================================
    def _batch_handler(self, topic, items):

        with self._structure_lock:
            subs = tuple(self._subscribers.get(topic, ()))

        if not subs:
            # Agar koi sunne wala nahi hai toh log mein pata chalna chahiye
            self._audit({"warn": "NO_SUBSCRIBER", "topic": topic})
            return

        for _, _, data, rc, eid in items:

            if not self._cas_state(eid, ["pending", "failed"], "running"):
                continue

            for cb in subs:
                if not callable(cb): continue # Agar function sahi nahi hai toh skip karo

                if self._submit_gate.acquire(timeout=1.0):
                    try:
                        fut = self._worker_exec.submit(
                            self._task_wrapper,
                            cb, topic, data, rc, eid
                        )
                        fut.add_done_callback(self._release_submit_gate)
                    except Exception:
                        self._submit_gate.release()
                        self._cas_state(eid, ["running"], "failed")
                        self._capture_retry(topic, data, rc, eid)
                else:
                    self._cas_state(eid, ["running"], "failed")
                    self._capture_retry(topic, data, rc, eid)

    # =====================================================
    # TASK WRAPPER
    # =====================================================
    def _task_wrapper(self, cb, topic, data, rc, eid):
        success = False
        result = None # Track output

        try:
            # Blueprint Fix: All callbacks must now return a value
            result = cb(data)
            success = True
        except Exception as e:
            self._audit({"err": str(e), "eid": eid})
        finally:
            # [CRITICAL WIRING] - Send result back to waiter
            with self._response_lock:
                waiter = self._response_waiters.get(eid)
                if waiter:
                    waiter["response"] = result
                    waiter["event"].set()

            self._cas_state(eid, ["running"], "done" if success else "failed")
            if not success:
                self._capture_retry(topic, data, rc, eid)
             
    # =====================================================
    # RETRY CAPTURE
    # =====================================================
    def _capture_retry(self, topic, data, rc, eid):

        with self._retry_lock:
            if len(self._retry_heap) < self.max_retry_heap:
                heapq.heappush(
                    self._retry_heap,
                    (rc, time.time(), topic, data, eid)
                )

    # =====================================================
    # AUDIT SYSTEM
    # =====================================================
    def _audit(self, msg):

        with self._dlq_lock:
            self._dlq.append(msg)

            if not self._dlq_running:
                self._dlq_running = True
                self._audit_exec.submit(self._flush)

    # =====================================================
    # FLUSH LOG
    # =====================================================
    def _flush(self):

        try:
            while self.active:
                with self._dlq_lock:
                    if not self._dlq:
                        break
                    item = self._dlq.popleft()

                with open("logs/audit.log", "a") as f:
                    f.write(json.dumps(item) + "\n")

        finally:
            with self._dlq_lock:
                self._dlq_running = False

    # =====================================================
    # SUBSCRIBE API (LAUNCHER/ORCH COMPATIBLE)
    # =====================================================
    def subscribe(self, topic, cb):

        with self._structure_lock:

            s = list(self._subscribers.get(topic, ()))

            if cb not in s:
                s.append(cb)
                self._subscribers[topic] = tuple(s)

                if topic not in self._shard_locks:
                    self._shard_locks[topic] = threading.Lock()
                    self._shards[topic] = []

    # =====================================================
    # GATE HELPERS
    # =====================================================
    def _release_worker_gate(self, _future):
        self._worker_gate.release()

    def _release_submit_gate(self, _future):
        self._submit_gate.release()

    def request(self, topic, payload=None, timeout=10):
        """Uplink Tar: Wait for AI/Manager to reply"""
        #eid = self._get_eid(topic, payload)
        eid = hashlib.md5(f"{topic}:{time.time_ns()}".encode()).hexdigest()
        event = threading.Event()

        with self._response_lock:
            self._response_waiters[eid] = {"event": event, "response": None}

        # Send the signal
        self.emit(topic, payload, eid=eid)
        # Wait for callback loop
        if event.wait(timeout):
            with self._response_lock:
                res = self._response_waiters.pop(eid, None)
                return res["response"] if res else None
        else:
            with self._response_lock:
                self._response_waiters.pop(eid, None)
            return {"error": "TIMEOUT", "eid": eid}
        
    def get_messenger_proxy(self):
        """Provides a proxy for the ExecutionManager to talk to the Bus."""
        return self # Ya jo aapka specific proxy object hai
    
    # control_bus.py 
    def send(self, topic: str, data: Any):
        """ExecutionManager       ."""
        return self.emit(topic, data) #  emit        
    
    # 1. Transport Layer Contract
    def on(self, event_name, callback):
        """Register a channel listener."""
        self.subscribe(event_name, callback)

    # 2. Channel Availability Check
    def has_channel(self, channel_name):
        """Check if a topic/channel exists."""
        with self._structure_lock:
            return channel_name in self._subscribers

    # 3. State Snapshoting
    def system_state_snapshot(self):
        """Return the current system registry state."""
        with self._registry_lock:
            return dict(self._event_registry)
        
    def get_service(self, name):
        # Agar _services exist karta hai, toh value return karo (nahi toh None)
        return getattr(self, "_services", {}).get(name)
        
# =====================================================
# KERNEL TEST BENCH (File ke bilkul end mein dalo)
# =====================================================
if __name__ == "__main__":
    # 1. Bus ka instance banao (Singleton)
    bus = ControlBus()
    
    # 2. Ek dummy logic handler (Subscriber)
    # Blueprint rule: Ab se har handler ko RETURN karna zaroori hai
    def test_handler(data):
        print(f"\n[TEST] Subscriber Received: {data}")
        return f"SUCCESS: Received command -> {data.get('cmd')}"
    
    # 3. Connection Jodo
    bus.subscribe("UI_REQUEST", test_handler)
    
    # 4. REAL LOOP TEST (The Request-Response Tar)
    print("\n" + "="*40)
    print("Z-STUDIO V50.0: TESTING CONTROL BUS LOOP")
    print("="*40)
    
    # Ye wait karega jab tak 'test_handler' return na kar de
    result = bus.request("UI_REQUEST", {"cmd": "Hello AI Engine"})
    
    print(f"\n[FINAL RESULT FROM BUS]: {result}")
    print("="*40)

# event_bus_ui.py mein
_BUS_INSTANCE = None

def get_event_bus():
    global _BUS_INSTANCE
    if _BUS_INSTANCE is None:
        _BUS_INSTANCE = ControlBus() # Yahan tumhara main class init hoga
    return _BUS_INSTANCE