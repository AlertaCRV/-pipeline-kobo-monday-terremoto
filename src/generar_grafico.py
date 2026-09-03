"""
Genera una pagina HTML con la matriz de decision Urgencia x Factibilidad,
usando los datos REALES actuales del tablero de Monday (via API).

Se guarda en docs/index.html en la raiz del repositorio -- esa carpeta la
publica GitHub Pages automaticamente como sitio web.

Version 2:
  - Los puntos son todos del mismo color (navy).
  - Cada cuadrante de fondo tiene su propio color distintivo, con su
    nombre etiquetado dentro de la zona.
  - Tooltip simplificado: solo nombre y numero de familias.
  - Ejes con nombre corto ("Factibilidad" / "Urgencia") y con marcas
    numericas visibles.
"""
import os
import math
import datetime
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

COLS = {
    "puntos_urgencia": "numeric_mm6rzmct",
    "puntos_factibilidad": "numeric_mm6rfwcg",
    "nivel_urgencia": "color_mm6rr2g5",
    "nivel_factibilidad": "color_mm6rkghg",
    "cuadrante": "color_mm6rzjwx",
    "familias": "numeric_mm6r640v",
    "tipo_area": "color_mm6r3ja7",
}
COL_IDS = list(COLS.values())

QUERY = """
query ($board: ID!, $cols: [String!]) {
  boards (ids: [$board]) {
    items_page (limit: 200) {
      items {
        id
        name
        column_values (ids: $cols) { id text }
      }
    }
  }
}
"""

PUNTO_COLOR = "#1C4269"  # todos los puntos del mismo color (navy CRV)

# Color de fondo distinto por cada uno de los 6 cuadrantes reales
ZONE_COLOR = {
    ("alta_urg", "alta_fac"):  ("#FBE6E5", "Intervenir ya"),
    ("alta_urg", "media_fac"): ("#FCEEDD", "Intervenir con gestión de riesgo"),
    ("alta_urg", "baja_fac"):  ("#FDF3D0", "Resolver acceso primero"),
    ("baja_urg", "alta_fac"):  ("#F3F8DD", "Oportunidad"),
    ("baja_urg", "media_fac"): ("#E3F1FA", "Programar con preparación"),
    ("baja_urg", "baja_fac"):  ("#EFEFEF", "Monitorear"),
}

resp = requests.post(
    MONDAY_API_URL,
    json={"query": QUERY, "variables": {"board": MONDAY_BOARD_ID, "cols": COL_IDS}},
    headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()
items_raw = data["data"]["boards"][0]["items_page"]["items"]

items = []
for it in items_raw:
    vals = {cv["id"]: cv["text"] for cv in it["column_values"]}
    try:
        pu = float(vals.get(COLS["puntos_urgencia"]) or 0)
        pf = float(vals.get(COLS["puntos_factibilidad"]) or 0)
    except ValueError:
        continue
    familias_raw = vals.get(COLS["familias"]) or "0"
    try:
        familias = float(familias_raw)
    except ValueError:
        familias = 0
    items.append({
        "name": it["name"],
        "pu": pu,
        "pf": pf,
        "cuadrante": vals.get(COLS["cuadrante"]) or "Sin cuadrante",
        "familias": familias,
    })

# ---- Rango de ejes con margen ----
if items:
    xs = [i["pf"] for i in items]
    ys = [i["pu"] for i in items]
    x_min, x_max = min(xs + [-6]), max(xs + [8])
    y_min, y_max = min(ys + [-2]), max(ys + [10])
else:
    x_min, x_max, y_min, y_max = -6, 8, -2, 10

x_pad = (x_max - x_min) * 0.15 or 2
y_pad = (y_max - y_min) * 0.15 or 2
x_min -= x_pad; x_max += x_pad
y_min -= y_pad; y_max += y_pad

W, H = 900, 580
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 65, 30, 25, 65
PLOT_W = W - MARGIN_L - MARGIN_R
PLOT_H = H - MARGIN_T - MARGIN_B

def sx(px):
    return MARGIN_L + (px - x_min) / (x_max - x_min) * PLOT_W

def sy(py):
    return MARGIN_T + PLOT_H - (py - y_min) / (y_max - y_min) * PLOT_H

UMBRAL_URG = 7
UMBRAL_FAC_ALTA = 0
UMBRAL_FAC_MEDIA = -4

# ---- Marcas numericas (ticks) ----
def marcas(vmin, vmax, n=6):
    span = vmax - vmin
    if span <= 0:
        return [vmin]
    raw_step = span / n
    magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
    step = magnitude
    for mult in (1, 2, 2.5, 5, 10):
        step = magnitude * mult
        if step >= raw_step:
            break
    start = math.floor(vmin / step) * step
    out = []
    v = start
    while v <= vmax + step * 0.001:
        if v >= vmin - step * 0.001:
            out.append(round(v, 2))
        v += step
    return out

x_ticks = marcas(x_min, x_max)
y_ticks = marcas(y_min, y_max)

def fmt(v):
    return str(int(v)) if float(v).is_integer() else f"{v:g}"

# ---- Fondo de cuadrantes ----
fac_bounds = sorted(set(b for b in [x_min, UMBRAL_FAC_MEDIA, UMBRAL_FAC_ALTA, x_max] if x_min <= b <= x_max) | {x_min, x_max})
urg_bounds = sorted(set(b for b in [y_min, UMBRAL_URG, y_max] if y_min <= b <= y_max) | {y_min, y_max})

rects_svg = []
labels_svg = []
for i in range(len(urg_bounds) - 1):
    y0, y1 = urg_bounds[i], urg_bounds[i + 1]
    urg_key = "alta_urg" if y0 >= UMBRAL_URG - 0.01 else "baja_urg"
    for j in range(len(fac_bounds) - 1):
        x0, x1 = fac_bounds[j], fac_bounds[j + 1]
        mid_x = (x0 + x1) / 2
        if mid_x >= UMBRAL_FAC_ALTA:
            fac_key = "alta_fac"
        elif mid_x >= UMBRAL_FAC_MEDIA:
            fac_key = "media_fac"
        else:
            fac_key = "baja_fac"
        color, zona_nombre = ZONE_COLOR.get((urg_key, fac_key), ("#FFFFFF", ""))
        rx, ry = sx(x0), sy(y1)
        rw, rh = sx(x1) - sx(x0), sy(y0) - sy(y1)
        rects_svg.append(f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" fill="{color}" />')
        if rw > 55 and rh > 25:
            labels_svg.append(
                f'<text x="{rx+8:.1f}" y="{ry+16:.1f}" font-size="10.5" fill="#7a7a7a" '
                f'font-style="italic" font-family="Open Sans, sans-serif">{zona_nombre}</text>'
            )

# ---- Lineas divisorias ----
lines_svg = []
for umbral in (UMBRAL_FAC_ALTA, UMBRAL_FAC_MEDIA):
    if x_min <= umbral <= x_max:
        lx = sx(umbral)
        lines_svg.append(f'<line x1="{lx:.1f}" y1="{MARGIN_T}" x2="{lx:.1f}" y2="{MARGIN_T+PLOT_H}" stroke="#999" stroke-dasharray="5,4" stroke-width="1.3" />')
if y_min <= UMBRAL_URG <= y_max:
    ly = sy(UMBRAL_URG)
    lines_svg.append(f'<line x1="{MARGIN_L}" y1="{ly:.1f}" x2="{MARGIN_L+PLOT_W}" y2="{ly:.1f}" stroke="#999" stroke-dasharray="5,4" stroke-width="1.3" />')

# ---- Ejes + marcas numericas ----
ticks_svg = []
for t in x_ticks:
    tx = sx(t)
    ticks_svg.append(f'<line x1="{tx:.1f}" y1="{MARGIN_T+PLOT_H}" x2="{tx:.1f}" y2="{MARGIN_T+PLOT_H+5}" stroke="#333" stroke-width="1"/>')
    ticks_svg.append(f'<text x="{tx:.1f}" y="{MARGIN_T+PLOT_H+18}" text-anchor="middle" font-size="10.5" fill="#555" font-family="Open Sans, sans-serif">{fmt(t)}</text>')
for t in y_ticks:
    ty = sy(t)
    ticks_svg.append(f'<line x1="{MARGIN_L-5}" y1="{ty:.1f}" x2="{MARGIN_L}" y2="{ty:.1f}" stroke="#333" stroke-width="1"/>')
    ticks_svg.append(f'<text x="{MARGIN_L-9}" y="{ty+3.5:.1f}" text-anchor="end" font-size="10.5" fill="#555" font-family="Open Sans, sans-serif">{fmt(t)}</text>')

axes_svg = f'''
<line x1="{MARGIN_L}" y1="{MARGIN_T}" x2="{MARGIN_L}" y2="{MARGIN_T+PLOT_H}" stroke="#333" stroke-width="1.5"/>
<line x1="{MARGIN_L}" y1="{MARGIN_T+PLOT_H}" x2="{MARGIN_L+PLOT_W}" y2="{MARGIN_T+PLOT_H}" stroke="#333" stroke-width="1.5"/>
{"".join(ticks_svg)}
<text x="{MARGIN_L+PLOT_W/2}" y="{H-8}" text-anchor="middle" font-size="13.5" font-weight="600" fill="#20303F" font-family="Open Sans, sans-serif">Factibilidad</text>
<text x="16" y="{MARGIN_T+PLOT_H/2}" text-anchor="middle" font-size="13.5" font-weight="600" fill="#20303F" font-family="Open Sans, sans-serif" transform="rotate(-90 16 {MARGIN_T+PLOT_H/2})">Urgencia</text>
'''

# ---- Puntos ----
max_familias = max([i["familias"] for i in items], default=1) or 1
points_svg = []
for it in items:
    cx, cy = sx(it["pf"]), sy(it["pu"])
    r = 6 + 14 * (it["familias"] / max_familias) ** 0.5
    tooltip = f"{it['name']}\\nFamilias: {int(it['familias'])}"
    points_svg.append(
        f'<g class="punto"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{PUNTO_COLOR}" '
        f'fill-opacity="0.78" stroke="{PUNTO_COLOR}" stroke-width="1.5"><title>{tooltip}</title></circle>'
        f'<text x="{cx:.1f}" y="{cy - r - 6:.1f}" text-anchor="middle" font-size="10.5" '
        f'fill="#333" font-family="Open Sans, sans-serif">{it["name"][:28]}</text></g>'
    )

legend_rows = []
for (u, f), (color, nombre) in ZONE_COLOR.items():
    legend_rows.append(f'<div class="legend-row"><span class="swatch" style="background:{color}"></span>{nombre}</div>')

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Matriz de decisión — CRV Terremoto 2026</title>
<style>
  body {{ font-family: "Open Sans", -apple-system, Segoe UI, Roboto, sans-serif; background:#fff; color:#20303F; margin:0; }}
  .topbar {{ background:#1C4269; color:#fff; padding:18px 32px; }}
  .topbar h1 {{ margin:0; font-size:19px; }}
  .topbar .sub {{ font-size:12px; color:#AFC1D6; margin-top:4px; }}
  .wrap {{ padding:24px 32px; max-width:1000px; margin:0 auto; }}
  .updated {{ font-size:12px; color:#66768A; margin-bottom:14px; }}
  svg {{ border:1px solid #E1E6EC; border-radius:8px; background:#fff; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:16px; margin-top:16px; font-size:13px; }}
  .legend-row {{ display:flex; align-items:center; gap:6px; }}
  .swatch {{ width:14px; height:14px; border-radius:3px; display:inline-block; border:1px solid #ddd; }}
  .punto text {{ pointer-events:none; }}
  .punto circle {{ cursor:pointer; }}
  .nota {{ font-size:12px; color:#999; margin-top:18px; }}
</style>
</head>
<body>
<div class="topbar">
  <h1>Matriz de decisión — Urgencia × Factibilidad</h1>
  <div class="sub">Cruz Roja Venezolana · Diagnóstico terreno, Terremoto 2026</div>
</div>
<div class="wrap">
  <div class="updated">Última actualización: {now}</div>
  <svg viewBox="0 0 {W} {H}" width="100%" height="auto">
    {"".join(rects_svg)}
    {"".join(labels_svg)}
    {"".join(lines_svg)}
    {axes_svg}
    {"".join(points_svg)}
  </svg>
  <div class="legend">
    {"".join(legend_rows)}
  </div>
  <div class="nota">El tamaño de cada punto representa el número de familias. Pasa el mouse sobre un punto para ver el nombre y el número de familias.</div>
</div>
</body>
</html>
'''

os.makedirs(os.path.join(os.path.dirname(__file__), "..", "docs"), exist_ok=True)
out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Página generada con {len(items)} evaluaciones -> docs/index.html")
