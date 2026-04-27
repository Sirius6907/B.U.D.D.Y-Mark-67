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
import math
import random
import psutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QLineEdit, QPushButton, QStackedWidget,
    QFrame, QSizePolicy, QScrollArea, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, QObject, QPropertyAnimation, 
    QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup,
    QPoint, QRect, QRectF, QPointF
)
from PyQt6.QtGui import (
    QPixmap, QFont, QColor, QIcon, QTextCursor, QPainter, QBrush, QPen,
    QPainterPath, QConicalGradient, QRadialGradient, QLinearGradient, QPolygon, QPolygonF
)
from config import get_api_key, get_os, update_config

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR   = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE   = CONFIG_DIR / "api_keys.json"

# Sci-Fi Colors - KINETIC SINGULARITY
COLOR_BG = "#080F18"        # Deep Space Neutral
COLOR_PRIMARY = "#00F2FF"   # Neon Cyan
COLOR_SECONDARY = "#FF59E3" # Neon Magenta
COLOR_ACCENT = "#99F7FF"    # Light Cyan highlight
COLOR_TEXT = "#E8EEFC"      # on_surface (no pure white)
COLOR_LOG_BG = "rgba(29, 38, 52, 0.4)" # surface_variant (#1D2634) at 40%
COLOR_BORDER = "rgba(66, 72, 83, 0.25)" # Ghost border
COLOR_PANEL_GRADIENT = "rgba(0, 242, 255, 0.1)"

try:
    from importlib.metadata import version
    __version__ = f"v{version('buddy-mk67')}"
except Exception:
    __version__ = "v1.0.0"

SYSTEM_NAME = "BUDDY MARK LXVII"
MODEL_BADGE = f"SINGULARITY // CORE"
BACKGROUND_IMAGE = str(BASE_DIR / "scifi_background_purple_1776829500844.png")

# ── Sci-Fi Core Widgets ───────────────────────────────────────────────────────

class BuddyCorePulse(QWidget):
    """The central pulsing power core of BUDDY."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)
        self.angle = 0
        self.pulse = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)
        
    def _animate(self):
        self.angle = (self.angle + 2) % 360
        self.pulse = (self.pulse + 0.05) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        
        pulse_scale = 1.0 + 0.1 * math.sin(self.pulse)
        
        # Outer Glowing Rings
        for i in range(3):
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self.angle * (1 if i%2==0 else -1) * (i+1) * 0.5)
            
            r = 100 + i*20
            pen = QPen(QColor(COLOR_PRIMARY))
            pen.setWidth(2)
            alpha = int(100 * (1 - i/3))
            c = QColor(COLOR_PRIMARY)
            c.setAlpha(alpha)
            pen.setColor(c)
            painter.setPen(pen)
            
            # Draw dashed arc
            painter.drawArc(int(-r), int(-r), int(r*2), int(r*2), 0, 120 * 16)
            painter.drawArc(int(-r), int(-r), int(r*2), int(r*2), 180 * 16, 120 * 16)
            painter.restore()
            
        # Inner Plasma Core
        grad = QRadialGradient(cx, cy, 60 * pulse_scale)
        c1 = QColor(COLOR_PRIMARY)
        c2 = QColor(COLOR_SECONDARY)
        c2.setAlpha(50)
        grad.setColorAt(0, c1)
        grad.setColorAt(0.7, c2)
        grad.setColorAt(1, QColor(0,0,0,0))
        
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 70 * pulse_scale, 70 * pulse_scale)
        
        # Core symbols
        painter.setPen(QPen(QColor(255, 255, 255, 180), 2))
        font = QFont("Consolas", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "LXVII")

# ── Custom Widgets ─────────────────────────────────────────────────────────────

class GlassPanel(QFrame):
    """Semi-transparent mecha panel with chamfered edges and glow border."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Glow effect
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(20)
        self.glow.setColor(QColor(COLOR_PRIMARY))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        
        c = 15 # Chamfer size
        
        # Create chamfered polygon
        poly = QPolygonF([
            QPointF(0, c),
            QPointF(c, 0),
            QPointF(w, 0),
            QPointF(w, h - c),
            QPointF(w - c, h),
            QPointF(0, h),
            QPointF(0, c)
        ])
        
        # Background
        bg_color = QColor(29, 38, 52, 100) # COLOR_LOG_BG equivalent
        painter.setBrush(QBrush(bg_color))
        
        # Border
        border_color = QColor(COLOR_PRIMARY)
        border_color.setAlpha(120)
        painter.setPen(QPen(border_color, 1))
        
        painter.drawPolygon(poly)
        
        # Sci-fi accents
        painter.setPen(QPen(QColor(COLOR_ACCENT), 2))
        painter.drawLine(0, c, c, 0) # Top-left accent
        painter.drawLine(int(w - c), h, w, int(h - c)) # Bottom-right accent
        
        # Corner bracket (top right)
        painter.drawLine(w - 15, 0, w, 0)
        painter.drawLine(w, 0, w, 15)
        
        # Corner bracket (bottom left)
        painter.drawLine(0, h - 15, 0, h)
        painter.drawLine(0, h, 15, h)

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

class NetworkTopology(QWidget):
    """Dynamic network graph with connecting nodes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(250, 150)
        self.nodes = []
        for _ in range(8):
            self.nodes.append({
                "pos": QPointF(random.randint(20, 230), random.randint(20, 130)),
                "vec": QPointF(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                "size": random.randint(2, 5)
            })
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)

    def _animate(self):
        for node in self.nodes:
            node["pos"] += node["vec"]
            if node["pos"].x() < 0 or node["pos"].x() > self.width(): node["vec"].setX(-node["vec"].x())
            if node["pos"].y() < 0 or node["pos"].y() > self.height(): node["vec"].setY(-node["vec"].y())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Connections
        painter.setPen(QPen(QColor(COLOR_PRIMARY + "44"), 1))
        for i, n1 in enumerate(self.nodes):
            for n2 in self.nodes[i+1:]:
                dist = (n1["pos"] - n2["pos"]).manhattanLength()
                if dist < 80:
                    painter.drawLine(n1["pos"], n2["pos"])
        
        # Nodes
        for node in self.nodes:
            painter.setBrush(QBrush(QColor(COLOR_SECONDARY if random.random() > 0.8 else COLOR_PRIMARY)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(node["pos"], node["size"], node["size"])

class SignalSpectrum(QWidget):
    """A scrolling signal spectrum visualizer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(250, 60)
        self.bars = [random.randint(5, 40) for _ in range(40)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)

    def _animate(self):
        self.bars.pop(0)
        self.bars.append(random.randint(5, 40))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        bar_w = w / len(self.bars)
        
        for i, val in enumerate(self.bars):
            # Gradient for each bar
            grad = QLinearGradient(0, h, 0, h - val)
            grad.setColorAt(0, QColor(COLOR_PRIMARY + "AA"))
            grad.setColorAt(1, QColor(COLOR_SECONDARY + "22"))
            
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(int(i * bar_w), h - val, int(bar_w - 1), val)

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

class ArcProgressWidget(QWidget):
    """Circular glowing arc progress bar."""
    def __init__(self, title, color_hex=COLOR_PRIMARY, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.title = title
        self.color = QColor(color_hex)
        self.value = 0
        self.target_value = 0
        
        self.anim = QTimer(self)
        self.anim.timeout.connect(self._animate)
        self.anim.start(30)

    def set_value(self, val):
        self.target_value = val

    def _animate(self):
        diff = self.target_value - self.value
        if abs(diff) > 0.1:
            self.value += diff * 0.1
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 10
        
        # 1. Outer Ring (Structure)
        painter.setPen(QPen(QColor(COLOR_PRIMARY).lighter(150), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius+4, radius+4)
        
        # 2. Background track with inner shadow
        painter.setPen(QPen(QColor(255, 255, 255, 10), 6))
        painter.drawArc(int(cx - radius), int(cy - radius), int(radius*2), int(radius*2), 0, 360 * 16)
        
        # 3. Progress Arc (Glow Layer)
        span_angle = -int(self.value * 3.6 * 16)
        start_angle = 90 * 16
        
        # Secondary glow arc
        glow_pen = QPen(self.color, 8)
        glow_color = QColor(self.color)
        glow_color.setAlpha(40)
        glow_pen.setColor(glow_color)
        painter.setPen(glow_pen)
        painter.drawArc(int(cx - radius), int(cy - radius), int(radius*2), int(radius*2), start_angle, span_angle)
        
        # Primary sharp arc
        main_pen = QPen(self.color, 4)
        main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(main_pen)
        painter.drawArc(int(cx - radius), int(cy - radius), int(radius*2), int(radius*2), start_angle, span_angle)
        
        # 4. Central Text / Value
        painter.setPen(QPen(QColor(255, 255, 255, 220)))
        font = QFont("Consolas", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.value)}%")
        
        dot_angle = math.radians(-90 - (self.value / 100.0) * 360)
        dot_x = cx + radius * math.cos(dot_angle)
        dot_y = cy + radius * math.sin(dot_angle)
        painter.drawEllipse(QPointF(dot_x, dot_y), 3, 3)

class RadarWidget(QWidget):
    """Rotating concentric circles with a targeting reticle."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        self.timer.start(50)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def _rotate(self):
        self.angle = (self.angle + 1.5) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx, cy = w/2, h/2
        painter.translate(cx, cy)
        
        # 1. Background atmospheric glow
        grad = QRadialGradient(0, 0, w/2)
        c_bg = QColor(COLOR_PRIMARY)
        c_bg.setAlpha(30)
        grad.setColorAt(0, c_bg)
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), w/2, h/2)

        # 2. Structural Rings
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i, r_factor in enumerate([0.95, 0.7, 0.45]):
            alpha = 150 - i*40
            painter.setPen(QPen(QColor(COLOR_PRIMARY + f"{alpha:02x}"), 1))
            radius = (w/2 - 10) * r_factor
            painter.drawEllipse(QPointF(0, 0), radius, radius)

        # 3. Sweeping Scanner (Tactical Sweep)
        painter.save()
        painter.rotate(-self.angle)
        sweep_grad = QConicalGradient(0, 0, 90)
        c_sweep = QColor(COLOR_PRIMARY)
        c_sweep.setAlpha(120)
        sweep_grad.setColorAt(0, c_sweep)
        sweep_grad.setColorAt(0.15, QColor(COLOR_PRIMARY + "00")) # Transparent
        painter.setBrush(QBrush(sweep_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPie(int(-w/2+5), int(-h/2+5), int(w-10), int(h-10), 0, 360 * 16)
        painter.restore()

        # 4. Crosshairs / Reticle
        painter.setPen(QPen(QColor(COLOR_ACCENT + "66"), 1))
        painter.drawLine(int(-w/2 + 10), 0, int(w/2 - 10), 0)
        painter.drawLine(0, int(-h/2 + 10), 0, int(h/2 - 10))
        
        # 5. Rotating Tech Bits
        painter.rotate(self.angle * 1.5)
        painter.setPen(QPen(QColor(COLOR_SECONDARY), 2))
        for a in range(0, 360, 60):
            painter.drawArc(int(-w/2+15), int(-h/2+15), int(w-30), int(h-30), a * 16, 15 * 16)

class DataWaveWidget(QWidget):
    """Sci-fi data stream visualizer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)
        
    def _animate(self):
        self.offset += 1
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        path = QPainterPath()
        path.moveTo(0, h/2)
        
        for x in range(w):
            y1 = math.sin((x + self.offset * 2) * 0.05) * (h/4)
            y2 = math.cos((x - self.offset) * 0.02) * (h/4)
            noise = (random.random() - 0.5) * 4
            path.lineTo(x, h/2 + y1 + y2 + noise)
            
        pen = QPen(QColor(COLOR_SECONDARY))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Glow
        pen.setColor(QColor(COLOR_SECONDARY).lighter(150))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)

# ── Style Sheet ────────────────────────────────────────────────────────────────

STYLE_SHEET = f"""
QMainWindow {{
    background-color: {COLOR_BG};
}}

QWidget {{
    color: {COLOR_TEXT};
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}

/* Glass Panel Effect */
GlassPanel {{
    background-color: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(0, 242, 255, 0.2);
    border-radius: 12px;
}}

/* Mission Terminal */
QTextEdit {{
    background-color: transparent;
    border: none;
    color: {COLOR_TEXT};
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 13px;
    selection-background-color: {COLOR_PRIMARY};
    selection-color: {COLOR_BG};
}}

QLineEdit {{
    background-color: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 242, 255, 0.1);
    border-radius: 8px;
    color: {COLOR_PRIMARY};
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 13px;
    padding: 12px 16px;
    letter-spacing: 1px;
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_PRIMARY};
    background-color: rgba(0, 242, 255, 0.05);
}}

/* Premium Buttons */
QPushButton {{
    background-color: rgba(0, 242, 255, 0.08);
    border: 1px solid rgba(0, 242, 255, 0.3);
    border-radius: 8px;
    color: {COLOR_PRIMARY};
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 10px 15px;
}}

QPushButton:hover {{
    background-color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_ACCENT};
    color: {COLOR_BG};
}}

QPushButton:pressed {{
    background-color: {COLOR_ACCENT};
    margin-top: 1px;
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
    font-family: 'JetBrains Mono', 'Consolas';
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
        
        self.mouse_pos = QPoint(0, 0)
        self.setMouseTracking(True)
        self.rotation_angle = 0
        self.core_timer = QTimer(self)
        self.core_timer.timeout.connect(self._rotate_core)
        self.core_timer.start(16) # ~60fps
        
        # Outstanding Design: Background Data Streams
        self.data_fragments = []
        for _ in range(20):
            self.data_fragments.append({
                "x": random.randint(0, 2000),
                "y": random.randint(0, 1200),
                "speed": random.uniform(0.5, 1.5),
                "text": "".join(random.choice("01") for _ in range(12)),
                "opacity": random.randint(15, 35)
            })

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
        self.vitals_panel.setFixedWidth(250)
        v_layout = QVBoxLayout(self.vitals_panel)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.setSpacing(15)

        # Arc Progress for Core Metrics
        self.cpu_arc = ArcProgressWidget("CPU LOAD", COLOR_PRIMARY)
        self.ram_arc = ArcProgressWidget("RAM USAGE", COLOR_SECONDARY)
        
        arc_layout = QHBoxLayout()
        arc_layout.addWidget(self.cpu_arc)
        arc_layout.addWidget(self.ram_arc)
        
        v_layout.addLayout(arc_layout)

        def add_metric(label_text, object_name):
            l = QLabel(label_text)
            l.setObjectName("MetricLabel")
            v_layout.addWidget(l)
            v = QLabel("--")
            v.setObjectName("MetricValue")
            v_layout.addWidget(v)
            return v

        self.disk_val = add_metric("DISK IO", "disk")
        self.net_val = add_metric("NET TRAFFIC", "net")
        
        # Add Network Topology
        v_layout.addWidget(NetworkTopology())

        # Add Data Wave at the bottom
        self.data_wave = DataWaveWidget()
        v_layout.addWidget(self.data_wave)
        
        # Add Signal Spectrum
        v_layout.addWidget(SignalSpectrum())
        
        v_layout.addStretch()
        
        sidebar_layout.addWidget(self.vitals_panel)

        # Avatar & State Panel
        self.state_panel = GlassPanel()
        self.state_panel.setFixedWidth(350)
        s_layout = QVBoxLayout(self.state_panel)
        s_layout.setContentsMargins(15, 15, 15, 15)
        
        s_layout.addWidget(QLabel("> NEURAL_PROCESS_FEED"))
        
        # Add a scrolling log or neural monitor here instead of a redundant core
        self.neural_log = QTextEdit()
        self.neural_log.setReadOnly(True)
        self.neural_log.setStyleSheet("background: transparent; border: none; font-size: 9px; color: #444;")
        self.neural_log.setFrameStyle(QFrame.Shape.NoFrame)
        s_layout.addWidget(self.neural_log)
        
        self.status_label = QLabel("SYSTEM ONLINE")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.addWidget(self.status_label)
        
        self.radar_small = RadarWidget()
        self.radar_small.setFixedSize(140, 140)
        s_layout.addWidget(self.radar_small, 0, Qt.AlignmentFlag.AlignCenter)
        
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
        self.send_btn.setFixedWidth(140)
        self.send_btn.clicked.connect(self._send_text)
        input_row.addWidget(self.send_btn)
        log_layout.addLayout(input_row)

        content_layout.addWidget(log_panel, 1)
        self.main_layout.addLayout(content_layout)

        # ── Timers ─────────────────────────────────────────────────────────────
        self.vitals_timer = QTimer()
        self.vitals_timer.timeout.connect(self._update_vitals)
        self.vitals_timer.start(1000)

        # Initialize telemetry tracking
        self.last_net = psutil.net_io_counters()
        self.last_disk = psutil.disk_io_counters()
        self.last_time = time.time()

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        # Neural Feed Timer
        self.neural_timer = QTimer()
        self.neural_timer.timeout.connect(self._update_neural_feed)
        self.neural_timer.start(2000)

        # Add Scanning Line
        self.scanner = ScanningLine(self)
        self.scanner.setGeometry(self.rect())

    def _update_clock(self):
        self.clock_label.setText(time.strftime("%H:%M:%S"))

    def _update_neural_feed(self):
        msgs = [
            "SYNCING NEURAL_WEIGHTS...",
            "HEURISTIC_ANALYSIS: OPTIMAL",
            "QUANTUM_STATE: COHERENT",
            "VECTOR_STORE: INDEXING...",
            "BUFFER_CLEANUP: SUCCESS",
            "LATENCY_CHECK: 14ms",
            "CORE_TEMP: 42.4°C",
            "UPLINK_STRENGTH: 98%"
        ]
        self.neural_log.append(f"<font color='#555'>> {random.choice(msgs)}</font>")
        if self.neural_log.document().blockCount() > 10:
            cursor = self.neural_log.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar() # Remove newline

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scanner'):
            self.scanner.setGeometry(self.rect())

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        self.update()
        super().mouseMoveEvent(event)

    def _rotate_core(self):
        self.rotation_angle = (self.rotation_angle + 1) % 360
        # Update Data Fragments
        h = self.height() if self.height() > 0 else 1080
        w = self.width() if self.width() > 0 else 1920
        for frag in self.data_fragments:
            frag["y"] += frag["speed"]
            if frag["y"] > h:
                frag["y"] = -20
                frag["x"] = random.randint(0, w)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx, cy = w/2, h/2
        
        # Parallax Calculation
        offset_x = (self.mouse_pos.x() - cx) / 80
        offset_y = (self.mouse_pos.y() - cy) / 80

        # 0. Background Data Streams (Outstanding Effect)
        painter.setFont(QFont("Consolas", 8))
        for frag in self.data_fragments:
            c = QColor(COLOR_PRIMARY)
            c.setAlpha(frag["opacity"])
            painter.setPen(c)
            painter.drawText(int(frag["x"]), int(frag["y"]), frag["text"])

        # 1. Background Pixmap (Base)
        if not self.bg_pixmap.isNull():
            painter.drawPixmap(self.rect(), self.bg_pixmap)
        
        # 2. Transparency Overlay
        painter.setBrush(QColor(8, 15, 24, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # 3. Dynamic Grid (Parallax Layer)
        grid_color = QColor(COLOR_PRIMARY)
        grid_color.setAlpha(10)
        painter.setPen(QPen(grid_color, 1))
        cell_size = 80
        start_x = int(-cell_size + (offset_x % cell_size))
        start_y = int(-cell_size + (offset_y % cell_size))
        for x in range(start_x, w + cell_size, cell_size):
            painter.drawLine(x, 0, x, h)
        for y in range(start_y, h + cell_size, cell_size):
            painter.drawLine(0, y, w, y)

        # 4. Central Rotating Core (The "Eye of Buddy") - SUBDUED BACKGROUND
        painter.save()
        painter.setOpacity(0.4) # Subdued for terminal readability
        painter.translate(cx + offset_x * 0.5, cy + offset_y * 0.5)
        
        # Outer Tech Rings
        for i, speed in enumerate([1.0, -0.7, 0.4]):
            painter.save()
            painter.rotate(self.rotation_angle * speed)
            c = QColor(COLOR_PRIMARY if i % 2 == 0 else COLOR_SECONDARY)
            c.setAlpha(40 - i*10) # Lower alpha
            painter.setPen(QPen(c, 2, Qt.PenStyle.DashLine))
            r = 150 + i*30
            painter.drawArc(int(-r), int(-r), int(r*2), int(r*2), 0, 240 * 16)
            painter.restore()
            
        # Inner Pulse
        pulse = abs(math.sin(self.rotation_angle * 0.05)) * 10
        grad = QRadialGradient(0, 0, 80 + pulse)
        grad.setColorAt(0, QColor(COLOR_PRIMARY + "66")) # Faded
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(0, 0), 80 + pulse, 80 + pulse)
        
        painter.restore()
        
        # 5. Vignette (Dark edges)
        vignette = QRadialGradient(cx, cy, math.hypot(cx, cy))
        vignette.setColorAt(0.5, QColor(0, 0, 0, 0))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 240))
        painter.setBrush(QBrush(vignette))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # 6. CRT Scanlines
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        for y in range(0, h, 4):
            painter.drawLine(0, y, w, y)

        # 7. Tactical HUD Corner Brackets (Outstanding Design)
        painter.setPen(QPen(QColor(COLOR_PRIMARY + "44"), 2))
        m, l = 40, 60
        # Top Left
        painter.drawLine(m, m, m+l, m); painter.drawLine(m, m, m, m+l)
        # Top Right
        painter.drawLine(w-m, m, w-m-l, m); painter.drawLine(w-m, m, w-m, m+l)
        # Bottom Left
        painter.drawLine(m, h-m, m+l, h-m); painter.drawLine(m, h-m, m, h-m-l)
        # Bottom Right
        painter.drawLine(w-m, h-m, w-m-l, h-m); painter.drawLine(w-m, h-m, w-m, h-m-l)

        # 8. Mute Indicator (SILENT_PROTOCOL) - MOVED TO TOP CENTER
        if hasattr(self, 'muted_state') and self.muted_state:
            painter.setPen(QPen(QColor(255, 50, 50, 200), 2))
            painter.setBrush(QColor(255, 50, 50, 40))
            # Positioned above the log panel, centered
            rect = QRect(int(w/2 - 100), 120, 200, 35)
            painter.drawRoundedRect(rect, 4, 4)
            
            font = painter.font()
            font.setBold(True)
            font.setPointSize(10)
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
            painter.setFont(font)
            painter.setPen(QColor(255, 80, 80))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "![ SILENT_PROTOCOL ]!")
            
        super().paintEvent(event)

    def _update_vitals(self):
        try:
            # Time delta
            now = time.time()
            dt = max(0.1, now - self.last_time)
            self.last_time = now

            # CPU & RAM
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.cpu_arc.set_value(cpu)
            self.ram_arc.set_value(ram)

            # Disk I/O
            disk = psutil.disk_io_counters()
            if disk and self.last_disk:
                read_bps = (disk.read_bytes - self.last_disk.read_bytes) / dt
                write_bps = (disk.write_bytes - self.last_disk.write_bytes) / dt
                total_disk_mbs = (read_bps + write_bps) / (1024 * 1024)
                self.disk_val.setText(f"{total_disk_mbs:.1f} MB/s")
                self.last_disk = disk

            # Network I/O
            net = psutil.net_io_counters()
            if net and self.last_net:
                sent_bps = (net.bytes_sent - self.last_net.bytes_sent) / dt
                recv_bps = (net.bytes_recv - self.last_net.bytes_recv) / dt
                total_net_kbs = (sent_bps + recv_bps) / 1024
                self.net_val.setText(f"{total_net_kbs:.1f} KB/s")
                self.last_net = net
        except Exception as e:
            # Fallback to random or just keep last value if psutil fails
            print(f"Telemetry error: {e}")

    def _send_text(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.write_log(f"<font color='{COLOR_ACCENT}'>[YOU]:</font> {text}")
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    def set_muted(self, muted: bool):
        self.muted_state = muted
        self.update()

    def write_log(self, text: str):
        timestamp = time.strftime("%H:%M:%S")
        if "[YOU]" in text:
            formatted = f"<span style='color: #666;'>[{timestamp}]</span> {text}"
        elif "BUDDY:" in text or "AI:" in text or "B.U.D.D.Y:" in text:
            msg = text.split(':', 1)[-1]
            formatted = f"<span style='color: #666;'>[{timestamp}]</span> <font color='{COLOR_PRIMARY}'><b>[BUDDY]:</b></font> <font color='#FFF'>{msg}</font>"
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
        self.write_log("SYS: Systems initialised. B.U.D.D.Y online.")
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

    def set_muted(self, muted: bool):
        self.muted = muted
        self.dashboard.set_muted(muted)

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
