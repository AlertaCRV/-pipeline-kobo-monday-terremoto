"""
Agrega UNA columna nueva a Monday: "Condiciones que dificultan distribución"
(tipo Menú desplegable), correspondiente al nuevo campo condiciones_distribucion.

Se corre una sola vez. Al final imprime el ID de la columna creada -- cópialo
para completar MONDAY_COLUMN_MAP en config.py.
"""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

MUTATION = """
mutation ($board: ID!, $title: String!) {
  create_column (board_id: $board, title: $title, column_type: dropdown) {
    id
    title
  }
}
"""

resp = requests.post(
    MONDAY_API_URL,
    json={
        "query": MUTATION,
        "variables": {"board": MONDAY_BOARD_ID, "title": "Condiciones que dificultan distribución"},
    },
    headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()

if "errors" in data:
    print("ERROR:", data["errors"])
else:
    col = data["data"]["create_column"]
    print(f"Columna creada correctamente.")
    print(f"  Título: {col['title']}")
    print(f"  ID: {col['id']}")
    print("\nCopia este ID para agregarlo a MONDAY_COLUMN_MAP en config.py:")
    print(f'    "condiciones_distribucion": "{col["id"]}",')
