"""Diagnostico puntual: muestra ubicacion y personas_actuales para items
cuyo nombre coincide con los pasados por argumento. Solo lectura."""
import os
import sys
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

COLS = {"ubicacion": "long_text_mm6rwcs", "personas": "numeric_mm6rst2h"}

QUERY = """
query ($board: ID!, $cols: [String!]) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items { id name column_values (ids: $cols) { id text } }
    }
  }
}
"""

nombres_buscados = sys.argv[1:]

resp = requests.post(
    MONDAY_API_URL,
    json={"query": QUERY, "variables": {"board": MONDAY_BOARD_ID, "cols": list(COLS.values())}},
    headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
    timeout=30,
)
resp.raise_for_status()
items = resp.json()["data"]["boards"][0]["items_page"]["items"]

for it in items:
    if any(n.lower() in it["name"].lower() for n in nombres_buscados):
        vals = {cv["id"]: cv["text"] for cv in it["column_values"]}
        print(f"{it['name']}:")
        print(f"  Ubicación: {vals.get(COLS['ubicacion'])}")
        print(f"  Personas (total): {vals.get(COLS['personas'])}")
