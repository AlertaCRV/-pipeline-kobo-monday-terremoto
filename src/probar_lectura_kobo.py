"""
Prueba de conexión real a Kobo -- SOLO LECTURA, sin escribir en Monday.

Por seguridad, este script NUNCA imprime los valores de las respuestas
(podrían incluir información sensible). Solo muestra:
  - Cuántas submissions hay en total.
  - Los nombres de los campos de la primera submission (para revisar si
    vienen con prefijo de grupo, ej. "6. Afectación.../n_lesionados").
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

print(f"Total de submissions encontradas: {len(results)}\n")

if results:
    print("Nombres de los campos de la primera submission (sin mostrar valores):")
    for key in sorted(results[0].keys()):
        print(f"  - {key}")
else:
    print("No hay submissions todavía en este formulario.")
