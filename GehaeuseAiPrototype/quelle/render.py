import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mk4_gehaeuse as GH
from build123d import *
import numpy as np
import pyvista as pv

OUTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "renders")
os.makedirs(OUTDIR, exist_ok=True)
WITH_PCB = "--pcb" in sys.argv


def tess(shape, tol=0.04, ang=0.25):
    v, t = shape.tessellate(tol, ang)
    v = np.array([[p.X, p.Y, p.Z] for p in v], dtype=float)
    f = np.hstack([[3, *tri] for tri in t]).astype(np.int64)
    m = pv.PolyData(v, f)
    return m.compute_normals(split_vertices=True, feature_angle=30)


def moved(shape, dx=0, dy=0, dz=0):
    return Pos(dx, dy, dz) * shape


C_BODY = "#3a3f47"
C_HOOD = "#d9661a"
C_PIPE = "#bfe8ff"
C_LEG = "#ffffff"
C_PCB = "#1f6b3a"


def build():
    t0 = time.time()
    base = GH.make_base()
    hood = GH.make_hood()
    pl = GH.make_panel(-1)
    pr = GH.make_panel(+1)
    door = GH.make_door()
    print("built", round(time.time() - t0, 1))
    return base, hood, pl, pr, door


def load_pcb_mesh():
    c = import_step(os.path.join(HERE, "pcb.step"))
    meshes = []
    for k in c.children:
        s = Pos(-135, 110, 0) * k
        try:
            meshes.append((k.label, tess(s, 0.08, 0.4)))
        except Exception:
            pass
    return meshes


def scene(pl_, items, cam, name, parallel=False, light=True):
    p = pv.Plotter(off_screen=True, window_size=(1600, 1150), lighting="three lights")
    p.set_background("#f4f5f7", top="#dfe3ea")
    for mesh, kw in items:
        kw = dict(kw)
        show_e = kw.pop("edges", True)
        p.add_mesh(mesh, smooth_shading=False, **kw)
        if show_e and mesh.n_points > 0:
            try:
                fe = mesh.extract_feature_edges(feature_angle=35, boundary_edges=True, manifold_edges=False,
                                                non_manifold_edges=False)
                p.add_mesh(fe, color="#101215", line_width=1.2)
            except Exception:
                pass
    p.camera_position = cam
    if parallel:
        p.enable_parallel_projection()
    p.camera.zoom(1.0)
    p.screenshot(os.path.join(OUTDIR, name))
    p.close()
    print("wrote", name)


if __name__ == "__main__":
    base, hood, pl, pr, door = build()
    M = {}
    M["base"] = tess(base)
    M["hood"] = tess(hood["Haube"])
    M["hood_pipe"] = tess(hood["Lichtleiter"])
    M["hood_lab"] = tess(hood["Beschriftung"])
    for side, d in (("L", pl), ("R", pr)):
        M["pan" + side] = tess(d["Paneel"])
        M["pip" + side] = tess(d["Lichtleiter"])
        M["leg" + side] = tess(d["Ziffern"])
    M["door"] = tess(door)
    pcb = load_pcb_mesh() if WITH_PCB else []
    print("tessellated")

    def asm(explode=0.0, show_hood=True, show_panels=True, show_door=True, pipe_op=0.85):
        items = [(M["base"], dict(color=C_BODY))]
        e = explode
        if show_door:
            items.append((M["door"].translate((0, 0, -e * 0.6), inplace=False), dict(color=C_BODY)))
        if show_hood:
            items.append((M["hood"].translate((0, 0, e * 1.6), inplace=False), dict(color=C_HOOD)))
            items.append((M["hood_pipe"].translate((0, 0, e * 1.6), inplace=False), dict(color=C_PIPE, opacity=pipe_op)))
            items.append((M["hood_lab"].translate((0, 0, e * 1.6), inplace=False), dict(color="#202020")))
        if show_panels:
            for s in ("L", "R"):
                items.append((M["pan" + s].translate((0, 0, e), inplace=False), dict(color=C_BODY)))
                items.append((M["pip" + s].translate((0, 0, e), inplace=False), dict(color=C_PIPE, opacity=pipe_op)))
                items.append((M["leg" + s].translate((0, 0, e), inplace=False), dict(color=C_LEG)))
        return items

    pcb_items = [(m.translate((0, 0, 0), inplace=False),
                  dict(color=(C_PCB if lab.startswith("MK4-Proto_PCB") else "#9aa0a8"))) for lab, m in pcb]

    iso_front = [(-190, -260, 210), (0, 0, -2), (0, 0, 1)]
    iso_back = [(190, 300, 190), (0, 5, -2), (0, 0, 1)]
    scene(None, asm(), iso_front, "01_iso_vorne.png")
    scene(None, asm(), iso_back, "02_iso_hinten.png")
    scene(None, asm(), [(0, 0, 400), (0, 8, 0), (0, 1, 0)], "03_draufsicht.png", parallel=True)
    scene(None, asm(), [(0, -400, -5), (0, 0, -5), (0, 0, 1)], "04_front.png", parallel=True)
    scene(None, asm(), [(-150, -170, -260), (0, 5, -10), (0, 0, 1)], "05_unten.png")
    ex = asm(explode=28) + pcb_items
    scene(None, ex, [(-230, -300, 240), (0, 0, 10), (0, 0, 1)], "06_explosion.png")
    if WITH_PCB:
        inner = asm(show_hood=False, show_panels=False) + pcb_items
        scene(None, inner, [(-150, -200, 220), (0, 0, 0), (0, 0, 1)], "07_innen_mit_platine.png")
