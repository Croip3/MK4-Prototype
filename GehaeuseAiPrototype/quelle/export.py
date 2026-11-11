"""Export: STEP (CAD, Einbaulage), 3MF (druckfertig, Mehrteil-Objekte), STL (Fallback, je Koerper)."""
import os
import sys
import ctypes
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mk4_gehaeuse as GH  # noqa: E402
from build123d import *  # noqa: E402,F401
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
import lib3mf  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
PCB_STEP = os.path.join(HERE, "pcb.step")
for d in ("STEP", "3MF", "STL"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
T0 = time.time()

C = {
    "dunkel": (0.20, 0.22, 0.25),
    "orange": (0.88, 0.42, 0.10),
    "klar": (0.80, 0.93, 1.00),
    "weiss": (0.97, 0.97, 0.97),
    "schwarz": (0.06, 0.06, 0.06),
}


def to_print(shape, kind):
    if kind in ("base", "door"):
        s = Pos(0, 0, -GH.Z_BOT) * shape
    elif kind == "hood":
        s = Pos(0, 0, GH.Z_TOP) * (Rot(180, 0, 0) * shape)
    elif kind == "panel":
        s = Pos(0, 0, GH.Z_FLANK) * (Rot(180, 0, 0) * shape)
    return s


def mesh_of(shape, tol=0.015, ang=0.15):
    v, t = shape.tessellate(tol, ang)
    V = np.array([[p.X, p.Y, p.Z] for p in v], dtype=np.float64)
    F = np.array(t, dtype=np.int64)
    return trimesh.Trimesh(V, F, process=True)


def write_3mf(path, objects):
    w = lib3mf.get_wrapper()
    model = w.CreateModel()
    model.SetUnit(lib3mf.ModelUnit.MilliMeter)
    for oname, parts, offset in objects:
        comp = model.AddComponentsObject()
        comp.SetName(oname)
        for pname, m, rgb in parts:
            mo = model.AddMeshObject()
            mo.SetName(pname)
            verts = [lib3mf.Position((ctypes.c_float * 3)(*[float(c) for c in p])) for p in m.vertices]
            tris = [lib3mf.Triangle((ctypes.c_uint32 * 3)(*[int(i) for i in f])) for f in m.faces]
            mo.SetGeometry(verts, tris)
            cg = model.AddColorGroup()
            cid = cg.AddColor(w.FloatRGBAToColor(rgb[0], rgb[1], rgb[2], 1.0))
            mo.SetObjectLevelProperty(cg.GetResourceID(), cid)
            comp.AddComponent(mo, w.GetIdentityTransform())
        model.AddBuildItem(comp, w.GetTranslationTransform(*offset))
    writer = model.QueryWriter("3mf")
    writer.WriteToFile(path)


def labeled(shape, label, rgb):
    shape.label = label
    shape.color = Color(*rgb)
    return shape


def main():
    base = GH.make_base()
    hood = GH.make_hood()
    pl = GH.make_panel(-1)
    pr = GH.make_panel(+1)
    door = GH.make_door()
    print(f"[{time.time() - T0:6.1f}s] Teile gebaut", flush=True)

    # name, kind, [(teilname, shape, farbe)]
    parts = [
        ("01_Unterteil", "base", [("Unterteil", base, C["dunkel"])]),
        ("02_Haube", "hood", [("Haube_Koerper", hood["Haube"], C["orange"]),
                              ("Haube_Lichtleiter_transparent", hood["Lichtleiter"], C["klar"]),
                              ("Haube_Beschriftung_Kontrastfarbe", hood["Beschriftung"], C["schwarz"])]),
        ("03_Seitenpaneel_L_Kanal_1-8", "panel", [("PaneelL_Koerper", pl["Paneel"], C["dunkel"]),
                                                  ("PaneelL_Lichtleiter_transparent", pl["Lichtleiter"], C["klar"]),
                                                  ("PaneelL_Ziffern_transparent", pl["Ziffern"], C["weiss"])]),
        ("04_Seitenpaneel_R_Kanal_9-16", "panel", [("PaneelR_Koerper", pr["Paneel"], C["dunkel"]),
                                                   ("PaneelR_Lichtleiter_transparent", pr["Lichtleiter"], C["klar"]),
                                                   ("PaneelR_Ziffern_transparent", pr["Ziffern"], C["weiss"])]),
        ("05_Batteriedeckel", "door", [("Batteriedeckel", door, C["dunkel"])]),
    ]

    # ---------------- STEP je Teil (Einbaulage) + Baugruppe
    asm_children = []
    for name, kind, bodies in parts:
        kids = [labeled(Compound(b.solids()) if len(b.solids()) > 1 else b, bn, rgb) for bn, b, rgb in bodies]
        comp = Compound(children=kids, label=name)
        export_step(comp, os.path.join(OUT, "STEP", f"MK4_{name}.step"))
        asm_children.append(Compound(children=[labeled(Compound(b.solids()) if len(b.solids()) > 1 else b, bn, rgb)
                                               for bn, b, rgb in bodies], label=name))
        print(f"[{time.time() - T0:6.1f}s] STEP {name}", flush=True)

    # Antenne (Referenz, eingeklappt) in die Baugruppe
    pz = GH.ANT_PIVOT_Z
    ant = (GH.cyl(GH.WELL_X, GH.Y_CHC, pz - 20.5, pz, 10.0) + Pos(GH.WELL_X, GH.Y_CHC, pz) * Sphere(5.0) +
           Pos(GH.WELL_X, GH.Y_CHC, pz) * Rot(0, -90, 0) * Cone(5.0, 3.9, 87.5, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    asm_children.append(labeled(ant, "Antenne_eingeklappt_Referenz", C["schwarz"]))
    asm = Compound(children=asm_children, label="MK4_Gehaeuse_Baugruppe")
    export_step(asm, os.path.join(OUT, "STEP", "MK4_Gehaeuse_Baugruppe.step"))
    print(f"[{time.time() - T0:6.1f}s] STEP Baugruppe", flush=True)
    # zusaetzlich mit Platine (aus KiCad exportiert, siehe README)
    if os.path.exists(PCB_STEP):
        pcb = import_step(PCB_STEP)
        pcb_m = Pos(-135, 110, 0) * pcb
        pcb_m.label = "MK4-Proto_Platine"
        asm2 = Compound(children=list(asm_children) + [pcb_m], label="MK4_Gehaeuse_Baugruppe_mit_Platine")
        export_step(asm2, os.path.join(OUT, "STEP", "MK4_Gehaeuse_Baugruppe_mit_Platine.step"))
        print(f"[{time.time() - T0:6.1f}s] STEP Baugruppe mit Platine", flush=True)

    # ---------------- 3MF + STL (Drucklage)
    all_objs = []
    x_cursor = 0.0
    for name, kind, bodies in parts:
        pb = [(bn, to_print(b, kind), rgb) for bn, b, rgb in bodies]
        # Teil in XY zentrieren
        bb = Compound([b for _, b, _ in pb]).bounding_box()
        cx, cy = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2
        pb = [(bn, Pos(-cx, -cy, -bb.min.Z) * b, rgb) for bn, b, rgb in pb]
        meshes = [(bn, mesh_of(b), rgb) for bn, b, rgb in pb]
        for bn, m, rgb in meshes:
            m.export(os.path.join(OUT, "STL", f"MK4_{name}__{bn}.stl"))
            print(f"      {bn:40s} watertight={m.is_watertight} tris={len(m.faces)}", flush=True)
        write_3mf(os.path.join(OUT, "3MF", f"MK4_{name}.3mf"), [(f"MK4_{name}", meshes, (0, 0, 0))])
        w = bb.max.X - bb.min.X
        all_objs.append((f"MK4_{name}", meshes, (x_cursor + w / 2, 0, 0)))
        x_cursor += w + 10
        print(f"[{time.time() - T0:6.1f}s] 3MF/STL {name}", flush=True)
    write_3mf(os.path.join(OUT, "3MF", "MK4_alle_Teile.3mf"), all_objs)
    print(f"[{time.time() - T0:6.1f}s] fertig", flush=True)


if __name__ == "__main__":
    main()
