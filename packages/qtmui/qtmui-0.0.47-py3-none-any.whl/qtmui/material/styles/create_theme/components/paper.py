from typing import Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from qtmui.material.styles.create_theme.theme_reducer import ThemeState

from .properties_name import *
from ....system.color_manipulator import alpha


def paper(_theme) -> Dict:
    theme: ThemeState = _theme
    # theme = _theme
    return {
        'PyPaper': {
            'styles': {
                "root": {
                    # backgroundColor:  theme.palette.background.paper,
                    backgroundColor:  "#ffffff",
                    borderRadius: "8px"
                },
                'outlined': {
                    # borderColor: alpha(theme.palette.grey._500, 0.16),
                    border: "1px solid rgba(0,0,0,0.12)"
                },
            },
        },
    }
