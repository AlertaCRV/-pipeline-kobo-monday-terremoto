"""
Genera una pagina HTML de resumen general (KPIs, distribuciones y
menciones mas frecuentes), agregando los principales campos de todos
los casos actuales en Monday.

Se guarda en docs/estadisticas.html. Se corre despues de cada
sincronizacion, igual que generar_grafico.py y generar_resumen.py.
"""
import os
import datetime
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

# --- Campos a sumar (numericos) ---------------------------------------
KPI_COLS = {
    "familias_actuales": ("Familias (total)", "numeric_mm6r640v"),
    "personas_actuales": ("Personas (total)", "numeric_mm6rst2h"),
    "familias_afectadas": ("Familias afectadas", "numeric_mm6rrfkn"),
    "familias_no_permanecen": ("Familias que no permanecen", "numeric_mm6r9t48"),
    "danadas_vivienda_n": ("Viviendas dañadas (n.º)", "numeric_mm6rqpsg"),
    "danadas_multifamiliar_n": ("Apartamentos dañados (n.º)", "numeric_mm6rdxse"),
    "familias_alojamiento": ("Familias que requieren alojamiento", "numeric_mm6rsrj2"),
}

# --- Campos a distribuir por categoria (selección única) ---------------
CATEGORIA_COLS = {
    "progreso": ("Progreso", "color_mm6vybqh", ["Evaluada", "Contactada", "Intervenida"]),
    "tipo_area": ("Tipo de área", "color_mm6r3ja7", None),
    "cuadrante": ("Cuadrante de prioridad", "color_mm6rzjwx", None),
    "evaluacion_seguridad": ("Evaluación de seguridad", "color_mm6vwnfn", ["Sí", "No"]),
}

# --- Campos de selección múltiple: contar menciones de cada etiqueta ---
MULTI_COLS = {
    "servicios_afectados": ("Servicios afectados", "dropdown_mm6r9z18"),
    "sectores_prioritarios": ("Sectores prioritarios", "dropdown_mm6rw0wh"),
    "brechas_necesidades": ("Brechas sin atender", "dropdown_mm6rztw"),
}

# Etiquetas y colores de las 6 zonas de la Matriz de Urgencia × Factibilidad
# (ver ZONE_INFO en generar_grafico.py -- mismos valores, para que el
# "Cuadrante de prioridad" se lea igual en ambas páginas del sitio).
CUADRANTE_ZONA = {
    "Intervenir ya": ("I", "#A63A2E",
        "Casos con necesidades urgentes de atención, ubicados en zonas de fácil acceso."),
    "Intervenir con gestión de riesgo": ("II", "#8C2F26",
        "Casos con necesidades urgentes de atención, pero con acceso actualmente bloqueado."),
    "Resolver acceso primero": ("III", "#C9822E",
        "Casos con necesidades urgentes de atención, con dificultades moderadas de acceso."),
    "Oportunidad": ("IV", "#3F7D6B",
        "Casos sin necesidades urgentes, ubicados en zonas de fácil acceso."),
    "Programar con preparación": ("V", "#6E8A9E",
        "Casos sin necesidades urgentes, con dificultades moderadas de acceso."),
    "Monitorear": ("VI", "#8A8D89",
        "Casos sin necesidades urgentes y con acceso limitado por el momento."),
}
CUADRANTE_ORDEN = ["Intervenir ya", "Intervenir con gestión de riesgo", "Resolver acceso primero",
                   "Oportunidad", "Programar con preparación", "Monitorear"]

# Colores de estado reutilizados de las otras páginas (mismo significado
# en todo el sitio: Progreso, y semáforo Sí/No según si implica alerta).
PROGRESO_COLOR = {"Evaluada": "#8C2F26", "Contactada": "#C9822E", "Intervenida": "#3F7D6B"}
SI_NO_COLOR = {
    "evaluacion_seguridad": {"Sí": "#3F7D6B", "No": "#C9822E"},
}
BARRA_COLOR_DEFAULT = "#2C6FB0"
BARRA_COLOR_MENCIONES = "#1C4269"

ALL_COL_IDS = (
    [c[1] for c in KPI_COLS.values()]
    + [c[1] for c in CATEGORIA_COLS.values()]
    + [c[1] for c in MULTI_COLS.values()]
)

QUERY = """
query ($board: ID!, $cols: [String!]) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items { id column_values (ids: $cols) { id text } }
    }
  }
}
"""


def esc(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


resp = requests.post(
    MONDAY_API_URL,
    json={"query": QUERY, "variables": {"board": MONDAY_BOARD_ID, "cols": ALL_COL_IDS}},
    headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
    timeout=30,
)
resp.raise_for_status()
items_raw = resp.json()["data"]["boards"][0]["items_page"]["items"]

filas = [{cv["id"]: cv["text"] for cv in it["column_values"]} for it in items_raw]
total_casos = len(filas)

# --- KPIs (sumas) -------------------------------------------------------
kpi_valores = {}
for campo, (etiqueta, col_id) in KPI_COLS.items():
    total = 0.0
    for fila in filas:
        try:
            total += float(fila.get(col_id) or 0)
        except ValueError:
            continue
    kpi_valores[campo] = (etiqueta, total)


def fmt_num(v):
    return f"{int(v):,}".replace(",", ".") if float(v).is_integer() else f"{v:,.1f}".replace(",", ".")


# --- Distribuciones por categoría ---------------------------------------
def contar_categoria(col_id):
    conteo = {}
    for fila in filas:
        valor = (fila.get(col_id) or "").strip()
        if not valor:
            valor = "Sin dato"
        conteo[valor] = conteo.get(valor, 0) + 1
    return conteo


def orden_categoria(conteo, orden_fijo):
    if orden_fijo:
        claves = [c for c in orden_fijo if c in conteo] + [c for c in conteo if c not in orden_fijo]
    else:
        claves = sorted(conteo, key=lambda k: -conteo[k])
    return claves


def color_categoria(campo, valor):
    if campo == "progreso":
        return PROGRESO_COLOR.get(valor, "#8A8D89")
    if campo == "cuadrante":
        return CUADRANTE_ZONA.get(valor, (None, "#8A8D89", None))[1]
    if campo in SI_NO_COLOR:
        return SI_NO_COLOR[campo].get(valor, "#8A8D89")
    return BARRA_COLOR_DEFAULT


def bloque_cuadrante(etiqueta, col_id):
    conteo = contar_categoria(col_id)
    claves = orden_categoria(conteo, CUADRANTE_ORDEN)
    max_val = max(conteo.values(), default=1)
    filas_html = []
    for clave in claves:
        n = conteo[clave]
        pct = (n / max_val * 100) if max_val else 0
        numero, color, desc = CUADRANTE_ZONA.get(clave, ("?", "#8A8D89", clave))
        filas_html.append(f'''
        <div class="cuadrante-fila">
          <div class="cuadrante-cabeza">
            <span class="num-badge" style="background:{color}">{esc(numero)}</span>
            <div class="cuadrante-desc">{esc(desc)}</div>
            <div class="barra-valor">{n}</div>
          </div>
          <div class="barra-pista"><div class="barra-relleno" style="width:{pct:.1f}%; background:{color}"></div></div>
        </div>''')
    return f'<div class="bloque"><h3>{esc(etiqueta)}</h3>{"".join(filas_html)}</div>'


def bloque_categoria(campo, etiqueta, col_id, orden_fijo):
    if campo == "cuadrante":
        return bloque_cuadrante(etiqueta, col_id)
    conteo = contar_categoria(col_id)
    claves = orden_categoria(conteo, orden_fijo)
    max_val = max(conteo.values(), default=1)
    filas_html = []
    for clave in claves:
        n = conteo[clave]
        pct = (n / max_val * 100) if max_val else 0
        color = color_categoria(campo, clave)
        filas_html.append(f'''
        <div class="barra-fila">
          <div class="barra-label">{esc(clave)}</div>
          <div class="barra-pista"><div class="barra-relleno" style="width:{pct:.1f}%; background:{color}"></div></div>
          <div class="barra-valor">{n}</div>
        </div>''')
    return f'<div class="bloque"><h3>{esc(etiqueta)}</h3>{"".join(filas_html)}</div>'


# --- Menciones más frecuentes (selección múltiple) ----------------------
def contar_menciones(col_id):
    conteo = {}
    for fila in filas:
        texto = (fila.get(col_id) or "").strip()
        if not texto:
            continue
        partes = [p.strip() for p in texto.split(";")] if ";" in texto else [p.strip() for p in texto.split(",")]
        for p in partes:
            if p:
                conteo[p] = conteo.get(p, 0) + 1
    return conteo


def bloque_menciones(etiqueta, col_id):
    conteo = contar_menciones(col_id)
    if not conteo:
        return f'<div class="bloque"><h3>{esc(etiqueta)}</h3><div class="sin-dato">Sin datos registrados.</div></div>'
    ordenadas = sorted(conteo.items(), key=lambda kv: -kv[1])
    max_val = ordenadas[0][1] if ordenadas else 1
    filas_html = []
    for clave, n in ordenadas:
        pct = (n / max_val * 100) if max_val else 0
        filas_html.append(f'''
        <div class="barra-fila">
          <div class="barra-label">{esc(clave)}</div>
          <div class="barra-pista"><div class="barra-relleno" style="width:{pct:.1f}%; background:{BARRA_COLOR_MENCIONES}"></div></div>
          <div class="barra-valor">{n}</div>
        </div>''')
    return f'<div class="bloque"><h3>{esc(etiqueta)}</h3>{"".join(filas_html)}</div>'


# --- Construcción de la página ------------------------------------------
kpi_tiles = []
kpi_tiles.append(f'<div class="stat-tile"><div class="stat-label">Total de casos</div><div class="stat-valor">{total_casos}</div></div>')
for campo, (etiqueta, valor) in kpi_valores.items():
    kpi_tiles.append(f'<div class="stat-tile"><div class="stat-label">{esc(etiqueta)}</div><div class="stat-valor">{fmt_num(valor)}</div></div>')

bloques_categoria = "".join(
    bloque_categoria(campo, etiqueta, col_id, orden_fijo)
    for campo, (etiqueta, col_id, orden_fijo) in CATEGORIA_COLS.items()
)
bloques_menciones = "".join(bloque_menciones(etiqueta, col_id) for campo, (etiqueta, col_id) in MULTI_COLS.items())

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
now_iso = datetime.datetime.now().isoformat(timespec="seconds")

html_parts = []
html_parts.append("<!DOCTYPE html>")
html_parts.append('<html lang="es">')
html_parts.append("<head>")
html_parts.append('<meta charset="UTF-8">')
html_parts.append(f'<meta name="generated-at" content="{now_iso}">')
html_parts.append("<title>Resumen general — CRV Terremoto 2026</title>")
html_parts.append("<style>")
html_parts.append('body { font-family:"Open Sans",-apple-system,Segoe UI,Roboto,sans-serif; background:#F5F7FA; color:#20303F; margin:0; }')
html_parts.append(".topbar { background:#1C4269; color:#fff; padding:14px 28px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }")
html_parts.append(".topbar h1 { margin:0; font-size:17px; font-weight:700; }")
html_parts.append(".topbar .sub { font-size:11px; color:#AFC1D6; margin-top:2px; }")
html_parts.append(".topbar nav { display:flex; gap:8px; }")
html_parts.append(".topbar a { color:#fff; font-size:12px; text-decoration:none; border:1px solid rgba(255,255,255,.4); padding:6px 12px; border-radius:16px; }")
html_parts.append(".topbar a:hover { background:rgba(255,255,255,.12); }")
html_parts.append(".wrap { padding:18px 28px 40px; max-width:1200px; margin:0 auto; }")
html_parts.append(".updated { font-size:11px; color:#8A93A0; margin-bottom:16px; }")
html_parts.append(".stat-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:14px; margin-bottom:28px; }")
html_parts.append(".stat-tile { background:#fff; border:1px solid #E1E6EC; border-radius:10px; padding:14px 16px; }")
html_parts.append(".stat-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.3px; color:#8A93A0; margin-bottom:6px; }")
html_parts.append(".stat-valor { font-size:26px; font-weight:800; color:#14202C; }")
html_parts.append(".secciones { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:20px; align-items:start; }")
html_parts.append(".bloque { background:#fff; border:1px solid #E1E6EC; border-radius:10px; padding:16px 18px; }")
html_parts.append(".bloque h3 { margin:0 0 12px; font-size:13px; color:#20303F; text-transform:uppercase; letter-spacing:.3px; }")
html_parts.append(".barra-fila { display:grid; grid-template-columns:minmax(90px,140px) 1fr 28px; align-items:center; gap:10px; margin-bottom:8px; }")
html_parts.append(".cuadrante-fila { margin-bottom:12px; }")
html_parts.append(".cuadrante-cabeza { display:flex; align-items:flex-start; gap:8px; margin-bottom:5px; }")
html_parts.append(".num-badge { flex-shrink:0; width:20px; height:20px; border-radius:5px; color:#fff; font-size:11px; font-weight:700; display:flex; align-items:center; justify-content:center; font-family:Georgia,serif; }")
html_parts.append(".cuadrante-desc { flex:1; font-size:12px; color:#3A4048; line-height:1.35; }")
html_parts.append(".barra-label { font-size:12px; color:#3A4048; }")
html_parts.append(".barra-pista { background:#F0F2F5; border-radius:6px; height:12px; overflow:hidden; }")
html_parts.append(".barra-relleno { height:100%; border-radius:6px; }")
html_parts.append(".barra-valor { font-size:12px; color:#5B6672; text-align:right; font-variant-numeric:tabular-nums; }")
html_parts.append(".sin-dato { font-size:12px; color:#8A93A0; font-style:italic; }")
html_parts.append(".subtitulo { font-size:13px; font-weight:700; color:#5B6672; text-transform:uppercase; letter-spacing:.4px; margin:28px 0 12px; }")
html_parts.append("</style>")
html_parts.append("</head>")
html_parts.append("<body>")
html_parts.append(
    '<div class="topbar"><div><h1>Resumen general</h1>'
    '<div class="sub">Cruz Roja Venezolana · Diagnóstico terreno, Terremoto 2026</div></div>'
    '<nav><a href="index.html">Matriz de cuadrantes</a><a href="comunidades.html">Resumen de casos</a></nav></div>'
)
html_parts.append('<div class="wrap">')
html_parts.append(f'<div class="updated">Última actualización: {now} · {total_casos} casos</div>')
html_parts.append(f'<div class="stat-grid">{"".join(kpi_tiles)}</div>')
html_parts.append('<div class="subtitulo">Distribución por categoría</div>')
html_parts.append(f'<div class="secciones">{bloques_categoria}</div>')
html_parts.append('<div class="subtitulo">Menciones más frecuentes</div>')
html_parts.append(f'<div class="secciones">{bloques_menciones}</div>')
html_parts.append('</div>')
html_parts.append("""
<script>
(function () {
  var generadoEn = document.querySelector('meta[name="generated-at"]').content;
  function revisarActualizacion() {
    fetch(window.location.pathname + '?_=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        var m = html.match(/<meta name="generated-at" content="([^"]+)"/);
        if (m && m[1] !== generadoEn) { location.reload(); }
      })
      .catch(function () {});
  }
  setInterval(revisarActualizacion, 180000);
})();
</script>
""")
html_parts.append("</body></html>")

html = "\n".join(html_parts)

docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(docs_dir, exist_ok=True)
with open(os.path.join(docs_dir, "estadisticas.html"), "w", encoding="utf-8") as f:
    f.write(html)

print(f"Página de estadísticas generada con {total_casos} casos -> docs/estadisticas.html")
