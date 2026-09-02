"""
Lista los grupos (secciones) del tablero "Diagnostico terreno" con sus IDs
reales de Monday. Solo lectura, no modifica nada.
"""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

QUERY = """
query ($board: ID!) {
  boards (ids: [$board]) {
    groups {
      id
      title
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
    groups = data["data"]["boards"][0]["groups"]
    print(f"Total de grupos: {len(groups)}\n")
    for g in groups:
        print(f"  id={g['id']:<20} | title={g['title']}")
