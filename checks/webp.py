# checks/webp.py
from utils import fetch, get_soup

def run(root):
    """Sprawdzenie, czy na stronie głównej są obrazy w formacie WebP/AVIF."""
    try:
        r = fetch(root)
        soup = get_soup(r.text)

        imgs = soup.find_all("img")
        total = len(imgs)

        webp_imgs = []
        non_webp_imgs = []

        for img in imgs:
            src = img.get("src") or img.get("data-src") or img.get("data-lazy") or ""
            s = src.lower()
            if s.endswith(".webp") or s.endswith(".avif"):
                webp_imgs.append(src[:140])
            elif s:
                non_webp_imgs.append(src[:140])

        if len(webp_imgs) > len(non_webp_imgs) and webp_imgs:
            status = "PASS"
        else:
            status = "WARN" if len(non_webp_imgs) > 0 else "SKIP"

        return {
            "name": "webp",
            "status": status,
            "metrics": {
                "images_total": total,
                "webp_count": len(webp_imgs),
                "non_webp_count": len(non_webp_imgs),
            },
            "samples": {
                "webp_imgs": webp_imgs[:10],
                "non_webp_imgs": non_webp_imgs[:10],
            },
            "fix_hint": (
                "Używaj WebP/AVIF na stronie głównej dla lepszej wydajności. "
                "Możesz włączyć konwersję wtyczką lub przez serwer (np. mod_pagespeed, nginx)."
            )
        }
    except Exception as e:
        return {"name": "webp", "status": "ERROR", "error": str(e)}
