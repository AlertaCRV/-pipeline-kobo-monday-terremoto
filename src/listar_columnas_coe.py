"""
Lista TODAS las columnas del tablero "COE: Análisis de situación" (solo
lectura, no borra ni modifica nada). El ID del tablero está fijo aquí
abajo -- es un tablero DISTINTO al de nuestro proyecto (Diagnóstico
terreno), así que no depende del secreto MONDAY_BOARD_ID.

Además, marca con [SOSPECHOSA] las columnas cuyo título coincide
exactamente con alguna de las que creamos para nuestro proyecto, para
facilitar identificarlas -- pero NO borra nada automáticamente.
"""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
BOARD_ID_COE = "18421997278"  # tablero "COE: Análisis de situación" -- NO es el nuestro
MONDAY_API_URL = "https://api.monday.com/v2"

# Nombres de columnas que SÍ creamos nosotros para el proyecto del terremoto
NUESTRAS_COLUMNAS = {
    "Tipo de área", "Estado", "Municipio", "Parroquia", "Comunidad / Sector",
    "Campamento", "Tipo de campamento", "Ubicación (mapa)", "Clasificación de comunidad",
    "Necesidades principales", "Prioridad 1", "Asistencia recibida", "Brechas sin atender",
    "Actores apoyando actualmente", "Riesgo de duplicación", "Familias (total)",
    "Personas (total)", "Familias afectadas", "Familias que no permanecen",
    "Edificaciones destruidas", "Edificaciones dañadas", "Viviendas dañadas (n.º)",
    "Apartamentos dañados (n.º)", "Servicios afectados", "Riesgos terremoto/réplicas",
    "Atención médica primaria activa", "Principal necesidad de salud",
    "Agua suficiente (comunidad)", "Fuente de agua (comunidad)",
    "Frecuencia de agua (comunidad)", "Calidad de agua (comunidad)", "Aguas negras / fugas",
    "Vectores/enfermedades (comunidad)", "Dificultad para obtener agua (comunidad)",
    "Fuente de agua (campamento)", "Agua suficiente (campamento)",
    "Vectores/enfermedades (campamento)", "Enfermedades reportadas (campamento)",
    "Puntos de lavado de manos (campamento)", "Estado de sanitarios (campamento)",
    "Suficiencia de sanitarios (campamento)", "Necesidades de alojamiento",
    "Riesgo que impide el retorno", "Familias que requieren alojamiento",
    "Intención de permanencia (campamento)", "Acceso a mercados",
    "Apoyo para reactivación económica", "Riesgos de protección",
    "Malestar emocional relevante", "Servicios SMAPS disponibles",
    "Grupos que requieren apoyo SMAPS", "Acceso vial", "Punto seguro de servicio",
    "Electricidad disponible", "Restricciones operacionales", "Condiciones del entorno",
    "Restricción operacional principal", "Prioridad preliminar", "Sectores prioritarios",
    "Requiere evaluación técnica", "Situación crítica", "Puntos Urgencia",
    "Nivel Urgencia", "Puntos Factibilidad", "Nivel Factibilidad", "Cuadrante",
    "Condiciones que dificultan distribución",
}

QUERY = """
query ($board: ID!) {
  boards (ids: [$board]) {
    name
    columns {
      id
      title
      type
    }
  }
}
"""

resp = requests.post(
    MONDAY_API_URL,
    json={"query": QUERY, "variables": {"board": BOARD_ID_COE}},
    headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()

if "errors" in data:
    print("ERROR:", data["errors"])
else:
    board = data["data"]["boards"][0]
    columns = board["columns"]
    print(f"Tablero: {board['name']}")
    print(f"Total de columnas: {len(columns)}\n")

    sospechosas = [c for c in columns if c["title"] in NUESTRAS_COLUMNAS]
    print(f"=== Columnas que coinciden con nuestro proyecto: {len(sospechosas)} ===\n")
    for c in sospechosas:
        print(f"  [SOSPECHOSA] {c['id']:<25} | {c['type']:<12} | {c['title']}")

    print(f"\n=== Resto de columnas del tablero (no tocar): {len(columns) - len(sospechosas)} ===\n")
    for c in columns:
        if c["title"] not in NUESTRAS_COLUMNAS:
            print(f"  {c['id']:<25} | {c['type']:<12} | {c['title']}")
