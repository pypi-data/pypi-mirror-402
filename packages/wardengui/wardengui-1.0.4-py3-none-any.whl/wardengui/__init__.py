"""WardenGUI - Terminal GUI for managing Warden Docker environments."""

__version__ = "1.0.0"
__author__ = "Yehor Shytikov"

from .manager import WardenManager, CommandResult

__all__ = ["WardenManager", "CommandResult"]
