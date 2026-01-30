from typing import TYPE_CHECKING, Optional, Dict

from ....system.color_manipulator import alpha
from .properties_name import *

if TYPE_CHECKING:
    from qtmui.material.styles.create_theme.theme_reducer import ThemeState

class MuiFormLabel:
    focused: str = ""
    error: str = ""
    disabled: str = ""
    filled: str = ""

class TextFieldStyle:
    muiFormHelperText: str = "" # HELPER
    muiFormLabel: Optional[MuiFormLabel] = None# LABEL
    muiInputBase: str = "" # BASE
    muiInput: str = "" # # STANDARD
    muiOutlinedInput: str = "" # # OUTLINED
    muiFilledInput: str = "" # # FILLED



def text_field(_theme) -> Dict:
    theme: ThemeState = _theme
    
    _color = {
        'focused': theme.palette.text.primary,
        'active': theme.palette.text.secondary,
        'placeholder': theme.palette.text.disabled,
    }

    # font = {
    #     'label': theme.typography.body1.to_qss_props(),
    #     'value': theme.typography.body2.to_qss_props(), # body2
    # }


    return {
        # HELPER
        'MuiFormHelperText': {
            'styles': {
                'root': {
                    marginTop: {theme.spacing(1)}
                }
            },
        },

        # "MuiInputBase": {
        #     "styles": {
        #         "root": {
        #             # lineHeight: theme.typography.body2.lineHeight,
        #             # fontSize: theme.typography.body2.fontSize,
        #             # fontWeight: 600,
        #             # # paddingRight: "54px",
        #             # paddingLeft: "0px",
        #             # color: theme.palette.text.primary,
        #             # # backgroundColor: "red",
        #             "props": {
        #                 "multiline": {
        #                     "small": {
        #                         paddingTop: "12px",
        #                     },
        #                     "medium": {
        #                         paddingTop: "16px",
        #                     },
        #                 },
        #                 "multiple": {
        #                     paddingTop: "0px",
        #                     paddingLeft: "0px",
        #                 },
                        
        #                 "filledVariant": {
        #                     "small": {
        #                         marginTop: "8px",
        #                     },
        #                     "medium": { 
        #                         marginTop: "10px",
        #                     },
        #                 }
        #             }
        #         }
        #     }
        # },

        # STANDARD
        'MuiStandardInput': {
            'styles': {
                'root': {
                    marginTop: "6px",
                    backgroundColor: "transparent",
                    color: theme.palette.text.primary,
                    border: "1px solid transparent",
                    borderBottom: f"1px solid {alpha(theme.palette.grey._500, 0.32)}" ,
                    borderRadius: '0px',
                    paddingLeft: '0px', # NOT WORK
                    "slots": {
                        'hovered': {
                            borderBottom: f"1px solid {_color['active']}" ,
                        },
                        'focused': {
                            borderBottom: f"1px solid {_color['focused']}" ,
                        },
                        'error': {
                            # "border-bottom": theme.palette.error.main
                            borderBottom: f"1px solid {theme.palette.error.main}" ,
                        },
                        'multiple': {
                            paddingRight: "0px"
                        },
                        'hasStartAdornment': {
                            paddingLeft: 0
                        },
                        'standardVariant': {
                            paddingLeft: "0px",
                        },
                    }
                },
            },
        },

        # OUTLINED
        'MuiOutlinedInput': {
            'styles': {
                'root': {
                    margin: "0px",
                    marginTop: "6px",
                    backgroundColor: "transparent",
                    color: theme.palette.text.primary,
                    border: f"1px solid {alpha(theme.palette.grey._500, 0.2)}",
                    borderRadius: f'{theme.shape.borderRadius}px',
                    paddingLeft: f"{theme.spacing(1)}",
                    "slots": {
                        'hovered': {
                            borderColor: _color['active']
                        },
                        'focused': {
                            borderColor: _color['focused']
                        },
                        'error': {
                            borderColor: theme.palette.error.main
                        },
                        'disabled': {
                            borderColor: theme.palette.action.disabledBackground
                        },
                        'multiple': {
                            paddingRight: "0px"
                        },
                        'hasStartAdornment': {
                            paddingLeft: 0
                        },

                    }
                },


            },
        },

        # FILLED
        'MuiFilledInput': {
            'styles': {
                'root': {
                    backgroundColor: alpha(theme.palette.grey._500, 0.16),
                    borderRadius: f'{theme.shape.borderRadius}px',
                    color: theme.palette.text.primary,
                    paddingLeft: f"{theme.spacing(1)}",
                    "slots": {
                        'hovered': {
                            backgroundColor: alpha(theme.palette.grey._500, 0.16)
                        },
                        'focused': {
                            backgroundColor: alpha(theme.palette.grey._500, 0.16)
                        },
                        'error': {
                            backgroundColor: alpha(theme.palette.error.main, 0.08)
                        },
                        'errorFocused': {
                            backgroundColor: alpha(theme.palette.error.main, 0.16)
                        },
                        'disabled': {
                            backgroundColor: theme.palette.action.disabledBackground
                        },
                        'multiple': {
                            paddingRight: "0px"
                        },
                        'hasStartAdornment': {
                            paddingLeft: 0
                        },
                    }
                },
            },
        },

        'MuiInputSize': {
            'styles': {
                'small': {
                    minHeight: "32px",
                    "typography": {
                        lineHeight: 1.5,
                        fontSize: "12px",
                        fontWeight: 600,
                    },
                    'filledVariant': {
                        # minHeight: "22px", #32 # mui 4
                        "slots": {
                            "focused": {
                                marginTop: "8px",
                            }
                        },
                        "props": {
                            "hasValue": {
                                marginTop: "8px",
                            }
                        }
                        
                    },
                    'dateTimeType': {
                        paddingLeft: f"{theme.spacing(1)}"
                    },
                    'hasStartAdornment': {
                        paddingLeft: f"{theme.spacing(1)}"
                    },
                },
                'medium': {
                    minHeight: "38px", # mui 4,
                    "typography": {
                        lineHeight: 1.57,
                        fontSize: "13px",
                        fontWeight: 600,
                    },
                    'filledVariant': {
                        minHeight: "38px", # mui 4
                        "slots": {
                            "focused": {
                                marginTop: "14px",
                            }
                        },
                        "props": {
                            "hasValue": {
                                marginTop: "14px",
                            }
                        }
                    },
                    'dateTimeType': {
                        paddingLeft: f"{theme.spacing(1)}"
                    }
                },

            }
        }

    }
