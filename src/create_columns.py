"""
Crea automáticamente en Monday las 66 columnas del tablero
"Diagnóstico terreno — Terremoto 2026", con el tipo correcto para cada una
(Estado, Menú desplegable, Números o Texto largo).

Este script se corre UNA SOLA VEZ, para poblar el tablero. Después de eso,
el pipeline diario (sync.py) solo llena datos en las columnas ya creadas.

Requiere las variables de entorno MONDAY_API_TOKEN y MONDAY_BOARD_ID
(ya guardadas como GitHub Secrets).
"""
import json
import os
import time
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

TYPE_MAP = {
    "Estado": "status",
    "Menú desplegable": "dropdown",
    "Números": "numbers",
    "Texto largo": "long_text",
}

KPI_COLUMNS = [
    ("Tipo de área", "Estado"), ("Estado", "Estado"), ("Municipio", "Estado"), ("Parroquia", "Estado"),
    ("Comunidad / Sector", "Texto largo"), ("Campamento", "Texto largo"), ("Tipo de campamento", "Estado"),
    ("Ubicación (mapa)", "Texto largo"), ("Clasificación de comunidad", "Estado"),
    ("Necesidades principales", "Menú desplegable"), ("Prioridad 1", "Estado"), ("Asistencia recibida", "Estado"),
    ("Brechas sin atender", "Menú desplegable"), ("Actores apoyando actualmente", "Menú desplegable"),
    ("Riesgo de duplicación", "Estado"), ("Familias (total)", "Números"), ("Personas (total)", "Números"),
    ("Familias afectadas", "Números"), ("Familias que no permanecen", "Números"),
    ("Edificaciones destruidas", "Menú desplegable"), ("Edificaciones dañadas", "Menú desplegable"),
    ("Viviendas dañadas (n.º)", "Números"), ("Apartamentos dañados (n.º)", "Números"),
    ("Servicios afectados", "Menú desplegable"), ("Riesgos terremoto/réplicas", "Menú desplegable"),
    ("Atención médica primaria activa", "Estado"), ("Principal necesidad de salud", "Menú desplegable"),
    ("Agua suficiente (comunidad)", "Estado"), ("Fuente de agua (comunidad)", "Estado"),
    ("Frecuencia de agua (comunidad)", "Estado"), ("Calidad de agua (comunidad)", "Estado"),
    ("Aguas negras / fugas", "Estado"), ("Vectores/enfermedades (comunidad)", "Menú desplegable"),
    ("Dificultad para obtener agua (comunidad)", "Estado"), ("Fuente de agua (campamento)", "Estado"),
    ("Agua suficiente (campamento)", "Estado"), ("Vectores/enfermedades (campamento)", "Menú desplegable"),
    ("Enfermedades reportadas (campamento)", "Menú desplegable"), ("Puntos de lavado de manos (campamento)", "Estado"),
    ("Estado de sanitarios (campamento)", "Estado"), ("Suficiencia de sanitarios (campamento)", "Estado"),
    ("Necesidades de alojamiento", "Menú desplegable"), ("Riesgo que impide el retorno", "Estado"),
    ("Familias que requieren alojamiento", "Números"), ("Intención de permanencia (campamento)", "Estado"),
    ("Acceso a mercados", "Estado"), ("Apoyo para reactivación económica", "Menú desplegable"),
    ("Riesgos de protección", "Menú desplegable"), ("Malestar emocional relevante", "Estado"),
    ("Servicios SMAPS disponibles", "Menú desplegable"), ("Grupos que requieren apoyo SMAPS", "Menú desplegable"),
    ("Acceso vial", "Estado"), ("Punto seguro de servicio", "Estado"), ("Electricidad disponible", "Estado"),
    ("Restricciones operacionales", "Menú desplegable"), ("Condiciones del entorno", "Menú desplegable"),
    ("Restricción operacional principal", "Texto largo"), ("Prioridad preliminar", "Estado"),
    ("Sectores prioritarios", "Menú desplegable"), ("Requiere evaluación técnica", "Menú desplegable"),
    ("Situación crítica", "Estado"),
]

SCORE_COLUMNS = [
    ("Puntos Urgencia", "Números"), ("Nivel Urgencia", "Estado"),
    ("Puntos Factibilidad", "Números"), ("Nivel Factibilidad", "Estado"),
    ("Cuadrante", "Estado"),
]

ALL_COLUMNS = KPI_COLUMNS + SCORE_COLUMNS

CREATE_COLUMN_MUTATION = """
mutation ($board: ID!, $title: String!, $type: ColumnType!) {
  create_column (board_id: $board, title: $title, column_type: $type) {
    id
    title
  }
}
"""


def create_column(title: str, friendly_type: str) -> dict:
    monday_type = TYPE_MAP[friendly_type]
    resp = requests.post(
        MONDAY_API_URL,
        json={
            "query": CREATE_COLUMN_MUTATION,
            "variables": {"board": MONDAY_BOARD_ID, "title": title, "type": monday_type},
        },
        headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    print(f"Creando {len(ALL_COLUMNS)} columnas en el tablero {MONDAY_BOARD_ID}...\n")
    created, failed = [], []
    for title, friendly_type in ALL_COLUMNS:
        result = create_column(title, friendly_type)
        if "errors" in result:
            print(f"  ❌ {title}: {result['errors']}")
            failed.append((title, result["errors"]))
        else:
            col = result["data"]["create_column"]
            print(f"  ✅ {title} -> id: {col['id']} ({friendly_type})")
            created.append(col)
        time.sleep(0.3)

    print(f"\n=== Resumen: {len(created)} columnas creadas, {len(failed)} con error ===")
    if failed:
        print("Revisa estas manualmente:")
        for title, err in failed:
            print(f"  - {title}: {err}")

    with open("columnas_creadas.json", "w", encoding="utf-8") as f:
        json.dump(created, f, ensure_ascii=False, indent=2)
    print("\nMapeo guardado en columnas_creadas.json (revisa el resultado del workflow para copiarlo).")


if __name__ == "__main__":
    main()
