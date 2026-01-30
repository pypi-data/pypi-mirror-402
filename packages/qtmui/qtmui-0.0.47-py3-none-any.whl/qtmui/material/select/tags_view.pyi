from typing import Callable, Dict, Optional, Union
import uuid
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from qtmui.hooks import State
from .py_line_edit_multiple import PyLineEditMultiple
class TagsView:
    def __init__(self, hidden: Optional[Union[State, bool]], content: State, sx: Optional[Union[Callable, str, Dict]], *args, **kwargs): ...
    def clear_layout(self, layout): ...
    def _render_ui(self): ...