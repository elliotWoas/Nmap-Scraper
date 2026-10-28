import os
import re
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import DEFAULT_HEADERS

# Reusable session with connection pooling for high throughput
_session = None

def get_download_session() -> requests.Session:
    """Get or create a thread-safe requests session with connection pooling"""
    global _session
    if _session is None:
        _session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=20,
            pool_maxsize=30,
            max_retries=Retry(total=2, backoff_factor=0.1)
        )
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
        _session.headers.update(DEFAULT_HEADERS)
    return _session

def sanitize_filename(name: str) -> str:
    """Sanitize string to be safely used as file or directory name across OSes"""
    cleaned = re.sub(r'[\\/*?:"<>|]', '_', name).strip()
    return cleaned if cleaned else "place"

def _download_single_photo(session: requests.Session, url: str, filepath: str) -> bool:
    """Download a single photo with fast timeout and error tolerance"""
    try:
        resp = session.get(url, timeout=6)
        if resp.status_code == 200 and len(resp.content) > 400:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        logging.debug(f"Failed photo download from {url}: {e}")
    return False

def download_photos_for_place(
    photos: List[str],
    place_name: str,
    place_idx: int,
    query: str,
    base_dir: str = "downloads",
    max_photos: int = 5
) -> List[str]:
    """
    Download up to max_photos (default 5 newest photos) concurrently using a thread pool.
    Saves to: downloads/<query>/<idx>_<name>/photo_*.jpg
    """
    if not photos:
        return []

    # Keep only the newest photos up to max_photos (default: 5)
    photos_to_download = photos[:max_photos]

    clean_q = sanitize_filename(query) or "search"
    clean_p = sanitize_filename(f"{place_idx:02d}_{place_name}")[:50]
    folder = os.path.join(base_dir, clean_q, clean_p)
    os.makedirs(folder, exist_ok=True)

    session = get_download_session()
    saved_files = []

    # Download photos in parallel (up to max_photos concurrent threads)
    max_workers = min(len(photos_to_download), max_photos, 8)
    tasks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, url in enumerate(photos_to_download, 1):
            ext = "jpg"
            lower_url = url.lower()
            if ".png" in lower_url:
                ext = "png"
            elif ".webp" in lower_url:
                ext = "webp"

            filepath = os.path.join(folder, f"photo_{i}.{ext}")
            future = executor.submit(_download_single_photo, session, url, filepath)
            tasks.append((future, filepath))

        for future, path in tasks:
            if future.result():
                saved_files.append(path)

    return saved_files
