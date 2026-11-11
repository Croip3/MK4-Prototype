"""MK4 Zuendanlage - 3D-druckbares Gehaeuse (build123d)

Koordinatensystem (alle Masse in mm):
  X = KiCad_x - 135        (Platinenmitte = 0, rechts = +X)
  Y = 110 - KiCad_y        (vorne/Bedienseite = -Y, hinten/Antenne = +Y)
  Z = 0 an der Platinen-UNTERseite, Platinen-Oberseite = 1.6

Teile:
  Unterteil   - Wanne: Batteriefach, Schalter vorne, USB-C, Antennen-Rueckenleiste
  Haube       - erhoehter Mittelteil ueber den Elkos, Status-Lichtleiter
  Paneel L/R  - Seitenpaneele buendig mit den Klemmen, Kanal-Lichtleiter + Nummern
  Batteriedeckel
"""
import os
import sys
import math
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build123d import *          # noqa: E402,F401
from glyphs import text_face     # noqa: E402

T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


# =============================================================== PARAMETER
PCB_TOP = 1.6
CAV = 50.5                 # Innenmass: halbe Breite / Front-Innenflaeche (0.5 Luft zur Platine)
WALL = 2.6
OUT = CAV + WALL           # 53.1 Aussenmass halbe Breite
YF_O, YF_I = -OUT, -CAV    # Front aussen / innen
Y_SPF = 52.5               # Vorderflaeche Rueckenleiste (dahinter 2.5 mm Kabelschacht zur Platine)
SP_FW, CH_W, SP_BW = 2.4, 13.0, 2.4
Y_CH0 = Y_SPF + SP_FW      # 54.9  Antennenrinne vorne
Y_CH1 = Y_CH0 + CH_W       # 67.9  Antennenrinne hinten
Y_BK = Y_CH1 + SP_BW       # 70.3  Rueckseite aussen
Y_CHC = (Y_CH0 + Y_CH1) / 2

Z_BOT = -27.5              # Gehaeuseboden aussen
FLOOR = 3.0
Z_FLOOR = Z_BOT + FLOOR
CONN_TOP = 10.8            # Oberkante CamdenBoss CTB932VE/2 (gemessen aus KiCad-3D)
CONN_PROTRUDE = 0.0        # 0 = buendig, 1.0 = Klemmen stehen 1 mm ueber
PANEL_T = 2.4
Z_FLANK = CONN_TOP - CONN_PROTRUDE
Z_RIM = Z_FLANK - PANEL_T  # Oberkante Wanne / Unterseite Seitenpaneele
Z_PLAT_U = 15.2            # Unterseite Haube (Elko-Oberkante 14.2 + 1.0)
Z_TOP = 17.6               # Oberseite Haube + Rueckenleiste (Stapelebene)

# Haube / Stufe
SX1, SX2 = 27.7, 32.85     # Stufenkante hinten / vorne (Ausweichen um C104)
JY0 = -29.0
JY1 = JY0 - (SX2 - SX1)
STEP_T = 2.4
FL_W, FL_T = 2.0, 1.6      # Flansch unter den Paneelen
Y_HB = Y_SPF - 0.2         # Hinterkante Haube / Paneele

# LEDs (WS2812B 5050, Oberkante 3.2)
Z_PIPE0 = 3.5
LED_X = 32.5
LED_Y = [38.5 - 9 * i for i in range(8)]
WIN_X0, WIN_X1 = 31.2, 41.0  # Fensterbereich (Betrag X)
WIN_H = 7.6
STAT_LED = [(-4.5, 6.8), (4.5, 6.8)]
STAT_LENS = [(-8.0, 6.8), (8.0, 6.8)]

# Schrauben / Gewindeeinsaetze
INS_D, INS_DEPTH = 4.0, 6.5      # M3 Einschmelzmutter (z.B. Ruthex M3x5.7)
SCREW_D = 3.4
CB_D, CB_H = 6.0, 3.2            # Senkung Zylinderkopf
CORNER = 46.5                    # Montageloecher Platine

# Schalter vorne
SW_HOLE = 10.2
SW_X = 18.0
SW_Z = -14.0
SW_POCKET, SW_POCKET_D = 16.5, 3.0
SW_PANEL_T = 1.8                 # Wandstaerke am Schalter (Schnapphaken!)

# USB-C (J201)
USB_X, USB_Z = -4.0, 3.2
USB_W, USB_H = 13.0, 7.5

# Laschen vorne (Haube verschrauben)
LUG_X = 28.5
LUG_D = 4.6

# Antenne (2.4 GHz Knickantenne, 108 mm, Gelenk ca. 25 mm ueber Steckerende)
WELL_X = 41.0
WELL_D = 13.0
CH_Z0 = 3.0                      # Boden Antennenrinne
CH_X0, CH_X1 = -48.5, 48.3
ANT_PIVOT_Z = 10.6               # Gelenkachse
PANEL_TOP_Z = ANT_PIVOT_Z - 23.5 # Oberseite Buchsen-Blech im Schacht
SNAP_X = -35.0

# Batterie 9 V (48.5 x 26.5 x 17.5)
BAT_IN = (-25.25, 25.25, 11.5, 39.5)
BAT_T = 1.6
BAT_CEIL = (-1.6, -0.3)
DOOR = (-32.0, 32.0, 9.4, 41.6)
DOOR_T = 2.4
DOOR_SCREW = [(-29.2, 25.5), (29.2, 25.5)]

COL = {
    "Unterteil": (0.22, 0.24, 0.27),
    "Haube": (0.85, 0.42, 0.10),
    "Paneel": (0.22, 0.24, 0.27),
    "Lichtleiter": (0.85, 0.95, 1.0),
    "Ziffern": (0.95, 0.98, 1.0),
    "Beschriftung": (0.95, 0.95, 0.95),
    "Deckel": (0.22, 0.24, 0.27),
}


# =============================================================== HELFER
def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def poly(pts):
    """Polygon immer gegen den Uhrzeigersinn -> Normale = +Ebenen-Normale (Extrusionsrichtung eindeutig)."""
    pts = list(pts)
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if a < 0:
        pts = pts[::-1]
    return Polygon(*pts, align=None)


def prism(pts_or_face, z0, z1):
    f = poly(pts_or_face) if isinstance(pts_or_face, (list, tuple)) else pts_or_face
    return Pos(0, 0, z0) * extrude(f, z1 - z0)


def yz_prism(pts, x0, x1):
    return Pos(x0, 0, 0) * extrude(Plane.YZ * poly(pts), x1 - x0)


def xz_prism(pts, y0, y1):
    return Pos(0, y1, 0) * extrude(Plane.XZ * poly(pts), y1 - y0)


def cyl(x, y, z0, z1, d):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def cone(x, y, z0, z1, d0, d1):
    return Pos(x, y, z0) * Cone(d0 / 2, d1 / 2, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def oct_pts(x0, x1, y0, y1, c):
    """Rechteck mit 45-Grad-Ecken (c = Fase), Start unten links, gegen Uhrzeiger."""
    if isinstance(c, (int, float)):
        c = (c, c, c, c)  # ul, ur, or, ol  (unten-links, unten-rechts, oben-rechts, oben-links)
    pts = []
    pts += [(x0 + c[0], y0), (x1 - c[1], y0)]
    pts += [(x1, y0 + c[1]), (x1, y1 - c[2])]
    pts += [(x1 - c[2], y1), (x0 + c[3], y1)]
    pts += [(x0, y1 - c[3]), (x0, y0 + c[0])]
    return pts


def oct_face(cx, cy, w, h, c):
    return poly(oct_pts(cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2, c))


def fuse_all(items):
    items = [i for i in items if i is not None]
    s = items[0]
    if len(items) > 1:
        s = s.fuse(*items[1:]).clean()
    return s


def cut_all(base, items):
    items = [i for i in items if i is not None]
    if not items:
        return base
    tool = items[0] if len(items) == 1 else items[0].fuse(*items[1:])
    return base.cut(tool).clean()


def text_on_xy(s, cx, cy, z0, z1, H, W, w, gap=0.6, rot=0):
    f, _ = text_face(s, H=H, W=W, w=w, gap=gap)
    f = Rot(0, 0, rot) * f
    return Pos(cx, cy, z0) * extrude(f, z1 - z0)


def text_on_front(s, cx, cz, depth, H, W, w, gap=0.6):
    """Text auf der Vorderseite (Normale -Y), 'depth' in die Wand hinein."""
    f, _ = text_face(s, H=H, W=W, w=w, gap=gap)
    f = Pos(cx, cz) * f
    return Pos(0, YF_O + depth, 0) * extrude(Plane.XZ * f, depth + 1.0)


def text_on_back(s, cx, cz, depth, H, W, w, gap=0.6):
    """Text auf der Rueckseite (Normale +Y), lesbar von hinten."""
    f, _ = text_face(s, H=H, W=W, w=w, gap=gap)
    f = Pos(-cx, cz) * f
    pl = Plane(origin=(0, Y_BK - depth, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
    return extrude(pl * f, depth + 1.0)


def text_on_side(s, cy, cz, depth, H, W, w, side=+1, gap=0.6):
    """Text auf einer Seitenflaeche (side=+1 rechts, -1 links), lesbar von aussen."""
    f, _ = text_face(s, H=H, W=W, w=w, gap=gap)
    if side > 0:
        pl = Plane(origin=(OUT - depth, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        f = Pos(cy, cz) * f
    else:
        pl = Plane(origin=(-OUT + depth, 0, 0), x_dir=(0, -1, 0), z_dir=(-1, 0, 0))
        f = Pos(-cy, cz) * f
    return extrude(pl * f, depth + 1.0)


# Stufenkontur der Haube (Draufsicht)
def hood_outline(grow=0.0, y0=YF_O, y1=Y_HB):
    d = grow
    k = d * math.tan(math.radians(22.5))
    return [(-SX1 - d, y1), (SX1 + d, y1), (SX1 + d, JY0 + k), (SX2 + d, JY1 + k), (SX2 + d, y0),
            (-SX2 - d, y0), (-SX2 - d, JY1 + k), (-SX1 - d, JY0 + k)]


# =============================================================== UNTERTEIL
def make_base():
    log("Unterteil ...")
    # --- Aussenform: Draufsicht ∩ Seitenansicht ∩ Vorderansicht
    plan = oct_pts(-OUT, OUT, YF_O, Y_BK, (2.5, 2.5, 8.0, 8.0))
    side = [(YF_O, Z_BOT + 1.2), (YF_O + 1.2, Z_BOT), (Y_BK - 1.2, Z_BOT), (Y_BK, Z_BOT + 1.2),
            (Y_BK, Z_TOP - 3.0), (Y_BK - 3.0, Z_TOP), (Y_SPF, Z_TOP), (Y_SPF, Z_RIM), (YF_O, Z_RIM)]
    front = [(-OUT, Z_BOT + 1.2), (-OUT + 1.2, Z_BOT), (OUT - 1.2, Z_BOT), (OUT, Z_BOT + 1.2),
             (OUT, Z_TOP - 2.0), (OUT - 2.0, Z_TOP), (-OUT + 2.0, Z_TOP), (-OUT, Z_TOP - 2.0)]
    outer = prism(plan, Z_BOT, Z_TOP) & yz_prism(side, -OUT - 1, OUT + 1) & xz_prism(front, YF_O - 1, Y_BK + 1)

    # Stapel-Leiste auf der Rueckenleiste (+1.5)
    ridge = yz_prism([(Y_SPF, Z_TOP - 0.01), (Y_CH0, Z_TOP - 0.01), (Y_CH0 - 0.5, Z_TOP + 1.5),
                      (Y_SPF + 0.5, Z_TOP + 1.5)], -40, 40)
    ridge = ridge & xz_prism([(-40, Z_TOP - 0.1), (40, Z_TOP - 0.1), (38.5, Z_TOP + 1.6), (-38.5, Z_TOP + 1.6)],
                             Y_SPF - 1, Y_CH0 + 1)
    # Laschen vorne (Haube verschrauben)
    lugs = []
    for sx in (-1, 1):
        lug = yz_prism([(YF_O + 0.6, 1.0 - LUG_D - 0.6), (YF_O + 0.6, Z_RIM), (YF_O - LUG_D, Z_RIM),
                        (YF_O - LUG_D, 1.0)], sx * LUG_X - 4.0, sx * LUG_X + 4.0)
        lug = lug & prism(oct_pts(sx * LUG_X - 4.0, sx * LUG_X + 4.0, YF_O - LUG_D, YF_O + 1, (1.2, 1.2, 0, 0)),
                          -20, 30)
        lugs.append(lug)
    body = fuse_all([outer, ridge] + lugs)

    # --- Hohlraeume
    cuts = []
    cuts.append(box(-CAV, CAV, YF_I, Y_SPF, Z_FLOOR, Z_TOP + 5))                    # Hauptraum
    cuts.append(box(-CAV, CAV, Y_CH0, Y_CH1, Z_FLOOR, CH_Z0 - 1.4))                  # Rueckenleiste innen
    cuts.append(box(CH_X0, CH_X1, Y_CH0, Y_CH1, CH_Z0, Z_TOP + 5))                  # Antennenrinne
    body = cut_all(body, cuts)

    # --- Einbauten
    adds = []
    # Eckpfosten fuer Platine (mit Einschmelzmutter von oben)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * CORNER, sy * CORNER
            yw = Y_SPF if sy > 0 else YF_I
            adds.append(cyl(cx, cy, Z_FLOOR - 0.1, 0.0, 8.0))
            adds.append(box(min(cx, sx * CAV), max(cx, sx * CAV), min(cy - 4 * sy, yw), max(cy - 4 * sy, yw),
                            Z_FLOOR - 0.1, 0.0))
            adds.append(box(min(cx - 4 * sx, sx * CAV), max(cx - 4 * sx, sx * CAV), min(cy, yw), max(cy, yw),
                            Z_FLOOR - 0.1, 0.0))
    # Auflageleisten unter den Klemmenreihen (45-Grad-Unterseite)
    led_prof_l = [(-CAV - 0.01, -5.9), (-47.6, -3.0), (-47.6, 0.0), (-CAV - 0.01, 0.0)]
    adds.append(xz_prism(led_prof_l, -42.5, 42.5))
    led_prof_r = [(CAV + 0.01, -5.9), (47.6, -3.0), (47.6, 0.0), (CAV + 0.01, 0.0)]
    adds.append(xz_prism(led_prof_r, -29.5, 42.5))
    # Batteriefach
    bx0, bx1, by0, by1 = BAT_IN
    bat_outer = box(bx0 - BAT_T, bx1 + BAT_T, by0 - BAT_T, by1 + BAT_T, Z_FLOOR - 0.1, BAT_CEIL[1])
    bat_inner = box(bx0, bx1, by0, by1, Z_FLOOR - 1, BAT_CEIL[0])
    adds.append(bat_outer.cut(bat_inner))
    for (x, y) in DOOR_SCREW:
        adds.append(cyl(x, y, Z_FLOOR - 0.1, -17.0, 7.6))
    # Schalter-Verstaerkung (innen an der Front)
    for sx in (-1, 1):
        adds.append(box(sx * SW_X - 10.5, sx * SW_X + 10.5, YF_I - 0.1, YF_O + SW_POCKET_D + SW_PANEL_T,
                        Z_FLOOR - 0.1, SW_Z + 11.5))
    # Ablage fuer Haube hinten (45-Grad-Unterseite)
    adds.append(yz_prism([(Y_SPF + 0.01, 7.6), (Y_SPF + 0.01, 11.0), (50.5, 11.0), (50.5, 9.6)], -SX1 + 0.3, SX1 - 0.3))
    # Antennenschacht: Rohr um Bohrung
    adds.append(cyl(WELL_X, Y_CHC, Z_FLOOR - 0.1, CH_Z0, WELL_D + 3.2))
    # Bodenrippen
    for sx in (-1, 1):
        adds.append(box(sx * 38 - 0.8, sx * 38 + 0.8, -44, 42, Z_FLOOR - 0.1, Z_FLOOR + 5))
    adds.append(box(-36, 36, -15.8, -14.2, Z_FLOOR - 0.1, Z_FLOOR + 5))
    body = fuse_all([body] + adds)

    # --- Durchbrueche
    cuts = []
    # Einschmelzmuttern Eckpfosten
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(sx * CORNER, sy * CORNER, -INS_DEPTH - 0.5, 0.1, INS_D))
            cuts.append(cyl(sx * CORNER, sy * CORNER, -INS_DEPTH - 4.0, -INS_DEPTH, 2.6))
    # Batteriefach: Bodenoeffnung, Deckeltasche, Muttern, Kabelschlitz, Griffmulde
    cuts.append(box(bx0, bx1, by0, by1, Z_BOT - 1, Z_FLOOR + 0.5))
    cuts.append(box(DOOR[0], DOOR[1], DOOR[2], DOOR[3], Z_BOT - 1, Z_BOT + DOOR_T))
    cuts.append(box(-6, 6, DOOR[3] - 0.1, DOOR[3] + 2.2, Z_BOT - 1, Z_BOT + 1.4))
    for (x, y) in DOOR_SCREW:
        cuts.append(cyl(x, y, Z_BOT + DOOR_T - 0.1, Z_BOT + DOOR_T + INS_DEPTH, INS_D))
    cuts.append(box(-23, -12, by0 - BAT_T - 1, by0 + 0.1, -10.0, BAT_CEIL[0]))
    # Schalter: Tasche + 10x10 Loch
    for sx in (-1, 1):
        pk = oct_pts(sx * SW_X - SW_POCKET / 2, sx * SW_X + SW_POCKET / 2, SW_Z - SW_POCKET / 2,
                     SW_Z + SW_POCKET / 2, 3.0)
        cuts.append(xz_prism(pk, YF_O - 1, YF_O + SW_POCKET_D))
        cuts.append(box(sx * SW_X - SW_HOLE / 2, sx * SW_X + SW_HOLE / 2, YF_O - 1, YF_I + 3,
                        SW_Z - SW_HOLE / 2, SW_Z + SW_HOLE / 2))
    # USB-C mit Fase
    cuts.append(box(USB_X - USB_W / 2, USB_X + USB_W / 2, YF_O - 1, YF_I + 0.5, USB_Z - USB_H / 2, USB_Z + USB_H / 2))
    usb_ch = loft([Plane.XZ.offset(-(YF_O - 0.01)) * oct_face(USB_X, USB_Z, USB_W + 2.4, USB_H + 2.4, 1.6),
                   Plane.XZ.offset(-(YF_O + 1.2)) * oct_face(USB_X, USB_Z, USB_W, USB_H, 0.4)])
    cuts.append(usb_ch)
    # Laschen: Einschmelzmutter
    for sx in (-1, 1):
        cuts.append(cyl(sx * LUG_X, YF_O - 1.0, Z_RIM - INS_DEPTH, Z_RIM + 0.1, INS_D))
    # Beschriftung vorne (gravieren)
    cuts.append(text_on_front("PWR", -SW_X, -2.6, 0.6, H=4.0, W=2.5, w=0.8, gap=0.55))
    cuts.append(text_on_front("ARM", SW_X, -2.6, 0.6, H=4.0, W=2.5, w=0.8, gap=0.55))
    # Antennenschacht: Bohrung oberhalb Blech, Hohlraum unterhalb, Buchsenloch, Kabelfenster, Ablauf
    cuts.append(cyl(WELL_X, Y_CHC, PANEL_TOP_Z, CH_Z0 + 0.5, WELL_D))
    cuts.append(cyl(WELL_X, Y_CHC, Z_FLOOR, PANEL_TOP_Z - 2.5, WELL_D))
    cuts.append(cyl(WELL_X, Y_CHC, PANEL_TOP_Z - 3.0, PANEL_TOP_Z + 0.5, 6.6))
    cuts.append(box(WELL_X - 6.5, WELL_X + 6.5, Y_SPF - 0.2, Y_CHC, Z_FLOOR + 1.0, PANEL_TOP_Z - 3.5))
    cuts.append(box(WELL_X - 1.5, WELL_X + 1.5, Y_CHC, Y_BK + 1, PANEL_TOP_Z, PANEL_TOP_Z + 2.0))
    for x in (-36, -12, 12):
        cuts.append(box(x - 1.5, x + 1.5, Y_CH1 - 0.2, Y_BK + 1, CH_Z0, CH_Z0 + 1.5))
    # Fingermulde Antennenspitze (Rueckwand der Rinne)
    cuts.append(Pos(-43.0, Y_CH1 + 1.2, Z_TOP) * Rot(90, 0, 0) * Cylinder(5.0, 6.0))
    # Stapel-Nut unten (passt auf Leiste)
    cuts.append(yz_prism([(Y_SPF - 1.0, Z_BOT - 0.01), (Y_CH0 + 1.0, Z_BOT - 0.01), (Y_CH0 + 0.4, Z_BOT + 1.9),
                          (Y_SPF - 0.4, Z_BOT + 1.9)], -41.0, 41.0))
    # Taschen fuer Gummifuesse (12 x 1 mm)
    for (x, y) in ((-44, -44), (44, -44), (-44, 40), (44, 40)):
        cuts.append(cyl(x, y, Z_BOT - 1, Z_BOT + 1.0, 12.4))
    # Seitenflaechen: vertiefte Paneele mit Lamellen
    for sx in (-1, 1):
        pts = oct_pts(-38.0, 36.0, -20.0, 1.0, (6.0, 2.0, 6.0, 2.0))
        x0 = sx * OUT
        rec = yz_prism(pts, x0 - 0.7, x0 + 0.7)
        cuts.append(rec)
    # Rueckseite: Schriftzug
    cuts.append(text_on_back("MK4", 0.0, -12.0, 0.7, H=9.0, W=5.6, w=1.4, gap=1.2))
    body = cut_all(body, cuts)

    # Lamellen in den Seitenpaneelen + Rastnasen Antenne (nach den Schnitten wieder anfuegen)
    adds = []
    for sx in (-1, 1):
        x_face = sx * (OUT - 0.7)
        for z in (-15.5, -10.0, -4.5):
            sl = yz_prism(oct_pts(-34.0, 32.0, z - 0.9, z + 0.9, 0.6), min(x_face, x_face + sx * 0.7),
                          max(x_face, x_face + sx * 0.7))
            adds.append(sl)
    for yw, sgn in ((Y_CH0, +1), (Y_CH1, -1)):
        bump = cyl(SNAP_X, yw, 12.5, Z_TOP - 0.4, 5.6) + cone(SNAP_X, yw, 9.7, 12.5, 0.01, 5.6)
        bump = bump & box(SNAP_X - 3.5, SNAP_X + 3.5, Y_CH0 - 1.2, Y_CH1 + 1.2, 9.0, Z_TOP)
        adds.append(bump)
    body = fuse_all([body] + adds)
    log("Unterteil fertig, Volumen %.1f cm3" % (body.volume / 1000))
    return body


# =============================================================== HAUBE
def make_hood():
    log("Haube ...")
    outline = hood_outline()
    inner = hood_outline(-STEP_T, y0=YF_O + STEP_T, y1=Y_HB - 4.0)
    plate = prism(outline, Z_PLAT_U, Z_TOP)
    ring = prism(outline, Z_RIM - FL_T, Z_PLAT_U + 0.01).cut(prism(inner, Z_RIM - FL_T - 1, Z_PLAT_U + 1))
    flange = prism(hood_outline(FL_W), Z_RIM - FL_T, Z_RIM).cut(prism(outline, Z_RIM - FL_T - 1, Z_RIM + 1))
    flange = flange & box(-60, 60, YF_I + 0.2, Y_HB, -50, 50)
    lugs = []
    for sx in (-1, 1):
        lug = box(sx * LUG_X - 4.0, sx * LUG_X + 4.0, YF_O - LUG_D, YF_O + 0.6, Z_RIM, Z_TOP)
        lug = lug & prism(oct_pts(sx * LUG_X - 4.0, sx * LUG_X + 4.0, YF_O - LUG_D, YF_O + 1, (1.2, 1.2, 0, 0)), 0, 30)
        lug = lug & yz_prism([(YF_O - LUG_D - 1, Z_RIM), (YF_O + 2, Z_RIM), (YF_O + 2, Z_TOP), (YF_O - LUG_D + 1.2, Z_TOP),
                              (YF_O - LUG_D, Z_TOP - 1.2)], -60, 60)
        lugs.append(lug)
    # Rippen, Pfosten, Taster-Fuehrungen, Lichtleiter-Huellen
    ribs = []
    for sx in (-1, 1):
        ribs.append(box(sx * 22 - 0.8, sx * 22 + 0.8, -33.0, Y_HB - 4.0, 11.2, Z_PLAT_U + 0.01))
        ribs.append(cyl(sx * 11.5, 33.0, PCB_TOP + 0.2, Z_PLAT_U + 0.01, 4.0))
    for y in (-2.0, 24.0):
        ribs.append(box(-SX1 + 1.0, SX1 - 1.0, y - 0.8, y + 0.8, 11.2, Z_PLAT_U + 0.01))
    taster = [(-15.15, 45.75, "RST"), (15.35, 45.75, "BOOT")]
    for (x, y, _) in taster:
        ribs.append(cyl(x, y, 7.2, Z_PLAT_U + 0.01, 5.0))
    back_rib = box(-SX1 + 0.01, SX1 - 0.01, Y_HB - 4.0, Y_HB, 11.0, Z_PLAT_U + 0.01)
    sleeves, pipes = [], []
    for (lx, ly), (cx, cy) in zip(STAT_LED, STAT_LENS):
        s0 = Pos(0, 0, Z_PIPE0) * oct_face(lx, ly, 6.0, 6.0, 0.5)
        s1 = Pos(0, 0, Z_PLAT_U) * oct_face(cx, cy, 13.6, 10.6, 3.0)
        sleeves.append(loft([s0, s1]))
        p0 = Pos(0, 0, Z_PIPE0) * oct_face(lx, ly, 4.4, 4.4, 0.3)
        p1 = Pos(0, 0, Z_PLAT_U) * oct_face(cx, cy, 12.0, 9.0, 2.4)
        pipe = loft([p0, p1]) + prism(oct_face(cx, cy, 12.0, 9.0, 2.4), Z_PLAT_U, Z_TOP)
        pipes.append(pipe)
    body = fuse_all([plate, ring, flange, back_rib] + lugs + ribs + sleeves)
    # Hinten: Seitenwaende ueber der Ablage kuerzen
    body = body.cut(box(-60, 60, Y_HB - 4.0, Y_HB + 1, Z_RIM - FL_T - 1, 11.0)).clean()
    # vorne: Ring unterhalb Z_RIM entfernen (sitzt auf Frontwand)
    body = body.cut(box(-60, 60, YF_O - 10, YF_I + 0.2, Z_RIM - 5, Z_RIM)).clean()

    cuts = []
    for (x, y, _) in taster:
        cuts.append(cyl(x, y, 6.0, Z_TOP + 1, 2.4))
        cuts.append(cone(x, y, Z_TOP - 1.0, Z_TOP + 0.01, 2.4, 4.4))
    for sx in (-1, 1):
        cuts.append(cyl(sx * LUG_X, YF_O - 1.0, Z_RIM - 1, Z_TOP + 1, SCREW_D))
        cuts.append(cyl(sx * LUG_X, YF_O - 1.0, Z_TOP - CB_H, Z_TOP + 1, CB_D))
    # Zierfuge (Panel-Linie) auf der Oberseite
    groove = prism(hood_outline(-3.0, y0=YF_O + 3.0, y1=Y_HB - 3.0), Z_TOP - 0.4, Z_TOP + 1).cut(
        prism(hood_outline(-3.6, y0=YF_O + 3.6, y1=Y_HB - 3.6), Z_TOP - 1, Z_TOP + 2))
    cuts.append(groove)
    body = cut_all(body, cuts)

    # Beschriftung als Einlage (Mehrfarbdruck)
    labels = [text_on_xy("MK4", 0.0, -42.5, Z_TOP - 0.6, Z_TOP, H=7.0, W=4.4, w=1.3, gap=1.0)]
    for (x, y, t) in taster:
        labels.append(text_on_xy(t, x, y - 4.8, Z_TOP - 0.6, Z_TOP, H=3.2, W=2.1, w=0.7, gap=0.45))
    # Warnstreifen vorne (45 Grad), links gespiegelt
    band = box(13.0, 27.5, -49.5, -44.0, Z_TOP - 0.6, Z_TOP)
    strs = []
    for k in range(-2, 6):
        xs = 13.0 + k * 3.4
        strs.append(prism([(xs, -49.5), (xs + 1.7, -49.5), (xs + 1.7 + 5.5, -44.0), (xs + 5.5, -44.0)],
                          Z_TOP - 0.6, Z_TOP))
    st = fuse_all(strs) & band
    labels += [st, mirror(st, about=Plane.YZ)]
    # HUD-Ecken um die Status-Linsen
    bx0, bx1, by0, by1, arm, wl = -17.0, 17.0, -0.6, 14.2, 3.6, 0.8
    for (cx, cy, dx, dy) in ((bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx1, by1, -1, -1), (bx0, by1, 1, -1)):
        a = box(min(cx, cx + dx * arm), max(cx, cx + dx * arm), min(cy, cy + dy * wl), max(cy, cy + dy * wl),
                Z_TOP - 0.6, Z_TOP)
        b = box(min(cx, cx + dx * wl), max(cx, cx + dx * wl), min(cy, cy + dy * arm), max(cy, cy + dy * arm),
                Z_TOP - 0.6, Z_TOP)
        labels += [a, b]
    label = fuse_all(labels)
    pipe = fuse_all(pipes)
    body = body.cut(pipe).cut(label).clean()
    log("Haube fertig")
    return {"Haube": body, "Lichtleiter": pipe, "Beschriftung": label}


# =============================================================== SEITENPANEELE
def make_panel(side=-1):
    """side=-1: links (Kanaele 1-8), +1: rechts (9-16). Gebaut fuer links, rechts gespiegelt."""
    log("Paneel", "L" if side < 0 else "R", "...")
    k = 0.2 * math.tan(math.radians(22.5))
    pts = [(-OUT, YF_O + 2.5), (-OUT + 2.5, YF_O), (-SX2 - 0.2, YF_O), (-SX2 - 0.2, JY1 + k),
           (-SX1 - 0.2, JY0 + k), (-SX1 - 0.2, Y_HB), (-OUT, Y_HB)]
    plate = prism(pts, Z_RIM, Z_FLANK)
    plate = plate & xz_prism([(-OUT - 1, Z_RIM - 1), (-OUT - 1, Z_FLANK - 1.0), (-OUT, Z_FLANK - 1.0),
                              (-OUT + 1.0, Z_FLANK), (0, Z_FLANK), (0, Z_RIM - 1)], YF_O - 1, Y_BK)
    plate = plate & yz_prism([(YF_O - 1, Z_RIM - 1), (YF_O - 1, Z_FLANK - 1.0), (YF_O, Z_FLANK - 1.0),
                              (YF_O + 1.0, Z_FLANK), (Y_BK, Z_FLANK), (Y_BK, Z_RIM - 1)], -60, 0)
    adds = []
    for sy in (-1, 1):
        adds.append(cyl(-CORNER, sy * CORNER, PCB_TOP, Z_RIM + 0.01, 7.2))
    adds.append(box(-50.3, -49.5, -42.9, 42.9, PCB_TOP, Z_RIM + 0.01))          # haelt Platinenrand
    for y in (-35.0, -43.0):
        adds.append(box(-50.3, -SX2 - FL_W - 0.3, y - 0.8, y + 0.8, 5.0, Z_RIM + 0.01))
    # Lichtleiter (je Kanal)
    pipes, legends, sleeves = [], [], []
    wx0, wx1 = -WIN_X1, -WIN_X0
    wcx = (wx0 + wx1) / 2
    ww = wx1 - wx0
    for i, ly in enumerate(LED_Y):
        if side < 0:
            num = i + 1
        else:
            num = 9 + i
        win = oct_face(wcx, ly, ww, WIN_H, 1.0)
        s0 = Pos(0, 0, Z_PIPE0) * oct_face(-LED_X, ly, 6.0, 6.0, 0.5)
        s1 = Pos(0, 0, Z_RIM) * oct_face(wcx, ly, ww + 1.6, WIN_H + 1.6, 1.4)
        sleeves.append(loft([s0, s1]))
        p0 = Pos(0, 0, Z_PIPE0) * oct_face(-LED_X, ly, 4.4, 4.4, 0.3)
        p1 = Pos(0, 0, Z_RIM) * oct_face(wcx, ly, ww, WIN_H, 1.0)
        pipe = loft([p0, p1]) + prism(win, Z_RIM, Z_FLANK - 1.0)
        pipes.append(pipe)
        ring = prism(win, Z_FLANK - 1.0, Z_FLANK) - prism(oct_face(wcx, ly, ww - 1.6, WIN_H - 1.6, 0.67),
                                                          Z_FLANK - 2, Z_FLANK + 1)
        # Ziffer: rechts wird spaeter gespiegelt -> Text vorab spiegeln, damit er richtig herum steht
        tx = text_on_xy(str(num), wcx, ly, Z_FLANK - 1.0, Z_FLANK, H=4.6, W=2.9, w=0.85, gap=0.55)
        if side > 0:
            tx = mirror(tx, about=Plane.YZ.offset(wcx))
        legends.append(ring + tx)
    body = fuse_all([plate] + adds + sleeves)
    cuts = []
    cuts.append(box(-49.25, -41.75, -28.96, 42.95, Z_RIM - 5, Z_FLANK + 1))       # Klemmen-Schlitz
    for sy in (-1, 1):
        cuts.append(cyl(-CORNER, sy * CORNER, PCB_TOP - 1, Z_FLANK + 1, SCREW_D))
        cuts.append(cyl(-CORNER, sy * CORNER, Z_FLANK - CB_H, Z_FLANK + 1, CB_D))
    body = cut_all(body, cuts)
    pipe = fuse_all(pipes)
    legend = fuse_all(legends)
    body = body.cut(pipe).cut(legend).clean()
    out = {"Paneel": body, "Lichtleiter": pipe, "Ziffern": legend}
    if side > 0:
        out = {k2: mirror(v, about=Plane.YZ) for k2, v in out.items()}
    log("Paneel fertig")
    return out


# =============================================================== BATTERIEDECKEL
def make_door():
    log("Batteriedeckel ...")
    c = 0.2
    d = box(DOOR[0] + c, DOOR[1] - c, DOOR[2] + c, DOOR[3] - c, Z_BOT, Z_BOT + DOOR_T)
    ribs = []
    rib_top = BAT_CEIL[0] - 0.5 - 17.5 - 0.3
    for x in (-15.0, 0.0, 15.0):
        ribs.append(box(x - 0.8, x + 0.8, BAT_IN[2] + 1.0, BAT_IN[3] - 1.0, Z_BOT + DOOR_T - 0.01, rib_top))
    d = fuse_all([d] + ribs)
    cuts = []
    for (x, y) in DOOR_SCREW:
        cuts.append(cyl(x, y, Z_BOT - 1, Z_BOT + DOOR_T + 1, SCREW_D))
        cuts.append(cone(x, y, Z_BOT - 0.01, Z_BOT + 1.7, 6.6, 3.2))
    # Text auf der Unterseite muss von unten lesbar sein -> gespiegelt gravieren
    cuts.append(mirror(text_on_xy("9V", 0.0, 25.5, Z_BOT - 0.01, Z_BOT + 0.5, H=7.0, W=4.2, w=1.2, gap=1.0),
                       about=Plane.YZ))
    d = cut_all(d, cuts)
    log("Batteriedeckel fertig")
    return d


def check(name, shp):
    bb = shp.bounding_box()
    sol = shp.solids()
    print(f"   {name:14s} solids={len(sol)} vol={shp.volume/1000:7.2f}cm3 valid={shp.is_valid} "
          f"bbox x[{bb.min.X:.1f},{bb.max.X:.1f}] y[{bb.min.Y:.1f},{bb.max.Y:.1f}] z[{bb.min.Z:.1f},{bb.max.Z:.1f}]")


if __name__ == "__main__":
    b = make_base()
    check("Unterteil", b)
    h = make_hood()
    for k, v in h.items():
        check(k, v)
    pl = make_panel(-1)
    for k, v in pl.items():
        check("L " + k, v)
    pr = make_panel(+1)
    for k, v in pr.items():
        check("R " + k, v)
    dr = make_door()
    check("Deckel", dr)
    log("alle Teile gebaut")
