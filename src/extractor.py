import re
import time
import logging
from typing import List, Tuple, Dict, Any
from playwright.sync_api import Page
from .models import Place
from .config import SELECTORS

def clean_persian_text(text: str) -> str:
    """Clean text by removing control characters, zero-width chars, and UI action residues"""
    if not text:
        return ""
    # Remove LTR/RTL marks and zero-width spaces
    cleaned = text.replace('\u200e', '').replace('\u200f', '').replace('\u200c', ' ')
    # Remove UI artifacts from Neshan buttons
    for artifact in [
        "آدرس کپی شد", "شماره تماس کپی شد", "مختصات جغرافیایی کپی شد",
        "مسیریابی", "اطلاعات عمومی", "نظرات", "تصاویر", "مکان‌های مشابه", "درباره",
        "ویرایش اطلاعات یا گزارش تعطیلی این مکان", "مدیر این کسب‌وکار هستید؟", "افزودن تصویر برای این مکان"
    ]:
        cleaned = cleaned.replace(artifact, "")
    # Normalize whitespaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n+', ' ', cleaned)
    return cleaned.strip()

def extract_place_coordinates(url: str) -> Tuple[str, str]:
    """Extract latitude and longitude from Neshan URL (hash or path format)"""
    lat, lng = "", ""
    m_hash = re.search(r'#c([0-9.]+)-([0-9.]+)', url)
    if m_hash:
        lat, lng = m_hash.group(1), m_hash.group(2)
    else:
        m_at = re.search(r'@([0-9.]+),([0-9.]+)', url)
        if m_at:
            lat, lng = m_at.group(1), m_at.group(2)
    return lat, lng

def extract_place_all_fast(page: Page) -> Tuple[Place, List[str]]:
    """
    Lightning-fast, single-evaluation extractor that extracts all place metadata
    and photos strictly from the place details view (< 20ms).
    """
    place = Place()
    place.neshan_url = page.url
    lat, lng = extract_place_coordinates(page.url)
    place.latitude = lat
    place.longitude = lng

    raw_data: Dict[str, Any] = {}
    try:
        raw_data = page.evaluate(r"""() => {
            const h1 = document.querySelector('h1');
            if (!h1) return null;

            // Target the active place container (XUaBDPb or parent)
            const panel = h1.closest('.XUaBDPb') || h1.parentElement?.parentElement?.parentElement || document.body;

            // 1. Name & Category
            const name = h1.innerText.trim();
            let category = '';
            const catEl = panel.querySelector('span.qpxuHlU, .lJ3T_kN');
            if (catEl) category = catEl.innerText.trim();

            // 2. Rating & Review Count
            let rating = '', reviews_count = '';
            const rEl = panel.querySelector('.qZI77s3, .J305Eoo');
            if (rEl) {
                const m = rEl.innerText.match(/(\d+[./]\d*)\s*\((\d+)\)/);
                if (m) {
                    rating = m[1].replace('/', '.');
                    reviews_count = m[2];
                }
            }
            if (!rating) {
                const rMatch = panel.innerText.match(/(\d+[./]\d+)\s*\n*\s*(\d+)\s*رای/);
                if (rMatch) {
                    rating = rMatch[1].replace('/', '.');
                    reviews_count = rMatch[2];
                }
            }

            // 3. Contact & Address Details
            let address = '', phone_number = '', website = '', opening_hours_today = '';
            const btns = Array.from(panel.querySelectorAll('button.wE_mwzL, button, a'));
            for (const btn of btns) {
                const t = (btn.innerText || '').trim();
                const img = btn.querySelector('img');
                const src = img ? (img.src || '') : '';

                if (src.includes('pin.png')) {
                    if (!address) address = t;
                } else if (src.includes('call.png') || t.includes('شماره تماس') || /^0\d{9,10}$/.test(t.replace(/[^0-9]/g, ''))) {
                    if (!phone_number) phone_number = t.replace('شماره تماس:', '').trim();
                } else if (src.includes('world.png') || t.includes('.ir') || t.includes('.com')) {
                    const a = btn.tagName === 'A' ? btn : btn.querySelector('a');
                    if (!website) website = a ? a.href : (t.includes('http') ? t : '');
                }
            }

            // Fallback for address from plain text
            if (!address) {
                const addrMatch = panel.innerText.match(/(تهران[^\n]+|خیابان[^\n]+|بلوار[^\n]+|میدان[^\n]+)/);
                if (addrMatch) address = addrMatch[1];
            }

            // 4. Hours
            const hMatch = panel.innerText.match(/ساعت کاری:\s*([^\n]+)/);
            if (hMatch) {
                opening_hours_today = hMatch[1].trim();
            } else {
                const hMatch2 = panel.innerText.match(/(باز است[^\n]*|بسته است[^\n]*)/);
                if (hMatch2) opening_hours_today = hMatch2[1].trim();
            }

            // 5. Description
            let description = '';
            const ps = Array.from(panel.querySelectorAll('p'));
            for (const p of ps) {
                const t = (p.innerText || '').trim();
                if (t.length > 20 && !t.includes('اطلاعات عمومی') && !t.includes('تصاویر') && !t.includes('نظرات')) {
                    description = t;
                    break;
                }
            }

            // 6. Photos strictly for this place (up to 5 newest photos)
            const photos = [];
            const imgs = Array.from(panel.querySelectorAll('img'));
            for (const img of imgs) {
                const src = img.src || img.getAttribute('data-src') || '';
                if (!src || src.endsWith('.svg') || src.includes('icon') || src.includes('traffic_zone') || src.includes('map_thumbnail')) continue;
                if (src.includes('places/images') || src.includes('Thumbnail') || src.includes('Original') || src.includes('poi-photo')) {
                    // Exclude recommendation cards at bottom
                    if (!img.closest('.recommendations, [class*="similar"]')) {
                        photos.push(src);
                    }
                }
            }

            return {
                name,
                category,
                rating,
                reviews_count,
                address,
                phone_number,
                website,
                opening_hours_today,
                description,
                photos: Array.from(new Set(photos)).slice(0, 5)
            };
        }""")
    except Exception as e:
        logging.debug(f"Fast evaluate error: {e}")

    if raw_data:
        if raw_data.get("name"):
            place.name = clean_persian_text(raw_data["name"])
        if raw_data.get("category"):
            place.category = clean_persian_text(raw_data["category"])
        if raw_data.get("rating"):
            place.rating = raw_data["rating"]
        if raw_data.get("reviews_count"):
            place.reviews_count = raw_data["reviews_count"]
        if raw_data.get("address"):
            place.address = clean_persian_text(raw_data["address"])
        if raw_data.get("phone_number"):
            place.phone_number = clean_persian_text(raw_data["phone_number"])
        if raw_data.get("website"):
            place.website = raw_data["website"]
        if raw_data.get("opening_hours_today"):
            place.opening_hours_today = clean_persian_text(raw_data["opening_hours_today"])
        if raw_data.get("description"):
            place.description = clean_persian_text(raw_data["description"])

    photos = raw_data.get("photos", []) if raw_data else []
    return place, photos

def extract_place(page: Page) -> Place:
    """Backwards compatible wrapper for extract_place"""
    place, _ = extract_place_all_fast(page)
    return place

def extract_place_photos(page: Page) -> List[str]:
    """Backwards compatible wrapper for extract_place_photos"""
    _, photos = extract_place_all_fast(page)
    return photos
