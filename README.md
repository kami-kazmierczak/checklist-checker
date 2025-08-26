<h2>🤖Service Account (Google Sheets & PageSpeedAPI)</h2>
<ul>
<li>Google Cloud → utwórz projekt.</li>
<li>Włącz Google Sheets API.</li>
<li>Włącz Page Speed API.</li>
<li>Credentials → Service Account → Keys → Add key → JSON (pobierz plik).</li>
<li>W arkuszu Google kliknij „Udostępnij” i dodaj e-mail konta serwisowego z pliku JSON (rola: Edytor).</li>
<li>Plik service_account.json wrzuć do głównego folderu projektu</li>
</ul>
<h2>⚙️Konfiguracja przez ENV</h2>
# .env (przykład)<br>
PSI_API_KEY = 1AbCdEfGhIjK... <br>
SHEET_ID=1AbCdEfGhIjK...     # ID całego arkusza <br>
GSPREAD_GID=12312312         # GID do tabeli<br>
<h2>Konfiguracja ustawień</h2>
<p>Plik config.py</p>
<p>Najważniejsze opcje, pozostałe opcje według uznania (są komentarze)</p>
<ul>
  <li>BLOG_PAGE - Slug do strony blogowej np. /blog/ </li>
<li>SHOP_PAGE - Slug do strony sklepu np. /shop/ | jeśli brak sklepu zostaw puste</li>
<li>BLOG_POST - Slug do blogposta np. /jak-stworzyc-bloga/</li>
<li>PRODUCT_URL - Slug do produtu np. /produkt-xyz-123/ </li>
<li>CONTACT_PAGE - Slug do strony kontaktowej np. /contact/</li>
  <li>TITLE_SUFFIX - Brand np. "Media Markt"</li>
  <li>CUSTOM_SITEMAPS - Sitemapy strony np. "/page-sitemap.xml" /</li>
  
</ul>
<h2>Uruchomienie audytu</h2>
<p>💻Komenda: <span style="color:green;">python runner.py https://example.com/ --pretty</span></p>
