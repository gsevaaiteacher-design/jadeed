"""
Z-STUDIO V12.3  RUNTIME API (INTERNAL EXECUTION LAYER)
Author/Brand: ZYNQUAR ATELIER
Module: stream_engine.py (V15 HARDENED)
Role: Real-time Token Streaming with Safe Cleanup & Multi-Thread Isolation.
-----------------------------------------------------------------------
"""

import time
import queue
import threading
from typing import Dict, Any, Optional, Generator

try:
    from logger_core import logger
except ImportError:
    import logging
    logger = logging.getLogger("ZYNQUAR_STREAMER")

class ZStudioStreamEngine:
    """
     ROLE: The Real-time Pipeline.
     LOGIC: Queue-based buffering with explicit race-condition protection.
    """

    def __init__(self):
        # Dictionary to hold thread-safe queues
        self.active_streams: Dict[str, queue.Queue] = {}
        # Lock for dictionary operations to prevent race conditions during cleanup
        self._lock = threading.Lock()
        logger.info("[ZYNQUAR STREAM] ENGINE V15 ACTIVE. MULTI-THREAD SAFETY ENABLED.")

    def create_stream(self, request_id: str):
        """Standard channel initialization."""
        with self._lock:
            self.active_streams[request_id] = queue.Queue()
        logger.info(f"[ZYNQUAR STREAM] CHANNEL OPENED: {request_id}")

    def push_token(self, request_id: str, token: Optional[str]):
        """
         AI Engine pushes tokens here. 
        Note: Sending None signals the end of the stream.
        """
        with self._lock:
            if request_id in self.active_streams:
                self.active_streams[request_id].put(token)
            else:
                # Logging orphan tokens for debugging leakages
                if token is not None:
                    logger.warning(f"[ZYNQUAR STREAM] ORPHAN TOKEN DISCARDED: {request_id}")

    def get_stream_iterator(self, request_id: str) -> Generator[str, None, None]:
        """
         UI consumes tokens from here using a generator.
        """
        stream_queue = None
        with self._lock:
            stream_queue = self.active_streams.get(request_id)

        if not stream_queue:
            logger.error(f"[ZYNQUAR STREAM] STREAM NOT FOUND: {request_id}")
            return

        try:
            while True:
                # Timeout prevents the thread from hanging forever if AI crashes
                token = stream_queue.get(timeout=15.0)
                
                if token is None: # Explicit Stop Signal
                    break
                
                yield token
        except queue.Empty:

            try:
                from system_core.control_bus import control_bus
                control_bus.publish("STREAM_ERROR", {"request_id": request_id, "status": "TIMEOUT"})
            except:
                pass
           
            logger.error(f"[ZYNQUAR STREAM] TIMEOUT EXCEEDED: {request_id}")
        finally:
            # FIX: Ensure cleanup happens only once and safely
            self.close_stream(request_id)

    def close_stream(self, request_id: str):
        """Safe Cleanup: Checks existence before deletion to avoid race conditions."""
        with self._lock:
            if request_id in self.active_streams:
                # Put a None signal just in case the iterator is still waiting
                try:
                    self.active_streams[request_id].put_nowait(None)
                except queue.Full:
                    pass
                
                del self.active_streams[request_id]
                logger.info(f"[ZYNQUAR STREAM] CHANNEL DESTROYED: {request_id}")

# GLOBAL SINGLETON
stream_engine = ZStudioStreamEngine()
StreamEngine = ZStudioStreamEngine

#  ZYNQUAR ATELIER  [PHASE 3 - FILE 3: 10/10 ABSOLUTE - LOCKED]