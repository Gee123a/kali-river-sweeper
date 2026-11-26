# Wesley — Environment mesh generators (Blender 5.3)

`SM_Env_*` meshes are generated from the same `RiverMath` formula as the C# code
(`unity/Assets/_Project/Scripts/Core/RiverFlowBuoyancy.cs`), so the visual riverbank and the
gameplay channel (`IsInRiver()`, trash drift) always match.

```
python blender/wesley_env/build_env.py          # bpy 5.3 wheel
blender -b -P blender/wesley_env/build_env.py   # Blender app, headless
```

Outputs: `unity/Assets/_Project/Environment/Meshes/SM_Env_*.fbx`, `blender/SM_Env_Pack.blend`.
FBX settings are imported from `kali_blender/export_fbx.py` (`-Z Forward`, `Y Up`, scale 1, Apply Transform).

| Mesh | Tris | Notes |
|---|---|---|
| `SM_Env_RiverValleyTerrain` | 3,240 | 130 × 180 m at origin, banks `+1.40`, bed `-2.0`, 45° talud crossing `Y = 0` exactly at `RiverHalfWidthMap`; 3 material slots (tanah / talud / lumpur); world-planar UV (1 tile = 4 m) |

`preview_terrain_map.png`: top view of the exported FBX overlaid with the 54 nodes of `kali-river-map.json`.
