from utils import fetch, extract_basic_meta, canonicalize_compare, throttle, collect_urls
from config import CRAWL_LIMIT

def run(root):
    urls = collect_urls(root, limit=CRAWL_LIMIT)

    not_self = []
    missing = []

    for u in urls:
        try:
            r = fetch(u, allow_redirects=True)
            final_url = r.url
            _, _, _, canonical = extract_basic_meta(r.text)
            if not canonical:
                missing.append(u)
            else:
                if not canonicalize_compare(final_url, canonical):
                    not_self.append({"url": u, "final": final_url, "canonical": canonical})
        except:
            continue
        throttle()

    status = "PASS" if not missing and not not_self else "FAIL"
    return {
        "name": "canonical_self_reference",
        "status": status,
        "metrics": {"checked_pages": len(urls), "missing": len(missing), "mismatch": len(not_self)},
        "samples": {"missing": missing[:10], "mismatch": not_self[:10]},
        "fix_hint": "Ustaw self-referencing canonical na każdej unikalnej stronie. Unikaj kanoników wskazujących na inną wersję URL."
    }
