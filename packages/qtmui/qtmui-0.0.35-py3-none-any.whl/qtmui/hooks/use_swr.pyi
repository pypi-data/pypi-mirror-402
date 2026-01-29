import sys
import json
import traceback
from PySide6.QtCore import QObject, QRunnable, Signal, Slot
from PySide6.QtCore import QObject, Signal, Slot
from qtmui.hooks import useState
class Signals:
class useSWR:
    def __init__(self, fn, *args, **kwargs): ...
    def run(self): ...