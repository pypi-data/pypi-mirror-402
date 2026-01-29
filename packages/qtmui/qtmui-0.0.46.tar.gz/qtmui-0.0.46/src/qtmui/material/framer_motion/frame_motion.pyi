import asyncio
from functools import lru_cache
import uuid
from typing import Optional, Union, Callable, Dict, List
from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, QPoint
from qtmui.material.styles.create_theme.components.get_qss_styles import get_qss_style
from qtmui.utils.data import deep_merge
from qtmui.material.styles import useTheme
from qtmui.hooks import useEffect, State
from qtmui.utils.calc import timer
from qtmui.material.widget_base import PyWidgetBase
from qtmui.material.widget_base.anim_manager import AnimManager
from qtmui.material.widget_base.shadow_effect import ShadownEffect
from qtmui.errors import PyMuiValidationError
from qtmui.material.utils.validate_params import _validate_param
from qtmui.configs import LOAD_WIDGET_ASYNC
class FrameMotion:
    def __init__(self, children: Optional[Union[State, List, str]], **kwargs): ...
    def _set_children(self, value): ...
    def _get_children(self): ...
    def _init_ui(self): ...
    def _update_children(self): ...
    def _onDestroy(self, obj): ...
    def showEvent(self, event): ...