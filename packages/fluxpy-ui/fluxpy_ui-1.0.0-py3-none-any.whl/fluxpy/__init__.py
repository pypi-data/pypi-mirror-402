from .core.app import FluxApp, Page
from .widgets.base import Container, Text, ElevatedButton
from .core.debugger import FluxDebugger

__version__ = "1.1.0"

def help():
    """Displays all available functions and classes in FluxPy."""
    functions = [
        "FluxApp() - Main application runner",
        "Page - The main window/canvas (Flet-style)",
        "Container(content, ...) - Layout container with padding, bgcolor, etc.",
        "Text(value, size, color, ...) - Highly customizable text element",
        "ElevatedButton(text, on_click, ...) - Modern button with hover effects",
        "Page.add(*controls) - Add elements to the page",
        "FluxDebugger - Smart error tracking system",
        "help() - Show this list of functions"
    ]
    print("\n--- FluxPy (Flet-Style) Functions & Classes ---")
    for func in functions:
        print(f"• {func}")
    print("-----------------------------------------------\n")

__all__ = ['FluxApp', 'Page', 'Container', 'Text', 'ElevatedButton', 'help']
