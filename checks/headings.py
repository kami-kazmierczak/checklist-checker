from bs4 import BeautifulSoup
from utils import fetch, throttle, collect_urls
from config import CRAWL_LIMIT

def run(root):
    urls = collect_urls(root, limit=CRAWL_LIMIT)

    over_h1 = []
    hidden_h1 = []

    for u in urls:
        try:
            r = fetch(u)
            soup = BeautifulSoup(r.text, "lxml")
            h1s = soup.find_all("h1")
            if len(h1s) > 1:
                over_h1.append(u)
            for h in h1s:
                style = (h.get("style") or "").lower()
                classes = " ".join(h.get("class", [])).lower()
                if "display:none" in style or "sr-only" in classes or "visually-hidden" in classes:
                    hidden_h1.append(u)
                    break
        except:
            continue
        throttle()

    status = "PASS" if not over_h1 and not hidden_h1 else "FAIL"
    return {
        "name": "headings_h1",
        "status": status,
        "metrics": {"checked_pages": len(urls), "too_many_h1": len(over_h1), "hidden_h1_pages": len(hidden_h1)},
        "samples": {"too_many_h1": over_h1[:10], "hidden_h1_pages": hidden_h1[:10]},
        "fix_hint": "Na każdej stronie powinien być dokładnie jeden widoczny H1."
    }
