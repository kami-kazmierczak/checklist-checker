# checks/home_latest_posts.py
import re
from urllib.parse import urljoin, urlsplit, urlunparse
from utils import fetch, get_soup

# Tekstowe hinty na sekcję „ostatnie wpisy”
SECTION_HINTS = [
    "ostatnie", "najnowsze", "z bloga", "blog", "aktualności", "newsy",
    "recent", "latest", "from the blog", "our blog", "articles", "wpisy", "artykuły"
]

# Selektory często używane dla list wpisów na home
POST_LIST_SELECTORS = [
    ".recent-posts a",
    ".latest-posts a",
    ".home-blog a",
    ".blog-posts a",
    ".posts a",
    ".article-list a",
    ".news a",
]

# Heurystyki odrzucania nie‑postowych linków
BAD_FRAGMENTS = (
    "/category/", "/tag/", "/author/", "/page/", "/strona/",
    "/cart", "/checkout", "/account", "/moje-konto", "/kontakt", "/contact"
)

# Wzorce „pojedynczego wpisu”
DATE_IN_PATH = re.compile(r"/20\d{2}/\d{1,2}/")     # /2025/08/...
SLUGGY = re.compile(r"/[a-z0-9\-]{4,}/?$", re.I)    # /jakis-slug/


def _is_abs(u: str) -> bool:
    try:
        p = urlsplit(u)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False

def _same_host(a: str, b: str) -> bool:
    return urlsplit(a).netloc.lower() == urlsplit(b).netloc.lower()

def _clean_url(u: str) -> str:
    p = urlsplit(u)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))

def _looks_like_post(path: str) -> bool:
    """Czy ścieżka wygląda na pojedynczy wpis (a nie kategorie/landing)?"""
    p = path.lower()
    if any(x in p for x in BAD_FRAGMENTS):
        return False
    # często blog jest pod /blog/... – post ma dodatkowy segment (slug) lub datę
    if DATE_IN_PATH.search(p):
        return True
    # slug na końcu (nie /blog/ samo w sobie)
    if SLUGGY.search(p) and not p.rstrip("/").endswith("/blog"):
        return True
    return False


def run(root):
    print(f"[home_latest_posts] Checking homepage: {root}")

    try:
        r = fetch(root)
        soup = get_soup(r.text)

        # 1) Sekcje po hintach i linki w nich
        section_links = []
        found_sections = 0
        for hint in SECTION_HINTS:
            elems = soup.find_all(
                lambda tag: tag.name in ["section", "div", "h2", "h3", "h4"]
                and hint in (tag.get_text() or "").lower()
            )
            for el in elems:
                found_sections += 1
                for a in el.find_all("a", href=True):
                    section_links.append(a["href"])

        # 2) Linki z typowych selektorów list wpisów
        hinted_links = []
        for sel in POST_LIST_SELECTORS:
            for el in soup.select(sel):
                if el.name == "a" and el.has_attr("href"):
                    hinted_links.append(el["href"])
                else:
                    for a in el.find_all("a", href=True):
                        hinted_links.append(a["href"])

        # 3) Fallback – wszystkie linki na stronie (na wszelki wypadek)
        all_links = [a.get("href") for a in soup.find_all("a", href=True)]

        # Normalizacja do absolutnych + deduplikacja
        raw = section_links + hinted_links + all_links
        abs_clean = []
        seen = set()
        for href in raw:
            if not href or href.startswith("#"):
                continue
            absu = href if _is_abs(href) else urljoin(root, href)
            absu = _clean_url(absu)
            if absu not in seen:
                seen.add(absu)
                abs_clean.append(absu)

        # Filtracja: tylko wewnętrzne i wyglądające na pojedynczy wpis
        post_links = []
        for u in abs_clean:
            if not _same_host(u, root):
                continue
            path = urlsplit(u).path or "/"
            if _looks_like_post(path):
                post_links.append(u)

        # Prosty próg: PASS jeśli >=3 posty, WARN jeśli 1-2, FAIL jeśli 0
        unique_posts = post_links[:30]
        if len(unique_posts) >= 3:
            status = "PASS"
        elif len(unique_posts) > 0:
            status = "WARN"
        else:
            status = "FAIL"

        return {
            "name": "home_latest_posts",
            "status": status,
            "metrics": {
                "sections_detected": found_sections,
                "post_links_detected": len(unique_posts),
            },
            "samples": {
                "links": unique_posts[:10],
            },
            "fix_hint": (
                "Dodaj na stronie głównej sekcję z ostatnimi wpisami blogowymi (3+ karty) "
                "z linkami do pojedynczych artykułów."
            ),
        }

    except Exception as e:
        return {"name": "home_latest_posts", "status": "ERROR", "error": str(e)}
