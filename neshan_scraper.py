#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neshan Maps Scraper - Main Entry Point
Supports Interactive Map Selection mode (Default) and automated CLI mode.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import argparse
import logging
from colorama import Fore, Style

from src.logger import setup_logging, print_banner
from src.exporter import save_data
from src.scraper import scrape_places
from src.interactive import run_interactive_mode

def main():
    parser = argparse.ArgumentParser(description="Advanced Neshan Maps Scraper (Interactive & CLI)")
    parser.add_argument("-s", "--search", type=str, default="آرایشگاه", help="Search query (e.g. آرایشگاه, کافه)")
    parser.add_argument("-t", "--total", type=int, default=10, help="Total items to scrape in CLI mode")
    parser.add_argument("-o", "--output", type=str, default="neshan_export", help="Base name for output file")
    parser.add_argument("-f", "--format", type=str, choices=['csv', 'json', 'parquet', 'sqlite'], default='csv', help="Output format")
    parser.add_argument("--headless", action="store_true", help="Run in background headless mode (CLI only)")
    parser.add_argument("--cli", action="store_true", help="Run automated CLI mode without interactive map UI")
    parser.add_argument("--delay", type=str, choices=['low', 'medium', 'high'], default='medium', help="Delay profile")
    parser.add_argument("--log", type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help="Logging level")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive map UI")
    parser.add_argument("--no-confirm", action="store_true", help="Disable confirmation prompt before scraping each place")
    parser.add_argument("--no-photos", action="store_true", help="Disable downloading photos")
    parser.add_argument("--max-photos", type=int, default=5, help="Maximum number of newest photos to download per place (default: 5)")

    args = parser.parse_args()

    # Set up logging & banner
    setup_logging(args.log)
    print_banner()

    # By default, run Interactive Mode with Map Selector, unless --cli or --headless is requested
    is_interactive = not (args.cli or args.headless)

    if is_interactive:
        search_query = args.search if args.search else "آرایشگاه"
        run_interactive_mode(
            initial_query=search_query,
            output_name=args.output,
            fmt=args.format,
            delay_mode=args.delay
        )
    else:
        search_query = args.search if args.search else "آرایشگاه"
        ask_confirm = not args.no_confirm
        download_photos = not args.no_photos

        logging.info(f"{Fore.GREEN}Starting Automated CLI Scraper...{Style.RESET_ALL} Query='{search_query}', Total={args.total}, Photos={download_photos}")
        results = scrape_places(
            search_for=search_query,
            total=args.total,
            headless=args.headless,
            delay_mode=args.delay,
            ask_confirm=ask_confirm,
            download_photos=download_photos,
            output_name=args.output,
            fmt=args.format
        )
        save_data(results, args.output, args.format)

if __name__ == "__main__":
    main()
