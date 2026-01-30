import sys
import math
from dataclasses import dataclass, field
from typing import Dict, List, Union, Callable, Optional, Any, Tuple
from PySide6.QtCore import QObject, Property, QVariantAnimation, QEasingCurve
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtCore import QRectF, Qt
def _to_str(v): ...
def _parse_px(v, default): ...
def _parse_percent(v, default: float): ...
def _parse_color(v, default: str): ...
def _parse_bool(v, default: bool): ...
def _parse_enum(v, allowed: set, default): ...
def _parse_spacing(v, default): ...
def _parse_border(v: Any): ...
def _parse_box_shadow(v: Any): ...
class ComputedStyle:
    width: Optional[float]
    height: Optional[float]
    min_width: Optional[float]
    min_height: Optional[float]
    max_width: Optional[float]
    max_height: Optional[float]
    margin: Tuple[float, float, float, float]
    padding: Tuple[float, float, float, float]
    background_color: QColor
    border_width: float
    border_style: str
    border_color: QColor
    border_radius: float
    outline_width: float
    outline_color: QColor
    opacity: float
    visibility: str
    overflow: str
    translate_x: float
    translate_y: float
    rotate: float
    scale_x: float
    scale_y: float
    shadow_enabled: bool
    shadow: bool
    shadow_ox: float
    shadow_oy: float
    shadow_blur: float
    shadow_spread: float
    shadow_color: QColor
    color: QColor
    font_size: float
    font_weight: int
    line_height: float
    text_align: str
    cursor: str
    user_select: str
    extra: Dict[str, Any]
def parse_sx(sx: dict): ...
class KeyframeTrack:
    times: List[float]
    values: List[Number]
def _lerp(a: float, b: float, t: float): ...
def _sample_track(track: KeyframeTrack, p: float): ...
def _cubic_bezier_ease(x1: float, y1: float, x2: float, y2: float, x: float): ...
class Timeline:
    def __init__(self, duration_ms: int, loop_count: int, easing: Union[QEasingCurve, List[float]]): ...
    def add_track(self, name: str, times: List[float], values: List[Number]): ...
    def _ease(self, p: float): ...
    def sample(self, progress_0_1: float): ...
def compile_variant_timeline(variants: dict, variant_key: str, apply_fn: Callable[Any, Any], parent: Optional[QObject]): ...