from utils import fetch
from urllib.parse import urljoin

def run(root):

    root_no = urljoin(root,"/kontakt")
    root_slash = root_no + "/"
    try:
        r1 = fetch(root_no, allow_redirects=True)
        r2 = fetch(root_slash, allow_redirects=True)
        consistent = r1.url == r2.url
        status = "PASS" if consistent else "FAIL"
        return {
            "name": "trailing_slash_consistency",
            "status": status,
            "metrics": {"no_slash":root_no,"no_slash_final": r1.url, "slash_final": r2.url},
            "samples": {},
            "fix_hint": "Wymuś spójność (301) między wersją z i bez ukośnika, aby uniknąć duplikacji."
        }
    except Exception as e:
        return {"name": "trailing_slash_consistency", "status": "ERROR", "error": str(e)}
