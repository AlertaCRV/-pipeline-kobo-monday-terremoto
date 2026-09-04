"""
Diagnóstico de solo lectura: muestra cuántas submissions hay en Kobo y el
rango de sus _id (mínimo y máximo), sin imprimir ningún valor de las
respuestas. Sirve para comparar contra ultimo_id_sincronizado.txt y
entender por qué sync.py no encuentra submissions nuevas.
"""
import os
import requests

KOBO_API_TOKEN = os.environ["KOBO_API_TOKEN"]
KOBO_ASSET_UID = os.environ["KOBO_ASSET_UID"]
KOBO_BASE_URL = os.getenv("KOBO_BASE_URL", "https://kobo.ifrc.org")

url = f"{KOBO_BASE_URL}/api/v2/assets/{KOBO_ASSET_UID}/data.json"
headers = {"Authorization": f"Token {KOBO_API_TOKEN}"}

print(f"Conectando a: {url}\n")
resp = requests.get(url, headers=headers, timeout=30)
print(f"Código de respuesta HTTP: {resp.status_code}\n")
resp.raise_for_status()
data = resp.json()
results = data.get("results", [])

print(f"Total de submissions encontradas (esta página): {len(results)}")
print(f"'count' reportado por la API: {data.get('count')}")

ids = sorted(r.get("_id", 0) for r in results)
if ids:
    print(f"_id mínimo: {ids[0]}")
    print(f"_id máximo: {ids[-1]}")
    print(f"Primeros 10 _id: {ids[:10]}")
    print(f"Últimos 10 _id: {ids[-10:]}")
else:
    print("No hay submissions todavía en este formulario.")
