# checks/nofollow_links.py
import re
from utils import fetch, get_soup
from config import NOFOLLOW_KEYWORDS, NOFOLLOW_SOCIAL_KEYWORDS


def _norm(txt: str) -> str:
    """Normalizacja: małe litery, spacje zamiast -/_."""
    if not isinstance(txt, str):
        return ""
    t = txt.lower()
    t = t.replace("-", " ").replace("_", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _rel_tokens(el) -> set:
    rel = el.get("rel")
    if isinstance(rel, list):
        toks = rel
    elif isinstance(rel, str):
        toks = re.split(r"\s+", rel)
    else:
        toks = []
    return {t.lower().strip() for t in toks if t}


def _link_text_bundle(a) -> str:
    parts = [
        a.get_text(" ", strip=True),
        a.get("title", ""),
        a.get("aria-label", ""),
        a.get("href", ""),
    ]
    return _norm(" ".join(p for p in parts if p))


def _matches_keywords(bundle: str, keywords: list[str]) -> bool:
    b = _norm(bundle)
    for kw in keywords:
        if _norm(kw) in b:
            return True
    return False


def run(root):
    candidates, compliant, noncomp, errors = [], [], [], []

    try:
        r = fetch(root)
        soup = get_soup(r.text)

        for a in soup.find_all("a", href=True):
            bundle = _link_text_bundle(a)
            if not bundle:
                continue

            # sprawdzamy dwie listy keywordów
            if _matches_keywords(bundle, NOFOLLOW_KEYWORDS) or _matches_keywords(bundle, NOFOLLOW_SOCIAL_KEYWORDS):
                info = {
                    "href": a.get("href"),
                    "text": a.get_text(" ", strip=True)[:120],
                    "rel": " ".join(sorted(list(_rel_tokens(a)))) or "",
                }
                candidates.append(info)

                if "nofollow" in _rel_tokens(a):
                    compliant.append(info)
                else:
                    noncomp.append(info)

    except Exception as e:
        errors.append({"url": root, "error": str(e)})

    if noncomp:
        status = "FAIL"
    elif candidates:
        status = "PASS"
    else:
        status = "WARN"

    return {
        "name": "nofollow_links_check",
        "status": status,
        "metrics": {
            "candidates": len(candidates),
            "compliant": len(compliant),
            "noncompliant": len(noncomp),
            "errors": len(errors),
        },
        "samples": {
            "noncompliant": noncomp[:10],
            "compliant": compliant[:10],
            "preview": candidates[:10],
            "errors": errors[:5],
        },
        "fix_hint": (
            "Dodaj `rel=\"nofollow\"` dla linków zawierających słowa: "
            + ", ".join(NOFOLLOW_KEYWORDS + NOFOLLOW_SOCIAL_KEYWORDS)
        ),
    }
