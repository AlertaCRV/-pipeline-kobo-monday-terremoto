"""
Renombra la columna "Mapa y fotos" (text_mm6vbwtv) a simplemente "Mapa",
ahora que las fotos tienen su propia columna dedicada ("Fotos").
Se corre una sola vez.
"""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

MAPA_COLUMN_ID = "text_mm6vbwtv"

MUTATION = """
mutation ($board: ID!, $column: String!, $title: String!) {
  change_column_title (board_id: $board, column_id: $column, title: $title) {
    id
    title
  }
}
"""


def main():
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": MUTATION, "variables": {"board": MONDAY_BOARD_ID, "column": MAPA_COLUMN_ID, "title": "Mapa"}},
        headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        print("ERROR:", data["errors"])
        return
    col = data["data"]["change_column_title"]
    print(f"Columna renombrada -> id: {col['id']}, nuevo titulo: {col['title']}")


if __name__ == "__main__":
    main()
