import asyncio
from functools import lru_cache
from typing import Callable, Optional, Union, Dict
from PySide6.QtGui import QCursor, QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget, QToolButton
from PySide6.QtCore import Qt, QUrl
import uuid
from qtmui.hooks.use_runable import useRunnable
from qtmui.hooks import State, useEffect
from qtmui.material.styles import useTheme
from qtmui.material.styles.create_theme.theme_reducer import ThemeState
from qtmui.material.styles.create_theme.create_palette import PaletteColor, TypeText
from qtmui.material.styles.create_theme.typography import TypographyStyle
from qtmui.material.styles.create_theme.components.get_qss_styles import get_qss_style
from qtmui.i18n.use_translation import translate, i18n
from ..widget_base import PyWidgetBase
from ..py_iconify import PyIconify
from ...utils.data import convert_sx_params_to_str, convert_sx_params_to_dict
class Link:
    def __init__(self, align, children, text: Optional[Union[str, State, Callable]], color: str, disabled: bool, value: object, classes, gutterBottom, wrap, width: Optional[int], paragraph, href: str, underline: str, onClick: Callable, sx: Optional[Union[Callable, str, Dict]], variant: str, *args, **kwargs): ...
    def _init_ui(self): ...
    def reTranslation(self, text): ...
    def _set_stylesheet(self, component_styled): ...
    def enterEvent(self, event): ...
    def leaveEvent(self, event): ...
    def mousePressEvent(self, event): ...