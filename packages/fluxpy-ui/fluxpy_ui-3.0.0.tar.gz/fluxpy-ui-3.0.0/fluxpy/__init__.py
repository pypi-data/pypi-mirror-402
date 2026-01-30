from .core.app import FluxApp, Page
from .widgets.base import Text, Container, ElevatedButton, Row, Column, TextField
from .engine.core import FluxEngine, GameEntity
from .core.orm import Model

__version__ = "3.0.0"

def help():
    print(f"\n[FluxPy-UI v{__version__} - Universal Framework]")
    print("-" * 50)
    print("Core: FluxApp, Page, Model")
    print("Widgets: Text, Container, ElevatedButton, Row, Column, TextField")
    print("Game: FluxEngine, GameEntity")
    print("Targets: Desktop (default), Web")
    print("-" * 50)
