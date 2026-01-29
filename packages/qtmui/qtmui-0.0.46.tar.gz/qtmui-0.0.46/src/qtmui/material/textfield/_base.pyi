import asyncio
from typing import Any
from PySide6.QtCore import QTimer, QDate, QDateTime, QTime
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QLineEdit, QSizePolicy
from qtmui.i18n.use_translation import translate, i18n
from qtmui.hooks.use_state import State, useState
from qtmui.material.date_time.date_picker import DatePicker, ZhDatePicker
from qtmui.material.date_time.time_picker import AMTimePicker, TimePicker
from qtmui.material.styles import useTheme
from qtmui.material.textfield.py_date_edit import PyDateEdit
from qtmui.material.textfield.py_date_time_edit import PyDateTimeEdit
from qtmui.material.textfield.tf_double_spinbox import TFDoubleSpinBox
from qtmui.material.textfield.tf_plaintext_edit import TFPlainTextEdit
from qtmui.material.textfield.py_plaintext_edit_multiple import PyPlainTextEditMultiple
from qtmui.material.textfield.tf_plaintext_edit_multiple import TFPlainTextEditMultiple
from qtmui.material.textfield.tf_spin_box import TFSpinBox
from qtmui.material.textfield.py_time_edit import PyTimeEdit
from qtmui.material.textfield.tf_line_edit import TFLineEdit
from qtmui.material.widget_base import PyWidgetBase
from ..utils._misc import signals_blocked
class TextFieldBaseMixin:
    def __init__(self, **kwargs): ...
    def base_init_ui(self): ...
    def base_init_input_field(self): ...
    def base_set_data(self, value, valueChanged, setText): ...
    def base_set_text_from_data(self): ...
    def base_connect_signals_props(self): ...
    def base_on_destroy(self, obj): ...
    def base_on_theme_changed(self): ...