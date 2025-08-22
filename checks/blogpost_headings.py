# checks/blogpost_headings.py
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import BLOG_POST

def _is_absolute(u: str) -> bool:
    try:
        return bool(urlsplit(u).scheme and urlsplit(u).netloc)
    except Exception:
        return False

def run(root):
    # zbuduj pełny URL blogposta
    if not BLOG_POST:
        return {
            "name": "blogpost_headings",
            "status": "SKIP",
            "metrics": {},
            "samples": {},
            "fix_hint": "Nie ustawiono BLOG_POST w config.py"
        }

    url = BLOG_POST if _is_absolute(BLOG_POST) else urljoin(root, BLOG_POST)
    print(f"[blogpost_headings] Checking {url}")

    try:
        r = fetch(url)
        soup = get_soup(r.text)

        headings = []
        for level in range(1, 7):
            for h in soup.find_all(f"h{level}"):
                text = h.get_text(strip=True)[:80]
                headings.append((level, text))

        # sprawdzanie kolejności
        errors = []
        prev_level = 0
        for (lvl, txt) in headings:
            if prev_level == 0:
                if lvl != 1:
                    errors.append(f"Pierwszy nagłówek nie jest H1 (jest H{lvl}: '{txt}')")
            else:
                if lvl > prev_level + 1:
                    errors.append(f"Przeskok z H{prev_level} do H{lvl} (nagłówek: '{txt}')")
            prev_level = lvl

        status = "PASS" if not errors else "FAIL"

        return {
            "name": "blogpost_headings",
            "status": status,
            "metrics": {
                "headings_found": len(headings),
                "errors_count": len(errors)
            },
            "samples": {
                "headings": [f"H{lvl}: {txt}" for lvl, txt in headings[:20]],
                "errors": errors
            },
            "fix_hint": "Utrzymuj logiczną strukturę nagłówków (H1 → H2 → H3…). Unikaj przeskoków poziomów."
        }

    except Exception as e:
        return {"name": "blogpost_headings", "status": "ERROR", "error": str(e)}
