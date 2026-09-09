"""
Borra TODOS los items del tablero (todas las comunidades/campamentos
sincronizados hasta ahora), para permitir una resincronizacion limpia
despues de ediciones al cuestionario de Kobo.

Se corre a pedido explicito del usuario. No toca columnas ni grupos,
solo los items (filas).
"""
import os
import time
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}

QUERY_ITEMS = """
query ($board: ID!) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items { id name }
    }
  }
}
"""

DELETE_MUTATION = """
mutation ($item: ID!) {
  delete_item (item_id: $item) { id }
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
    items = data["data"]["boards"][0]["items_page"]["items"]
    print(f"Total de items a borrar: {len(items)}\n")

    borrados, fallidos = 0, 0
    for it in items:
        del_data = graphql(DELETE_MUTATION, {"item": it["id"]})
        if "errors" in del_data:
            print(f"  ERROR borrando '{it['name']}' ({it['id']}): {del_data['errors']}")
            fallidos += 1
        else:
            print(f"  Borrado: '{it['name']}'")
            borrados += 1
        time.sleep(0.3)

    print(f"\n=== Resumen: {borrados} borrados, {fallidos} con error ===")


if __name__ == "__main__":
    main()
