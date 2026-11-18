#!/usr/bin/env python3
"""Genera el mapa de localidades (SVG/HTML) y el inventario de sillas (CSV).

Reglas:
- ULTRA y VIP: se bloquea el 30% de las mesas (dicen "RESERVADA").
- Las mesas disponibles llevan 10 sillas; mesas y sillas se enumeran por bloque.
  Mesas: 1..N de izquierda a derecha, de escenario hacia atrás.
  Sillas: 1-5 lado izquierdo y 6-10 lado derecho (de escenario hacia atrás).
- PREFERENCIA y GENERAL quedan igual que en el croquis original.
"""
import csv
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
W = 1728  # 18 in de ancho a 96 dpi; el alto se ajusta al contenido

# ---------------------------------------------------------------- geometría
COLS_SIDE = 12
PITCH = 50          # distancia entre centros de mesas
AISLE = 46          # pasillo central
TABLE_W, TABLE_H = 18, 62
CHAIR_R = 5.5
CHAIR_DX = TABLE_W / 2 + 2 + CHAIR_R
CHAIR_DY = [-24, -12, 0, 12, 24]
ROW_PITCH = 84
GROUP_W = COLS_SIDE * PITCH - 6
BLOCK_W = GROUP_W * 2 + AISLE
X0 = (W - BLOCK_W) / 2


def col_x(c):
    """Centro x de la columna c (0..23)."""
    if c < COLS_SIDE:
        return X0 + 22 + c * PITCH
    return X0 + GROUP_W + AISLE + 22 + (c - COLS_SIDE) * PITCH


# ---------------------------------------------------------------- bloques
def ultra_layout():
    # 5 filas x 24 mesas = 120
    return [[c for c in range(24)] for _ in range(5)]


def vip_layout():
    # 150 mesas, 11 por lado (columnas 1-22, centradas en el bloque)
    # fila 1: 10 + FOH + 10 (el FOH ocupa una mesa de cada sección)
    # filas 2-6: 22 ; fila 7: 10 + 10 (sin las mesas de las esquinas)
    # => 20 + 5*22 + 20 = 150
    first = list(range(1, 11)) + list(range(13, 23))
    last = list(range(2, 12)) + list(range(12, 22))
    return [first] + [list(range(1, 23)) for _ in range(5)] + [last]


def reserved_set(layout, rows_full, extra_row, extra_left, extra_right):
    """Bloquea las primeras filas completas + las mesas junto al pasillo
    central en la fila siguiente."""
    res = set()
    for r in range(rows_full):
        for c in layout[r]:
            res.add((r, c))
    if extra_left or extra_right:
        cols = layout[extra_row]
        left = [c for c in cols if c < COLS_SIDE][-extra_left:] if extra_left else []
        right = [c for c in cols if c >= COLS_SIDE][:extra_right]
        res.update((extra_row, c) for c in left + right)
    return res


BLOCKS = [
    dict(key="ULTRA", price="Q1,210", layout=ultra_layout(),
         reserve=dict(rows_full=1, extra_row=1, extra_left=6, extra_right=6),
         c_main="#D9542B", c_dark="#9A3412", c_bg="#FBEDE6", c_chair="#F4B79C"),
    dict(key="VIP", price="Q770", layout=vip_layout(),
         reserve=dict(rows_full=2, extra_row=2, extra_left=2, extra_right=1),
         c_main="#5B4FCF", c_dark="#3B2F9A", c_bg="#EEEDFB", c_chair="#C3BDF3"),
]

for b in BLOCKS:
    total = sum(len(r) for r in b["layout"])
    res = reserved_set(b["layout"], **b["reserve"])
    b["total"], b["reserved"] = total, res
    target = math.floor(total * 0.30 + 0.5)
    assert len(res) == target, (b["key"], len(res), target)

# ---------------------------------------------------------------- SVG
svg = []
add = svg.append
FONT = "Inter, 'DejaVu Sans', sans-serif"


def text(x, y, s, size, fill="#222", weight=400, anchor="middle", extra=""):
    add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{s}</text>')


def draw_table(cx, cy, b, num):
    x, y = cx - TABLE_W / 2, cy - TABLE_H / 2
    for side in (-1, 1):
        for i, dy in enumerate(CHAIR_DY):
            seat = (i + 1) if side == -1 else (i + 6)
            px, py = cx + side * CHAIR_DX, cy + dy
            add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{CHAIR_R}" fill="{b["c_chair"]}" '
                f'stroke="{b["c_dark"]}" stroke-width="0.7"/>')
            text(px, py + 2.1, seat, 5.6, b["c_dark"], 700)
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{TABLE_W}" height="{TABLE_H}" rx="3" '
        f'fill="{b["c_main"]}" stroke="{b["c_dark"]}" stroke-width="0.8"/>')
    text(cx, cy + 3, num, 8.5 if num < 100 else 7.4, "#fff", 800)


def draw_reserved(cx, cy, num):
    x, y = cx - TABLE_W / 2, cy - TABLE_H / 2
    for side in (-1, 1):
        for dy in CHAIR_DY:
            add(f'<circle cx="{cx + side * CHAIR_DX:.1f}" cy="{cy + dy:.1f}" r="{CHAIR_R}" '
                f'fill="#EEEEEE" stroke="#BDBDBD" stroke-width="0.6" stroke-dasharray="1.5 1.2"/>')
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{TABLE_W}" height="{TABLE_H}" rx="3" '
        f'fill="url(#hatch)" stroke="#6B6B6B" stroke-width="0.8"/>')
    text(cx, cy - 20, num, 8 if num < 100 else 7, "#222", 800)
    ty = cy + 8
    text(cx + 2.2, ty, "RESERVADA", 5.8, "#333", 800,
         extra=f'transform="rotate(-90 {cx + 2.2:.1f} {ty:.1f})" letter-spacing="0.2"')


rows_csv = []
y = 0

add('<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" '
    'patternTransform="rotate(45)"><rect width="5" height="5" fill="#D6D6D6"/>'
    '<line x1="0" y1="0" x2="0" y2="5" stroke="#B0B0B0" stroke-width="2"/></pattern></defs>')
add('<rect width="100%" height="100%" fill="#FFFFFF"/>')

# título + escenario
text(W / 2, 78, "MAPA DE LOCALIDADES", 40, "#222", 800, extra='letter-spacing="1"')
text(W / 2, 112, "ULTRA y VIP: cada mesa numerada es para 10 personas", 17, "#555")
add(f'<rect x="{W/2-200}" y="138" width="400" height="86" rx="10" fill="#2B2B2B"/>')
text(W / 2, 192, "ESCENARIO", 30, "#fff", 800, extra='letter-spacing="6"')

y = 252
block_boxes = {}
for b in BLOCKS:
    n_rows = len(b["layout"])
    bh = 66 + n_rows * ROW_PITCH
    bx = X0 - 26
    add(f'<rect x="{bx:.1f}" y="{y}" width="{BLOCK_W + 52:.1f}" height="{bh}" rx="10" '
        f'fill="{b["c_bg"]}" stroke="{b["c_main"]}" stroke-width="2"/>')
    text(W / 2, y + 36, f'{b["key"]} · {b["price"]}', 26, b["c_dark"], 800)
    block_boxes[b["key"]] = (y, bh)
    num = 0
    for r, cols in enumerate(b["layout"]):
        cy = y + 66 + r * ROW_PITCH + ROW_PITCH / 2 - 6
        for c in cols:
            cx = col_x(c)
            num += 1
            reserved = (r, c) in b["reserved"]
            if reserved:
                draw_reserved(cx, cy, num)
            else:
                draw_table(cx, cy, b, num)
            for s in range(1, 11):
                rows_csv.append([b["key"], b["price"], num, s,
                                 f'{b["key"]}-M{num:03d}-S{s:02d}',
                                 "Reservada" if reserved else "Disponible"])
        if b["key"] == "VIP" and r == 0:
            fx = col_x(11) - 22
            fw = col_x(12) + 22 - fx
            add(f'<rect x="{fx:.1f}" y="{cy-31:.1f}" width="{fw:.1f}" height="62" rx="6" '
                f'fill="#F1EFEA" stroke="#9A9A9A" stroke-width="1.2"/>')
            text(fx + fw / 2, cy + 6, "FOH", 16, "#555", 700)
    b["available"] = num - len(b["reserved"])
    y += bh + 20

# laterales (sin cambios)
vip_y, vip_h = block_boxes["VIP"]
side_h, side_w = 420, 104
side_y = vip_y + vip_h / 2 - side_h / 2
for sx, label, price, color in [
        (X0 - 26 - 50 - side_w, "PREFERENCIA NORTE", "Q440 · Aforo: 500 personas", "#1E9E73"),
        (X0 + BLOCK_W + 26 + 50, "GENERAL GRADERÍO", "Q220", "#B8741A")]:
    add(f'<rect x="{sx:.1f}" y="{side_y:.1f}" width="{side_w}" height="{side_h}" rx="10" fill="{color}"/>')
    ccx, ccy = sx + side_w / 2, side_y + side_h / 2
    text(ccx - 10, ccy, label, 22, "#fff", 800,
         extra=f'transform="rotate(-90 {ccx-10:.1f} {ccy:.1f})" letter-spacing="1"')
    text(ccx + 22, ccy, price, 19 if "Aforo" not in price else 17, "#fff", 500,
         extra=f'transform="rotate(-90 {ccx+22:.1f} {ccy:.1f})"')

# preferencia y general (sin cambios)
bx, bw = X0 - 26, BLOCK_W + 52
add(f'<rect x="{bx:.1f}" y="{y}" width="{bw:.1f}" height="120" rx="10" fill="#1E9E73"/>')
text(W / 2, y + 56, "PREFERENCIA", 32, "#fff", 800)
text(W / 2, y + 92, "Q440 · Aforo: 1,000 personas", 22, "#fff", 500)
y += 140
add(f'<rect x="{bx:.1f}" y="{y}" width="{bw:.1f}" height="170" rx="10" fill="#B8741A"/>')
text(W / 2, y + 80, "GENERAL", 36, "#fff", 800)
text(W / 2, y + 120, "Q220 · Aforo: 2,100 personas", 24, "#fff", 500)
y += 170
H = int(y + 50)  # alto de página ajustado al contenido

svg_doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" font-family="{FONT}">' + "\n".join(svg) + "</svg>")
(OUT / "mapa_localidades.svg").write_text(svg_doc, encoding="utf-8")
(OUT / "mapa_localidades.html").write_text(
    "<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Mapa de localidades</title>"
    f"<style>@page{{size:{W}px {H}px;margin:0}}html,body{{margin:0;background:#fff}}"
    f"svg{{display:block;width:{W}px;height:{H}px}}</style></head><body>" + svg_doc + "</body></html>",
    encoding="utf-8")

# inventario
with open(OUT / "inventario_sillas.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Localidad", "Precio", "Mesa", "Silla", "Codigo", "Estado"])
    w.writerows(rows_csv)

for b in BLOCKS:
    print(b["key"], "total", b["total"], "reservadas", len(b["reserved"]),
          "disponibles", b["available"], "sillas", b["available"] * 10)
print("filas CSV", len(rows_csv))
