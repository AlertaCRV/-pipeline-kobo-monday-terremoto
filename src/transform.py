"""
Transforma una submission cruda de Kobo en el registro plano que usan
scoring.py y monday_client.py.

NOTA IMPORTANTE para cuando se conecte a Kobo real (hoy solo se prueba con
datos ficticios ya "decodificados"):
  - Kobo devuelve las respuestas con las claves prefijadas por el nombre del
    grupo (ej. "6. Afectación.../n_lesionados" en vez de "n_lesionados").
  - Los campos select_one/select_multiple devuelven el CÓDIGO de la opción
    (ej. "alta"), no la etiqueta visible ("Alta"). Antes de aplicar
    scoring.py hay que traducir código -> etiqueta usando la hoja "choices"
    del formulario (ya la tenemos analizada en este chat).
  Ese diccionario código->etiqueta se añade aquí como CHOICE_LABELS cuando
  se conecte la fuente real; con datos ficticios no hace falta porque el
  fixture ya usa las etiquetas directamente.
"""
import json
from pathlib import Path

_KPI_FIELDS_PATH = Path(__file__).parent / "kpi_fields.json"
KPI_FIELDS = json.loads(_KPI_FIELDS_PATH.read_text(encoding="utf-8"))
KPI_FIELD_NAMES = {f["campo"] for f in KPI_FIELDS}


def flatten_submission(raw: dict) -> dict:
    """
    Punto de extensión: aquí se haría el strip de prefijos de grupo y la
    traducción código -> etiqueta cuando se conecte Kobo real.
    Con el fixture de prueba, la submission ya viene plana y con etiquetas,
    así que esta función es un paso transparente por ahora.
    """
    return dict(raw)


def select_kpi_record(flat: dict) -> dict:
    """Se queda solo con los campos confirmados como KPI (para mostrar en Monday)."""
    return {k: v for k, v in flat.items() if k in KPI_FIELD_NAMES}


def build_item_name(flat: dict) -> str:
    """Nombre del ítem en Monday: usa el nombre de comunidad/campamento si existe."""
    return flat.get("nombre_o_sector") or flat.get("sector_comunidad") or flat.get("nombre_campamento") or f"Submission {flat.get('_id', '?')}"
