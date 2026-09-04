"""
Prueba de escritura real en Monday, usando las 5 comunidades ficticias
(sin conectar a Kobo todavía -- eso se hace en un paso aparte).

Reutiliza el mismo código de monday_client.py que usa el pipeline real
(sync.py) -- así prueba de verdad la lógica de agrupación por Progreso y
no una copia desactualizada. Como monday_client.upsert_item respeta
DRY_RUN (definido en config.py), el workflow que corre este script debe
fijar DRY_RUN=false para que escriba de verdad en Monday; si se corre sin
esa variable (o en local, donde DRY_RUN es "true" por defecto), solo
imprime el payload sin llamar a la API.
"""
import json
from pathlib import Path
from scoring import compute_score
from transform import select_kpi_record, build_item_name
from monday_client import build_column_values, upsert_item

FIXTURE_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_submissions.json"


def main():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    print(f"Escribiendo {len(data)} comunidades ficticias en el tablero real...\n")
    for raw in data:
        score = compute_score(raw)
        kpi_record = select_kpi_record(raw)
        item_name = build_item_name(raw)
        column_values = build_column_values(kpi_record, score)
        result = upsert_item(item_name, column_values)
        if "errors" in result:
            print(f"  ❌ {item_name}: {result['errors']}")
        else:
            print(f"  ✅ {item_name} -> {score['cuadrante']}")


if __name__ == "__main__":
    main()
