"""
ROLE: 5/11 - SYSTEM MONITOR (PERFORMANCE TELEMETRY)
VERSION: 1.5.0 (FINAL PRODUCTION HARDENED)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
-----------------------------------------------------------------------
FINAL POLISH: 
1. Restored & Hardened reset_monitor() for clean system restarts.
2. Semantic State Caching (Using status labels instead of raw hex).
3. Industrial-grade Style Overrides for high-speed UI sync.
-----------------------------------------------------------------------
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

class ZStudioSystemMonitor(QWidget):
    #  INDUSTRIAL PERFORMANCE THRESHOLDS
    CPU_CRITICAL = 85.0
    GPU_CRITICAL = 90.0
    LATENCY_WARNING = 200
    LATENCY_CRITICAL = 500

    #  COLOR SCHEME
    COLOR_NORMAL = "#00FFCC"
    COLOR_WARNING = "#FFA500"
    COLOR_CRITICAL = "#FF3333"

    def __init__(self, parent_layout=None):
        super().__init__()
        
        if parent_layout:
            parent_layout.addWidget(self)

        #  SEMANTIC STATE CACHING (v1.5 Upgrade)
        self._cpu_state = "NORMAL"
        self._gpu_state = "NORMAL"
        self._lat_state = "NORMAL"

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self.setStyleSheet("""
            QFrame#StatCard { 
                background-color: #151515; border: 1px solid #2A2A2A; 
                border-radius: 6px; padding: 15px;
            }
            QLabel#StatTitle { color: #888; font-size: 11px; text-transform: uppercase; font-weight: bold; }
            QLabel#StatValue { color: #00FFCC; font-size: 24px; font-family: 'Consolas', monospace; }
            QLabel#StatUnit { color: #555; font-size: 12px; margin-left: 5px; }
            QLabel#UptimeLbl { color: #444; font-size: 10px; margin-top: 10px; font-family: 'Consolas'; }
        """)

        self._setup_ui()

    def _setup_ui(self):
        self.cpu_val = self._add_stat_card("CPU UTILIZATION", "0", "%")
        self.gpu_val = self._add_stat_card("GPU UTILIZATION", "0", "%")
        self.lat_val = self._add_stat_card("ENGINE RESPONSE", "0", "ms")

        self.uptime_lbl = QLabel("CORE UPTIME: 00:00:00")
        self.uptime_lbl.setObjectName("UptimeLbl")
        
        self.layout.addStretch()
        self.layout.addWidget(self.uptime_lbl)

    def _add_stat_card(self, title, val, unit):
        frame = QFrame(); frame.setObjectName("StatCard")
        f_layout = QVBoxLayout(frame)
        t_lbl = QLabel(title); t_lbl.setObjectName("StatTitle")
        
        v_layout = QHBoxLayout()
        v_lbl = QLabel(val); v_lbl.setObjectName("StatValue")
        u_lbl = QLabel(unit); u_lbl.setObjectName("StatUnit")
        
        v_layout.addWidget(v_lbl); v_layout.addWidget(u_lbl); v_layout.addStretch()
        f_layout.addWidget(t_lbl); f_layout.addLayout(v_layout)
        self.layout.addWidget(frame)
        return v_lbl

    # ---  PRODUCTION HARDENED METHODS ---

    def reset_monitor(self):
        """Restores UI to factory state (Crucial for System Reboot)."""
        self.cpu_val.setText("0")
        self.gpu_val.setText("0")
        self.lat_val.setText("0")
        self.uptime_lbl.setText("CORE UPTIME: 00:00:00")
        
        # Reset colors and states
        for widget in [self.cpu_val, self.gpu_val, self.lat_val]:
            widget.setStyleSheet(f"color: {self.COLOR_NORMAL};")
        
        self._cpu_state = "NORMAL"
        self._gpu_state = "NORMAL"
        self._lat_state = "NORMAL"

    def _apply_semantic_style(self, widget, target_state, state_attr):
        """Optimized semantic rendering engine."""
        if getattr(self, state_attr) != target_state:
            color = self.COLOR_NORMAL
            if target_state == "CRITICAL": color = self.COLOR_CRITICAL
            elif target_state == "WARNING": color = self.COLOR_WARNING
            
            widget.setStyleSheet(f"color: {color};")
            setattr(self, state_attr, target_state)

    def update_telemetry(self, stats):
        """Hardened Live Telemetry Entry-Point."""
        if not stats: return

        # 1. CPU
        cpu = stats.get('cpu', 0.0)
        self.cpu_val.setText(f"{cpu:.1f}")
        cpu_s = "CRITICAL" if cpu > self.CPU_CRITICAL else "NORMAL"
        self._apply_semantic_style(self.cpu_val, cpu_s, "_cpu_state")

        # 2. GPU
        gpu = stats.get('gpu', 0.0)
        self.gpu_val.setText(f"{gpu:.1f}")
        gpu_s = "CRITICAL" if gpu > self.GPU_CRITICAL else "NORMAL"
        self._apply_semantic_style(self.gpu_val, gpu_s, "_gpu_state")

        # 3. Latency
        lat = stats.get('latency', 0)
        self.lat_val.setText(str(lat))
        lat_s = "NORMAL"
        if lat > self.LATENCY_CRITICAL: lat_s = "CRITICAL"
        elif lat > self.LATENCY_WARNING: lat_s = "WARNING"
        self._apply_semantic_style(self.lat_val, lat_s, "_lat_state")
        
        # 4. Uptime
        self.uptime_lbl.setText(f"CORE UPTIME: {stats.get('uptime', '00:00:00')}")