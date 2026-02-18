#!/usr/bin/env python3
"""
Génère index.html à partir du fichier Excel referentiel_données.xlsx.
Usage : python3 build_from_excel.py
(Lancer depuis le dossier guide-voyage ou le dossier parent du projet.)
"""
import zipfile
import xml.etree.ElementTree as ET
import json
import re
import os
from pathlib import Path
from datetime import datetime

try:
    from country_tips import build_tips_json
except ImportError:
    build_tips_json = None

SCRIPT_DIR = Path(__file__).resolve().parent
EXCEL_PATH = SCRIPT_DIR / "referentiel_données.xlsx"
TEMPLATE_PATH = SCRIPT_DIR / "index_template.html"
OUTPUT_HTML = SCRIPT_DIR / "index.html"
MAE_SLUGS_JSON = SCRIPT_DIR / "mae_slugs.json"
MAE_OVERRIDE_JSON = SCRIPT_DIR / "mae_slugs_override.json"


def col_letter_to_idx(ref):
    m = re.match(r"^([A-Z]+)", ref)
    if not m:
        return 0
    s = m.group(1)
    return sum((ord(c) - 64) * (26**i) for i, c in enumerate(s[::-1])) - 1


def xlsx_shared_strings(zipf):
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    try:
        with zipf.open("xl/sharedStrings.xml") as f:
            tree = ET.parse(f)
    except KeyError:
        return []
    root = tree.getroot()
    strings = []
    for si in root.findall("main:si", ns):
        t = si.find("main:t", ns)
        if t is not None and t.text is not None:
            strings.append(t.text)
        else:
            parts = []
            for r in si.findall("main:r", ns):
                t_el = r.find("main:t", ns)
                parts.append(t_el.text if t_el is not None and t_el.text else "")
            strings.append("".join(parts))
    return strings


def parse_bool(val):
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("yes", "oui", "1", "true", "x", "o")


def read_excel_rows(path):
    """Lit le premier onglet et retourne (headers, list of row dicts)."""
    with zipfile.ZipFile(path, "r") as z:
        strings = xlsx_shared_strings(z)
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        with z.open("xl/worksheets/sheet1.xml") as f:
            tree = ET.parse(f)
        root = tree.getroot()
        sheet_data = root.find("main:sheetData", ns)
        rows_el = sheet_data.findall("main:row", ns) if sheet_data is not None else []
        if not rows_el:
            return [], []

        def cell_value(c, strings):
            t = c.get("t", "")
            v_el = c.find("main:v", ns)
            v = v_el.text if v_el is not None else ""
            if t == "s" and v:
                try:
                    idx = int(v)
                    v = strings[idx] if idx < len(strings) else v
                except ValueError:
                    pass
            return v.strip() if isinstance(v, str) else v

        # Ligne 1 = en-têtes
        first = rows_el[0]
        cells_1 = first.findall("main:c", ns)
        headers = [None] * 25
        for c in cells_1:
            ref = c.get("r", "")
            col = col_letter_to_idx(ref)
            headers[col] = cell_value(c, strings) or ""

        # Indices des colonnes (noms attendus dans l'Excel)
        code_col = 0
        name_en_col = 1
        name_fr_col = 2
        risk_col = 3
        blocked_col = 4
        customs_col = 5
        data_risk_col = 6
        forfait_col = 7
        comments_col = 8

        # Vérifier que la première cellule ressemble à "Code"
        if headers[0] and "code" not in (headers[0] or "").lower():
            for i, h in enumerate(headers):
                if h and "code" in (h or "").lower() and "name" not in (h or "").lower():
                    code_col = i
                    break

        out = []
        for row in rows_el[1:]:
            cells = row.findall("main:c", ns)
            row_vals = [None] * 25
            for c in cells:
                ref = c.get("r", "")
                col = col_letter_to_idx(ref)
                row_vals[col] = cell_value(c, strings)
            code = (row_vals[code_col] or "").strip()
            name_fr = (row_vals[name_fr_col] or row_vals[name_en_col] or "").strip()
            if not code or not name_fr:
                continue
            risk_color = (row_vals[risk_col] or "").strip()
            blocked = parse_bool(row_vals[blocked_col])
            customs_risk = parse_bool(row_vals[customs_col])
            local_data_risk = parse_bool(row_vals[data_risk_col])
            forfait4g = parse_bool(row_vals[forfait_col])
            comments = (row_vals[comments_col] or "").strip()

            out.append({
                "code": code,
                "nom": name_fr,
                "nomEN": (row_vals[name_en_col] or "").strip(),
                "riskColor": risk_color,
                "blocked": blocked,
                "cleanDevice": customs_risk,
                "cleanOnReturn": local_data_risk,
                "olaflySim": not forfait4g,
                "notifyAssistants": bool(risk_color),
                "quarantineRisk": risk_color and str(risk_color).lower() in ("red", "rouge"),
                "comments": comments,
            })
        return headers, out


def main():
    if not EXCEL_PATH.exists():
        print(f"Fichier Excel introuvable : {EXCEL_PATH}")
        return 1
    if not TEMPLATE_PATH.exists():
        print(f"Template introuvable : {TEMPLATE_PATH}")
        return 1

    _, rows = read_excel_rows(EXCEL_PATH)
    rows.sort(key=lambda p: p["nom"].lower())
    json_data = json.dumps(rows, ensure_ascii=False, indent=2)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if "__PAYS_JSON__" not in template:
        print("Le template doit contenir la chaîne __PAYS_JSON__")
        return 1
    html = template.replace("__PAYS_JSON__", json_data)

    if "__TIPS_JSON__" in template and build_tips_json is not None:
        codes = [r["code"] for r in rows]
        tips = build_tips_json(codes)
        tips_json = json.dumps(tips, ensure_ascii=False)
        html = html.replace("__TIPS_JSON__", tips_json)
    elif "__TIPS_JSON__" in template:
        html = html.replace("__TIPS_JSON__", "{}")

    if "__MAE_SLUGS_JSON__" in template:
        mae_slugs = json.loads(MAE_SLUGS_JSON.read_text(encoding="utf-8")) if MAE_SLUGS_JSON.exists() else {}
        html = html.replace("__MAE_SLUGS_JSON__", json.dumps(mae_slugs, ensure_ascii=False))
    if "__MAE_OVERRIDE_JSON__" in template:
        mae_override = json.loads(MAE_OVERRIDE_JSON.read_text(encoding="utf-8")) if MAE_OVERRIDE_JSON.exists() else {}
        html = html.replace("__MAE_OVERRIDE_JSON__", json.dumps(mae_override, ensure_ascii=False))

    generation_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
    if "__GENERATION_DATE__" in html:
        html = html.replace("__GENERATION_DATE__", generation_date)

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Généré : {OUTPUT_HTML} ({len(rows)} pays)")
    return 0


if __name__ == "__main__":
    exit(main())
