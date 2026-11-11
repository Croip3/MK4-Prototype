import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mk4_gehaeuse as GH
import render as R
import check_render as CR
from build123d import *
import pyvista as pv
import trimesh
import numpy as np

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
base, hood, pl, pr, door = R.build()
ex = CR.extras()
pcb = R.load_pcb_mesh()

M = {"base": R.tess(base), "hood": R.tess(hood["Haube"]), "hpipe": R.tess(hood["Lichtleiter"]),
     "hlab": R.tess(hood["Beschriftung"]), "door": R.tess(door), "ant": R.tess(ex["Antenne"])}
for s, d in (("L", pl), ("R", pr)):
    M["pan" + s] = R.tess(d["Paneel"]); M["pip" + s] = R.tess(d["Lichtleiter"]); M["leg" + s] = R.tess(d["Ziffern"])
pz = GH.ANT_PIVOT_Z
M["ant_up"] = R.tess(Pos(GH.WELL_X, GH.Y_CHC, pz) * Cone(5.0, 3.9, 87.5, align=(Align.CENTER, Align.CENTER, Align.MIN)))

GLOW = "#9fe3ff"


def asm(dz=0.0, explode=0.0, ant=True, glow=False):
    t = lambda m, z=0.0: m.translate((0, 0, dz + z), inplace=False)
    e = explode
    it = [(t(M["base"]), dict(color=R.C_BODY)), (t(M["door"], -0.6 * e), dict(color=R.C_BODY)),
          (t(M["hood"], 1.6 * e), dict(color=R.C_HOOD)),
          (t(M["hpipe"], 1.6 * e), dict(color=GLOW if glow else R.C_PIPE, opacity=1.0 if glow else 0.85)),
          (t(M["hlab"], 1.6 * e), dict(color="#15171a"))]
    for s in ("L", "R"):
        it += [(t(M["pan" + s], e), dict(color=R.C_BODY)),
               (t(M["pip" + s], e), dict(color=GLOW if glow else R.C_PIPE, opacity=1.0 if glow else 0.85)),
               (t(M["leg" + s], e), dict(color="#ffffff"))]
    if ant:
        it.append((t(M["ant"]), dict(color="#121212")))
    return it


def shot(items, cam, name, parallel=False, size=(1600, 1100), bg=("#f4f5f7", "#dfe3ea"), zoom=1.0):
    p = pv.Plotter(off_screen=True, window_size=size, lighting="three lights")
    p.set_background(bg[0], top=bg[1])
    for m, kw in items:
        kw = dict(kw)
        e = kw.pop("edges", True)
        p.add_mesh(m, smooth_shading=False, **kw)
        if e and m.n_points:
            p.add_mesh(m.extract_feature_edges(feature_angle=35, boundary_edges=True, manifold_edges=False,
                                               non_manifold_edges=False), color="#101215", line_width=1.1)
    p.camera_position = cam
    if parallel:
        p.enable_parallel_projection()
    p.camera.zoom(zoom)
    p.screenshot(os.path.join(OUT, name))
    p.close()
    print("wrote", name, flush=True)


pcb_items = [(m, dict(color=(R.C_PCB if lab.startswith("MK4-Proto_PCB") else "#9aa0a8"))) for lab, m in pcb]

ONLY = "--only-layout" in sys.argv
if not ONLY: shot(asm(), [(-200, -265, 205), (0, 4, -3), (0, 0, 1)], "01_ansicht_vorne.png")
if not ONLY: shot(asm() + [(M["ant_up"], dict(color="#121212", opacity=0.35, edges=False))],
     [(215, 300, 200), (0, 10, 15), (0, 0, 1)], "02_ansicht_hinten_antenne.png")
if not ONLY: shot(asm(), [(0, 0, 400), (0, 8, 0), (0, 1, 0)], "03_draufsicht.png", parallel=True, zoom=1.25)
if not ONLY: shot(asm(explode=30, ant=False) + pcb_items, [(-235, -300, 250), (0, 0, 12), (0, 0, 1)], "04_explosion_mit_platine.png")
if not ONLY: shot(asm(), [(-150, -170, -260), (0, 5, -10), (0, 0, 1)], "05_unterseite.png")
if not ONLY: shot(asm() + asm(dz=GH.Z_TOP - GH.Z_BOT), [(-260, -330, 230), (0, 4, 18), (0, 0, 1)], "06_gestapelt.png")
if not ONLY: shot(asm(glow=True), [(0, -230, 260), (0, 0, 0), (0, 0, 1)], "07_leuchtend.png",
     bg=("#1b1e24", "#2a2f38"))

# Drucklage
import export as EX
lay = []
x = 0.0
parts = [("base", [(base, R.C_BODY)]), ("hood", [(hood["Haube"], R.C_HOOD), (hood["Lichtleiter"], R.C_PIPE),
                                                 (hood["Beschriftung"], "#15171a")]),
         ("panel", [(pl["Paneel"], R.C_BODY), (pl["Lichtleiter"], R.C_PIPE), (pl["Ziffern"], "#ffffff")]),
         ("panel", [(pr["Paneel"], R.C_BODY), (pr["Lichtleiter"], R.C_PIPE), (pr["Ziffern"], "#ffffff")]),
         ("door", [(door, R.C_BODY)])]
for kind, bodies in parts:
    pb = [(EX.to_print(b, kind), c) for b, c in bodies]
    bb = Compound([b for b, _ in pb]).bounding_box()
    for b, c in pb:
        lay.append((R.tess(Pos(x - bb.min.X, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * b), dict(color=c)))
    x += (bb.max.X - bb.min.X) + 12
bed = pv.Plane(center=(x / 2 - 6, 0, -0.05), direction=(0, 0, 1), i_size=x + 20, j_size=150)
lay.append((bed, dict(color="#c8ccd2", edges=False)))
shot(lay, [(x / 2 - 6, -420, 330), (x / 2 - 6, 0, 0), (0, 0, 1)], "08_drucklage.png", size=(1800, 1000))
