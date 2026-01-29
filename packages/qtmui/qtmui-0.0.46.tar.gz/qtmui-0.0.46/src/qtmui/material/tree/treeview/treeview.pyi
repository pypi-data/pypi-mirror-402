from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QFileSystemModel
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING, Union
from .treeview_model import TreeViewModel
class TreeView:
    def __init__(self, model: Union[TreeViewModel], rootIndexPath: str): ...