"""
Cálculo del score de Urgencia x Factibilidad operativa -- versión 2.

Cambios en esta versión (Factibilidad rediseñada tras reemplazar la
sección 15 del cuestionario por una sola pregunta de selección múltiple,
"condiciones_distribucion", con 13 opciones):

- Factibilidad ya NO combina 5 variables distintas. Se calcula sumando el
  puntaje de cada condición marcada en "condiciones_distribucion"
  (selección múltiple aditiva, igual lógica que antes tenía
  restricciones_operacionales).
- Factibilidad tiene 3 niveles reales (Alta/Media/Baja) -- NO se colapsa
  Media hacia Alta (a diferencia de Urgencia, que sí colapsa).
- Regla de anulación: si "Clima sociocomunitario hostil" o "Sospecha de
  actividad delictiva..." es la ÚNICA condición marcada, Factibilidad es
  "Baja" automáticamente, sin importar el puntaje. Si vienen combinadas
  con otras condiciones, se calcula por puntaje normal (sin anular).
"""
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "scoring_config.json"
_config = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
WEIGHTS = _config["weights"]
THRESHOLDS = _config["thresholds"]
MULTISELECT_BINARIO = _config["multiselect_binario"]
CONDICIONES_ANULAN_BAJA = set(_config["condiciones_distribucion_anulan_baja"])

URGENCIA_SIMPLE_VARS = ["prioridad_preliminar", "riesgo_retorno", "via_denuncia",
                        "estado_establecimiento", "riesgo_duplicacion"]
URGENCIA_BINARIO_VARS = ["riesgos_terremoto", "riesgos_proteccion", "evaluacion_tecnica"]


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
    partes = [p.strip() for p in str(valor_traducido).split(";")]
    tiene_algo_real = any(p not in neutros for p in partes)
    return 1.0 if tiene_algo_real else 0.0


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
    efectiva = THRESHOLDS["colapso_media_urgencia"] if nivel == "Media" else nivel
    return {"puntos_urgencia": puntos, "nivel_urgencia": nivel, "urgencia_efectiva": efectiva}


def compute_factibilidad(record: dict) -> dict:
    valor = record.get("condiciones_distribucion")
    if valor in (None, ""):
        return {"puntos_factibilidad": 0.0, "nivel_factibilidad": "Alta"}

    partes = [p.strip() for p in str(valor).split(";")]

    # Regla de anulación: la única condición marcada es una de las dos severas
    if len(partes) == 1 and partes[0] in CONDICIONES_ANULAN_BAJA:
        return {"puntos_factibilidad": WEIGHTS["condiciones_distribucion"].get(partes[0], 0), "nivel_factibilidad": "Baja"}

    tabla = WEIGHTS["condiciones_distribucion"]
    puntos = sum(tabla.get(p, 0) for p in partes)

    if puntos >= THRESHOLDS["factibilidad_alta"]:
        nivel = "Alta"
    elif puntos >= THRESHOLDS["factibilidad_media"]:
        nivel = "Media"
    else:
        nivel = "Baja"
    return {"puntos_factibilidad": puntos, "nivel_factibilidad": nivel}


# Matriz 2x3: Urgencia efectiva (Alta/Baja, ya colapsada) x Factibilidad (Alta/Media/Baja)
CUADRANTES = {
    ("Alta", "Alta"): "Intervenir ya",
    ("Alta", "Media"): "Intervenir con gestión de riesgo",
    ("Alta", "Baja"): "Resolver acceso primero",
    ("Baja", "Alta"): "Oportunidad",
    ("Baja", "Media"): "Programar con preparación",
    ("Baja", "Baja"): "Monitorear",
}


def compute_score(record: dict) -> dict:
    urg = compute_urgencia(record)
    fac = compute_factibilidad(record)
    cuadrante = CUADRANTES[(urg["urgencia_efectiva"], fac["nivel_factibilidad"])]
    return {**urg, **fac, "cuadrante": cuadrante}
