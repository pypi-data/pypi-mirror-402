from __future__ import annotations
from typing import Optional, Union
import sys
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from qtmui.material.styles import useTheme
class MapChangeTheme:
    def __init__(self, initialViewState: dict, *args, **kwargs): ...
    def _init_map(self): ...
    def _autorun_set_theme(self): ...