# checks/schema_pages.py
import json
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import SCHEMA_EXTRA_PATHS

def _is_absolute(u: str) -> bool:
    try:
        return bool(urlsplit(u).scheme and urlsplit(u).netloc)
    except Exception:
        return False

def _page_schema_types(url: str):
    """Zwraca listę typów schema znalezionych na pojedynczej stronie."""
    found = []
    try:
        r = fetch(url)
        soup = get_soup(r.text)

        # JSON-LD
        for s in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(s.string)
                items = data if isinstance(data, list) else [data]
                for i in items:
                    if isinstance(i, dict):
                        t = i.get("@type")
                        if isinstance(t, list):
                            found.extend([str(x) for x in t])
                        elif t:
                            found.append(str(t))
            except Exception:
                continue

        # Microdata
        for tag in soup.find_all(attrs={"itemscope": True}):
            t = tag.get("itemtype")
            if t:
                found.append(str(t))

        # RDFa
        for tag in soup.find_all(attrs={"typeof": True}):
            found.append(str(tag["typeof"]))

    except Exception as e:
        return {"error": str(e), "types": []}

    # deduplikacja przy zachowaniu prostoty
    types_unique = sorted(set(found))
    return {"error": None, "types": types_unique}

def run(root):
    # Zbuduj listę stron do sprawdzenia: home + dodatkowe z configa
    targets = [root]
    for p in SCHEMA_EXTRA_PATHS:
        full = p if _is_absolute(p) else urljoin(root, p)
        if full not in targets:
            targets.append(full)

    results_per_page = {}
    pages_with_schema = []
    errors = 0

    print(f"[schema] Targets: {len(targets)}")
    for i, url in enumerate(targets, start=1):
        info = _page_schema_types(url)
        results_per_page[url] = info
        if info["error"]:
            errors += 1
            print(f"[schema] {i}/{len(targets)} {url} -> ERROR ({info['error']})")
        else:
            has = bool(info["types"])
            print(f"[schema] {i}/{len(targets)} {url} -> {'FOUND' if has else 'NONE'} {info['types']}")
            if has:
                pages_with_schema.append(url)

    home_has_schema = bool(results_per_page[root]["types"]) if root in results_per_page else False
    any_schema = bool(pages_with_schema)

    if home_has_schema:
        status = "PASS"
    elif any_schema:
        status = "WARN"  # brak na home, ale jest na innych
    else:
        status = "FAIL"

    return {
        "name": "schema_pages",
        "status": status,
        "metrics": {
            "checked_pages": len(targets),
            "home_has_schema": home_has_schema,
            "pages_with_schema": len(pages_with_schema),
            "errors": errors
        },
        "samples": {
            "pages_with_schema": pages_with_schema[:10],
            "per_page_types": results_per_page  # map: url -> {error, types[]}
        },
        "fix_hint": (
            "Na stronie głównej dodaj dane strukturalne (np. Organization, Website). "
            "Na podstronach rozważ: BreadcrumbList, Article/BlogPosting, Product, FAQPage."
        )
    }
