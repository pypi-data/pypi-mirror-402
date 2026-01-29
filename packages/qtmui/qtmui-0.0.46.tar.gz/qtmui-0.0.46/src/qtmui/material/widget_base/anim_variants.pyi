import sys
from typing import Optional, Dict, List, Callable, Union, Any
from math import cos, pi
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from src.components.animate.variants import varFade, varZoom, varFlip, varSlide, varScale, varBounce, varRotate, varBgPan, varBgColor, varBgKenburns
VARIANT_MAP: Dict[str, Dict[str, Any]]
def getVariant(variant: str): ...