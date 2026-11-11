"""Diagnostico puntual: compara, para los items cuyo nombre coincide con
los pasados por argumento, cuantas fotos hay en 3 lugares distintos:
  1. La columna Fotos en Monday (column_values -> value, JSON de archivos)
  2. El campo "assets" del item en Monday (lo que usa generar_resumen.py
     para descargar fotos a la web)
  3. Los adjuntos de la submission en Kobo (_attachments)
Solo lectura, no sube ni borra nada."""
import json
import os
import sys
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"
KOBO_API_TOKEN = os.environ["KOBO_API_TOKEN"]
KOBO_ASSET_UID = os.environ["KOBO_ASSET_UID"]
KOBO_BASE_URL = os.getenv("KOBO_BASE_URL", "https://kobo.ifrc.org")

FOTOS_COLUMN_ID = "file_mm71v7va"
KOBO_ID_COLUMN_ID = "text_mm718zj1"

QUERY = """
query ($board: ID!, $cols: [String!]) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items {
        id name
        column_values (ids: $cols) { id value }
        assets { id name public_url }
      }
    }
  }
}
"""

nombres_buscados = sys.argv[1:]

resp = requests.post(
    MONDAY_API_URL,
    json={"query": QUERY, "variables": {"board": MONDAY_BOARD_ID, "cols": [FOTOS_COLUMN_ID, KOBO_ID_COLUMN_ID]}},
    headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
    timeout=30,
)
resp.raise_for_status()
items = resp.json()["data"]["boards"][0]["items_page"]["items"]

kobo_resp = requests.get(
    f"{KOBO_BASE_URL}/api/v2/assets/{KOBO_ASSET_UID}/data.json",
    headers={"Authorization": f"Token {KOBO_API_TOKEN}"},
    timeout=30,
)
kobo_resp.raise_for_status()
kobo_subs = {str(s.get("_id")): s for s in kobo_resp.json().get("results", [])}

for it in items:
    if not any(n.lower() in it["name"].lower() for n in nombres_buscados):
        continue

    vals = {cv["id"]: cv for cv in it["column_values"]}
    kobo_id = (vals.get(KOBO_ID_COLUMN_ID) or {}).get("value")
    kobo_id = json.loads(kobo_id) if kobo_id else None

    valor_col_fotos = (vals.get(FOTOS_COLUMN_ID) or {}).get("value")
    archivos_col = []
    if valor_col_fotos:
        try:
            archivos_col = [f.get("name") for f in json.loads(valor_col_fotos).get("files", [])]
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    assets = it.get("assets") or []
    nombres_assets = [a.get("name") for a in assets]

    print(f"=== {it['name']} (item {it['id']}, kobo_id={kobo_id}) ===")
    print(f"  Columna 'Fotos' (value/files):  {len(archivos_col)} -> {archivos_col}")
    print(f"  item.assets (usado por la web): {len(nombres_assets)} -> {nombres_assets}")

    sub = kobo_subs.get(str(kobo_id)) if kobo_id else None
    if sub is not None:
        adjuntos = sub.get("_attachments", []) or []
        nombres_kobo = [a.get("filename", "").split("/")[-1] for a in adjuntos]
        print(f"  Kobo _attachments:              {len(nombres_kobo)} -> {nombres_kobo}")
    else:
        print("  Kobo _attachments:              (no se encontró la submission por kobo_id)")
    print()
