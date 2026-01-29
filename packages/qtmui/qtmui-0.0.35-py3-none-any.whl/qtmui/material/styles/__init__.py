import inspect
from typing import Callable, Optional, Union, List, Dict
from dataclasses import field, replace
from functools import lru_cache

from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import QTimer

from redux.main import Store

# from qtmui.hooks.use_effect import useEffect
# from qtmui.hooks import useState

from PySide6.QtWidgets import QFrame

from qtmui.material.styles.create_theme.components.qss_properties import QssProperties

from ._generateButtonQss import generateButtonQss

from ...material.styles.create_theme.theme_reducer import CreateThemeAction, ChangePaletteAction, MergeOverideComponentsAction, ThemeState

from .root_reducer import root_reducer, StateType, ActionType


from PySide6.QtCore import QObject, Property, Signal

from qtmui.utils.lodash import merge

from ..system import (
    hexToRgb,
    rgbToHex,
    hslToRgb,
    decomposeColor,
    recomposeColor,
    getContrastRatio,
    getLuminance,
    emphasize,
    alpha,
    darken,
    lighten,
)

from .styled import styled

class ThemeSignal(QObject):
    valueChanged = Signal()

    def __init__(self, theme=None):
        super().__init__()
        self._theme = theme

    def getTheme(self) -> dict:
        return self._theme

    def setTheme(self, value):
        if self._theme != value:
            self._theme = value
            self.valueChanged.emit()

    theme = Property(str, getTheme, setTheme, notify=valueChanged)

themeSignal = ThemeSignal()

def onThemeChanged(data: dict):
    themeSignal.theme = data
    

theme_store: Store[StateType, ActionType, None] = Store(root_reducer)
theme_store.dispatch(CreateThemeAction())


def setTheme(mode):
    theme_store.dispatch(ChangePaletteAction(mode=mode))
    onThemeChanged(theme_store._state.theme)

# @lru_cache(maxsize=128) ===> lỗi 

def useTheme():
    theme: ThemeState = theme_store._state.theme
    theme = replace(theme, state=themeSignal)
    return theme



class ThemeProvider(QFrame):
    def __init__(
        self, 
        children: Optional[List],
        theme: Optional[Dict]
    ):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        
        self._children = children
        
        # themeSignal.changed.connect(self.initUi)
        
        theme_store.dispatch(MergeOverideComponentsAction(payload=theme))
        
        QTimer.singleShot(0, self.initUi)
        

        
        def setSt(mode):
            if mode == "dark":
                stylesheet = ""
                with open("[type=Button][variant=Contained][color=Default][mode=Dark].qss", "r", encoding="utf-8") as f:
                    stylesheet += f.read()
                with open("[type=Button][variant=Contained][color=Primary][mode=Dark].qss", "r", encoding="utf-8") as f:
                    stylesheet += f.read()
                
                self.setStyleSheet(stylesheet)
            else:
                stylesheet = ""
                with open("[type=Button][variant=Contained][color=Default][mode=Light].qss", "r", encoding="utf-8") as f:
                    stylesheet += f.read()
                with open("[type=Button][variant=Contained][color=Primary][mode=Light].qss", "r", encoding="utf-8") as f:
                    stylesheet += f.read()
                self.setStyleSheet(stylesheet)
        
        @theme_store.autorun(lambda state: state.theme)
        def _theme(_theme: ThemeState):
            print("_theme changed__________________________1111111111", _theme.palette.primary.main)
            # themeSignal.changed.emit()
            # setSt(_theme.palette.mode)
            # QTimer.singleShot(0, self.initUi) # Cách này khi load nhiều widget sẽ bị crash
            """
                self.setCentralWidget(
                    ThemeProvider(
                        theme={
                            "palette": {
                                "primary": {
                                    "main": "#007FFF",
                                    "dark": "#0066CC",
                                }
                            }
                        },
                        children=lambda: [ # Nếu không có lambda thì Box tạo trước khi hàm __initUi được của ThemeProvider được gọi
                            Box(
                                sx={
                                    "width": "100px",
                                    "height": "10px",
                                    "border-radius": 1,
                                    "background-color": "primary.main",
                                    "&:hover": {
                                        "background-color": "primary.dark",
                                    },
                                }
                            )
                            for i in range(3000)
                        ],
                    )
                )
            """
            
        
    def initUi(self):
        
        # button_styles = generateButtonQss(theme_store._state.theme, get_qss_style)
        # print("button_styles generated__________________________", button_styles)
        print("initUi called__________________________55555555555555555")
        
        if isinstance(self._children, Callable):
            self._children = self._children()
                
        if isinstance(self._children, list):
            for widget in self._children:
                self.layout().addWidget(widget)
            


###################### test gen qss file #########################
def camel_to_kebab_case(s: str) -> str:
    """
    Chuyển đổi chuỗi từ camelCase sang kebab-case.
    """
    return ''.join(['-' + c.lower() if c.isupper() else c for c in s]).lstrip('-')


def resolve_theme_value(theme, value: Union[str, Callable], key: str=None) -> Optional[str]:
    """
    Giải quyết giá trị theme từ chuỗi dạng 'palette.primary.main', 'text.secondary', v.v.
    """

    if isinstance(value, str) and (
        value.startswith("text.") 
        or value.startswith("background.")
        or value.startswith("primary.")
        or value.startswith("secondary.")
        or value.startswith("info.")
        or value.startswith("warning.")
        or value.startswith("error.")
        or value.startswith("grey.")
        ):
        value = f"palette.{value}"
        # print(value)

    if isinstance(value, str) and value.startswith("palette."):
        parts = value.split(".")
        theme_value = theme
        _value = None
        for part in parts:
            theme_value = getattr(theme_value, part, None)
            if theme_value is None:
                return None
        return theme_value
    elif isinstance(value, Callable):
        # return value(theme) # cũ 
        
        sig = inspect.signature(value)
        # Tạo đối số mặc định nếu không có
        default_args = {
            k: (v.default if v.default is not inspect.Parameter.empty else None)
            for k, v in sig.parameters.items()
        }

        try:
            return value(**default_args)
        except Exception as e:
            return None
    # elif "font" not in key and ((isinstance(value, int) or isinstance(value, float)) and 0 <= value <= 3):
    elif "font" not in key and ((isinstance(value, int) or isinstance(value, float)) and 0 <= value <= 5):
    # elif "font" not in key and ((isinstance(value, int) or isinstance(value, float))): # bị vỡ hết
        # value = 8 * value
        value = value * theme.spacing.default_spacing

    return value


def get_qss_style(sx: Dict, class_name: Optional[str] = None) -> str:
    """
    Hàm tạo chuỗi QSS từ dictionary sx, hỗ trợ nested selectors và pseudo-classes.
    Nếu class_name=None, chỉ trả về chuỗi thuộc tính mà không bao bọc trong block.
    """
    # print("get_qss_style_____________________", sx)
    if isinstance(sx, str):
        return sx

    theme = useTheme()
    base_styles = []  # Styles cấp cao
    nested_styles = []  # Styles cho các selector lồng nhau

    for key, value in sx.items():
        # Chỉ áp dụng camel_to_kebab_case cho các key không bắt đầu bằng "&"
        if not key.startswith("&"):
            css_key = camel_to_kebab_case(key)
        else:
            css_key = key

        # Xử lý các selector lồng nhau (bắt đầu bằng "&")
        if css_key.startswith("&"):
            print('nested selector found_____________________', css_key)
            selector = css_key[1:].strip()  # Bỏ "&" và khoảng trắng
            if class_name is None:
                continue  # Bỏ qua nested selectors nếu không có class_name
            if selector.startswith(":"):  # Pseudo-class như &:hover
                pseudo_part, *child_part = selector.split(" ", 1)
                pseudo = pseudo_part[1:]  # Bỏ ":"
                if child_part:  # Có selector con, ví dụ &:hover .Typography
                    nested_selector = f"{class_name}[slot={pseudo}] {child_part[0].lstrip('.')}"
                else:
                    nested_selector = f"{class_name}[slot={pseudo}]"
            else:  # Không có pseudo-class, ví dụ & Typography hoặc & #container
                if " " in selector:  # Có khoảng trắng, ví dụ & Typography
                    nested_selector = selector.split(" ", 1)[1]  # Lấy phần sau khoảng trắng
                else:
                    nested_selector = f"{class_name} {selector}"

            print('nested _____________________', nested_selector)

            if isinstance(value, dict):
                nested_qss = get_qss_style(value, nested_selector)
                nested_styles.append(nested_qss)
            continue

        # Xử lý thuộc tính CSS cấp cao
        
        resolved_value = resolve_theme_value(theme, value, key)
        if resolved_value is None:
            continue

        if css_key in QssProperties.__dict__.values():

            if css_key in ["marginX", "mx"]:
                base_styles.append(f"margin-left: {resolved_value};")
                base_styles.append(f"margin-right: {resolved_value};")
            elif css_key in ["marginY", "my"]:
                base_styles.append(f"margin-top: {resolved_value};")
                base_styles.append(f"margin-bottom: {resolved_value};")
            elif css_key in ["paddingX", "px"]:
                base_styles.append(f"padding-left: {resolved_value};")
                base_styles.append(f"padding-right: {resolved_value};")
            elif css_key in ["paddingY", "py"]:
                base_styles.append(f"padding-top: {resolved_value};")
                base_styles.append(f"padding-bottom: {resolved_value};")
            elif css_key == "width" and str(resolved_value).find("%") == -1:
                base_styles.append(f"min-width: {resolved_value};")
                base_styles.append(f"max-width: {resolved_value};")
            elif css_key == "height" and str(resolved_value).find("%") == -1:
                base_styles.append(f"min-height: {resolved_value};")
                base_styles.append(f"max-height: {resolved_value};")
            elif css_key not in ["mb", "display", "flex-shrink", "flex-grow", "align-items", 
                                "flex-direction", "align-self", "z-index", "justify-content"]:
                base_styles.append(f"{css_key}: {resolved_value};")

    # Tạo QSS
    qss = ""
    if base_styles:
        if class_name:
            qss = f"{class_name} {{\n    " + "\n    ".join(base_styles) + "\n}}"
        else:
            qss = "\n    ".join(base_styles)  # Chỉ trả về chuỗi thuộc tính nếu không có class_name
    if nested_styles:
        if qss:
            qss += "\n\n"
        qss += "\n\n".join(nested_styles)

    return qss.strip().replace("}}", "}")