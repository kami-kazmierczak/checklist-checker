# checks/related_products.py
from urllib.parse import urljoin, urlsplit, urlunparse
from utils import fetch, get_soup
from config import PRODUCT_URL

# typowe selektory linków produktowych (WooCommerce i ogólne)
PRODUCT_LINK_SELECTORS = [
    ".related.products a",
    ".upsells.products a",
    ".cross-sells a",
    "a.woocommerce-LoopProduct__link",
    "[data-product-id] a",
    '[itemtype*=\"Product\" i] a',
    ".products a",
    ".product-grid a",
    ".product-card a",
]

BAD_FRAGMENTS = ("/cart", "/koszyk", "/checkout", "/moje-konto", "/account", "/login", "/wishlist","/blog")

def _is_abs(u: str) -> bool:
    try:
        p = urlsplit(u)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False

def _same_host(a: str, b: str) -> bool:
    return urlsplit(a).netloc.lower() == urlsplit(b).netloc.lower()

def _clean_url(u: str) -> str:
    """Zostaw tylko scheme/netloc/path (bez query/hash)."""
    p = urlsplit(u)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))

def _parent_dir(path: str) -> str:
    if not path.endswith("/"):
        path += "/"
    parts = [x for x in path.split("/") if x]
    if len(parts) <= 1:
        return "/"
    return "/" + "/".join(parts[:-1]) + "/"

def _target_url(root):
    if not PRODUCT_URL:
        return None
    return PRODUCT_URL if _is_abs(PRODUCT_URL) else urljoin(root, PRODUCT_URL)

def run(root):
    url = _target_url(root)
    if not url:
        return {
            "name": "related_products",
            "status": "SKIP",
            "metrics": {},
            "samples": {"note": "Brak PRODUCT_URL w config.py"},
            "fix_hint": "Ustaw PRODUCT_URL w config.py, aby sprawdzić powiązane linki."
        }

    print(f"[related_products] Checking links: {url}")

    try:
        r = fetch(url)
        soup = get_soup(r.text)

        base = _clean_url(url)
        base_path = urlsplit(base).path or "/"
        base_parent = _parent_dir(base_path)

        # 1) Linki z typowych selektorów produktowych
        hinted_links = []
        for sel in PRODUCT_LINK_SELECTORS:
            for el in soup.select(sel):
                if el.name == "a" and el.has_attr("href"):
                    hinted_links.append(el["href"])
                else:
                    for a in el.find_all("a", href=True):
                        hinted_links.append(a["href"])

        # 2) Wszystkie linki na stronie (fallback)
        all_links = [a.get("href") for a in soup.find_all("a", href=True)]
        raw_candidates = hinted_links + all_links

        # Normalizacja
        candidates = []
        seen = set()
        for href in raw_candidates:
            if not href or href.startswith("#"):
                continue
            absu = href if _is_abs(href) else urljoin(url, href)
            absu = _clean_url(absu)
            if absu not in seen:
                seen.add(absu)
                candidates.append(absu)

        # Filtracja – tylko inne produkty wewnętrzne
        product_links = []
        for u in candidates:
            if not _same_host(u, base):
                continue
            if u == base:
                continue
            upath = urlsplit(u).path or "/"
            if any(bad in upath.lower() for bad in BAD_FRAGMENTS):
                continue
            if upath.count("/") < 2:
                continue

            priority = 1 if upath.startswith(base_parent) else 2
            product_links.append((u, priority))

        # Sortowanie i deduplikacja
        product_links.sort(key=lambda x: (x[1], x[0]))
        uniq = []
        seen2 = set()
        for u, _prio in product_links:
            if u not in seen2:
                seen2.add(u)
                uniq.append(u)

        status = "PASS" if uniq else "FAIL"

        return {
            "name": "related_products",
            "status": status,
            "metrics": {
                "related_product_links": len(uniq),
                "same_bucket_parent": base_parent,
            },
            "samples": {
                "links": uniq[:12],
                "checked_url": base,
            },
            "fix_hint": (
                "Dodaj linki do innych kart produktów (np. sekcja 'Podobne produkty'), "
                "aby zwiększyć cross-selling i SEO (linkowanie wewnętrzne)."
            )
        }

    except Exception as e:
        return {"name": "related_products", "status": "ERROR", "error": str(e)}
