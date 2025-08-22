# checks/psi.py
import json
import time
from urllib.parse import urlencode
import requests
from config import PSI_API_KEY, PSI_STRATEGIES

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# Ustawienia sieci dla PSI (ciężkie zapytania -> dajemy większy timeout i retry)
_PSI_TIMEOUT = 60          # sekundy
_PSI_RETRIES = 3
_PSI_BACKOFF = 2.0         # mnożnik czasu czekania między próbami (exponential backoff)

def _http_get(url: str, params: dict):
    """GET z retry/backoff specjalnie pod PSI."""
    attempt = 0
    while True:
        attempt += 1
        try:
            r = requests.get(url, params=params, timeout=_PSI_TIMEOUT)
            # retry przy 429 i 5xx
            if r.status_code in (429, 500, 502, 503, 504):
                if attempt < _PSI_RETRIES:
                    wait = (_PSI_BACKOFF ** (attempt - 1))
                    print(f"[psi] HTTP {r.status_code} -> retry {attempt}/{_PSI_RETRIES} za {wait:.1f}s")
                    time.sleep(wait)
                    continue
            return r
        except requests.exceptions.ReadTimeout as e:
            if attempt < _PSI_RETRIES:
                wait = (_PSI_BACKOFF ** (attempt - 1))
                print(f"[psi] ReadTimeout -> retry {attempt}/{_PSI_RETRIES} za {wait:.1f}s")
                time.sleep(wait)
                continue
            raise e

def _get(url: str, strategy: str):
    params = {"url": url, "strategy": strategy}
    if PSI_API_KEY:
        params["key"] = PSI_API_KEY
    r = _http_get(PSI_ENDPOINT, params)
    if r.status_code != 200:
        # pokaż kawałek treści dla debugowania
        snippet = r.text[:200] if isinstance(r.text, str) else str(r.content)[:200]
        raise RuntimeError(f"PSI HTTP {r.status_code}: {snippet}")
    try:
        return r.json()
    except json.JSONDecodeError:
        raise RuntimeError("PSI: nieprawidłowy JSON w odpowiedzi")

def _get_safe(dct, path, default=None):
    cur = dct
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def _extract_scores(resp):
    # performance score (0..1)
    perf = _get_safe(resp, ["lighthouseResult", "categories", "performance", "score"], None)
    # inne kategorie (opcjonalnie)
    acc  = _get_safe(resp, ["lighthouseResult", "categories", "accessibility", "score"], None)
    bp   = _get_safe(resp, ["lighthouseResult", "categories", "best-practices", "score"], None)
    seo  = _get_safe(resp, ["lighthouseResult", "categories", "seo", "score"], None)

    # CWV field data
    le  = resp.get("loadingExperience") or {}
    ole = resp.get("originLoadingExperience") or {}

    def _metric(src, key_opts):
        for key in key_opts:
            m = _get_safe(src, ["metrics", key], {})
            if m:
                return {
                    "category": m.get("category"),  # GOOD / NEEDS_IMPROVEMENT / POOR
                    "p75": m.get("percentile"),
                    "distributions": m.get("distributions", []),
                }
        return None

    lcp = _metric(le, ["LARGEST_CONTENTFUL_PAINT_MS"]) or _metric(ole, ["LARGEST_CONTENTFUL_PAINT_MS"])
    cls = _metric(le, ["CUMULATIVE_LAYOUT_SHIFT_SCORE"]) or _metric(ole, ["CUMULATIVE_LAYOUT_SHIFT_SCORE"])
    inp = _metric(le, ["INTERACTION_TO_NEXT_PAINT", "EXPERIMENTAL_INTERACTION_TO_NEXT_PAINT"]) or \
          _metric(ole, ["INTERACTION_TO_NEXT_PAINT", "EXPERIMENTAL_INTERACTION_TO_NEXT_PAINT"])

    # Lighthouse lab metrics (opcjonalnie)
    audits = _get_safe(resp, ["lighthouseResult", "audits"], {})
    def _val(audit_id):
        a = audits.get(audit_id, {})
        return a.get("numericValue")
    lab = {
        "lcp_ms": _val("largest-contentful-paint"),
        "inp_ms": _val("interactive") if _val("interactive") is not None else None,  # to nie INP (field)
        "tbt_ms": _val("total-blocking-time"),
        "cls": _val("cumulative-layout-shift"),
        "si_ms": _val("speed-index"),
        "fcp_ms": _val("first-contentful-paint"),
    }

    return {
        "scores": {
            "performance": perf,
            "accessibility": acc,
            "best_practices": bp,
            "seo": seo,
        },
        "cwv_field": {
            "lcp": lcp,
            "inp": inp,
            "cls": cls,
        },
        "lab": lab,
    }

def _strategy_status(s):
    """
    Heurystyka statusu:
    - PASS: CWV categories (field data) wszystkie GOOD albo perf >= 0.90
    - WARN: są dane, ale min. jedna CWV to NEEDS_IMPROVEMENT/POOR, lub perf 0.60–0.89
    - FAIL: brak danych CWV i perf < 0.60
    """
    perf = s["scores"]["performance"]
    lcp = s["cwv_field"]["lcp"] or {}
    inp = s["cwv_field"]["inp"] or {}
    cls = s["cwv_field"]["cls"] or {}
    have_cwv = any([lcp, inp, cls])

    if have_cwv and all(m and (m.get("category") == "GOOD") for m in [lcp, inp, cls] if m):
        return "PASS"
    if perf is not None and perf >= 0.90:
        return "PASS"

    if perf is not None and perf >= 0.60:
        return "WARN"
    if not have_cwv and (perf is None or perf < 0.60):
        return "FAIL"
    return "WARN"

def run(root):
    strategies = PSI_STRATEGIES or ["mobile", "desktop"]
    results = {}
    errors = {}

    print(f"[psi] Checking PSI for: {root} (strategies: {', '.join(strategies)})")

    for strat in strategies:
        try:
            resp = _get(root, strat)
            parsed = _extract_scores(resp)
            status = _strategy_status(parsed)
            results[strat] = {**parsed, "status": status}
            print(f"[psi] {strat}: perf={parsed['scores']['performance']} status={status}")
        except Exception as e:
            errors[strat] = str(e)
            print(f"[psi] {strat}: ERROR {e}")

    # zagregowany status:
    # - jeśli chociaż jedna strategia się uda -> najgorszy status z udanych
    # - jeśli wszystkie padły -> ERROR
    order = {"PASS": 0, "WARN": 1, "FAIL": 2}
    if results:
        worst = max((r["status"] for r in results.values()), key=lambda st: order.get(st, 1))
        overall = worst
    else:
        overall = "ERROR"

    return {
        "name": "psi",
        "status": overall,
        "metrics": {
            "strategies_checked": list(results.keys()) if results else [],
            "errors": errors,
            "mobile_performance": results.get("mobile", {}).get("scores", {}).get("performance"),
            "desktop_performance": results.get("desktop", {}).get("scores", {}).get("performance"),
        },
        "samples": {
            "mobile": results.get("mobile"),
            "desktop": results.get("desktop"),
        },
        "fix_hint": (
            "Skup się na CWV: LCP (≤2.5s), INP (≤200ms), CLS (≤0.1). "
            "Użyj lazy-loading, optymalizacji obrazów (WebP/AVIF), preconnect, i eliminuj JS blokujący render."
        ),
    }
