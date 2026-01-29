from __future__ import annotations
from typing import Optional, Union
import sys
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from .map_change_theme import MapChangeTheme
from .map_widget import MapWindow
class Map:
    def __init__(self, initialViewState: dict, *args, **kwargs): ...