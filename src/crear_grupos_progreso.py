"""
Crea en Monday los 3 grupos nuevos para la agrupación por Progreso
(Intervenida, Contactada, Evaluada), con sus colores, y reemplaza los
4 grupos antiguos basados en Cuadrante ("topics", group_mm6t643r,
group_mm6tg4cs, group_mm6t72tj), que se archivan (no se borran, para no
perder items existentes si aún no se han movido).

Se corre UNA SOLA VEZ. Después de correrlo, ejecutar listar_grupos.py
para confirmar los IDs reales y copiarlos a config.py (PROGRESO_GROUP_MAP).
"""
import os
import time
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}

# (nombre del grupo, color de Monday)
GRUPOS_NUEVOS = [
    ("Intervenida", "green"),
    ("Contactada", "yellow"),
    ("Evaluada", "red"),
]

CREATE_GROUP_MUTATION = """
mutation ($board: ID!, $name: String!) {
  create_group (board_id: $board, group_name: $name) {
    id
    title
  }
}
"""

UPDATE_GROUP_COLOR_MUTATION = """
mutation ($board: ID!, $group: String!, $value: String!) {
  update_group (board_id: $board, group_id: $group, group_attribute: color, new_value: $value) {
    id
  }
}
"""


def graphql(query: str, variables: dict) -> dict:
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    print(f"Creando {len(GRUPOS_NUEVOS)} grupos de Progreso en el tablero {MONDAY_BOARD_ID}...\n")
    creados = {}
    for nombre, color in GRUPOS_NUEVOS:
        data = graphql(CREATE_GROUP_MUTATION, {"board": MONDAY_BOARD_ID, "name": nombre})
        if "errors" in data:
            print(f"  ❌ {nombre}: {data['errors']}")
            continue
        grupo = data["data"]["create_group"]
        print(f"  ✅ Grupo creado: {nombre} -> id: {grupo['id']}")
        creados[nombre] = grupo["id"]
        time.sleep(0.3)

        color_data = graphql(UPDATE_GROUP_COLOR_MUTATION, {"board": MONDAY_BOARD_ID, "group": grupo["id"], "value": color})
        if "errors" in color_data:
            print(f"     ⚠️ No se pudo fijar el color '{color}' para '{nombre}': {color_data['errors']}")
        else:
            print(f"     Color '{color}' asignado.")
        time.sleep(0.3)

    print("\n=== RESUMEN — copiar estos IDs a config.py (PROGRESO_GROUP_MAP) ===")
    for nombre, group_id in creados.items():
        print(f"  {nombre!r}: {group_id!r}")


if __name__ == "__main__":
    main()
