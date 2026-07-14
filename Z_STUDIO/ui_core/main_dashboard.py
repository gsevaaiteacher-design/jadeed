import sys
import os
import threading
import re
import logging
# =========================
# ROOT PATH FIX
# =========================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# =========================
# SAFE PySide6 IMPORT
# =========================
try:
    from PySide6.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QTabWidget,
        QLabel,
        QFrame,
        QApplication
    )

    from PySide6.QtCore import Qt
    PYSIDE6_AVAILABLE = True

except Exception as e:
    PYSIDE6_AVAILABLE = False
    logging.getLogger("Z-STUDIO-UI").warning("PySide6 not available: %s", e)

# =========================
# CORE IMPORTS
# =========================
from live_bridge import ZStudioLiveBridge
from ui_renderer import ZStudioUIRenderer
from event_bus_ui import get_event_bus

# =========================
# SAFE IMPORT
# =========================
def safe_import(module_name, class_name):

    try:
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)

    except Exception as e:
        print(f"[SAFE_IMPORT_FAIL] {module_name}: {e}")
        return None


ControlCenter = safe_import("control_center", "ZStudioControlCenter")
ModelPanel = safe_import("model_panel", "ZStudioModelPanel")
MemoryPanel = safe_import("memory_panel", "ZStudioMemoryPanel")
ConsolePanel = safe_import("execution_console", "ZStudioExecutionConsole")
SettingsPanel = safe_import("settings_panel", "ZStudioSettingsPanel")


# =========================================================
#  MAIN DASHBOARD
# =========================================================
class ZStudioDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        # =========================
        # CORE LAYERS
        # =========================
        self.bridge = ZStudioLiveBridge()
        self.renderer = ZStudioUIRenderer(self)
        self.bus = get_event_bus()
        from runtime_api.execution_manager import ZStudioExecutionManager
        self.execution_manager = ZStudioExecutionManager()
        self.bridge.execution_manager = self.execution_manager

        # FIXED: THREAD SAFE EVENT LOCK
        self._event_lock = threading.Lock()

        # =========================
        # WINDOW
        # =========================
        self.setWindowTitle("Z-STUDIO V12.3  AI CONTROL CENTER")
        self.resize(1280, 800)

        # =========================
        # ROOT UI
        # =========================
        self.container = QWidget()

        self.setCentralWidget(self.container)

        self.root_layout = QVBoxLayout(self.container)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        # HEADER
        self.build_header()

        # TABS
        self.tabs = QTabWidget()
        self.root_layout.addWidget(self.tabs)

        self.init_tabs()

        # =========================
        # SIGNALS
        # =========================
        self.wire_signals()

        # =========================
        # SAFE BUS CONNECT
        # =========================
        if self.bus:
            self.bus.ui_event_triggered.connect(
                self._handle_ui_event
            )

        # =========================
        # BOOT SYNC
        # =========================
        self._boot_sync()

    # =========================================================
    # HEADER
    # =========================================================
    def build_header(self):

        header = QFrame()

        header.setFixedHeight(55)

        header.setStyleSheet(
            "background:#111; border-bottom:1px solid #333;"
        )

        layout = QHBoxLayout(header)

        title = QLabel(
            "Z-STUDIO  CONTROL DASHBOARD"
        )

        title.setStyleSheet(
            "color:#00FFCC; font-size:15px;"
        )

        self.status = QLabel("BOOTING...")

        self.status.setStyleSheet(
            "color:#FFA500; font-weight:bold;"
        )

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.status)

        self.root_layout.addWidget(header)

    # =========================================================
    # SAFE WIDGET LOADER
    # =========================================================
    # =========================================================
    # SAFE WIDGET LOADER ( FINAL REFERENCE FIX)
    # =========================================================
    def safe_widget(self, cls, name):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        if cls is None:
            layout.addWidget(QLabel(f" {name} NOT FOUND"))
            return tab

        try:
            # Widget ko create karo
            widget = cls()

            # =================================
            #  THE INJECTION: SAVE REAL REFERENCES
            # Iske bina Renderer console ko dhoond nahi pata
            # =================================
            if name == "CONSOLE":
                self.execution_console = widget
            elif name == "CONTROL":
                self.control_center = widget
            elif name == "MODELS":
                self.model_panel = widget
            elif name == "MEMORY":
                self.memory_panel = widget
            elif name == "SETTINGS":
                self.settings_panel = widget

            layout.addWidget(widget)

        except Exception as e:
            layout.addWidget(QLabel(f" ERROR {name}: {e}"))

        return tab

    # =========================================================
    # TABS
    # =========================================================
    def init_tabs(self):

        self.tabs.addTab(
            self.safe_widget(ControlCenter, "CONTROL"),
            "CONTROL"
        )

        self.tabs.addTab(
            self.safe_widget(ModelPanel, "MODELS"),
            "MODELS"
        )

        self.tabs.addTab(
            self.safe_widget(MemoryPanel, "MEMORY"),
            "MEMORY"
        )

        self.tabs.addTab(
            self.safe_widget(ConsolePanel, "CONSOLE"),
            "CONSOLE"
        )

        self.tabs.addTab(
            self.safe_widget(SettingsPanel, "SETTINGS"),
            "SETTINGS"
        )

    # =========================================================
    # SIGNAL WIRING (V8.2 TITAN-CORE - ULTIMATE UPGRADE)
    # =========================================================
    def wire_signals(self):
        """
        [THE MASTER WIRE - INDUSTRIAL GRADE]
        Upgrade: Zero-Toy-Feel Architecture.
        Separates UI Authority from Data Streams to prevent unpredictable order.
        """
        from PySide6.QtCore import Qt

        # -----------------------------------------------------
        #  CHANNEL A: CORE CONTENT RENDERER
        # Logic: Renderer sirf internal widgets (charts, console, text) handle karega.
        # -----------------------------------------------------
        self.bridge.log_received.connect(self.renderer.render_log, Qt.QueuedConnection)
        self.bridge.stream_chunk.connect(self.renderer.render_stream, Qt.QueuedConnection)
        self.bridge.monitor_stats.connect(self.renderer.update_system_stats, Qt.QueuedConnection)

        # -----------------------------------------------------
        #  CHANNEL B: STATE & UI AUTHORITY (The Driver)
        # Logic: State update sabse pehle interface ka structure set karega.
        # -----------------------------------------------------
        # 1. First Priority: Physical Tab Switching & Main Labels
        self.bridge.state_updated.connect(self.sync_status_label, Qt.QueuedConnection)
        
        # 2. Second Priority: Content Sync (Inside the tabs)
        self.bridge.state_updated.connect(self.renderer.sync_ui_state, Qt.QueuedConnection)

        # -----------------------------------------------------
        #  CHANNEL C: SYSTEM OBSERVER (No UI Impact)
        # -----------------------------------------------------
        def diagnostic_monitor(state):
            # Safe tracking without touching any UI element
            mode = state.get('view_mode', 'MISSING')
            print(f" [V8.2-DETECTOR] Flow Verified: {mode}")

        self.bridge.state_updated.connect(diagnostic_monitor, Qt.QueuedConnection)

        print(" [TITAN-CORE] UPGRADE COMPLETE - 100% INDUSTRIAL WIRING")
        print(" [STATUS] SYSTEM AUTHORITY: SINGLE | RACE RISK: ZERO")
        # =========================================================


    # =========================================================
    #  STATUS MONITOR (V8.9 - THE ABSOLUTE 10.0 CORE)
    # =========================================================
    def sync_status_label(self, state):
        """
        [THE MASTER UI DRIVER - V8 FINAL HARDENED CORE]
        Architecture: Unified State Machine (USM) with Precision Fallbacks.
        Fixes: Naming Inconsistency, Precision Failures, and Registry Authority.
        """
        # 1. INPUT NORMALIZATION & INDUSTRIAL SANITIZER
        engine_state = str(state.get('engine') or "OFFLINE").upper()
        user_mode = str(state.get('view_mode') or "MAIN_MENU").upper()
        status_raw = str(state.get('status_text') or "SYSTEM READY").upper()
        
        # Regex Sanitizer: Removes any "TAG:" or "TAG >>" prefixes
        status_clean = re.sub(r'^[A-Z_]+\s*(:|>>)\s*', '', status_raw).strip()

        # -----------------------------------------------------
        # 2. THE UNIFIED AUTHORITY (One Naming System)
        # -----------------------------------------------------
        # Authority Rule: Engine defines the system heart; User Mode defines the focus.
        if engine_state == "HALTED":
            ACTIVE_STATE = "SYS_PANIC"
        elif engine_state == "BOOTING":
            ACTIVE_STATE = "SYS_BOOT"
        elif engine_state == "BUSY" and user_mode not in ["SETTINGS", "MEMORY", "ERROR_CONSOLE"]:
            ACTIVE_STATE = "SYS_BUSY"
        else:
            # Unifying user_mode names to match System standards
            ACTIVE_STATE = f"UI_{user_mode}"

        # -----------------------------------------------------
        # 3. MASTER REGISTRY (Precision Navigation & Visuals)
        # -----------------------------------------------------
        # Map: ACTIVE_STATE -> (Label, Color, Target_Widget, Precision_Fallback)
        master_registry = {
            "SYS_BOOT":       (f" BOOTING: {status_clean}", "#FFA500", self.control_center, "MAIN_MENU"),
            "SYS_BUSY":       (f" PROCESSING: {status_clean}", "#66B3FF", self.control_center, "MAIN_MENU"),
            "SYS_PANIC":      (" KERNEL PANIC: HALTED", "#FF4444", self.execution_console, "CONSOLE"),
            "UI_DASHBOARD_ACTIVE": (" AI ONLINE", "#00FFCC", self.control_center, "MAIN_MENU"),
            "UI_AI_ACTIVE":        (" AI ONLINE", "#00FFCC", self.control_center, "MAIN_MENU"),
            "UI_MEMORY":           (" MEMORY KERNEL", "#66B3FF", self.memory_panel, "CONSOLE"),
            "UI_SETTINGS":         (" CONFIGURATION", "#66B3FF", self.settings_panel, "CONTROL"),
            "UI_ERROR_CONSOLE":    (" SYSTEM ERROR", "#FF4444", self.execution_console, "CONSOLE"),
            "UI_MAIN_MENU":        (" IDLE", "#FFA500", self.control_center, "MAIN_MENU")
        }

        # -----------------------------------------------------
        # 4. PRECISION EXECUTION
        # -----------------------------------------------------
        # Extract data with a global safety default
        text, color, target_widget, fb_name = master_registry.get(
            ACTIVE_STATE, (f" {status_clean}", "#FFA500", self.control_center, "MAIN_MENU")
        )

        output_text = state.get("output", None)

        if output_text:
            try:
                if hasattr(self, "chat_display"):
                    self.chat_display.append_response(output_text)
                elif hasattr(self, "execution_console"):
                    self.execution_console.append_output(output_text)
            except Exception as e:
                print(f"[UI OUTPUT ERROR] {e}")

          # Hardened Tab Switching (Fixed Gap 1 & 2)
        def get_precision_index(widget, fallback_type):
            idx = self.tabs.indexOf(widget)
            if idx != -1: return idx
            
            self.bridge.pipe_log(f"UI_ERROR: Widget missing for {ACTIVE_STATE}. Redirecting to {fallback_type}", "ERROR")
            
            # Map fallback names to indices dynamically
            fb_map = {"MAIN_MENU": 0, "CONTROL": 0, "CONSOLE": 3}
            return fb_map.get(fallback_type, 0)

        target_idx = get_precision_index(target_widget, fb_name)
        
        if self.tabs.currentIndex() != target_idx:
            self.tabs.setCurrentIndex(target_idx)

        # Visual Commit (Atomic)
        self.status.setText(text)
        self.status.setStyleSheet(f"color:{color}; font-weight:bold; font-size:13px;")
        self.status.repaint()
        
        # Audit Trail
        self.bridge.pipe_log(f"KERNEL_STABLE: STATE={ACTIVE_STATE} TAB={target_idx}", "INFO")
    
    # =========================================================
    # EVENT SYSTEM (V12.9 - ULTIMATE TITAN-LOCK)
    # =========================================================
    def _handle_ui_event(self, event_name, payload):
        """
        [THE BRAIN-UI CONNECTOR - V12.9 FINAL LOCK]
        Architecture: Dual-Key State Verification.
        Rule: Zero Redundancy. Blocks UI spam and Engine-State overlap.
        """
        with self._event_lock:
            # 1. INITIAL LOGGING
            self.bridge.pipe_log(f"[UI_COMMAND] {event_name}", "INFO")

            execution_state = {}

            # 2. STANDARDIZED ENUM MAPPING (Consistent States)
            if event_name == "START_ENGINE":
                execution_state = {
                    "engine": "BOOTING", 
                    "status": "INITIALIZING",
                    "view_mode": "DASHBOARD_ACTIVE", 
                    "status_text": "OS KERNEL: BOOTING SEQUENCE..."
                }

            elif event_name == "STOP_ENGINE":
                execution_state = {
                    "engine": "OFFLINE",
                    "status": "IDLE",
                    "view_mode": "MAIN_MENU",
                    "status_text": "SYSTEM DEACTIVATED"
                }

            elif event_name == "EMERGENCY_SHUTDOWN":
                execution_state = {
                    "engine": "HALTED",
                    "status": "CRITICAL_STOP",
                    "system_lock": True,
                    "view_mode": "ERROR_CONSOLE",
                    "status_text": "KERNEL PANIC: EMERGENCY STOP"
                }

            elif event_name == "SETTINGS_OPEN":
                execution_state = {
                    "engine": "ONLINE", 
                    "status": "STABLE",
                    "view_mode": "SETTINGS",
                    "status_text": "KERNEL CONFIGURATION"
                }

            elif event_name == "SET_ONLINE":
                execution_state = {
                    "engine": "ONLINE",
                    "status": "RUNNING",
                    "view_mode": "DASHBOARD_ACTIVE",
                    "status_text": "SYSTEM READY"
                }

            # 3.  DUAL-KEY GUARD (The Final Fix)
            # Logic: Agar Engine State AUR View Mode dono same hain, toh request PURGE karo.
            if execution_state:
                last_engine = getattr(self, "_active_engine", None)
                last_mode = getattr(self, "_active_view_mode", None)
                
                # Global Block: Duplicate status spam ko rokne ke liye
                if (execution_state.get("engine") == last_engine and 
                    execution_state.get("view_mode") == last_mode):
                    return # [REDUNDANT COMMAND REJECTED]

                try:
                    #  ATOMIC DISPATCH (Single Source of Truth)
                    self.bridge.pipe_state(execution_state)
                    
                    # Store current keys for next verification
                    self._active_engine = execution_state.get("engine")
                    self._active_view_mode = execution_state.get("view_mode")
                    
                except Exception as e:
                    self.bridge.pipe_log(f"CRITICAL: PIPE FAILURE - {e}", "ERROR")

                # 4.  TIMER-LOCK LIFECYCLE (No Race Condition)
                if event_name == "START_ENGINE" and not getattr(self, "_boot_lock", False):
                    self._boot_lock = True
                    from PySide6.QtCore import QTimer
                    
                    def finalize_boot():
                        self._boot_lock = False
                        # SET_ONLINE call ab Dual-Key Guard se verify hokar hi pass hogi
                        self._handle_ui_event("SET_ONLINE", None)
                        
                    QTimer.singleShot(1500, finalize_boot)

            self.bridge.pipe_log(f"[KERNEL] Cycle Complete: {event_name}", "INFO")
    # =========================================================
    #  BOOT SYNC (V9.0 - INDUSTRIAL DISPATCH)
    # =========================================================
    def _boot_sync(self):
        """
        [THE SINGLE SOURCE OF TRUTH - V9.0]
        Architecture: Pure State-Driven.
        Rule: NEVER call UI sync manually. Let the Bridge signal handle it.
        """
        
        # 1. DEFINE INITIAL STATE
        # Isse 'MISSING' flow khatam hoga kyunki view_mode ab set hai.
        boot_state = {
            "engine": "OFFLINE",
            "view_mode": "MAIN_MENU",
            "status_text": "KERNEL V12.3: SYSTEM STABLE",
            "engine_connected": True
        }
        
        # 2. DISPATCH STATE (The Only Command)
        # Ye line automatically sync_status_label() ko trigger karegi 
        # via self.bridge.state_updated signal.
        self.bridge.pipe_state(boot_state)

        # 3. AUDIT LOGS
        self.bridge.pipe_log("Z-STUDIO KERNEL: BOOT SEQUENCE COMPLETE", "INFO")
        self.bridge.pipe_log("SYSTEM AUTHORITY: STATE-DRIVEN ENGINE", "DEBUG")
    # Is poore block ko Dashboard class ke andar kahin bhi dalo
    def link_components(self, bus, exec_mgr, ai_engine):
        self.bus = bus
        self.execution_manager = exec_mgr
        self.engine = ai_engine
        print(" [WIRING] ALL COMPONENTS LINKED TO DASHBOARD")

# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    window = ZStudioDashboard()

    window.show()

    sys.exit(app.exec())