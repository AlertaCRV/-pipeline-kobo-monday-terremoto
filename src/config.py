"""
Configuración del pipeline Kobo -> Monday.

Nada de esto contiene credenciales reales. Todo se lee de variables de entorno
(en producción: GitHub Secrets). En modo de prueba (DRY_RUN=true) el script
nunca llama a la API real de Kobo ni de Monday.
"""
import os

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

KOBO_API_TOKEN = os.getenv("KOBO_API_TOKEN", "")
KOBO_ASSET_UID = os.getenv("KOBO_ASSET_UID", "")
KOBO_BASE_URL = os.getenv("KOBO_BASE_URL", "https://kf.kobotoolbox.org")

MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN", "")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID", "")
MONDAY_API_URL = "https://api.monday.com/v2"

MONDAY_COLUMN_MAP = {
    # "campo_kobo": "id_columna_monday"
    # se completa junto con la creación real del tablero
}
