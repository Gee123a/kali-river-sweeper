#if UNITY_EDITOR
using System;
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
            BuildGreyboxGroundAndRiver(terrainGroup.transform);
            SetupLightingRig(lightingGroup.transform);

            foreach (MapItem item in data.items)
            {
                SpawnItem(item, buildingsGroup.transform, trashGroup.transform, infraGroup.transform, gunungGroup.transform, root.transform);
            }

            Debug.Log($"[KALI] Imported {data.items.Length} objects from {path} into _KALI_World.");
        }

        private static void BuildGreyboxGroundAndRiver(Transform parent)
        {
            GameObject ground = GameObject.CreatePrimitive(PrimitiveType.Cube);
            ground.name = "Ground_Daratan";
            ground.transform.SetParent(parent);
            ground.transform.position = new Vector3(0f, -0.5f, 0f);
            ground.transform.localScale = new Vector3(RiverMath.WorldW * RiverMath.MapScale, 1f, RiverMath.WorldH * RiverMath.MapScale);
            ApplyTint(ground, new Color(0.24f, 0.31f, 0.22f));

            GameObject river = GameObject.CreatePrimitive(PrimitiveType.Plane);
            river.name = "River_WaterSurface";
            river.transform.SetParent(parent);
            river.transform.position = new Vector3(0f, 0.05f, -5f);
            river.transform.localScale = new Vector3(2.4f, 1f, 16f);
            ApplyTint(river, new Color(0.24f, 0.20f, 0.14f));
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
            "PF_Trash_BatangPisang"
        };

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
                // Fallback directional light if rig is not built yet
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
                player.transform.position = RiverMath.ToWorld3D(item.x, item.y, 1.0f);
                player.transform.rotation = Quaternion.Euler(0f, 180f, 0f); // Look North (-Z) toward Gunung Sampah
                CharacterController cc = player.AddComponent<CharacterController>();
                cc.height = 1.8f;
                cc.radius = 0.4f;
                player.AddComponent<KaliPlayerController>();

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

            go.transform.SetParent(targetParent);
            go.transform.position = RiverMath.ToWorld3D(item.x, item.y, sy * 0.5f);
            go.transform.rotation = Quaternion.Euler(0f, item.rot, 0f);
            go.transform.localScale = new Vector3(sx, sy, sz);

            if (ColorUtility.TryParseHtmlString(item.color, out Color parsed)) ApplyTint(go, parsed);

            // Optional props attachment (Lanterns & Beacons)
            if (item.type == "warung")
            {
                AttachPropIfPresent(go.transform, "Assets/_Project/Lighting/Prefabs/PF_Lantern_Warung.prefab", new Vector3(0f, sy * 0.5f + 0.5f, 0f));
            }
            else if (item.type == "sluice_gate")
            {
                AttachPropIfPresent(go.transform, "Assets/_Project/Lighting/Prefabs/PF_WarningBeacon_PintuAir.prefab", new Vector3(0f, sy * 0.5f + 0.8f, 0f));
            }
        }

        private static void SpawnTrashCluster(MapItem item, Transform parent)
        {
            Vector3 center = RiverMath.ToWorld3D(item.x, item.y, 0f);
            int count = 4;
            bool spawnedRealProp = false;

            for (int i = 0; i < count; i++)
            {
                string randomName = TrashPrefabNames[(i + Mathf.Abs(item.name.GetHashCode())) % TrashPrefabNames.Length];
                string prefabPath = $"Assets/_Project/Props/Trash/Prefabs/{randomName}.prefab";
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);

                if (prefab != null)
                {
                    GameObject trashObj = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
                    Vector3 offset = new Vector3(UnityEngine.Random.Range(-2f, 2f), 0f, UnityEngine.Random.Range(-2f, 2f));
                    trashObj.transform.position = center + offset;
                    trashObj.transform.rotation = Quaternion.Euler(0f, UnityEngine.Random.Range(0f, 360f), 0f);
                    spawnedRealProp = true;
                }
            }

            if (!spawnedRealProp)
            {
                // Fallback greybox if prefabs not built yet
                GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                go.name = item.name;
                float sx = Mathf.Max(1.5f, item.w * RiverMath.MapScale);
                float sz = Mathf.Max(1.5f, item.h * RiverMath.MapScale);
                float sy = 0.5f;
                go.transform.SetParent(parent);
                go.transform.position = center;
                go.transform.localScale = new Vector3(sx, sy, sz);
                if (ColorUtility.TryParseHtmlString(item.color, out Color parsed)) ApplyTint(go, parsed);
                go.AddComponent<RiverFlowBuoyancy>();
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
