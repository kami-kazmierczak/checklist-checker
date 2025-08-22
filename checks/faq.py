# checks/faq.py
import json
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import CONTACT_PAGE

def _is_abs(u: str) -> bool:
    try:
        p = urlsplit(u)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False

def _target_urls(root):
    urls = [root]  # homepage zawsze
    if CONTACT_PAGE:
        urls.append(CONTACT_PAGE if _is_abs(CONTACT_PAGE) else urljoin(root, CONTACT_PAGE))
    return urls

def run(root):
    urls = _target_urls(root)
    found_faq = []
    checked = []

    try:
        for url in urls:
            r = fetch(url)
            soup = get_soup(r.text)
            checked.append(url)

            # --- 1) Szukamy schema.org FAQ ---
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "{}")
                except Exception:
                    continue

                # czasem ld+json to lista
                if isinstance(data, list):
                    for d in data:
                        if isinstance(d, dict) and d.get("@type") == "FAQPage":
                            found_faq.append({"url": url, "type": "ld+json"})
                elif isinstance(data, dict) and data.get("@type") == "FAQPage":
                    found_faq.append({"url": url, "type": "ld+json"})

            # --- 2) Szukamy elementów w DOM ---
            if soup.select("[id*='faq'], [class*='faq']"):
                found_faq.append({"url": url, "type": "dom"})

        status = "PASS" if found_faq else "FAIL"

        return {
            "name": "faq",
            "status": status,
            "metrics": {
                "checked_urls": checked,
                "faq_found": len(found_faq),
            },
            "samples": {"faq_locations": found_faq[:10]},
            "fix_hint": (
                "Dodaj FAQ na stronie głównej lub /kontakt. "
                "Najlepiej wdrożyć FAQPage schema w JSON-LD."
            )
        }

    except Exception as e:
        return {"name": "faq", "status": "ERROR", "error": str(e)}
