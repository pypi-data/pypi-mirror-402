import sys
import uuid
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
class Item:
    def __init__(self, content: QWidget): ...