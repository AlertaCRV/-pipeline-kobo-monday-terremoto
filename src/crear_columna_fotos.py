"""
Crea la columna "Fotos" (tipo Archivo) en el tablero de Monday, donde se
subiran las fotos adjuntas en el grupo repetible "grupo_fotos" del
formulario de Kobo. Se corre una sola vez.
"""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

MUTATION = """
mutation ($board: ID!, $title: String!) {
  create_column (board_id: $board, title: $title, column_type: file) {
    id
    title
  }
}
"""


def main():
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": MUTATION, "variables": {"board": MONDAY_BOARD_ID, "title": "Fotos"}},
        headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        print("ERROR:", data["errors"])
        return
    col = data["data"]["create_column"]
    print(f"Columna creada: {col['title']} -> id: {col['id']}")
    print("Copiar este id a config.py (FOTOS_COLUMN_ID).")


if __name__ == "__main__":
    main()
