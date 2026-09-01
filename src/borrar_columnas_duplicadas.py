"""
Borra las 61 columnas duplicadas en Monday (identificadas por el diagnostico
anterior). Conserva siempre la copia que ya esta en uso en config.py.
Se corre una sola vez.
"""
import os
import time
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

IDS_A_BORRAR = [
    "color_mm6sy4p",
    "color_mm6sjj6j",
    "color_mm6sq6pg",
    "long_text_mm6sdpe1",
    "long_text_mm6sekmw",
    "color_mm6s7p9v",
    "long_text_mm6sv5f7",
    "color_mm6spe8j",
    "dropdown_mm6s80z0",
    "color_mm6sn3f2",
    "color_mm6sg7dz",
    "dropdown_mm6svbsg",
    "dropdown_mm6sdhev",
    "color_mm6sgfxk",
    "numeric_mm6s4y07",
    "numeric_mm6s1r7z",
    "numeric_mm6stmmx",
    "numeric_mm6svnbf",
    "dropdown_mm6smcpp",
    "dropdown_mm6sk2z1",
    "numeric_mm6ss7v0",
    "numeric_mm6se572",
    "dropdown_mm6szrh1",
    "dropdown_mm6s15kw",
    "color_mm6s57xv",
    "dropdown_mm6s5nd",
    "color_mm6sk0c8",
    "color_mm6sg0sn",
    "color_mm6shtkv",
    "color_mm6sfqyf",
    "color_mm6syvmh",
    "dropdown_mm6s801y",
    "color_mm6s1jqz",
    "color_mm6s6js5",
    "color_mm6saznk",
    "dropdown_mm6s96wx",
    "dropdown_mm6szy9q",
    "color_mm6stgp9",
    "color_mm6szxsq",
    "color_mm6sphmd",
    "dropdown_mm6sbrc9",
    "color_mm6swakc",
    "numeric_mm6s7c3c",
    "color_mm6scpe0",
    "color_mm6skamy",
    "dropdown_mm6sdfz3",
    "dropdown_mm6s92vn",
    "color_mm6sabem",
    "dropdown_mm6saawj",
    "dropdown_mm6sam8r",
    "long_text_mm6sv1tk",
    "color_mm6s2nb2",
    "dropdown_mm6saq42",
    "dropdown_mm6s2a0n",
    "color_mm6smrp4",
    "numeric_mm6sbksh",
    "color_mm6sxscq",
    "numeric_mm6sh6n2",
    "color_mm6sgd00",
    "color_mm6s5cqj",
    "dropdown_mm6s6t68"
]

MUTATION = """
mutation ($board: ID!, $column: String!) {
  delete_column (board_id: $board, column_id: $column) {
    id
  }
}
"""

print(f"Borrando {len(IDS_A_BORRAR)} columnas duplicadas...\n")
ok, fail = 0, 0
for col_id in IDS_A_BORRAR:
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": MUTATION, "variables": {"board": MONDAY_BOARD_ID, "column": col_id}},
        headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
        timeout=30,
    )
    data = resp.json()
    if "errors" in data:
        print(f"  ERROR borrando {col_id}: {data['errors']}")
        fail += 1
    else:
        print(f"  Borrada: {col_id}")
        ok += 1
    time.sleep(0.3)

print(f"\n=== Resumen: {ok} borradas, {fail} con error ===")
