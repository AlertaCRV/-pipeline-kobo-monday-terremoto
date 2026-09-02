"""
Orquestador del pipeline diario Kobo -> Monday.

Incluye control de duplicados: recuerda el _id más alto ya sincronizado
en el archivo "ultimo_id_sincronizado.txt" (en la raíz del repositorio),
y solo procesa submissions con _id mayor a ese valor. El workflow de
GitHub Actions se encarga de guardar ese archivo de vuelta en el
repositorio al final de cada corrida.

Uso:
    DRY_RUN=true python sync.py          # modo de prueba, datos ficticios (default)
    DRY_RUN=false python sync.py         # modo real
"""
from pathlib import Path
from config import DRY_RUN
from kobo_client import get_new_submissions
from transform import flatten_submission, select_kpi_record, build_item_name
from scoring import compute_score
from monday_client import build_column_values, upsert_item

STATE_FILE = Path(__file__).parent.parent / "ultimo_id_sincronizado.txt"


def leer_ultimo_id() -> int:
    if not STATE_FILE.exists():
        return 0
    contenido = STATE_FILE.read_text(encoding="utf-8").strip()
    return int(contenido) if contenido else 0


def guardar_ultimo_id(nuevo_id: int) -> None:
    STATE_FILE.write_text(str(nuevo_id), encoding="utf-8")


def run(since_id: int = None):
    if since_id is None:
        since_id = leer_ultimo_id()

    print(f"=== Sincronización Kobo -> Monday | DRY_RUN={DRY_RUN} ===")
    print(f"Último ID sincronizado previamente: {since_id}\n")

    submissions = get_new_submissions(since_id=since_id)
    print(f"Submissions nuevas encontradas: {len(submissions)}\n")

    results = []
    max_id_procesado = since_id
    for raw in submissions:
        flat = flatten_submission(raw)
        score = compute_score(flat)
        kpi_record = select_kpi_record(flat)
        item_name = build_item_name(flat)
        column_values = build_column_values(kpi_record, score)

        result = upsert_item(item_name, column_values, cuadrante=score["cuadrante"])
        results.append({"item_name": item_name, "cuadrante": score["cuadrante"], "result": result})

        print(f"  -> {item_name}: {score['nivel_urgencia']} urgencia / "
              f"{score['nivel_factibilidad']} factibilidad => {score['cuadrante']}")

        sub_id = raw.get("_id", 0)
        if sub_id > max_id_procesado:
            max_id_procesado = sub_id

    if max_id_procesado > since_id:
        guardar_ultimo_id(max_id_procesado)
        print(f"\nÚltimo ID actualizado a: {max_id_procesado}")
    else:
        print("\nNo hubo submissions nuevas; el archivo de control no cambia.")

    print(f"=== Fin. {len(results)} ítems procesados. ===")
    return results


if __name__ == "__main__":
    run()
