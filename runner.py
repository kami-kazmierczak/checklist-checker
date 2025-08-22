import argparse, json, sys, time, os
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime

from checks import ALL_CHECKS

STATUS_ICON = {
    "PASS": "✅",
    "WARN": "⚠️ ",
    "FAIL": "❌",
    "ERROR": "💥",
}

def ensure_root(u: str) -> str:
    p = urlsplit(u if "://" in u else "https://" + u)
    scheme = p.scheme or "https"
    netloc = p.netloc or p.path
    return urlunsplit((scheme, netloc, "/", "", ""))

def main():
    ap = argparse.ArgumentParser(description="SEO Checker MVP")
    ap.add_argument("domain_or_url", help="np. example.com albo https://example.com/")
    ap.add_argument("--pretty", action="store_true", help="ładny JSON na końcu")
    args = ap.parse_args()

    nossl_root = args.domain_or_url
    root = ensure_root(args.domain_or_url)
    print(f"[START] Audyt domeny: {root}\n")

    results = []
    total = len(ALL_CHECKS)

    for i, (check_name, check_fn) in enumerate(ALL_CHECKS, start=1):
        print(f"[{i}/{total}] RUN {check_name} ...", end="", flush=True)
        t0 = time.time()
        try:
            if check_name == "redirects_core":
                res = check_fn(nossl_root)
            else:
                res = check_fn(root)
        except Exception as e:
            res = {"name": check_name, "status": "ERROR", "error": str(e)}
        dt = time.time() - t0

        res.setdefault("name", check_name)
        results.append(res)

        icon = STATUS_ICON.get(res.get("status", "ERROR"), "")
        print(f" -> {icon} {res.get('status')} ({dt:.2f}s)")

    print("\n[RESULTS] Podsumowanie:")
    for r in results:
        icon = STATUS_ICON.get(r.get("status", ""), "")
        print(f" - {icon} {r['name']}: {r['status']}")

    # JSON OUTPUT
    json_str = json.dumps(results, indent=2 if args.pretty else None, ensure_ascii=False)
    print("\n[JSON OUTPUT]")
    print(json_str)

    # 🔹 Zapis do pliku z nazwą domeny + timestamp
    domain = urlsplit(root).netloc
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    # katalog bazowy + katalog domeny
    output_dir = os.path.join("reports", domain)
    os.makedirs(output_dir, exist_ok=True)
    fname = os.path.join(output_dir, f"{domain}_{now_str}.json")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(json_str)

    print(f"\n✅ Raport zapisany do pliku: {fname}")

    # exit code
    code = 0
    for r in results:
        st = r.get("status")
        if st == "WARN" and code < 1:
            code = 1
        elif st == "FAIL" and code < 2:
            code = 2
        elif st == "ERROR" and code < 3:
            code = 3
    sys.exit(code)

if __name__ == "__main__":
    main()
