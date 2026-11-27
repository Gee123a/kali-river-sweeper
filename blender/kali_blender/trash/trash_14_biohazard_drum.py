"""Biohazard / radioactive B3 containment drum (200 L steel drum, 0.58 m x 0.88 m): purple coated body
(DESIGN.md #A855F7) with rolling hoops and chimes, lime hazard band (#84CC16) with trefoils and a BIOHAZARD
stencil (labels.py "biohazard_drum", worn), lid with bung. Dented and crushed on one side, a lime ooze blob
leaking from the dent; lies on its side, band up, the way it floats. WasteClass.Biohazard is inferred in Unity
from the name (PF_Trash_BiohazardDrum).

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 14,
    "name": "SM_Trash_BiohazardDrum",
    "prefab": "PF_Trash_BiohazardDrum",
    "label": "Biohazard B3 drum, purple + lime (dented, leaking)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "biohazard_drum", "rows": 3},
    "palette": [
        ("#8f46d6", 0.3, 0.45),  # 0 purple coated steel (a little faded)
        ("#a3e635", 0.0, 0.9),   # 1 lime ooze, wet
        ("#3a3540", 0.6, 0.4),   # 2 dark steel lid / bung
    ],
}

SEGS = 12
LABEL_Z = (0.31, 0.57)
RINGS = [
    (0.000, 0.270, 0.270),
    (0.015, 0.290, 0.290),    # bottom chime
    (0.030, 0.283, 0.283),
    (0.290, 0.283, 0.283),
    (0.300, 0.293, 0.293),    # rolling hoop
    (0.310, 0.283, 0.283),    # hazard band
    (0.570, 0.283, 0.283),
    (0.580, 0.293, 0.293),    # rolling hoop
    (0.590, 0.283, 0.283),
    (0.850, 0.283, 0.283),
    (0.865, 0.290, 0.290),    # top chime
    (0.880, 0.270, 0.270),
    (0.872, 0.255, 0.255),    # lid, set in
]


def _key(r):
    if r == 5:
        return "label"
    return 2 if r >= 11 else 0


def build():
    geo = ts.Geo()
    ts.lathe(geo, RINGS, SEGS, _key, uv=ts.wrap_uv(*LABEL_Z), cap0=0, cap1=2)
    geo.xform = Matrix.Translation((0.12, 0.08, 0.872))
    ts.lathe(geo, [(0.0, 0.03, 0.03), (0.015, 0.025, 0.025)], 6, lambda r: 2, cap1=2)     # bung
    geo.xform = Matrix.Translation((0.20, -0.20, 0.70)) @ Matrix.Rotation(0.8, 4, "Z")
    ts.lathe(geo, [(0.0, 0.05, 0.03), (0.03, 0.06, 0.04), (0.06, 0.035, 0.025)], 6, lambda r: 1, cap0=1, cap1=1)  # ooze
    geo.xform = None
    ts.dent(geo, (0.22, -0.20, 0.72), 0.17, (-0.05, 0.04, 0.0))       # crushed shoulder, leaking
    ts.dent(geo, (-0.27, 0.05, 0.20), 0.14, (0.035, 0.0, 0.0))
    ts.crumple(geo, 0.004, 6.0, seed=14)
    ts.lay_flat(geo, (8, 0), on_side=True)
    geo.recentre()
    return geo.objects(SPEC["name"])
