from qtmui.hooks import useState, State
from dataclasses import dataclass
from typing import Callable, Dict
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QMainWindow, QWidget, QLineEdit
from PySide6.QtCore import QObject, Property, Signal
class Boolean:
    state: State
    onTrue: Callable
    onFalse: Callable
    onToggle: Callable
    toggle: Callable
class UseBoolean:
    def __init__(self, initValue): ...
    def onTrue(self, *args, **kwargs): ...
    def onFalse(self): ...
    def onToggle(self): ...
def useBoolean(initValue): ...