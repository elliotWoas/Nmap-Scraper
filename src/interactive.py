import os
import sys
import time
import queue
import threading
import logging
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Page
from colorama import Fore, Style
from .config import NESHAN_MAPS_URL, SELECTORS
from .models import ScrapeOptions, BoundingBox
from .browser import create_browser_session
from .scraper import run_scraping_flow, trigger_and_fill_search

def inject_overlay_ui(page: Page):
    """Read src/overlay.js and inject it into the active Neshan Maps page"""
    src_dir = os.path.dirname(os.path.abspath(__file__))
    overlay_path = os.path.join(src_dir, "overlay.js")

    if not os.path.exists(overlay_path):
        overlay_path = os.path.join(os.path.dirname(src_dir), "overlay.js")

    if not os.path.exists(overlay_path):
        logging.warning(f"overlay.js not found at {overlay_path}!")
        return

    try:
        with open(overlay_path, "r", encoding="utf-8") as f:
            script_content = f.read()
        page.evaluate(script_content)
        logging.info("Interactive Neshan overlay successfully injected.")
    except Exception as e:
        logging.error(f"Failed to inject overlay UI: {e}")

def count_places_in_box(page: Page, query: str, box_data: Optional[Dict[str, Any]] = None) -> int:
    """Execute search scoped to the selected box / viewport and count results (optional)"""
    try:
        logging.info(f"🔎 جستجوی «{query}» روی نقشه نشان...")
        trigger_and_fill_search(page, query)

        result_selector = SELECTORS["search_result_item"]
        try:
            page.wait_for_selector(result_selector, timeout=15000)
        except Exception:
            logging.warning("پاسخی از لیست نتایج دریافت نشد.")
            return 0

        box = BoundingBox.from_dict(box_data)
        if box and box.center_x and box.center_y:
            try:
                canvas_loc = page.locator("canvas.mapboxgl-canvas")
                if canvas_loc.count() > 0:
                    c_box = canvas_loc.first.bounding_box()
                    if c_box:
                        map_cx = c_box["x"] + c_box["width"] / 2
                        map_cy = c_box["y"] + c_box["height"] / 2
                        dx = map_cx - box.center_x
                        dy = map_cy - box.center_y
                        if abs(dx) > 30 or abs(dy) > 30:
                            page.mouse.move(box.center_x, box.center_y)
                            page.mouse.down()
                            page.mouse.move(box.center_x + dx * 0.5, box.center_y + dy * 0.5, steps=8)
                            page.mouse.up()
                            time.sleep(1.0)
            except Exception as e:
                logging.debug(f"Map panning note: {e}")

            try:
                page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const target = btns.find(b => b.innerText && (b.innerText.includes('در این ناحیه') || b.innerText.includes('این محدوده')));
                    if (target) target.click();
                }""")
                time.sleep(2.0)
            except Exception:
                pass

        count = page.locator(result_selector).count()
        logging.info(f"✅ تعداد نتایج یافت‌شده: {count} مکان.")
        return max(count, 0)
    except Exception as e:
        logging.warning(f"Error during counting places: {e}")
        return 0

def run_interactive_mode(
    initial_query: str = "آرایشگاه",
    output_name: str = "neshan_export",
    fmt: str = "csv",
    delay_mode: str = "medium"
):
    """
    Launch interactive browser session on Neshan Maps with custom floating panel,
    bounding box drawing tool, and step-by-step confirmation.
    """
    logging.info(f"{Fore.GREEN}Starting Interactive Mode on Neshan Maps...{Style.RESET_ALL}")
    
    action_queue = queue.Queue()
    terminal_queue = queue.Queue()

    # Background thread to capture terminal inputs (e.g. Enter to start, or s/y/a/q during scrape)
    def terminal_listener():
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                terminal_queue.put(line.strip())
            except Exception:
                break

    t_term = threading.Thread(target=terminal_listener, daemon=True)
    t_term.start()

    def on_ui_action(action):
        try:
            logging.info(f"UI Action received: {action.get('type')}")
            action_queue.put(action)
        except Exception as e:
            logging.error(f"Error handling UI action: {e}")

    with sync_playwright() as p:
        browser, context, page = create_browser_session(p, headless=False)

        # Expose communication bridge to page
        page.expose_function("__dispatch_ui_action", on_ui_action)

        # Re-inject overlay on page navigations
        page.on("load", lambda: inject_overlay_ui(page))

        logging.info("Opening Neshan Maps and injecting interactive overlay...")
        page.goto(NESHAN_MAPS_URL, wait_until="commit")
        
        # Wait for page to initialize and inject UI
        try:
            page.wait_for_selector(
                f"{SELECTORS['search_input_trigger']}, {SELECTORS['map_canvas']}",
                timeout=25000
            )
        except Exception:
            pass

        inject_overlay_ui(page)

        # Search immediately on map for initial query
        if initial_query:
            try:
                logging.info(f"در حال نمایش نتایج اولیه برای «{initial_query}»...")
                trigger_and_fill_search(page, initial_query)
            except Exception as e:
                logging.debug(f"Initial search note: {e}")

        print("\n" + "=" * 68)
        print(f"{Fore.CYAN}🎯 اسکرپر هوشمند نشان آماده است!{Style.RESET_ALL}")
        print(f"۱. {Fore.WHITE}نقشه را آزادانه به شهر، محله یا خیابان مورد نظرتان ببرید.{Style.RESET_ALL}")
        print(f"۲. {Fore.GREEN}برای شروع بررسی و استخراج مکان‌ها:{Style.RESET_ALL}")
        print(f"   • روی دکمه {Fore.GREEN}«🚀 شروع بررسی و استخراج»{Style.RESET_ALL} در نوار پایین مرورگر کلیک کنید")
        print(f"   • یا در همین پنجره ترمینال کلید {Fore.YELLOW}Enter{Style.RESET_ALL} را بزنید.")
        print(f"۳. {Fore.WHITE}هر مکان باز می‌شود و می‌توانید در نشان آن را ببینید و با {Fore.GREEN}Enter{Fore.WHITE} تایید یا با {Fore.YELLOW}s{Fore.WHITE} رد کنید.{Style.RESET_ALL}")
        print("=" * 68 + "\n")

        # Drain any residual keystrokes from launching the program
        time.sleep(0.5)
        while not terminal_queue.empty():
            try:
                terminal_queue.get_nowait()
            except:
                break

        # Main interactive event loop
        while True:
            action = None
            try:
                action = action_queue.get_nowait()
            except queue.Empty:
                pass

            # Check if user pressed Enter in terminal to start
            if not action:
                try:
                    term_msg = terminal_queue.get_nowait()
                    logging.info("دریافت دستور شروع از ترمینال...")
                    action = {
                        "type": "start",
                        "options": {"query": initial_query, "limit": 50, "askConfirm": True, "downloadPhotos": True}
                    }
                except queue.Empty:
                    pass

            if not action:
                if page.is_closed():
                    logging.info("Browser closed by user.")
                    break
                time.sleep(0.4)
                continue

            try:
                action_type = action.get("type")

                if action_type == "start":
                    opts_dict = action.get("options", {})
                    options = ScrapeOptions(
                        query=opts_dict.get("query") or initial_query,
                        limit=int(opts_dict.get("limit") or 50),
                        ask_confirm=bool(opts_dict.get("askConfirm", True)),
                        download_photos=bool(opts_dict.get("downloadPhotos", True)),
                        delay_mode=delay_mode,
                        output_name=output_name,
                        output_format=fmt
                    )

                    logging.info(f"شروع استخراج برای «{options.query}» (سقف={options.limit}, تایید تک‌تک={options.ask_confirm}, دانلود عکس={options.download_photos})")
                    run_scraping_flow(page=page, options=options, terminal_queue=terminal_queue)
                    logging.info("استخراج پایان یافت. می‌توانید مجدداً جستجو کنید یا مرورگر را ببندید.")
            except Exception as e:
                logging.exception(f"Error handling action in event loop: {e}")

        browser.close()
