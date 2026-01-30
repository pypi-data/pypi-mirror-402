from .core.app import FluxApp
from .core.orm import Model
from .engine.core import FluxEngine, GameEntity

# استيراد جميع العناصر من حزمة widgets الفرعية
from .widgets import (
    # Base
    Control, Text, ElevatedButton, TextButton, OutlinedButton, IconButton, FloatingActionButton,
    # Layout
    Container, Row, Column, Stack, Divider,
    # Input
    TextField, Checkbox, Radio, Slider, Switch, Dropdown,
    # Media
    Image, Icon,
    # List & Table
    ListView, DataTable,
    # Dialogs & Navigation
    Page, AlertDialog, BottomSheet, NavigationBar, Tabs
)

__version__ = "3.1.6"

def help():
    print(f"\n[FluxPy-UI v{__version__} - The Ultimate Universal Framework]")
    print("-" * 60)
    print("Core: FluxApp, Model, FluxEngine")
    print("Layout: Container, Row, Column, Stack, Divider")
    print("Input: TextField, Checkbox, Dropdown, Slider, Switch, Radio")
    print("Buttons: ElevatedButton, TextButton, OutlinedButton, IconButton, FloatingActionButton")
    print("Dialogs: Page, AlertDialog, BottomSheet, Tabs, NavigationBar")
    print("Media: Image, Icon")
    print("Lists: ListView, DataTable")
    print("-" * 60)
