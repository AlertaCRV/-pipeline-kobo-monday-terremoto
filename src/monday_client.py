"""
Cliente minimo para crear/actualizar items en Monday.com via su API GraphQL.

Todos los items nuevos van al unico grupo del tablero (MONDAY_DEFAULT_GROUP_ID
en config.py). El estado real de avance se registra en la columna Progreso,
no separando items en distintos grupos.

En DRY_RUN=true no se hace ninguna llamada de red: se imprime el payload
que se habria enviado, para poder revisar el resultado sin credenciales.
"""
import json
import requests
from config import DRY_RUN, MONDAY_API_TOKEN, MONDAY_API_URL, MONDAY_BOARD_ID, MONDAY_COLUMN_MAP, MONDAY_DEFAULT_GROUP_ID, PROGRESO_DEFAULT


def build_column_values(record: dict, score: dict) -> dict:
    combined = {**record, **score, "progreso": PROGRESO_DEFAULT}
    column_values = {}
    for campo, valor in combined.items():
        col_id = MONDAY_COLUMN_MAP.get(campo)
        if col_id and valor not in (None, ""):
            column_values[col_id] = str(valor)
    return column_values


def upsert_item(item_name: str, column_values: dict) -> dict:
    group_id = MONDAY_DEFAULT_GROUP_ID

    payload = {
        "query": """
            mutation ($board: ID!, $name: String!, $vals: JSON!, $group: String) {
              create_item(board_id: $board, item_name: $name, column_values: $vals, create_labels_if_missing: true, group_id: $group) {
                id
              }
            }
        """,
        "variables": {
            "board": MONDAY_BOARD_ID,
            "name": item_name,
            "vals": json.dumps(column_values, ensure_ascii=False),
            "group": group_id,
        },
    }

    if DRY_RUN:
        print(f"\n[DRY_RUN] Se crearia el item '{item_name}' en el tablero {MONDAY_BOARD_ID or '<sin definir>'}, grupo '{group_id}':")
        print(json.dumps(column_values, ensure_ascii=False, indent=2))
        return {"dry_run": True, "item_name": item_name, "column_values": column_values, "group_id": group_id}

    headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}
    resp = requests.post(MONDAY_API_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()
