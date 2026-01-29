import uuid
from PySide6.QtWidgets import QVBoxLayout, QFrame, QSizePolicy
from PySide6.QtCore import Qt
from typing import Optional, Union, List, Callable
from qtmui.hooks import State
from ..typography import Typography
from ..box import Box
from qtmui.material.styles import useTheme
class AlignBox:
    def __init__(self, **kwargs): ...
class TimelineContent:
    def __init__(self, children, classes: dict, sx: Union[List[Union[Callable, dict, bool]], Callable, dict], text: Optional[Union[str, State, Callable]]): ...
    def _initUI(self): ...