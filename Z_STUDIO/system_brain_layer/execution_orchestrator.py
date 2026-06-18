"""
Z-STUDIO OS  SYSTEM BRAIN LAYER
=============================================================================
Module: execution_orchestrator
Version: 14.0 (V8 Hardened Architecture  Solid Decoupled Control Kernel)
Role: Central Brain Intelligence, High-Throughput Traffic Router, Gateway Guard.
Design Pattern: Sub-Component Decoupling, Pre-Warmed Isolated Worker Pools,
                Encapsulated Telemetry Registry, Autonomous Circuit Breaker Matrix.

 ULTIMATE ARCHITECTURAL PURITY: Eradicates Monolithic Blur via Strict Layer Separation.
=============================================================================
"""

import time
import uuid
import logging
import threading
import queue
from typing import Dict, Any, Optional, Tuple, Callable, List

logger = logging.getLogger("Z-STUDIO.ORCHESTRATOR")

from system_core.portless_router import router




class _TelemetryRegistry:
    """
     LAYER 1: THE ACCOUNTANT (Dedicated Observability & Metrics Registry)
    Strictly handles running latency metrics, drop-counters, and system snapshots.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.total_tasks_processed = 0
        self.total_tasks_dropped = 0
        self.total_routing_failures = 0
        self.callback_overflow_drops = 0
        self.watchdog_timeouts = 0
        self.average_system_latency = 0.0
        self.channel_latency_registry: Dict[str, List[float]] = {}
        

    def record_latency(self, channel: str, latency: float) -> None:
        with self.lock:
            latencies = self.channel_latency_registry.setdefault(channel, [])
            latencies.append(latency)
            if len(latencies) > 20:
                latencies.pop(0)  # Rolling slice window
            self.average_system_latency = (self.average_system_latency * 0.9) + (latency * 0.1)

    def get_average_latency(self, channel: str) -> float:
        with self.lock:
            latencies = self.channel_latency_registry.get(channel, [])
            if not latencies:
                return 0.0
            return sum(latencies) / len(latencies)

    def generate_report(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "total_tasks_processed": self.total_tasks_processed,
                "total_tasks_dropped": self.total_tasks_dropped,
                "total_routing_failures": self.total_routing_failures,
                "callback_overflow_drops": self.callback_overflow_drops,
                "watchdog_timeouts": self.watchdog_timeouts,
                "average_system_latency": self.average_system_latency
            }


class _CircuitBreaker:
    """
     LAYER 2: THE GUARDIAN (Dedicated Reliability & Quarantine Engineer)
    Strictly handles circuit states, fault limits, and dynamic historic decay curves.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.failures: Dict[str, float] = {}
        self.successes: Dict[str, int] = {}
        self.tripped_circuits: Dict[str, float] = {}
        self.THRESHOLD = 3.0
        self.COOLDOWN = 15.0
        self.HEAL_THRESHOLD = 5
        self.DECAY_RATE = 0.85

    def is_healthy(self, channel: str) -> bool:
        now = time.time()
        with self.lock:
            if channel in self.tripped_circuits:
                if now < self.tripped_circuits[channel]:
                    return False
                # Cooldown expired, auto-clear quarantine line
                del self.tripped_circuits[channel]
                self.failures[channel] = 0.0
                self.successes[channel] = 0
            return True

    def record_failure(self, channel: str) -> None:
        with self.lock:
            self.successes[channel] = 0
            self.failures[channel] = self.failures.get(channel, 0.0) + 1.0
            if self.failures[channel] >= self.THRESHOLD:
                self.tripped_circuits[channel] = time.time() + self.COOLDOWN
                logger.critical(f" CIRCUIT_TRIPPED: Isolated faulty route channel [{channel}].")

    def record_success(self, channel: str) -> None:
        with self.lock:
            if channel in self.tripped_circuits:
                return
            self.failures[channel] = max(0.0, self.failures.get(channel, 0.0) - 0.5)
            self.successes[channel] = self.successes.get(channel, 0) + 1
            if self.successes[channel] >= self.HEAL_THRESHOLD:
                logger.info(f" CIRCUIT_STABILIZED: Route channel [{channel}] verified operational.")

    def apply_decay(self) -> None:
        with self.lock:
            for channel in list(self.failures.keys()):
                if channel not in self.tripped_circuits:
                    self.failures[channel] *= self.DECAY_RATE
                    if self.failures[channel] < 0.05:
                        self.failures[channel] = 0.0


class ExecutionOrchestrator:
    """
     LAYER 3: THE MASTER SWITCHBOARD (Decoupled Central Core Brain)
    Pure structural responsibility: Validates tasks, sorts traffic lanes, handles callbacks.
    """
    def __init__(self, runtime_bus: Any):
        self._assert_bus_contract(runtime_bus)
        
        self.bus = runtime_bus
        self.memory_controller = None
        self.scheduler = None
        self.resource_guard = None
        
        self.version = "14.0"
        self._lock = threading.RLock()
        self._system_operational = True
        
        if not hasattr(self.bus, "get_available_channels"):
            self.bus.get_available_channels = lambda: ["inference", "system_core"]
        
        #  STRUCTURAL SUB-MODULE INJECTIONS (SRP Compliance)
        self.telemetry = _TelemetryRegistry()
        self.circuit_breaker = _CircuitBreaker()
        
        #  MULTI-ENGINE ADAPTIVE FALLBACK CHAIN MATRIX
        self.ROUTES = {
            "LICENSE_VALIDATION": ["security_vault", "system_core", "fallback_engine"],
            "MODEL_LOAD": ["runtime_engine", "system_core", "fallback_engine"],
            "INFERENCE": ["inference", "fallback_engine"],
            "TOOL_EXEC": ["tool_executor", "execution_manager", "fallback_engine"],
            "MULTIMODAL": ["multimodal_router", "ai_engine", "fallback_engine"],
            "MEMORY": ["vector_db", "system_core", "fallback_engine"],
            "API_GEN": ["execution_manager", "fallback_engine"],
            "SYSTEM": ["system_core", "fallback_engine"],
            "FALLBACK": ["fallback_engine"]
        }
        
        #  ALLOCATION CAPS
        self.MAX_RETRY_DEPTH = 2
        self.MAX_CALLBACK_REGISTRY_CAP = 5000            
        self.TRACE_TTL = 300.0                             
        self.MAX_QUEUE_THRESHOLD = 1000
        self.CRITICAL_REJECT_LIMIT = 2500
        
        #  MEMORY REGISTERS
        self._internal_retry_registry: Dict[str, int] = {}  
        self._global_trace_registry: Dict[str, float] = {}  
        self._callback_registry: Dict[str, Tuple[Callable, float, Dict[str, Any], str, float]] = {} 
        self._lifecycle_states: Dict[str, str] = {}
        
        #  PRE-WARMED WORKER THREAD POOL PIPELINE
        self.MAX_POOL_WORKERS = 16
        self._callback_queue: queue.Queue = queue.Queue(maxsize=10000)
        self._pool_workers: List[threading.Thread] = []
        self.active_queue_depth = 0
        
        #  WATCHDOG POINTERS
        #  WATCHDOG POINTERS
        self._watchdog_thread: Optional[threading.Thread] = None

        # =====================================================================
        #  CHK FIX: REGISTER SELF TO THE BUS SO LAUNCHER POST 8 CAN RESOLVE IT
        # =====================================================================
        if runtime_bus is not None and hasattr(runtime_bus, "stage_service"):
            runtime_bus.stage_service("orchestrator", self)
        # =====================================================================
        
        # Trigger initialization sequences
        self._initialize_closed_loop_listener()
        self._spawn_worker_thread_pool()
        self._spawn_lifecycle_watchdog()
        
        logger.info(f" Z-STUDIO KERNEL [v{self.version}]: Decoupled Architecture Core Engaged.")
        print(f"[DEBUG] ORCHESTRATOR BUS ID: {id(self.bus)}")


        
        
        # 2. Registry     (     )
        self.registry = None 

        # --- [FORCE FIX] ---
        self.registry = self.bus.resolve("registry")
        
        
        # -------------------
        
        # 3.       'Tools' 
        logger.info(" Brain Mesh Initialized: Orchestrator fully linked.")

        

        
        
        

        
        logger.info(f"Z-STUDIO KERNEL [v{self.version}]: Decoupled Architecture Core Engaged.")
        logger.info(" Brain Mesh Initialized: Orchestrator fully linked.")


    def bind_service(self, name, instance):
        if name == "memory_budget_controller": self.memory_controller = instance
        elif name == "scheduler": 
            self.scheduler = instance
            self.scheduler.set_orchestrator(self)
        elif name == "resource_guard": self.resource_guard = instance
        elif name == "inference": self.inference_engine = instance
        elif name == "registry": 
            # Ab hum trust kar sakte hain ki instance ke paas get_active_channel hai
            self.registry = instance
        
        print(f"[ORCHESTRATOR] Successfully bound {name}")

    def discover_services(self):
        #   'inference'  
        if hasattr(self.bus, "get_service"):
            service = self.bus.get_service("inference")
            if service:
                self.inference_engine = service
                print("[ORCHESTRATOR] Inference Engine discovered and linked.")

    def _assert_bus_contract(self, bus: Any) -> None:
        if bus is None:
            raise ValueError(" KERNEL_CONTRACT_CRITICAL: Transport Bus instance cannot be None.")
        required_attributes = ["emit", "on", "has_channel", "system_state_snapshot"]
        missing_contracts = [attr for attr in required_attributes if not hasattr(bus, attr)]
        if missing_contracts:
            raise AttributeError(f" KERNEL_CONTRACT_VIOLATION: Transport layers layout broken: {missing_contracts}")

    def _initialize_closed_loop_listener(self) -> None:
        try:
            self.bus.on("RESULT_READY", self._handle_engine_response_reconciliation)
        except Exception as e:
            logger.error(f" CONTRACT_WARN: Bus interface integration fault: {e}")

    def _spawn_worker_thread_pool(self) -> None:
        with self._lock:
            for i in range(self.MAX_POOL_WORKERS):
                worker = threading.Thread(
                    target=self._dedicated_pool_worker_loop,
                    name=f"Z-CoreWorker-{i:02d}",
                    daemon=True
                )
                worker.start()
                self._pool_workers.append(worker)

    def _dedicated_pool_worker_loop(self) -> None:
        while self._system_operational:
            try:
                task_item = self._callback_queue.get(block=True, timeout=1.0)
                if task_item is None:
                    break
                
                callback_target, payload, trace_id = task_item
                try:
                    callback_target(payload)
                except Exception as cb_err:
                    logger.critical(f" POOL_WORKER_EXECUTION_CRASH for trace [{trace_id}]: {cb_err}")
                finally:
                    self._callback_queue.task_done()
            except queue.Empty:
                continue

    def _spawn_lifecycle_watchdog(self) -> None:
        with self._lock:
            self._watchdog_thread = threading.Thread(
                target=self._lifecycle_watchdog_loop, 
                name="Z-Studio-CoreWatchdog-v14.0", 
                daemon=True
            )
            self._watchdog_thread.start()

    def _lifecycle_watchdog_loop(self) -> None:
        while self._system_operational:
            try:
                time.sleep(1.0)
                self.flush_expired_lifecycles()
                self.circuit_breaker.apply_decay()  # Delegated out to sub-module
                self._purge_expired_global_traces()
            except Exception as e:
                logger.error(f" WATCHDOG_RUNTIME_ANOMALY: Internal evaluation fault state: {e}")

    def submit_task(self, raw_task: Dict[str, Any], completion_callback: Optional[Callable] = None) -> Tuple[bool, Dict[str, Any]]:
        print(f"[DEBUG] Registry object: {self.registry}")
        print(f"[DEBUG] Does registry have method: {hasattr(self.registry, 'get_active_channel')}")
        # --- [FIX START]: PEHLE CHECK KARO KI KYA SYSTEM READY HAI ---
        if self.memory_controller is None or self.scheduler is None or getattr(self, 'registry', None) is None:
            # Agar abhi tak linkage nahi hui, toh task ko process mat karo
            print(f"[CRITICAL] Orchestrator not yet linked. Dependencies: Memory={self.memory_controller is not None}, Scheduler={self.scheduler is not None}, Registry={getattr(self, 'registry', None) is not None}")
            return False, self._generate_error_payload(raw_task, "BOOT_PENDING", "Orchestrator dependencies not ready yet.")
        # --- [FIX END] ---

        # 1.  
        if not isinstance(raw_task, dict) or "payload" not in raw_task:
            return False, self._generate_error_payload(raw_task, "INVALID_FORMAT", "Task layout error.")
        
        # 2. 
        task_type = self._classify_intent(raw_task)
        # ... baaki ka purana code waisa ka waisa hi rahega ...

        trace_id = raw_task.get("trace_id") or f"Z-TRC-{uuid.uuid4().hex[:12].upper()}"
        
        # 3.  
        with self._lock:
            if self.active_queue_depth >= self.CRITICAL_REJECT_LIMIT or len(self._callback_registry) >= self.MAX_CALLBACK_REGISTRY_CAP:
                self.telemetry.total_tasks_dropped += 1
                return False, self._generate_error_payload(raw_task, "BACKPRESSURE_REJECT", "Kernel resources saturated.")
            self.active_queue_depth += 1

        try:
            # 4.    
            if not self.memory_controller.check_budget(1024, 0):
                return self.scheduler.enqueue_and_wait(raw_task)

            active_channel = self.registry.get_active_channel(task_type)
            if active_channel == "text_core": 
                active_channel = "inference"
            if not active_channel:
                print(f"[CRITICAL] Channel not found for {task_type}. Trying to force-load...")
                self.bus.emit("MODEL_LOAD_REQUEST", {"task_type": "text", "model_id": "text_core"})
                return self.scheduler.enqueue_and_wait(raw_task)

            # 5.   (Global Registry)
            with self._lock:
                if trace_id in self._global_trace_registry:
                    return False, self._generate_error_payload(raw_task, "DUPLICATE_TRACE", "Replay token dropped.")
                self._global_trace_registry[trace_id] = time.time()

            # 6.  
            is_safe, reason = self._validate_safety_gate_with_state(raw_task)
            if not is_safe:
                return False, self._generate_error_payload(raw_task, "SAFETY_VIOLATION", reason)

            # 7.  
            enriched_task = self._enrich_task(task_type, raw_task, trace_id)
            potential_channels = [active_channel] 
            dispatch_status = False
            allocated_channel = active_channel

            for iteration, channel in enumerate(potential_channels):
                print(f"[DEBUG] Attempting dispatch to channel: '{channel}' | Bus has channel: {self.bus.has_channel(channel)}")
                if iteration > self.MAX_RETRY_DEPTH: break
                
                #   
                if not self.circuit_breaker.is_healthy(channel) or not self.bus.has_channel(channel):
                    continue
                
                enriched_task["route"] = channel
                if completion_callback:
                    with self._lock:
                        self._callback_registry[trace_id] = (completion_callback, time.time() + 30.0, enriched_task, channel, time.time())
                        self._lifecycle_states[trace_id] = "DISPATCHED"

                dispatch_status = self._safe_non_blocking_bus_dispatch(channel, enriched_task)
                if dispatch_status: break
                else: self.circuit_breaker.record_failure(channel)

            if not dispatch_status:
                return False, self._generate_error_payload(raw_task, "MAX_RETRIES_EXHAUSTION", "Delivery routing failed.")

            self.telemetry.total_tasks_processed += 1
            return True, {"status": "DISPATCHED", "trace_id": trace_id, "channel": allocated_channel}

        except Exception as e:
            logger.critical(f"KERNEL_CORE_PANIC: {str(e)}")
            return False, self._generate_error_payload(raw_task, "CRITICAL_KERNEL_FAULT", str(e))

        finally:
            with self._lock:
                self.active_queue_depth = max(0, self.active_queue_depth - 1)
                if trace_id in self._internal_retry_registry: del self._internal_retry_registry[trace_id]

    def _safe_non_blocking_bus_dispatch(self, channel: str, packet: Dict[str, Any]) -> bool:
        execution_status = [False]
        def _target_emission_wrapper():
            try:
                if hasattr(self.bus, "emit_with_ack") and callable(self.bus.emit_with_ack):
                    execution_status[0] = self.bus.emit_with_ack(channel, packet)
                else:
                    self.bus.emit(channel, packet)
                    execution_status[0] = True
            except Exception:
                execution_status[0] = False

        dispatch_worker = threading.Thread(target=_target_emission_wrapper, daemon=True)
        dispatch_worker.start()
        dispatch_worker.join(timeout=5.0)
        return execution_status[0]

    def _classify_intent(self, task: Dict[str, Any]) -> str:
        explicit_type = str(task.get("type", "")).upper().strip()
        if explicit_type == "LICENSE" or "license_key" in task.get("payload", {}):
            return "LICENSE_VALIDATION"
        if explicit_type in self.ROUTES:
            return explicit_type
        return "FALLBACK"

    def _get_latency_sorted_channels(self, task_type: str) -> List[str]:
        configured_channels = self.ROUTES.get(task_type, self.ROUTES["FALLBACK"])
        with self._lock:
            return sorted(configured_channels, key=lambda ch: self.telemetry.get_average_latency(ch))

    def _validate_safety_gate_with_state(self, task: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            state_snapshot = self.bus.system_state_snapshot.read()
            if state_snapshot.get("memory_stress_level", 0.0) > 0.92:
                return False, "STATE_VIOLATION: System memory exhausted."
        except Exception:
            pass
        return True, "SAFE"

    def _enrich_task(self, task_type: str, task: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        return {
            "trace_id": trace_id,
            "timestamp": task.get("timestamp", time.time()),
            "reply_to": task.get("reply_to", "ui_notification_bridge"),
            "priority": int(task.get("priority", 2)), 
            "type": task_type,
            "payload": task.get("payload", {}),
            "orchestrator_version": self.version
        }

    def _handle_engine_response_reconciliation(self, response_payload: Dict[str, Any]) -> None:
        """
         CLOSED-LOOP RECONCILIATION GATEWAY (Atomic Execution Hand-off)
        """
        print(f"[DEBUG] RECONCILIATION GATEWAY RECEIVED: {response_payload}")
        
        if not isinstance(response_payload, dict) or "trace_id" not in response_payload:
            return

        trace_id = response_payload["trace_id"]
        callback_target, active_channel, dispatch_time = None, "unknown", 0.0

        with self._lock:
            if trace_id in self._callback_registry and self._lifecycle_states.get(trace_id) == "DISPATCHED":
                callback_target, expiration, _, active_channel, dispatch_time = self._callback_registry[trace_id]
                self._lifecycle_states[trace_id] = "RECONCILED"
                del self._callback_registry[trace_id]
                del self._lifecycle_states[trace_id]

        if callback_target:
            current_latency = time.time() - dispatch_time
            # Delegate out operational records metrics
            self.circuit_breaker.record_success(active_channel)
            self.telemetry.record_latency(active_channel, current_latency)

            try:
                self._callback_queue.put_nowait((callback_target, response_payload, trace_id))
            except queue.Full:
                with self._lock: self.telemetry.callback_overflow_drops += 1
                emergency_payload = self._generate_error_payload({"trace_id": trace_id}, "QUEUE_OVERFLOW_SHED", "System buffer full.")
                threading.Thread(target=lambda: callback_target(emergency_payload), daemon=True).start()

    def flush_expired_lifecycles(self) -> None:
        now = time.time()
        expired_traces = []
        
        with self._lock:
            for trace_id, (cb, expiration, _, active_channel, _) in list(self._callback_registry.items()):
                if now > expiration:
                    expired_traces.append((trace_id, cb, active_channel))
                    del self._callback_registry[trace_id]
                    if trace_id in self._lifecycle_states: del self._lifecycle_states[trace_id]
                    
        for trace_id, cb, active_channel in expired_traces:
            with self._lock: self.telemetry.watchdog_timeouts += 1
            self.circuit_breaker.record_failure(active_channel)
            try:
                timeout_payload = {
                    "trace_id": trace_id,
                    "status": "TIMEOUT_REJECTED",
                    "error_metrics": {"code": "WORKER_HANG_TIMEOUT", "reason": "Execution timed out."}
                }
                self._callback_queue.put_nowait((cb, timeout_payload, trace_id))
            except queue.Full:
                pass

    def _purge_expired_global_traces(self) -> None:
        now = time.time()
        with self._lock:
            for trace_id, entry_time in list(self._global_trace_registry.items()):
                if now - entry_time > self.TRACE_TTL:
                    del self._global_trace_registry[trace_id]

    def get_live_telemetry_report(self) -> Dict[str, Any]:
        """ METRICS PASS-THROUGH FROM DECOUPLED OBJECT"""
        report = self.telemetry.generate_report()
        with self._lock:
            report.update({
                "orchestrator_version": self.version,
                "current_active_queue_depth": self.active_queue_depth,
                "worker_pool_queue_size": self._callback_queue.qsize()
            })
        return report

    def terminate_orchestrator_kernels(self) -> None:
        self._system_operational = False
        with self._lock:
            for _ in range(self.MAX_POOL_WORKERS):
                self._callback_queue.put(None)
        logger.info(" SHUTDOWN: Orchestrator decoupled runtime modules terminated.")

    def _generate_error_payload(self, task: Dict[str, Any], err_code: str, message: str) -> Dict[str, Any]:
        return {
            "trace_id": task.get("trace_id", f"Z-ERR-{uuid.uuid4().hex[:8].upper()}"),
            "timestamp": time.time(),
            "status": "REJECTED",
            "error_metrics": {"code": err_code, "reason": message, "stage": "KERNEL_INDUSTRIAL_GATEWAY"}
        }
    

    def dispatch(self, topic: str, data: Any):
        # 1. HANDLERS (System Signals)
        print(f"[DEBUG_VERIFY] Current Bus Subscribers: {self.bus._subscribers.get('inference')}")
        handlers = {
            "ORCHESTRATOR_TASK": self.submit_task,
            "ENGINE_LOADED_SIGNAL": self._on_engine_loaded,
            "TASK_STATUS": self._on_task_update,
            "EXECUTION_PROGRESS": self._on_progress,
            "RUNTIME_READY": self._on_runtime_ready,
            "UI_REQUEST": self._on_ui_request
        }
        
        if topic in handlers:
            return handlers[topic](data)

        # 2. [FIXED] BUS-FIRST DISPATCH
        # Hum engine.execute() ki jagah Bus publish use kar rahe hain
        # taaki InferenceEngine ka listener (subscribe) trigger ho sake.
        try:
            # Task format banao
            packet = {
                "payload": data,
                "trace_id": f"Z-TRC-{time.time()}",
                "type": "inference"
            }
            
            target_channel = "inference"
            print(f"[DEBUG] Orchestrating via Bus Channel: '{target_channel}'")
            
            # Yahan se Engine ka _bus_inference_entry() trigger hoga
            print(f"[ORCHESTRATOR_TRACE] Publishing to bus: {task}")
            print(f"[VERIFY_ORCH] Publishing to Channel 'inference'. Bus Registry: {self.bus._subscribers.keys()}")
            self.bus.publish(target_channel, packet)
            
            return {"status": "DISPATCHED_TO_BUS", "channel": target_channel}
            
        except Exception as e:
            print(f"[ORCHESTRATOR ERROR] Bus Dispatch failed: {e}")
            return {"status": "DISPATCH_FAILED", "error": str(e)}
    # =====================================================
    # EVENT HANDLERS (    )
    # =====================================================
    def _on_engine_loaded(self, data):
        return {"status": "ENGINE_CONFIRMED"}

    def _on_task_update(self, data):
        #      
        return {"status": "TASK_UPDATED"}

    def _on_progress(self, data):
        return {"status": "PROGRESS_LOGGED"}

    def _on_runtime_ready(self, data):
        return {"status": "RUNTIME_ACTIVE"}

    def _on_ui_request(self, data):
        #   'hii'        
        print(f"[ORCHESTRATOR] UI Request received: {data}")
        return {"response": f"Z-STUDIO ACK: Processed {data}"}
    
def get_orchestrator(runtime_bus):
    return ExecutionOrchestrator(runtime_bus)
orchestrator = ExecutionOrchestrator
orchestrator_core = ExecutionOrchestrator