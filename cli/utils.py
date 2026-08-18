"""
RAKAN - CLI Utilities
Colored terminal output and structured interface
"""

import sys
import os
import platform
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""
    
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


class Terminal:
    """Terminal utility class for colored output."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.colors_enabled = self._check_color_support()
    
    def _check_color_support(self) -> bool:
        """Check if terminal supports ANSI colors."""
        if not sys.stdout.isatty():
            return False
        
        if self.system == 'windows':
            # Windows 10+ supports ANSI colors
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable ANSI colors on Windows
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        
        return True
    
    def colorize(self, text: str, color: str, bold: bool = False) -> str:
        """Apply color to text."""
        if not self.colors_enabled:
            return text
        
        color_code = getattr(Colors, color.upper(), Colors.WHITE)
        if bold:
            color_code = Colors.BOLD + color_code
        
        return f"{color_code}{text}{Colors.RESET}"
    
    def print_colored(self, text: str, color: str = 'white', bold: bool = False):
        """Print colored text."""
        print(self.colorize(text, color, bold))
    
    def print_success(self, message: str):
        """Print success message."""
        symbol = "[OK]" if self.system == 'windows' else "✓"
        self.print_colored(f"{symbol} {message}", 'green', bold=True)
    
    def print_error(self, message: str):
        """Print error message."""
        symbol = "[ERROR]" if self.system == 'windows' else "✗"
        self.print_colored(f"{symbol} {message}", 'red', bold=True)
    
    def print_warning(self, message: str):
        """Print warning message."""
        symbol = "[WARNING]" if self.system == 'windows' else "⚠"
        self.print_colored(f"{symbol} {message}", 'yellow', bold=True)
    
    def print_info(self, message: str):
        """Print info message."""
        symbol = "[INFO]" if self.system == 'windows' else "ℹ"
        self.print_colored(f"{symbol} {message}", 'cyan')
    
    def print_header(self, title: str, width: int = 60):
        """Print formatted header."""
        line = "=" * width
        self.print_colored(line, 'cyan', bold=True)
        centered_title = title.center(width)
        self.print_colored(centered_title, 'cyan', bold=True)
        self.print_colored(line, 'cyan', bold=True)
        print()
    
    def print_section(self, title: str):
        """Print section header."""
        self.print_colored(f"\n{title}", 'blue', bold=True)
        self.print_colored("-" * len(title), 'blue')
    
    def print_subsection(self, title: str):
        """Print subsection header."""
        self.print_colored(f"\n  {title}", 'magenta', bold=True)
    
    def print_command(self, command: str, description: str = ""):
        """Print command with description."""
        self.print_colored(f"  $ {command}", 'bright_yellow', bold=True)
        if description:
            self.print_colored(f"    {description}", 'white')
    
    def print_key_value(self, key: str, value: str, key_color: str = 'cyan'):
        """Print key-value pair."""
        self.print_colored(f"  {key}:", key_color, bold=True)
        print(f"    {value}")
    
    def print_list_item(self, item: str, index: Optional[int] = None):
        """Print list item."""
        prefix = f"{index}." if index is not None else "•"
        self.print_colored(f"  {prefix} {item}", 'white')
    
    def print_progress(self, current: int, total: int, message: str = ""):
        """Print progress indicator."""
        percentage = (current / total) * 100
        bar_length = 30
        filled = int(bar_length * current / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        self.print_colored(f"  [{bar}] {percentage:.1f}%", 'blue', bold=True)
        if message:
            self.print_colored(f"  {message}", 'white')
    
    def print_table(self, headers: list, rows: list):
        """Print formatted table."""
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print header
        header_line = "  "
        for i, header in enumerate(headers):
            header_line += f"{header:<{col_widths[i]}}  "
        self.print_colored(header_line, 'cyan', bold=True)
        
        # Print separator
        separator = "  "
        for width in col_widths:
            separator += "-" * width + "  "
        self.print_colored(separator, 'cyan')
        
        # Print rows
        for row in rows:
            row_line = "  "
            for i, cell in enumerate(row):
                row_line += f"{str(cell):<{col_widths[i]}}  "
            print(row_line)
    
    def clear_screen(self):
        """Clear terminal screen."""
        if self.system == 'windows':
            os.system('cls')
        else:
            os.system('clear')


# Global terminal instance
terminal = Terminal()


def print_banner():
    """Print RAKAN banner."""
    terminal.print_header("RAKAN - Local AI Development Platform", 70)
    terminal.print_colored("Created by DevFazla", 'magenta')
    terminal.print_colored("https://devfazla.com | @devfazla", 'magenta')
    print()


def print_version():
    """Print version information."""
    terminal.print_section("Version Information")
    terminal.print_key_value("RAKAN", "0.1.0")
    terminal.print_key_value("Python", sys.version.split()[0])
    terminal.print_key_value("Platform", platform.platform())
    terminal.print_key_value("Author", "DevFazla")
    terminal.print_key_value("Website", "https://devfazla.com")
    print()


def print_help_summary():
    """Print help summary."""
    terminal.print_section("Quick Start")
    terminal.print_command("rakan doctor", "Check system health")
    terminal.print_command("rakan model list", "List available models")
    terminal.print_command("rakan model use <name>", "Select a model")
    terminal.print_command("rakan chat", "Start interactive chat")
    terminal.print_command("rakan agent run", "Run AI agent")
    terminal.print_command("rakan --help", "Show all commands")
    print()