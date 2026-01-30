from typing import Optional, Union, Callable, Dict
from PySide6.QtWidgets import QFrame, QHBoxLayout
from .linear_indeterminate import LinearIndeterminate
from .linear_query import LinearQuery
from .linear_determinate import LinearDeterminate
from .linear_buffer import LinearBuffer
class LinearProgress:
    def __init__(self, key: str, value: int, variant: str, color: str, sx: Optional[Union[Callable, str, Dict]]): ...
    def _init_ui(self): ...