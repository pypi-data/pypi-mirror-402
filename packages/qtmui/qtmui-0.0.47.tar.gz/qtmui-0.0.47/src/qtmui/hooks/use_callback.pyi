from typing import Callable, Dict, List, Optional, Any
import inspect
from qtmui.hooks import State
from .use_boolean import UseBoolean
class CallbackState:
    def __init__(self): ...
def useCallback(callback: Callable, dependencies: Optional[List[State]]): ...