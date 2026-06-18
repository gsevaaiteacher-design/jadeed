"""
ROLE: 3/11 - MODEL PANEL (SELECTION & LOADING UI)
VERSION: 1.1.0 (PRO-SYNC)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
-----------------------------------------------------------------------
FIXES: Added Selection Guards, Dynamic Model Loading, and Live Bridge Sync.
STRICT RESPONSIBILITY: Model display and Load/Unload triggers only.
-----------------------------------------------------------------------
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QLabel, QProgressBar)
from PySide6.QtCore import Qt
from event_bus_ui import get_event_bus

class ZStudioModelPanel(QWidget):
    def __init__(self, parent_layout=None):
        super().__init__()
        
        #  Injection & Bus Setup
        if parent_layout:
            parent_layout.addWidget(self)
        
        #  FIX 4: Secure Singleton Bus Access
        self.bus = get_event_bus()
        
        #  Layout & Styling
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        self._apply_styles()

        #  UI COMPONENTS
        self._setup_ui()

    def _apply_styles(self):
        self.setStyleSheet("""
            QListWidget { background-color: #151515; border: 1px solid #2A2A2A; color: #EEE; border-radius: 5px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #222; }
            QListWidget::item:selected { background-color: #2A2A2A; color: #00FFCC; }
            #LoadBtn { background-color: #004D40; color: #00FFCC; border: 1px solid #00FFCC; padding: 10px; font-weight: bold; }
            #UnloadBtn { background-color: #331111; color: #FF3333; border: 1px solid #FF3333; padding: 10px; font-weight: bold; }
            QProgressBar { background-color: #1A1A1A; border: 1px solid #333; height: 10px; text-align: center; color: transparent; }
            QProgressBar::chunk { background-color: #00FFCC; }
        """)

    def _setup_ui(self):
        self.layout.addWidget(QLabel("AVAILABLE AI MODELS"))

        #  FIX 2: Dynamic List (Initial placeholder, will be cleared by set_models)
        self.model_list = QListWidget()
        self.layout.addWidget(self.model_list)

        self.status_label = QLabel("STATUS: IDLE")
        self.layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("LOAD SELECTED MODEL")
        self.btn_load.setObjectName("LoadBtn")
        self.btn_load.clicked.connect(self._on_load_clicked)
        
        self.btn_unload = QPushButton("UNLOAD MODEL")
        self.btn_unload.setObjectName("UnloadBtn")
        self.btn_unload.clicked.connect(self._on_unload_clicked)

        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_unload)
        self.layout.addLayout(btn_layout)

    # ---  FIXES & REFINEMENTS ---

    def _on_load_clicked(self):
        selected = self.model_list.currentItem()
        #  FIX 1: Null Safety Guard
        if not selected:
            self.status_label.setText("STATUS: ERROR - NO MODEL SELECTED")
            self.status_label.setStyleSheet("color: #FF3333;")
            return
        
        model_id = selected.text()
        self.bus.emit_model_request("LOAD", model_id)

    def _on_unload_clicked(self):
        selected = self.model_list.currentItem()
        if not selected:
            self.status_label.setText("STATUS: ERROR - SELECT MODEL TO UNLOAD")
            return
        
        self.bus.emit_model_request("UNLOAD", selected.text())

    #  FIX 2: Dynamic Population (Called by live_bridge/manager)
    def set_models(self, models_list):
        self.model_list.clear()
        self.model_list.addItems(models_list)

    #  FIX 3: Single Source of Truth (Live Bridge Hook)
    def sync_state(self, state_dict):
        """
        Updates UI based on backend state broadcast.
        state_dict: {'status': str, 'progress': int, 'is_loading': bool}
        """
        status = state_dict.get("status", "IDLE")
        progress = state_dict.get("progress", 0)
        
        self.status_label.setText(f"STATUS: {status}")
        self.status_label.setStyleSheet("color: #00FFCC;" if "LOADED" in status else "color: #EEE;")
        
        if state_dict.get("is_loading", False):
            self.progress_bar.show()
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.hide()