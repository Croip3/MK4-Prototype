import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mk4_gehaeuse as GH
import render as R
import check_render as CR
from build123d import *
import pyvista as pv

OUT = os.path.join(HERE, "renders")
os.makedirs(OUT, exist_ok=True)

base, hood, pl, pr, door = R.build()
ex = CR.extras()
pcb = CR.load_pcb()

colors = []
parts = [("base", base, R.C_BODY), ("hood", hood["Haube"], R.C_HOOD), ("hpipe", hood["Lichtleiter"], R.C_PIPE),
         ("door", door, R.C_BODY)]
for s, d in (("L", pl), ("R", pr)):
    parts += [("pan" + s, d["Paneel"], "#4a515c"), ("pip" + s, d["Lichtleiter"], R.C_PIPE),
              ("leg" + s, d["Ziffern"], "#ffffff")]
parts += [("bat", ex["Batterie"], "#c9b037"), ("sw", ex["Schalter"], "#8a2be2"), ("ant", ex["Antenne"], "#111111"),
          ("buchse", ex["Buchse"], "#d4af37")]
for lab, s in pcb:
    parts.append(("pcb_" + lab, s, R.C_PCB if lab.startswith("MK4-Proto_PCB") else "#a7adb5"))


def section(name, keep_box, cam, parallel=True, zoom=1.0):
    items = []
    kb = GH.box(*keep_box)
    for (n, s, c) in parts:
        try:
            if not CR.bb_overlap(s, kb, 0):
                continue
            cut = CR.common(s, kb)
            if CR.inter_vol(s, kb) < 1e-3:
                continue
            m = R.tess(cut, 0.04, 0.3)
            items.append((m, dict(color=c)))
        except Exception as e:
            print("skip", n, e)
    p = pv.Plotter(off_screen=True, window_size=(1700, 1100), lighting="three lights")
    p.set_background("#ffffff")
    for m, kw in items:
        p.add_mesh(m, smooth_shading=False, **kw)
        fe = m.extract_feature_edges(feature_angle=35, boundary_edges=True, manifold_edges=False,
                                     non_manifold_edges=False)
        p.add_mesh(fe, color="#101215", line_width=1.0)
    p.camera_position = cam
    if parallel:
        p.enable_parallel_projection()
    p.camera.zoom(zoom)
    p.screenshot(os.path.join(OUT, name))
    p.close()
    print("wrote", name)


big = 200
# A: Schnitt durch Kanal 1/9 (Y = 38.5), Blick von vorne
section("10_schnitt_kanal1.png", (-60, 60, 38.5, 90, -40, 30), [(0, -400, -4), (0, 0, -4), (0, 0, 1)], zoom=1.55)
# B: Schnitt durch Antennenschacht (X = 41), Blick von rechts
section("11_schnitt_antenne.png", (-60, 41.0, -70, 90, -40, 30), [(400, 0, -4), (0, 5, -4), (0, 0, 1)], zoom=1.3)
# C: Schnitt Mitte (X = -4.5 durch Status-LED links), Blick von rechts
section("12_schnitt_status.png", (-60, -4.5, -70, 90, -40, 30), [(400, 0, -4), (0, 5, -4), (0, 0, 1)], zoom=1.3)
# D: Schnitt durch Schalter (X = 18), Blick von rechts
section("13_schnitt_schalter.png", (-60, 18.0, -70, 90, -40, 30), [(400, 0, -4), (0, 5, -4), (0, 0, 1)], zoom=1.3)
# E: Schnitt durch Elko C104 (Y = -40.5)
section("14_schnitt_elko.png", (-60, 60, -40.5, 90, -40, 30), [(0, -400, -4), (0, 0, -4), (0, 0, 1)], zoom=1.55)
