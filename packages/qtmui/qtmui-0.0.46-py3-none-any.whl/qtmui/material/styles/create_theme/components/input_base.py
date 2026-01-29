from typing import TYPE_CHECKING, Optional

from ....system.color_manipulator import alpha

from .properties_name import *


if TYPE_CHECKING:
    from ..theme_reducer import ThemeState
    from qtmui.material.styles.create_theme.create_palette import Palette


def input_base(_theme):
    # Khởi tạo các thông tin cần thiết
    theme: ThemeState = _theme
    theme_palette: Palette = theme.palette

    COLORS = ['primary', 'secondary', 'info', 'success', 'warning', 'error']
    lightMode = theme.palette.mode == 'light'
    
    _color = {
        'focused': theme.palette.text.primary,
        'active': theme.palette.text.secondary,
        'placeholder': theme.palette.text.disabled,
    }
    
    return {
        'MuiInputBase': {
            'styles': {
                'root': {
                    border: "none",
                    fontWeight: 600,
                    lineHeight: theme.typography.body2.lineHeight,
                    fontSize: theme.typography.body2.fontSize,
                    color: theme.palette.text.primary,
                },
                'placeholder': {
                    lineHeight: theme.typography.body2.lineHeight,
                    fontSize: theme.typography.body2.fontSize,
                    opacity: 1,
                    color: _color['placeholder']
                },
                'size': {
                  "small": {
                    "height": "30px"
                  },
                  "medium": {
                    "height": "36px"
                  }
                }
            }
        }
    }