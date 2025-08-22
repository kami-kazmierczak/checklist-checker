import json
from utils import fetch, get_soup

def run(root):
    try:
        r = fetch(root)
        soup = get_soup(r.text)
        has_html_breadcrumbs = bool(soup.select('[aria-label*="breadcrumb" i], nav.breadcrumb, .breadcrumb'))
        has_jsonld = False
        for s in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(s.string)
                items = data if isinstance(data, list) else [data]
                if any(isinstance(i, dict) and i.get("@type") == "BreadcrumbList" for i in items):
                    has_jsonld = True
                    break
            except:
                continue
        status = "PASS" if (has_html_breadcrumbs or has_jsonld) else "FAIL"
        return {
            "name": "breadcrumbs_presence",
            "status": status,
            "metrics": {"html": has_html_breadcrumbs, "jsonld": has_jsonld},
            "samples": {},
            "fix_hint": "Dodaj breadcrumbs (HTML i/lub JSON-LD `BreadcrumbList`) dla lepszej nawigacji i rich results."
        }
    except Exception as e:
        return {"name": "breadcrumbs_presence", "status": "ERROR", "error": str(e)}
