"""
Prueba de escritura real en Monday, usando las 5 comunidades ficticias
(sin conectar a Kobo todavía -- eso se hace en un paso aparte).

Este script SIEMPRE escribe de verdad en Monday (usa el MONDAY_API_TOKEN y
MONDAY_BOARD_ID reales de los GitHub Secrets). No usa la variable DRY_RUN.
"""
import json
import os
import requests
from pathlib import Path
from scoring import compute_score
from transform import select_kpi_record, build_item_name

FIXTURE_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_submissions.json"
MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

from config import MONDAY_COLUMN_MAP


def build_column_values(record: dict, score: dict) -> dict:
    combined = {**record, **score}
    column_values = {}
    for campo, valor in combined.items():
        col_id = MONDAY_COLUMN_MAP.get(campo)
        if col_id and valor not in (None, ""):
            column_values[col_id] = str(valor)
    return column_values


def create_item(item_name: str, column_values: dict) -> dict:
    payload = {
        "query": """
            mutation ($board: ID!, $name: String!, $vals: JSON!) {
              create_item(board_id: $board, item_name: $name, column_values: $vals) {
                id
              }
            }
        """,
        "variables": {
            "board": MONDAY_BOARD_ID,
            "name": item_name,
            "vals": json.dumps(column_values, ensure_ascii=False),
        },
    }
    headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}
    resp = requests.post(MONDAY_API_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    print(f"Escribiendo {len(data)} comunidades ficticias en el tablero real {MONDAY_BOARD_ID}...\n")
    for raw in data:
        score = compute_score(raw)
        kpi_record = select_kpi_record(raw)
        item_name = build_item_name(raw)
        column_values = build_column_values(kpi_record, score)
        result = create_item(item_name, column_values)
        if "errors" in result:
            print(f"  ❌ {item_name}: {result['errors']}")
        else:
            print(f"  ✅ {item_name} -> {score['cuadrante']}")


if __name__ == "__main__":
    main()
