import time
import queue
import logging
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page
from tqdm import tqdm
from colorama import Fore, Style

from .config import SELECTORS, NESHAN_MAPS_URL
from .models import Place, ScrapeOptions
from .browser import human_delay, get_delay, create_browser_session
from .extractor import extract_place, extract_place_photos, extract_place_all_fast
from .downloader import download_photos_for_place
from .exporter import save_data

def trigger_and_fill_search(page: Page, query: str):
    """
    Robust human-like search activation on Neshan Maps:
    1. Check if active search input (input.AZLBjuP) is already visible
    2. Otherwise wait for initial search placeholder input (input.f5AeHfr) and click it
    3. Fill query and submit with Enter
    """
    try:
        page.wait_for_selector("input.f5AeHfr, input.AZLBjuP", timeout=25000)
    except Exception:
        pass

    try:
        active_input = page.locator("input.AZLBjuP")
        if active_input.count() > 0 and active_input.first.is_visible():
            active_input.first.fill(query)
            human_delay(0.2, 0.4)
            page.keyboard.press("Enter")
            return
    except Exception:
        pass

    try:
        trigger_input = page.locator("input.f5AeHfr")
        if trigger_input.count() > 0:
            trigger_input.first.click(timeout=8000)

        page.wait_for_selector("input.AZLBjuP", timeout=10000)
        page.fill("input.AZLBjuP", query)
        human_delay(0.2, 0.4)
        page.keyboard.press("Enter")
    except Exception as e:
        logging.warning(f"Search input note: {e}")

def open_place_details(page: Page, item_locator) -> bool:
    """Reliably and quickly open a place details view on Neshan Maps"""
    try:
        item_locator.scroll_into_view_if_needed(timeout=1500)
    except Exception:
        pass

    # Try clicking the place link, title, or card
    clicked = False
    for sel in ["a[href*='/places/']", "h2", ".WKMp5zo"]:
        try:
            target = item_locator.locator(sel).first
            if target.count() > 0:
                target.click(force=True, timeout=1200)
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        try:
            item_locator.click(force=True, timeout=1200)
        except Exception:
            pass

    # Wait for place details view to appear and populate
    try:
        page.wait_for_url("**/places/**", timeout=4000)
    except Exception:
        pass

    try:
        page.wait_for_selector("h1", timeout=3500)
        try:
            page.wait_for_selector("button.wE_mwzL, .wE_mwzL", timeout=3000)
        except Exception:
            pass
        return True
    except Exception:
        return False

def return_to_search_results(page: Page, result_selector: str):
    """Reliably and quickly return to the search results list from a place details page"""
    try:
        if page.locator(result_selector).count() > 0 and page.locator(result_selector).first.is_visible():
            return
        page.go_back(wait_until="commit")
        page.wait_for_selector(result_selector, timeout=6000)
        return
    except Exception:
        pass

    try:
        back_btn = page.locator("button:has(img[alt*='back']), button:has(img[alt*='بازگشت'])")
        if back_btn.count() > 0:
            back_btn.first.click(timeout=1500)
            page.wait_for_selector(result_selector, timeout=4000)
    except Exception:
        pass

def ask_user_confirmation(
    page: Page,
    place_info: dict,
    idx: int,
    total: int,
    terminal_queue: Optional[queue.Queue] = None
) -> str:
    """
    Dual-channel confirmation prompt while the place is visibly opened on Neshan Maps:
    1. Shows the sleek floating action bar on Neshan's page
    2. Shows the question and place preview in the terminal console
    User can respond either by clicking on the action bar OR pressing a key:
    - Enter / y : Approve and scrape place
    - s : Skip this place (رد کردن)
    - a : Scrape all remaining places automatically
    - q : Quit and save collected data
    """
    # 1. Show sleek action bar in browser
    try:
        page.evaluate("""(data) => {
            if (typeof window.neshan_show_confirm === 'function') {
                window.neshan_show_confirm(data.info, data.idx, data.total);
            }
        }""", {"info": place_info, "idx": idx, "total": total})
    except Exception as e:
        logging.debug(f"Action bar note: {e}")

    # 2. Print formatted prompt in terminal
    name = place_info.get("name", "بدون نام")
    cat = place_info.get("category", "")
    addr = place_info.get("address", "")
    rating = place_info.get("rating", "")

    print("\n" + "=" * 68)
    print(f"📍 {Fore.CYAN}[مکان {idx+1}/{total}]{Style.RESET_ALL} {Fore.WHITE}{Style.BRIGHT}{name}{Style.RESET_ALL}")
    meta = []
    if cat: meta.append(f"🏢 دسته‌بندی: {cat}")
    if rating: meta.append(f"⭐ امتیاز: {rating}")
    if meta:
        print(" | ".join(meta))
    if addr:
        print(f"📌 آدرس: {addr}")
    print("-" * 68)
    print(f"👉 گزینه‌ها: {Fore.GREEN}[Enter یا y = استخراج]{Style.RESET_ALL} | {Fore.YELLOW}[s = رد کردن/Skip]{Style.RESET_ALL} | {Fore.BLUE}[a = استخراج همه]{Style.RESET_ALL} | {Fore.RED}[q = پایان و ذخیره]{Style.RESET_ALL}")
    print("انتخاب شما: ", end="", flush=True)

    # 3. Wait for browser button click or terminal queue input
    while True:
        # Check browser action bar click or keypress
        try:
            choice = page.evaluate("() => window.__neshan_last_confirm_choice")
            if choice:
                page.evaluate("() => { window.__neshan_last_confirm_choice = null; }")
                choice_fa = {"approve": "تایید", "skip": "رد شد", "all": "استخراج همه", "stop": "توقف"}.get(choice, choice)
                print(f"({choice_fa} از طریق مرورگر)")
                return choice
        except Exception:
            pass

        # Check terminal input
        if terminal_queue:
            try:
                term_input = terminal_queue.get_nowait()
                val = term_input.strip().lower()
                if val in ('s', 'skip', '2', 'رد'):
                    choice = 'skip'
                    print(f"{Fore.YELLOW}رد شد (Skip){Style.RESET_ALL}")
                elif val in ('q', 'quit', 'stop', '4', 'خروج'):
                    choice = 'stop'
                    print(f"{Fore.RED}توقف و ذخیره{Style.RESET_ALL}")
                elif val in ('a', 'all', '3', 'همه'):
                    choice = 'all'
                    print(f"{Fore.BLUE}استخراج همه{Style.RESET_ALL}")
                else: # Default: Enter / y / 1
                    choice = 'approve'
                    print(f"{Fore.GREEN}تایید استخراج{Style.RESET_ALL}")

                # Dismiss action bar confirm state
                try:
                    page.evaluate("() => { if (typeof window.neshan_hide_confirm === 'function') window.neshan_hide_confirm(); }")
                except:
                    pass
                return choice
            except queue.Empty:
                pass

        if page.is_closed():
            return "stop"

        time.sleep(0.12)

def run_scraping_flow(
    page: Page,
    options: ScrapeOptions,
    terminal_queue: Optional[queue.Queue] = None
) -> List[Place]:
    """
    Execute place scraping by opening each place directly on Neshan Maps,
    allowing the user to inspect it, and downloading all data and photos.
    """
    places: List[Place] = []
    result_selector = SELECTORS["search_result_item"]

    try:
        # Check if search results already exist on screen
        existing_count = page.locator(result_selector).count()
        if existing_count == 0:
            logging.info(f"🔎 در حال جستجوی «{options.query}» روی نقشه...")
            try:
                page.evaluate("([c, m, t]) => { if (typeof window.neshan_update_progress === 'function') window.neshan_update_progress(c, m, t); }",
                              [0, options.limit, f"در حال جستجوی «{options.query}»..."])
            except:
                pass
            trigger_and_fill_search(page, options.query)
            try:
                page.wait_for_selector(result_selector, timeout=12000)
            except Exception:
                pass

        # 1. Apply user's current map viewport if 'جستجو در این ناحیه' button is visible
        try:
            clicked_area = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                const target = btns.find(b => b.innerText && (b.innerText.includes('این ناحیه') || b.innerText.includes('این محدوده')));
                if (target && target.offsetWidth > 0 && target.offsetHeight > 0) {
                    target.click();
                    return true;
                }
                return false;
            }""")
            if clicked_area:
                logging.info("فیلتر محدوده: دکمه «جستجو در این ناحیه» کلیک شد.")
                time.sleep(1.8)
        except Exception as e:
            logging.debug(f"Area button note: {e}")

        # Wait for results to be ready
        try:
            page.wait_for_selector(result_selector, timeout=8000)
        except Exception:
            pass

        items_count = page.locator(result_selector).count()
        if items_count == 0:
            logging.warning(f"موردی برای «{options.query}» در این محدوده یافت نشد.")
            try:
                page.evaluate("([c, m, t]) => { if (typeof window.neshan_update_progress === 'function') window.neshan_update_progress(c, m, t); }",
                              [0, 0, f"⚠️ موردی برای «{options.query}» در این محدوده یافت نشد."])
            except:
                pass
            return []

        # 2. Scroll sidebar listings smoothly using scrollIntoView (never touches map canvas)
        logging.info(f"در حال بارگذاری نتایج تا سقف {options.limit} مکان...")
        last_count = 0
        scroll_attempts = 0
        while scroll_attempts < 4:
            current_count = page.locator(result_selector).count()
            if current_count >= options.limit:
                break
            if current_count == last_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_count = current_count
            page.evaluate("""() => {
                const items = document.querySelectorAll('.nrFZBE4');
                if (items.length > 0) {
                    items[items.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            }""")
            human_delay(1.0, 1.8)

        total = min(page.locator(result_selector).count(), options.limit)
        logging.info(f"تعداد {total} مکان برای بررسی و استخراج آماده است.")

        auto_approve_all = not options.ask_confirm

        for idx in range(total):
            listing = page.locator(result_selector).nth(idx)

            # Card preview info from sidebar
            try:
                preview_title = listing.locator("h2").inner_text().strip()
            except:
                preview_title = f"مکان {idx+1}"
            try:
                preview_cat = listing.locator(".lJ3T_kN").inner_text().strip()
            except:
                preview_cat = ""
            try:
                preview_addr = listing.locator(".xz2hYYU").inner_text().strip()
            except:
                preview_addr = ""
            try:
                preview_rating = listing.locator(".J305Eoo").inner_text().strip()
            except:
                preview_rating = ""

            preview_info = {
                "name": preview_title,
                "category": preview_cat,
                "address": preview_addr,
                "rating": preview_rating
            }

            # 3. OPEN THE PLACE ON NESHAN MAPS SO USER CAN VIEW EVERYTHING!
            logging.info(f"باز کردن مکان [{idx+1}/{total}]: {Fore.CYAN}{preview_title}{Style.RESET_ALL}")
            opened = open_place_details(page, listing)
            if not opened:
                logging.warning(f"مکان {idx+1} باز نشد، تلاش مجدد...")
                time.sleep(0.5)
                # Re-locate and try once more
                listing = page.locator(result_selector).nth(idx)
                open_place_details(page, listing)

            # Brief pause for assets
            time.sleep(0.15)

            # 4. Ask confirmation if enabled (user can inspect the real page now!)
            decision = "approve"
            if not auto_approve_all and options.ask_confirm:
                decision = ask_user_confirmation(page, preview_info, idx, total, terminal_queue)

                if decision == "skip":
                    logging.info(f"⏭️ رد شد: {preview_title}")
                    try:
                        page.evaluate("([c, m, t]) => { if (typeof window.neshan_update_progress === 'function') window.neshan_update_progress(c, m, t); }",
                                      [idx + 1, total, f"رد شد: {preview_title}"])
                    except:
                        pass
                    return_to_search_results(page, result_selector)
                    continue

                elif decision == "stop":
                    logging.info("⏹️ استخراج متوقف شد. در حال ذخیره مکان‌های استخراج‌شده...")
                    return_to_search_results(page, result_selector)
                    break

                elif decision == "all":
                    auto_approve_all = True
                    logging.info("⚡ استخراج خودکار تمام موارد باقیمانده...")

            # 5. Fast single-shot data extraction & parallel photo download
            try:
                data, photos = extract_place_all_fast(page)
                if not data.name:
                    data.name = preview_title
                if not data.category:
                    data.category = preview_cat
                if not data.address:
                    data.address = preview_addr
                if not data.rating:
                    data.rating = preview_rating

                if options.download_photos:
                    if photos:
                        saved_paths = download_photos_for_place(photos, data.name, idx + 1, options.query, max_photos=5)
                        data.photo_count = len(saved_paths)
                        data.photo_paths = "; ".join(saved_paths)
                        logging.info(f"📸 {len(saved_paths)} عکس جدید برای «{data.name}» دانلود شد.")
                    else:
                        data.photo_count = 0
                        logging.info(f"عکسی برای «{data.name}» موجود نیست.")

                places.append(data)
                logging.info(f"✅ استخراج شد [{len(places)}/{total}]: {Fore.GREEN}{data.name}{Style.RESET_ALL}")

                try:
                    page.evaluate("([c, m, t]) => { if (typeof window.neshan_update_progress === 'function') window.neshan_update_progress(c, m, t); }",
                                  [idx + 1, total, f"استخراج شد: {data.name}"])
                except:
                    pass

            except Exception as e:
                logging.warning(f"خطا در استخراج جزئیات مکان {idx+1}: {e}")

            # Return to search results list for the next place
            return_to_search_results(page, result_selector)
            time.sleep(0.1)

        # Save data
        if places:
            save_data(places, options.output_name, options.output_format)
            logging.info(f"🎉 اطلاعات {len(places)} مکان در فایل {options.output_name}.{options.output_format} ذخیره شد.")

        try:
            page.evaluate("([c, m, t]) => { if (typeof window.neshan_update_progress === 'function') window.neshan_update_progress(c, m, t); }",
                          [len(places), total, f"✅ استخراج {len(places)} مکان پایان یافت و ذخیره شد."])
        except:
            pass

    except Exception as e:
        logging.error(f"Scraping flow encountered an error: {e}")

    return places

def scrape_places(
    search_for: str,
    total: int = 5,
    headless: bool = False,
    delay_mode: str = "medium",
    ask_confirm: bool = False,
    download_photos: bool = False,
    output_name: str = "neshan_export",
    fmt: str = "csv"
) -> List[Place]:
    """Standard automated CLI scraping function"""
    places: List[Place] = []
    result_selector = SELECTORS["search_result_item"]

    with sync_playwright() as p:
        browser, context, page = create_browser_session(p, headless=headless)

        try:
            logging.info(f"Navigating to Neshan to search: {Fore.CYAN}{search_for}")
            page.goto(NESHAN_MAPS_URL, wait_until="commit")

            trigger_and_fill_search(page, search_for)

            page.wait_for_selector(result_selector, timeout=20000)

            logging.info(f"Scrolling to find {total} listings...")
            last_count = 0
            while True:
                current_count = page.locator(result_selector).count()
                if current_count >= total or current_count == last_count:
                    break
                page.evaluate("""() => {
                    const items = document.querySelectorAll('.nrFZBE4');
                    if (items.length > 0) items[items.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
                }""")
                time.sleep(get_delay(delay_mode))
                last_count = current_count

            actual_total = min(page.locator(result_selector).count(), total)

            pbar = tqdm(
                total=actual_total,
                desc=f"{Fore.MAGENTA}Scraping{Style.RESET_ALL}",
                bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
            )

            auto_approve_all = not ask_confirm

            for idx in range(actual_total):
                listing = page.locator(result_selector).nth(idx)
                try:
                    preview_name = listing.locator("h2").inner_text().strip()
                except:
                    preview_name = f"Item {idx+1}"

                # Open place details
                opened = open_place_details(page, listing)
                time.sleep(0.15)

                if not auto_approve_all:
                    ans = input(f"\n[مکان {idx+1}/{actual_total}] «{preview_name}» استخراج شود؟ (Enter/y=تایید، s=رد کردن، a=همه، q=خروج): ").strip().lower()
                    if ans == 's':
                        pbar.update(1)
                        return_to_search_results(page, result_selector)
                        continue
                    elif ans == 'q':
                        logging.info("Stopping scrape by user request.")
                        return_to_search_results(page, result_selector)
                        break
                    elif ans == 'a':
                        auto_approve_all = True

                try:
                    data, photos = extract_place_all_fast(page)
                    if not data.name:
                        data.name = preview_name

                    if download_photos:
                        if photos:
                            saved = download_photos_for_place(photos, data.name, idx + 1, search_for, max_photos=5)
                            data.photo_count = len(saved)
                            data.photo_paths = "; ".join(saved)
                        else:
                            data.photo_count = 0

                    if data.name:
                        places.append(data)
                        logging.debug(f"Extracted: {data.name}")

                except Exception as e:
                    logging.warning(f"Error on item {idx+1}: {e}")

                return_to_search_results(page, result_selector)
                time.sleep(0.1)
                pbar.update(1)
            pbar.close()

            if places:
                save_data(places, output_name, fmt)

        finally:
            browser.close()

    return places
