# checks/error_page_404.py
from urllib.parse import urljoin
from utils import fetch, get_soup

ERROR_HINTS = [
    "404", "nie znaleziono", "page not found", "not found", "oops", "błąd", "error"
]

def run(root):
    test_url = urljoin(root.rstrip("/") + "/", "nonexistent-seo-audit-check-404-page")
    print(f"[error_page_404] Checking: {test_url}")

    try:
        r = fetch(test_url)
        status_code = r.status_code
        text = (r.text or "").lower()
        soup = get_soup(r.text)

        # Heurystyka 1: sprawdzamy kod odpowiedzi
        if status_code != 404:
            return {
                "name": "error_page_404",
                "status": "FAIL",
                "metrics": {"http_status": status_code},
                "samples": {"url_tested": test_url},
                "fix_hint": "Serwer nie zwraca HTTP 404 dla nieistniejących stron (tylko {})."\
                            " Skonfiguruj poprawną stronę błędu 404.".format(status_code),
            }

        # Heurystyka 2: szukamy fraz w treści
        found_hint = None
        for h in ERROR_HINTS:
            if h in text:
                found_hint = h
                break

        # Heurystyka 3: sprawdź długość treści (aby nie była pusta/redirect)
        is_too_short = len(text.strip()) < 100

        if found_hint and not is_too_short:
            status = "PASS"
        else:
            status = "WARN"

        return {
            "name": "error_page_404",
            "status": status,
            "metrics": {
                "http_status": status_code,
                "found_hint": found_hint,
                "content_length": len(text),
            },
            "samples": {
                "url_tested": test_url,
                "title": soup.title.string if soup.title else None,
            },
            "fix_hint": (
                "Upewnij się, że strona 404 ma własny layout, treść i komunikat "
                "dla użytkownika (np. 'Strona nie została znaleziona')."
            ),
        }

    except Exception as e:
        return {"name": "error_page_404", "status": "ERROR", "error": str(e)}
