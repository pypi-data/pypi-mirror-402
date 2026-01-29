from __future__ import annotations
import asyncio
import contextlib
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Mapping
import contextvars
import uuid
from qtmui.redux import BaseAction
from .action_bus import ActionBus
from .effects import Call, Cancel, Cancelled, Delay, Fork, Spawn, Join, Put, Race, All, Parallel, Select, Take, ActionChannel, EventChannel
from .channel import Channel, BufferConfig
class SagaEnv:
    dispatch: Callable[Any, Any]
    get_state: Callable[Any, Any]
    bus: ActionBus
class _TaskMeta:
    id: str
    parent_id: Any
    cancelled_flag: bool
_current_task_id: contextvars.ContextVar[Any]
class SagaRuntime:
    def __init__(self, env: SagaEnv): ...
    def run(self, saga: Any, *args, **kwargs): ...
    def run_detached(self, saga: Any, *args, **kwargs): ...
    def _create_task(self, coro: Awaitable[Any]): ...
    def _pattern_to_predicate(self, pattern: Any): ...