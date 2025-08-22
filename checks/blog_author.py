# checks/blog_author.py
import json
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import BLOG_POST

def _is_abs(u: str) -> bool:
    try:
        p = urlsplit(u)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False

def _text(el):
    return (el.get_text(" ", strip=True) if el else "").strip()

def _add(name_set, val):
    v = (val or "").strip()
    if v:
        name_set.add(v)

def _jsonld_authors(soup):
    names = set()
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(tag.string)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict):
                continue
            # author może być na poziomie Article / BlogPosting lub zagnieżdżony
            for node in (it, *([it.get("mainEntityOfPage")] if isinstance(it.get("mainEntityOfPage"), dict) else [])):
                if not isinstance(node, dict):
                    continue
                author = node.get("author")
                if not author:
                    continue
                if isinstance(author, list):
                    for a in author:
                        if isinstance(a, dict):
                            _add(names, a.get("name"))
                        else:
                            _add(names, str(a))
                elif isinstance(author, dict):
                    _add(names, author.get("name"))
                else:
                    _add(names, str(author))
    return names

def run(root):
    if not BLOG_POST:
        return {
            "name": "blog_author",
            "status": "SKIP",
            "metrics": {},
            "samples": {"note": "Brak BLOG_POST w config.py"},
            "fix_hint": "Ustaw BLOG_POST (ścieżka względna lub pełny URL) wpisu do sprawdzenia."
        }

    url = BLOG_POST if _is_abs(BLOG_POST) else urljoin(root, BLOG_POST)
    print(f"[blog_author] Checking {url}")

    try:
        r = fetch(url)
        soup = get_soup(r.text)

        authors = set()

        # 1) <meta name="author" content="...">
        for m in soup.find_all("meta", attrs={"name": "author"}):
            _add(authors, m.get("content"))

        # 2) rel="author"
        for a in soup.find_all("a", rel=True):
            rels = [x.lower() for x in (a.get("rel") if isinstance(a.get("rel"), list) else str(a.get("rel")).split())]
            if "author" in rels:
                _add(authors, _text(a))

        # 3) typowe klasy/byline
        candidates = soup.select(
            '.author, .post-author, .byline, .entry-author, a[rel~="author"], [itemprop="author"]'
        )
        for el in candidates:
            # jeśli to microdata itemprop=author i posiada itemprop=name w środku
            name_el = el.find(attrs={"itemprop": "name"})
            if name_el:
                _add(authors, _text(name_el))
            else:
                _add(authors, _text(el))

        # 4) Microdata: itemprop="author" może być też w meta
        for meta in soup.select('meta[itemprop="author"]'):
            _add(authors, meta.get("content"))

        # 5) JSON-LD (Article/BlogPosting/CreativeWork z polem author)
        authors |= _jsonld_authors(soup)

        status = "PASS" if authors else "FAIL"

        return {
            "name": "blog_author",
            "status": status,
            "metrics": {
                "authors_found": len(authors)
            },
            "samples": {
                "authors": sorted(list(authors))[:10],
                "checked_url": url
            },
            "fix_hint": (
                "Dodaj informację o autorze: meta[name=author], widoczną sekcję z autorem, "
                "oraz/lub JSON-LD (Article/BlogPosting z polem author.name)."
            )
        }

    except Exception as e:
        return {"name": "blog_author", "status": "ERROR", "error": str(e)}
