from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QSize, QCoreApplication, QEvent, Signal, QRect
from PySide6.QtGui import QMovie, QIcon, Qt, QColor
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QApplication, QStyleOptionButton, QPushButton
from ...utils.icon import icon_base64_to_pixmap
class StyledOptionButton:
    def __init__(self, parent, name: str, iconBase64: object, size: QSize, iconSize: QSize): ...