# Props Editor Tools (JC)

`KaliPropPrefabBuilder.cs` (namespace `Kali.Props.EditorTools`) turns JC's FBX meshes into prefabs and builds the shared atlas materials. Run these from the Unity menu bar. All logs use the `[KALI JC]` prefix.

| Menu item | What it does |
| :--- | :--- |
| `KALI > JC > Build Atlas Materials` | Sets texture import settings for `T_Trash_Atlas_*` and `T_Tools_Atlas_*` (Albedo sRGB, Normal as NormalMap, Mask linear, Point filter, max 2048). Creates or updates `M_Trash_Atlas.mat` and `M_Tools_Atlas.mat` (URP Lit). |
| `KALI > JC > Build Trash Prefabs` | Runs Build Atlas Materials, then builds `Trash/Meshes/SM_Trash_<Variant>.fbx` into `Trash/Prefabs/PF_Trash_<Variant>.prefab` (MeshCollider convex, Rigidbody mass 0.5 / drag 1 / angular drag 1, `RiverFlowBuoyancy` if present, `M_Trash_Atlas`). |
| `KALI > JC > Build Tool Prefabs` | Runs Build Atlas Materials, then builds `Tools/Meshes/SM_Tool_<Name>.fbx` into `Tools/Prefabs/PF_Tool_<Name>.prefab` (BoxCollider fitted to the mesh, no Rigidbody, `M_Tools_Atlas`, root transform left as imported). |
| `KALI > JC > Build All JC Prefabs` | Runs Build Atlas Materials, Trash prefabs, Tool prefabs in that order and logs a summary. |

Notes:
- Missing folders are created automatically. Missing textures or FBX files are logged as warnings and skipped.
- Prefabs are saved with `PrefabUtility.SaveAsPrefabAsset`, so re-running overwrites them.
- Trash prefab names must match the `MapJsonImporter.cs` contract: `Assets/_Project/Props/Trash/Prefabs/PF_Trash_<Variant>.prefab`.
- Convex MeshCollider meshes should stay at or under 255 triangles (trash budget is 150-400 tris, so keep trash props low-poly).
