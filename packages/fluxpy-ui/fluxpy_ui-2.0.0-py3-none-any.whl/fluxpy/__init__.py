from .core.app import FluxApp, Page
from .widgets.base import Text, Container, ElevatedButton
from .engine.core import FluxEngine, GameEntity

__version__ = "2.0.0"

def help():
    print("\n[FluxPy-UI v2.0.0 - Global Functions & Classes]")
    print("-" * 40)
    print("Core:")
    print("  - FluxApp: Main application class")
    print("  - Page: Main UI container and controller")
    print("\nWidgets:")
    print("  - Text: Highly customizable text element")
    print("  - Container: Box model for layout and styling")
    print("  - ElevatedButton: Modern clickable button")
    print("\nGame Engine (FluxEngine):")
    print("  - FluxEngine: 2D Game engine view")
    print("  - GameEntity: Base class for game objects")
    print("\nUsage Example:")
    print("  import fluxpy as fx")
    print("  def main(page: fx.Page):")
    print("      page.add(fx.Text('Hello World'))")
    print("  app = fx.FluxApp()")
    print("  app.run(main)")
    print("-" * 40)
