"""
Recrea la columna "Comunidad / Sector" (tipo Texto largo), borrada en
algun momento del tablero de Monday. Se corre una sola vez; despues hay
que actualizar MONDAY_COLUMN_MAP en config.py con el nuevo id.
"""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

MUTATION = """
mutation ($board: ID!, $title: String!) {
  create_column (board_id: $board, title: $title, column_type: long_text) {
    id
    title
  }
}
"""


def main():
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": MUTATION, "variables": {"board": MONDAY_BOARD_ID, "title": "Comunidad / Sector"}},
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
    print("Copiar este id a config.py (MONDAY_COLUMN_MAP['sector_comunidad']).")


if __name__ == "__main__":
    main()
