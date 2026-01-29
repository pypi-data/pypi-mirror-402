"""WardenGUI - Terminal GUI for managing Warden Docker environments."""

__version__ = "1.0.0"
__author__ = "Yehor Shytikov"

from .warden import WardenManager, CommandResult
from .colors import Colors

__all__ = ["WardenManager", "CommandResult", "Colors"]
