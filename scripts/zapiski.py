#!/usr/bin/env python3
"""Buduje sekcję „Zapisane podczas spaceru” (public/zapiski/) z notatek w content/zapiski/.

Notatki to pliki .md skopiowane z Obsidiana (Obsidian Vault/40000steps/Zapisane/).
Nagłówek notatki:
    ---
    tytuł: Panika nie wybiera
    miejsce: Warszawa
    miesiąc: październik 2026
    słowa: lęk, praca
    szkic: tak            # tak = nie publikować
    ---
Pliki zaczynające się od „_” są pomijane.

Kolejność: content/zapiski/kolejnosc.txt — adres (slug) każdej opublikowanej notatki,
dopisywany przy pierwszej publikacji. Najnowsza na końcu, na stronie na górze.
Raz nadany adres się nie zmienia, nawet gdy zmienisz tytuł.

Użycie:
    python3 scripts/zapiski.py            # buduje tylko notatki gotowe (szkic ≠ tak)
    python3 scripts/zapiski.py --szkice   # podgląd: buduje też szkice, nic nie zapisuje do kolejnosc.txt
"""
import html, json, os, re, shutil, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
SRC = os.path.join(ROOT, 'content', 'zapiski')
ORDER = os.path.join(SRC, 'kolejnosc.txt')
OUT = os.path.join(PUB, 'zapiski')
HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = 'Zapisane podczas spaceru'
PREVIEW = '--szkice' in sys.argv

MONTHS = ['styczeń', 'luty', 'marzec', 'kwiecień', 'maj', 'czerwiec', 'lipiec',
          'sierpień', 'wrzesień', 'październik', 'listopad', 'grudzień']
PL = str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ')


def slugify(t):
    t = unicodedata.normalize('NFC', t).translate(PL).lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


def parse(path):
    raw = open(path, encoding='utf-8').read().replace('\r\n', '\n')
    m = re.match(r'^---\n(.*?)\n---\n?(.*)$', raw, re.S)
    if not m:
        raise SystemExit(f'Brak nagłówka (---) w pliku: {os.path.basename(path)}')
    meta = {}
    for line in m.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            meta[unicodedata.normalize('NFC', k.strip().lower())] = v.strip()
    for k in ('tytuł', 'miejsce', 'miesiąc'):
        if not meta.get(k):
            raise SystemExit(f'Brak pola „{k}” w pliku: {os.path.basename(path)}')
    body = m.group(2).strip()
    if not body:
        raise SystemExit(f'Pusta treść w pliku: {os.path.basename(path)}')
    month = meta['miesiąc'].lower().split()
    if len(month) != 2 or month[0] not in MONTHS or not month[1].isdigit():
        raise SystemExit(f'Pole „miesiąc” ma mieć postać np. „październik 2026”: {os.path.basename(path)}')
    return dict(
        file=os.path.basename(path), title=meta['tytuł'], place=meta['miejsce'],
        month=meta['miesiąc'].lower(), iso=f'{month[1]}-{MONTHS.index(month[0]) + 1:02d}',
        words=[w.strip() for w in meta.get('słowa', '').split(',') if w.strip()],
        draft=meta.get('szkic', 'nie').lower() in ('tak', 'yes', 'true'),
        paras=[p.strip() for p in re.split(r'\n\s*\n', body) if p.strip()])


def inline(t):
    """Akapit z Obsidiana → HTML: *kursywa*, **pogrubienie**, [tekst](adres), [[link]] → sam tekst."""
    t = html.escape(t, quote=False)
    t = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+|mailto:[^)\s]+|/[^)\s]*)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])[*_](?!\s)(.+?)(?<!\s)[*_](?![*\w])', r'<em>\1</em>', t)
    return t.replace('\n', '<br>')


def plain(t):
    return re.sub(r'[*_]|\[\[|\]\]|\[([^\]]+)\]\([^)]*\)', r'\1', t)


def excerpt(paras):
    first = plain(paras[0])
    m = re.match(r'(.+?[.!?…])(\s|$)', first)
    return m.group(1) if m and len(m.group(1)) <= 180 else (first[:170].rsplit(' ', 1)[0] + '…' if len(first) > 180 else first)


# ── wspólne elementy strony (ze strony Spacery, żeby menu, stopka i tryby widoku były identyczne) ──
sp = open(os.path.join(PUB, 'spacery', 'index.html'), encoding='utf-8').read()
head_top = sp[:sp.index('<title>')]
i = sp.index('<meta name="theme-color"'); theme = sp[i:sp.index('</script>', i) + 9]
bar = sp[sp.index('<header class="bar">'):sp.index('</header>') + 9]
footer = sp[sp.index('<footer>'):sp.index('</footer>') + 9]
i = sp.index('<div class="scrim"'); panel = sp[i:sp.index('</aside>', i) + 8]
panel = panel.replace(' aria-current="page"', '').replace('<a href="/zapiski/">', '<a href="/zapiski/" aria-current="page">')
i = sp.index('<script>', sp.index('</aside>')); menu_js = sp[i:sp.index('</script>', i) + 9]
view = sp[sp.index('<div class="view-pop"'):sp.rindex('</body>')]
css = open(os.path.join(HERE, 'zapiski-base.css'), encoding='utf-8').read().replace(
    '</style>', open(os.path.join(HERE, 'zapiski.css'), encoding='utf-8').read() + '</style>')
home = open(os.path.join(PUB, 'index.html'), encoding='utf-8').read()
j = home.index('<script>\n(function () {\n  var f = document.getElementById(\'ml-form\')')
form_js = home[j:home.index('</script>', j) + 9]

if '/zapiski/' not in panel:
    raise SystemExit('W menu strony Spacery brakuje pozycji „Zapisane podczas spaceru”.')


def page(title, desc, path, main, extra='', ld=None):
    e = html.escape
    return (head_top + f'<title>{e(title)}</title>\n<meta name="description" content="{e(desc)}">\n'
            f'<link rel="canonical" href="https://40000steps.com{path}">\n'
            f'<meta property="og:title" content="{e(title)}">\n<meta property="og:description" content="{e(desc)}">\n'
            f'<meta property="og:url" content="https://40000steps.com{path}">\n'
            '<meta property="og:image" content="https://40000steps.com/assets/og.jpg">\n'
            '<meta property="og:locale" content="pl_PL">\n<meta property="og:site_name" content="40000 kroków">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            f'<meta name="robots" content="{"noindex" if PREVIEW else "index, follow"}">\n'
            + (f'<script type="application/ld+json">\n{json.dumps(ld, ensure_ascii=False, indent=1)}\n</script>\n' if ld else '')
            + theme + '\n' + css + '\n</head>\n<body>\n' + bar + '\n\n<main>\n' + main + '\n</main>\n\n'
            + footer + '\n\n' + panel + '\n' + menu_js + '\n' + extra + '\n' + view + '</body>\n</html>\n')


# ── notatki ──
notes = []
for f in sorted(os.listdir(SRC)):
    if f.endswith('.md') and not f.startswith('_'):
        n = parse(os.path.join(SRC, f))
        if PREVIEW or not n['draft']:
            notes.append(n)

order = [l.split('\t') for l in open(ORDER, encoding='utf-8').read().splitlines() if l.strip()] if os.path.exists(ORDER) else []
slug_of = {fn: sl for sl, fn in order}
taken = set(slug_of.values())
for n in notes:
    if n['file'] not in slug_of:
        s = base = slugify(n['title']) or 'notatka'
        k = 2
        while s in taken:
            s = f'{base}-{k}'; k += 1
        slug_of[n['file']] = s; taken.add(s)
        order.append([s, n['file']])
    n['slug'] = slug_of[n['file']]
rank = {fn: i for i, (sl, fn) in enumerate(order)}
notes.sort(key=lambda n: rank[n['file']], reverse=True)   # najnowsza na górze

if not notes:
    raise SystemExit('Nie ma żadnej gotowej notatki (wszystkie mają „szkic: tak”). Nic nie zbudowano.')

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

e = html.escape
items = '\n'.join(
    f'      <li><a href="/zapiski/{n["slug"]}/"><span class="where">{e(n["place"])} · {e(n["month"])}'
    f'{" · szkic" if n["draft"] else ""}</span><span class="nt">{e(n["title"])}</span>'
    f'<span class="ex">{e(excerpt(n["paras"]))}</span></a></li>' for n in notes)
main = f'''  <div class="col">
    <header class="nb-head">
      <h1>{TITLE}</h1>
      <p>Notatki z drogi. Piszę, kiedy jest o czym dać znać, nie według kalendarza.</p>
    </header>
    <ol class="notes" reversed>
{items}
    </ol>
    <section class="tell" aria-label="Powiadomienia">
      <p>Gdy zapiszę coś nowego, mogę dać Ci znać mailem.</p>
      <form class="sub" id="ml-form" method="post" novalidate action="https://assets.mailerlite.com/jsonp/2711601/forms/201295463689749769/subscribe">
        <input type="email" name="fields[email]" required autocomplete="email" placeholder="twój@adres.pl" aria-label="Adres e-mail">
        <input type="hidden" name="ml-submit" value="1"><input type="hidden" name="anticsrf" value="true">
        <button class="btn" type="submit">Daj mi znać</button>
      </form>
      <p class="note" id="ml-msg" role="status">Bez stałego rytmu i bez spamu. Wypiszesz się jednym kliknięciem. <a href="/prywatnosc/">Polityka prywatności</a>.</p>
    </section>
  </div>'''
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page(
    f'{TITLE} · 40000 kroków',
    'Notatki Łukasza o wysokofunkcjonującej depresji, lęku i szukaniu pomocy. Pisane, kiedy jest o czym dać znać.',
    '/zapiski/', main, form_js))

for idx, n in enumerate(notes):
    body = '\n'.join(f'      <p>{inline(p)}</p>' for p in n['paras'])
    older = ''
    if idx + 1 < len(notes):
        o = notes[idx + 1]
        older = (f'    <nav class="older" aria-label="Wcześniejsza notatka"><a href="/zapiski/{o["slug"]}/">'
                 f'<span class="where">Wcześniej · {e(o["place"])} · {e(o["month"])}</span>'
                 f'<span class="nt">{e(o["title"])}</span></a></nav>\n')
    main = f'''  <article class="col entry">
    <a class="back" href="/zapiski/">← {TITLE}</a>
    <span class="where">{e(n["place"])} · {e(n["month"])}</span>
    <h1>{e(n["title"])}</h1>
    <div class="body">
{body}
      <p class="close">Jeśli coś z tego jest o Tobie, <a href="mailto:lukasz@40000steps.com">napisz do mnie</a>.</p>
    </div>
{older}  </article>'''
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": n['title'],
          "description": excerpt(n['paras']), "inLanguage": "pl-PL", "datePublished": n['iso'],
          "url": f"https://40000steps.com/zapiski/{n['slug']}/",
          "author": {"@type": "Person", "name": "Łukasz", "url": "https://40000steps.com/manifest/"},
          "isPartOf": {"@type": "Blog", "name": TITLE, "url": "https://40000steps.com/zapiski/"}}
    if n['words']:
        ld['keywords'] = ', '.join(n['words'])
    os.makedirs(os.path.join(OUT, n['slug']))
    open(os.path.join(OUT, n['slug'], 'index.html'), 'w', encoding='utf-8').write(
        page(f'{n["title"]} · {TITLE}', excerpt(n['paras']), f'/zapiski/{n["slug"]}/', main, ld=ld))

if not PREVIEW:
    open(ORDER, 'w', encoding='utf-8').write(''.join(f'{s}\t{f}\n' for s, f in order))
    # mapa strony: podmień wpisy /zapiski/
    sm_path = os.path.join(PUB, 'sitemap.xml')
    sm = open(sm_path, encoding='utf-8').read()
    sm = re.sub(r'\s*<url>\s*<loc>https://40000steps\.com/zapiski/[^<]*</loc>.*?</url>', '', sm, flags=re.S)
    add = ''.join(f'\n  <url><loc>https://40000steps.com/zapiski/{s}</loc></url>'
                  for s in [''] + [n['slug'] + '/' for n in notes])
    sm = sm.replace('</urlset>', add + '\n</urlset>')
    open(sm_path, 'w', encoding='utf-8').write(sm)

print(('PODGLĄD (ze szkicami): ' if PREVIEW else 'Zbudowano: ') + f'{len(notes)} notatek')
for n in notes:
    print(f'  /zapiski/{n["slug"]}/  —  {n["title"]}' + ('  [szkic]' if n['draft'] else ''))
