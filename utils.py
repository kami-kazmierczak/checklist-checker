import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, urlunsplit, urljoin

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT,CUSTOM_SITEMAPS, EXTRA_URLS, CRAWL_LIMIT

def fetch(url, method="GET", allow_redirects=True, headers=None):
    h = DEFAULT_HEADERS.copy()
    if headers:
        h.update(headers)
    r = requests.request(method, url, timeout=REQUEST_TIMEOUT, allow_redirects=allow_redirects, headers=h)
    return r

def get_soup(html):
    return BeautifulSoup(html, "lxml")

def normalize_url(u: str) -> str:
    p = urlsplit(u)
    netloc = p.netloc.lower()
    path = p.path or "/"
    # usuń podwójne slashe, normalizuj trailing (zostaw jak jest)
    path = re.sub(r"/{2,}", "/", path)
    return urlunsplit((p.scheme, netloc, path, "", ""))

def canonicalize_compare(a: str, b: str) -> bool:
    return normalize_url(a.rstrip("/")) == normalize_url(b.rstrip("/"))

def find_sitemap_urls(root: str):
    """Zwraca listę sitemap: /sitemap.xml, /sitemap_index.xml oraz robots.txt wskazanie."""
    roots = []
    for guess in ("/sitemap.xml", "/sitemap_index.xml"):
        try:
            r = fetch(urljoin(root, guess))
            if r.status_code == 200 and b"<urlset" in r.content or b"<sitemapindex" in r.content:
                roots.append(urljoin(root, guess))
        except:
            pass
    # robots.txt
    try:
        r = fetch(urljoin(root, "/robots.txt"))
        if r.status_code == 200:
            for line in r.text.splitlines():
                if "Sitemap:" in line:
                    sm = line.split("Sitemap:", 1)[1].strip()
                    roots.append(sm)
    except:
        pass
    # deduplikacja
    return list(dict.fromkeys(roots))

def iter_urls_from_sitemap(sm_url: str, limit: int = 200):
    try:
        r = fetch(sm_url)
        if r.status_code != 200:
            return
        tree = ET.fromstring(r.content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        # sitemapindex
        if tree.tag.endswith("sitemapindex"):
            for sm in tree.findall("sm:sitemap/sm:loc", ns):
                yield from iter_urls_from_sitemap(sm.text.strip(), limit)
        else:
            count = 0
            for loc in tree.findall(".//sm:url/sm:loc", ns):
                if count >= limit:
                    break
                yield loc.text.strip()
                count += 1
    except:
        return

def throttle(sec=0.2):
    time.sleep(sec)

def extract_basic_meta(html: str):
    soup = get_soup(html)
    title = (soup.title.string or "").strip() if soup.title else ""
    desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        desc = md["content"].strip()
    canonical = ""
    lc = soup.find("link", rel=lambda v: v and "canonical" in v)
    if lc and lc.get("href"):
        canonical = lc["href"].strip()
    return soup, title, desc, canonical

def list_images(soup, base_url, limit=20):
    urls = []
    # img + sources z picture
    for node in soup.select("img[src]"):
        urls.append(urljoin(base_url, node.get("src")))
    for node in soup.select("source[srcset]"):
        srcset = node.get("srcset", "")
        first = srcset.split(",")[0].strip().split(" ")[0]
        if first:
            urls.append(urljoin(base_url, first))
    # dedupe, ogranicz
    deduped = []
    seen = set()
    for u in urls:
        if u not in seen:
            deduped.append(u)
            seen.add(u)
        if len(deduped) >= limit:
            break
    return deduped

def collect_urls(root: str, limit=CRAWL_LIMIT):
    urls = []

    # 1) jeśli są ustawione custom sitemapy
    if CUSTOM_SITEMAPS:
        for sm in CUSTOM_SITEMAPS:
            sm = urljoin(root,sm)
            urls.extend(list(iter_urls_from_sitemap(sm, limit=limit)))
    else:
        # szukaj automatycznie
        for sm in find_sitemap_urls(root):
            urls.extend(list(iter_urls_from_sitemap(sm, limit=limit)))

    # 2) dodaj EXTRA_URLS (jeśli istnieją)
    urls.extend(EXTRA_URLS)

    # 3) ogranicz liczbę i deduplikuj
    seen, unique = set(), []
    for u in urls:
        if u not in seen:
            unique.append(u)
            seen.add(u)
        if len(unique) >= limit:
            break

    return unique or [root]