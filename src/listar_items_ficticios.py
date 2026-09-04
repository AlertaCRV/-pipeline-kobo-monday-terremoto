"""
Lista todos los items del tablero cuyo nombre contiene "(FICTICIO)"
(datos de prueba escritos por probar_escritura_monday.py), con su ID
y grupo, para poder borrarlos manualmente en Monday con confianza.
Solo lectura, no modifica nada.
"""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

QUERY = """
query ($board: ID!) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items {
        id
        name
        group { id title }
      }
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
    items = data["data"]["boards"][0]["items_page"]["items"]
    print(f"Total de items en el tablero: {len(items)}\n")

    ficticios = [it for it in items if "FICTICIO" in it["name"].upper()]
    print(f"=== Items FICTICIOS encontrados: {len(ficticios)} ===\n")
    for it in ficticios:
        print(f"  id={it['id']:<15} | grupo={it['group']['title']:<15} | nombre={it['name']}")

    otros = [it for it in items if it not in ficticios]
    if otros:
        print(f"\n=== Otros items (NO ficticios, no tocar) ===\n")
        for it in otros:
            print(f"  id={it['id']:<15} | grupo={it['group']['title']:<15} | nombre={it['name']}")
