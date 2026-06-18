"""
ROLE: 6/11 - EXECUTION CONSOLE (CHAT, LOGS & ACTIONS)
VERSION: 2.1.0 (REAL AI ROUTING + PREMIUM CHATGPT-STYLE UI ENGINE)
PROJECT: Z-STUDIO | OWNER: ZYNQUAR ATELIER
"""

import html
import time
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton,
    QSplitter, QFrame, QLabel
)

from PySide6.QtCore import Qt, QDateTime, Signal, Slot, QTimer
from PySide6.QtGui import QTextCursor

from event_bus_ui import get_event_bus


# =========================
# LOG WIDGET
# =========================
class LogWidget(QTextEdit):

    def __init__(self, max_lines=500):
        super().__init__()

        self.max_lines = max_lines
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)

        self.setStyleSheet("""
            background-color: #0A0A0A;
            color: #AAA;
            font-family: Consolas;
            font-size: 11px;
            border: 1px solid #222;
        """)

    def add_log_batch(self, entries):

        doc = self.document()

        while doc.blockCount() > self.max_lines:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

        fragments = []

        for msg, level, ts in entries:

            safe_msg = html.escape(str(msg))

            color = {
                "INFO": "#00FFCC",
                "WARN": "#FFA500",
                "ERROR": "#FF3333"
            }.get(level, "#00FFCC")

            fragments.append(
                f"<div>"
                f"<span style='color:#444;'>[{ts}]</span> "
                f"<b style='color:{color};'>[{level}]</b> "
                f"{safe_msg}"
                f"</div>"
            )

        self.moveCursor(QTextCursor.End)
        self.insertHtml("".join(fragments))
        self.ensureCursorVisible()


# =========================
# CHAT MODULE
# =========================
class ChatWidget(QWidget):

    def __init__(self, bus):
        super().__init__()

        self.bus = bus
        self.history = []

        self.layout = QVBoxLayout(self)

        self.thinking_label = QLabel("")
        self.thinking_label.setStyleSheet(
            "color:#888; font-style:italic;"
        )

        self.display = QTextEdit()
        self.display.setReadOnly(True)

        self.display.setStyleSheet("""
            background-color: #111;
            border: 1px solid #222;
            color: #EEE;
        """)

        self.input_field = QLineEdit()

        self.input_field.setPlaceholderText(
            "Ask Z-STUDIO anything..."
        )

        self.input_field.returnPressed.connect(
            self._submit
        )

        self.input_field.setStyleSheet("""
            padding: 12px;
            background: #181818;
            color: #00FFCC;
            border: 1px solid #333;
        """)

        self.layout.addWidget(self.thinking_label)
        self.layout.addWidget(self.display)
        self.layout.addWidget(self.input_field)

        self._cooldown = False

    # =========================
    # USER INPUT
    # =========================
    def _submit(self):

        text = self.input_field.text().strip()

        if not text or self._cooldown:
            return

        self._cooldown = True

        QTimer.singleShot(
            400,
            lambda: setattr(self, "_cooldown", False)
        )

        self.display.append(
            f"<b style='color:#00FFCC;'>You:</b> "
            f"{html.escape(text)}"
        )

        self.history.append(("user", text))

        self.thinking_label.setText(
            "Z-STUDIO is thinking..."
        )

        self.bus.emit_ui_event(
            "CHAT_SEND",
            {"message": text}
        )

        self.input_field.clear()

    # =========================
    # AI RESPONSE
    # =========================
    def add_ai_response(self, text):

        self.thinking_label.setText("")

        self.history.append(("ai", text))

        self.display.append(
            f"<b style='color:#FFA500;'>Z-STUDIO:</b> "
            f"{html.escape(text)}"
        )


# =========================
# EXECUTION CONSOLE CORE
# =========================
class ZStudioExecutionConsole(QWidget):

    log_signal = Signal(str, str)
    ai_signal = Signal(str)

    def __init__(self, parent_layout=None):
        super().__init__()

        if parent_layout:
            parent_layout.addWidget(self)

        self.bus = get_event_bus()

        #  REAL AI BRIDGE
        self.runtime_bridge = None

        self._log_queue = deque(maxlen=1000)

        self._batch_timer = QTimer()
        self._batch_timer.timeout.connect(
            self._flush_logs
        )
        self._batch_timer.start(100)

        self.chat_module = ChatWidget(self.bus)

        self.log_module = LogWidget(
            max_lines=500
        )

        self._setup_ui()

        # =========================
        # SIGNALS
        # =========================
        self.log_signal.connect(
            self._queue_log,
            Qt.QueuedConnection
        )

        self.ai_signal.connect(
            self._route_ai_response,
            Qt.QueuedConnection
        )

        # =========================
        # EVENT BUS
        # =========================
        self.bus.ui_event_triggered.connect(
            self._handle_bus_event
        )

    # =========================
    # UI
    # =========================
    def _setup_ui(self):

        self.splitter = QSplitter(Qt.Vertical)

        self.action_bar = QFrame()

        self.action_bar.setFixedHeight(45)

        self.action_bar.setStyleSheet("""
            background:#121212;
            border-top:1px solid #222;
        """)

        layout = QHBoxLayout(self.action_bar)

        btn_clear = QPushButton("CLEAR")

        btn_clear.clicked.connect(
            self._clear_ui
        )

        layout.addWidget(btn_clear)
        layout.addStretch()

        self.splitter.addWidget(self.chat_module)
        self.splitter.addWidget(self.log_module)

        main = QVBoxLayout(self)

        main.addWidget(self.splitter)
        main.addWidget(self.action_bar)

    # =========================
    # REAL AI ROUTER
    # =========================
    def _handle_bus_event(self, event, payload):

        if event != "CHAT_SEND":
            return

        try:

            msg = payload.get(
                "message",
                ""
            ).strip()

            if not msg:
                return

            # =====================
            # LOG INPUT
            # =====================
            self.append_log(
                f"USER_INPUT: {msg}",
                "INFO"
            )

            response = None

            # =====================
            # REAL ENGINE CALL
            # =====================
            if self.runtime_bridge:

                if hasattr(
                    self.runtime_bridge,
                    "generate"
                ):
                    response = self.runtime_bridge.generate(msg)

                elif hasattr(
                    self.runtime_bridge,
                    "chat"
                ):
                    response = self.runtime_bridge.chat(msg)

                elif hasattr(
                    self.runtime_bridge,
                    "ask"
                ):
                    response = self.runtime_bridge.ask(msg)

            # =====================
            # FAILSAFE
            # =====================
            if not response:

                response = (
                    "[AI_ENGINE_OFFLINE] "
                    "No inference backend connected."
                )

            # =====================
            # SEND TO UI
            # =====================
            self.ai_signal.emit(
                str(response)
            )

            self.append_log(
                "AI_RESPONSE_OK",
                "INFO"
            )

        except Exception as e:

            error_msg = (
                f"AI_ROUTE_FAIL: {str(e)}"
            )

            self.ai_signal.emit(error_msg)

            self.append_log(
                error_msg,
                "ERROR"
            )

    # =========================
    # LOG PIPE
    # =========================
    def _queue_log(self, msg, level):

        ts = QDateTime.currentDateTime().toString(
            "hh:mm:ss"
        )

        self._log_queue.append(
            (msg, level, ts)
        )

    def _flush_logs(self):

        if self._log_queue:

            batch = list(self._log_queue)

            self._log_queue.clear()

            self.log_module.add_log_batch(
                batch
            )

    # =========================
    # AI ROUTE
    # =========================
    def _route_ai_response(self, text):

        self.chat_module.add_ai_response(
            text
        )

    # =========================
    # CLEAR UI
    # =========================
    def _clear_ui(self):

        self.chat_module.display.clear()
        self.log_module.clear()

    # =========================
    # EXTERNAL LOG API
    # =========================
    @Slot(str, str)
    def append_log(
        self,
        msg,
        level="INFO"
    ):
        self._queue_log(msg, level)