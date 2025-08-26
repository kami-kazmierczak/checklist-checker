import os
from dotenv import load_dotenv

load_dotenv()

# --- Ustawienia globalne requestów ---
DEFAULT_HEADERS = {
    "User-Agent": "SEO-Checker/0.1 (+contact: admin@delante)"
}
REQUEST_TIMEOUT = 20

# --- Crawling ---
CRAWL_LIMIT = 50       # max liczba URL-i do sprawdzenia z sitemap
MAX_IMG_HEAD = 30      # ile obrazków badamy per strona (HEAD)

# --- Statystyki akapitów na stronie głównej ---
PARA_SHORT_THRESHOLD = 20    # próg: bardzo krótki akapit
PARA_LONG_THRESHOLD  = 120   # próg: bardzo długi akapit


# --- Check: NOFOLLOW ---
NOFOLLOW_KEYWORDS = [
    "regulamin",
    "polityka",
    "moje konto", "moje-konto", "konto",
    "koszyk", "cart",
    "logowanie", "zaloguj", "rejestracja",
    "Privacy Policy", "Terms of Service", "Terms and Conditions",
    "Ochrona danych", "Polityka prywatności", "Polityka cookies",
    "Zwroty i reklamacje", "Dostawa i płatności",
]
NOFOLLOW_SOCIAL_KEYWORDS = [
    "facebook", "instagram", "linkedin", "twitter",
    "youtube", "tiktok", "pinterest"
]


# --- Check: Blog ---
BLOG_HINTS = [
    "/blog",
    "blog",
    "aktualności",
    "wpisy",
    "artykuły"
]

# Podstawowe ścieżki do audytu
BLOG_PAGE   = "/blog/"
SHOP_PAGE   = ""
BLOG_POST   = "/jak-tworzyc-tresci-cytowane-przez-ai/"
PRODUCT_URL = ""
CONTACT_PAGE = "/kontakt"


# --- Check: Title ---
# Suffix tytułu (opcjonalny — np. " | NazwaFirmy")
TITLE_SUFFIX = "Delante"


# --- Check: ALT TAGS ---
ALT_EXCLUDE_SELECTORS = [
    # 'header .logo img',
]
ALT_INCLUDE_SVG = True


# --- Check: PageSpeed Insights ---
# Opcjonalny klucz (bez klucza też działa, ale z mniejszym limitem zapytań)
PSI_API_KEY = os.getenv("PSI_API_KEY")
# Jakie strategie sprawdzać (mobile/desktop)
PSI_STRATEGIES = ["mobile", "desktop"]


# --- Dodatkowe ścieżki / sitemapy ---
CUSTOM_SITEMAPS = [
    "/page-sitemap.xml",
]
EXTRA_URLS = [
    "/reklamy-na-instagramie/",
    BLOG_POST
]
SCHEMA_EXTRA_PATHS = [
    "/kontakt/",
    "/blog/",
    BLOG_POST
]
CLICKABLE_PATHS = [
    "/",            # strona główna
    CONTACT_PAGE,   # kontakt
]
