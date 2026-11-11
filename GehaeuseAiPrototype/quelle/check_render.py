import os, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mk4_gehaeuse as GH
from build123d import *
G = GH
import numpy as np

MODE = sys.argv[1] if len(sys.argv) > 1 else "all"


def load_pcb():
    c = import_step(os.path.join(HERE, "pcb.step"))
    parts = []
    for k in c.children:
        s = Pos(-135, 110, 0) * k
        parts.append((k.label, s))
    return parts


def bb_overlap(a, b, tol=0.05):
    A, B = a.bounding_box(), b.bounding_box()
    return (A.min.X - tol < B.max.X and B.min.X - tol < A.max.X and A.min.Y - tol < B.max.Y and
            B.min.Y - tol < A.max.Y and A.min.Z - tol < B.max.Z and B.min.Z - tol < A.max.Z)


from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp


def common(a, b):
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    op.Build()
    return Compound(op.Shape())


def inter_vol(a, b):
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    op.Build()
    if not op.IsDone():
        return -1
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(op.Shape(), props)
    return props.Mass()


def extras():
    """Platzhalter: Batterie, Schalter, Antenne, USB-Stecker."""
    ex = {}
    bx0, bx1, by0, by1 = G.BAT_IN
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    top = G.BAT_CEIL[0] - 0.5
    ex["Batterie"] = G.box(cx - 24.25, cx + 24.25, cy - 13.25, cy + 13.25, top - 17.5, top)
    sw = []
    for sx in (-1, 1):
        body = G.box(sx * G.SW_X - 4.9, sx * G.SW_X + 4.9, G.YF_O + G.SW_POCKET_D + G.SW_PANEL_T,
                     G.YF_O + G.SW_POCKET_D + G.SW_PANEL_T + 20, G.SW_Z - 4.9, G.SW_Z + 4.9)
        bez = G.box(sx * G.SW_X - 6.5, sx * G.SW_X + 6.5, G.YF_O + G.SW_POCKET_D - 2.0, G.YF_O + G.SW_POCKET_D,
                    G.SW_Z - 6.5, G.SW_Z + 6.5)
        sw.append(body + bez)
    ex["Schalter"] = sw[0] + sw[1]
    # Antenne eingeklappt: Huelse senkrecht im Schacht, Peitsche waagerecht in der Rinne
    pz = G.ANT_PIVOT_Z
    sleeve = G.cyl(G.WELL_X, G.Y_CHC, pz - 20.5, pz, 10.0)
    knuckle = Pos(G.WELL_X, G.Y_CHC, pz) * Sphere(5.0)
    whip = Pos(G.WELL_X, G.Y_CHC, pz) * Rot(0, -90, 0) * Cone(5.0, 3.9, 82.5 + 5,
                                                             align=(Align.CENTER, Align.CENTER, Align.MIN))
    ex["Antenne"] = sleeve + knuckle + whip
    # Buchse (RP-SMA Einbau) unter dem Blech
    ex["Buchse"] = G.cyl(G.WELL_X, G.Y_CHC, G.PANEL_TOP_Z - 2.5 - 1.5 - 6.0, G.PANEL_TOP_Z + 9.0, 6.3)
    return ex


def tess(shape, tol=0.05):
    import pyvista as pv
    v, t = shape.tessellate(tol, 0.3)
    v = np.array([[p.X, p.Y, p.Z] for p in v])
    f = np.hstack([[3, *tri] for tri in t]).astype(np.int64)
    return pv.PolyData(v, f)


if __name__ == "__main__":
    t0 = time.time()
    base = G.make_base()
    hood = G.make_hood()
    pl = G.make_panel(-1)
    pr = G.make_panel(+1)
    door = G.make_door()
    enc = {"Unterteil": base, "Haube": hood["Haube"], "Haube-Lichtleiter": hood["Lichtleiter"],
           "Haube-Beschriftung": hood["Beschriftung"],
           "PaneelL": pl["Paneel"], "PaneelL-Lichtleiter": pl["Lichtleiter"], "PaneelL-Ziffern": pl["Ziffern"],
           "PaneelR": pr["Paneel"], "PaneelR-Lichtleiter": pr["Lichtleiter"], "PaneelR-Ziffern": pr["Ziffern"],
           "Deckel": door}
    ex = extras()
    print("built", time.time() - t0)
    if MODE in ("all", "check"):
        pcb = load_pcb()
        print("PCB parts", len(pcb), time.time() - t0)
        # 1) Gehaeuse vs Platine/Bauteile
        hits = []
        for en, e in enc.items():
            for (lab, p) in pcb:
                if not bb_overlap(e, p):
                    continue
                v = inter_vol(e, p)
                if v != 0 and abs(v) > 1e-4:
                    hits.append((en, lab, round(v, 4), p.bounding_box()))
        print("== Kollisionen Gehaeuse <-> Platine ==")
        for h in hits:
            bb = h[3]
            print(f"  {h[0]:22s} {h[1][:40]:40s} {h[2]:9.4f} mm3  @ x[{bb.min.X:.1f},{bb.max.X:.1f}] y[{bb.min.Y:.1f},{bb.max.Y:.1f}] z[{bb.min.Z:.1f},{bb.max.Z:.1f}]")
        # 2) Teile untereinander
        print("== Kollisionen Teile untereinander ==")
        names = list(enc.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = enc[names[i]], enc[names[j]]
                if not bb_overlap(a, b, 0.0):
                    continue
                v = inter_vol(a, b)
                if abs(v) > 1e-3:
                    print(f"  {names[i]:22s} x {names[j]:22s} {v:9.4f} mm3")
        # 3) Platzhalter
        print("== Platzhalter ==")
        for xn, x in ex.items():
            for en, e in enc.items():
                if not bb_overlap(e, x, 0.0):
                    continue
                v = inter_vol(e, x)
                if abs(v) > 1e-3:
                    print(f"  {xn:12s} x {en:22s} {v:9.4f} mm3")
            for (lab, p) in pcb:
                if bb_overlap(x, p, 0.0):
                    v = inter_vol(x, p)
                    if abs(v) > 1e-3:
                        print(f"  {xn:12s} x PCB {lab[:40]:40s} {v:9.4f} mm3")
        print("check done", time.time() - t0)
