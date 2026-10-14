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
