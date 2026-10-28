import sqlite3
import logging
from datetime import datetime
from typing import List
from dataclasses import asdict
import pandas as pd
from colorama import Fore, Style
from .models import Place

def save_data(places: List[Place], base_name: str = "neshan_export", fmt: str = "csv") -> str:
    """Save scraped places to the chosen file format (csv, json, parquet, sqlite)"""
    if not places:
        logging.warning("No data to save!")
        return ""

    df = pd.DataFrame([asdict(p) for p in places])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}_{timestamp}.{fmt}"

    try:
        if fmt == "csv":
            df.to_csv(filename, index=False, encoding="utf-8-sig")
        elif fmt == "json":
            df.to_json(filename, orient="records", force_ascii=False, indent=4)
        elif fmt == "parquet":
            df.to_parquet(filename, index=False)
        elif fmt == "sqlite":
            filename = f"{base_name}_{timestamp}.db"
            conn = sqlite3.connect(filename)
            df.to_sql("places", conn, if_exists="replace", index=False)
            conn.close()

        logging.info(f"Data successfully saved to {Fore.YELLOW}{filename}{Style.RESET_ALL}")
        return filename
    except Exception as e:
        logging.error(f"Failed to save data to {filename}: {e}")
        return ""
