from utils import fetch, extract_basic_meta, throttle
from config import CRAWL_LIMIT
from utils import find_sitemap_urls, iter_urls_from_sitemap, collect_urls

def run(root):
    urls = collect_urls(root, limit=CRAWL_LIMIT)
    print(f"[meta_tags] URLs to scan: {len(urls)} (limit={CRAWL_LIMIT})")

    missing_title = []
    missing_desc = []

    for u in urls:
        try:
            r = fetch(u)
            soup, title, desc, _ = extract_basic_meta(r.text)
            print(f"Checked {u}: title='{title}' desc='{desc}\n'")
            if not title:
                missing_title.append(u)
            if not desc:
                missing_desc.append(u)
        except Exception:
            continue
        throttle()

    status = "PASS" if not missing_title and not missing_desc else "FAIL"
    return {
        "name": "meta_tags_coverage",
        "status": status,
        "metrics": {
            "pages_scanned": len(urls),
            "missing_title": len(missing_title),
            "missing_description": len(missing_desc)
        },
        "samples": {
            "missing_title": missing_title[:10],
            "missing_description": missing_desc[:10]
        },
        "fix_hint": "Uzupełnij brakujące tytuły i meta description; w sklepach użyj szablonów wtyczki SEO."
    }
