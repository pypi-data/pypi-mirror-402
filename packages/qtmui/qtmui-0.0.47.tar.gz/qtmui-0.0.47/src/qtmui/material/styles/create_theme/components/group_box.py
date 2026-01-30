from typing import TYPE_CHECKING
from .properties_name import *
if TYPE_CHECKING:
    from qtmui.material.styles.create_theme.theme_reducer import ThemeState
from ....system.color_manipulator import alpha

def group_box(_theme):
    theme: ThemeState = _theme

    lightMode = theme.palette.mode == "light"
    
    return {
        'PyGroupBox': {
            'styles': {
                'root': {
                    border: f'1px solid {alpha(theme.palette.grey._500, 0.16)}',
                    borderRadius: theme.spacing(2),
                    marginTop: "10px",
                    fontWeight: theme.typography.button.fontWeight,
                    fontSize: theme.typography.button.fontSize
                },
                'title': {
                    subcontrolOrigin: 'margin',
                    subcontrolPosition: 'top center',
                    border: f'1px solid {alpha(theme.palette.grey._500, 0.16)}',
                    borderRadius: "11px",
                    backgroundColor: theme.palette.background.paper,
                    color: theme.palette.text.secondary,
                    left: "16px",
                    p: "5px",
                    height: "20px",
                    fontWeight: theme.typography.button.fontWeight,
                    fontSize: theme.typography.button.fontSize
                }
            },
        },
    }
