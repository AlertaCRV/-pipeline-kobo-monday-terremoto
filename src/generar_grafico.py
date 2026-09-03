"""
Genera una pagina HTML con la matriz de decision Urgencia x Factibilidad,
usando los datos REALES actuales del tablero de Monday (via API).

Se guarda en docs/index.html -- GitHub Pages la publica automaticamente.

Version 4:
  - Layout en dos columnas: grafico a la izquierda, leyenda a la derecha
    (para que quepa todo en una pantalla).
  - Numero romano grande y centrado en cada cuadrante (semi-transparente).
  - Colores con mas contraste entre zonas.
  - Puntos del mismo color; se separan si caen muy cerca (linea guia).
  - Flechas bidireccionales junto al nombre de cada eje.
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
    "cuadrante": "color_mm6rzjwx",
    "familias": "numeric_mm6r640v",
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

PUNTO_COLOR = "#1C4269"

# (color de zona a saturacion plena, numero romano, nombre, descripcion breve)
ZONE_INFO = {
    ("alta_urg", "alta_fac"):  ("#A63A2E", "I", "Intervenir ya",
        "Urgente y con buen acceso: desplegar de inmediato."),
    ("alta_urg", "media_fac"): ("#C9822E", "III", "Intervenir con gestión de riesgo",
        "Urgente con dificultades moderadas: actuar con planificación."),
    ("alta_urg", "baja_fac"):  ("#8C2F26", "II", "Resolver acceso primero",
        "Urgente pero con acceso bloqueado: gestionar la vía antes de desplegar."),
    ("baja_urg", "alta_fac"):  ("#3F7D6B", "IV", "Oportunidad",
        "No urgente y de fácil acceso: atender cuando haya capacidad libre."),
    ("baja_urg", "media_fac"): ("#6E8A9E", "V", "Programar con preparación",
        "No urgente, con dificultades moderadas: programar con anticipación."),
    ("baja_urg", "baja_fac"):  ("#8A8D89", "VI", "Monitorear",
        "Ni urgente ni accesible por ahora: revisar en la próxima ronda."),
}

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def tint(hexcolor, amount=0.72):
    r, g, b = hex_to_rgb(hexcolor)
    r = round(r + (255 - r) * amount)
    g = round(g + (255 - g) * amount)
    b = round(b + (255 - b) * amount)
    return f"#{r:02X}{g:02X}{b:02X}"

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
    try:
        pu = float(vals.get(COLS["puntos_urgencia"]) or 0)
        pf = float(vals.get(COLS["puntos_factibilidad"]) or 0)
    except ValueError:
        continue
    try:
        familias = float(vals.get(COLS["familias"]) or 0)
    except ValueError:
        familias = 0
    items.append({"name": it["name"], "pu": pu, "pf": pf, "familias": familias})

if items:
    xs = [i["pf"] for i in items]; ys = [i["pu"] for i in items]
    x_min, x_max = min(xs + [-6]), max(xs + [8])
    y_min, y_max = min(ys + [-2]), max(ys + [10])
else:
    x_min, x_max, y_min, y_max = -6, 8, -2, 10

x_pad = (x_max - x_min) * 0.15 or 2
y_pad = (y_max - y_min) * 0.15 or 2
x_min -= x_pad; x_max += x_pad; y_min -= y_pad; y_max += y_pad

W, H = 800, 560
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 60, 24, 20, 58
PLOT_W = W - MARGIN_L - MARGIN_R
PLOT_H = H - MARGIN_T - MARGIN_B

def sx(px): return MARGIN_L + (px - x_min) / (x_max - x_min) * PLOT_W
def sy(py): return MARGIN_T + PLOT_H - (py - y_min) / (y_max - y_min) * PLOT_H

UMBRAL_URG, UMBRAL_FAC_ALTA, UMBRAL_FAC_MEDIA = 7, 0, -4

def marcas(vmin, vmax, n=6):
    span = vmax - vmin
    if span <= 0: return [vmin]
    raw_step = span / n
    magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
    step = magnitude
    for mult in (1, 2, 2.5, 5, 10):
        step = magnitude * mult
        if step >= raw_step: break
    start = math.floor(vmin / step) * step
    out, v = [], start
    while v <= vmax + step * 0.001:
        if v >= vmin - step * 0.001: out.append(round(v, 2))
        v += step
    return out

def fmt(v): return str(int(v)) if float(v).is_integer() else f"{v:g}"

x_ticks, y_ticks = marcas(x_min, x_max), marcas(y_min, y_max)

fac_bounds = sorted(set(b for b in [x_min, UMBRAL_FAC_MEDIA, UMBRAL_FAC_ALTA, x_max] if x_min <= b <= x_max) | {x_min, x_max})
urg_bounds = sorted(set(b for b in [y_min, UMBRAL_URG, y_max] if y_min <= b <= y_max) | {y_min, y_max})

rects_svg, labels_svg = [], []
for i in range(len(urg_bounds) - 1):
    y0, y1 = urg_bounds[i], urg_bounds[i + 1]
    urg_key = "alta_urg" if y0 >= UMBRAL_URG - 0.01 else "baja_urg"
    for j in range(len(fac_bounds) - 1):
        x0, x1 = fac_bounds[j], fac_bounds[j + 1]
        mid_x = (x0 + x1) / 2
        fac_key = "alta_fac" if mid_x >= UMBRAL_FAC_ALTA else ("media_fac" if mid_x >= UMBRAL_FAC_MEDIA else "baja_fac")
        base_color, numero, zona_nombre, _ = ZONE_INFO.get((urg_key, fac_key), ("#DDDDDD", "", "", ""))
        color = tint(base_color)
        rx, ry = sx(x0), sy(y1)
        rw, rh = sx(x1) - sx(x0), sy(y0) - sy(y1)
        rects_svg.append(f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" fill="{color}" stroke="#fff" stroke-width="2"/>')
        cx_zone, cy_zone = rx + rw / 2, ry + rh / 2
        labels_svg.append(
            f'<text x="{cx_zone:.1f}" y="{cy_zone+13:.1f}" text-anchor="middle" font-size="38" '
            f'font-weight="700" fill="{base_color}" fill-opacity="0.32" '
            f'font-family="Georgia, serif">{numero}</text>'
        )

lines_svg = []
for umbral in (UMBRAL_FAC_ALTA, UMBRAL_FAC_MEDIA):
    if x_min <= umbral <= x_max:
        lx = sx(umbral)
        lines_svg.append(f'<line x1="{lx:.1f}" y1="{MARGIN_T}" x2="{lx:.1f}" y2="{MARGIN_T+PLOT_H}" stroke="#C7CDD3" stroke-dasharray="4,4" stroke-width="1" />')
if y_min <= UMBRAL_URG <= y_max:
    ly = sy(UMBRAL_URG)
    lines_svg.append(f'<line x1="{MARGIN_L}" y1="{ly:.1f}" x2="{MARGIN_L+PLOT_W}" y2="{ly:.1f}" stroke="#C7CDD3" stroke-dasharray="4,4" stroke-width="1" />')

ticks_svg = []
for t in x_ticks:
    tx = sx(t)
    ticks_svg.append(f'<line x1="{tx:.1f}" y1="{MARGIN_T+PLOT_H}" x2="{tx:.1f}" y2="{MARGIN_T+PLOT_H+5}" stroke="#8A93A0" stroke-width="1"/>')
    ticks_svg.append(f'<text x="{tx:.1f}" y="{MARGIN_T+PLOT_H+18}" text-anchor="middle" font-size="10" fill="#66768A" font-family="Open Sans, sans-serif">{fmt(t)}</text>')
for t in y_ticks:
    ty = sy(t)
    ticks_svg.append(f'<line x1="{MARGIN_L-5}" y1="{ty:.1f}" x2="{MARGIN_L}" y2="{ty:.1f}" stroke="#8A93A0" stroke-width="1"/>')
    ticks_svg.append(f'<text x="{MARGIN_L-9}" y="{ty+3.5:.1f}" text-anchor="end" font-size="10" fill="#66768A" font-family="Open Sans, sans-serif">{fmt(t)}</text>')

axes_svg = (
    f'<line x1="{MARGIN_L}" y1="{MARGIN_T}" x2="{MARGIN_L}" y2="{MARGIN_T+PLOT_H}" stroke="#3A4048" stroke-width="1.4"/>'
    f'<line x1="{MARGIN_L}" y1="{MARGIN_T+PLOT_H}" x2="{MARGIN_L+PLOT_W}" y2="{MARGIN_T+PLOT_H}" stroke="#3A4048" stroke-width="1.4"/>'
    + "".join(ticks_svg) +
    f'<text x="{MARGIN_L+PLOT_W/2}" y="{H-6}" text-anchor="middle" font-size="13" font-weight="600" fill="#20303F" font-family="Open Sans, sans-serif">Factibilidad \u2194</text>'
    f'<text x="14" y="{MARGIN_T+PLOT_H/2}" text-anchor="middle" font-size="13" font-weight="600" fill="#20303F" font-family="Open Sans, sans-serif" transform="rotate(-90 14 {MARGIN_T+PLOT_H/2})">Urgencia \u2195</text>'
)

raw_points = [{"item": it, "x": sx(it["pf"]), "y": sy(it["pu"])} for it in items]
parent = list(range(len(raw_points)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i
def union(i, j):
    ri, rj = find(i), find(j)
    if ri != rj: parent[ri] = rj

RADIUS_CLUSTER = 22
for i in range(len(raw_points)):
    for j in range(i + 1, len(raw_points)):
        dx = raw_points[i]["x"] - raw_points[j]["x"]
        dy = raw_points[i]["y"] - raw_points[j]["y"]
        if (dx * dx + dy * dy) ** 0.5 < RADIUS_CLUSTER:
            union(i, j)

clusters = {}
for i in range(len(raw_points)):
    clusters.setdefault(find(i), []).append(i)

for idxs in clusters.values():
    n = len(idxs)
    if n == 1:
        p = raw_points[idxs[0]]
        p["dx"], p["dy"] = p["x"], p["y"]
        continue
    cx = sum(raw_points[i]["x"] for i in idxs) / n
    cy = sum(raw_points[i]["y"] for i in idxs) / n
    spread_r = 13 + 5 * n
    for k, i in enumerate(idxs):
        angle = 2 * math.pi * k / n
        raw_points[i]["dx"] = cx + spread_r * math.cos(angle)
        raw_points[i]["dy"] = cy + spread_r * math.sin(angle)

max_familias = max([i["familias"] for i in items], default=1) or 1
leader_svg, points_svg = [], []
for p in raw_points:
    it = p["item"]
    dx, dy = p["dx"], p["dy"]
    moved = abs(dx - p["x"]) > 2 or abs(dy - p["y"]) > 2
    if moved:
        leader_svg.append(f'<line x1="{p["x"]:.1f}" y1="{p["y"]:.1f}" x2="{dx:.1f}" y2="{dy:.1f}" stroke="#B7BEC7" stroke-width="1"/>')
        leader_svg.append(f'<circle cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="2.2" fill="#B7BEC7"/>')
    r = 6 + 12 * (it["familias"] / max_familias) ** 0.5
    tooltip = f"{it['name']}\\nFamilias: {int(it['familias'])}"
    points_svg.append(
        f'<g class="punto"><circle cx="{dx:.1f}" cy="{dy:.1f}" r="{r:.1f}" fill="{PUNTO_COLOR}" '
        f'fill-opacity="0.82" stroke="#0F2A47" stroke-width="1.2"><title>{tooltip}</title></circle>'
        f'<text x="{dx:.1f}" y="{dy - r - 6:.1f}" text-anchor="middle" font-size="10" '
        f'fill="#2A3038" font-family="Open Sans, sans-serif">{it["name"][:24]}</text></g>'
    )

legend_rows = []
for (u, f), (color, numero, nombre, desc) in ZONE_INFO.items():
    legend_rows.append(
        f'<div class="legend-row"><span class="num-badge" style="background:{color}">{numero}</span>'
        f'<div><div class="legend-title">{nombre}</div><div class="legend-desc">{desc}</div></div></div>'
    )

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

svg_content = (
    "".join(rects_svg) + "".join(labels_svg) + "".join(lines_svg) + axes_svg
    + "".join(leader_svg) + "".join(points_svg)
)
legend_content = "".join(legend_rows)

html_parts = []
html_parts.append("<!DOCTYPE html>")
html_parts.append('<html lang="es">')
html_parts.append("<head>")
html_parts.append('<meta charset="UTF-8">')
html_parts.append("<title>Matriz de Urgencia \u00d7 Factibilidad (Comunidades)</title>")
html_parts.append("<style>")
html_parts.append('body { font-family:"Open Sans",-apple-system,Segoe UI,Roboto,sans-serif; background:#fff; color:#20303F; margin:0; }')
html_parts.append(".topbar { background:#1C4269; color:#fff; padding:10px 28px; }")
html_parts.append(".topbar h1 { margin:0; font-size:16px; font-weight:700; }")
html_parts.append(".topbar .sub { font-size:11px; color:#AFC1D6; margin-top:2px; }")
html_parts.append(".wrap { padding:12px 28px 18px; max-width:1280px; margin:0 auto; }")
html_parts.append(".updated { font-size:11px; color:#8A93A0; margin-bottom:10px; }")
html_parts.append(".layout { display:flex; gap:24px; align-items:flex-start; flex-wrap:wrap; }")
html_parts.append(".chart-col { flex:1 1 560px; min-width:400px; }")
html_parts.append("svg { border:1px solid #E1E6EC; border-radius:10px; background:#fff; width:100%; height:auto; display:block; }")
html_parts.append(".legend-col { flex:0 0 300px; max-width:320px; }")
html_parts.append('.legend-col h2 { font-size:12px; margin:4px 0 12px; color:#20303F; text-transform:uppercase; letter-spacing:.4px; }')
html_parts.append(".legend { display:flex; flex-direction:column; gap:13px; }")
html_parts.append(".legend-row { display:flex; align-items:flex-start; gap:10px; }")
html_parts.append(".num-badge { flex-shrink:0; width:22px; height:22px; border-radius:5px; color:#fff; font-size:11px; font-weight:700; display:flex; align-items:center; justify-content:center; font-family:Georgia,serif; }")
html_parts.append(".legend-title { font-size:12.5px; font-weight:700; color:#20303F; }")
html_parts.append(".legend-desc { font-size:11.5px; color:#5B6672; margin-top:1px; line-height:1.3; }")
html_parts.append(".nota { font-size:11px; color:#8A93A0; margin-top:14px; }")
html_parts.append("@media (max-width:760px){ .layout{flex-direction:column;} .legend-col{max-width:100%;} }")
html_parts.append("</style>")
html_parts.append("</head>")
html_parts.append("<body>")
html_parts.append('<div class="topbar"><h1>Matriz de Urgencia \u00d7 Factibilidad (Comunidades)</h1>'
                   '<div class="sub">Cruz Roja Venezolana \u00b7 Diagn\u00f3stico terreno, Terremoto 2026</div></div>')
html_parts.append('<div class="wrap">')
html_parts.append(f'<div class="updated">\u00daltima actualizaci\u00f3n: {now}</div>')
html_parts.append('<div class="layout">')
html_parts.append('<div class="chart-col">')
html_parts.append(f'<svg viewBox="0 0 {W} {H}">{svg_content}</svg>')
html_parts.append('</div>')
nota_html = ('<div class="nota">El tama\u00f1o de cada punto representa el n\u00famero de familias. '
             'Los puntos muy pr\u00f3ximos se separan levemente para poder distinguirlos; la l\u00ednea gris '
             'indica su posici\u00f3n real. Pasa el mouse sobre un punto para ver el nombre y el n\u00famero de familias.</div>')
html_parts.append('<div class="legend-col"><h2>Cuadrantes</h2><div class="legend">' + legend_content + '</div>' + nota_html + '</div>')
html_parts.append('</div>')
html_parts.append('</div>')
html_parts.append("</body></html>")

html = "\n".join(html_parts)

os.makedirs(os.path.join(os.path.dirname(__file__), "..", "docs"), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "..", "docs", "index.html"), "w", encoding="utf-8") as f:
    f.write(html)

print(f"Página generada con {len(items)} evaluaciones -> docs/index.html")
