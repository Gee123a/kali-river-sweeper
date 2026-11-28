using System;
using System.Collections.Generic;
using System.IO;
using KaliRiverSweeper.Env;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace KaliRiverSweeper.EnvEditor
{
    /// <summary>
    /// Wesley (Environment): KALI > Environment > Build Lamps, Plants & Kampung Dressing.
    /// 1. materials for SM_Env_Lampu.fbx + SM_Env_Vegetasi.fbx (SG_EnvWeathered / URP Lit cutout)
    /// 2. prefabs PF_Env_LampuJalan, PF_Env_LampuBohlam and one PF_Env_&lt;plant&gt; per plant mesh
    /// 3. bohlam wall lamps inside every station / building prefab (spots from env_dressing.json)
    /// 4. PF_Env_KampungDressing: every street lamp and plant laid out by blender/wesley_env/dressing.py
    /// Re-running is safe: assets are updated in place (GUIDs kept), old lamps are replaced.
    /// </summary>
    public static class EnvDressingBuilder
    {
        private const string Env = "Assets/_Project/Environment/";
        private const string Mats = Env + "Materials/";
        private const string Tex = Env + "Textures/";
        private const string Prefabs = Env + "Prefabs/";
        private const string LampuFbx = Env + "Meshes/SM_Env_Lampu.fbx";
        private const string VegFbx = Env + "Meshes/SM_Env_Vegetasi.fbx";
        private const string LayoutJson = Env + "Data/env_dressing.json";
        private const string WeatheredShader = "Shader Graphs/SG_EnvWeathered";

        // yellow kampung light (Wesley: "lampu cahayanya kuning")
        private static readonly Color LightYellow = new Color(1f, 0.80f, 0.36f);
        private static readonly Color GlowYellow = new Color(1f, 0.78f, 0.22f);
        private static readonly Vector3 LanternGlass = new Vector3(1.05f, 2.265f, 0f);
        private static readonly Vector3 BulbCentre = new Vector3(0.44f, -0.19f, 0f);

        private static readonly string[] Plants =
            { "PohonPisang", "PohonKelapa", "PohonKetapang", "Bambu", "Semak", "Rumput", "Alang", "RumputKering", "Batu" };

        [MenuItem("KALI/Environment/Build Lamps, Plants & Kampung Dressing")]
        public static void BuildAll()
        {
            BuildMaterials();
            RemapFbx(LampuFbx);
            RemapFbx(VegFbx);
            var lampuJalan = BuildLampuJalan();
            var bohlam = BuildBohlam();
            var plants = new Dictionary<string, GameObject>();
            foreach (var p in Plants) plants[p] = BuildPlant(p);
            var layout = JsonUtility.FromJson<Layout>(File.ReadAllText(LayoutJson));
            int walls = BuildWallLamps(layout, bohlam);
            BuildDressing(layout, lampuJalan, plants);
            AssetDatabase.SaveAssets();
            Debug.Log($"[EnvDressingBuilder] {layout.lamps.Length} street lamps, {layout.plants.Length} plants, {walls} wall lamps.");
        }

        // ---------------- materials ----------------

        private static void BuildMaterials()
        {
            ConfigureCardTextures("T_Env_DaunPisang", "T_Env_DaunKelapa", "T_Env_DaunRimbun", "T_Env_RumputAlang");
            Weathered("M_Env_BesiKarat", "T_Env_CatKarat", new Color(0.55f, 0.30f, 0.20f), 0.25f, 0.1f);
            Weathered("M_Env_KulitPohon", "T_Env_KulitPohon", new Color(0.56f, 0.45f, 0.35f), 0.12f, 0.35f);
            Weathered("M_Env_BatangPisang", "T_Env_KulitPohon", new Color(0.66f, 0.72f, 0.42f), 0.2f, 0.15f);
            Weathered("M_Env_DaunRimbunPadat", "T_Env_DaunRimbun", new Color(0.82f, 0.86f, 0.8f), 0.18f, 0f);
            Weathered("M_Env_Bambu", "T_Env_Bambu", Color.white, 0.35f, 0.1f);
            Weathered("M_Env_BatuSungai", "T_Env_BetonKotor", new Color(0.52f, 0.50f, 0.46f), 0.2f, 0.55f);
            Cutout("M_Env_DaunPisang", "T_Env_DaunPisang", Color.white);
            Cutout("M_Env_DaunPisangKering", "T_Env_DaunPisang", new Color(0.92f, 0.62f, 0.34f));
            Cutout("M_Env_DaunKelapa", "T_Env_DaunKelapa", Color.white);
            Cutout("M_Env_DaunRimbun", "T_Env_DaunRimbun", Color.white);
            Cutout("M_Env_Rumput", "T_Env_RumputAlang", Color.white);
            Cutout("M_Env_RumputKering", "T_Env_RumputAlang", new Color(0.92f, 0.78f, 0.52f));

            var kaca = LoadOrCreate("M_Env_LampuKaca", Shader.Find("Universal Render Pipeline/Lit"));
            kaca.SetColor("_BaseColor", new Color(1f, 0.9f, 0.6f));
            kaca.SetFloat("_Smoothness", 0.8f);
            kaca.EnableKeyword("_EMISSION");
            kaca.SetColor("_EmissionColor", Color.black);          // EnvNightLamp drives it per lamp
            kaca.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            EditorUtility.SetDirty(kaca);

            var pool = LoadOrCreate("M_Env_LightPool", Shader.Find("KALI/Env/LightPool"));
            pool.SetColor("_Color", GlowYellow);
            pool.SetFloat("_Intensity", 1.0f);
            pool.SetFloat("_Falloff", 2.2f);
            EditorUtility.SetDirty(pool);
        }

        private static Material LoadOrCreate(string name, Shader shader)
        {
            string path = Mats + name + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                m = new Material(shader) { name = name };
                AssetDatabase.CreateAsset(m, path);
            }
            else if (m.shader != shader)
            {
                m.shader = shader;
            }
            return m;
        }

        private static void Weathered(string name, string tex, Color tint, float smooth, float moss)
        {
            var m = LoadOrCreate(name, Shader.Find(WeatheredShader));
            m.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(Tex + tex + ".png"));
            m.SetColor("_BaseColor", tint);
            m.SetFloat("_Smoothness", smooth);
            m.SetFloat("_MossAmount", moss);
            m.SetColor("_MossColor", new Color(0.25f, 0.29f, 0.16f));
            m.SetFloat("_NoiseScale", 3f);
            m.SetFloat("_WetHeight", 1f);
            m.SetFloat("_WetEdge", 0.35f);
            m.SetFloat("_WetDarken", 0.42f);
            m.SetFloat("_WetSmoothness", 0.7f);
            EditorUtility.SetDirty(m);
        }

        private static void Cutout(string name, string tex, Color tint)
        {
            var m = LoadOrCreate(name, Shader.Find("Universal Render Pipeline/Lit"));
            m.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(Tex + tex + ".png"));
            m.SetColor("_BaseColor", tint);
            m.SetFloat("_Smoothness", 0.12f);
            m.SetFloat("_AlphaClip", 1f);
            m.SetFloat("_Cutoff", 0.45f);
            m.EnableKeyword("_ALPHATEST_ON");
            m.SetFloat("_Cull", (float)CullMode.Off);              // leaves are seen from both sides
            m.doubleSidedGI = true;
            m.renderQueue = (int)RenderQueue.AlphaTest;
            m.SetOverrideTag("RenderType", "TransparentCutout");
            EditorUtility.SetDirty(m);
        }

        private static void ConfigureCardTextures(params string[] names)
        {
            foreach (var n in names)
            {
                var ti = (TextureImporter)AssetImporter.GetAtPath(Tex + n + ".png");
                if (ti == null) continue;
                ti.alphaIsTransparency = true;
                ti.mipMapsPreserveCoverage = true;                 // leaves don't thin out in the distance
                ti.alphaTestReferenceValue = 0.45f;
                ti.wrapMode = TextureWrapMode.Clamp;
                ti.SaveAndReimport();
            }
        }

        private static void RemapFbx(string fbx)
        {
            var mi = (ModelImporter)AssetImporter.GetAtPath(fbx);
            mi.importNormals = ModelImporterNormals.Import;        // keep the bent foliage normals
            mi.addCollider = false;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(fbx))
            {
                if (o is not Material src) continue;
                var dst = AssetDatabase.LoadAssetAtPath<Material>(Mats + src.name + ".mat");
                if (dst != null) mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), src.name), dst);
            }
            mi.SaveAndReimport();
        }

        // ---------------- prefabs ----------------

        private static GameObject MeshObject(string fbx, string meshName, string goName)
        {
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(fbx);
            var src = model.transform.Find(meshName);
            var go = new GameObject(goName);
            go.AddComponent<MeshFilter>().sharedMesh = src.GetComponent<MeshFilter>().sharedMesh;
            go.AddComponent<MeshRenderer>().sharedMaterials = src.GetComponent<MeshRenderer>().sharedMaterials;
            return go;
        }

        private static Light AddLight(Transform parent, Vector3 pos, float range, float intensity)
        {
            var go = new GameObject("Lampu");
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            var l = go.AddComponent<Light>();
            l.type = LightType.Point;
            l.color = LightYellow;
            l.range = range;
            l.intensity = intensity;
            l.shadows = LightShadows.None;
            l.renderMode = LightRenderMode.Auto;
            l.lightmapBakeType = LightmapBakeType.Realtime;
            return l;
        }

        private static MeshRenderer AddPool(Transform parent, Vector3 pos, float size)
        {
            var go = MeshObject(LampuFbx, "SM_Env_LampuPool", "CahayaTanah");
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = new Vector3(size, 1f, size);
            var r = go.GetComponent<MeshRenderer>();
            r.sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>(Mats + "M_Env_LightPool.mat");
            r.shadowCastingMode = ShadowCastingMode.Off;
            r.receiveShadows = false;
            r.lightProbeUsage = LightProbeUsage.Off;
            return r;
        }

        private static GameObject Save(GameObject root, string name)
        {
            var asset = PrefabUtility.SaveAsPrefabAsset(root, Prefabs + name + ".prefab");
            UnityEngine.Object.DestroyImmediate(root);
            return asset;
        }

        private static GameObject BuildLampuJalan()
        {
            var root = new GameObject("PF_Env_LampuJalan");
            var mesh = MeshObject(LampuFbx, "SM_Env_LampuJalan", "SM_Env_LampuJalan");
            mesh.transform.SetParent(root.transform, false);
            var light = AddLight(root.transform, LanternGlass + Vector3.down * 0.05f, 11f, 2.6f);
            var pool = AddPool(root.transform, new Vector3(LanternGlass.x * 0.6f, 0.04f, 0f), 9f);
            var col = root.AddComponent<CapsuleCollider>();
            col.center = new Vector3(0f, 1.8f, 0f);
            col.height = 3.7f;
            col.radius = 0.22f;
            var lamp = root.AddComponent<EnvNightLamp>();
            lamp.lamp = light;
            lamp.onIntensity = 2.6f;
            lamp.glowColor = GlowYellow;
            lamp.glowEmission = 5f;
            lamp.glowRenderers = new Renderer[] { mesh.GetComponent<MeshRenderer>(), pool };
            return Save(root, "PF_Env_LampuJalan");
        }

        private static GameObject BuildBohlam()
        {
            var root = new GameObject("PF_Env_LampuBohlam");
            var mesh = MeshObject(LampuFbx, "SM_Env_LampuBohlam", "SM_Env_LampuBohlam");
            mesh.transform.SetParent(root.transform, false);
            mesh.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
            var light = AddLight(root.transform, BulbCentre + Vector3.down * 0.06f, 7.5f, 1.8f);
            var lamp = root.AddComponent<EnvNightLamp>();
            lamp.lamp = light;
            lamp.onIntensity = 1.8f;
            lamp.glowColor = GlowYellow;
            lamp.glowEmission = 6f;
            lamp.glowRenderers = new Renderer[] { mesh.GetComponent<MeshRenderer>() };
            return Save(root, "PF_Env_LampuBohlam");
        }

        private static GameObject BuildPlant(string kind)
        {
            var root = MeshObject(VegFbx, "SM_Env_" + kind, "PF_Env_" + kind);
            var r = root.GetComponent<MeshRenderer>();
            bool small = kind is "Rumput" or "Alang" or "RumputKering";
            r.shadowCastingMode = small ? ShadowCastingMode.Off : ShadowCastingMode.On;
            switch (kind)
            {
                case "PohonKetapang": Trunk(root, 0.32f, 6f, 0f); break;
                case "PohonKelapa": Trunk(root, 0.25f, 8f, 0.7f); break;
                case "PohonPisang": Trunk(root, 0.2f, 3f, 0f); break;
                case "Bambu": Trunk(root, 0.45f, 4f, 0f); break;
                case "Batu":
                    var mc = root.AddComponent<MeshCollider>();
                    mc.sharedMesh = root.GetComponent<MeshFilter>().sharedMesh;
                    mc.convex = true;
                    break;
            }
            return Save(root, "PF_Env_" + kind);
        }

        private static void Trunk(GameObject go, float radius, float height, float lean)
        {
            var c = go.AddComponent<CapsuleCollider>();
            c.radius = radius;
            c.height = height;
            c.center = new Vector3(lean, height * 0.5f - 0.2f, 0f);
        }

        // ---------------- wall lamps inside the building prefabs ----------------

        private static int BuildWallLamps(Layout layout, GameObject bohlam)
        {
            int count = 0;
            foreach (var w in layout.wall_lamps)
            {
                string path = Prefabs + w.prefab + ".prefab";
                if (AssetDatabase.LoadAssetAtPath<GameObject>(path) == null)
                {
                    Debug.LogWarning($"[EnvDressingBuilder] {path} missing, skipped.");
                    continue;
                }
                var root = PrefabUtility.LoadPrefabContents(path);
                for (int i = root.transform.childCount - 1; i >= 0; i--)
                {
                    var c = root.transform.GetChild(i);
                    if (c.name.StartsWith("LampuBohlam_") || c.name.StartsWith("CahayaTanah_")) UnityEngine.Object.DestroyImmediate(c.gameObject);
                }
                float ground = w.prefab == "PF_Env_RumahPanggung" ? 2.02f : 0.24f;   // stilt house: veranda deck
                for (int i = 0; i < w.spots.Length; i++)
                {
                    var s = w.spots[i];
                    var inst = (GameObject)PrefabUtility.InstantiatePrefab(bohlam, root.transform);
                    inst.name = $"LampuBohlam_{i + 1}";
                    inst.transform.localPosition = new Vector3(s.p[0], s.p[1], s.p[2]);
                    inst.transform.localRotation = Quaternion.Euler(0f, s.yaw, 0f);
                    Vector3 under = inst.transform.localPosition + inst.transform.localRotation * new Vector3(BulbCentre.x + 0.6f, 0f, 0f);
                    var pool = AddPool(root.transform, new Vector3(under.x, ground, under.z), 6f);
                    pool.name = $"CahayaTanah_{i + 1}";
                    var lamp = inst.GetComponent<EnvNightLamp>();
                    var glow = new List<Renderer>(lamp.glowRenderers) { pool };
                    lamp.glowRenderers = glow.ToArray();
                    count++;
                }
                PrefabUtility.SaveAsPrefabAsset(root, path);
                PrefabUtility.UnloadPrefabContents(root);
            }
            return count;
        }

        // ---------------- PF_Env_KampungDressing ----------------

        private static void BuildDressing(Layout layout, GameObject lampuJalan, Dictionary<string, GameObject> plants)
        {
            var root = new GameObject("PF_Env_KampungDressing");
            var lampParent = new GameObject("LampuJalan").transform;
            lampParent.SetParent(root.transform, false);
            for (int i = 0; i < layout.lamps.Length; i++)
            {
                var l = layout.lamps[i];
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(lampuJalan, lampParent);
                inst.name = $"LampuJalan_{i + 1:00}";
                inst.transform.SetPositionAndRotation(new Vector3(l.p[0], l.p[1], l.p[2]), Quaternion.Euler(0f, l.yaw, 0f));
            }
            var groups = new Dictionary<string, Transform>();
            foreach (var p in layout.plants)
            {
                if (!groups.TryGetValue(p.m, out var g))
                {
                    g = new GameObject(p.m).transform;
                    g.SetParent(root.transform, false);
                    groups[p.m] = g;
                }
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(plants[p.m], g);
                inst.transform.SetPositionAndRotation(new Vector3(p.p[0], p.p[1], p.p[2]), Quaternion.Euler(0f, p.yaw, 0f));
                inst.transform.localScale = Vector3.one * p.s;
                GameObjectUtility.SetStaticEditorFlags(inst, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic);
            }
            Save(root, "PF_Env_KampungDressing");
        }

        // ---------------- env_dressing.json ----------------

        [Serializable] private class Lamp { public float[] p; public float yaw; }
        [Serializable] private class PlantItem { public string m; public float[] p; public float yaw; public float s; }
        [Serializable] private class Spot { public float[] p; public float yaw; }
        [Serializable] private class Wall { public string prefab; public Spot[] spots; }
        [Serializable] private class Layout { public Lamp[] lamps; public PlantItem[] plants; public Wall[] wall_lamps; }
    }
}
