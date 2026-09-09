"""Script temporal de introspeccion: lista mutaciones de la API de Monday
relacionadas con "column", para confirmar el nombre correcto antes de usarlo."""
import os
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_API_URL = "https://api.monday.com/v2"

QUERY = """
query {
  __type(name: "Mutation") {
    fields {
      name
      args { name type { name kind ofType { name } } }
    }
  }
}
"""

resp = requests.post(MONDAY_API_URL, json={"query": QUERY},
                      headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"}, timeout=30)
resp.raise_for_status()
data = resp.json()
fields = data["data"]["__type"]["fields"]
for f in fields:
    if "column" in f["name"].lower():
        args = ", ".join(a["name"] for a in f["args"])
        print(f"{f['name']}({args})")
