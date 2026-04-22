"""
ui.py — B.U.D.D.Y Native Sci-Fi Dashboard (PyQt6)
=================================================
Native replacement for the webview-based UI.
Maintains the same public API for BuddyLive integration.
"""

import os
import sys
import json
import time
import threading
import platform
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QLineEdit, QPushButton, QStackedWidget,
    QFrame, QSizePolicy, QScrollArea, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, QObject, QPropertyAnimation, 
    QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup,
    QPoint
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QIcon, QTextCursor, QPainter, QBrush, QPen
from config import get_api_key, get_os, update_config

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR   = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE   = CONFIG_DIR / "api_keys.json"

# Sci-Fi Colors - VIBRANT PURPLE EDITION
COLOR_BG = "#0A001F"        # Deep Midnight Purple
COLOR_PRIMARY = "#BC13FE"   # Vibrant Neon Purple
COLOR_SECONDARY = "#1E003D" # Deep Purple Shadow
COLOR_ACCENT = "#00F2FF"    # Cyan Highlight
COLOR_TEXT = "#E0D7FF"      # Soft Lavender Text
COLOR_LOG_BG = "rgba(10, 0, 31, 0.2)" # 80% Transparent (0.2 alpha)
COLOR_BORDER = "rgba(188, 19, 254, 0.4)" # Subtle purple border
COLOR_PANEL_GRADIENT = "rgba(188, 19, 254, 0.1)"

SYSTEM_NAME = "J.A.R.V.I.S"
MODEL_BADGE = "MK-37 // PROTOCOL SIRIUS"
BACKGROUND_IMAGE = r"C:\Users\opcha\Downloads\SIRIUS\Jarvis-MK37-main\scifi_background_purple_1776829500844.png" # Fixed path to use project dir if available

# ── Custom Widgets ─────────────────────────────────────────────────────────────

class GlassPanel(QFrame):
    """Semi-transparent panel with a glow border and 3D depth."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            GlassPanel {{
                background-color: {COLOR_LOG_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        
        # Add a subtle inner glow
        self.inner_border = QFrame(self)
        self.inner_border.setStyleSheet(f"""
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 11px;
        """)
        self.inner_border.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Glow effect
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(15)
        self.glow.setColor(QColor(COLOR_PRIMARY))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'inner_border'):
            self.inner_border.setGeometry(1, 1, self.width()-2, self.height()-2)

class PulseAvatar(QLabel):
    """Animated avatar that pulses with a 'breathing' effect."""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.opacity_effect = QGraphicsDropShadowEffect(self)
        self.opacity_effect.setBlurRadius(20)
        self.opacity_effect.setColor(QColor(COLOR_PRIMARY))
        self.opacity_effect.setOffset(0)
        self.setGraphicsEffect(self.opacity_effect)

        # Animation for pulsing glow
        self.anim = QPropertyAnimation(self.opacity_effect, b"blurRadius")
        self.anim.setDuration(2000)
        self.anim.setStartValue(10)
        self.anim.setEndValue(40)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.anim.setLoopCount(-1)
        self.anim.start()

class ScanningLine(QWidget):
    """A horizontal line that moves up and down to simulate a scan."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.line_y = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_pos)
        self.timer.start(30)
        self.direction = 1

    def _update_pos(self):
        if not self.parent(): return
        h = self.parent().height()
        self.line_y += 2 * self.direction
        if self.line_y >= h or self.line_y <= 0:
            self.direction *= -1
        self.update()

    def paintEvent(self, event):
        if not self.parent(): return
        painter = QPainter(self)
        gradient = QColor(COLOR_PRIMARY)
        gradient.setAlpha(100)
        painter.setPen(QPen(gradient, 2))
        painter.drawLine(0, self.line_y, self.width(), self.line_y)
        
        # Subtle glow trailing the line
        glow_height = 20
        for i in range(glow_height):
            alpha = int(80 * (1 - i/glow_height))
            c = QColor(COLOR_PRIMARY)
            c.setAlpha(alpha)
            painter.setPen(QPen(c, 1))
            painter.drawLine(0, self.line_y - (i * self.direction), self.width(), self.line_y - (i * self.direction))

class GlowButton(QPushButton):
    """Button that pulses and glows on hover."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Scale animation
        self._scale_anim = QPropertyAnimation(self, b"size")
        self._scale_anim.setDuration(100)
        
    def enterEvent(self, event):
        self.setGraphicsEffect(None)
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(25)
        glow.setColor(QColor(COLOR_PRIMARY))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        
        # Subtle lift effect
        self.setStyleSheet(self.styleSheet() + f"margin-top: -2px; margin-bottom: 2px; background-color: {COLOR_PRIMARY};")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setGraphicsEffect(None)
        self.setStyleSheet(self.styleSheet().replace(f"margin-top: -2px; margin-bottom: 2px; background-color: {COLOR_PRIMARY};", ""))
        super().leaveEvent(event)

# ── Style Sheet ────────────────────────────────────────────────────────────────

STYLE_SHEET = f"""
QMainWindow {{
    background-color: {COLOR_BG};
}}

QWidget {{
    color: {COLOR_TEXT};
    font-family: 'Segoe UI Semibold', 'Exo 2', sans-serif;
}}

QTextEdit {{
    background-color: transparent;
    border: none;
    color: {COLOR_TEXT};
    font-family: 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.4;
    selection-background-color: {COLOR_PRIMARY};
}}

QLineEdit {{
    background-color: rgba(0, 0, 0, 0.5);
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    color: {COLOR_ACCENT};
    font-family: 'Consolas';
    font-size: 14px;
    padding: 10px 20px;
    selection-background-color: {COLOR_PRIMARY};
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_PRIMARY};
    background-color: rgba(188, 19, 254, 0.1);
}}

QPushButton {{
    background-color: rgba(45, 0, 77, 0.6);
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    color: {COLOR_TEXT};
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 2px;
    padding: 8px 20px;
}}

QPushButton:hover {{
    background-color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_ACCENT};
    color: white;
}}

QLabel#StatusLabel {{
    color: {COLOR_ACCENT};
    font-weight: bold;
    font-size: 16px;
    text-transform: uppercase;
    letter-spacing: 4px;
    font-family: 'Segoe UI Black';
}}

QLabel#HeaderLabel {{
    color: {COLOR_PRIMARY};
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 10px;
    text-transform: uppercase;
}}

QLabel#MetricValue {{
    color: white;
    font-family: 'Consolas';
    font-size: 18px;
    font-weight: bold;
}}

QLabel#MetricLabel {{
    color: {COLOR_ACCENT};
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 4px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: 2px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""

# ── Signal Bridge ─────────────────────────────────────────────────────────────

class UISignals(QObject):
    log_signal = pyqtSignal(str)
    state_signal = pyqtSignal(str)
    setup_finished = pyqtSignal()
    approval_signal = pyqtSignal(str, object)  # (message, event_to_set)

# ── Setup Wizard ──────────────────────────────────────────────────────────────

class SetupWizard(QWidget):
    def __init__(self, signals: UISignals, parent=None):
        super().__init__(parent)
        self.signals = signals
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Center Panel
        self.panel = GlassPanel()
        self.panel.setFixedWidth(500)
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(40, 40, 40, 40)
        panel_layout.setSpacing(25)

        header = QLabel("SYSTEM INITIALIZATION")
        header.setObjectName("HeaderLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(f"font-size: 20px; letter-spacing: 5px; color: {COLOR_PRIMARY};")
        panel_layout.addWidget(header)

        desc = QLabel("ESTABLISHING NEURAL LINK... PROVIDE CREDENTIALS")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 10px; font-family: 'Consolas';")
        panel_layout.addWidget(desc)

        self.key_input = QTextEdit()
        self.key_input.setPlaceholderText("PASTE GEMINI API KEYS (ONE PER LINE)...")
        self.key_input.setFixedHeight(120)
        self.key_input.setStyleSheet(f"background: rgba(0,0,0,0.3); border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 10px;")
        panel_layout.addWidget(self.key_input)

        self.os_input = QLineEdit()
        self.os_input.setText(self._detect_os())
        self.os_input.setPlaceholderText("OS (WINDOWS/MAC/LINUX)")
        panel_layout.addWidget(self.os_input)

        self.tg_token_input = QLineEdit()
        self.tg_token_input.setPlaceholderText("TELEGRAM BOT TOKEN (OPTIONAL)")
        panel_layout.addWidget(self.tg_token_input)

        self.tg_username_input = QLineEdit()
        self.tg_username_input.setPlaceholderText("TELEGRAM USERNAME (OPTIONAL)")
        panel_layout.addWidget(self.tg_username_input)

        self.save_btn = GlowButton("INITIALIZE CORE")
        self.save_btn.clicked.connect(self.save_keys)
        panel_layout.addWidget(self.save_btn)

        self.main_layout.addWidget(self.panel, 0, Qt.AlignmentFlag.AlignCenter)

    def _detect_os(self) -> str:
        s = platform.system().lower()
        if s == "darwin": return "mac"
        if s == "windows": return "windows"
        return "linux"

    def save_keys(self):
        raw_text = self.key_input.toPlainText().strip()
        keys_list = [line.strip() for line in raw_text.splitlines() if line.strip()]
        gemini_key = ",".join(keys_list)
        os_system = self.os_input.text().strip().lower()
        tg_token = self.tg_token_input.text().strip()
        tg_username = self.tg_username_input.text().strip()

        if not gemini_key:
            return

        os.makedirs(CONFIG_DIR, exist_ok=True)
        update_config(
            gemini_api_key=gemini_key, 
            os_system=os_system,
            telegram_bot_token=tg_token,
            telegram_username=tg_username
        )
        
        self.signals.setup_finished.emit()

# ── Main Dashboard ────────────────────────────────────────────────────────────

class Dashboard(QWidget):
    def __init__(self, face_path, signals: UISignals, parent=None):
        super().__init__(parent)
        self.signals = signals
        self.on_text_command = None
        self.bg_pixmap = QPixmap(BACKGROUND_IMAGE)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # ── Header ─────────────────────────────────────────────────────────────
        self.header = QHBoxLayout()
        
        self.sys_title = QLabel(f"{SYSTEM_NAME} <font color='#888'>//</font> {MODEL_BADGE}")
        self.sys_title.setStyleSheet(f"color: {COLOR_PRIMARY}; font-weight: bold; letter-spacing: 2px; font-size: 16px;")
        self.header.addWidget(self.sys_title)
        
        self.header.addStretch()
        
        self.clock_label = QLabel("00:00:00")
        self.clock_label.setStyleSheet(f"color: {COLOR_TEXT}; font-family: 'Consolas'; font-size: 18px; letter-spacing: 2px;")
        self.header.addWidget(self.clock_label)
        
        self.header.addStretch()

        self.neural_status = QLabel("NEURAL_LINK: ACTIVE")
        self.neural_status.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        self.header.addWidget(self.neural_status)
        
        self.main_layout.addLayout(self.header)

        # ── Main Content Body ──────────────────────────────────────────────────
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left Sidebar: Vitals & Modules
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(15)
        
        # Vitals Panel
        self.vitals_panel = GlassPanel()
        self.vitals_panel.setFixedWidth(200)
        v_layout = QVBoxLayout(self.vitals_panel)
        v_layout.setContentsMargins(15, 15, 15, 15)
        v_layout.setSpacing(10)

        def add_metric(label_text, object_name):
            l = QLabel(label_text)
            l.setObjectName("MetricLabel")
            v_layout.addWidget(l)
            v = QLabel("--")
            v.setObjectName("MetricValue")
            v_layout.addWidget(v)
            return v

        self.cpu_val = add_metric("CPU LOAD", "cpu")
        self.ram_val = add_metric("MEMORY USAGE", "ram")
        self.disk_val = add_metric("DISK IO", "disk")
        self.net_val = add_metric("NET TRAFFIC", "net")
        v_layout.addStretch()
        
        sidebar_layout.addWidget(self.vitals_panel)

        # Avatar & State Panel
        self.state_panel = GlassPanel()
        self.state_panel.setFixedWidth(200)
        s_layout = QVBoxLayout(self.state_panel)
        s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar = PulseAvatar(face_path)
        self.avatar.setFixedSize(160, 160)
        s_layout.addWidget(self.avatar)
        
        self.status_label = QLabel("READY")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.addWidget(self.status_label)
        
        sidebar_layout.addWidget(self.state_panel)
        content_layout.addLayout(sidebar_layout)

        # Main Log Stream
        log_panel = GlassPanel()
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(20, 20, 20, 20)
        
        log_head = QHBoxLayout()
        log_head.addWidget(QLabel("> MISSION_TERMINAL_STREAM"))
        log_head.addStretch()
        self.quota_badge = QLabel("QUOTA: NOMINAL")
        self.quota_badge.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 9px; border: 1px solid {COLOR_ACCENT}; border-radius: 4px; padding: 2px 5px;")
        log_head.addWidget(self.quota_badge)
        log_layout.addLayout(log_head)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        log_layout.addWidget(self.log_area)
        
        # Input Bar
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 10, 0, 0)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("ENTER COMMAND OR NEURAL INPUT...")
        self.input_field.returnPressed.connect(self._send_text)
        input_row.addWidget(self.input_field)
        
        self.send_btn = GlowButton("TRANSMIT")
        self.send_btn.setFixedWidth(120)
        self.send_btn.clicked.connect(self._send_text)
        input_row.addWidget(self.send_btn)
        log_layout.addLayout(input_row)

        content_layout.addWidget(log_panel, 1)
        self.main_layout.addLayout(content_layout)

        # ── Timers ─────────────────────────────────────────────────────────────
        self.vitals_timer = QTimer()
        self.vitals_timer.timeout.connect(self._update_vitals)
        self.vitals_timer.start(1000)

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        # Add Scanning Line
        self.scanner = ScanningLine(self)
        self.scanner.setGeometry(self.rect())

    def _update_clock(self):
        self.clock_label.setText(time.strftime("%H:%M:%S"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scanner'):
            self.scanner.setGeometry(self.rect())

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.bg_pixmap.isNull():
            painter.drawPixmap(self.rect(), self.bg_pixmap)
        
        # 80% Transparency Overlay (51 alpha = 20% opacity = 80% transparent)
        painter.setBrush(QColor(10, 0, 31, 51))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # Draw Holographic Grid
        grid_color = QColor(COLOR_PRIMARY)
        grid_color.setAlpha(20)
        grid_pen = QPen(grid_color)
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        
        cell_size = 50
        for x in range(0, self.width(), cell_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), cell_size):
            painter.drawLine(0, y, self.width(), y)
            
        super().paintEvent(event)

    def _update_vitals(self):
        import random
        cpu = random.randint(2, 8)
        ram = random.randint(42, 45)
        self.cpu_val.setText(f"{cpu}%")
        self.ram_val.setText(f"{ram}%")
        self.disk_val.setText(f"{random.randint(0, 2)} MB/s")
        self.net_val.setText(f"{random.randint(10, 100)} KB/s")

    def _send_text(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.write_log(f"<font color='{COLOR_ACCENT}'>[YOU]:</font> {text}")
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    def write_log(self, text: str):
        timestamp = time.strftime("%H:%M:%S")
        if "[YOU]" in text:
            formatted = f"<span style='color: #666;'>[{timestamp}]</span> {text}"
        elif "BUDDY:" in text or "AI:" in text or "J.A.R.V.I.S:" in text:
            msg = text.split(':', 1)[-1]
            formatted = f"<span style='color: #666;'>[{timestamp}]</span> <font color='{COLOR_PRIMARY}'><b>[JARVIS]:</b></font> <font color='#FFF'>{msg}</font>"
        else:
            formatted = f"<span style='color: #666;'>[{timestamp}]</span> <font color='{COLOR_ACCENT}'>[SYS]:</font> <font color='#AAA'>{text}</font>"
            
        self.log_area.append(formatted)
        self.log_area.moveCursor(QTextCursor.MoveOperation.End)

    def set_state(self, state: str):
        self.status_label.setText(state)

    def update_runtime_status(self, status):
        # Update sidebar/header with runtime status
        pass

# ── Root Shim ────────────────────────────────────────────────────────────────

class _PyQtRoot:
    def __init__(self, app):
        self.app = app

    def mainloop(self):
        sys.exit(self.app.exec())

# ── Main UI class ──────────────────────────────────────────────────────────────

class BuddyUI:
    def __init__(self, face_path, size=None):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLE_SHEET)
        
        self.signals = UISignals()
        self.window = QMainWindow()
        self.window.setWindowTitle(f"{SYSTEM_NAME} — {MODEL_BADGE}")
        self.window.resize(1100, 750)

        self.stack = QStackedWidget()
        self.window.setCentralWidget(self.stack)

        self.setup_wizard = SetupWizard(self.signals)
        self.dashboard = Dashboard(face_path, self.signals)
        
        self.stack.addWidget(self.setup_wizard)
        self.stack.addWidget(self.dashboard)

        self.speaking = False
        self.muted = False
        self._on_text_command_callback = None
        self._api_key_ready = self._api_keys_exist()

        if self._api_key_ready:
            self.stack.setCurrentWidget(self.dashboard)
        else:
            self.stack.setCurrentWidget(self.setup_wizard)

        # Connect signals for thread-safe updates
        self.signals.log_signal.connect(self.dashboard.write_log)
        self.signals.state_signal.connect(self.dashboard.set_state)
        self.signals.setup_finished.connect(self._on_setup_finished)
        self.signals.approval_signal.connect(self._on_request_approval)

        self.window.show()
        self.root = _PyQtRoot(self.app)

    def _on_request_approval(self, message, result_dict):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.window, "Security Clearance Required",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        result_dict['approved'] = (reply == QMessageBox.StandardButton.Yes)
        result_dict['event'].set()

    def request_approval(self, message: str) -> bool:
        """
        Public API for the runtime to request user approval.
        Thread-safe.
        """
        event = threading.Event()
        result = {'approved': False, 'event': event}
        self.signals.approval_signal.emit(message, result)
        event.wait()
        return result['approved']

    @property
    def on_text_command(self):
        return self._on_text_command_callback

    @on_text_command.setter
    def on_text_command(self, value):
        self._on_text_command_callback = value
        self.dashboard.on_text_command = value

    def _on_setup_finished(self):
        self._api_key_ready = True
        self.stack.setCurrentWidget(self.dashboard)
        self.write_log("SYS: Systems initialised. J.A.R.V.I.S online.")
        self.set_state("LISTENING")

    def _api_keys_exist(self) -> bool:
        try:
            return bool(get_api_key(required=False)) and bool(get_os())
        except Exception:
            return False

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_state(self, state: str):
        self.signals.state_signal.emit(state)
        
        # Logical state tracking
        if state == "MUTED":
            self.speaking = False
        elif state == "SPEAKING":
            self.speaking = True
        elif state == "THINKING":
            self.speaking = False
        elif state == "LISTENING":
            self.speaking = False
        elif state == "PROCESSING":
            self.speaking = False
        else:
            self.speaking = False

    def write_log(self, text: str):
        tl = text.lower()
        if tl.startswith("you:"):
            self.set_state("PROCESSING")
        elif tl.startswith("buddy:") or tl.startswith("ai:"):
            self.set_state("SPEAKING")
        
        self.signals.log_signal.emit(text)

    def update_runtime_status(self, status):
        self.dashboard.update_runtime_status(status)

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if not self.muted:
            self.set_state("LISTENING")

    def wait_for_api_key(self):
        while not self._api_key_ready:
            time.sleep(0.5)

if __name__ == "__main__":
    ui = BuddyUI("face.png")
    ui.root.mainloop()
