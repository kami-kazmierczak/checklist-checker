# checks/blog_exists.py
from utils import fetch, get_soup
from config import BLOG_HINTS

def run(root):
    print(f"[blog_exists] Checking blog presence on: {root}")
    try:
        r = fetch(root)
        soup = get_soup(r.text)

        found_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            text = (a.get_text() or "").lower()

            for hint in BLOG_HINTS:
                if hint in href or hint in text:
                    found_links.append({"href": href, "text": text.strip()})
                    break

        status = "PASS" if found_links else "FAIL"

        return {
            "name": "blog_exists",
            "status": status,
            "metrics": {"found_links": len(found_links)},
            "samples": found_links[:10],
            "fix_hint": (
                "Brak sekcji bloga — rozważ dodanie bloga (np. /blog/), aby zwiększyć widoczność w SEO "
                "i publikować treści wspierające słowa kluczowe."
            )
        }

    except Exception as e:
        return {"name": "blog_exists", "status": "ERROR", "error": str(e)}
