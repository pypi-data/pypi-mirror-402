from __future__ import annotations
from typing import Optional, Union
import sys
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarCategoryAxis, QChart, QChartView
from PySide6.QtGui import QGradient, QPen, QLinearGradient, QPainter, QColor, QBrush
from ..system.color_manipulator import alpha
from qtmui.material.styles import useTheme
from qtmui.hooks import useEffect
class ChartLine:
    def __init__(self, dir: str, type: str, series: object, width: Optional[Union[str, int]], height: Optional[Union[str, int]], options: object, key: str, *args, **kwargs): ...
    def _init_line_chart(self): ...
    def _set_stylesheet(self): ...