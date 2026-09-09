"""
Orquestador del pipeline diario Kobo -> Monday.

Hace un upsert real: en cada corrida procesa TODAS las submissions de
Kobo (no solo las nuevas), y por cada una:
  - Si ya existe un item en Monday con ese _id de Kobo (columna ID Kobo),
    lo ACTUALIZA con los valores actuales de Kobo -- asi, si alguien edita
    una respuesta ya aplicada en Kobo, el cambio llega a Monday sin tener
    que borrar nada.
  - Si no existe, crea el item nuevo (y le sube las fotos, si trae).

Las columnas que el equipo llena a mano en Monday (Progreso, Mapa) NUNCA
se sobreescriben en una actualizacion -- ver MONDAY_ONLY_COLUMN_IDS y
PROGRESO_COLUMN_ID en config.py, y monday_client.update_item().

Uso:
    DRY_RUN=true python sync.py          # modo de prueba, datos ficticios (default)
    DRY_RUN=false python sync.py         # modo real
"""
from config import DRY_RUN
from kobo_client import get_new_submissions
from transform import flatten_submission, select_kpi_record, build_item_name, extract_attachments
from scoring import compute_score
from monday_client import (
    build_column_values, upsert_item, update_item, get_created_item_id,
    upload_photos_to_item, fetch_kobo_id_map,
)


def run():
    print(f"=== Sincronización Kobo -> Monday | DRY_RUN={DRY_RUN} ===")

    kobo_id_map = fetch_kobo_id_map()
    print(f"Items existentes en Monday (con ID Kobo reconocido): {len(kobo_id_map)}\n")

    submissions = get_new_submissions(since_id=0)
    print(f"Submissions encontradas en Kobo: {len(submissions)}\n")

    results = []
    creados, actualizados = 0, 0
    for raw in submissions:
        kobo_id = str(raw.get("_id", ""))
        flat = flatten_submission(raw)
        score = compute_score(flat)
        kpi_record = select_kpi_record(flat)
        item_name = build_item_name(flat)
        column_values = build_column_values(kpi_record, score)

        if kobo_id in kobo_id_map:
            item_id = kobo_id_map[kobo_id]
            result = update_item(item_id, item_name, column_values)
            if isinstance(result, dict) and result.get("errors"):
                print(f"  ❌ ERROR actualizando '{item_name}' ({item_id}): {result['errors']}")
            else:
                actualizados += 1
                print(f"  ~ actualizado: {item_name} ({score['nivel_urgencia']} urgencia / "
                      f"{score['nivel_factibilidad']} factibilidad => {score['cuadrante']})")
        else:
            result = upsert_item(item_name, column_values, kobo_id)
            if isinstance(result, dict) and result.get("errors"):
                print(f"  ❌ ERROR creando '{item_name}': {result['errors']}")
            else:
                creados += 1
                print(f"  + creado: {item_name} ({score['nivel_urgencia']} urgencia / "
                      f"{score['nivel_factibilidad']} factibilidad => {score['cuadrante']})")

                item_id = get_created_item_id(result)
                attachments = extract_attachments(raw)
                if attachments:
                    upload_photos_to_item(item_id, attachments)

        results.append({"item_name": item_name, "cuadrante": score["cuadrante"], "result": result})

    print(f"\n=== Fin. {creados} creados, {actualizados} actualizados. ===")
    return results


if __name__ == "__main__":
    run()
