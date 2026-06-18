import sys
import os

# System path set karna taaki files mil sakein
sys.path.append(os.getcwd())

print(" --- Z-STUDIO WIRING DIAGNOSTIC START ---")

try:
    # 1. Check Master Bridge
    from runtime_api.bridge_controller import BridgeController
    bridge = BridgeController()
    print(" [BRIDGE] Controller Loaded.")
    
    state = bridge.get_state() if hasattr(bridge, 'get_state') else "No state method"
    print(f" [STATUS] Current System State: {state}")

    # 2. Check Execution Manager
    from runtime_api.execution_manager import ZStudioExecutionManager
    em = ZStudioExecutionManager()
    print(" [MANAGER] Execution Manager Active.")

    # 3. Check wiring integrity
    integrity = {
        "bus": em.bus is not None,
        "orchestrator": em.orchestrator is not None,
        "bridge": em.live_bridge is not None,
        "ai": em.ai_brain is not None,
    }
    print(f" [WIRING] Links: {integrity}")

except Exception as e:
    print(f" [CRASHED] Diagnostic failed at: {e}")

print(" --- DIAGNOSTIC COMPLETE ---")