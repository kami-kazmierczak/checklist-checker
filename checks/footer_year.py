# checks/footer_year.py
import re
from datetime import datetime
from utils import fetch, get_soup

YEAR_RE = re.compile(r"(19|20)\d{2}")
RANGE_RE = re.compile(r"(?P<start>(19|20)\d{2})\s*[-–—]\s*(?P<end>(19|20)\d{2})")

FOOTER_SELECTORS = [
    "footer",              
    ".footer", "#footer",  
]

def _extract_text_candidates(soup):
    chunks = []
    found = False
    for sel in FOOTER_SELECTORS:
        for el in soup.select(sel):
            t = el.get_text(" ", strip=True)
            if t:
                chunks.append(t)
                found = True
    if not found:
        chunks.append(soup.get_text(" ", strip=True))
    # dorzuć zawartość <script> do heurystyki JS (np. getFullYear)
    scripts = " ".join((s.get_text(" ", strip=True) or "") for s in soup.find_all("script"))
    return chunks, scripts

def run(root):
    print(f"[footer_year] Checking: {root}")
    try:
        r = fetch(root)
        soup = get_soup(r.text)

        now_year = datetime.now().year
        texts, scripts_blob = _extract_text_candidates(soup)

        found_years = set()
        found_ranges = []
        context_hits = []

        for txt in texts:
            # najpierw zakresy "2016–2025"
            for m in RANGE_RE.finditer(txt):
                start = int(m.group("start"))
                end = int(m.group("end"))
                found_ranges.append({"start": start, "end": end})
                found_years.add(start); found_years.add(end)
                # krótki kontekst
                start_i = max(m.start()-40, 0); end_i = min(m.end()+40, len(txt))
                context_hits.append(txt[start_i:end_i])

            # pojedyńcze lata
            for m in YEAR_RE.finditer(txt):
                yr = int(m.group(0))
                found_years.add(yr)

        has_getfullyear = "getfullyear" in scripts_blob.lower()

        # Ocena
        status = "FAIL"
        reason = "brak roku w stopce/stronie"
        if found_years:
            if now_year in found_years or any(r.get("end") == now_year for r in found_ranges):
                status = "PASS"
                reason = "znaleziono aktualny rok"
            else:
                status = "WARN"
                reason = "brak aktualnego roku; znaleziono inne lata"

        return {
            "name": "footer_year",
            "status": status,
            "metrics": {
                "now_year": now_year,
                "unique_years_found": sorted(found_years),
                "ranges_found": found_ranges,
                "has_js_getFullYear": has_getfullyear,
                "reason": reason,
            },
            "samples": {
                "contexts": context_hits[:5],  
            },
            "fix_hint": (
                "Upewnij się, że w stopce wyświetla się aktualny rok (np. © 2016–{YYYY}). "
                "Możesz użyć JS: new Date().getFullYear() lub po stronie serwera (np. w szablonie)."
            )
        }

    except Exception as e:
        return {"name": "footer_year", "status": "ERROR", "error": str(e)}
