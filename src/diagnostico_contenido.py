"""
Diagnóstico de contenido -- SOLO LECTURA, no muestra valores reales.

Para cada submission, muestra si cada campo de nuestros 61 KPI + los 2
campos de cálculo (via_denuncia, estado_establecimiento) tiene o no tiene
respuesta (Sí/No), sin revelar el contenido de la respuesta.
"""
import json
import os
import requests

KOBO_API_TOKEN = os.environ["KOBO_API_TOKEN"]
KOBO_ASSET_UID = os.environ["KOBO_ASSET_UID"]
KOBO_BASE_URL = os.getenv("KOBO_BASE_URL", "https://kobo.ifrc.org")

KPI_FIELDS = json.loads(open("kpi_fields.json", encoding="utf-8").read())
CAMPOS_A_REVISAR = sorted({f["campo"] for f in KPI_FIELDS} | {"via_denuncia", "estado_establecimiento", "situacion_critica"})

url = f"{KOBO_BASE_URL}/api/v2/assets/{KOBO_ASSET_UID}/data.json"
headers = {"Authorization": f"Token {KOBO_API_TOKEN}"}
resp = requests.get(url, headers=headers, timeout=30)
resp.raise_for_status()
results = resp.json().get("results", [])

print(f"Total submissions: {len(results)}\n")

for sub in results:
    flat_keys = {k.split("/")[-1]: v for k, v in sub.items()}
    sid = sub.get("_id")
    con_dato = [c for c in CAMPOS_A_REVISAR if flat_keys.get(c) not in (None, "")]
    sin_dato = [c for c in CAMPOS_A_REVISAR if flat_keys.get(c) in (None, "")]
    print(f"--- Submission {sid} ---")
    print(f"  Campos CON respuesta: {len(con_dato)} / {len(CAMPOS_A_REVISAR)}")
    if con_dato:
        print(f"    -> {', '.join(con_dato[:15])}{' ...' if len(con_dato) > 15 else ''}")
    print()
