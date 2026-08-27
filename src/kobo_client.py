"""
Cliente mínimo para leer submissions de KoboToolbox vía su API REST.

En DRY_RUN=true no se hace ninguna llamada de red: se leen las submissions
ficticias de tests/fixtures/sample_submissions.json.
"""
import json
from pathlib import Path
import requests
from config import DRY_RUN, KOBO_API_TOKEN, KOBO_ASSET_UID, KOBO_BASE_URL

FIXTURE_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_submissions.json"


def get_new_submissions(since_id: int = 0) -> list:
    if DRY_RUN:
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        return [r for r in data if r["_id"] > since_id]

    url = f"{KOBO_BASE_URL}/api/v2/assets/{KOBO_ASSET_UID}/data.json"
    headers = {"Authorization": f"Token {KOBO_API_TOKEN}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return [r for r in results if r.get("_id", 0) > since_id]
