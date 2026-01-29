from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping, TypeVar, Generic
from qtmui.redux import BaseAction
from .channel import BufferConfig, Channel
class Take:
    pattern: Any
class Put:
    action: BaseAction
class Call:
    fn: Callable[Any, Any]
    args: tuple[Any, Any]
    kwargs: Any
class Delay:
    seconds: float
class Fork:
    saga: Any
    args: tuple[Any, Any]
    kwargs: Any
class Spawn:
    saga: Any
    args: tuple[Any, Any]
    kwargs: Any
class Join:
    task: Any
class Cancel:
    task: Any
class Race:
    effects: Mapping[str, Any]
class All:
    effects: list[Any]
class Parallel:
    effects: Mapping[str, Any]
class Select:
    selector: Callable[Any, R]
    default: Any
class Cancelled:
def actionChannel(pattern): ...
def eventChannel(subscribe): ...
def take(pattern_or_channel: Any): ...
def put(action: BaseAction): ...
def call(fn: Callable[Any, Any], *args, **kwargs): ...
def delay(seconds: float): ...
def fork(saga: Any, *args, **kwargs): ...
def spawn(saga: Any, *args, **kwargs): ...
def join(task: Any): ...
def cancel(task: Any): ...
def race(**named_effects): ...
def all_(*effects): ...
def parallel(**named_effects): ...
def select(selector: Callable[Any, Any], default: Any): ...
def cancelled(): ...
class ActionChannel:
    pattern: Any
    buffer: BufferConfig
class EventChannel:
    subscribe: Callable[Any, Callable[Any, Any]]
    buffer: BufferConfig