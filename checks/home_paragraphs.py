# checks/home_paragraphs.py
from statistics import mean, median
from utils import fetch, get_soup
from config import PARA_SHORT_THRESHOLD, PARA_LONG_THRESHOLD

def _wc(txt: str) -> int:
    return len((txt or "").split())

def _sample(txt: str, n=90) -> str:
    txt = (txt or "").replace("\n", " ").strip()
    return (txt[:n] + "…") if len(txt) > n else txt

def run(root):
    try:
        r = fetch(root)
        soup = get_soup(r.text)

        # jeśli jest <main>, licz tylko w nim — w przeciwnym razie globalnie
        scope = soup.find("main") or soup
        paragraphs = [p.get_text(" ", strip=True) for p in scope.find_all("p")]

        counts = [ _wc(p) for p in paragraphs if p ]
        if not counts:
            return {
                "name": "home_paragraphs",
                "status": "WARN",
                "metrics": {"paragraphs": 0, "total_words": 0},
                "samples": {"note": "Nie znaleziono żadnych <p> na stronie głównej."},
                "fix_hint": "Dodaj treść tekstową w akapity <p> na stronie głównej."
            }

        # statystyki
        total_paras   = len(counts)
        total_words   = sum(counts)
        avg_words     = round(mean(counts), 2)
        med_words     = int(median(counts))
        min_words     = min(counts)
        max_words     = max(counts)

        # przygotuj listę (count, sample) do próbek
        pairs = list(zip(counts, paragraphs))
        pairs_sorted_short = sorted(pairs, key=lambda x: x[0])[:5]
        pairs_sorted_long  = sorted(pairs, key=lambda x: -x[0])[:5]

        # małe podsumowanie w konsoli
        print(f"[home_paragraphs] paragraphs={total_paras} total_words={total_words} "
              f"avg={avg_words} median={med_words} min={min_words} max={max_words}")

        # pomocnicze kubełki długości (do szybkiego wglądu)
        short_cnt = sum(1 for c in counts if c < PARA_SHORT_THRESHOLD)
        long_cnt  = sum(1 for c in counts if c >= PARA_LONG_THRESHOLD)

        return {
            "name": "home_paragraphs",
            "status": "PASS",  # tylko pomiar, bez oceniania jakości
            "metrics": {
                "paragraphs": total_paras,
                "total_words": total_words,
                "avg_words_per_paragraph": avg_words,
                "median_words_per_paragraph": med_words,
                "min_words": min_words,
                "max_words": max_words,
                "short_paragraphs_lt_threshold": short_cnt,
                "long_paragraphs_ge_threshold": long_cnt,
                "short_threshold": PARA_SHORT_THRESHOLD,
                "long_threshold": PARA_LONG_THRESHOLD
            },
            "samples": {
                "shortest": [f"{cnt}w: {_sample(txt)}" for cnt, txt in pairs_sorted_short],
                "longest":  [f"{cnt}w: {_sample(txt)}" for cnt, txt in pairs_sorted_long]
            },
            "fix_hint": (
                "To tylko statystyki długości akapitów na stronie głównej. "
                "Użyj ich, aby zdecydować, czy dołożyć/skrótcić treść."
            )
        }

    except Exception as e:
        return {"name": "home_paragraphs", "status": "ERROR", "error": str(e)}
