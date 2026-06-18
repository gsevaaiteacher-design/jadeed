"""
ROLE: 11/11 - EVENT BUS UI (CENTRAL EVENT ROUTER & THROTTLER)
VERSION: 1.2.1 (STABLE + SAFE SUBSCRIBE FIX + THREAD-SAFE SIGNAL PATCH)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
"""

import time
import threading
from collections import deque
from PySide6.QtCore import QObject, Signal, Slot, QTimer


class ZStudioEventBusUI(QObject):

    # =========================
    # SIGNALS
    # =========================
    ui_event_triggered = Signal(str, dict)
    system_alert = Signal(str)
    event_trace = Signal(str, dict)

    _instance = None
    _lock = threading.Lock()

    # =========================
    # SINGLETON
    # =========================
    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        super().__init__()
        self._initialized = True

        # =========================
        # CORE SAFETY
        # =========================
        self._event_lock = threading.Lock()
        self._last_event_time = {}
        self._throttle_limit = 0.25

        self._queue = deque()
        self._processing = False

        #  FIX: Prevent Qt thread signal drop
        self._dispatcher_timer = QTimer()
        self._dispatcher_timer.timeout.connect(self._process_queue)
        self._dispatcher_timer.start(5)  # continuous safe pump

    # =========================
    # MAIN EMIT CORE
    # =========================
    def emit_ui_event(self, event_name, payload=None):

        payload = payload or {}
        current_time = time.time()

        with self._event_lock:

            last_time = self._last_event_time.get(event_name, 0)

            # THROTTLE PROTECTION
            if (current_time - last_time) < self._throttle_limit:
                self.system_alert.emit(f"EVENT_THROTTLED: {event_name}")
                return

            self._last_event_time[event_name] = current_time
            self._queue.append((event_name, payload))

    # =========================
    # EVENT PROCESSOR (FIXED SAFE LOOP)
    # =========================
    def _process_queue(self):

        if self._processing:
            return

        self._processing = True

        try:
            while True:

                with self._event_lock:
                    if not self._queue:
                        break
                    event_name, payload = self._queue.popleft()

                # TRACE SAFE
                try:
                    self.event_trace.emit(event_name, payload)
                except Exception:
                    pass

                # MAIN DISPATCH SAFE
                try:
                    self.ui_event_triggered.emit(event_name, payload)
                except Exception as e:
                    self.system_alert.emit(f"DISPATCH_ERROR: {str(e)}")

        except Exception as e:
            self.system_alert.emit(f"QUEUE_ERROR: {str(e)}")

        finally:
            self._processing = False

    # =========================
    # EXTERNAL INJECTION
    # =========================
    @Slot(str, dict)
    def inject_event(self, name, data):
        self.emit_ui_event(name, data)

    # =========================
    # DEBUG TOOL
    # =========================
    def get_queue_size(self):
        return len(self._queue)

    # =========================
    #  FIXED SUBSCRIBE SYSTEM (IMPORTANT PATCH)
    # =========================
    def subscribe(self, event_name, callback):

        def handler(name, payload):
            try:
                if name == event_name:
                    callback(payload)
            except Exception as e:
                self.system_alert.emit(f"SUBSCRIBE_ERROR: {str(e)}")

        #  FIX: queued connection safe for UI thread
        self.ui_event_triggered.connect(handler, type=1)

    # =========================
    # BACKEND COMPATIBILITY
    # =========================
    def emit(self, event_name, payload=None):
        self.emit_ui_event(event_name, payload)


# =========================
#  SINGLETON ACCESS
# =========================
def get_event_bus():
    return ZStudioEventBusUI()