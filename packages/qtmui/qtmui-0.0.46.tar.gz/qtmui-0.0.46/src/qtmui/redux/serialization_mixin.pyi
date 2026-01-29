from __future__ import annotations
import dataclasses
from types import NoneType
from typing import TYPE_CHECKING, Any
from qtmui.immutable import Immutable, is_immutable
class SerializationMixin:
    def serialize_value(cls: type[SerializationMixin], obj: Any): ...
    def _serialize_dataclass_to_dict(cls: type[SerializationMixin], obj: Immutable): ...