"""
Z-STUDIO V12.3  SYSTEM CORE (PORTLESS ROUTER - ETERNAL)
Author/Brand: ZYNQUAR ATELIER
Role: Industrial Nerve System with Priority Overflow Recovery. Zero-Gap Logic.
"""

import threading
import queue
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, Dict

# Standard ZYNQUAR Industrial Logger
try:
    from system_core.logger_core import logger
except ImportError:
    logger = logging.getLogger("ZYNQUAR_ROUTER")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s | ZYNQUAR | %(levelname)s | %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

class PortlessRouter:
    _instance = None
    _lock = threading.RLock() 

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        with self._lock:
            if hasattr(self, '_initialized'): return
            
            self._subscribers: Dict[str, list] = {}
            self._MAX_QUEUE = 5000
            self._event_queue = queue.Queue(maxsize=self._MAX_QUEUE)
            
            # FIX (0.1 Gap): Emergency Overflow Buffer for Critical Recovery
            self._priority_buffer = queue.Queue(maxsize=100) 
            
            self._active = True
            
            # Bounded Worker Pool (Industrial Scale)
            self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="Z_Worker")
            
            # Master Dispatcher Thread
            self._dispatch_thread = threading.Thread(target=self._event_loop, name="Z_Router_Core", daemon=True)
            self._dispatch_thread.start()
            
            self._initialized = True
            logger.info("[ZYNQUAR_ROUTER] ETERNAL KERNEL ONLINE | PRIORITY RECOVERY ACTIVE.")

    def subscribe(self, event_type: str, callback: Callable):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, data: Any = None, priority: bool = False):
        """Broadcasts signals with Pressure Telemetry and Overflow Recovery."""
        payload = {"type": event_type, "data": data, "ts": time.time(), "prio": priority}
        
        # Telemetry Monitoring
        current_load = self._event_queue.qsize()
        if current_load > (self._MAX_QUEUE * 0.85):
            logger.warning(f"[ZYNQUAR_ROUTER] CRITICAL PRESSURE: {current_load}/{self._MAX_QUEUE}")

        try:
            # Standard Async Dispatch
            self._event_queue.put(payload, timeout=0.1)
        except queue.Full:
            # FIX (Recovery Strategy): Emergency Priority Drop
            if priority or "SHUTDOWN" in event_type or "CRITICAL" in event_type:
                try:
                    self._priority_buffer.put_nowait(payload)
                    logger.info(f"[ZYNQUAR_ROUTER] OVERFLOW RECOVERY: Critical event {event_type} buffered.")
                except queue.Full:
                    logger.critical(f"[ZYNQUAR_ROUTER] TOTAL SYSTEM SATURATION: {event_type} LOST.")
            else:
                logger.error(f"[ZYNQUAR_ROUTER] LOW_PRIO_DROP: {event_type} discarded under pressure.")

    def _event_loop(self):
        """Kernel loop: Processes Priority Buffer first, then Main Queue."""
        while self._active or not self._event_queue.empty() or not self._priority_buffer.empty():
            try:
                # 1. Process Priority Signals First (Recovery Logic)
                try:
                    p_event = self._priority_buffer.get_nowait()
                    self._dispatch(p_event)
                    self._priority_buffer.task_done()
                    continue # Clear priority buffer immediately
                except queue.Empty:
                    pass

                # 2. Process Standard Signals
                timeout = 0.5 if self._active else 0.05
                event = self._event_queue.get(timeout=timeout)
                self._dispatch(event)
                self._event_queue.task_done()
            except queue.Empty:
                if not self._active: break
                continue

    def _dispatch(self, event: dict):
        event_type = event["type"]
        data = event["data"]
        with self._lock:
            callbacks = self._subscribers.get(event_type, []).copy()
        
        for callback in callbacks:
            self._executor.submit(self._safe_execute, callback, data, event_type)

    def _safe_execute(self, callback, data, event_type):
        try:
            callback(data)
        except Exception as e:
            logger.error(f"[ZYNQUAR_ROUTER] CALLBACK_CRASH | {event_type} | {str(e)}")

    def shutdown(self):
        logger.info("[ZYNQUAR_ROUTER] SHUTDOWN: SECURING NERVE SYSTEM...")
        self._active = False
        if self._dispatch_thread.is_alive():
            self._dispatch_thread.join(timeout=5.0)
        self._executor.shutdown(wait=True)
        logger.info("[ZYNQUAR_ROUTER] KERNEL SEALED.")

# GLOBAL ACCESS
router = PortlessRouter()
