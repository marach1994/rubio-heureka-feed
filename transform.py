#!/usr/bin/env python3
"""Heuréka feed Rubiomonocoat.cz — doplní <SPECIAL_SERVICE> podle rules.yaml.

Feed se upravuje jako text: do každého <SHOPITEM> se před </SHOPITEM> vloží
řádky se službami. Vše ostatní (CDATA v popisech, pořadí, formátování) zůstává
přesně jako ve feedu ze Shoptetu.
"""

import os
import re
import sys
from html import escape
from pathlib import Path

import requests
import yaml

MAX_SERVICES = 5
MAX_LEN = 128
ITEM_RE = re.compile(r"<SHOPITEM>.*?</SHOPITEM>", re.S)


def tag(item, name):
    m = re.search(rf"<{name}>(.*?)</{name}>", item, re.S)
    return m.group(1).strip() if m else ""


def services_for(item, rules):
    item_id, category = tag(item, "ITEM_ID"), tag(item, "CATEGORYTEXT")
    if item_id in rules.get("skip_items", []):
        return []
    if any(c in category for c in rules.get("skip_categories", [])):
        return []
    out = list(rules.get("services_all", []))
    for c, svc in (rules.get("services_by_category") or {}).items():
        if c in category:
            out += svc
    out += (rules.get("services_by_item") or {}).get(item_id, [])
    seen = []
    for s in out:
        s = s.strip()[:MAX_LEN]
        if s and s not in seen:
            seen.append(s)
    return seen[:MAX_SERVICES]


def main():
    base = Path(__file__).resolve().parent
    rules = yaml.safe_load((base / "rules.yaml").read_text(encoding="utf-8"))

    print(f"Stahování feedu: {rules['feed_url']}")
    try:
        resp = requests.get(rules["feed_url"], timeout=300)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.exit(f"Chyba stahování feedu: {e}")
    xml = resp.content.decode("utf-8")
    if "</SHOP>" not in xml:
        sys.exit("Feed je neúplný (chybí </SHOP>), výstup se nepřepisuje.")

    stats = {"items": 0, "with_services": 0, "existing": 0}

    def add(m):
        item = m.group(0)
        stats["items"] += 1
        if "<SPECIAL_SERVICE>" in item:
            stats["existing"] += 1
            return item
        svc = services_for(item, rules)
        if not svc:
            return item
        stats["with_services"] += 1
        lines = "".join(f"    <SPECIAL_SERVICE>{escape(s, quote=False)}</SPECIAL_SERVICE>\n" for s in svc)
        return item[: -len("</SHOPITEM>")] + lines + "</SHOPITEM>"

    out = ITEM_RE.sub(add, xml)
    if stats["items"] == 0:
        sys.exit("Ve feedu nejsou žádné produkty, výstup se nepřepisuje.")

    out_path = base / rules.get("output", "output/heureka.xml")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(out, encoding="utf-8", newline="")
    os.replace(tmp, out_path)  # atomicky — Heuréka nikdy nestáhne rozepsaný soubor

    print(f"Produktů: {stats['items']}, se službami: {stats['with_services']}, "
          f"už měly SPECIAL_SERVICE (ponecháno): {stats['existing']}")
    print(f"Zapsáno: {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
