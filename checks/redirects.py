from urllib.parse import urljoin
from utils import fetch

def run(root):
    # proste „główne” URL-e do sprawdzenia
    candidates = [f"https://{root}", f"http://{root}", f"https://www.{root}"]

    chains = []
    errors = 0

    for u in candidates:
        try:
            r = fetch(u, allow_redirects=True)
            history = [{"status": h.status_code, "url": h.headers.get("Location", "") or ""} for h in r.history]
            final = r.url
            chains.append({"start": u, "final": final, "hops": len(r.history), "history": history, "final_code": r.status_code})
        except Exception as e:
            errors += 1
            chains.append({"start": u, "error": str(e)})

    long_chains = [c for c in chains if c.get("hops", 0) > 1]
    non_200_final = [c for c in chains if c.get("final_code") and c["final_code"] not in (200, 204)]
    status = "PASS" if not long_chains and not non_200_final and errors == 0 else "WARN" if errors == 0 else "FAIL"

    return {
        "name": "redirects_core",
        "status": status,
        "metrics": {
            "checked": len(candidates),
            "errors": errors,
            "chains_gt1": len(long_chains),
            "non_200_final": len(non_200_final)
        },
        "samples": {"details": chains},
        "fix_hint": "Unikaj łańcuchów >1 hop; doprowadź do 301 → 200 w jednym skoku; strony kluczowe muszą kończyć na 200."
    }
