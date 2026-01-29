from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any, Callable, Union, List
from dataclasses import field, replace
from typing import Callable, Sequence, Optional
from qtmui.immutable import Immutable
from qtmui.redux import ReducerResult, CompleteReducerResult, BaseAction, BaseEvent, Store
class LocationState:
    currentUrl: Optional[str]
    prevUrl: Optional[List]
    mextUrl: Optional[List]
class UpdateCurrentUrlAction:
    url: Optional[str]
def location_reducer(state: Any, action: BaseAction): ...