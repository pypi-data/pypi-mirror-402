from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer, QEasingCurve
from PySide6.QtGui import QPainter, QColor
import sys
import time
from qtmui.material.styles import useTheme
def alpha(color: QColor, alpha: float): ...
class LinearIndeterminate:
    def __init__(self, key: str, color: str): ...
    def paintEvent(self, event): ...