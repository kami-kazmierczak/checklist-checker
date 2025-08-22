# checks/contact_form_under_post.py
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import BLOG_POST

def _is_abs(u: str) -> bool:
    try:
        p = urlsplit(u)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False

def _target_url(root):
    if BLOG_POST:
        return BLOG_POST if _is_abs(BLOG_POST) else urljoin(root, BLOG_POST)
    return None

def run(root):
    url = _target_url(root)
    if not url:
        return {
            "name": "contact_form_under_post",
            "status": "SKIP",
            "metrics": {},
            "samples": {"note": "Brak BLOG_POST w config.py"},
            "fix_hint": "Ustaw BLOG_POST w config.py, aby sprawdzić formularz."
        }

    print(f"[contact_form_under_post] Checking: {url}")

    try:
        r = fetch(url)
        soup = get_soup(r.text)

        forms = soup.find_all("form")
        total_forms = len(forms)

        # heurystyki na formularz kontaktowy
        contact_like = []
        for f in forms:
            txt = f.get_text(" ", strip=True).lower()
            if "email" in txt or "wiadomość" in txt or "message" in txt or "kontakt" in txt:
                contact_like.append({"form_html": str(f)[:180]})

        status = "PASS" if contact_like else "FAIL"

        return {
            "name": "contact_form_under_post",
            "status": status,
            "metrics": {
                "checked_url": url,
                "total_forms_found": total_forms,
                "contact_forms_detected": len(contact_like),
            },
            "samples": {"contact_forms": contact_like[:5]},
            "fix_hint": (
                "Dodaj formularz kontaktowy pod blogpostem. "
                "Użyj etykiet typu Email, Wiadomość, aby było jasne dla użytkowników i botów."
            )
        }

    except Exception as e:
        return {"name": "contact_form_under_post", "status": "ERROR", "error": str(e)}
