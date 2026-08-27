"""
Orquestador del pipeline diario Kobo -> Monday.

Uso:
    DRY_RUN=true python sync.py          # modo de prueba, datos ficticios (default)
    DRY_RUN=false python sync.py         # modo real (requiere las variables de entorno
                                          # KOBO_API_TOKEN, KOBO_ASSET_UID, MONDAY_API_TOKEN,
                                          # MONDAY_BOARD_ID y MONDAY_COLUMN_MAP completos)
"""
from config import DRY_RUN
from kobo_client import get_new_submissions
from transform import flatten_submission, select_kpi_record, build_item_name
from scoring import compute_score
from monday_client import build_column_values, upsert_item


def run(since_id: int = 0):
    print(f"=== Sincronización Kobo -> Monday | DRY_RUN={DRY_RUN} ===\n")
    submissions = get_new_submissions(since_id=since_id)
    print(f"Submissions nuevas encontradas: {len(submissions)}\n")

    results = []
    for raw in submissions:
        flat = flatten_submission(raw)
        score = compute_score(flat)
        kpi_record = select_kpi_record(flat)
        item_name = build_item_name(flat)
        column_values = build_column_values(kpi_record, score)

        result = upsert_item(item_name, column_values)
        results.append({"item_name": item_name, "cuadrante": score["cuadrante"], "result": result})

        print(f"  -> {item_name}: {score['nivel_urgencia']} urgencia / "
              f"{score['nivel_factibilidad']} factibilidad => {score['cuadrante']}")

    print(f"\n=== Fin. {len(results)} ítems procesados. ===")
    return results


if __name__ == "__main__":
    run()
