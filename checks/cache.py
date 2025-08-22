# checks/cache.py
from utils import fetch

CACHE_HEADERS = [
    "x-cache",
    "x-cache-status",
    "cf-cache-status",
    "age",
    "x-litespeed-cache",
    "x-varnish",
]

def run(root):
    print(f"[cache_headers] Checking cache headers for: {root}")
    try:
        r = fetch(root)
        headers = {k.lower(): v for k, v in r.headers.items()}

        found = {}
        for h in CACHE_HEADERS:
            if h in headers:
                found[h] = headers[h]

        status = "PASS" if found else "FAIL"

        return {
            "name": "cache_headers",
            "status": status,
            "metrics": {
                "headers_checked": CACHE_HEADERS,
                "headers_found": list(found.keys()),
            },
            "samples": found,
            "fix_hint": (
                "Brak nagłówków cache sugeruje, że strona nie korzysta z cache na serwerze/CDN. "
                "Włącz caching (np. LiteSpeed Cache, WP Rocket, Cloudflare), aby przyspieszyć stronę."
            )
        }
    except Exception as e:
        return {"name": "cache_headers", "status": "ERROR", "error": str(e)}
