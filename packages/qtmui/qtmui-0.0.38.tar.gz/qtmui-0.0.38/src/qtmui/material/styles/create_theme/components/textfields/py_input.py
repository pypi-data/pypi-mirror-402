from typing import Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from ...theme_reducer import ThemeState

from ..properties_name import *
from .....system.color_manipulator import alpha

def py_input(_theme):
    theme: ThemeState = _theme

    _color = {
        'focused': theme.palette.text.primary,
        'active': theme.palette.text.secondary,
        'placeholder': theme.palette.text.disabled,
        'disabled': theme.palette.text.disabled,
        'error': theme.palette.error.main,
    }

    return {
        'MuiInput': {
            'styles': {
                'root': {
                    margin: "0px",
                    backgroundColor: "transparent",
                    border: f"1px solid transparent",
                    borderRadius: f'{theme.shape.borderRadius}px',
                },
                "title": {
                    subcontrolOrigin: "margin",
                    left: theme.spacing(1),
                    border: "none",
                    borderRadius: theme.spacing(1),
                    height: int(theme.spacing(1).replace("px", "")),
                    color: _color['active'],
                    p: "0 2px", # đang lười sửa
                    "slots": {
                        'focused': {
                            color: _color['focused']
                        },
                        'error': {
                            color: _color['error']
                        },
                        'disabled': {
                            color: _color['disabled']
                        },
                    },
                    "props": {
                        "standardVariant": {
                            left: 0,
                            p: 0
                        },
                        "filledVariant": {
                            "small": {
                                paddingTop: "2px",
                            },
                            "medium": {
                                paddingTop: "4px",
                            },
                        },
                        "typography": {
                            "small": {
                                lineHeight: 1.5,
                                fontSize: "9px",
                                fontWeight: 500,
                            },
                            "medium": {
                                lineHeight: 1.5,
                                fontSize: "11px",
                                fontWeight: 500,
                            }
                        }
                    }
                },
                "helperLabel": {
                    lineHeight: 1.5,
                    fontSize: "12px",
                    fontWeight: 400,
                    height: "20px",
                    marginLeft: f"{theme.spacing(1)}",
                    "slots": {
                        "error": {
                            color: _color['error']
                        }
                    },
                    "props": {
                        "standard": {
                            marginLeft: 0
                        }
                    }
                }

            },
        },

    }