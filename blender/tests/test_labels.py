"""Self-check for the procedural labels and their atlas regions (no build outputs needed):
    blender -b --factory-startup -P blender/tests/test_labels.py      # prints ALL LABEL TESTS PASSED
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402,F401
import numpy as np  # noqa: E402
from kali_blender import labels, tools_common as tc, trash_shapes as ts  # noqa: E402

# every label region sits inside its cell, below the swatch row it leaves free, and is 3 swatch rows tall
for index in range(1, tc.ATLAS_COLS * tc.ATLAS_ROWS + 1):
    u0, v0, u1, v1 = tc.cell_rect(index)
    x0, y0, x1, y1 = tc.label_box(index, 3)
    n = tc.ATLAS_SIZE
    assert u0 * n <= x0 < x1 <= u1 * n and v0 * n <= y0 < y1 <= v1 * n, index
    assert y1 <= tc.swatch_rect(index, 0, margin=False)[1] * n + 1e-6, index
    assert y1 - y0 == 3 * tc.ATLAS_SIZE // (tc.ATLAS_ROWS * tc.SWATCH_GRID), index

# every brand renders clean and dirty at the atlas size, in range, and the wear actually changes it
for name in labels.ARTS:
    clean = labels.render_label(name, 409, 384, dirty=False)
    dirty = labels.render_label(name, 409, 384, dirty=True)
    for out in (clean, dirty):
        assert out["albedo"].shape == (384, 409, 3) and out["normal"].shape == (384, 409, 3), name
        assert out["albedo"].min() >= 0 and out["albedo"].max() <= 1, name
    assert np.abs(clean["albedo"] - dirty["albedo"]).mean() > 0.01, name
assert not bpy.data.fonts or all(f.name == "Bfont Regular" for f in bpy.data.fonts), "system fonts left behind"

# bottle band UVs: a face straddling no seam keeps s inside one panel; the seam corners land on 0 / 1
wrap = ts.wrap_uv(0.0, 1.0)
step = 2 * math.pi / 12
for k in range(12):
    a0, a1 = k * step, (k + 1) * step
    s0, s1 = wrap((a0 + a1) / 2, a0, 0.5)[0], wrap((a0 + a1) / 2, a1, 0.5)[0]
    assert 0 <= s0 < s1 <= 1 and abs((s1 - s0) - 1 / 6) < 1e-9, (k, s0, s1)

# welding: coincident points share one vertex, so deformations keep seams closed
geo = ts.Geo()
assert geo.vert((0, 0, 0)) == geo.vert((0, 0, 1e-9)) != geo.vert((0, 0, 0.001))
print("ALL LABEL TESTS PASSED")
