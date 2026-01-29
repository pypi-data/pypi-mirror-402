from __future__ import annotations
import contextlib
import inspect
import threading
from asyncio import Handle, iscoroutine
from typing import TYPE_CHECKING, Any, Generic, cast
from qtmui.redux.basic_types import Event, EventHandler, TaskCreator
class SideEffectRunner:
    def __init__(self: SideEffectRunner): ...
    def run(self: SideEffectRunner[Event]): ...