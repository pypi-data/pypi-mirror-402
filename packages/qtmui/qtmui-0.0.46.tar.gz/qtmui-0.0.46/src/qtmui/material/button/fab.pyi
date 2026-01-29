import asyncio
from typing import Callable, Dict, List, Optional, Union
from qtmui.hooks import State
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer
from qtmui.material.styles import useTheme
from .button import Button
from qtmui.material.styles.create_theme.components.get_qss_styles import get_qss_style
class Fab:
    def __init__(self, icon: Optional[Union[State, str]], animate: Union[State, bool], sx: Optional[Union[State, Dict, Callable, str]], variant: Union[State, str], *args, **kwargs): ...