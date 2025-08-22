# checks/alt_tags.py
import re
from urllib.parse import urljoin, urlsplit
from utils import fetch, get_soup
from config import PRODUCT_URL, BLOG_POST

# Heurystyki wykrywania "auto-altów"
AUTO_ALT_PATTERNS = [
    r"^img\d*$", r"^image\d*$", r"^zdj(ę|e)cie\d*$", r"^photo\d*$", r"^picture\d*$",
    r"^dsc[_-]?\d+$", r"^img[_-]?\d+$", r"^\d{6,}$",      # numery / timestampy
    r"^[a-f0-9]{8,}$",                                   # heksy/hashe
]

# Alt będący nazwą pliku
FILE_NAMEY = [r"^.*\.(jpg|jpeg|png|webp|gif|avif|svg)$"]

# Wzorce śmieciowych/technicznych obrazków do pominięcia (bez configa)
NOISE_SRC_PATTERNS = [
    r"^data:image/",                # wszystkie data-uri (svg, gif, png)
    r"\.svg($|\?)",                 # pliki SVG
    r"loading(\.|\b)", r"spinner",  # loadery/spinnery
    r"/wp-postratings/",            # wtyczkowe gwiazdki itp.
    r"/flags?/", r"\bflag[s]?\b",   # flagi
    r"\bstar(\.|\b)", r"\brating\b",
    r"\bchevron\b", r"\barrow\b", r"\bhamburger\b", r"\bcaret\b",
    r"\bfavicon\b", r"\bemoji\b", r"\bsprite\b",
    r"(?:^|/)(?:pixel|tracker|1x1)(?:\.|/)",  # 1x1 i trackery
]
NOISE_CLASS_PATTERNS = [
    r"\bicon\b", r"\bicons?\b", r"\bflag\b", r"\brating\b", r"\bstar\b",
    r"\bspinner\b", r"\bloading\b", r"\bchevron\b", r"\barrow\b"
]

_auto_alt_re = [re.compile(p, re.I) for p in AUTO_ALT_PATTERNS]
_file_name_re = [re.compile(p, re.I) for p in FILE_NAMEY]
_noise_src_re = [re.compile(p, re.I) for p in NOISE_SRC_PATTERNS]
_noise_cls_re = [re.compile(p, re.I) for p in NOISE_CLASS_PATTERNS]


def _is_abs(u: str) -> bool:
    try:
        p = urlsplit(u)
        return bool(p.scheme and p.netloc)
    except Exception:
        return False


def _target_url(root):
    """Zwraca pełny URL do sprawdzenia: produkt > blogpost, inaczej SKIP."""
    if PRODUCT_URL:
        return PRODUCT_URL if _is_abs(PRODUCT_URL) else urljoin(root, PRODUCT_URL), "product"
    if BLOG_POST:
        return BLOG_POST if _is_abs(BLOG_POST) else urljoin(root, BLOG_POST), "blogpost"
    return None, None


def _is_decorative(img):
    # alt="" jest OK tylko dla obrazów czysto dekoracyjnych
    role = (img.get("role") or "").lower()
    aria_hidden = (img.get("aria-hidden") or "").lower()
    return role in ("presentation", "none") or aria_hidden in ("true", "1")


def _looks_auto_alt(alt: str, src_like: str) -> bool:
    if not alt:
        return False
    a = alt.strip().lower()

    if any(r.search(a) for r in _auto_alt_re):
        return True

    base = (src_like or "").rsplit("/", 1)[-1]
    base = re.sub(r"\.(jpg|jpeg|png|webp|gif|avif|svg)$", "", base, flags=re.I)
    base = base.lower().replace("_", " ").replace("-", " ").strip()
    a_norm = a.replace("_", " ").replace("-", " ").strip()

    if base and (a_norm == base or any(r.match(alt) for r in _file_name_re)):
        return True
    return False


def _is_noise_image(img, src_low: str) -> bool:
    """Pomija ikony/trackery/loadery/inline data itp. — bez dodatkowego configa."""
    if not src_low:
        return False

    # 1) patterny po adresie
    if any(r.search(src_low) for r in _noise_src_re):
        return True

    # 2) bardzo małe piksele (jeśli width/height atrybuty są znane)
    try:
        w = int(img.get("width") or 0)
        h = int(img.get("height") or 0)
        if (w and w <= 2) or (h and h <= 2):
            return True
    except Exception:
        pass

    # 3) po klasach (np. "icon", "flag", "spinner")
    try:
        cls = " ".join(img.get("class", [])) if isinstance(img.get("class"), list) else (img.get("class") or "")
        if any(r.search(cls) for r in _noise_cls_re):
            return True
    except Exception:
        pass

    return False


def run(root):
    url, page_type = _target_url(root)
    if not url:
        return {
            "name": "alt_tags",
            "status": "SKIP",
            "metrics": {},
            "samples": {"note": "Brak PRODUCT_URL i BLOG_POST w config.py"},
            "fix_hint": "Ustaw PRODUCT_URL lub BLOG_POST w config.py, aby sprawdzić alty."
        }

    print(f"[alt_tags] Checking {page_type}: {url}")

    try:
        r = fetch(url)
        soup = get_soup(r.text)

        imgs = soup.find_all("img")
        total = len(imgs)

        missing_alt = []       # brak atrybutu alt
        empty_alt = []         # alt="" (i NIE dekoracyjny)
        auto_alt  = []         # alt wygląda na automatyczny/bezwartościowy
        skipped   = 0          # pominięte przez filtry "noise"

        for img in imgs:
            src = img.get("src") or img.get("data-src") or img.get("data-lazy") or ""
            s_low = (src or "").strip().lower()

            # ❗️Pomijamy SVG, data-uri, loadery/spinnery, flagi, piksele, itp.
            if _is_noise_image(img, s_low):
                skipped += 1
                continue

            alt = img.get("alt")

            # brak alt jako atrybut
            if alt is None:
                missing_alt.append({"src": src[:140]})
                continue

            alt_txt = (alt or "").strip()

            # alt="" — akceptujemy tylko, jeśli obraz jest dekoracyjny
            if alt_txt == "":
                if not _is_decorative(img):
                    empty_alt.append({"src": src[:140]})
                continue

            # heurystyka: alt „automatyczny”
            if _looks_auto_alt(alt_txt, s_low):
                auto_alt.append({"src": src[:140], "alt": alt_txt[:140]})

        # Ustal status
        if missing_alt or empty_alt:
            status = "FAIL"
        elif auto_alt:
            status = "WARN"
        else:
            status = "PASS"

        return {
            "name": "alt_tags",
            "status": status,
            "metrics": {
                "checked_url": url,
                "page_type": page_type,
                "images_found": total,
                "skipped_noise": skipped,
                "missing_alt": len(missing_alt),
                "empty_alt_non_decorative": len(empty_alt),
                "auto_alt_like": len(auto_alt),
            },
            "samples": {
                "missing_alt": missing_alt[:10],
                "empty_alt_non_decorative": empty_alt[:10],
                "auto_alt_like": auto_alt[:10],
            },
            "fix_hint": (
                "Dla obrazów treściowych dodaj opisowe `alt`. `alt=\"\"` tylko dla dekoracyjnych "
                "(role=presentation/none, aria-hidden=true). Unikaj altów typu nazwa pliku/IMG_1234."
            )
        }

    except Exception as e:
        return {"name": "alt_tags", "status": "ERROR", "error": str(e)}
