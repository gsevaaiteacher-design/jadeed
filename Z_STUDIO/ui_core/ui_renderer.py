"""
ROLE: 10/11 - UI RENDERER (GRAND VISUAL ORCHESTRATOR)
VERSION: 1.3.0 (FULL WIRING RESTORED + STATE ROUTER FIX)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
"""

from PySide6.QtCore import QObject, Signal, Slot, Qt


class ZStudioUIRenderer(QObject):

    # =========================
    # PROXY SIGNALS (UI BRIDGE LAYER)
    # =========================
    request_log_update = Signal(str, str)
    request_stream_update = Signal(str)
    request_stats_update = Signal(dict)
    request_state_sync = Signal(dict)

    def __init__(self, dashboard_instance):
        super().__init__()

        self.dashboard = dashboard_instance

        self.console = None
        self.monitor = None

        #  STATE MEMORY (IMPORTANT FIX)
        self._last_view_mode = None
        self._last_state = {}

        self._resolve_components()
        self._connect_internal_proxies()

        #  NEW: FULL UI WIRING CONNECTOR
        self._bind_dashboard_signals()

    # =========================
    #  NEW: DASHBOARD SIGNAL WIRING FIX
    # =========================
    def _bind_dashboard_signals(self):
        """
        CRITICAL FIX:
        LiveBridge  Renderer connection guarantee
        """
        try:
            if hasattr(self.dashboard, "live_bridge"):
                bridge = self.dashboard.live_bridge

                # HARD WIRING (MISSING LINK FIXED)
                bridge.state_updated.connect(self.sync_ui_state, Qt.QueuedConnection)
                bridge.log_received.connect(self.render_log, Qt.QueuedConnection)
                bridge.stream_chunk.connect(self.render_stream, Qt.QueuedConnection)
                bridge.monitor_stats.connect(self.update_system_stats, Qt.QueuedConnection)

                print(" [UI_RENDERER] LIVE BRIDGE FULLY CONNECTED")

        except Exception as e:
            print(f" [UI_RENDERER] WIRING FAILED: {e}")

    # =========================
    # COMPONENT RESOLVER
    # =========================
    def _resolve_components(self):

        self.console = (
            getattr(self.dashboard, "execution_console", None)
            or getattr(self.dashboard, "console", None)
            or self._search_child("ZStudioExecutionConsole")
        )

        self.monitor = (
            getattr(self.dashboard, "system_monitor", None)
            or self._search_child("SystemMonitor")
        )

    # =========================
    # SAFE CHILD SEARCH
    # =========================
    def _search_child(self, class_name):

        try:
            for child in self.dashboard.findChildren(QObject):
                if child.__class__.__name__ == class_name:
                    return child
        except Exception:
            pass

        return None

    # =========================
    # INTERNAL PROXY WIRING
    # =========================
    def _connect_internal_proxies(self):

        if self.console:

            if hasattr(self.console, "append_log"):
                self.request_log_update.connect(
                    self.console.append_log,
                    Qt.QueuedConnection
                )

            if hasattr(self.console, "append_ai_response"):
                self.request_stream_update.connect(
                    self.console.append_ai_response,
                    Qt.QueuedConnection
                )

        if self.monitor and hasattr(self.monitor, "refresh_stats"):
            self.request_stats_update.connect(
                self.monitor.refresh_stats,
                Qt.QueuedConnection
            )

    # =========================
    # LOG PIPE
    # =========================
    @Slot(str, str)
    def render_log(self, message, level):
        self.request_log_update.emit(message, level)

    # =========================
    # STREAM PIPE
    # =========================
    @Slot(str)
    def render_stream(self, chunk):
        self.request_stream_update.emit(chunk)

    # =========================
    # STATS PIPE
    # =========================
    @Slot(dict)
    def update_system_stats(self, stats):
        self.request_stats_update.emit(stats)

    # =========================
    #  FIXED: SMART UI STATE ENGINE
    # =========================
    @Slot(dict)
    def sync_ui_state(self, state):

        if not isinstance(state, dict):
            return

        view_mode = state.get("view_mode")

        # =========================
        #  CHANGE DETECTION FIX
        # =========================
        if state == self._last_state:
            return
        self._last_state = state

        # =========================
        #  FULL VIEW ROUTER (CRITICAL FIX)
        # =========================
        VIEW_MAP = {
            "DASHBOARD_ACTIVE": 0,
            "CONTROL_CENTER": 0,
            "MODEL_PANEL": 1,
            "MEMORY_PANEL": 2,
            "SETTINGS": 3,
            "EXECUTION": 4,
            "LOGS": 5
        }

        index = VIEW_MAP.get(view_mode)

        if index is not None and hasattr(self.dashboard, "tabs"):
            if self._last_view_mode != view_mode:
                self.dashboard.tabs.setCurrentIndex(index)
                self._last_view_mode = view_mode
                print(f" [RENDERER] VIEW SWITCH  {view_mode}")

        # =========================
        # STATUS LABEL
        # =========================
        status_label = getattr(self.dashboard, "status", None)
        if status_label:
            text = state.get("status_text") or state.get("status") or "IDLE"
            status_label.setText(text)

            color = "#00FFCC" if view_mode == "DASHBOARD_ACTIVE" else "#FFA500"
            status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # =========================
        # STATUS BAR FIX
        # =========================
        status_bar = getattr(self.dashboard, "status_bar", None)
        if status_bar:
            try:
                connected = state.get("engine") in ["ONLINE", "BOOTING"]
                color = "#00FFCC" if connected else "#FF3333"

                if hasattr(status_bar, "set_status"):
                    status_bar.set_status(text, color)

            except Exception:
                pass

        # =========================
        # FINAL BROADCAST
        # =========================
        self.request_state_sync.emit(state)

    # =========================
    # FORCE REFRESH
    # =========================
    def force_refresh(self):
        try:
            if hasattr(self.dashboard, "update"):
                self.dashboard.update()
        except Exception:
            pass