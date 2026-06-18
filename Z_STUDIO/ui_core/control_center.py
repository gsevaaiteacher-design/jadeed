"""
ROLE: 2/11 - CONTROL CENTER (SYSTEM COMMANDER)
VERSION: 1.2.0 (HARDENED PRODUCTION CORE)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
"""

# 1. Ye line aisi honi chahiye (Qt, Signal, Slot, QTimer chaaro hone chahiye)
from PySide6.QtCore import Qt, Signal, Slot, QTimer

# 2. Aur niche wali line mein QApplication check kar lo
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QFrame,
    QApplication
)
from event_bus_ui import get_event_bus

class ZStudioControlCenter(QWidget):
    def __init__(self, parent_layout=None):
        super().__init__()

        # =========================
        #  SYSTEM STATE GUARDS
        # =========================
        self._engine_locked = False 
        self.bus = get_event_bus()

        # Attach to dashboard if layout provided
        if parent_layout:
            parent_layout.addWidget(self)

        # =========================
        # UI STRUCTURE
        # =========================
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(20)

        self._apply_style()
        self._build_header()
        self._build_engine_controls()
        self._build_memory_controls()
        
        # Bottom spacer
        self.main_layout.addStretch()

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background: #0B0B0B;
                color: #DDD;
                font-family: 'Segoe UI', Arial;
            }
            QGroupBox {
                border: 1px solid #2A2A2A;
                border-radius: 12px;
                margin-top: 20px;
                padding: 15px;
                font-weight: bold;
                color: #00FFCC;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QPushButton {
                background: #151515;
                border: 1px solid #2F2F2F;
                color: #FFF;
                padding: 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                text-align: center;
            }
            QPushButton:hover {
                border: 1px solid #00FFCC;
                background: #1A1A1A;
                color: #00FFCC;
            }
            QPushButton:pressed {
                background: #00FFCC;
                color: #000;
            }
            QPushButton#emergency_btn {
                border: 1px solid #FF3333;
            }
            QPushButton#emergency_btn:hover {
                background: #330000;
                color: #FF3333;
            }
        """)

    def _build_header(self):
        header = QLabel("Z-STUDIO COMMANDER v12.3")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #555;")
        self.main_layout.addWidget(header)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #222;")
        self.main_layout.addWidget(line)

    def _build_engine_controls(self):
        box = QGroupBox("SYSTEM ENGINE ORCHESTRATION")
        layout = QVBoxLayout(box)
        layout.setSpacing(12)

        self.btn_start = QPushButton("START SYSTEM ENGINE")
        self.btn_stop = QPushButton("STOP ACTIVE ENGINE")
        self.btn_restart = QPushButton("HARD REBOOT CORE")

        # Connection Logic
        self.btn_start.clicked.connect(lambda: self._emit("START_ENGINE"))
        self.btn_stop.clicked.connect(lambda: self._emit("STOP_ENGINE"))
        self.btn_restart.clicked.connect(lambda: self._emit("REBOOT_CORE"))

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_restart)
        self.main_layout.addWidget(box)

    def _build_memory_controls(self):
        box = QGroupBox("MEMORY & STATE MANAGEMENT")
        layout = QVBoxLayout(box)
        layout.setSpacing(12)

        self.btn_reset = QPushButton("FLUSH SYSTEM MEMORY")
        self.btn_emergency = QPushButton("EMERGENCY SHUTDOWN")
        self.btn_emergency.setObjectName("emergency_btn")

        self.btn_reset.clicked.connect(lambda: self._emit("RESET_MEMORY"))
        self.btn_emergency.clicked.connect(lambda: self._emit("EMERGENCY_SHUTDOWN"))

        layout.addWidget(self.btn_reset)
        layout.addWidget(self.btn_emergency)
        self.main_layout.addWidget(box)

    # =========================================================
    #  THE ENGINE ROOM: ANTI-SPAM + DIRECT ROUTING
    # =========================================================
    def _emit(self, event_name):
        """
        Processes events and ensures the UI doesn't fall into a loop.
        """
        # 1.  SPAM GUARD: Don't trigger START if already active
        if event_name == "START_ENGINE":
            if self._engine_locked:
                print(" [GUARD] Blocked repeated START signal.")
                return
            self._engine_locked = True
        
        # 2.  RESET GUARD: Unlock on stop/reboot
        if event_name in ["STOP_ENGINE", "EMERGENCY_SHUTDOWN", "REBOOT_CORE"]:
            self._engine_locked = False

        # 3. CONSTRUCT PAYLOAD (The critical metadata)
        # 3. CONSTRUCT PAYLOAD (The critical metadata)
        payload = {
            "source": "control_center",
            "event": event_name,
            "view_mode": "DASHBOARD_ACTIVE" if event_name == "START_ENGINE" else "MAIN_MENU",
            "status_text": f"SYSTEM: {event_name.replace('_', ' ')}"
        }

        # 4.  SIGNAL BROADCAST
        QTimer.singleShot(0, lambda: self.bus.emit_ui_event(event_name, payload))
        
        #  UI REFRESH (Ye screen ko turant jagayega)
        QApplication.processEvents()
        
        # 5. CONSOLE TRACE
        print(f" [COMMANDER] DISPATCHED: {event_name}")
        
        

    @Slot(bool)
    def update_engine_state(self, is_running):
        """External sync to update button states if core state changes"""
        self._engine_locked = is_running
        self.btn_start.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)


    def trigger_ai(self):
        print("STEP 1: UI TRIGGER")

        task = {
            "type": "USER_INPUT",
            "payload": {
               "input": "hello test"
            }
        }

        #  bridge call
        if hasattr(self, "bridge"):
          self.bridge.send_task(task)
        else:
            print(" bridge missing in control_center")