import uuid
from PySide6.QtWidgets import QVBoxLayout, QFrame, QSizePolicy
from PySide6.QtCore import Qt
from typing import Optional, Union, List, Callable
from qtmui.hooks import State
from ..typography import Typography
class TimelineOppositeContent:
    def __init__(self, children, classes: dict, sx: Union[List[Union[Callable, dict, bool]], Callable, dict], text: Optional[Union[str, State, Callable]]): ...
    def _initUI(self): ...