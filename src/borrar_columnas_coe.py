"""
Borra las 74 columnas "sospechosas" (importadas por error) del tablero
"COE: Analisis de situacion" (ID 18421997278). NO toca ninguna columna
que no este en esta lista explicita. Se corre una sola vez.
"""
import os
import time
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
BOARD_ID_COE = "18421997278"
MONDAY_API_URL = "https://api.monday.com/v2"

IDS_A_BORRAR = [
    "text_mm6rqhe2",
    "color_mm6r3v0h",
    "text_mm6r1fp3",
    "color_mm6rgr8t",
    "text_mm6rc5ms",
    "color_mm6r2avj",
    "color_mm6rm4gs",
    "text_mm6r46n",
    "color_mm6ry6nv",
    "text_mm6rs7fd",
    "long_text_mm6r8h4z",
    "long_text_mm6r9ykc",
    "text_mm6rma71",
    "long_text_mm6rte0x",
    "text_mm6rd0g0",
    "color_mm6rn5ss",
    "color_mm6r4by7",
    "color_mm6r34fw",
    "text_mm6r7ygq",
    "long_text_mm6rnabq",
    "text_mm6rmcyt",
    "color_mm6rq82p",
    "text_mm6r63gx",
    "dropdown_mm6rebcc",
    "text_mm6rbf44",
    "text_mm6rt75w",
    "text_mm6ryy87",
    "text_mm6rgqgg",
    "text_mm6rj2qj",
    "text_mm6r9vek",
    "text_mm6rnsy3",
    "text_mm6rgenw",
    "text_mm6rzbfh",
    "text_mm6r8wzd",
    "text_mm6r4a1n",
    "text_mm6r4qvt",
    "text_mm6rx6bd",
    "text_mm6rf0pp",
    "text_mm6r5ymf",
    "text_mm6rwwmw",
    "text_mm6r19hv",
    "text_mm6rnjtj",
    "text_mm6rqqeq",
    "text_mm6rtv4e",
    "text_mm6rfmmh",
    "text_mm6rr1xj",
    "text_mm6rt0gv",
    "text_mm6rsssf",
    "text_mm6rwqg9",
    "text_mm6rxjvy",
    "text_mm6r6fxr",
    "text_mm6rxgtk",
    "text_mm6rg3n6",
    "text_mm6rfgp9",
    "text_mm6r9kg8",
    "text_mm6rms14",
    "text_mm6rkasn",
    "text_mm6r5gr0",
    "text_mm6rrsdy",
    "text_mm6rvd3f",
    "text_mm6rn2me",
    "text_mm6r7jm",
    "text_mm6r3whd",
    "text_mm6r6d4q",
    "text_mm6rhwnd",
    "text_mm6r2h97",
    "text_mm6r32j8",
    "text_mm6r76gr",
    "text_mm6rrtfw",
    "text_mm6rgqpe",
    "text_mm6rzmz",
    "text_mm6rrcxg",
    "text_mm6r5a2k",
    "text_mm6rjfce",
    "color_mm6r3e2a"
]

MUTATION = """
mutation ($board: ID!, $column: String!) {
  delete_column (board_id: $board, column_id: $column) {
    id
  }
}
"""

print(f"Borrando {len(IDS_A_BORRAR)} columnas del tablero COE...\n")
ok, fail = 0, 0
for col_id in IDS_A_BORRAR:
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": MUTATION, "variables": {"board": BOARD_ID_COE, "column": col_id}},
        headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
        timeout=30,
    )
    data = resp.json()
    errors = data.get("errors")
    if errors:
        print("  ERROR borrando " + col_id + ": " + str(errors))
        fail += 1
    else:
        print("  Borrada: " + col_id)
        ok += 1
    time.sleep(0.3)

print(f"\n=== Resumen: {ok} borradas, {fail} con error ===")
