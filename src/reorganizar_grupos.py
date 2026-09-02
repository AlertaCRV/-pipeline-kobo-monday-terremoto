"""
Reorganiza los items EXISTENTES en el tablero, moviendolos al grupo
correcto segun el valor actual de su columna Cuadrante. Se corre una
sola vez, despues de haber creado los grupos en Monday.
"""
import os
import time
import requests
from config import CUADRANTE_GROUP_MAP

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"
CUADRANTE_COLUMN_ID = "color_mm6rzjwx"

QUERY_ITEMS = """
query ($board: ID!, $col: [String!]) {
  boards (ids: [$board]) {
    items_page (limit: 100) {
      items {
        id
        name
        group { id title }
        column_values (ids: $col) { text }
      }
    }
  }
}
"""

MOVE_MUTATION = """
mutation ($item: ID!, $group: String!) {
  move_item_to_group (item_id: $item, group_id: $group) {
    id
  }
}
"""

headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}

resp = requests.post(
    MONDAY_API_URL,
    json={"query": QUERY_ITEMS, "variables": {"board": MONDAY_BOARD_ID, "col": [CUADRANTE_COLUMN_ID]}},
    headers=headers,
    timeout=30,
)
resp.raise_for_status()
data = resp.json()

if "errors" in data:
    print("ERROR:", data["errors"])
else:
    items = data["data"]["boards"][0]["items_page"]["items"]
    print(f"Total de items encontrados: {len(items)}\n")

    movidos, sin_cambio, sin_cuadrante = 0, 0, 0
    for item in items:
        cuadrante_texto = item["column_values"][0]["text"]
        grupo_actual = item["group"]["id"]

        if not cuadrante_texto:
            print(f"  [SIN CUADRANTE] {item['name']}")
            sin_cuadrante += 1
            continue

        grupo_destino = CUADRANTE_GROUP_MAP.get(cuadrante_texto)
        if not grupo_destino:
            print(f"  [SIN MAPEO] {item['name']} -> Cuadrante='{cuadrante_texto}' (no está en CUADRANTE_GROUP_MAP)")
            continue

        if grupo_actual == grupo_destino:
            sin_cambio += 1
            continue

        move_resp = requests.post(
            MONDAY_API_URL,
            json={"query": MOVE_MUTATION, "variables": {"item": item["id"], "group": grupo_destino}},
            headers=headers,
            timeout=30,
        )
        move_data = move_resp.json()
        if "errors" in move_data:
            print(f"  ERROR moviendo '{item['name']}': {move_data['errors']}")
        else:
            print(f"  Movido: '{item['name']}' -> {cuadrante_texto}")
            movidos += 1
        time.sleep(0.3)

    print(f"\n=== Resumen: {movidos} movidos, {sin_cambio} ya estaban correctos, {sin_cuadrante} sin dato de Cuadrante ===")
