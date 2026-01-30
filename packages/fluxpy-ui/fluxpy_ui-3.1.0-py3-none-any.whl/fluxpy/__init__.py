from .core.app import FluxApp, Page
from .widgets.base import (Text, Container, ElevatedButton, Row, Column, 
                            TextField, Checkbox, Dropdown, Slider, Switch)
from .widgets.dialogs import AlertDialog, Tabs, Tab
from .engine.core import FluxEngine, GameEntity
from .core.orm import Model

__version__ = "3.1.0"

def help():
    print(f"\n[FluxPy-UI v{__version__} - The Ultimate Universal Framework]")
    print("-" * 60)
    print("Core: FluxApp, Page, Model")
    print("Layout: Container, Row, Column, Stack, Divider")
    print("Input: TextField, Checkbox, Dropdown, Slider, Switch, Radio")
    print("Buttons: ElevatedButton, TextButton, OutlinedButton, IconButton, FAB")
    print("Dialogs: AlertDialog, BottomSheet, Tabs, NavigationBar")
    print("Media: Image, Icon")
    print("Lists: ListView, DataTable")
    print("-" * 60)
