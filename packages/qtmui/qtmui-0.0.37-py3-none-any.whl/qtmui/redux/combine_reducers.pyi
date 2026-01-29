from __future__ import annotations
import copy
import functools
import operator
import uuid
from dataclasses import fields
from typing import TYPE_CHECKING, TypeVar
from qtmui.immutable import make_immutable
from .basic_types import Action, BaseAction, BaseCombineReducerState, BaseEvent, CombineReducerAction, CombineReducerInitAction, CombineReducerRegisterAction, CombineReducerUnregisterAction, CompleteReducerResult, Event, InitAction, is_complete_reducer_result
def combine_reducers(state_type: type[CombineReducerState], action_type: type[Action], event_type: type[Event], **reducers): ...