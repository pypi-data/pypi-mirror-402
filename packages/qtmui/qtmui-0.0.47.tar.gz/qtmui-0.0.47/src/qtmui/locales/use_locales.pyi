import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QMainWindow, QWidget
from PySide6.QtCore import QObject, Property, Signal, Slot
from src.i18n.use_translation import changeLanguage
from src.i18n.use_translation import changeLanguage
from .config_lang import defaultLang, allLangs
def setCurrentLanguage(key: str): ...