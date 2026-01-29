from typing import Callable, Optional, Union
from PySide6.QtWidgets import QHBoxLayout, QFrame, QSpacerItem, QSizePolicy
from qtmui.hooks import State
from ..typography.typography import Typography
from ..button import IconButton
class DialogHeader:
    def __init__(self, parent, title: Optional[Union[State, str, Callable]], align: str): ...