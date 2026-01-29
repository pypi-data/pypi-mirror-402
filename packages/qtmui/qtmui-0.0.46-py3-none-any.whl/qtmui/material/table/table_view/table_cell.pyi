from typing import TYPE_CHECKING, Callable, Union, Optional
from PySide6.QtWidgets import QFrame, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal
from ...typography import Typography
from ...avatar import Avatar
from ...label import Label
from qtmui.hooks import useState, State
class TableViewCell:
    def __init__(self, key: str, data: object, padding: str, align: str, children: object, colSpan: int, onClick: Callable, sx: Optional[Union[dict, State]], text: str): ...
    def enterEvent(self, event): ...