from typing import Optional, Callable, Union
from qtmui.material.py_iconify import Iconify
from qtmui.hooks import State
from .button import Button
class ToggleButton:
    def __init__(self, icon: Optional[Iconify], text: Optional[Union[str, State, Callable]], value: Optional[object], selected: bool, *args, **kwargs): ...
    def _setup_toggle_button(self): ...