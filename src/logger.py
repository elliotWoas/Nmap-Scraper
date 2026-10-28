import sys
import logging
from colorama import init, Fore, Style
from .config import BANNER_LINES, BANNER_COLORS

# Initialize UTF-8 for console output on Windows to prevent UnicodeEncodeError
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Initialize colorama
init(autoreset=True)

class ColorLogFormatter(logging.Formatter):
    """Custom colored formatter for logging output"""
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, Fore.WHITE)
        format_str = f"{Fore.LIGHTBLACK_EX}%(asctime)s{Style.RESET_ALL} - {log_color}%(levelname)s{Style.RESET_ALL} - %(message)s"
        formatter = logging.Formatter(format_str, datefmt="%H:%M:%S")
        return formatter.format(record)

def setup_logging(level: str = "INFO"):
    """Configure root logger with colored output"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorLogFormatter())
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)

def print_banner():
    """Print a colorful ASCII banner for Neshan Scraper"""
    try:
        print("\n")
        for line, color in zip(BANNER_LINES, BANNER_COLORS):
            print(f"  {color}{line}{Style.RESET_ALL}")
        print("\n" + "=" * 54 + "\n")
    except Exception:
        print("\n=== NESHAN MAPS SCRAPER ===\n")
