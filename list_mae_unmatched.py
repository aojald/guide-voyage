#!/usr/bin/env python3
"""Affiche la liste des pays du référentiel Excel sans correspondance (mae_slugs + override)."""
import json
import re
import unicodedata
from pathlib import Path

from build_from_excel import EXCEL_PATH, MAE_SLUGS_JSON, MAE_OVERRIDE_JSON, read_excel_rows

SCRIPT_DIR = Path(__file__).resolve().parent


def normalize_name(name: str) -> str:
    """Même logique que dans le template JS et build_mae_slugs."""
    if not name or not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFD", name)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[\u2019\u2018']", "'", s)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def main():
    if not EXCEL_PATH.exists():
        print(f"Fichier Excel introuvable : {EXCEL_PATH}")
        return 1
    if not MAE_SLUGS_JSON.exists():
        print(f"Fichier {MAE_SLUGS_JSON} introuvable. Lancez d'abord : python3 build_mae_slugs.py")
        return 1

    _, rows = read_excel_rows(EXCEL_PATH)
    mae_slugs = json.loads(MAE_SLUGS_JSON.read_text(encoding="utf-8"))
    mae_override = json.loads(MAE_OVERRIDE_JSON.read_text(encoding="utf-8")) if MAE_OVERRIDE_JSON.exists() else {}

    unmatched = []
    for p in rows:
        code = (p.get("code") or "").strip().upper()
        if code in mae_override:
            continue
        nom = p.get("nom") or ""
        key = normalize_name(nom)
        if key and key not in mae_slugs:
            unmatched.append({"code": p.get("code", ""), "nom": nom})

    out_path = SCRIPT_DIR / "mae_unmatched.txt"
    lines = [
        f"Pays sans match MAE ({len(unmatched)} sur {len(rows)})\n",
        "Code | Nom (FR)",
        "-----|--------",
    ]
    for p in sorted(unmatched, key=lambda x: (x["nom"].lower(), x["code"])):
        lines.append(f"{p['code']:4} | {p['nom']}")
    text = "\n".join(lines)
    print(text)
    out_path.write_text(text, encoding="utf-8")
    print(f"\nListe enregistrée dans : {out_path}")
    return 0


if __name__ == "__main__":
    exit(main())
