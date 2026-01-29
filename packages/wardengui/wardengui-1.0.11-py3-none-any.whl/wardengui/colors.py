"""ANSI color codes and box drawing characters for terminal output."""


class Colors:
    """ANSI color codes for terminal output."""
    # Reset
    RESET = "\033[0m"
    
    # Text styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    BROWN = "\033[38;5;130m"  # Brown color (256-color mode)
    
    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    BG_DARK_GRAY = "\033[48;5;236m"
    
    # Combined styles
    BOLD_CYAN = "\033[1;36m"
    BOLD_RED = "\033[1;91m"
    BOLD_GREEN = "\033[1;92m"
    BOLD_YELLOW = "\033[1;93m"
    BOLD_BLUE = "\033[1;34m"
    
    # Box drawing characters
    BOX_TOP_LEFT = "╔"
    BOX_TOP_RIGHT = "╗"
    BOX_BOTTOM_LEFT = "╚"
    BOX_BOTTOM_RIGHT = "╝"
    BOX_VERTICAL = "║"
    BOX_HORIZONTAL = "═"
    BOX_HORIZONTAL_THIN = "─"
    BOX_T_LEFT = "╠"
    BOX_T_RIGHT = "╣"
    BOX_T_TOP = "╦"
    BOX_T_BOTTOM = "╩"
    BOX_CROSS = "╬"
    BOX_TREE = "├"
    BOX_TREE_END = "└"
    
    @staticmethod
    def hyperlink(url: str, text: str) -> str:
        """Create a clickable hyperlink in terminal (OSC 8 escape sequence)."""
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"
