from typing import Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from qtmui.material.styles.create_theme.theme_reducer import ThemeState
    from qtmui.material.styles.create_theme.create_palette import Palette

from .properties_name import *
from ....system.color_manipulator import alpha


def checkbox(_theme) -> Dict:
    theme: ThemeState = _theme
    COLORS = ['primary', 'secondary', 'info', 'success', 'warning', 'error']
    lightMode = theme.palette.mode == 'light'
    theme_palette: Palette = theme.palette

    return {
        # CHECKBOX, RADIO, SWITCH
        'MuiFormControlLabel': {
            'styles': {
                'label': {
                    fontSize: theme.typography.body2.fontSize,
                    fontWeight: theme.typography.body2.fontWeight,
                    lineHeight: theme.typography.body2.lineHeight,
                }
            },
        },
        'MuiCheckbox': {
            'styles': {
                'root': lambda ownerState: {
                    **{
                        "width": "30px" if ownerState.get("size") == "small" else "36px",
                        "height": "30px" if ownerState.get("size") == "small" else "36px",
                    },
                    **{
                        "default": {
                            color: theme.palette.grey._900 if lightMode else theme.palette.common.white,
                            # p: theme.spacing,
                            p: '0px',
                            borderRadius: "15px" if ownerState.get("size") == "small" else "18px",
                            backgroundColor: "transparent",
                            "slots": {
                                "hover": {
                                    backgroundColor: alpha(theme_palette.grey._500, 0.24),
                                },
                                "checked": {
                                    backgroundColor: alpha(theme_palette.grey._500, 0.24),
                                },
                            }
                        },
                    },
                    **{
                        f"{_color}": {
                            color: getattr(theme.palette, _color).main,
                            # p: theme.spacing,
                            p: '0px',
                            borderRadius: "15px" if ownerState.get("size") == "small" else "18px",
                            backgroundColor: "transparent",
                            "slots": {
                                "hover": {
                                    backgroundColor: alpha(getattr(theme.palette, _color).main, 0.32),
                                },
                                "checked": {
                                    backgroundColor: alpha(getattr(theme.palette, _color).main, 0.32),
                                },
                            }
                        }
                        for _color in COLORS
                    }
                },
                "icon": lambda ownerState: {
                    color: theme.palette.text.disabled,
                    "size": {
                        "width": 20 if ownerState.get("size") == "small" else 26,
                        "height": 20 if ownerState.get("size") == "small" else 26,
                    }
                },
                "checkedIndicator": {
                    borderWidth: "1px",
                    borderRadius: "3px",
                    p: "8px",
                }
            }
        },
    }
