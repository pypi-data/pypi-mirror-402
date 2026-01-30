from typing import TYPE_CHECKING, Union, Callable
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, Property, Slot, Signal
from ..controller import Controller
from ..slider import Slider
from ..box import Box
from ..form_helper_text import FormHelperText
from qtmui.material.styles import useTheme
from qtmui.hooks import useState
from ..qss_name import *
class RHFSlider:
    def __init__(self, name: str, control: QWidget, onChange: Callable, helperText: str): ...
    def set_value(self, value): ...
    def stateSignal(self): ...
    def stateSignal(self, value): ...
    def state(self, state): ...