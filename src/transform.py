"""
Transforma una submission cruda de Kobo en el registro plano que usan
scoring.py y monday_client.py.

NOTA para cuando se conecte a Kobo real: los campos select_one/select_multiple
devuelven el CÓDIGO de la opción, no la etiqueta. Antes de aplicar scoring.py
hay que traducir código -> etiqueta usando la hoja "choices" del formulario.
Con datos ficticios no hace falta porque el fixture ya usa las etiquetas.
"""
import json
from pathlib import Path

_KPI_FIELDS_PATH = Path(__file__).parent / "kpi_fields.json"
KPI_FIELDS = json.loads(_KPI_FIELDS_PATH.read_text(encoding="utf-8"))
KPI_FIELD_NAMES = {f["campo"] for f in KPI_FIELDS}


def flatten_submission(raw: dict) -> dict:
    return dict(raw)


def select_kpi_record(flat: dict) -> dict:
    return {k: v for k, v in flat.items() if k in KPI_FIELD_NAMES}


def build_item_name(flat: dict) -> str:
    return flat.get("nombre_o_sector") or flat.get("sector_comunidad") or flat.get("nombre_campamento") or f"Submission {flat.get('_id', '?')}"
