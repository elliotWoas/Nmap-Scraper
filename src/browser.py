import os
import time
import random
import platform
from typing import Tuple
from playwright.sync_api import Playwright, Browser, BrowserContext, Page
from .config import DELAYS

def get_delay(mode: str = "medium") -> float:
    """Return a random delay value based on selected delay profile"""
    min_d, max_d = DELAYS.get(mode, DELAYS["medium"])
    return random.uniform(min_d, max_d)

def human_delay(min_s: float = 0.6, max_s: float = 1.8):
    """Sleep for a realistic human delay with random jitter"""
    time.sleep(random.uniform(min_s, max_s))

def find_system_chrome_path() -> str:
    """Find installed Google Chrome path on Windows if present"""
    if platform.system() == "Windows":
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    return ""

DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def get_desktop_user_agent() -> str:
    """Return a modern desktop user-agent string (never mobile)"""
    return random.choice(DESKTOP_USER_AGENTS)

# Advanced Stealth Script to bypass bot detection & Cloudflare fingerprinting
STEALTH_INIT_SCRIPT = """
(() => {
    // 1. Delete navigator.webdriver automation flag
    delete Object.getPrototypeOf(navigator).webdriver;
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // 2. Mock chrome runtime object
    window.chrome = window.chrome || {
        app: { isInstalled: false, InstallState: { DISABLED: 'DISABLED', INSTALLED: 'INSTALLED', NOT_INSTALLED: 'NOT_INSTALLED' } },
        runtime: {
            OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install' },
            PlatformArch: { X86_64: 'x86-64' }
        },
        loadTimes: function() {},
        csi: function() {}
    };

    // 3. Mock languages (Persian + English)
    Object.defineProperty(navigator, 'languages', {
        get: () => ['fa-IR', 'fa', 'en-US', 'en'],
        configurable: true
    });

    // 4. Mock navigator plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const plugins = [
                { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                { name: 'Chromium PDF Plugin', filename: 'internal-nacl-plugin', description: '' }
            ];
            plugins.item = (i) => plugins[i];
            plugins.namedItem = (n) => plugins.find(p => p.name === n);
            return plugins;
        },
        configurable: true
    });

    // 5. Mock notification permissions
    if (window.navigator.permissions) {
        const origQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (param) => (
            param.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                origQuery(param)
        );
    }
})();
"""

def create_browser_session(
    p: Playwright,
    headless: bool = False
) -> Tuple[Browser, BrowserContext, Page]:
    """
    Launch an ultra-stealth Playwright session with real Chrome flags,
    desktop user-agent, mock navigator properties, and anti-bot evasions.
    """
    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-sandbox",
        "--disable-infobars",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--no-default-browser-check"
    ]
    browser_kwargs = {
        "headless": headless,
        "args": launch_args
    }
    chrome_path = find_system_chrome_path()
    if chrome_path:
        browser_kwargs["executable_path"] = chrome_path

    browser = p.chromium.launch(**browser_kwargs)
    context = browser.new_context(
        user_agent=get_desktop_user_agent(),
        viewport={"width": 1366, "height": 768},
        locale="fa-IR",
        timezone_id="Asia/Tehran",
        color_scheme="light"
    )

    # Inject stealth scripts before any document loads
    context.add_init_script(STEALTH_INIT_SCRIPT)

    page = context.new_page()
    return browser, context, page
