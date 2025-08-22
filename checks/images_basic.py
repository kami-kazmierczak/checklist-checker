from utils import fetch, get_soup, list_images, throttle

def run(root):
    try:
        r = fetch(root)
        soup = get_soup(r.text)
        imgs = list_images(soup, r.url, limit=30)
        largest = []
        has_webp = False

        for u in imgs:
            try:
                h = fetch(u, method="HEAD", allow_redirects=True)
                ctype = h.headers.get("Content-Type", "").lower()
                clen = int(h.headers.get("Content-Length", "0") or "0")
                if "image/webp" in ctype or u.lower().endswith(".webp"):
                    has_webp = True
                largest.append({"url": u, "bytes": clen, "content_type": ctype})
            except:
                continue
            throttle(0.05)

        largest = sorted(largest, key=lambda x: x["bytes"] if x["bytes"] else 0, reverse=True)[:5]
        too_big = [i for i in largest if i["bytes"] and i["bytes"] > 500_000]  # >500 KB

        status = "PASS" if has_webp and not too_big else "WARN" if has_webp else "FAIL"
        return {
            "name": "images_weight_webp",
            "status": status,
            "metrics": {"checked_imgs": len(imgs), "has_webp": has_webp, "largest_bytes": largest},
            "samples": {"too_big_top": too_big},
            "fix_hint": "Konwertuj do WebP/AVIF i zmniejsz największe grafiki (>500KB)."
        }
    except Exception as e:
        return {"name": "images_weight_webp", "status": "ERROR", "error": str(e)}
