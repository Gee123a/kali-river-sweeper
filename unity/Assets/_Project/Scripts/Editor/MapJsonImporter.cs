#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem.UI;
#endif
using KaliRiverSweeper.Core;
using KaliRiverSweeper.Player;

namespace KaliRiverSweeper.Editor
{
    public static class MapJsonImporter
    {
        private const string DefaultMapPath = "Assets/_Project/Data/kali-river-map.json";
        private const string MainScenePath = "Assets/_Project/Scenes/Main.unity";
        private const string MethaneBubblesPrefabPath = "Assets/_Project/VFX/VFX_MethaneSludgeBubbles.prefab";
        private const float BankTopY = 1.40f;
        private const float RiverbedTopY = -2.0f;

        [Serializable]
        private class MapData
        {
            public MapItem[] items;
        }

        [Serializable]
        private class KampungMix
        {
            public float rumah;
            public float warung_madura;
            public float warung;
        }

        [Serializable]
        private class MapItem
        {
            public string id;
            public string type;
            public string name;
            public float x;
            public float y;
            public float w;
            public float h;
            public float elev;
            public float rot;
            public string color;
            public float x1;
            public float y1;
            public float x2;
            public float y2;
            public float spacing;
            public int seed;
            public int depth;
            public KampungMix mix;
            public string role;
            public int count;
            public float radius;
        }

        private static KaliMapBackdropBuilder.SceneAssetCache activeAssetCache;

        private static readonly string[] NormalTrashNames = new[]
        {
            "PF_Trash_BungkusIndomy",
            "PF_Trash_SachetKecapBingo",
            "PF_Trash_SachetMoli",
            "PF_Trash_BotolLifeman",
            "PF_Trash_BungkusSariBoti",
            "PF_Trash_BungkusRisol",
            "PF_Trash_StyrofoamMakanan",
            "PF_Trash_BotolSprit",
            "PF_Trash_KotakRokok",
            "PF_Trash_SandalSwallow",
            "PF_Trash_AquaBottle_600ml",
            "PF_Trash_AquaGalon_19L",
            "PF_Trash_PopMieCup",
            "PF_Trash_KresekBag",
            "PF_Trash_KasurKapuk",
            "PF_Trash_BanBekas",
            "PF_Trash_EcengGondok",
            "PF_Trash_BatangPisang"
        };

        private static readonly string[] MedicalTrashNames = new[]
        {
            "PF_Trash_MedicalBag",
            "PF_Trash_SyringeBox"
        };

        private static readonly string[] BiohazardTrashNames = new[]
        {
            "PF_Trash_BiohazardDrum",
            "PF_Trash_RadioactiveBarrel"
        };

        private static readonly string[] NikiRootPrefabs = new[]
        {
            "Assets/_Project/UI/Prefabs/Canvas_HUD.prefab",
            "Assets/_Project/UI/Prefabs/Canvas_ShopBankSampah.prefab",
            "Assets/_Project/UI/Prefabs/Canvas_SDGImpactReport.prefab",
            "Assets/_Project/VFX/VFX_MonsoonRain.prefab",
            "Assets/_Project/VFX/VFX_WaterSplashMuddy.prefab",
            "Assets/_Project/VFX/VFX_TrashAvalanche.prefab"
        };

        private static string[] EnvPaths(string baseName) => new[]
        {
            $"Assets/_Project/Environment/Prefabs/PF_Env_{baseName}.prefab",
            $"Assets/_Project/Environment/Meshes/SM_Env_{baseName}.fbx"
        };

        private static string[] PropPaths(string baseName) => new[]
        {
            $"Assets/_Project/Props/Equipment/Prefabs/PF_Prop_{baseName}.prefab",
            $"Assets/_Project/Props/Equipment/Meshes/SM_Prop_{baseName}.fbx"
        };

        private static readonly Dictionary<string, string[]> ItemAssetTable = new Dictionary<string, string[]>
        {
            ["bank_sampah"] = EnvPaths("BankSampah"),
            ["pos_medis"] = EnvPaths("PosMedisB3"),
            ["karantina_biohazard"] = EnvPaths("KarantinaBiohazard"),
            ["pengepul"] = EnvPaths("GudangPengepul"),
            ["kopdes"] = new[]
            {
                "Assets/_Project/Environment/Prefabs/PF_Env_KoperasiDesa.prefab",
                "Assets/_Project/Environment/Meshes/SM_Env_KoperasiDesa.fbx",
                "Assets/_Project/Environment/Prefabs/PF_Env_Kopdes.prefab",
                "Assets/_Project/Environment/Meshes/SM_Env_Kopdes.fbx"
            },
            ["toko_alat"] = new[]
            {
                "Assets/_Project/Environment/Prefabs/PF_Env_KoperasiDesa.prefab",
                "Assets/_Project/Environment/Meshes/SM_Env_KoperasiDesa.fbx",
                "Assets/_Project/Environment/Prefabs/PF_Env_TokoAlat.prefab",
                "Assets/_Project/Environment/Meshes/SM_Env_TokoAlat.fbx"
            },
            ["rumah"] = EnvPaths("RumahPanggung"),
            ["warung"] = new[]
            {
                "Assets/_Project/Environment/Prefabs/PF_Env_WarungMadura.prefab",
                "Assets/_Project/Environment/Meshes/SM_Env_WarungMadura.fbx",
                "Assets/_Project/Environment/Prefabs/PF_Env_Warung.prefab",
                "Assets/_Project/Environment/Meshes/SM_Env_Warung.fbx"
            },
            ["warung_madura"] = EnvPaths("WarungMadura"),
            ["dermaga"] = EnvPaths("Dermaga"),
            ["gunung_node"] = EnvPaths("GunungSampah_3Tiers"),
            ["jembatan"] = EnvPaths("JembatanUtama"),
            ["sluice_gate"] = EnvPaths("PintuAirSiaga1"),
            ["interceptor"] = PropPaths("SolarInterceptor"),
            ["trash_boom"] = PropPaths("TrashBoomSegment"),
            ["excavator"] = new[]
            {
                "Assets/_Project/Rigging/PF_ExcavatorAmfibi.prefab",
                "Assets/_Project/Rigging/SK_ExcavatorAmfibi.fbx"
            }
        };

        [MenuItem("KALI/Load Default Purpose-Built Map")]
        public static void LoadDefaultMap()
        {
            EnsureUrpPipelineAssigned();
            if (ImportFromPath(DefaultMapPath) && !Application.isPlaying && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                SaveMainScene();
            }
        }

        [MenuItem("KALI/Save Main Scene")]
        public static void SaveMainScene()
        {
            if (Application.isPlaying || EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("[KALI] Cannot save Main.unity while in PlayMode.");
                return;
            }

            if (!AssetDatabase.IsValidFolder("Assets/_Project/Scenes"))
            {
                AssetDatabase.CreateFolder("Assets/_Project", "Scenes");
            }

            Scene scene = SceneManager.GetActiveScene();
            if (!EditorSceneManager.SaveScene(scene, MainScenePath))
            {
                Debug.LogError($"[KALI] Failed to save scene at: {MainScenePath}");
                return;
            }

            List<EditorBuildSettingsScene> scenes = new List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
            int idx = scenes.FindIndex(s => string.Equals(s.path, MainScenePath, StringComparison.OrdinalIgnoreCase));
            if (idx >= 0) scenes[idx].enabled = true;
            else scenes.Insert(0, new EditorBuildSettingsScene(MainScenePath, true));
            EditorBuildSettings.scenes = scenes.ToArray();

            Debug.Log($"[KALI] Saved {MainScenePath} and enabled it in EditorBuildSettings.");
        }

        [MenuItem("KALI/Setup URP Pipeline")]
        public static void EnsureUrpPipelineAssigned()
        {
            if (GraphicsSettings.defaultRenderPipeline != null) return;

            const string dir = "Assets/_Project/Settings";
            const string assetPath = dir + "/URP_KaliPipeline.asset";
            const string rendererPath = dir + "/URP_KaliRenderer.asset";
            if (!AssetDatabase.IsValidFolder(dir))
            {
                AssetDatabase.CreateFolder("Assets/_Project", "Settings");
            }

            UniversalRenderPipelineAsset pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(assetPath);
            if (pipeline == null)
            {
                pipeline = UniversalRenderPipelineAsset.Create();
                AssetDatabase.CreateAsset(pipeline, assetPath);
                pipeline.LoadBuiltinRendererData(RendererType.UniversalRenderer);
                if (AssetDatabase.LoadAssetAtPath<ScriptableRendererData>("Assets/UniversalRenderer.asset") != null)
                {
                    AssetDatabase.MoveAsset("Assets/UniversalRenderer.asset", rendererPath);
                }
                AssetDatabase.SaveAssets();
            }

            GraphicsSettings.defaultRenderPipeline = pipeline;
            QualitySettings.renderPipeline = pipeline;
            Debug.Log("[KALI] Assigned URP Pipeline Asset: " + assetPath);
        }

        [MenuItem("KALI/Import Map JSON to Scene...")]
        public static void ImportViaDialog()
        {
            EnsureUrpPipelineAssigned();
            string path = EditorUtility.OpenFilePanel("Select KALI Map JSON", Application.dataPath, "json");
            if (!string.IsNullOrEmpty(path)) ImportFromPath(path);
        }

        public static List<KaliKampungBuilder.ExpandedBuilding> ExpandDefaultMapKampungRows()
        {
            if (!File.Exists(DefaultMapPath))
            {
                Debug.LogError($"[KALI] Map JSON not found at: {DefaultMapPath}");
                return new List<KaliKampungBuilder.ExpandedBuilding>();
            }

            string rawJson = File.ReadAllText(DefaultMapPath);
            MapData data = JsonUtility.FromJson<MapData>(rawJson);
            if (data == null || data.items == null)
            {
                Debug.LogError("[KALI] Failed to parse default Map JSON.");
                return new List<KaliKampungBuilder.ExpandedBuilding>();
            }

            CollectRowsAndAvoidance(data, rawJson, out var rowSpecs, out var avoidZones, out var footpaths);
            // Same real-footprint refinement as the bake, when the built world is in the scene.
            GameObject built = GameObject.Find("_KALI_World");
            if (built != null) RefineAvoidZonesToRealFootprints(built.transform, avoidZones);
            return KaliKampungBuilder.ExpandKampungRows(rowSpecs, avoidZones, footpaths);
        }

        public static List<KaliNpcBuilder.ExpandedNpc> ExpandDefaultMapNpcGroups()
        {
            if (!File.Exists(DefaultMapPath))
            {
                Debug.LogError($"[KALI] Map JSON not found at: {DefaultMapPath}");
                return new List<KaliNpcBuilder.ExpandedNpc>();
            }

            string rawJson = File.ReadAllText(DefaultMapPath);
            MapData data = JsonUtility.FromJson<MapData>(rawJson);
            if (data == null || data.items == null)
            {
                Debug.LogError("[KALI] Failed to parse default Map JSON.");
                return new List<KaliNpcBuilder.ExpandedNpc>();
            }

            CollectRowsAndAvoidance(data, rawJson, out var rowSpecs, out var avoidZones, out var footpaths);
            GameObject built = GameObject.Find("_KALI_World");
            if (built != null) RefineAvoidZonesToRealFootprints(built.transform, avoidZones);
            var expandedBuildings = KaliKampungBuilder.ExpandKampungRows(rowSpecs, avoidZones, footpaths);
            var npcGroups = CollectNpcGroups(data);
            return KaliNpcBuilder.ExpandNpcGroups(npcGroups, expandedBuildings, avoidZones, footpaths);
        }

        private static List<KaliNpcBuilder.NpcGroupSpec> CollectNpcGroups(MapData data)
        {
            var groups = new List<KaliNpcBuilder.NpcGroupSpec>();
            if (data?.items == null) return groups;
            foreach (MapItem item in data.items)
            {
                if (item.type != "npc_group") continue;
                groups.Add(new KaliNpcBuilder.NpcGroupSpec
                {
                    id = item.id,
                    role = item.role,
                    x = item.x,
                    y = item.y,
                    count = item.count,
                    radius = item.radius,
                    seed = item.seed
                });
            }
            return groups;
        }

        private static void CollectRowsAndAvoidance(
            MapData data,
            string rawJson,
            out List<KaliKampungBuilder.KampungRowSpec> rowSpecs,
            out List<KaliKampungBuilder.AvoidanceZone> avoidZones,
            out List<KaliKampungBuilder.PathSegment> footpaths)
        {
            rowSpecs = new List<KaliKampungBuilder.KampungRowSpec>();
            avoidZones = new List<KaliKampungBuilder.AvoidanceZone>();
            footpaths = KaliKampungBuilder.ParseFootpathsFromJson(rawJson);

            if (data?.items == null) return;

            foreach (MapItem item in data.items)
            {
                if (item.type == "kampung_row")
                {
                    float rumahW = item.mix != null ? item.mix.rumah : 0f;
                    float warungW = item.mix != null
                        ? (item.mix.warung_madura > 0f ? item.mix.warung_madura : item.mix.warung)
                        : 0f;
                    if (rumahW <= 0f && warungW <= 0f)
                    {
                        rumahW = 0.7f;
                        warungW = 0.3f;
                    }

                    rowSpecs.Add(new KaliKampungBuilder.KampungRowSpec
                    {
                        id = item.id,
                        name = item.name,
                        x1 = item.x1,
                        y1 = item.y1,
                        x2 = item.x2,
                        y2 = item.y2,
                        spacing = item.spacing,
                        seed = item.seed,
                        depth = item.depth,
                        rumahWeight = rumahW,
                        warungWeight = warungW
                    });
                }
                else if (TryGetAvoidanceSpec(item.type, out Vector2 halfExtents, out float minClearance))
                {
                    avoidZones.Add(new KaliKampungBuilder.AvoidanceZone
                    {
                        name = string.IsNullOrEmpty(item.name) ? item.type : item.name,
                        worldCenter = RiverMath.ToWorld3D(item.x, item.y, 0f),
                        halfExtentsXZ = halfExtents,
                        minClearanceM = minClearance
                    });
                }
            }
        }

        // Replaces the hardcoded hub/Dermaga footprints with the real XZ bounds of the spawned objects.
        // Zones with no matching renderer keep their spec fallback. Particle renderers and ground light pools are skipped.
        private static void RefineAvoidZonesToRealFootprints(Transform root, List<KaliKampungBuilder.AvoidanceZone> avoidZones)
        {
            Transform[] all = root.GetComponentsInChildren<Transform>(true);
            for (int i = 0; i < avoidZones.Count; i++)
            {
                KaliKampungBuilder.AvoidanceZone z = avoidZones[i];
                Transform match = null;
                foreach (Transform t in all)
                {
                    if (t.name == z.name && t.GetComponentInChildren<Renderer>(true) != null)
                    {
                        match = t;
                        break;
                    }
                }
                if (match == null) continue;

                bool any = false;
                Bounds b = default;
                foreach (Renderer r in match.GetComponentsInChildren<Renderer>(true))
                {
                    if (r is ParticleSystemRenderer || KaliKampungBuilder.IsGroundLightPool(r)) continue;
                    if (!any) { b = r.bounds; any = true; }
                    else b.Encapsulate(r.bounds);
                }
                if (!any) continue;

                z.worldCenter = new Vector3(b.center.x, 0f, b.center.z);
                z.halfExtentsXZ = new Vector2(b.extents.x, b.extents.z);
                avoidZones[i] = z;
            }
        }

        private static bool TryGetAvoidanceSpec(string type, out Vector2 halfExtentsXZ, out float minClearanceM)
        {
            switch (type)
            {
                case "bank_sampah":
                case "pos_medis":
                case "karantina_biohazard":
                case "pengepul":
                    halfExtentsXZ = new Vector2(3.0f, 4.5f);
                    minClearanceM = 6.5f;
                    return true;
                case "kopdes":
                case "toko_alat":
                    halfExtentsXZ = new Vector2(3.0f, 5.5f);
                    minClearanceM = 6.5f;
                    return true;
                case "dermaga":
                    halfExtentsXZ = new Vector2(4.0f, 2.0f);
                    minClearanceM = 6.0f;
                    return true;
                case "jembatan":
                    halfExtentsXZ = new Vector2(23.0f, 3.8f);
                    minClearanceM = 5.0f;
                    return true;
                case "sluice_gate":
                    halfExtentsXZ = new Vector2(15.0f, 8.0f);
                    minClearanceM = 5.0f;
                    return true;
                case "gunung_node":
                    halfExtentsXZ = new Vector2(20.0f, 12.0f);
                    minClearanceM = 5.0f;
                    return true;
                case "excavator":
                    halfExtentsXZ = new Vector2(4.0f, 4.0f);
                    minClearanceM = 5.0f;
                    return true;
                case "interceptor":
                    halfExtentsXZ = new Vector2(4.5f, 3.0f);
                    minClearanceM = 5.0f;
                    return true;
                case "trash_boom":
                    halfExtentsXZ = new Vector2(9.0f, 2.0f);
                    minClearanceM = 5.0f;
                    return true;
                case "spawn":
                    halfExtentsXZ = new Vector2(1.0f, 1.0f);
                    minClearanceM = 6.5f;
                    return true;
                default:
                    halfExtentsXZ = Vector2.zero;
                    minClearanceM = 0f;
                    return false;
            }
        }

        private static bool ImportFromPath(string path)
        {
            if (!File.Exists(path))
            {
                Debug.LogError($"[KALI] Map JSON not found at: {path}");
                return false;
            }

            string rawJson = File.ReadAllText(path);
            MapData data = JsonUtility.FromJson<MapData>(rawJson);
            if (data == null || data.items == null)
            {
                Debug.LogError("[KALI] Failed to parse Map JSON.");
                return false;
            }

            GameObject existing = GameObject.Find("_KALI_World");
            if (existing != null) UnityEngine.Object.DestroyImmediate(existing);

            var assetCache = new KaliMapBackdropBuilder.SceneAssetCache();
            activeAssetCache = assetCache;
            try
            {
                GameObject root = new GameObject("_KALI_World");
                GameObject terrainGroup = CreateGroup("Terrain", root.transform);
                GameObject buildingsGroup = CreateGroup("Buildings", root.transform);
                GameObject clutterGroup = CreateGroup("Clutter", root.transform);
                GameObject treesGroup = CreateGroup("Trees", root.transform);
                GameObject npcsGroup = CreateGroup("NPCs", root.transform);
                GameObject trashGroup = CreateGroup("Trash", root.transform);
                GameObject infraGroup = CreateGroup("Infrastructure", root.transform);
                GameObject gunungGroup = CreateGroup("GunungSampah", root.transform);
                GameObject managersGroup = CreateGroup("Managers", root.transform);
                GameObject lightingGroup = CreateGroup("Lighting", root.transform);

                managersGroup.AddComponent<RiverGameManager>();
                RiverTrashSpawner spawner = managersGroup.AddComponent<RiverTrashSpawner>();
                spawner.SetTrashRoot(trashGroup.transform);
                spawner.normalPrefabs = LoadTrashPrefabPool(NormalTrashNames);
                spawner.medicalPrefabs = LoadTrashPrefabPool(MedicalTrashNames);
                spawner.biohazardPrefabs = LoadTrashPrefabPool(BiohazardTrashNames);

                BuildTerrainAndWater(terrainGroup.transform, out Material resolvedWaterMat);
                SetupLightingRig(lightingGroup.transform);

                foreach (MapItem item in data.items)
                {
                    SpawnItem(
                        item,
                        buildingsGroup.transform,
                        trashGroup.transform,
                        infraGroup.transform,
                        gunungGroup.transform,
                        treesGroup.transform,
                        root.transform,
                        assetCache);
                }

                CollectRowsAndAvoidance(data, rawJson, out var rowSpecs, out var avoidZones, out var footpaths);
                RefineAvoidZonesToRealFootprints(root.transform, avoidZones);
                var expanded =KaliKampungBuilder.ExpandKampungRows(rowSpecs, avoidZones, footpaths);
                var stats = KaliKampungBuilder.SpawnKampungAndClutter(
                    expanded,
                    buildingsGroup.transform,
                    clutterGroup.transform,
                    treesGroup.transform,
                    assetCache,
                    avoidZones,
                    footpaths);

                Physics.SyncTransforms();
                var npcGroups = CollectNpcGroups(data);
                var expandedNpcs = KaliNpcBuilder.ExpandNpcGroups(npcGroups, expanded, avoidZones, footpaths);
                int npcCount = KaliNpcBuilder.SpawnNpcGroups(expandedNpcs, npcsGroup.transform, assetCache);

                KaliMapBackdropBuilder.BuildBackdropAndBoundary(
                    root.transform,
                    assetCache,
                    resolvedWaterMat,
                    out int backdropCount,
                    out int boundaryCount);

                foreach (string nikiPath in NikiRootPrefabs)
                {
                    AttachPrefabIfPresent(root.transform, nikiPath);
                }

                EnsureEventSystem(root.transform);

                Debug.Log(
                    $"[KALI] Imported {data.items.Length} JSON items + kampung expansion from {path} into _KALI_World | " +
                    $"buildings={stats.totalBuildings} (rumah={stats.rumahCount}, warung={stats.warungCount}, west={stats.westCount}, east={stats.eastCount}), " +
                    $"jetties={stats.jettyCount}, bins={stats.binCount}, boats={stats.boatCount}, lanterns={stats.lanternCount}, " +
                    $"npcs={npcCount}, rearTrees={stats.rearTreeCount}, backdrop={backdropCount}, boundaries={boundaryCount}.");
                return true;
            }
            finally
            {
                activeAssetCache = null;
            }
        }

        private static void EnsureEventSystem(Transform root)
        {
            if (UnityEngine.Object.FindObjectOfType<EventSystem>() != null) return;
            GameObject esGo = new GameObject("EventSystem");
            esGo.transform.SetParent(root);
            esGo.AddComponent<EventSystem>();
#if ENABLE_INPUT_SYSTEM
            esGo.AddComponent<InputSystemUIInputModule>();
#else
            esGo.AddComponent<StandaloneInputModule>();
#endif
        }

        private static GameObject LoadFirstPrefab(params string[] paths) => LoadFirstAsset<GameObject>(paths);

        private static T LoadFirstAsset<T>(params string[] paths) where T : UnityEngine.Object
        {
            if (paths == null) return null;
            foreach (string p in paths)
            {
                T asset = AssetDatabase.LoadAssetAtPath<T>(p);
                if (asset != null) return asset;
            }
            return null;
        }

        private static GameObject[] LoadTrashPrefabPool(string[] names)
        {
            List<GameObject> list = new List<GameObject>();
            foreach (string n in names)
            {
                GameObject p = LoadFirstPrefab($"Assets/_Project/Props/Trash/Prefabs/{n}.prefab");
                if (p != null) list.Add(p);
            }
            return list.ToArray();
        }

        private static void BuildTerrainAndWater(Transform parent, out Material resolvedWaterMat)
        {
            float worldWidthM = RiverMath.WorldW * RiverMath.MapScale; // 130m
            float worldLenM = RiverMath.WorldH * RiverMath.MapScale;  // 180m

            GameObject valleyPrefab = LoadFirstPrefab(EnvPaths("RiverValleyTerrain"));
            if (valleyPrefab != null)
            {
                GameObject valley = (GameObject)PrefabUtility.InstantiatePrefab(valleyPrefab, parent);
                valley.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
                // Static terrain: non-convex MeshCollider on every mesh that lacks a collider (no Rigidbody)
                foreach (MeshFilter mf in valley.GetComponentsInChildren<MeshFilter>(true))
                {
                    if (mf.sharedMesh != null && mf.GetComponent<Collider>() == null)
                    {
                        MeshCollider mc = mf.gameObject.AddComponent<MeshCollider>();
                        mc.convex = false;
                        mc.sharedMesh = mf.sharedMesh;
                    }
                }
                EnsureCollider(valley, concaveMesh: true, ensureRootCollider: false, solidRootCollider: false);
                KaliMapBackdropBuilder.MarkStaticDecor(valley, includeOccluder: true);
            }
            else
            {
                BuildSplitBanksAndRiver(parent, worldWidthM, worldLenM);
            }

            GameObject river = FindDescendantByName(parent, "River_WaterSurface");
            bool createdRiver = river == null;
            if (createdRiver)
            {
                river = GameObject.CreatePrimitive(PrimitiveType.Plane);
                river.name = "River_WaterSurface";
                river.transform.SetParent(parent);
                river.transform.position = Vector3.zero;
                river.transform.localScale = new Vector3(worldWidthM * 0.1f, 1f, worldLenM * 0.1f);
            }

            Collider waterCol = river.GetComponent<Collider>();
            if (waterCol != null) UnityEngine.Object.DestroyImmediate(waterCol);

            Material waterMat = LoadFirstAsset<Material>(
                "Assets/_Project/Shaders/M_KaliWater.mat",
                "Assets/_Project/Environment/Materials/M_KaliWater.mat");
            Renderer riverRenderer = river.GetComponent<Renderer>();
            if (waterMat != null && riverRenderer != null)
            {
                riverRenderer.sharedMaterial = waterMat;
            }
            else if (createdRiver || (riverRenderer != null && riverRenderer.sharedMaterial == null))
            {
                ApplyTint(river, new Color(0.24f, 0.20f, 0.14f, 0.85f));
            }

            resolvedWaterMat = riverRenderer != null ? riverRenderer.sharedMaterial : waterMat;

            if (river.GetComponent<RiverWaterSurfaceFollower>() == null)
            {
                river.AddComponent<RiverWaterSurfaceFollower>();
            }
        }

        /// <summary>
        /// Greybox fallback when SM_Env_RiverValleyTerrain is absent: splits Ground_Daratan into
        /// West and East riverbank segments matching RiverMath S-curve down to -2.0m.
        /// </summary>
        private static void BuildSplitBanksAndRiver(Transform parent, float worldWidthM, float worldLenM)
        {
            float halfWorldX = worldWidthM * 0.5f;                   // 65m
            float bankThickness = BankTopY - RiverbedTopY;           // 3.4m
            float bankCenterY = RiverbedTopY + bankThickness * 0.5f; // -0.3m

            GameObject riverbed = GameObject.CreatePrimitive(PrimitiveType.Cube);
            riverbed.name = "Riverbed_Floor";
            riverbed.transform.SetParent(parent);
            riverbed.transform.position = new Vector3(0f, RiverbedTopY - 0.5f, 0f);
            riverbed.transform.localScale = new Vector3(worldWidthM, 1f, worldLenM);
            ApplyTint(riverbed, new Color(0.18f, 0.15f, 0.11f));
            KaliMapBackdropBuilder.MarkStaticDecor(riverbed, includeOccluder: true);

            const int slices = 18;
            float sliceLenM = worldLenM / slices;
            Color bankColor = new Color(0.24f, 0.31f, 0.22f);

            for (int i = 0; i < slices; i++)
            {
                float zCenter = -worldLenM * 0.5f + (i + 0.5f) * sliceLenM;
                float mapY = zCenter / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
                float cxWorld = (RiverMath.RiverCenterMapX(mapY) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
                float hwWorld = RiverMath.RiverHalfWidthMap(mapY) * RiverMath.MapScale;

                float westEdge = cxWorld - hwWorld;
                float westWidth = Mathf.Max(2f, westEdge - (-halfWorldX));
                GameObject westBank = GameObject.CreatePrimitive(PrimitiveType.Cube);
                westBank.name = $"Ground_Daratan_West_{i:00}";
                westBank.transform.SetParent(parent);
                westBank.transform.position = new Vector3(-halfWorldX + westWidth * 0.5f, bankCenterY, zCenter);
                westBank.transform.localScale = new Vector3(westWidth, bankThickness, sliceLenM + 0.15f);
                ApplyTint(westBank, bankColor);
                KaliMapBackdropBuilder.MarkStaticDecor(westBank, includeOccluder: true);

                float eastEdge = cxWorld + hwWorld;
                float eastWidth = Mathf.Max(2f, halfWorldX - eastEdge);
                GameObject eastBank = GameObject.CreatePrimitive(PrimitiveType.Cube);
                eastBank.name = $"Ground_Daratan_East_{i:00}";
                eastBank.transform.SetParent(parent);
                eastBank.transform.position = new Vector3(eastEdge + eastWidth * 0.5f, bankCenterY, zCenter);
                eastBank.transform.localScale = new Vector3(eastWidth, bankThickness, sliceLenM + 0.15f);
                ApplyTint(eastBank, bankColor);
                KaliMapBackdropBuilder.MarkStaticDecor(eastBank, includeOccluder: true);
            }
        }

        private static void SetupLightingRig(Transform parent)
        {
            GameObject rigPrefab = LoadFirstPrefab("Assets/_Project/Lighting/Prefabs/PF_LightingRig.prefab");
            if (rigPrefab != null)
            {
                GameObject rig = (GameObject)PrefabUtility.InstantiatePrefab(rigPrefab, parent);
                rig.name = "PF_LightingRig";

                Light rigLight = rig.GetComponentInChildren<Light>(true);
                if (rigLight != null) RenderSettings.sun = rigLight;

                Material skyMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/_Project/Lighting/Materials/M_KaliSky.mat");
                if (skyMat != null) RenderSettings.skybox = skyMat;

                RenderSettings.ambientMode = AmbientMode.Trilight;
                RenderSettings.fog = true;
                RenderSettings.fogMode = FogMode.ExponentialSquared;

                KaliDayNightCycle cycle = rig.GetComponent<KaliDayNightCycle>();
                if (cycle != null) cycle.SetHour(cycle.startHour);

                Debug.Log("[KALI] Successfully instantiated PF_LightingRig + M_KaliSky.");
                return;
            }

            GameObject sun = new GameObject("Directional Light (Fallback)");
            sun.transform.SetParent(parent);
            sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            Light l = sun.AddComponent<Light>();
            l.type = LightType.Directional;
            l.color = new Color(1f, 0.95f, 0.84f);
            l.intensity = 1.8f;
            l.shadows = LightShadows.Soft;
        }

        private static void SpawnItem(
            MapItem item,
            Transform buildings,
            Transform trash,
            Transform infra,
            Transform gunung,
            Transform trees,
            Transform root,
            KaliMapBackdropBuilder.SceneAssetCache assetCache)
        {
            if (item.type == "kampung_row" || item.type == "npc_group")
            {
                return;
            }

            if (item.type == "pohon")
            {
                uint h = Fnv1aHash(item.id);
                var rng = new System.Random((int)h);
                float yaw = (float)(rng.NextDouble() * 360.0);
                float scale = 0.85f + (float)(rng.NextDouble() * 0.40);
                float tilt = (float)(rng.NextDouble() * 8.0 - 4.0);
                bool useAltGreen = rng.NextDouble() < 0.45;
                KaliMapBackdropBuilder.CreateLowPolyTree(
                    trees,
                    assetCache,
                    RiverMath.ToWorld3D(item.x, item.y, BankTopY),
                    yaw,
                    scale,
                    tilt,
                    item.name,
                    useAltGreen,
                    addCollider: true,
                    isStatic: true);
                return;
            }

            if (item.type == "spawn")
            {
                SpawnPlayerRig(item, root);
                return;
            }

            if (item.type == "trash_pile")
            {
                SpawnTrashCluster(item, trash);
                AttachPrefabIfPresent(trash, MethaneBubblesPrefabPath, RiverMath.ToWorld3D(item.x, item.y, 0f), $"VFX_MethaneSludgeBubbles_{item.name}");
                return;
            }

            Transform targetParent = item.type switch
            {
                "gunung_node" => gunung,
                "dermaga" or "trash_boom" or "excavator" or "interceptor" or "jembatan" or "sluice_gate" => infra,
                _ => buildings
            };

            bool isWaterLevel = item.type is "gunung_node" or "dermaga" or "trash_boom" or "interceptor" or "excavator" or "jembatan" or "sluice_gate";
            float groundY = isWaterLevel ? 0f : BankTopY;

            GameObject go = SpawnEnvOrFallback(item, targetParent, groundY, out bool usedPrefab);

            if (item.type is "bank_sampah" or "kopdes" or "toko_alat" or "pengepul" or "pos_medis" or "karantina_biohazard"
                or "rumah" or "warung" or "warung_madura" or "jembatan" or "sluice_gate" or "dermaga")
            {
                KaliMapBackdropBuilder.MarkStaticDecor(go, includeOccluder: item.type != "dermaga");
            }

            if (item.type == "gunung_node")
            {
                GunungNodeController gCtrl = go.GetComponent<GunungNodeController>();
                if (gCtrl == null) gCtrl = go.AddComponent<GunungNodeController>();
                gCtrl.scaleFromCenterPrimitive = !usedPrefab;
                AttachPrefabIfPresent(gunung, MethaneBubblesPrefabPath, RiverMath.ToWorld3D(item.x, item.y, 0f), $"VFX_MethaneSludgeBubbles_{item.name}");
            }
            else if (item.type is "warung" or "warung_madura")
            {
                AttachOnTopIfPresent(go.transform, "Assets/_Project/Lighting/Prefabs/PF_Lantern_Warung.prefab");
            }
            else if (item.type == "sluice_gate")
            {
                AttachOnTopIfPresent(go.transform, "Assets/_Project/Lighting/Prefabs/PF_WarningBeacon_PintuAir.prefab");
                CreatePintuAirPileZone(item, infra);
            }
            else if (item.type is "bank_sampah" or "pos_medis" or "karantina_biohazard" or "pengepul")
            {
                CreateStationRiverDockTrigger(item, go.transform);
            }

            if (item.type is "bank_sampah" or "pos_medis" or "karantina_biohazard" or "pengepul" or "kopdes")
            {
                CreateStationServicePoint(item, go.transform);
            }
        }

        /// <summary>
        /// Spec A: the only place a station can be used. A 2 m trigger sphere on the ground, 2.5 m out from the
        /// building's river-facing side (the side the footpath runs along), outside the building collider.
        /// </summary>
        private static void CreateStationServicePoint(MapItem item, Transform stationTransform)
        {
            const float Radius = 2.0f;
            const float GapFromWall = 2.5f;

            Bounds b = new Bounds(stationTransform.position, Vector3.one * 2f);
            Renderer[] renderers = stationTransform.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length > 0)
            {
                b = renderers[0].bounds;
                for (int i = 1; i < renderers.Length; i++) b.Encapsulate(renderers[i].bounds);
            }

            float cxWorld = (RiverMath.RiverCenterMapX(item.y) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
            float dirX = cxWorld >= b.center.x ? 1f : -1f;
            float x = (dirX > 0f ? b.max.x : b.min.x) + dirX * GapFromWall;

            GameObject sp = new GameObject($"{item.name}_ServicePoint");
            sp.transform.SetParent(stationTransform, worldPositionStays: true);
            sp.transform.position = new Vector3(x, BankTopY, b.center.z);
            SphereCollider sc = sp.AddComponent<SphereCollider>();
            sc.isTrigger = true;
            Vector3 ls = sp.transform.lossyScale;
            sc.radius = Radius / Mathf.Max(0.0001f, Mathf.Max(Mathf.Abs(ls.x), Mathf.Abs(ls.z)));
        }

        private static void CreateStationRiverDockTrigger(MapItem item, Transform stationTransform)
        {
            float cxWorld = (RiverMath.RiverCenterMapX(item.y) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
            float hwWorld = RiverMath.RiverHalfWidthMap(item.y) * RiverMath.MapScale;
            Vector3 stPos = stationTransform.position;
            float bankEdgeX = stPos.x >= cxWorld ? (cxWorld + hwWorld - 1.5f) : (cxWorld - hwWorld + 1.5f);
            float midX = (stPos.x + bankEdgeX) * 0.5f;
            float spanX = Mathf.Max(6f, Mathf.Abs(stPos.x - bankEdgeX) + 5f);

            GameObject dockTrigger = new GameObject($"{item.name}_RiverDockTrigger");
            dockTrigger.transform.SetParent(stationTransform, worldPositionStays: true);
            dockTrigger.transform.position = new Vector3(midX, 0.8f, stPos.z);
            BoxCollider bc = dockTrigger.AddComponent<BoxCollider>();
            bc.isTrigger = true;
            bc.size = new Vector3(spanX, 4.5f, 8f);
        }

        private static GameObject SpawnEnvOrFallback(MapItem item, Transform parent, float groundY, out bool usedPrefab)
        {
            GameObject prefab = ItemAssetTable.TryGetValue(item.type, out string[] paths) ? LoadFirstPrefab(paths) : null;
            if (prefab != null)
            {
                usedPrefab = true;
                GameObject inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
                inst.name = item.name;
                inst.transform.SetPositionAndRotation(RiverMath.ToWorld3D(item.x, item.y, groundY), Quaternion.Euler(0f, item.rot, 0f));

                bool concave = item.type is "jembatan" or "sluice_gate";
                bool isGunung = item.type == "gunung_node";
                bool needRoot = isGunung || item.type is "bank_sampah" or "pos_medis" or "karantina_biohazard" or "pengepul" or "kopdes" or "toko_alat" or "dermaga";
                bool solidRoot = isGunung || item.type == "dermaga";
                EnsureCollider(inst, concave, needRoot, solidRoot);
                return inst;
            }

            usedPrefab = false;
            if (item.type == "jembatan") return BuildElevatedBridge(item, parent);

            float sx = Mathf.Max(item.type == "sluice_gate" ? 16f : 1.5f, item.w * RiverMath.MapScale);
            float sz = Mathf.Max(item.type == "sluice_gate" ? 3f : 1.5f, item.h * RiverMath.MapScale);
            float sy = Mathf.Max(item.type == "sluice_gate" ? 4f : 0.8f, item.elev * RiverMath.MapScale);

            GameObject fallback = GameObject.CreatePrimitive(item.type == "pohon" ? PrimitiveType.Cylinder : PrimitiveType.Cube);
            fallback.name = item.name;
            fallback.transform.SetParent(parent);
            fallback.transform.SetPositionAndRotation(RiverMath.ToWorld3D(item.x, item.y, groundY + sy * 0.5f), Quaternion.Euler(0f, item.rot, 0f));
            fallback.transform.localScale = new Vector3(sx, sy, sz);
            if (ColorUtility.TryParseHtmlString(item.color, out Color parsed)) ApplyTint(fallback, parsed);
            return fallback;
        }

        private static void SpawnPlayerRig(MapItem item, Transform root)
        {
            GameObject player = new GameObject("Player_Rig");
            player.transform.SetParent(root);
            player.transform.position = RiverMath.ToWorld3D(item.x, item.y, BankTopY + 1.0f);
            player.transform.rotation = Quaternion.Euler(0f, 180f, 0f); // Look North (-Z) toward Gunung Sampah
            CharacterController cc = player.AddComponent<CharacterController>();
            cc.height = 1.8f;
            cc.radius = 0.4f;
            KaliPlayerController ctrl = player.AddComponent<KaliPlayerController>();
            player.AddComponent<KaliFieldGuideOverlay>();

            Camera mainCam = Camera.main;
            if (mainCam == null)
            {
                GameObject camGo = new GameObject("Main Camera");
                camGo.tag = "MainCamera";
                mainCam = camGo.AddComponent<Camera>();
            }
            mainCam.transform.SetParent(player.transform);
            mainCam.transform.localPosition = new Vector3(0f, 0.7f, 0f);
            mainCam.transform.localRotation = Quaternion.identity;
            mainCam.clearFlags = CameraClearFlags.Skybox;
            mainCam.fieldOfView = 60f;
            UniversalAdditionalCameraData camData = mainCam.GetComponent<UniversalAdditionalCameraData>();
            if (camData == null) camData = mainCam.gameObject.AddComponent<UniversalAdditionalCameraData>();
            camData.renderPostProcessing = true;

            GameObject socket = new GameObject("ToolSocket");
            socket.transform.SetParent(mainCam.transform);
            socket.transform.localPosition = new Vector3(0.38f, -0.32f, 0.65f);
            socket.transform.localRotation = Quaternion.identity;
            ctrl.toolSocket = socket.transform;

            IReadOnlyList<ToolDefinition> allTools = ToolCatalog.AllTools;
            ctrl.toolPrefabs = new GameObject[allTools.Count];
            for (int i = 0; i < allTools.Count; i++)
            {
                ctrl.toolPrefabs[i] = AssetDatabase.LoadAssetAtPath<GameObject>(
                    $"Assets/_Project/Props/Tools/Prefabs/{allTools[i].PrefabName}.prefab");
            }
        }

        private static GameObject BuildElevatedBridge(MapItem item, Transform parent)
        {
            float sx = Mathf.Max(12f, item.w * RiverMath.MapScale);
            float sz = Mathf.Max(4f, item.h * RiverMath.MapScale);
            Vector3 center = RiverMath.ToWorld3D(item.x, item.y, 0f);

            GameObject bridgeRoot = new GameObject(item.name);
            bridgeRoot.transform.SetParent(parent);
            bridgeRoot.transform.SetPositionAndRotation(center, Quaternion.Euler(0f, item.rot, 0f));

            const float deckY = 3.6f; // >= 3.6m boat clearance above baseline water
            const float deckThick = 0.45f;
            Color deckCol = new Color(0.48f, 0.36f, 0.25f);
            Color pierCol = new Color(0.45f, 0.50f, 0.56f);

            GameObject deck = GameObject.CreatePrimitive(PrimitiveType.Cube);
            deck.name = "Bridge_Deck";
            deck.transform.SetParent(bridgeRoot.transform);
            deck.transform.localPosition = new Vector3(0f, deckY, 0f);
            deck.transform.localScale = new Vector3(sx, deckThick, sz);
            ApplyTint(deck, deckCol);

            float[] pierXFrac = new[] { -0.38f, -0.22f, 0.22f, 0.38f };
            float[] pierZFrac = new[] { -0.35f, 0.35f };
            foreach (float xf in pierXFrac)
            {
                foreach (float zf in pierZFrac)
                {
                    GameObject pier = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    pier.name = "Bridge_Pier";
                    pier.transform.SetParent(bridgeRoot.transform);
                    pier.transform.localPosition = new Vector3(sx * xf, (deckY + RiverbedTopY) * 0.5f, sz * zf);
                    pier.transform.localScale = new Vector3(0.95f, deckY - RiverbedTopY, 0.95f);
                    ApplyTint(pier, pierCol);
                }
            }

            const float rampLen = 8.5f;
            float dy = deckY - BankTopY;
            float hyp = Mathf.Sqrt(rampLen * rampLen + dy * dy);
            float angleDeg = Mathf.Atan2(dy, rampLen) * Mathf.Rad2Deg;
            foreach (int side in new[] { -1, 1 })
            {
                GameObject ramp = GameObject.CreatePrimitive(PrimitiveType.Cube);
                ramp.name = side < 0 ? "Bridge_Ramp_West" : "Bridge_Ramp_East";
                ramp.transform.SetParent(bridgeRoot.transform);
                ramp.transform.localPosition = new Vector3(side * (sx * 0.5f + rampLen * 0.5f - 0.3f), BankTopY + dy * 0.5f, 0f);
                ramp.transform.localRotation = Quaternion.Euler(0f, 0f, -side * angleDeg);
                ramp.transform.localScale = new Vector3(hyp, deckThick, sz * 0.92f);
                ApplyTint(ramp, pierCol);
            }

            return bridgeRoot;
        }

        private static void CreatePintuAirPileZone(MapItem item, Transform parent)
        {
            float sx = Mathf.Max(16f, item.w * RiverMath.MapScale);
            Vector3 center = RiverMath.ToWorld3D(item.x, item.y, 0f);

            // Scoopable barrier pile zone just upstream (-Z) of downstream Pintu Air
            GameObject pileZone = GameObject.CreatePrimitive(PrimitiveType.Cube);
            pileZone.name = "PintuAirPile_Zone";
            pileZone.transform.SetParent(parent);
            // Column spanning the full water range so the trigger stays reachable as water rises
            const float floodWaterY = 2.45f; // ponytail: mirrors RiverGameManager.fatalFloodWaterY default (instance field, not const)
            float bottomY = RiverGameManager.BaseWaterLevelY - 0.5f;
            float topY = floodWaterY + 0.5f;
            pileZone.transform.position = new Vector3(center.x, (bottomY + topY) * 0.5f, center.z - 7.5f);
            pileZone.transform.localScale = new Vector3(sx * 0.55f, topY - bottomY, 4.5f);
            BoxCollider bc = pileZone.GetComponent<BoxCollider>();
            if (bc != null) bc.isTrigger = true;
            ApplyTint(pileZone, new Color(0.47f, 0.35f, 0.24f));
        }

        private static void SpawnTrashCluster(MapItem item, Transform parent)
        {
            Vector3 center = RiverMath.ToWorld3D(item.x, item.y, 0f);
            const int count = 5;

            // Stable FNV-1a hash of item.id so cluster layout is identical across imports
            uint hash = 2166136261u;
            foreach (char ch in item.id ?? string.Empty)
            {
                hash ^= ch;
                hash *= 16777619u;
            }
            var rng = new System.Random((int)(hash & 0x7FFFFFFF));
            float spread = Mathf.Clamp(Mathf.Max(item.w, item.h) * RiverMath.MapScale * 0.5f, 1.5f, 6f);
            float Jitter() => (float)(rng.NextDouble() * 2.0 * spread - spread);

            bool tutorial = (item.name ?? string.Empty).Contains("Tutorial");
            for (int i = 0; i < count; i++)
            {
                // Spec E mix over the 8 map piles (40 items): 32 Normal / 6 Medical / 2 Biohazard. Tutorial piles near
                // spawn are all Normal so step 1 -> step 2 (Bank Sampah) works; drums only in the upstream muara piles.
                WasteClass wc = tutorial || i < 3 ? WasteClass.Normal
                    : (i == 3 && item.y < 350f ? WasteClass.Biohazard : (i == 4 ? WasteClass.Medical : WasteClass.Normal));
                GameObject[] pool = LoadTrashPrefabPool(wc switch
                {
                    WasteClass.Medical => MedicalTrashNames,
                    WasteClass.Biohazard => BiohazardTrashNames,
                    _ => NormalTrashNames
                });
                GameObject prefab = pool.Length > 0 ? pool[rng.Next(pool.Length)] : null;

                Vector3 offset = new Vector3(Jitter(), 0f, Jitter());
                GameObject trashObj;
                if (prefab != null)
                {
                    trashObj = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
                    trashObj.transform.SetPositionAndRotation(center + offset, Quaternion.Euler(0f, (float)(rng.NextDouble() * 360.0), 0f));
                    trashObj.transform.localScale *= 2.2f; // same readable bundle scale as RiverTrashSpawner.bundleVisualScale
                }
                else
                {
                    PrimitiveType prim = wc == WasteClass.Biohazard ? PrimitiveType.Cylinder : PrimitiveType.Cube;
                    trashObj = GameObject.CreatePrimitive(prim);
                    trashObj.name = $"{item.name}_{wc}_{i}";
                    trashObj.transform.SetParent(parent);
                    trashObj.transform.position = center + offset;
                    trashObj.transform.localScale = wc == WasteClass.Biohazard
                        ? new Vector3(0.75f, 0.85f, 0.75f)
                        : (wc == WasteClass.Medical ? new Vector3(0.65f, 0.45f, 0.55f) : new Vector3(0.70f, 0.35f, 0.50f));
                    Color fallbackCol = wc == WasteClass.Biohazard
                        ? new Color(0.66f, 0.33f, 0.97f)
                        : (wc == WasteClass.Medical ? new Color(0.92f, 0.70f, 0.03f) : new Color(0.56f, 0.45f, 0.33f));
                    ApplyTint(trashObj, fallbackCol);
                }

                RiverTrashItem trashItem = trashObj.GetComponent<RiverTrashItem>();
                if (trashItem == null) trashItem = trashObj.AddComponent<RiverTrashItem>();
                trashItem.wasteClass = wc;
                trashItem.trashUnits = 1; // 8 piles x 5 = 40 units seeded at t=0 (spec D: 30-40)

                RiverFlowBuoyancy buoy = trashObj.GetComponent<RiverFlowBuoyancy>();
                if (buoy == null) buoy = trashObj.AddComponent<RiverFlowBuoyancy>();
                // ponytail: map piles are snagged (bob in place, no drift) so the tutorial piles stay in front of spawn.
                buoy.driftDownstream = false;
                if (trashObj.GetComponentInChildren<Collider>(true) == null) trashObj.AddComponent<BoxCollider>();
            }
        }

        private static GameObject AttachPrefabIfPresent(Transform parent, string path, Vector3? worldPos = null, string nameOverride = null)
        {
            GameObject prefab = LoadFirstPrefab(path);
            if (prefab == null)
            {
                Debug.Log("[KALI] Optional prefab not found (greybox/skip): " + path);
                return null;
            }

            GameObject inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
            if (worldPos.HasValue) inst.transform.position = worldPos.Value;
            if (!string.IsNullOrEmpty(nameOverride)) inst.name = nameOverride;
            return inst;
        }

        private static void AttachOnTopIfPresent(Transform parent, string path)
        {
            // Measure the building before instantiating so the attachment does not inflate its own bounds
            bool hasBounds = TryGetLocalBounds(parent.gameObject, out Bounds b);
            GameObject inst = AttachPrefabIfPresent(parent, path);
            if (inst == null) return;

            inst.transform.localPosition = hasBounds
                ? new Vector3(b.center.x, b.max.y + 0.05f, b.center.z)
                : new Vector3(0f, 0.55f, 0f);
        }

        private static void EnsureCollider(GameObject go, bool concaveMesh, bool ensureRootCollider, bool solidRootCollider)
        {
            if (go.GetComponentInChildren<Collider>(true) == null)
            {
                if (concaveMesh)
                {
                    foreach (MeshFilter mf in go.GetComponentsInChildren<MeshFilter>(true))
                    {
                        if (mf.sharedMesh != null && mf.gameObject.GetComponent<Collider>() == null)
                        {
                            mf.gameObject.AddComponent<MeshCollider>().sharedMesh = mf.sharedMesh;
                        }
                    }
                    if (go.GetComponentInChildren<Collider>(true) != null) return;
                }

                AddFittedBoxCollider(go, isTrigger: false);
                return;
            }

            if (ensureRootCollider && go.GetComponent<Collider>() == null)
            {
                AddFittedBoxCollider(go, isTrigger: !solidRootCollider);
            }
        }

        private static void AddFittedBoxCollider(GameObject go, bool isTrigger)
        {
            BoxCollider box = go.AddComponent<BoxCollider>();
            box.isTrigger = isTrigger;
            if (TryGetLocalBounds(go, out Bounds localBounds))
            {
                box.center = localBounds.center;
                box.size = localBounds.size;
            }
        }

        private static bool TryGetLocalBounds(GameObject root, out Bounds localBounds)
        {
            localBounds = new Bounds();
            bool any = false;
            foreach (MeshFilter mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                if (mf.sharedMesh != null) EncapsulateMeshBounds(root.transform, mf.transform, mf.sharedMesh, ref localBounds, ref any);
            }
            foreach (SkinnedMeshRenderer smr in root.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                if (smr.sharedMesh != null) EncapsulateMeshBounds(root.transform, smr.transform, smr.sharedMesh, ref localBounds, ref any);
            }
            return any;
        }

        private static void EncapsulateMeshBounds(Transform root, Transform meshTransform, Mesh mesh, ref Bounds localBounds, ref bool any)
        {
            Bounds mb = mesh.bounds;
            Vector3 min = mb.min;
            Vector3 max = mb.max;
            for (int i = 0; i < 8; i++)
            {
                Vector3 corner = new Vector3((i & 1) == 0 ? min.x : max.x, (i & 2) == 0 ? min.y : max.y, (i & 4) == 0 ? min.z : max.z);
                Vector3 local = root.InverseTransformPoint(meshTransform.TransformPoint(corner));
                if (!any) { localBounds = new Bounds(local, Vector3.zero); any = true; }
                else localBounds.Encapsulate(local);
            }
        }

        private static GameObject FindDescendantByName(Transform parent, string targetName)
        {
            foreach (Transform t in parent.GetComponentsInChildren<Transform>(true))
            {
                if (t.name == targetName) return t.gameObject;
            }
            return null;
        }

        private static GameObject CreateGroup(string name, Transform parent)
        {
            GameObject g = new GameObject(name);
            g.transform.SetParent(parent);
            return g;
        }

        private static uint Fnv1aHash(string text)
        {
            unchecked
            {
                uint hash = 2166136261u;
                if (!string.IsNullOrEmpty(text))
                {
                    for (int i = 0; i < text.Length; i++)
                    {
                        hash ^= text[i];
                        hash *= 16777619u;
                    }
                }
                return hash;
            }
        }

        private static void ApplyTint(GameObject go, Color col)
        {
            Renderer r = go.GetComponent<Renderer>();
            if (r == null) return;
            if (activeAssetCache != null)
            {
                r.sharedMaterial = KaliMapBackdropBuilder.GetSharedTintMaterial(activeAssetCache, col);
                return;
            }
            Shader sh = Shader.Find("Universal Render Pipeline/Lit");
            if (sh == null) sh = Shader.Find("Standard");
            r.sharedMaterial = new Material(sh) { color = col };
        }
    }
}
#endif
