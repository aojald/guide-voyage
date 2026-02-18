#!/usr/bin/env python3
"""Génère mae_slugs.json à partir de mae_liste_pays.html (nom FR normalisé → slug)."""
import json
import re
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HTML_PATH = SCRIPT_DIR / "mae_liste_pays.html"
OUTPUT_JSON = SCRIPT_DIR / "mae_slugs.json"


def normalize_name(name: str) -> str:
    """Même logique que côté JS : NFD, sans accents, minuscules, espaces simples, apostrophe unifiée."""
    if not name or not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFD", name)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[\u2019\u2018']", "'", s)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def main():
    html = HTML_PATH.read_text(encoding="utf-8")
    # href="fr/.../slug/" title="Nom"
    pattern = re.compile(
        r'href="fr/conseils-aux-voyageurs/conseils-par-pays-destination/([^/]+)/"[^>]*title="([^"]*)"',
        re.IGNORECASE,
    )
    slugs = {}
    for m in pattern.finditer(html):
        slug, name = m.group(1), m.group(2)
        key = normalize_name(name)
        if key and key not in slugs:
            slugs[key] = slug
    OUTPUT_JSON.write_text(json.dumps(slugs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Écrit {OUTPUT_JSON} : {len(slugs)} pays.")
    return 0


if __name__ == "__main__":
    exit(main())
