from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QFrame
class Controller:
    def __init__(self, key: str, name: str, value: object, control: object, render: Callable, defaultValue, rules: object, shouldUnregister: bool): ...