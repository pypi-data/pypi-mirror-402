import sys
from typing import Any, Optional
from qtmui.material.styles import useTheme
from .use_media_query import useMediaQuery
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from qtmui.hooks import useState, State
def get_screen_size(): ...
def ___useResponsive(size: int, query: str, start: Optional[Any], end: Optional[Any]): ...
def useResponsive(query: str, start: Optional[Any], end: Optional[Any]): ...