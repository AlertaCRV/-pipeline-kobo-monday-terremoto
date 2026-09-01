"""
Lista TODAS las columnas actuales del tablero de Monday (solo lectura,
no borra ni modifica nada). Sirve para diagnosticar duplicados.
"""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

QUERY = """
query ($board: ID!) {
  boards (ids: [$board]) {
    columns {
      id
      title
      type
    }
  }
}
"""

resp = requests.post(
    MONDAY_API_URL,
    json={"query": QUERY, "variables": {"board": MONDAY_BOARD_ID}},
    headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()

if "errors" in data:
    print("ERROR:", data["errors"])
else:
    columns = data["data"]["boards"][0]["columns"]
    print(f"Total de columnas: {len(columns)}\n")

    from collections import Counter
    titulos = [c["title"] for c in columns]
    conteo = Counter(titulos)
    duplicados = {t: n for t, n in conteo.items() if n > 1}

    if duplicados:
        print(f"=== TÍTULOS DUPLICADOS ({len(duplicados)}) ===")
        for titulo, n in duplicados.items():
            print(f"  '{titulo}' aparece {n} veces:")
            for c in columns:
                if c["title"] == titulo:
                    print(f"      id={c['id']}  tipo={c['type']}")
        print()
    else:
        print("No se detectaron títulos duplicados.\n")

    print("=== LISTADO COMPLETO ===")
    for c in columns:
        print(f"  {c['id']:<25} | {c['type']:<12} | {c['title']}")
