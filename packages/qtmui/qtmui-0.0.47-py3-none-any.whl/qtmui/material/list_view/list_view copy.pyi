from typing import Dict
from PySide6.QtWidgets import QVBoxLayout, QFrame, QListView, QAbstractItemView, QLabel, QFrame, QScrollArea, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QStringListModel, QEvent, QPoint, QRect
import sys
from PySide6.QtGui import QFocusEvent
class ListView:
    def __init__(self, parent_frame, context, fullWidth: bool, children: list): ...
    def update_height(self): ...