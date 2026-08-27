"""
Cálculo del score de Urgencia x Factibilidad operativa.

Replica EXACTAMENTE la lógica validada en Matriz_Urgencia_Factibilidad_v2_definitivo.xlsx
(hojas 'Pesos_Umbrales' y 'Comunidades'). Los valores de pesos y umbrales se cargan
desde scoring_config.json, que fue extraído directamente de ese Excel -- no están
tecleados a mano aquí, para evitar que el código y el Excel de referencia diverjan.

Reglas híbridas (confirmadas con Fernando):
  - situacion_critica = "Sí"              -> Urgencia = "Alta" (anula el puntaje)
  - restricciones_operacionales = severa  -> Factibilidad = "Baja" (anula el puntaje)
  - Urgencia "Media" se colapsa a "Alta" para efectos de la matriz (postura conservadora)
  - riesgo_duplicacion actúa como REDUCTOR del puntaje de Urgencia, no como agravante
"""
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "scoring_config.json"
_config = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
WEIGHTS = _config["weights"]
THRESHOLDS = _config["thresholds"]

URGENCIA_VARS = [
    "prioridad_preliminar", "evaluacion_tecnica", "riesgos_terremoto",
    "riesgo_retorno", "riesgos_proteccion", "via_denuncia",
    "estado_establecimiento", "riesgo_duplicacion",
]
FACTIBILIDAD_VARS = ["acceso_vial", "punto_servicio", "electricidad", "condiciones_entorno"]


def _points(variable: str, category: str) -> float:
    if category is None or category == "":
        return 0.0
    table = WEIGHTS.get(variable, {})
    val = table.get(category, 0)
    return 0.0 if val == "N/A" else float(val)


def compute_urgencia(record: dict) -> dict:
    puntos = sum(_points(v, record.get(v)) for v in URGENCIA_VARS)
    if record.get("situacion_critica") == "Sí":
        nivel = "Alta"
    elif puntos >= THRESHOLDS["urgencia_alta"]:
        nivel = "Alta"
    elif puntos >= THRESHOLDS["urgencia_media"]:
        nivel = "Media"
    else:
        nivel = "Baja"
    efectiva = THRESHOLDS["colapso_media"] if nivel == "Media" else nivel
    return {"puntos_urgencia": puntos, "nivel_urgencia": nivel, "urgencia_efectiva": efectiva}


def compute_factibilidad(record: dict) -> dict:
    puntos = sum(_points(v, record.get(v)) for v in FACTIBILIDAD_VARS)
    if record.get("restricciones_operacionales") == "Severa (anula → Baja)":
        nivel = "Baja"
    elif puntos >= THRESHOLDS["factibilidad_alta"]:
        nivel = "Alta"
    else:
        nivel = "Baja"
    return {"puntos_factibilidad": puntos, "nivel_factibilidad": nivel}


CUADRANTES = {
    ("Alta", "Alta"): "Intervenir ya",
    ("Alta", "Baja"): "Resolver acceso primero",
    ("Baja", "Alta"): "Oportunidad",
    ("Baja", "Baja"): "Monitorear",
}


def compute_score(record: dict) -> dict:
    urg = compute_urgencia(record)
    fac = compute_factibilidad(record)
    cuadrante = CUADRANTES[(urg["urgencia_efectiva"], fac["nivel_factibilidad"])]
    return {**urg, **fac, "cuadrante": cuadrante}
