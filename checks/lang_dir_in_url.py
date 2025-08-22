# checks/lang_dir_in_url.py
import re
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup

# najczęstsze kody językowe (ISO 639-1)
LANG_CODES = [
    "pl", "en", "de", "fr", "es", "it", "pt", "ru", "uk", "cs", "sk", "ro", "hu",
    "nl", "sv", "no", "da", "fi", "tr", "el", "bg", "hr", "sr", "sl", "lt", "lv", "et",
]

_lang_re = re.compile(r"/(" + "|".join(LANG_CODES) + r")(/|$)", re.I)

def run(root):
    try:
        r = fetch(root)
        soup = get_soup(r.text)

        # zbieramy wszystkie linki wewnętrzne
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        links = [urljoin(root, href) for href in links]
        flagged = []
        for href in links:
            path = urlsplit(href).path
            if _lang_re.search(path):
                flagged.append(href)

        status = "PASS"
        if flagged:
            status = "FAIL"

        return {
            "name": "lang_dir_in_url",
            "status": status,
            "metrics": {
                "links_checked": len(links),
                "with_lang_dir": len(flagged),
            },
            "samples": {"with_lang_dir": flagged[:10]},
            "fix_hint": (
                "Usuń katalogi językowe z URL-i (np. /pl/, /en/). "
                "Zamiast tego użyj subdomen (pl.example.com) lub hreflang w head."
            )
        }

    except Exception as e:
        return {"name": "lang_dir_in_url", "status": "ERROR", "error": str(e)}
