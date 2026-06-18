"""
ROLE: 7/11 - SETTINGS PANEL (SYSTEM CONFIG INTERFACE)
VERSION: 1.0.1 (PREMIUM UI WIRED EDITION)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QCheckBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt

from event_bus_ui import get_event_bus


class ZStudioSettingsPanel(QWidget):

    def __init__(self, parent_layout=None):
        super().__init__()

        if parent_layout:
            parent_layout.addWidget(self)

        # =========================
        # EVENT BUS (UI  CORE LINK)
        # =========================
        self.bus = get_event_bus()

        # internal cache (UI ONLY)
        self._last_packet = None

        self._setup_ui()
        self._apply_style()

    # =========================
    # STYLE (PREMIUM UI FEEL)
    # =========================
    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0B0B0B;
                color: #E6E6E6;
                font-family: Segoe UI;
            }

            QLabel {
                color: #888;
                font-size: 11px;
            }

            QLineEdit {
                background: #151515;
                border: 1px solid #2A2A2A;
                padding: 10px;
                color: #00FFCC;
                border-radius: 6px;
            }

            QLineEdit:focus {
                border: 1px solid #00FFCC;
            }

            QCheckBox {
                color: #BBB;
                spacing: 8px;
            }

            QPushButton#ApplyBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00FFCC, stop:1 #009977);
                color: #000;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
            }

            QPushButton#ApplyBtn:hover {
                background: #00DDAA;
            }
        """)

    # =========================
    # UI BUILD
    # =========================
    def _setup_ui(self):

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(25, 25, 25, 25)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.form = QFormLayout(container)
        self.form.setSpacing(15)

        # -------------------------
        # CORE SECTION
        # -------------------------
        self._header("CORE ACCESS")

        self.api_key = QLineEdit()
        self.api_key.setPlaceholderText("API KEY (optional)")
        self.form.addRow("API KEY", self.api_key)

        self.db_path = QLineEdit()
        self.db_path.setPlaceholderText("database/main.db")
        self.form.addRow("DATABASE", self.db_path)

        # -------------------------
        # RUNTIME SECTION
        # -------------------------
        self._header("RUNTIME ENGINE")

        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("ai_models/")
        self.form.addRow("MODEL DIR", self.model_path)

        self.auto_start = QCheckBox("Auto Start Engine")
        self.form.addRow("", self.auto_start)

        # -------------------------
        # PERFORMANCE
        # -------------------------
        self._header("SYSTEM MODE")

        self.gpu = QCheckBox("GPU Acceleration")
        self.gpu.setChecked(True)
        self.form.addRow("", self.gpu)

        self.debug = QCheckBox("Verbose Debug Logs")
        self.form.addRow("", self.debug)

        scroll.setWidget(container)
        self.layout.addWidget(scroll)

        # APPLY BUTTON
        self.btn = QPushButton("SYNC SYSTEM CONFIG")
        self.btn.setObjectName("ApplyBtn")
        self.btn.clicked.connect(self._apply)
        self.layout.addWidget(self.btn)

    # =========================
    # HEADER
    # =========================
    def _header(self, text):
        label = QLabel(text)
        label.setStyleSheet("color:#00FFCC; font-weight:bold; margin-top:12px;")
        self.form.addRow(label)

    # =========================
    # APPLY (ONLY UI  EVENT BUS)
    # =========================
    def _apply(self):

        packet = {
            "api_key": self.api_key.text().strip(),
            "db_path": self.db_path.text().strip(),
            "model_path": self.model_path.text().strip(),
            "auto_start": self.auto_start.isChecked(),
            "gpu": self.gpu.isChecked(),
            "debug": self.debug.isChecked()
        }

        # validation (UI ONLY)
        if not packet["db_path"] or not packet["model_path"]:
            print("[UI WARNING] Missing critical config paths")
            return

        self._last_packet = packet

        #  REAL WIRING POINT (IMPORTANT FIX)
        self.bus.emit_ui_event("SETTINGS_UPDATE", packet)