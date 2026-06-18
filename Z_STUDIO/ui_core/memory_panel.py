"""
ROLE: 4/11 - MEMORY PANEL (RESOURCE VISUALIZER)
VERSION: 1.2.0 (FINAL HARDENED)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
-----------------------------------------------------------------------
FINAL POLISH: 
1. Added Data Fallback (None-Type safety) to prevent crashes.
2. Fixed explicit object naming for styling stability.
3. Unit Scaling for Cache (KB/MB/GB).
-----------------------------------------------------------------------
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QGridLayout
from PySide6.QtCore import Qt

class ZStudioMemoryPanel(QWidget):
    def __init__(self, parent_layout=None):
        super().__init__()
        
        #  Injection into Dashboard
        if parent_layout:
            parent_layout.addWidget(self)

        #  Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(20)

        #  STYLESHEET (Final Industrial Polish)
        self.setStyleSheet("""
            QLabel#SectionTitle { 
                color: #00FFCC; font-size: 16px; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 5px;
            }
            QLabel#ValueLabel { color: #EEE; font-size: 14px; font-family: 'Consolas'; }
            
            QProgressBar { 
                background-color: #1A1A1A; border: 1px solid #333; border-radius: 3px; 
                text-align: right; color: transparent; height: 15px;
            }
            QProgressBar#RAMBar::chunk { background-color: #00FFCC; }
            QProgressBar#GPUBar::chunk { background-color: #FFA500; }
        """)

        self._setup_ui()

    def _setup_ui(self):
        # --- SECTION 1: RAM ---
        self.layout.addWidget(self._create_header("SYSTEM RAM UTILIZATION"))
        self.ram_bar = QProgressBar()
        self.ram_bar.setObjectName("RAMBar")
        self.layout.addWidget(self.ram_bar)
        
        self.ram_stats = QLabel("USED: 0.0 GB / TOTAL: 0.0 GB")
        self.ram_stats.setObjectName("ValueLabel")
        self.layout.addWidget(self.ram_stats)

        # --- SECTION 2: GPU ---
        self.layout.addWidget(self._create_header("GPU VRAM UTILIZATION"))
        self.gpu_bar = QProgressBar()
        self.gpu_bar.setObjectName("GPUBar")
        self.layout.addWidget(self.gpu_bar)
        
        self.gpu_stats = QLabel("USED: 0.0 GB / TOTAL: 0.0 GB")
        self.gpu_stats.setObjectName("ValueLabel")
        self.layout.addWidget(self.gpu_stats)

        # --- SECTION 3: CACHE ---
        self.layout.addWidget(self._create_header("AI CONTEXT & CACHE"))
        grid = QGridLayout()
        self.cache_size = QLabel("0.00 MB")
        self.cache_size.setObjectName("ValueLabel")
        grid.addWidget(QLabel("Current Cache Load:"), 0, 0)
        grid.addWidget(self.cache_size, 0, 1)
        
        self.layout.addLayout(grid)
        self.layout.addStretch()

    def _create_header(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("SectionTitle")
        return lbl

    # ---  HARDENED METHODS (10/10 SAFETY) ---

    def reset_ui(self):
        """Clears all UI components to default state."""
        self.ram_bar.setValue(0)
        self.gpu_bar.setValue(0)
        self.ram_stats.setText("USED: 0.0 GB / TOTAL: 0.0 GB")
        self.gpu_stats.setText("USED: 0.0 GB / TOTAL: 0.0 GB")
        self.cache_size.setText("0.00 MB")

    def update_metrics(self, data):
        """
        Data Fallback added: If data is missing/None, UI shows 0 instead of crashing.
        """
        if not data: data = {} # Guard clause

        # RAM Safe Update
        ram_pct = int(data.get('ram_pct', 0))
        self.ram_bar.setValue(ram_pct)
        self.ram_stats.setText(f"USED: {data.get('ram_used', 0.0):.1f} GB / TOTAL: {data.get('ram_total', 0.0):.1f} GB")

        # GPU Safe Update
        gpu_pct = int(data.get('gpu_pct', 0))
        self.gpu_bar.setValue(gpu_pct)
        self.gpu_stats.setText(f"USED: {data.get('gpu_used', 0.0):.1f} GB / TOTAL: {data.get('gpu_total', 0.0):.1f} GB")

        # Cache Safe Scaling (KB -> MB -> GB)
        kb = data.get('cache_kb', 0)
        if kb > 1048576: # More than 1GB
            self.cache_size.setText(f"{kb/1048576:.2f} GB")
        elif kb > 1024:
            self.cache_size.setText(f"{kb/1024:.2f} MB")
        else:
            self.cache_size.setText(f"{kb:.2f} KB")