# 40000steps

Blog o zdrowiu psychicznym mężczyzn, zwłaszcza o wysokofunkcjonującej depresji.

Strona: [40000steps.com](https://40000steps.com)

## Struktura

- `public/` — wszystko, co trafia na stronę (Cloudflare Workers, static assets; konfiguracja w `wrangler.jsonc`)
  - `manifest/index.html` — manifest (adres kanoniczny `/manifest/`)
  - `index.html` — strona główna; na razie kopia manifestu
  - `prywatnosc/index.html` — polityka prywatności
  - `assets/` — zdjęcia, czcionki (self-hosted), obraz do udostępnień
- `photos/` — oryginalne zdjęcia (nie są publikowane)

Formularz „Zostaw adres” wysyła adres do MailerLite (formularz „Spacer”, double opt-in).

## Zapisane podczas spaceru (`/zapiski/`)

Notatki powstają w Obsidianie Łukasza: `Obsidian Vault/40000steps/Zapisane/` (iCloud). Jeden plik = jedna notatka, nagłówek: `tytuł`, `miejsce`, `miesiąc`, `słowa` (niewidoczne słowa kluczowe), `szkic` (`tak` = nie publikować). Pliki zaczynające się od `_` są pomijane.

Źródło na stronie: kopie notatek w `content/zapiski/`, kolejność i stałe adresy w `content/zapiski/kolejnosc.txt`.

- `python3 scripts/zapiski.py` buduje `public/zapiski/` tylko z gotowych notatek i aktualizuje `sitemap.xml`.
- `python3 scripts/zapiski.py --szkice` to podgląd ze szkicami (`noindex`). Nigdy nie trafia na `main`.

Publikacja: Claude kopiuje notatki z Obsidiana, buduje, pokazuje podgląd i publikuje (push na `main`) dopiero po akceptacji.
