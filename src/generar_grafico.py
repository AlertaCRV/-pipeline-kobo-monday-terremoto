"""
Genera una pagina HTML con la matriz de decision Urgencia x Factibilidad,
usando los datos REALES actuales del tablero de Monday (via API).

Se guarda en docs/index.html -- GitHub Pages la publica automaticamente.

Version 3:
  - Paleta coherente: cada zona usa una version clara de SU PROPIO color,
    y ese mismo color aparece a saturacion completa en la leyenda.
  - Leyenda con una descripcion breve de que significa cada cuadrante,
    no solo su nombre.
  - Puntos que caen muy cerca entre si se separan visualmente con una
    linea guia delgada hacia su posicion real (sin alterar el dato).
  - Titulo: "Matriz de Urgencia x Factibilidad (Comunidades)".
"""
import os
import math
import datetime
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

COLS = {
    "puntos_urgencia": "numeric_mm6rzmct",
    "puntos_factibilidad": "numeric_mm6rfwcg",
    "cuadrante": "color_mm6rzjwx",
    "familias": "numeric_mm6r640v",
}
COL_IDS = list(COLS.values())

QUERY = """
query ($board: ID!, $cols: [String!]) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items { id name column_values (ids: $cols) { id text } }
    }
  }
}
"""

PUNTO_COLOR = "#1C4269"

# (color de zona a saturacion plena, numero romano, nombre, descripcion breve)
ZONE_INFO = {
    ("alta_urg", "alta_fac"):  ("#A63A2E", "I", "Intervenir ya",
        "Urgente y con buen acceso: desplegar de inmediato."),
    ("alta_urg", "media_fac"): ("#C9822E", "III", "Intervenir con gestión de riesgo",
        "Urgente con dificultades moderadas: actuar con planificación."),
    ("alta_urg", "baja_fac"):  ("#8C2F26", "II", "Resolver acceso primero",
        "Urgente pero con acceso bloqueado: gestionar la vía antes de desplegar."),
    ("baja_urg", "alta_fac"):  ("#3F7D6B", "IV", "Oportunidad",
        "No urgente y de
