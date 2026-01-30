from .core.app import FluxApp, Page
from .widgets.base import Text, Container, ElevatedButton, Row, Column, TextField, Icon, Checkbox
from .engine.core import FluxEngine, GameEntity
from .core.orm import Model

__version__ = "2.0.7"

def help():
    print(f"\n[FluxPy-UI v{__version__} - Enterprise Framework]")
    print("-" * 50)
    print("Core:")
    print("  - FluxApp: Main application entry point")
    print("  - Page: Window controller (title, icon, bgcolor, frameless, show_message)")
    print("  - Model: Simple ORM for database management")
    print("\nLayouts:")
    print("  - Row: Horizontal layout container")
    print("  - Column: Vertical layout container")
    print("  - Container: Styled box model")
    print("\nWidgets:")
    print("  - Text: Customizable text (size, weight, color)")
    print("  - TextField: User input (placeholder, password, on_change)")
    print("  - ElevatedButton: Modern button with icon support")
    print("  - Icon: Display icons")
    print("  - Checkbox: Boolean selection")
    print("\nGame Engine:")
    print("  - FluxEngine: 2D Graphics engine")
    print("  - GameEntity: Game object with physics properties")
    print("\nWindow Customization:")
    print("  page.icon = 'path/to/icon.png'")
    print("  page.show_minimize = False")
    print("  page.frameless = True")
    print("-" * 50)
