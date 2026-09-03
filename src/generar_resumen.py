"""
Genera una pagina HTML con un resumen por comunidad/campamento, en formato
de tarjetas, para consulta rapida y amigable de gerencia.

NO incluye datos de contacto (nombre ni telefono del lider/referente) --
esos quedan solo en Monday, nunca en esta pagina publica.

Se guarda en docs/comunidades.html. Se corre despues de cada sincronizacion.
"""
import os
import datetime
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

COLS = {
    "fecha_eval": "date_mm6v1zxa",
    "estado": "color_mm6rjg61",
    "municipio": "color_mm6rcbv4",
    "parroquia": "color_mm6r6yre",
    "ubicacion": "long_text_mm6rwcs",
    "familias_actuales": "numeric_mm6r640v",
    "sectores_prioritarios": "dropdown_mm6rw0wh",
    "evaluacion_tecnica": "dropdown_mm6rme59",
    "condiciones_distribucion": "dropdown_mm6s4s4x",
    "cuadrante": "color_mm6rzjwx",
    "acciones_siguientes": "text_mm6vfd10",
    "tipo_area": "color_mm6r3ja7",
    "mapa_fotos": "text_mm6vbwtv",
}
COL_IDS = list(COLS.values())

QUERY = """
query ($board: ID!, $cols: [String!]) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items { id name column_values (ids: $cols) { id text } }
    }
  }
}
"""

ZONE_INFO = {
    "Intervenir ya": ("#A63A2E", "I"),
    "Intervenir con gestión de riesgo": ("#C9822E", "III"),
    "Resolver acceso primero": ("#8C2F26", "II"),
    "Oportunidad": ("#3F7D6B", "IV"),
    "Programar con preparación": ("#6E8A9E", "V"),
    "Monitorear": ("#8A8D89", "VI"),
}
ORDEN_CUADRANTE = ["Intervenir ya", "Resolver acceso primero", "Intervenir con gestión de riesgo",
                   "Oportunidad", "Programar con preparación", "Monitorear"]

def esc(s):
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

resp = requests.post(
    MONDAY_API_URL,
    json={"query": QUERY, "variables": {"board": MONDAY_BOARD_ID, "cols": COL_IDS}},
    headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
    timeout=30,
)
resp.raise_for_status()
items_raw = resp.json()["data"]["boards"][0]["items_page"]["items"]

items = []
for it in items_raw:
    vals = {cv["id"]: cv["text"] for cv in it["column_values"]}
    items.append({
        "name": it["name"],
        "fecha": vals.get(COLS["fecha_eval"]) or "",
        "estado": vals.get(COLS["estado"]) or "",
        "municipio": vals.get(COLS["municipio"]) or "",
        "parroquia": vals.get(COLS["parroquia"]) or "",
        "ubicacion": vals.get(COLS["ubicacion"]) or "",
        "familias": vals.get(COLS["familias_actuales"]) or "",
        "sectores": vals.get(COLS["sectores_prioritarios"]) or "",
        "eval_tecnica": vals.get(COLS["evaluacion_tecnica"]) or "",
        "condiciones": vals.get(COLS["condiciones_distribucion"]) or "",
        "cuadrante": vals.get(COLS["cuadrante"]) or "Sin cuadrante",
        "acciones": vals.get(COLS["acciones_siguientes"]) or "",
        "tipo_area": vals.get(COLS["tipo_area"]) or "",
        "mapa_fotos": vals.get(COLS["mapa_fotos"]) or "",
    })

def orden_key(it):
    try:
        idx = ORDEN_CUADRANTE.index(it["cuadrante"])
    except ValueError:
        idx = len(ORDEN_CUADRANTE)
    return (idx, it["name"])

items.sort(key=orden_key)

def tag_list(texto):
    if not texto:
        return ""
    partes = [p.strip() for p in texto.split(";")] if ";" in texto else [p.strip() for p in texto.split(",")]
    return "".join(f'<span class="tag">{esc(p)}</span>' for p in partes if p)

cards_html = []
for it in items:
    color, numero = ZONE_INFO.get(it["cuadrante"], ("#999999", "?"))
    familias_txt = f'{int(float(it["familias"]))} familias' if it["familias"] else "Familias: sin dato"
    ubicacion_txt = it["ubicacion"] or "Sin coordenadas"
    breadcrumb = " / ".join(x for x in [it["estado"], it["municipio"], it["parroquia"]] if x)
    acciones_txt = esc(it["acciones"]) or "<span class=\"muted\">Sin acciones registradas</span>"

    if it["mapa_fotos"] and it["mapa_fotos"].startswith("http"):
        enlace_mapa_html = (f'<div class="section-label">Mapa y fotos</div>'
                             f'<a class="mapa-link" href="{esc(it["mapa_fotos"])}" target="_blank" rel="noopener">📍 Ver mapa y fotos</a>')
    elif it["mapa_fotos"]:
        enlace_mapa_html = (f'<div class="section-label">Mapa y fotos</div>'
                             f'<div class="acciones">{esc(it["mapa_fotos"])}</div>')
    else:
        enlace_mapa_html = ""

    card = f'''
    <div class="card" data-fecha="{esc(it["fecha"])}">
      <div class="card-top" style="background:{color}">
        <span class="num">{numero}</span>
        <span class="cuadrante-nombre">{esc(it["cuadrante"])}</span>
      </div>
      <div class="card-body">
        <h3>{esc(it["name"])}</h3>
        <div class="meta-row">
          <span class="pill-tipo">{esc(it["tipo_area"])}</span>
          <span class="fecha">{esc(it["fecha"]) or "Sin fecha"}</span>
        </div>
        <div class="breadcrumb">{esc(breadcrumb) or "Sin ubicación administrativa"}</div>
        <div class="coord">📍 {esc(ubicacion_txt)}</div>
        <div class="familias">👪 {familias_txt}</div>
        <div class="section-label">Sectores prioritarios</div>
        <div class="tags">{tag_list(it["sectores"]) or '<span class="muted">Ninguno</span>'}</div>
        <div class="section-label">¿Requiere evaluación técnica?</div>
        <div class="tags">{tag_list(it["eval_tecnica"]) or '<span class="muted">No</span>'}</div>
        <div class="section-label">Condiciones que dificultan distribución</div>
        <div class="tags">{tag_list(it["condiciones"]) or '<span class="muted">Ninguna</span>'}</div>
        {enlace_mapa_html}
        <div class="section-label">Acciones recomendadas</div>
        <div class="acciones">{acciones_txt}</div>
      </div>
    </div>
    '''
    cards_html.append(card)

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

html_parts = []
html_parts.append("<!DOCTYPE html>")
html_parts.append('<html lang="es">')
html_parts.append("<head>")
html_parts.append('<meta charset="UTF-8">')
html_parts.append("<title>Resumen por comunidad — CRV Terremoto 2026</title>")
html_parts.append("<style>")
html_parts.append('body { font-family:"Open Sans",-apple-system,Segoe UI,Roboto,sans-serif; background:#F5F7FA; color:#20303F; margin:0; }')
html_parts.append(".topbar { background:#1C4269; color:#fff; padding:14px 28px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }")
html_parts.append(".topbar h1 { margin:0; font-size:17px; font-weight:700; }")
html_parts.append(".topbar .sub { font-size:11px; color:#AFC1D6; margin-top:2px; }")
html_parts.append(".topbar a { color:#fff; font-size:12px; text-decoration:none; border:1px solid rgba(255,255,255,.4); padding:6px 12px; border-radius:16px; }")
html_parts.append(".topbar a:hover { background:rgba(255,255,255,.12); }")
html_parts.append(".wrap { padding:18px 28px 40px; max-width:1400px; margin:0 auto; }")
html_parts.append(".updated { font-size:11px; color:#8A93A0; margin-bottom:16px; }")
html_parts.append(".grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:18px; }")
html_parts.append(".card { background:#fff; border-radius:10px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.08); border:1px solid #E1E6EC; }")
html_parts.append(".card-top { padding:8px 14px; display:flex; align-items:center; gap:8px; color:#fff; }")
html_parts.append(".card-top .num { font-family:Georgia,serif; font-weight:700; font-size:15px; background:rgba(255,255,255,.25); width:22px; height:22px; border-radius:5px; display:flex; align-items:center; justify-content:center; }")
html_parts.append(".card-top .cuadrante-nombre { font-size:12.5px; font-weight:700; }")
html_parts.append(".card-body { padding:14px 16px 16px; }")
html_parts.append(".card-body h3 { margin:0 0 6px; font-size:15px; color:#20303F; }")
html_parts.append(".meta-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }")
html_parts.append(".pill-tipo { font-size:10.5px; font-weight:700; text-transform:uppercase; background:#E7F0FA; color:#2C6FB0; padding:2px 8px; border-radius:10px; }")
html_parts.append(".fecha { font-size:11px; color:#8A93A0; }")
html_parts.append(".breadcrumb { font-size:11.5px; color:#5B6672; margin-bottom:4px; }")
html_parts.append(".coord, .familias { font-size:12px; color:#3A4048; margin-bottom:3px; }")
html_parts.append(".section-label { font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.3px; color:#8A93A0; margin-top:10px; margin-bottom:4px; }")
html_parts.append(".tags { display:flex; flex-wrap:wrap; gap:5px; }")
html_parts.append(".tag { font-size:11px; background:#F0F2F5; color:#3A4048; padding:2px 8px; border-radius:10px; }")
html_parts.append(".muted { font-size:11.5px; color:#B0B7BF; font-style:italic; }")
html_parts.append(".acciones { font-size:12px; color:#3A4048; line-height:1.4; background:#FAFBFC; border-left:3px solid #C7CDD3; padding:6px 10px; border-radius:0 6px 6px 0; }")
html_parts.append(".filtro-bar { display:flex; align-items:center; gap:16px; flex-wrap:wrap; background:#fff; border:1px solid #E1E6EC; border-radius:8px; padding:10px 16px; margin-bottom:16px; }")
html_parts.append(".filtro-bar label { font-size:12px; color:#5B6672; display:flex; align-items:center; gap:6px; }")
html_parts.append(".filtro-bar input[type=date] { border:1px solid #D6DBE1; border-radius:5px; padding:4px 6px; font-size:12px; font-family:inherit; }")
html_parts.append(".filtro-bar button { background:#EDEFF2; border:none; border-radius:14px; padding:5px 12px; font-size:12px; cursor:pointer; color:#3A4048; }")
html_parts.append(".filtro-bar button:hover { background:#E1E4E8; }")
html_parts.append(".contador-filtro { font-size:11.5px; color:#8A93A0; margin-left:auto; }")
html_parts.append(".sin-resultados { text-align:center; color:#8A93A0; font-size:13px; padding:40px 0; }")
html_parts.append(".mapa-link { display:inline-block; font-size:12px; color:#2C6FB0; text-decoration:none; font-weight:600; }")
html_parts.append(".mapa-link:hover { text-decoration:underline; }")
html_parts.append("</style>")
html_parts.append("</head>")
html_parts.append("<body>")
html_parts.append('<div class="topbar"><div><h1>Resumen por comunidad</h1>'
                   '<div class="sub">Cruz Roja Venezolana \u00b7 Diagn\u00f3stico terreno, Terremoto 2026</div></div>'
                   '<a href="index.html">Ver matriz de cuadrantes \u2192</a></div>')
html_parts.append('<div class="wrap">')
html_parts.append(f'<div class="updated">\u00daltima actualizaci\u00f3n: {now} \u00b7 {len(items)} evaluaciones \u00b7 Ordenadas por prioridad</div>')
html_parts.append(
    '<div class="filtro-bar">'
    '<label>Desde <input type="date" id="fecha-desde" onchange="filtrarPorFecha()"></label>'
    '<label>Hasta <input type="date" id="fecha-hasta" onchange="filtrarPorFecha()"></label>'
    '<button onclick="limpiarFiltro()">Limpiar filtro</button>'
    '<span id="contador-filtro" class="contador-filtro"></span>'
    '</div>'
)
html_parts.append('<div class="grid" id="grid-comunidades">' + "".join(cards_html) + '</div>')
html_parts.append('<div id="sin-resultados" class="sin-resultados" style="display:none;">No hay comunidades evaluadas en ese periodo.</div>')
html_parts.append('</div>')
html_parts.append("""
<script>
function filtrarPorFecha() {
  const desde = document.getElementById('fecha-desde').value;
  const hasta = document.getElementById('fecha-hasta').value;
  const tarjetas = document.querySelectorAll('#grid-comunidades .card');
  let visibles = 0;
  tarjetas.forEach(function(card) {
    const fecha = card.getAttribute('data-fecha');
    let mostrar = true;
    if (desde && (!fecha || fecha < desde)) mostrar = false;
    if (hasta && (!fecha || fecha > hasta)) mostrar = false;
    card.style.display = mostrar ? '' : 'none';
    if (mostrar) visibles++;
  });
  document.getElementById('contador-filtro').textContent = visibles + ' de ' + tarjetas.length + ' comunidades visibles';
  document.getElementById('sin-resultados').style.display = (visibles === 0) ? 'block' : 'none';
}
function limpiarFiltro() {
  document.getElementById('fecha-desde').value = '';
  document.getElementById('fecha-hasta').value = '';
  filtrarPorFecha();
}
document.addEventListener('DOMContentLoaded', filtrarPorFecha);
</script>
""")
html_parts.append("</body></html>")

html = "\n".join(html_parts)

docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(docs_dir, exist_ok=True)
with open(os.path.join(docs_dir, "comunidades.html"), "w", encoding="utf-8") as f:
    f.write(html)

print(f"Página de resumen generada con {len(items)} evaluaciones -> docs/comunidades.html")
