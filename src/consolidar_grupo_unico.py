"""
Revierte la separación en 3 grupos (Intervenida/Contactada/Evaluada) y deja
un solo grupo para todos los items. El estado de avance real se maneja
manualmente por el equipo en la columna "Progreso" (status), no por la
ubicación del item en el tablero.

Pasos:
1. Lista cuántos items hay en cada uno de los 3 grupos.
2. Mueve todos los items de "Contactada" e "Intervenida" hacia "Evaluada".
3. Renombra el grupo "Evaluada" a "Comunidades" (nombre neutral, ya que
   ahora es el único grupo y "Evaluada" también es una etiqueta de Progreso).
4. Borra los grupos "Contactada" e "Intervenida" (ya vacíos).

Se corre una sola vez.
"""
import os
import time
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}

GRUPO_DESTINO = "group_mm6w12kt"  # Evaluada -> se renombra a Comunidades
GRUPOS_A_ELIMINAR = ["group_mm6ws63p", "group_mm6wxey0"]  # Contactada, Intervenida

QUERY_ITEMS = """
query ($board: ID!) {
  boards (ids: [$board]) {
    groups {
      id
      title
      items_page (limit: 100) {
        items { id name }
      }
    }
  }
}
"""

MOVE_MUTATION = """
mutation ($item: ID!, $group: String!) {
  move_item_to_group (item_id: $item, group_id: $group) { id }
}
"""

RENAME_MUTATION = """
mutation ($board: ID!, $group: String!, $value: String!) {
  update_group (board_id: $board, group_id: $group, group_attribute: title, new_value: $value) { id }
}
"""

DELETE_GROUP_MUTATION = """
mutation ($board: ID!, $group: String!) {
  delete_group (board_id: $board, group_id: $group) { id }
}
"""


def graphql(query, variables):
    resp = requests.post(MONDAY_API_URL, json={"query": query, "variables": variables}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    data = graphql(QUERY_ITEMS, {"board": MONDAY_BOARD_ID})
    if "errors" in data:
        print("ERROR:", data["errors"])
        return

    groups = data["data"]["boards"][0]["groups"]
    print("=== Items por grupo (antes) ===")
    for g in groups:
        items = g["items_page"]["items"]
        print(f"  {g['title']} ({g['id']}): {len(items)} items")

    print("\n=== Moviendo items de Contactada/Intervenida a Evaluada ===")
    for g in groups:
        if g["id"] in GRUPOS_A_ELIMINAR:
            for it in g["items_page"]["items"]:
                move_data = graphql(MOVE_MUTATION, {"item": it["id"], "group": GRUPO_DESTINO})
                if "errors" in move_data:
                    print(f"  ERROR moviendo '{it['name']}': {move_data['errors']}")
                else:
                    print(f"  Movido: '{it['name']}'")
                time.sleep(0.3)

    print(f"\n=== Renombrando {GRUPO_DESTINO} a 'Comunidades' ===")
    rename_data = graphql(RENAME_MUTATION, {"board": MONDAY_BOARD_ID, "group": GRUPO_DESTINO, "value": "Comunidades"})
    if "errors" in rename_data:
        print(f"  ERROR: {rename_data['errors']}")
    else:
        print("  OK")

    print(f"\n=== Borrando grupos vacíos: {GRUPOS_A_ELIMINAR} ===")
    for group_id in GRUPOS_A_ELIMINAR:
        del_data = graphql(DELETE_GROUP_MUTATION, {"board": MONDAY_BOARD_ID, "group": group_id})
        if "errors" in del_data:
            print(f"  ERROR borrando {group_id}: {del_data['errors']}")
        else:
            print(f"  Borrado: {group_id}")
        time.sleep(0.3)


if __name__ == "__main__":
    main()
