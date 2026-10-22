# 40000steps

Blog o zdrowiu psychicznym mężczyzn, zwłaszcza o wysokofunkcjonującej depresji.

Strona: [40000steps.com](https://40000steps.com)

## Struktura

- `public/` — wszystko, co trafia na stronę (Cloudflare Workers, static assets; konfiguracja w `wrangler.jsonc`)
  - `manifest/index.html` — manifest (adres kanoniczny `/manifest/`)
  - `index.html` — strona główna; na razie kopia manifestu
  - `prywatnosc/index.html` — polityka prywatności
  - `jak-szukasz-pomocy/index.html` — ankieta „Jak szukasz pomocy” (edycja 1: 21.10–30.11.2026)
- `src/worker.js` — Worker obsługujący tylko `/api/*`: zapis anonimowych odpowiedzi z ankiety w Durable Object (SQLite, jurysdykcja UE)
  - `assets/` — zdjęcia, czcionki (self-hosted), obraz do udostępnień
- `photos/` — oryginalne zdjęcia (nie są publikowane)

Formularz „Zostaw adres” wysyła adres do MailerLite (formularz „Spacer”, double opt-in).

## Ankieta „Jak szukasz pomocy”

- `POST /api/ankieta` — zapis odpowiedzi (bez IP i godziny, tylko data; wymaga zgody; przyjmowane tylko w czasie edycji).
- `GET /api/ankieta/status` — czy baza działa i czy edycja jest otwarta.
- `GET /api/ankieta/eksport` — eksport CSV (`?format=json` dla JSON). Wyłączony, dopóki w Cloudflare nie ustawisz sekretu `EXPORT_TOKEN`; zapytanie wymaga nagłówka `Authorization: Bearer <EXPORT_TOKEN>`.
- Daty edycji: w `src/worker.js` (`EDITIONS`) i w skrypcie strony `public/jak-szukasz-pomocy/index.html` (`START`, `END`).
