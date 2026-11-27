# Props & Rigging Editor Tools (JC)

`KaliPropPrefabBuilder.cs` (namespace `Kali.Props.EditorTools`) turns JC's FBX meshes into prefabs, configures URP materials, and builds amphibious excavator rigs. Run these from the Unity menu bar. All logs use the `[KALI JC]` prefix.

| Menu item | What it does |
| :--- | :--- |
| `KALI > JC > Build Atlas Materials` | Sets texture import settings for `T_Trash_Atlas_*`, `T_Tools_Atlas_*` and `T_Products_Atlas_*` (Albedo sRGB, Normal as NormalMap, Mask linear point-filtered, max 2048; tool albedo point filter without mipmaps, trash and product albedo bilinear with mipmaps for the painted labels). Creates or updates `M_Trash_Atlas.mat`, `M_Tools_Atlas.mat`, `M_Products_Atlas.mat` and `M_Equipment_Atlas.mat` (URP Lit; the equipment one also gets its `_Emission` mask, shared with `KaliLightingBuilder`). |
| `KALI > JC > Build Trash Prefabs` | Runs Build Atlas Materials, then builds `Trash/Meshes/SM_Trash_<Variant>.fbx` into `Trash/Prefabs/PF_Trash_<Variant>.prefab` (BoxCollider fitted to the mesh bounds, kinematic Rigidbody mass 0.5 / drag 1 / angular drag 1, `RiverFlowBuoyancy`, `RiverTrashItem` with reflection-assigned `wasteClass`, and `M_Trash_Atlas`). |
| `KALI > JC > Build Tool Prefabs` | Runs Build Atlas Materials, then builds `Tools/Meshes/SM_Tool_<Name>.fbx` into `Tools/Prefabs/PF_Tool_<Name>.prefab` (BoxCollider fitted to the mesh with `isTrigger = true` so equipped tools never block CharacterController or scoop raycasts, `M_Tools_Atlas`, root transform left as imported). |
| `KALI > JC > Build Product Prefabs` | Runs Build Atlas Materials, then builds `Products/Meshes/SM_Product_<Name>.fbx` into `Products/Prefabs/PF_Product_<Name>.prefab` (clean shop / world items: solid BoxCollider fitted to the mesh, `M_Products_Atlas`, no Rigidbody, no `RiverTrashItem`). The mesh origin is the base, so a prefab placed at floor or shelf height stands on it. |
| `KALI > JC > Build Equipment Prefabs` | Runs Build Atlas Materials, then builds `Equipment/Meshes/SM_Prop_<Name>.fbx` into `Equipment/Prefabs/PF_Prop_<Name>.prefab` (trash boom, rakit, sampan, kampung bin: `M_Equipment_Atlas`, solid fitted BoxCollider, no Rigidbody / `RiverTrashItem`). The lighting meshes (`LanternWarung`, `WarningBeacon`, `BeaconRotor`) are skipped: `KALI > Lighting > Build All Lighting Assets` wraps them. Boom and boats keep their waterline origin (importer places `trash_boom` at y = 0); the bin keeps its base origin. |
| `KALI > JC > Build Excavator Prefab` | Builds URP Lit materials (`M_Excavator_Body.mat`, `M_Hydraulic_Steel.mat`, `M_Pontoon_Rubber.mat`) with exact color and smoothness specs, unpacks `SK_ExcavatorAmfibi.fbx`, remaps renderer slots, fits a `BoxCollider`, and saves `PF_ExcavatorAmfibi.prefab`. |
| `KALI > JC > Build All JC Prefabs` | Runs Build Atlas Materials, Trash prefabs, Tool prefabs, Product prefabs, Equipment prefabs, and Excavator prefab in sequence and logs an exhaustive summary. |

Notes:
- Missing folders are created automatically. Missing textures or FBX files are logged as warnings and skipped.
- Prefabs are saved with `PrefabUtility.SaveAsPrefabAsset`, so re-running overwrites them.
- Trash prefab names must match the `MapJsonImporter.cs` contract: `Assets/_Project/Props/Trash/Prefabs/PF_Trash_<Variant>.prefab`.
- Trash uses a fitted BoxCollider instead of a convex MeshCollider, because convex meshes over 255 polygons fail PhysX cooking.
- Tools have `box.isTrigger = true` to allow smooth interaction when equipped or collected.
