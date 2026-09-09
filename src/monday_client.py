"""
Cliente minimo para crear/actualizar items en Monday.com via su API GraphQL.

Todos los items nuevos van al unico grupo del tablero (MONDAY_DEFAULT_GROUP_ID
en config.py). El estado real de avance se registra en la columna Progreso,
no separando items en distintos grupos.

Upsert real: cada item guarda el _id de su submission de Kobo en la
columna ID Kobo. fetch_kobo_id_map() lee esa columna para TODOS los
items de una sola vez, y sync.py usa ese mapa para decidir si crear un
item nuevo o actualizar uno existente -- asi, editar una respuesta ya
aplicada en Kobo se refleja en Monday sin borrar nada. Las columnas
manuales (Progreso, Mapa) nunca se tocan en una actualizacion.

En DRY_RUN=true no se hace ninguna llamada de red: se imprime el payload
que se habria enviado, para poder revisar el resultado sin credenciales.
"""
import json
import requests
from config import (
    DRY_RUN, KOBO_API_TOKEN, MONDAY_API_TOKEN, MONDAY_API_URL, MONDAY_BOARD_ID,
    MONDAY_COLUMN_MAP, MONDAY_DEFAULT_GROUP_ID, PROGRESO_DEFAULT, FOTOS_COLUMN_ID,
    KOBO_ID_COLUMN_ID, PROGRESO_COLUMN_ID, MONDAY_ONLY_COLUMN_IDS,
)

MONDAY_FILE_UPLOAD_URL = "https://api.monday.com/v2/file"


def build_column_values(record: dict, score: dict) -> dict:
    combined = {**record, **score, "progreso": PROGRESO_DEFAULT}
    column_values = {}
    for campo, valor in combined.items():
        col_id = MONDAY_COLUMN_MAP.get(campo)
        if col_id and valor not in (None, ""):
            column_values[col_id] = str(valor)
    return column_values


def fetch_valid_column_ids() -> set:
    """
    Devuelve el conjunto de column_id que realmente existen HOY en el
    tablero. Si alguien borra o cambia una columna en Monday sin avisar,
    esto evita que TODA una actualizacion falle por una sola columna
    invalida (Monday rechaza change_multiple_column_values entero si un
    solo column_id no existe).
    """
    if DRY_RUN:
        return set(MONDAY_COLUMN_MAP.values()) | {KOBO_ID_COLUMN_ID, FOTOS_COLUMN_ID} | MONDAY_ONLY_COLUMN_IDS

    query = "query ($board: ID!) { boards (ids: [$board]) { columns { id } } }"
    headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}
    resp = requests.post(MONDAY_API_URL, json={"query": query, "variables": {"board": MONDAY_BOARD_ID}},
                          headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        print("  ⚠️ No se pudo leer la lista de columnas:", data["errors"])
        return set(MONDAY_COLUMN_MAP.values()) | {KOBO_ID_COLUMN_ID, FOTOS_COLUMN_ID} | MONDAY_ONLY_COLUMN_IDS
    return {c["id"] for c in data["data"]["boards"][0]["columns"]}


def fetch_kobo_id_map() -> dict:
    """
    Devuelve {kobo_id: item_id} para todos los items actuales del tablero,
    leyendo la columna ID Kobo. Se llama UNA vez al inicio de sync.py.
    Siempre refleja el estado real de Monday (si alguien borro un item a
    mano, simplemente no aparece aqui -- no hay archivo de estado que se
    pueda desincronizar).
    """
    if DRY_RUN:
        print("[DRY_RUN] No se consulta el mapa de IDs de Kobo (se asume que todo es nuevo).")
        return {}

    query = """
        query ($board: ID!, $col: [String!]) {
          boards (ids: [$board]) {
            items_page (limit: 200) {
              items { id column_values (ids: $col) { text } }
            }
          }
        }
    """
    headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": query, "variables": {"board": MONDAY_BOARD_ID, "col": [KOBO_ID_COLUMN_ID]}},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        print("  ⚠️ No se pudo leer el mapa de IDs de Kobo:", data["errors"])
        return {}

    items = data["data"]["boards"][0]["items_page"]["items"]
    mapa = {}
    for it in items:
        texto = (it["column_values"][0]["text"] or "").strip()
        if texto:
            mapa[texto] = it["id"]
    return mapa


def upsert_item(item_name: str, column_values: dict, kobo_id: str) -> dict:
    """Crea un item NUEVO (usar solo cuando kobo_id no esta en fetch_kobo_id_map())."""
    group_id = MONDAY_DEFAULT_GROUP_ID
    column_values = {**column_values, KOBO_ID_COLUMN_ID: kobo_id}

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


def update_item(item_id: str, item_name: str, column_values: dict) -> dict:
    """
    Actualiza un item EXISTENTE con los valores actuales de Kobo. Nunca
    toca la columna Progreso ni las columnas manuales (ver
    MONDAY_ONLY_COLUMN_IDS en config.py), para no pisar el trabajo que el
    equipo hace directo en Monday.
    """
    column_values = {
        col_id: valor for col_id, valor in column_values.items()
        if col_id != PROGRESO_COLUMN_ID and col_id not in MONDAY_ONLY_COLUMN_IDS
    }

    payload = {
        "query": """
            mutation ($board: ID!, $item: ID!, $vals: JSON!) {
              change_multiple_column_values (board_id: $board, item_id: $item, column_values: $vals, create_labels_if_missing: true) {
                id
              }
            }
        """,
        "variables": {
            "board": MONDAY_BOARD_ID,
            "item": item_id,
            "vals": json.dumps(column_values, ensure_ascii=False),
        },
    }

    if DRY_RUN:
        print(f"\n[DRY_RUN] Se actualizaria el item '{item_name}' ({item_id}):")
        print(json.dumps(column_values, ensure_ascii=False, indent=2))
        return {"dry_run": True, "item_id": item_id, "column_values": column_values}

    headers = {"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}
    resp = requests.post(MONDAY_API_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_created_item_id(upsert_result: dict):
    """Extrae el id del item recien creado a partir del resultado de upsert_item."""
    try:
        return upsert_result["data"]["create_item"]["id"]
    except (KeyError, TypeError):
        return None


def upload_photos_to_item(item_id, attachments: list) -> None:
    """
    Descarga cada foto adjunta de la submission (via la API de Kobo) y la
    sube a la columna Fotos del item correspondiente en Monday.
    """
    if not attachments:
        return

    if DRY_RUN:
        print(f"[DRY_RUN] Se subirian {len(attachments)} foto(s) al item {item_id}, columna '{FOTOS_COLUMN_ID}'")
        return

    if not item_id:
        print("  ⚠️ No se pudo subir fotos: no hay item_id (¿fallo la creacion del item?).")
        return

    mutation = (
        "mutation add_file($file: File!) { "
        f'add_file_to_column (file: $file, item_id: {item_id}, column_id: "{FOTOS_COLUMN_ID}") {{ id }} '
        "}"
    )

    for att in attachments:
        url = att.get("download_url")
        if not url:
            continue
        filename = (att.get("filename") or "foto.jpg").split("/")[-1]

        img_resp = requests.get(url, headers={"Authorization": f"Token {KOBO_API_TOKEN}"}, timeout=60)
        img_resp.raise_for_status()

        upload_resp = requests.post(
            MONDAY_FILE_UPLOAD_URL,
            headers={"Authorization": MONDAY_API_TOKEN},
            data={"query": mutation},
            files={"variables[file]": (filename, img_resp.content)},
            timeout=60,
        )
        upload_resp.raise_for_status()
        result = upload_resp.json()
        if "errors" in result:
            print(f"  ❌ Error subiendo foto '{filename}' al item {item_id}: {result['errors']}")
        else:
            print(f"  📷 Foto subida: '{filename}' -> item {item_id}")
