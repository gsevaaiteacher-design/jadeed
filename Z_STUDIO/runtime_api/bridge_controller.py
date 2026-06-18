"""
Z-STUDIO V12.3  TITAN-OS KERNEL (ENTERPRISE-READY FIXED SAFE PATCH v2)
Author: ZYNQUAR ATELIER
Status: ENUM-TAXONOMY | TYPE-SAFE-FAULT | DETERMINISTIC-MONITOR | DEADLOCK-PROOF
"""

import time, uuid, random, multiprocessing, queue, logging, traceback, sys, os, importlib
from enum import Enum
from typing import Dict, Any

# Import this to push data to the streamer
from runtime_api.stream_engine import stream_engine

#  ERROR TAXONOMY
class TitanError(Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    PROCESS_CRASH = "PROCESS_CRASH"
    CONTRACT_VOID = "CONTRACT_VOID"
    IMPORT_FAIL = "IMPORT_FAIL"
    VALIDATION_FAIL = "VALIDATION_FAIL"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    OVERLOAD = "OVERLOAD"
    KERNEL_ERROR = "KERNEL_ERROR"


#  LOGGING
class TitanLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs.setdefault('extra', self.extra)
        if 'req_id' not in kwargs['extra']:
            kwargs['extra']['req_id'] = 'SYSTEM'
        return msg, kwargs


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [ID:%(req_id)s] %(message)s'
)

raw_logger = logging.getLogger("Z_TITAN")
logger = TitanLoggerAdapter(raw_logger, {'req_id': 'BOOT'})


#  GLOBAL IMPORT CACHE (FIX #3)
_CORE_CACHE = None


def _get_core():
    global _CORE_CACHE
    if _CORE_CACHE is None:
        try:
            mod = importlib.import_module("runtime_api.api_core")
            _CORE_CACHE = getattr(mod, "api_core", None)
        except Exception:
            return None
    return _CORE_CACHE


def _isolated_kernel_executor(action: str, payload: dict, result_queue: multiprocessing.Queue):
    try:
        core = _get_core()

        if not core or not hasattr(core, "execute_pipeline"):
            result_queue.put({
                "status": TitanError.CONTRACT_VOID.value,
                "data": None,
                "error_code": TitanError.CONTRACT_VOID.value
            })
            return

        response = core.execute_pipeline(
            action=action,
            payload=payload,
            priority=5
        )

        result_queue.put({
            "status": TitanError.SUCCESS.value,
            "data": response,
            "error_code": None
        })

    except Exception:
        result_queue.put({
            "status": TitanError.KERNEL_ERROR.value,
            "data": None,
            "error_code": TitanError.KERNEL_ERROR.value,
            "msg": traceback.format_exc()
        })
    finally:
        sys.stdout.flush()


class ZStudioBridgeController:

    def __init__(self, max_workers: int = 10, failure_threshold: int = 5, recovery_threshold: int = 5):
        self.runtime_engine = None
        self.capacity_guard = multiprocessing.Semaphore(max_workers)
        self.lock = multiprocessing.Lock()
        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.probe_active = False
        self.recovery_threshold = recovery_threshold
        self.failure_threshold = failure_threshold
        self._shutdown = multiprocessing.Event()

    def attach_runtime_engine(self, engine):
        self.runtime_engine = engine

    def _validate(self, h, d, t, p, to):
        return all([
            isinstance(h, str) and h.strip(),
            isinstance(t, str) and t.strip(),
            isinstance(p, dict),
            isinstance(to, (int, float)) and to > 0,
            d is not None,
            not self._shutdown.is_set()
        ])

    def process(self, handle: str, data: Any, task_type: str, params: dict, timeout: int, retries: int = 2):
        req_id = str(uuid.uuid4())

        if not self._validate(handle, data, task_type, params, timeout):
            return self._finalize_error(req_id, TitanError.VALIDATION_FAIL, "Invalid payload")

        for attempt in range(retries + 1):

            with self.lock:
                if self.state == "OPEN":
                    if (time.time() - self.last_failure_time) > 45:
                        self.state, self.success_count = "HALF-OPEN", 0
                    else:
                        return self._finalize_error(req_id, TitanError.CIRCUIT_OPEN, "Cooling")

                if self.state == "HALF-OPEN" and self.probe_active:
                    return self._finalize_error(req_id, TitanError.OVERLOAD, "Probe active")

                self.probe_active = True

            res = self._run_task(req_id, handle, data, task_type, params, timeout)

            if res.get("status") == TitanError.SUCCESS.value:
                return res

            if attempt < retries and res.get("error_code") in [
                TitanError.TIMEOUT.value,
                TitanError.PROCESS_CRASH.value
            ]:
                time.sleep(min(2 ** attempt + random.uniform(0.1, 0.9), 8))
            else:
                break

        return res

    def _run_task(self, req_id, handle, data, task_type, params, timeout, req_logger=None):
        action_map = {
            "text": "inference_run",
            "voice_clone": "audio_voice_cloning",
            "audio_upscale": "audio_enhancer_v2",
            "bg_remove": "audio_separator_core",
            "music_gen": "music_synthesis_run",
            "image_gen": "stable_diffusion_run",
            "video_gen": "video_render_engine",
            "load": "model_load",
            "status": "system_status"
        }

        if not self.capacity_guard.acquire(block=False):
            return self._finalize_error(req_id, TitanError.OVERLOAD, "Saturated")

        q, p = multiprocessing.Queue(maxsize=1), None
        payload = {"input": data, **params}

        try:
            # FIX: Mapping overwriting khatam, sirf upar wala map use ho raha hai
            final_action = action_map.get(task_type, task_type)

            p = multiprocessing.Process(target=_isolated_kernel_executor, args=(final_action, payload, q))
            p.start()

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    res = q.get(timeout=0.2)
                    self._report_status(True)
                    return {"status": res.get("status"), "data": res.get("data"), "request_id": req_id, "error_code": res.get("error_code")}
                except queue.Empty:
                    if p.is_alive() and (time.time() - start_time) > timeout:
                        p.terminate()
                    if p.exitcode is not None:
                        raise ChildProcessError(f"Exit {p.exitcode}")
            raise TimeoutError("Timeout")

        except Exception as e:
            self._report_status(False)
            err = TitanError.TIMEOUT if isinstance(e, TimeoutError) else TitanError.PROCESS_CRASH
            return self._finalize_error(req_id, err, str(e))
        finally:
            try:
                if p:
                    p.terminate()
                    p.join(timeout=0.5)
            except Exception:
                pass
            self.capacity_guard.release()

    def _report_status(self, success: bool):
        with self.lock:
            if success:
                self.failure_count = 0
                if self.state == "HALF-OPEN":
                    self.success_count += 1
                    if self.success_count >= self.recovery_threshold:
                        self.state = "CLOSED"
                self.probe_active = False

            else:
                self.failure_count += 1
                self.success_count = 0

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    self.last_failure_time = time.time()

                self.probe_active = False


    def _finalize_error(self, req_id, error_enum: TitanError, msg):
        return {
            "request_id": req_id,
            "status": "FAILED",
            "error_code": error_enum.value,
            "message": msg
    
        }
    
    # 2. FIXED: Simplified State Inspection
    def get_state(self):
        return {
            "engine_attached": hasattr(self, "runtime_engine") and self.runtime_engine is not None,
            "status": self.state
        }
        
    def pipe_state(self, payload: dict):
        try:
            #  HOOK: Data ko stream engine ko bhejo
            stream_engine.push(payload) 
            
            logger.info(f"[Z-PIPE] Output Ready: {payload.get('status')}")
            return True
        except Exception as e:
            logger.error(f"[Z-PIPE ERROR] Stream Engine link broken: {str(e)}")
            return False
        
    def user_select_model(self, path: str) -> dict:
        return self.process(
            handle="MODEL_UI",
            data=path,
            task_type="load",
            params={},
            timeout=120
        )
        
    def _sync_with_state_manager(self, state: str) -> None:
        """
        [V12.4 FINAL] - Optimized, Flat Syntax, Zero Recursion Risk.
        """
        # 1. Try to publish to Bus
        try:
            from system_core.control_bus import event_bus
            event_bus.publish("SYSTEM_STATE_CHANGE", {"state": state})
            return  # Success, exit function
        except (ImportError, Exception):
            pass # Fallback to pipe_state
            
        # 2. Fallback: Use pipe_state if Bus fails
        try:
            print(f"[Z-SYNC] Bus failed, falling back to internal pipe: {state}")
            self.pipe_state({
                "status": state, 
                "engine": "INFERENCE_CORE", 
                "silent": True
            })
        except Exception as e:
            # Final safety layer
            logger.error(f"[Z-SYNC CRITICAL] Both Bus and Pipe failed: {e}")
        
# --- YE SAHI WIRING HAI ---
_global_bridge_instance = None

def BridgeController():
    """Poore OS mein sirf ek hi Bridge rehne wala logic"""
    global _global_bridge_instance
    if _global_bridge_instance is None:
        _global_bridge_instance = ZStudioBridgeController()
    return _global_bridge_instance

# Global Variable taaki doosri files access kar sakein
bridge_controller = BridgeController()