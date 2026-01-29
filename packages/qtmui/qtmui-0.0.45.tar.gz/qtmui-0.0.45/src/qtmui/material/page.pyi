import threading
import time
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QFrame
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QPoint, QRect, Signal, QTimer
from .view import View
from qtmui.hooks import useState
class Page:
    def __init__(self, *args, **kwargs): ...
    def _wait_for_3s(self): ...
    def add_widget(self, element: QWidget): ...