"""
Transforma una submission cruda de Kobo en el registro plano que usan
scoring.py y monday_client.py.

Incluye la traducción automática de códigos de Kobo (ej. "alta") a las
etiquetas legibles que usa scoring.py (ej. "Alta"), usando los diccionarios
choice_labels.json (campos cortos) y choice_labels_geo.json (Estado/Municipio/
Parroquia).

NOTA: el separador entre etiquetas de selección múltiple es ";" (no ","),
porque varias etiquetas del cuestionario (ej. "Vialidad en mal estado...
(huecos, baches, fallas de borde)") contienen comas dentro de su propio
texto, y usar coma como separador rompía el cálculo del score.
"""
import json
from pathlib import Path

_HERE = Path(__file__).parent

KPI_FIELDS = json.loads((_HERE / "kpi_fields.json").read_text(encoding="utf-8"))
KPI_FIELD_NAMES = {f["campo"] for f in KPI_FIELDS}

CHOICE_LABELS = {}
CHOICE_LABELS.update(json.loads((_HERE / "choice_labels.json").read_text(encoding="utf-8")))
CHOICE_LABELS.update(json.loads((_HERE / "choice_labels_geo.json").read_text(encoding="utf-8")))


def translate_value(campo: str, raw_value):
    if campo not in CHOICE_LABELS or raw_value in (None, ""):
        return raw_value
    tabla = CHOICE_LABELS[campo]
    codigos = str(raw_value).split()
    etiquetas = [tabla.get(c, c) for c in codigos]
    return "; ".join(etiquetas)


def flatten_submission(raw: dict) -> dict:
    flat = {}
    for key, value in raw.items():
        campo = key.split("/")[-1]
        flat[campo] = translate_value(campo, value)
    return flat


def select_kpi_record(flat: dict) -> dict:
    return {k: v for k, v in flat.items() if k in KPI_FIELD_NAMES}


def build_item_name(flat: dict) -> str:
    return (
        flat.get("nombre_o_sector")
        or flat.get("sector_comunidad")
        or flat.get("nombre_campamento")
        or f"Submission {flat.get('_id', '?')}"
    )
