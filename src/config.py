from colorama import Fore, Style

# Default URLs
NESHAN_MAPS_URL = "https://neshan.org/maps"

# Delay profiles in seconds (min, max) to avoid anti-bot detection
DELAYS = {
    "low": (0.5, 1.5),
    "medium": (1.5, 3.5),
    "high": (3.5, 6.0)
}

# Centralized CSS Selectors for Neshan Maps
# Note: #root prefix is essential so selectors never match injected assistant inputs!
SELECTORS = {
    "search_input_trigger": "#root input.f5AeHfr, #root input[readonly], #root input[type='search']",
    "search_input_active": "#root input.AZLBjuP, #root input[type='search']:not([readonly])",
    "search_input": "#root input.AZLBjuP, #root input[type='search']:not([readonly])",
    "search_result_item": ".nrFZBE4",
    "search_in_area_btn": "button:has-text('در این ناحیه'), button:has-text('این محدوده'), button:has-text('جستجوی')",
    "map_canvas": "canvas.mapboxgl-canvas",
    "place_title": "h1",
    "place_category": "span.qpxuHlU, span[class*='category']",
    "place_rating": ".qZI77s3",
    "place_info_buttons": "button.wE_mwzL",
    "place_hours": "div.GiQOShA",
}

# ASCII Banner configuration
BANNER_LINES = [
    r"███╗   ██╗███████╗███████╗██╗  ██╗ █████╗ ███╗   ██╗",
    r"████╗  ██║██╔════╝██╔════╝██║  ██║██╔══██╗████╗  ██║",
    r"██╔██╗ ██║█████╗  ███████╗███████║███████║██╔██╗ ██║",
    r"██║╚██╗██║██╔══╝  ╚════██║██╔══██║██╔══██║██║╚██╗██║",
    r"██║ ╚████║███████╗███████║██║  ██║██║  ██║██║ ╚████║",
    r"╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝"
]

BANNER_COLORS = [
    Fore.RED + Style.BRIGHT,
    Fore.YELLOW + Style.BRIGHT,
    Fore.GREEN + Style.BRIGHT,
    Fore.CYAN + Style.BRIGHT,
    Fore.BLUE + Style.BRIGHT,
    Fore.MAGENTA + Style.BRIGHT
]

# Standard request headers for downloading assets
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://neshan.org/maps"
}
