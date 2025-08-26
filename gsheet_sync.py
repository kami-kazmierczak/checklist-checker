# gsheets_simple.py
import os,json
import datetime as dt
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.getenv("SHEET_ID")

WORKSHEET_NAME = "Checklist checker"
WORKSHEET_GID = os.getenv("WORKSHEET_GID")

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ── stałe kolumn (dopasuj do swojego arkusza) ─────────────────────────────────
COL_STAN = 4             # D: "Stan"
COL_DATA = 5             # E: "Data ukończenia"
COL_KOMENT = 6           # F: "Komentarz"
COL_JSON   = 7           # G: "JSON output"

# ── mapa: nazwa_checka -> wiersz w arkuszu ───────────────────────────────────
CHECK_ROWS = {
    "meta_tags_coverage":3,
    "headings_h1":5, 
    "canonical_self_reference":6, 
    "redirects_core":2,
    "trailing_slash_consistency":15,
    "breadcrumbs_presence":23,
    "images_weight_webp":42,
    "schema_pages":24,
    "blogpost_headings":13,
    "home_paragraphs":14, 
    "clickable_elements":21, 
    "nofollow_links_check":17,
    "blog_author":30,
    "alt_tags":35,
    "pagination_title":36,
    "lang_dir_in_url":37,
    "blogpost_rating":38,
    "psi":41,
    "webp":43,
    "faq":44, 
    "contact_form_under_post":45,
    "cache_headers":47,
    "blog_exists":48,
    "error_page_404":55,
    "footer_year":7,
}
_client = None

def _get_client():
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client

def get_ws():
    sh = _get_client().open_by_key(SHEET_ID)
    return sh.get_worksheet_by_id(int(WORKSHEET_GID))

def _a1(row: int, col: int) -> str:
    letters, c = "", col
    while c:
        c, rem = divmod(c - 1, 26)
        letters = chr(65 + rem) + letters
    return f"{letters}{row}"

def set_check_result(name: str, passed: bool, comment: str = "", raw: dict | None = None):
    row = CHECK_ROWS[name]
    ws = get_ws()
    stan = "PASS" if passed else "FAIL"
    date_val = dt.datetime.now().strftime("%Y-%m-%d") if passed else ""
    json_str = json.dumps(raw or {}, ensure_ascii=False, separators=(",", ":"))
    updates = [
        {"range": _a1(row, COL_STAN),   "values": [[stan]]},
        {"range": _a1(row, COL_DATA),   "values": [[date_val]]},
        {"range": _a1(row, COL_KOMENT), "values": [[comment or ""]]},
        {"range": _a1(row, COL_JSON),   "values": [[json_str]]},   # <-- G: JSON
    ]
    ws.batch_update(updates)

def batch_set_results(results: list[dict]):
    """
    results = [
      {"name": "nofollow_links_check", "passed": True,  "comment": "", "raw": {...}},
      {"name": "img_alt",              "passed": False, "comment": "3 bez alt", "raw": {...}},
      ...
    ]
    """
    if not results:
        return
    ws = get_ws()
    updates = []
    today = dt.datetime.now().strftime("%Y-%m-%d")
    skipped = []

    for r in results:
        name = r["name"]
        row = CHECK_ROWS.get(name)
        if not row:
            skipped.append(name)
            continue

        passed = bool(r.get("passed", False))
        stan = "PASS" if passed else "FAIL"
        date_val = today if passed else ""
        comment = r.get("comment", "") or ""
        raw = r.get("raw", {}) or {}
        json_str = json.dumps(raw, ensure_ascii=False, indent=2)

        # w kolumnie G tylko skrót (status + długość JSON)
        short_val = f"{stan} · {len(json_str)}B"

        updates.extend([
            {"range": _a1(row, COL_STAN),   "values": [[stan]]},
            {"range": _a1(row, COL_DATA),   "values": [[date_val]]},
            {"range": _a1(row, COL_KOMENT), "values": [[comment]]},
            {"range": _a1(row, COL_JSON),   "values": [[short_val]]},
        ])

        # pełny JSON jako notatka w tej samej komórce
        _set_cell_note(ws, row, COL_JSON, json_str)

    if updates:
        ws.batch_update(updates)
    if skipped:
        print("⚠️  Pominięto checki bez mapy wierszy:", ", ".join(skipped))


def _set_cell_note(ws, row: int, col: int, text: str):
    """Ustawia notatkę (note) w komórce [row, col]."""
    ws.spreadsheet.batch_update({
        "requests": [{
            "updateCells": {
                "range": {
                    "sheetId": int(WORKSHEET_GID),
                    "startRowIndex": row-1, "endRowIndex": row,
                    "startColumnIndex": col-1, "endColumnIndex": col
                },
                "rows": [{
                    "values": [{
                        "note": text
                    }]
                }],
                "fields": "note"
            }
        }]
    })