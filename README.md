# Heuréka feed Rubiomonocoat.cz — SPECIAL_SERVICE

Skript stáhne Heuréka feed ze Shoptetu
(`https://www.rubiomonocoat.cz/heureka/export/products.xml`), ke každému produktu
přidá tagy `<SPECIAL_SERVICE>` a uloží nový feed do `output/heureka.xml`.
Zbytek feedu zůstává bajtově stejný jako ze Shoptetu.

Služby se nastavují v `rules.yaml` (pro všechny produkty, podle kategorie, podle ITEM_ID,
výjimky). Kód se při běžné změně neupravuje.

## Kde to běží

GitHub Actions (`.github/workflows/transform-feed.yml`) každou hodinu v 25. minutě
spustí `transform.py` a výsledek vystaví na GitHub Pages. Tuto URL stahuje Heuréka:

```
https://<github-účet>.github.io/rubio-heureka-feed/heureka.xml
```

Ruční spuštění: záložka Actions → Transform Heureka Feed → Run workflow.
`keepalive.yml` jednou měsíčně udělá prázdný commit, jinak by GitHub plánovaný běh
po 60 dnech bez commitu vypnul.

Lokální zkouška: `pip install -r requirements.txt && python transform.py`

## Bezpečnost běhu

- Když se feed nestáhne, je neúplný nebo neobsahuje produkty, skript skončí chybou
  a **starý výstup nechá beze změny**. Heuréka tak nikdy nedostane prázdný feed.
- Zápis je atomický (dočasný soubor + přejmenování), Heuréka nestáhne rozepsaný soubor.
- Produkty, které už `SPECIAL_SERVICE` mají (kdyby ho Shoptet začal posílat), se nemění.

## Limity Heuréky

Max. 5 služeb na produkt, každá max. 128 znaků. Skript obojí ohlídá.
Dokumentace: https://sluzby.heureka.cz/napoveda/xml-feed/#SPECIAL_SERVICE
