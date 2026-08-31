"""
Cálculo del score de Urgencia x Factibilidad operativa.

Corrección importante (tras probar con datos tipo Kobo real): varios campos
no son "Sí/No" simples como se asumió en la calibración inicial -- son de
selección múltiple con categorías específicas. Este archivo maneja tres
formas distintas de puntuar:

1. Campos de una sola opción con tabla de puntos directa (WEIGHTS).
2. Campos de selección múltiple "binarios": si la única opción marcada es la
   neutra (ej. "Ninguna", "No se sabe"), suman 0; si hay cualquier opción
   real marcada, suman 1 (riesgos_terremoto, riesgos_proteccion,
   evaluacion_tecnica).
3. `restricciones_operacionales`: selección múltiple ADITIVA -- cada
   restricción marcada resta sus propios puntos (no hay anulación).
"""
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "scoring_config.json"
_config = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
WEIGHTS = _config["weights"]
THRESHOLDS = _config["thresholds"]
CONDICIONES_ENTORNO_NINGUNA = _config["condiciones_entorno_ninguna_label"]
MULTISELECT_BINARIO = _config["multiselect_binario"]

URGENCIA_SIMPLE_VARS = ["prioridad_preliminar", "riesgo_retorno", "via_denuncia",
                        "estado_establecimiento", "riesgo_duplicacion"]
URGENCIA_BINARIO_VARS = ["riesgos_terremoto", "riesgos_proteccion", "evaluacion_tecnica"]

FACTIBILIDAD_SIMPLE_VARS = ["acceso_vial", "punto_servicio", "electricidad"]


def _points_simple(variable: str, category) -> float:
    if category in (None, ""):
        return 0.0
    table = WEIGHTS.get(variable, {})
    val = table.get(category, 0)
    return 0.0 if val == "N/A" else float(val)


def _points_binario(variable: str, valor_traducido) -> float:
    if valor_traducido in (None, ""):
        return 0.0
    neutros = set(MULTISELECT_BINARIO.get(variable, {}).get("neutros", []))
    partes = [p.strip() for p in str(valor_traducido).split(",")]
    tiene_algo_real = any(p not in neutros for p in partes)
    return 1.0 if tiene_algo_real else 0.0


def _points_restricciones(valor_traducido) -> float:
    if valor_traducido in (None, ""):
        return 0.0
    tabla = WEIGHTS["restricciones_operacionales"]
    partes = [p.strip() for p in str(valor_traducido).split(",")]
    return sum(tabla.get(p, 0) for p in partes)


def _points_condiciones_entorno(valor_traducido) -> float:
    if valor_traducido in (None, ""):
        return 0.0
    return 1.0 if valor_traducido.strip() == CONDICIONES_ENTORNO_NINGUNA else 0.0


def compute_urgencia(record: dict) -> dict:
    puntos = sum(_points_simple(v, record.get(v)) for v in URGENCIA_SIMPLE_VARS)
    puntos += sum(_points_binario(v, record.get(v)) for v in URGENCIA_BINARIO_VARS)

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
    puntos = sum(_points_simple(v, record.get(v)) for v in FACTIBILIDAD_SIMPLE_VARS)
    puntos += _points_condiciones_entorno(record.get("condiciones_entorno"))
    puntos += _points_restricciones(record.get("restricciones_operacionales"))

    nivel = "Alta" if puntos >= THRESHOLDS["factibilidad_alta"] else "Baja"
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
