# checks/pagination_title.py
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import SHOP_PAGE, BLOG_PAGE

def _is_abs(u: str) -> bool:
    try:
        p = urlsplit(u)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False

def _target_url(root):
    """Zwróć pełny URL do sprawdzenia paginacji: SHOP_PAGE > BLOG_PAGE, inaczej SKIP."""
    if SHOP_PAGE:
        base = SHOP_PAGE if _is_abs(SHOP_PAGE) else urljoin(root, SHOP_PAGE)
        return base, "shop"
    if BLOG_PAGE:
        base = BLOG_PAGE if _is_abs(BLOG_PAGE) else urljoin(root, BLOG_PAGE)
        return base, "blog"
    return None, None

def run(root):
    url, page_type = _target_url(root)
    if not url:
        return {
            "name": "pagination_title",
            "status": "SKIP",
            "metrics": {},
            "samples": {"note": "Brak SHOP_PAGE i BLOG_PAGE w config.py"},
            "fix_hint": "Ustaw SHOP_PAGE lub BLOG_PAGE w config.py, aby sprawdzić tytuły stron paginacyjnych."
        }

    # spróbujemy wymusić stronę 2 – zwykle /page/2/ działa na WP/WooCommerce
    paginated_url = url.rstrip("/") + "/page/2/"
    print(f"[pagination_title] Checking {page_type}: {paginated_url}")

    try:
        r = fetch(paginated_url)
        soup = get_soup(r.text)

        title = (soup.title.string or "").strip() if soup.title else ""

        has_number = any(x in title.lower() for x in ["page", "strona", "página", "seite"]) or \
                     any(ch.isdigit() for ch in title)

        status = "PASS" if has_number else "FAIL"

        return {
            "name": "pagination_title",
            "status": status,
            "metrics": {
                "checked_url": paginated_url,
                "page_type": page_type,
                "title_found": title,
                "has_number": has_number,
            },
            "samples": {"title": title},
            "fix_hint": "Upewnij się, że w <title> stron paginacyjnych pojawia się numer strony (np. 'Strona 2 z 10')."
        }

    except Exception as e:
        return {"name": "pagination_title", "status": "ERROR", "error": str(e)}
