"""
Fija el color de los 3 grupos de Progreso ya creados en Monday
(Intervenida/Contactada/Evaluada), usando sus IDs reales devueltos por
crear_grupos_progreso.py. Se corre una sola vez, después de ese script.
"""
import os
import time
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}

GRUPOS = [
    ("group_mm6wxey0", "Intervenida", "green"),
    ("group_mm6ws63p", "Contactada", "yellow"),
    ("group_mm6w12kt", "Evaluada", "red"),
]

MUTATION = """
mutation ($board: ID!, $group: String!, $value: String!) {
  update_group (board_id: $board, group_id: $group, group_attribute: color, new_value: $value) {
    id
  }
}
"""


def main():
    for group_id, nombre, color in GRUPOS:
        resp = requests.post(
            MONDAY_API_URL,
            json={"query": MUTATION, "variables": {"board": MONDAY_BOARD_ID, "group": group_id, "value": color}},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            print(f"  ❌ {nombre} ({group_id}): {data['errors']}")
        else:
            print(f"  ✅ {nombre} ({group_id}) -> color '{color}' asignado")
        time.sleep(0.3)


if __name__ == "__main__":
    main()
