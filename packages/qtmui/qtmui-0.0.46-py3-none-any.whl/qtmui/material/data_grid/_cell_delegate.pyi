from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtCore import QRect, QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyleOptionButton, QStyle
from ..utils.icon import icon_base64_to_pixmap
from ._base_button_delegate import DelegateButton
from .icon import icon_base_64_data, icon_chrome_closed, icon_chrome_opened, icon_chrome_opening_closing, icon_profile_edit, icon_profile_delete
class CellDelegate:
    def __init__(self, parent): ...
    def paint(self, painter, option, index): ...