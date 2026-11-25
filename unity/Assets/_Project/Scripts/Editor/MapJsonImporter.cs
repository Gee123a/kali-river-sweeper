#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using KaliRiverSweeper.Core;
using KaliRiverSweeper.Player;

namespace KaliRiverSweeper.Editor
{
    public static class MapJsonImporter
    {
        private const string DefaultMapPath = "Assets/_Project/Data/kali-river-map.json";
        private const float BankTopY = 1.40f;
        private const float RiverbedTopY = -2.0f;

        [Serializable]
        private class MapData
        {
            public MapItem[] items;
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
        }

        private static readonly string[] TrashPrefabNames = new[]
        {
            "PF_Trash_SandalSwallow",
            "PF_Trash_AquaBottle_600ml",
            "PF_Trash_AquaGalon_19L",
            "PF_Trash_PopMieCup",
            "PF_Trash_KresekBag",
            "PF_Trash_KasurKapuk",
            "PF_Trash_BanBekas",
            "PF_Trash_EcengGondok",
            "PF_Trash_BatangPisang",
            "PF_Trash_MedicalBag",
            "PF_Trash_SyringeBox"
        };

        private static readonly string[] NormalTrashNames = new[]
        {
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

        [MenuItem("KALI/Load Default Purpose-Built Map")]
        public static void LoadDefaultMap()
        {
            ImportFromPath(DefaultMapPath);
        }

        [MenuItem("KALI/Import Map JSON to Scene...")]
        public static void ImportViaDialog()
        {
            string path = EditorUtility.OpenFilePanel("Select KALI Map JSON", Application.dataPath, "json");
            if (!string.IsNullOrEmpty(path)) ImportFromPath(path);
        }

        private static void ImportFromPath(string path)
        {
            if (!File.Exists(path))
            {
                Debug.LogError($"[KALI] Map JSON not found at: {path}");
                return;
            }

            MapData data = JsonUtility.FromJson<MapData>(File.ReadAllText(path));
            if (data == null || data.items == null)
            {
                Debug.LogError("[KALI] Failed to parse Map JSON.");
                return;
            }

            GameObject existing = GameObject.Find("_KALI_World");
            if (existing != null) UnityEngine.Object.DestroyImmediate(existing);

            GameObject root = new GameObject("_KALI_World");
            GameObject terrainGroup = CreateGroup("Terrain", root.transform);
            GameObject buildingsGroup = CreateGroup("Buildings", root.transform);
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

            BuildSplitBanksAndRiver(terrainGroup.transform);
            SetupLightingRig(lightingGroup.transform);

            foreach (MapItem item in data.items)
            {
                SpawnItem(item, buildingsGroup.transform, trashGroup.transform, infraGroup.transform, gunungGroup.transform, root.transform);
            }

            Debug.Log($"[KALI] Imported {data.items.Length} objects from {path} into _KALI_World.");
        }

        private static GameObject[] LoadTrashPrefabPool(string[] names)
        {
            List<GameObject> list = new List<GameObject>();
            foreach (string n in names)
            {
                GameObject p = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/_Project/Props/Trash/Prefabs/{n}.prefab");
                if (p != null) list.Add(p);
            }
            return list.ToArray();
        }

        /// <summary>
        /// Splits Ground_Daratan into West & East riverbank segments matching RiverMath S-curve,
        /// leaving the central river channel open down to -2.0m for boats and water flow.
        /// </summary>
        private static void BuildSplitBanksAndRiver(Transform parent)
        {
            float worldWidthM = RiverMath.WorldW * RiverMath.MapScale;   // 130m
            float worldLenM = RiverMath.WorldH * RiverMath.MapScale;     // 180m
            float halfWorldX = worldWidthM * 0.5f;                       // 65m
            float bankThickness = BankTopY - RiverbedTopY;               // 3.4m
            float bankCenterY = RiverbedTopY + bankThickness * 0.5f;     // -0.3m

            // 1. Sunken riverbed floor at Y = -2.0m
            GameObject riverbed = GameObject.CreatePrimitive(PrimitiveType.Cube);
            riverbed.name = "Riverbed_Floor";
            riverbed.transform.SetParent(parent);
            riverbed.transform.position = new Vector3(0f, RiverbedTopY - 0.5f, 0f);
            riverbed.transform.localScale = new Vector3(worldWidthM, 1f, worldLenM);
            ApplyTint(riverbed, new Color(0.18f, 0.15f, 0.11f));

            // 2. Segmented West & East embankments leaving open S-curve water channel
            const int slices = 18;
            float sliceLenM = worldLenM / slices; // 10m per slice
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

                float eastEdge = cxWorld + hwWorld;
                float eastWidth = Mathf.Max(2f, halfWorldX - eastEdge);
                GameObject eastBank = GameObject.CreatePrimitive(PrimitiveType.Cube);
                eastBank.name = $"Ground_Daratan_East_{i:00}";
                eastBank.transform.SetParent(parent);
                eastBank.transform.position = new Vector3(eastEdge + eastWidth * 0.5f, bankCenterY, zCenter);
                eastBank.transform.localScale = new Vector3(eastWidth, bankThickness, sliceLenM + 0.15f);
                ApplyTint(eastBank, bankColor);
            }

            // 3. Water Surface Plane (collider disabled so boats/players pass cleanly through water)
            GameObject river = GameObject.CreatePrimitive(PrimitiveType.Plane);
            river.name = "River_WaterSurface";
            river.transform.SetParent(parent);
            river.transform.position = new Vector3(0f, 0.0f, 0f);
            river.transform.localScale = new Vector3(worldWidthM * 0.1f, 1f, worldLenM * 0.1f);
            Collider waterCol = river.GetComponent<Collider>();
            if (waterCol != null) UnityEngine.Object.DestroyImmediate(waterCol);
            ApplyTint(river, new Color(0.24f, 0.20f, 0.14f, 0.85f));
            river.AddComponent<RiverWaterSurfaceFollower>();
        }

        private static void SetupLightingRig(Transform parent)
        {
            const string rigPath = "Assets/_Project/Lighting/Prefabs/PF_LightingRig.prefab";
            GameObject rigPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(rigPath);
            if (rigPrefab != null)
            {
                GameObject rig = (GameObject)PrefabUtility.InstantiatePrefab(rigPrefab, parent);
                rig.name = "PF_LightingRig";
                Debug.Log("[KALI] Successfully instantiated JC's PF_LightingRig.");
            }
            else
            {
                GameObject sun = new GameObject("Directional Light (Fallback)");
                sun.transform.SetParent(parent);
                sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
                Light l = sun.AddComponent<Light>();
                l.type = LightType.Directional;
                l.color = new Color(1f, 0.95f, 0.84f);
                l.intensity = 1.8f;
                l.shadows = LightShadows.Soft;
            }
        }

        private static void SpawnItem(MapItem item, Transform buildings, Transform trash, Transform infra, Transform gunung, Transform root)
        {
            if (item.type == "spawn")
            {
                GameObject player = new GameObject("Player_Rig");
                player.transform.SetParent(root);
                player.transform.position = RiverMath.ToWorld3D(item.x, item.y, BankTopY + 1.0f);
                player.transform.rotation = Quaternion.Euler(0f, 180f, 0f); // Look North (-Z) toward Gunung Sampah
                CharacterController cc = player.AddComponent<CharacterController>();
                cc.height = 1.8f;
                cc.radius = 0.4f;
                KaliPlayerController ctrl = player.AddComponent<KaliPlayerController>();

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

                GameObject socket = new GameObject("ToolSocket");
                socket.transform.SetParent(mainCam.transform);
                socket.transform.localPosition = new Vector3(0.38f, -0.32f, 0.65f);
                socket.transform.localRotation = Quaternion.identity;
                ctrl.toolSocket = socket.transform;

                var allTools = ToolCatalog.AllTools;
                ctrl.toolPrefabs = new GameObject[allTools.Count];
                for (int i = 0; i < allTools.Count; i++)
                {
                    ctrl.toolPrefabs[i] = AssetDatabase.LoadAssetAtPath<GameObject>(
                        $"Assets/_Project/Props/Tools/Prefabs/{allTools[i].PrefabName}.prefab");
                }
                return;
            }

            if (item.type == "trash_pile")
            {
                SpawnTrashCluster(item, trash);
                return;
            }

            if (item.type == "trash_boom")
            {
                const string boomPath = "Assets/_Project/Props/Equipment/Prefabs/PF_Prop_TrashBoomSegment.prefab";
                GameObject boomPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(boomPath);
                if (boomPrefab != null)
                {
                    GameObject boom = (GameObject)PrefabUtility.InstantiatePrefab(boomPrefab, infra);
                    boom.name = item.name;
                    boom.transform.position = RiverMath.ToWorld3D(item.x, item.y, 0f);
                    boom.transform.rotation = Quaternion.Euler(0f, item.rot, 0f);
                    return;
                }
            }

            if (item.type == "jembatan")
            {
                BuildElevatedBridge(item, infra);
                return;
            }

            if (item.type == "sluice_gate")
            {
                BuildSluiceGateAndPileZone(item, infra);
                return;
            }

            PrimitiveType prim = item.type == "pohon" ? PrimitiveType.Cylinder : PrimitiveType.Cube;
            GameObject go = GameObject.CreatePrimitive(prim);
            go.name = item.name;

            float sx = Mathf.Max(1.5f, item.w * RiverMath.MapScale);
            float sz = Mathf.Max(1.5f, item.h * RiverMath.MapScale);
            float sy = Mathf.Max(0.8f, item.elev * RiverMath.MapScale);

            Transform targetParent = item.type switch
            {
                "gunung_node" => gunung,
                "dermaga" or "trash_boom" or "excavator" or "interceptor" or "sorting_yard" => infra,
                _ => buildings
            };

            bool isWaterFeature = item.type == "gunung_node" || item.type == "dermaga" ||
                                  item.type == "trash_boom" || item.type == "interceptor";
            float groundY = isWaterFeature ? 0f : BankTopY;

            go.transform.SetParent(targetParent);
            go.transform.position = RiverMath.ToWorld3D(item.x, item.y, groundY + sy * 0.5f);
            go.transform.rotation = Quaternion.Euler(0f, item.rot, 0f);
            go.transform.localScale = new Vector3(sx, sy, sz);

            if (ColorUtility.TryParseHtmlString(item.color, out Color parsed)) ApplyTint(go, parsed);

            if (item.type == "gunung_node")
            {
                GunungNodeController gCtrl = go.AddComponent<GunungNodeController>();
                gCtrl.scaleFromCenterPrimitive = true;
            }

            if (item.type == "warung")
            {
                AttachPropIfPresent(go.transform, "Assets/_Project/Lighting/Prefabs/PF_Lantern_Warung.prefab", new Vector3(0f, 0.55f, 0f));
            }
        }

        private static void BuildElevatedBridge(MapItem item, Transform parent)
        {
            float sx = Mathf.Max(12f, item.w * RiverMath.MapScale);
            float sz = Mathf.Max(4f, item.h * RiverMath.MapScale);
            Vector3 center = RiverMath.ToWorld3D(item.x, item.y, 0f);

            GameObject bridgeRoot = new GameObject(item.name);
            bridgeRoot.transform.SetParent(parent);
            bridgeRoot.transform.position = center;
            bridgeRoot.transform.rotation = Quaternion.Euler(0f, item.rot, 0f);

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

            // Outer piers leaving wide central channel unobstructed for boats
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

            // Approach ramps down to West & East riverbanks (+1.4m)
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
        }

        private static void BuildSluiceGateAndPileZone(MapItem item, Transform parent)
        {
            float sx = Mathf.Max(16f, item.w * RiverMath.MapScale);
            float sz = Mathf.Max(3f, item.h * RiverMath.MapScale);
            float sy = Mathf.Max(4f, item.elev * RiverMath.MapScale);
            Vector3 center = RiverMath.ToWorld3D(item.x, item.y, 0f);

            GameObject sluiceRoot = GameObject.CreatePrimitive(PrimitiveType.Cube);
            sluiceRoot.name = item.name;
            sluiceRoot.transform.SetParent(parent);
            sluiceRoot.transform.position = new Vector3(center.x, sy * 0.5f, center.z);
            sluiceRoot.transform.rotation = Quaternion.Euler(0f, item.rot, 0f);
            sluiceRoot.transform.localScale = new Vector3(sx, sy, sz);
            if (ColorUtility.TryParseHtmlString(item.color, out Color parsed)) ApplyTint(sluiceRoot, parsed);

            AttachPropIfPresent(sluiceRoot.transform, "Assets/_Project/Lighting/Prefabs/PF_WarningBeacon_PintuAir.prefab", new Vector3(0f, 0.55f, 0f));

            // Scoopable barrier pile zone just upstream (-Z) of downstream Pintu Air
            GameObject pileZone = GameObject.CreatePrimitive(PrimitiveType.Cube);
            pileZone.name = "PintuAirPile_Zone";
            pileZone.transform.SetParent(parent);
            pileZone.transform.position = new Vector3(center.x, 0.25f, center.z - 7.5f);
            pileZone.transform.localScale = new Vector3(sx * 0.55f, 1.2f, 4.5f);
            BoxCollider bc = pileZone.GetComponent<BoxCollider>();
            if (bc != null) bc.isTrigger = true;
            ApplyTint(pileZone, new Color(0.47f, 0.35f, 0.24f));
        }

        private static void SpawnTrashCluster(MapItem item, Transform parent)
        {
            Vector3 center = RiverMath.ToWorld3D(item.x, item.y, 0f);
            int count = 5;

            for (int i = 0; i < count; i++)
            {
                // Ensure each cluster guarantees Normal + Medical + Biohazard variety
                WasteClass wc = i == 3 ? WasteClass.Medical : (i == 4 ? WasteClass.Biohazard : WasteClass.Normal);
                string prefabName = wc switch
                {
                    WasteClass.Medical => MedicalTrashNames[(i + Mathf.Abs(item.name.GetHashCode())) % MedicalTrashNames.Length],
                    WasteClass.Biohazard => BiohazardTrashNames[(i + Mathf.Abs(item.name.GetHashCode())) % BiohazardTrashNames.Length],
                    _ => NormalTrashNames[(i + Mathf.Abs(item.name.GetHashCode())) % NormalTrashNames.Length]
                };

                string prefabPath = $"Assets/_Project/Props/Trash/Prefabs/{prefabName}.prefab";
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);

                // Also verify against TrashPrefabNames contract list
                if (prefab == null && wc == WasteClass.Normal)
                {
                    string alt = TrashPrefabNames[(i + Mathf.Abs(item.name.GetHashCode())) % TrashPrefabNames.Length];
                    prefab = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/_Project/Props/Trash/Prefabs/{alt}.prefab");
                }

                Vector3 offset = new Vector3(UnityEngine.Random.Range(-2.2f, 2.2f), 0f, UnityEngine.Random.Range(-2.2f, 2.2f));
                GameObject trashObj;
                if (prefab != null)
                {
                    trashObj = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
                    trashObj.transform.position = center + offset;
                    trashObj.transform.rotation = Quaternion.Euler(0f, UnityEngine.Random.Range(0f, 360f), 0f);
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

                if (trashObj.GetComponent<RiverFlowBuoyancy>() == null)
                {
                    trashObj.AddComponent<RiverFlowBuoyancy>();
                }
                if (trashObj.GetComponent<Collider>() == null)
                {
                    trashObj.AddComponent<BoxCollider>();
                }
            }
        }

        private static void AttachPropIfPresent(Transform parent, string path, Vector3 localPos)
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (prefab != null)
            {
                GameObject inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
                inst.transform.localPosition = localPos;
            }
        }

        private static GameObject CreateGroup(string name, Transform parent)
        {
            GameObject g = new GameObject(name);
            g.transform.SetParent(parent);
            return g;
        }

        private static void ApplyTint(GameObject go, Color col)
        {
            Renderer r = go.GetComponent<Renderer>();
            if (r == null) return;
            Shader sh = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            Material mat = new Material(sh) { color = col };
            r.sharedMaterial = mat;
        }
    }
}
#endif
