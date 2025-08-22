# checks/blogpost_rating.py
import json
import re
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import BLOG_POST

def _is_abs(u: str) -> bool:
    try:
        p = urlsplit(u)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False

def _short(txt: str, n=120):
    if not isinstance(txt, str): return ""
    t = " ".join(txt.split())
    return (t[:n] + "…") if len(t) > n else t

# --- heurystyki wykrycia UI/widgetu ---
WIDGET_CLASS_HINTS = [
    "wp-postratings", "post-ratings", "rating", "ratings", "star-rating",
    "rating-stars", "stars", "score", "vote", "votes"
]
# Teksty typu "4.7/5", "4,5 / 5", "ocena: 4.5 z 5", itp.
RATING_TEXT_RE = re.compile(
    r"(ocen[ay]?\s*[:\-]?\s*)?(\d+[.,]?\d*)\s*/\s*5\b|(\b\d+[.,]?\d*\s*z\s*5\b)",
    re.I
)

def _find_jsonld_ratings(soup):
    found = []
    for s in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(s.string)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            # bezpośrednie AggregateRating
            if isinstance(it, dict) and it.get("@type") == "AggregateRating":
                found.append({
                    "type": "AggregateRating",
                    "ratingValue": it.get("ratingValue"),
                    "ratingCount": it.get("ratingCount") or it.get("reviewCount"),
                })
            # zagnieżdżone w Article/BlogPosting
            if isinstance(it, dict) and it.get("@type") in ("Article","BlogPosting","CreativeWork"):
                ar = it.get("aggregateRating")
                if isinstance(ar, dict) and ar.get("@type") == "AggregateRating":
                    found.append({
                        "type": "AggregateRating",
                        "ratingValue": ar.get("ratingValue"),
                        "ratingCount": ar.get("ratingCount") or ar.get("reviewCount"),
                    })
    return found

def _find_microdata_rdfa_ratings(soup):
    found = []
    # Microdata AggregateRating
    for agg in soup.select('[itemscope][itemtype*="AggregateRating" i]'):
        rv = None; rc = None
        rv_el = agg.find(attrs={"itemprop": "ratingValue"})
        rc_el = agg.find(attrs={"itemprop": "ratingCount"}) or agg.find(attrs={"itemprop": "reviewCount"})
        if rv_el:
            rv = rv_el.get("content") or rv_el.get_text(strip=True)
        if rc_el:
            rc = rc_el.get("content") or rc_el.get_text(strip=True)
        found.append({"type": "AggregateRating", "ratingValue": rv, "ratingCount": rc})

    # RDFa typeof AggregateRating
    for agg in soup.select('[typeof*="AggregateRating" i]'):
        rv = None; rc = None
        rv_el = agg.find(attrs={"property": "ratingValue"})
        rc_el = agg.find(attrs={"property": "ratingCount"}) or agg.find(attrs={"property": "reviewCount"})
        if rv_el:
            rv = rv_el.get("content") or rv_el.get_text(strip=True)
        if rc_el:
            rc = rc_el.get("content") or rc_el.get_text(strip=True)
        found.append({"type": "AggregateRating", "ratingValue": rv, "ratingCount": rc})
    return found

def _find_widget_ui(soup):
    widgets = []
    # po klasach/id
    for cls in WIDGET_CLASS_HINTS:
        for el in soup.select(f'.{cls}, [class*="{cls}"], #{cls}'):
            txt = el.get_text(" ", strip=True)
            if txt:
                widgets.append({"hint": cls, "text": _short(txt)})
            else:
                widgets.append({"hint": cls, "text": ""})

    # po aria-label z "rating"
    for el in soup.select('[aria-label*="rating" i], [aria-label*="ocena" i]'):
        widgets.append({"hint": "aria-label", "text": _short(el.get("aria-label", ""))})

    # po wystąpieniach wzorca tekstowego w całej stronie
    body_text = soup.get_text(" ", strip=True)
    for m in RATING_TEXT_RE.finditer(body_text):
        widgets.append({"hint": "text-pattern", "text": _short(m.group(0))})

    # deduplikacja
    seen = set(); unique = []
    for w in widgets:
        key = (w["hint"], w["text"])
        if key not in seen:
            unique.append(w); seen.add(key)
    return unique

def run(root):
    if not BLOG_POST:
        return {
            "name": "blogpost_rating",
            "status": "SKIP",
            "metrics": {},
            "samples": {"note": "Brak BLOG_POST w config.py"},
            "fix_hint": "Ustaw BLOG_POST (ścieżka względna lub pełny URL) wpisu do sprawdzenia."
        }

    url = BLOG_POST if _is_abs(BLOG_POST) else urljoin(root, BLOG_POST)
    print(f"[blogpost_rating] Checking {url}")

    try:
        r = fetch(url)
        soup = get_soup(r.text)

        jsonld = _find_jsonld_ratings(soup)
        micro  = _find_microdata_rdfa_ratings(soup)
        ui     = _find_widget_ui(soup)

        has_schema = bool(jsonld or micro)
        has_ui     = bool(ui)

        # Logika statusu: PASS jeśli cokolwiek wskazuje na rating; WARN jeśli tylko schema bez UI
        if has_schema and not has_ui:
            status = "WARN"
        elif has_schema or has_ui:
            status = "PASS"
        else:
            status = "FAIL"

        return {
            "name": "blogpost_rating",
            "status": status,
            "metrics": {
                "has_schema": has_schema,
                "has_ui": has_ui,
                "jsonld_count": len(jsonld),
                "microdata_rdfa_count": len(micro),
                "ui_hints": len(ui),
                "checked_url": url
            },
            "samples": {
                "jsonld": jsonld[:5],
                "microdata_rdfa": micro[:5],
                "ui": ui[:10]
            },
            "fix_hint": (
                "Dodaj system ocen (widget gwiazdkowy + dane strukturalne AggregateRating). "
                "Przykład JSON‑LD: Article/BlogPosting z polem aggregateRating { ratingValue, ratingCount }."
            )
        }

    except Exception as e:
        return {"name": "blogpost_rating", "status": "ERROR", "error": str(e)}
