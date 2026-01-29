from __future__ import annotations
from typing import Optional, Union
import sys
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QAreaSeries, QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QValueAxis
from PySide6.QtGui import QGradient, QPen, QLinearGradient, QPainter
from .map_change_theme import MapChangeTheme
class Map:
    def __init__(self, initialViewState: dict, *args, **kwargs): ...