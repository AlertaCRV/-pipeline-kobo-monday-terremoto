"""
Rellena la columna "ID Kobo" en los items que ya existen en Monday
(creados antes de que existiera esa columna), emparejandolos con su
submission de Kobo por nombre exacto de item. Se corre UNA SOLA VEZ,
antes de la primera sincronizacion con la logica de upsert nueva --
si no se hace, esos items no se reconocen y sync.py los duplicaria.

Los items que no logren emparejarse por nombre se listan al final para
revisión manual (no se tocan).
"""
import os
import time
import requests
from kobo_client import get_new_submissions
from transform import flatten_submission, build_item_name
from config import KOBO_ID_COLUMN_ID, DRY_RUN

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

QUERY_ITEMS = """
query ($board: ID!, $col: [String!]) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items { id name column_values (ids: $col) { text } }
    }
  }
}
"""

MUTATION = """
mutation ($board: ID!, $item: ID!, $col: String!, $value: String!) {
  change_simple_column_value (board_id: $board, item_id: $item, column_id: $col, value: $value) {
    id
  }
}
"""

headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}


def main():
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": QUERY_ITEMS, "variables": {"board": MONDAY_BOARD_ID, "col": [KOBO_ID_COLUMN_ID]}},
        headers=headers, timeout=30,
    )
    resp.raise_for_status()
    items = resp.json()["data"]["boards"][0]["items_page"]["items"]

    sin_id = [it for it in items if not (it["column_values"][0]["text"] or "").strip()]
    print(f"Items en Monday: {len(items)} | Sin ID Kobo: {len(sin_id)}\n")

    submissions = get_new_submissions(since_id=0)
    nombre_a_kobo_id = {}
    for raw in submissions:
        flat = flatten_submission(raw)
        nombre = build_item_name(flat)
        nombre_a_kobo_id[nombre] = str(raw.get("_id"))

    emparejados, sin_pareja = 0, []
    for it in sin_id:
        kobo_id = nombre_a_kobo_id.get(it["name"])
        if not kobo_id:
            sin_pareja.append(it["name"])
            continue

        if DRY_RUN:
            print(f"  [DRY_RUN] Se asignaria ID Kobo {kobo_id} -> '{it['name']}'")
            emparejados += 1
            continue

        result = requests.post(
            MONDAY_API_URL,
            json={"query": MUTATION, "variables": {
                "board": MONDAY_BOARD_ID, "item": it["id"], "col": KOBO_ID_COLUMN_ID, "value": kobo_id,
            }},
            headers=headers, timeout=30,
        ).json()
        if "errors" in result:
            print(f"  ❌ Error en '{it['name']}': {result['errors']}")
        else:
            print(f"  ✅ '{it['name']}' -> ID Kobo {kobo_id}")
            emparejados += 1
        time.sleep(0.3)

    print(f"\n=== Resumen: {emparejados} emparejados, {len(sin_pareja)} sin pareja ===")
    if sin_pareja:
        print("Revisar manualmente (no se tocaron):")
        for nombre in sin_pareja:
            print(f"  - {nombre}")


if __name__ == "__main__":
    main()
