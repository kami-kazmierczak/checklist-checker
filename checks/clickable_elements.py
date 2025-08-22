# checks/clickable_elements.py
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import CLICKABLE_PATHS

def _is_absolute(u: str) -> bool:
    try:
        return bool(urlsplit(u).scheme and urlsplit(u).netloc)
    except Exception:
        return False

def run(root):
    targets = []
    if not CLICKABLE_PATHS:
        targets = [root]
    else:
        for p in CLICKABLE_PATHS:
            full = p if _is_absolute(p) else urljoin(root, p)
            targets.append(full)

    found_tel = []
    found_mail = []
    errors = []

    print(f"[clickable] Targets: {len(targets)}")

    for url in targets:
        try:
            r = fetch(url)
            soup = get_soup(r.text)
            for a in soup.find_all("a", href=True):
                href = a["href"].strip().lower()
                if href.startswith("tel:"):
                    found_tel.append({"url": url, "href": href})
                elif href.startswith("mailto:"):
                    found_mail.append({"url": url, "href": href})
        except Exception as e:
            errors.append({"url": url, "error": str(e)})

    status = "PASS" if (found_tel or found_mail) else "FAIL"

    return {
        "name": "clickable_elements",
        "status": status,
        "metrics": {
            "checked_pages": len(targets),
            "tel_links": len(found_tel),
            "mailto_links": len(found_mail),
            "errors": len(errors),
        },
        "samples": {
            "tel": found_tel[:10],
            "mailto": found_mail[:10],
            "errors": errors[:5],
        },
        "fix_hint": "Upewnij się, że numer telefonu i adres e-mail są podane jako klikalne linki (`tel:` / `mailto:`)."
    }
