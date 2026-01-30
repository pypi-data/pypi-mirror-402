from typing import Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from qtmui.material.styles.create_theme.theme_reducer import ThemeState

from ....system.color_manipulator import alpha
from .properties_name import *

def select(_theme) -> Dict:
    theme: ThemeState = _theme

    return {
        'MuiSelect': {
            'styles': {
                'root': {
                    "@multiple": {
                        "min-height": 38,
                        "@chip": {
                            "min-height": 44,
                        }
                    }
                },
                "icon": {
                    "width": 24,
                    "height": 24,
                }
                
            }
        },
    }
