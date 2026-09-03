"""
Genera una pagina HTML con la matriz de decision Urgencia x Factibilidad,
usando los datos REALES actuales del tablero de Monday (via API).

Se guarda en docs/index.html en la raiz del repositorio -- esa carpeta la
publica GitHub Pages automaticamente como sitio web.

Se corre despues de cada sincronizacion (sync-kobo-monday.yml la llama).
"""
import os
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

CUADRANTE_COLOR = {
    "Intervenir ya": "#C4302B",
    "Intervenir con gestión de riesgo": "#C97B14",
    "Resolver acceso primero": "#C97B14",
    "Oportunidad": "#8A6D00",
    "Programar con preparación": "#5C6B73",
    "Monitorear": "#999999",
}
DEFAULT_COLOR = "#2C6FB0"

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
        "nivel_urg": vals.get(COLS["nivel_urgencia"]) or "",
        "nivel_fac": vals.get(COLS["nivel_factibilidad"]) or "",
        "cuadrante": vals.get(COLS["cuadrante"]) or "Sin cuadrante",
        "familias": familias,
        "tipo_area": vals.get(COLS["tipo_area"]) or "",
    })

# ---- Calcular rango de ejes con margen ----
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

W, H = 900, 560
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 70, 30, 30, 60
PLOT_W = W - MARGIN_L - MARGIN_R
PLOT_H = H - MARGIN_T - MARGIN_B

def sx(px):
    return MARGIN_L + (px - x_min) / (x_max - x_min) * PLOT_W

def sy(py):
    return MARGIN_T + PLOT_H - (py - y_min) / (y_max - y_min) * PLOT_H

UMBRAL_URG = 7
UMBRAL_FAC_ALTA = 0
UMBRAL_FAC_MEDIA = -4

# Fondo de cuadrantes (bandas)
bands = []
fac_bounds = [x_min, UMBRAL_FAC_MEDIA, UMBRAL_FAC_ALTA, x_max]
fac_bounds = sorted(set(b for b in fac_bounds if x_min <= b <= x_max) | {x_min, x_max})
urg_bounds = sorted(set(b for b in [y_min, UMBRAL_URG, y_max] if y_min <= b <= y_max) | {y_min, y_max})

band_colors = {
    ("alta_urg", "baja_fac"): "#FBE6E5",
    ("alta_urg", "media_fac"): "#FCF0DC",
    ("alta_urg", "alta_fac"): "#FBE6E5",
    ("baja_urg", "baja_fac"): "#F2F2F2",
    ("baja_urg", "media_fac"): "#F2F2F2",
    ("baja_urg", "alta_fac"): "#FFF9DB",
}

rects_svg = []
for i in range(len(urg_bounds) - 1):
    y0, y1 = urg_bounds[i], urg_bounds[i+1]
    urg_key = "alta_urg" if y0 >= UMBRAL_URG - 0.01 else "baja_urg"
    for j in range(len(fac_bounds) - 1):
        x0, x1 = fac_bounds[j], fac_bounds[j+1]
        mid_x = (x0 + x1) / 2
        if mid_x >= UMBRAL_FAC_ALTA:
            fac_key = "alta_fac"
        elif mid_x >= UMBRAL_FAC_MEDIA:
            fac_key = "media_fac"
        else:
            fac_key = "baja_fac"
        color = band_colors.get((urg_key, fac_key), "#FFFFFF")
        rx, ry = sx(x0), sy(y1)
        rw, rh = sx(x1) - sx(x0), sy(y0) - sy(y1)
        rects_svg.append(f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" fill="{color}" />')

# Lineas divisorias
lines_svg = []
if x_min <= UMBRAL_FAC_ALTA <= x_max:
    lx = sx(UMBRAL_FAC_ALTA)
    lines_svg.append(f'<line x1="{lx:.1f}" y1="{MARGIN_T}" x2="{lx:.1f}" y2="{MARGIN_T+PLOT_H}" stroke="#999" stroke-dasharray="5,4" stroke-width="1.5" />')
if x_min <= UMBRAL_FAC_MEDIA <= x_max:
    lx = sx(UMBRAL_FAC_MEDIA)
    lines_svg.append(f'<line x1="{lx:.1f}" y1="{MARGIN_T}" x2="{lx:.1f}" y2="{MARGIN_T+PLOT_H}" stroke="#bbb" stroke-dasharray="3,3" stroke-width="1" />')
if y_min <= UMBRAL_URG <= y_max:
    ly = sy(UMBRAL_URG)
    lines_svg.append(f'<line x1="{MARGIN_L}" y1="{ly:.1f}" x2="{MARGIN_L+PLOT_W}" y2="{ly:.1f}" stroke="#999" stroke-dasharray="5,4" stroke-width="1.5" />')

# Ejes
axes_svg = f'''
<line x1="{MARGIN_L}" y1="{MARGIN_T}" x2="{MARGIN_L}" y2="{MARGIN_T+PLOT_H}" stroke="#333" stroke-width="1.5"/>
<line x1="{MARGIN_L}" y1="{MARGIN_T+PLOT_H}" x2="{MARGIN_L+PLOT_W}" y2="{MARGIN_T+PLOT_H}" stroke="#333" stroke-width="1.5"/>
<text x="{MARGIN_L+PLOT_W/2}" y="{H-15}" text-anchor="middle" font-size="13" fill="#333" font-family="Open Sans, sans-serif">Puntos Factibilidad</text>
<text x="18" y="{MARGIN_T+PLOT_H/2}" text-anchor="middle" font-size="13" fill="#333" font-family="Open Sans, sans-serif" transform="rotate(-90 18 {MARGIN_T+PLOT_H/2})">Puntos Urgencia</text>
'''

# Puntos
max_familias = max([i["familias"] for i in items], default=1) or 1
points_svg = []
for it in items:
    cx, cy = sx(it["pf"]), sy(it["pu"])
    r = 6 + 14 * (it["familias"] / max_familias) ** 0.5
    color = CUADRANTE_COLOR.get(it["cuadrante"], DEFAULT_COLOR)
    tooltip = (f"{it['name']} ({it['tipo_area']})\\n"
               f"Cuadrante: {it['cuadrante']}\\n"
               f"Urgencia: {it['nivel_urg']} ({it['pu']:.1f} pts)\\n"
               f"Factibilidad: {it['nivel_fac']} ({it['pf']:.1f} pts)\\n"
               f"Familias: {int(it['familias'])}")
    points_svg.append(
        f'<g class="punto"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{color}" '
        f'fill-opacity="0.75" stroke="{color}" stroke-width="2"><title>{tooltip}</title></circle>'
        f'<text x="{cx:.1f}" y="{cy - r - 6:.1f}" text-anchor="middle" font-size="10.5" '
        f'fill="#333" font-family="Open Sans, sans-serif">{it["name"][:28]}</text></g>'
    )

legend_items = list(dict.fromkeys(CUADRANTE_COLOR.keys()))
legend_svg = ""
ly = 20
legend_rows = []
for name, color in CUADRANTE_COLOR.items():
    legend_rows.append(
        f'<div class="legend-row"><span class="swatch" style="background:{color}"></span>{name}</div>'
    )

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
  .swatch {{ width:14px; height:14px; border-radius:3px; display:inline-block; }}
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
  <div class="updated">Última actualización: {now} (se regenera automáticamente con cada sincronización)</div>
  <svg viewBox="0 0 {W} {H}" width="100%" height="auto">
    {"".join(rects_svg)}
    {"".join(lines_svg)}
    {axes_svg}
    {"".join(points_svg)}
  </svg>
  <div class="legend">
    {"".join(legend_rows)}
  </div>
  <div class="nota">El tamaño de cada punto representa el número de familias. Pasa el mouse sobre un punto para ver el detalle completo.</div>
</div>
</body>
</html>
'''

os.makedirs(os.path.join(os.path.dirname(__file__), "..", "docs"), exist_ok=True)
out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Página generada con {len(items)} evaluaciones -> docs/index.html")
