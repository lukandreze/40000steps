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

Notatki powstają w Obsidianie Łukasza: `Obsidian Vault/40000steps/Zapisane/` (iCloud). Jeden plik to jedna notatka: **nazwa pliku jest tytułem**, treść to zwykłe akapity, bez żadnego nagłówka. Pliki zaczynające się od `_` są pomijane.

- `content/zapiski/` – kopie notatek (źródło strony).
- `content/zapiski/kolejnosc.txt` – adres, plik i miesiąc pierwszej publikacji. Raz nadane, nie zmieniają się.
- `python3 scripts/zapiski.py` – buduje `public/zapiski/` i aktualizuje `sitemap.xml`.

Publikacja: Łukasz pisze w wątku „opublikuj”. Claude kopiuje folder `Zapisane`, buduje, wypycha na `main` (Cloudflare wdraża sam) i sprawdza stronę.
