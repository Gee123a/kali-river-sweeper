# Props & Rigging Editor Tools (JC)

`KaliPropPrefabBuilder.cs` (namespace `Kali.Props.EditorTools`) turns JC's FBX meshes into prefabs, configures URP materials, and builds amphibious excavator rigs. Run these from the Unity menu bar. All logs use the `[KALI JC]` prefix.

| Menu item | What it does |
| :--- | :--- |
| `KALI > JC > Build Atlas Materials` | Sets texture import settings for `T_Trash_Atlas_*` and `T_Tools_Atlas_*` (Albedo sRGB, Normal as NormalMap, Mask linear, Point filter, mipmaps off, max 2048). Creates or updates `M_Trash_Atlas.mat` and `M_Tools_Atlas.mat` (URP Lit). |
| `KALI > JC > Build Trash Prefabs` | Runs Build Atlas Materials, then builds `Trash/Meshes/SM_Trash_<Variant>.fbx` into `Trash/Prefabs/PF_Trash_<Variant>.prefab` (BoxCollider fitted to the mesh bounds, kinematic Rigidbody mass 0.5 / drag 1 / angular drag 1, `RiverFlowBuoyancy`, `RiverTrashItem` with reflection-assigned `wasteClass`, and `M_Trash_Atlas`). |
| `KALI > JC > Build Tool Prefabs` | Runs Build Atlas Materials, then builds `Tools/Meshes/SM_Tool_<Name>.fbx` into `Tools/Prefabs/PF_Tool_<Name>.prefab` (BoxCollider fitted to the mesh with `isTrigger = true` so equipped tools never block CharacterController or scoop raycasts, `M_Tools_Atlas`, root transform left as imported). |
| `KALI > JC > Build Excavator Prefab` | Builds URP Lit materials (`M_Excavator_Body.mat`, `M_Hydraulic_Steel.mat`, `M_Pontoon_Rubber.mat`) with exact color and smoothness specs, unpacks `SK_ExcavatorAmfibi.fbx`, remaps renderer slots, fits a `BoxCollider`, and saves `PF_ExcavatorAmfibi.prefab`. |
| `KALI > JC > Build All JC Prefabs` | Runs Build Atlas Materials, Trash prefabs, Tool prefabs, and Excavator prefab in sequence and logs an exhaustive summary. |

Notes:
- Missing folders are created automatically. Missing textures or FBX files are logged as warnings and skipped.
- Prefabs are saved with `PrefabUtility.SaveAsPrefabAsset`, so re-running overwrites them.
- Trash prefab names must match the `MapJsonImporter.cs` contract: `Assets/_Project/Props/Trash/Prefabs/PF_Trash_<Variant>.prefab`.
- Trash uses a fitted BoxCollider instead of a convex MeshCollider, because convex meshes over 255 polygons fail PhysX cooking.
- Tools have `box.isTrigger = true` to allow smooth interaction when equipped or collected.
