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
    /// 4. PF_Env_QuestLandmarks: Priority 0 quest landmarks (Tangga Cuci, Tiang Nyangkut, warung stalls,
    ///    Pos Ronda) + wayfinding signposts, positions from env_dressing.json
    /// 5. PF_Env_TandaLayanan: floor mark + post sign at every station service point (Core Mechanics v2,
    ///    spec A); EnvServicePointMarks snaps them onto Ivan's "&lt;Station&gt;_ServicePoint" triggers
    /// 6. PF_Env_KampungDressing: every street lamp and plant laid out by blender/wesley_env/dressing.py;
    ///    run it with Main.unity open so spots inside houses / near NPCs are skipped
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
        private const string LandmarkFbx = Env + "Meshes/SM_Env_Landmark.fbx";
        private const string LayananFbx = Env + "Meshes/SM_Env_TandaLayanan.fbx";
        private const string LayoutJson = Env + "Data/env_dressing.json";
        private const string WeatheredShader = "Shader Graphs/SG_EnvWeathered";

        // yellow kampung light (Wesley: "lampu cahayanya kuning")
        private static readonly Color LightYellow = new Color(1f, 0.80f, 0.36f);
        private static readonly Color GlowYellow = new Color(1f, 0.78f, 0.22f);
        private static readonly Vector3 LanternGlass = new Vector3(1.05f, 2.265f, 0f);
        private static readonly Vector3 BulbCentre = new Vector3(0.44f, -0.19f, 0f);

        // station key (SM_Env_PapanLayanan_<key>), name keyword of its service point, floor paint colour (DESIGN.md)
        private static readonly (string key, string keyword, Color paint)[] Layanan =
        {
            ("BankSampah", "Bank Sampah", new Color(0.13f, 0.77f, 0.37f)),
            ("Kopdes", "Kopdes", new Color(0.96f, 0.62f, 0.04f)),
            ("Pengepul", "Pengepul", new Color(0.86f, 0.58f, 0.20f)),
            ("PosMedis", "Pos Medis", new Color(0.92f, 0.70f, 0.03f)),
            ("Karantina", "Karantina", new Color(0.66f, 0.33f, 0.97f)),
        };

        private static readonly string[] Plants =
            { "PohonPisang", "PohonKelapa", "PohonKetapang", "Bambu", "Semak", "Rumput", "Alang", "RumputKering", "Batu" };

        [MenuItem("KALI/Environment/Build Lamps, Plants & Kampung Dressing")]
        public static void BuildAll()
        {
            BuildMaterials();
            RemapFbx(LampuFbx);
            RemapFbx(VegFbx);
            RemapFbx(LandmarkFbx);
            RemapFbx(LayananFbx);
            var lampuJalan = BuildLampuJalan();
            var bohlam = BuildBohlam();
            var plants = new Dictionary<string, GameObject>();
            foreach (var p in Plants) plants[p] = BuildPlant(p);
            var layout = JsonUtility.FromJson<Layout>(File.ReadAllText(LayoutJson));
            int walls = BuildWallLamps(layout, bohlam);
            var landmarks = BuildLandmarkPrefabs(bohlam);
            var quest = BuildQuestLandmarks(layout, landmarks);
            var tanda = BuildServicePointMarks(out int snapped);
            int skipped = BuildDressing(layout, lampuJalan, plants, tanda, quest);
            AssetDatabase.SaveAssets();
            Debug.Log($"[EnvDressingBuilder] {layout.lamps.Length} street lamps, {layout.plants.Length} plants ({skipped} skipped: inside a scene collider / near an NPC), {walls} wall lamps, {layout.landmarks.Length} quest landmarks, {layout.signposts.Length} signposts, {snapped}/{Layanan.Length} service-point marks snapped.");
        }

        // ---------------- materials ----------------

        private static void BuildMaterials()
        {
            ConfigureCardTextures("T_Env_DaunPisang", "T_Env_DaunKelapa", "T_Env_DaunRimbun", "T_Env_RumputAlang", "T_Env_TandaLantai");
            Weathered("M_Env_BesiKarat", "T_Env_CatKarat", new Color(0.55f, 0.30f, 0.20f), 0.25f, 0.1f);
            Weathered("M_Env_KulitPohon", "T_Env_KulitPohon", new Color(0.56f, 0.45f, 0.35f), 0.12f, 0.35f);
            Weathered("M_Env_BatangPisang", "T_Env_KulitPohon", new Color(0.66f, 0.72f, 0.42f), 0.2f, 0.15f);
            Weathered("M_Env_DaunRimbunPadat", "T_Env_DaunRimbun", new Color(0.82f, 0.86f, 0.8f), 0.18f, 0f);
            Weathered("M_Env_Bambu", "T_Env_Bambu", Color.white, 0.35f, 0.1f);
            Weathered("M_Env_BatuSungai", "T_Env_BetonKotor", new Color(0.52f, 0.50f, 0.46f), 0.2f, 0.55f);
            Weathered("M_Env_PapanLayanan", "T_Env_PapanLayanan", new Color(0.93f, 0.93f, 0.93f), 0.2f, 0f);
            Paint("M_Env_TandaLantai", Color.white);
            foreach (var l in Layanan) Paint("M_Env_TandaLantai_" + l.key, PaintAlbedo(l.paint));
            Weathered("M_Env_PapanLandmark", "T_Env_PapanLandmark", new Color(0.93f, 0.93f, 0.93f), 0.2f, 0f);
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

        internal static Material LoadOrCreate(string name, Shader shader)
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

        internal static void Weathered(string name, string tex, Color tint, float smooth, float moss)
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

        /// <summary>Flat ground takes the full noon sun (Unity light intensity is gamma here, so 2.15 acts like
        /// ~5x). A DESIGN.md colour at full albedo clips to cyan/white, so the paint keeps its hue but its
        /// brightest linear channel is capped at 0.2, like real sun-faded paint.</summary>
        private static Color PaintAlbedo(Color c)
        {
            Color lin = c.linear;
            float max = Mathf.Max(lin.r, Mathf.Max(lin.g, lin.b));
            if (max <= 0.2f) return c;
            Color g = (lin * (0.2f / max)).gamma;
            g.a = 1f;                                              // alpha drives the cutout, keep it opaque
            return g;
        }

        /// <summary>Worn floor paint: cutout so scuffs show the ground, both faces so it never vanishes.</summary>
        private static void Paint(string name, Color colour)
        {
            Cutout(name, "T_Env_TandaLantai", colour);
            var m = AssetDatabase.LoadAssetAtPath<Material>(Mats + name + ".mat");
            m.SetFloat("_Cutoff", 0.5f);
            m.SetFloat("_Smoothness", 0f);                         // matte: no sky glint turning green cyan
            m.SetFloat("_SpecularHighlights", 0f);
            m.EnableKeyword("_SPECULARHIGHLIGHTS_OFF");
            m.SetFloat("_EnvironmentReflections", 0f);
            m.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF");
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

        internal static void RemapFbx(string fbx)
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

        internal static GameObject MeshObject(string fbx, string meshName, string goName)
        {
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(fbx);
            var src = model.transform.Find(meshName) ?? model.transform;     // a single-object FBX imports as the root itself
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

        internal static GameObject Save(GameObject root, string name)
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

        // ---------------- Priority 0 quest landmarks ----------------

        internal static GameObject Child(GameObject root, string fbx, string mesh)
        {
            var go = MeshObject(fbx, mesh, mesh);
            go.transform.SetParent(root.transform, false);
            return go;
        }

        internal static void Box(GameObject root, string name, Vector3 centre, Vector3 size)
        {
            var go = new GameObject(name);
            go.transform.SetParent(root.transform, false);
            go.transform.localPosition = centre;
            go.AddComponent<BoxCollider>().size = size;
        }

        private static void AddBohlam(GameObject root, GameObject bohlam, Vector3 pos, float yaw, float groundY)
        {
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(bohlam, root.transform);
            inst.name = "LampuBohlam";
            inst.transform.localPosition = pos;
            inst.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
            Vector3 under = pos + Quaternion.Euler(0f, yaw, 0f) * new Vector3(BulbCentre.x + 0.4f, 0f, 0f);
            var pool = AddPool(root.transform, new Vector3(under.x, groundY, under.z), 5f);
            var lamp = inst.GetComponent<EnvNightLamp>();
            lamp.glowRenderers = new List<Renderer>(lamp.glowRenderers) { pool }.ToArray();
        }

        private static Dictionary<string, GameObject> BuildLandmarkPrefabs(GameObject bohlam)
        {
            var map = new Dictionary<string, GameObject>();

            // Q2 Tangga Cuci: walkable stairs (mesh collider) + litter that disappears as the river clears
            var root = new GameObject("PF_Env_TanggaCuci");
            var steps = Child(root, LandmarkFbx, "SM_Env_TanggaCuci");
            steps.AddComponent<MeshCollider>().sharedMesh = steps.GetComponent<MeshFilter>().sharedMesh;
            var litter = Child(root, LandmarkFbx, "SM_Env_TanggaCuci_Sampah");
            litter.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
            var stain = root.AddComponent<EnvClarityStain>();
            stain.dirtyOnly = new[] { litter };
            stain.stainRenderers = new Renderer[] { steps.GetComponent<MeshRenderer>() };
            map["PF_Env_TanggaCuci"] = Save(root, "PF_Env_TanggaCuci");

            // Q3 Kail Nyangkut: pilings block boats (capsules), plastic snag shows while dirty
            root = new GameObject("PF_Env_TiangNyangkut");
            var posts = Child(root, LandmarkFbx, "SM_Env_TiangNyangkut");
            var snag = Child(root, LandmarkFbx, "SM_Env_TiangNyangkut_Sampah");
            foreach (var p in new[] { new Vector3(0f, 0f, 0f), new Vector3(0.95f, 0f, 0.55f), new Vector3(0.35f, 0f, -0.85f), new Vector3(1.55f, 0f, -0.2f), new Vector3(-0.45f, 0f, 0.95f) })
            {
                var c = new GameObject("Tiang_Collider");
                c.transform.SetParent(root.transform, false);
                c.transform.localPosition = p + Vector3.down * 0.5f;
                var cap = c.AddComponent<CapsuleCollider>();
                cap.radius = 0.12f;
                cap.height = 3.0f;
            }
            stain = root.AddComponent<EnvClarityStain>();
            stain.dirtyOnly = new[] { snag };
            stain.stainRenderers = new Renderer[] { posts.GetComponent<MeshRenderer>() };
            map["PF_Env_TiangNyangkut"] = Save(root, "PF_Env_TiangNyangkut");

            // warung stalls: counter + bench colliders, a bohlam under the tarp
            foreach (var side in new[] { "Barat", "Timur" })
            {
                root = new GameObject("PF_Env_WarungStall_" + side);
                Child(root, LandmarkFbx, "SM_Env_WarungStall_" + side);
                Box(root, "Warung_Counter", new Vector3(0.48f, 0.47f, 0f), new Vector3(0.67f, 0.94f, 2.52f));
                Box(root, "Warung_Bench", new Vector3(1.42f, 0.24f, 0f), new Vector3(0.4f, 0.48f, 2.2f));
                Box(root, "Warung_Shelf", new Vector3(-0.8f, 0.85f, 0f), new Vector3(0.3f, 1.7f, 2.4f));
                AddBohlam(root, bohlam, new Vector3(-0.8f, 2.05f, 0.55f), 0f, 0.03f);
                map["PF_Env_WarungStall_" + side] = Save(root, "PF_Env_WarungStall_" + side);
            }

            // Pak RT's pos ronda + notice board
            root = new GameObject("PF_Env_PosRonda");
            Child(root, LandmarkFbx, "SM_Env_PosRonda");
            Box(root, "PosRonda_BaleBale", new Vector3(0f, 0.3f, 0f), new Vector3(2.0f, 0.6f, 2.4f));
            Box(root, "PosRonda_PapanPengumuman", new Vector3(0.3f, 1.0f, 2.85f), new Vector3(0.2f, 2.0f, 1.7f));
            AddBohlam(root, bohlam, new Vector3(1.06f, 1.95f, -1.14f), 0f, 0.03f);
            map["PF_Env_PosRonda"] = Save(root, "PF_Env_PosRonda");

            // wayfinding post + arrow boards
            root = MeshObject(LandmarkFbx, "SM_Env_TiangPapanArah", "PF_Env_TiangPapanArah");
            var pc = root.AddComponent<BoxCollider>();
            pc.center = new Vector3(0f, 1.1f, 0f);
            pc.size = new Vector3(0.14f, 2.6f, 0.14f);
            map["PF_Env_TiangPapanArah"] = Save(root, "PF_Env_TiangPapanArah");
            foreach (var a in new[] { "Medis", "Karantina", "BankSampah" })
            {
                root = MeshObject(LandmarkFbx, "SM_Env_Panah" + a, "PF_Env_Panah" + a);
                map["PF_Env_Panah" + a] = Save(root, "PF_Env_Panah" + a);
            }
            return map;
        }

        private static GameObject BuildQuestLandmarks(Layout layout, Dictionary<string, GameObject> map)
        {
            var root = new GameObject("PF_Env_QuestLandmarks");
            for (int i = 0; i < layout.signposts.Length; i++)
            {
                var sp = layout.signposts[i];
                var post = (GameObject)PrefabUtility.InstantiatePrefab(map["PF_Env_TiangPapanArah"], root.transform);
                post.name = $"PapanArah_{i + 1}";
                post.transform.position = new Vector3(sp.p[0], sp.p[1], sp.p[2]);
                Physics.SyncTransforms();
                foreach (var a in sp.arrows)
                {
                    var arrow = (GameObject)PrefabUtility.InstantiatePrefab(map[a.prefab], post.transform);
                    arrow.transform.localPosition = new Vector3(0f, a.y, 0f);
                    arrow.transform.localRotation = Quaternion.Euler(0f, a.yaw, 0f);
                }
            }
            Physics.SyncTransforms();
            foreach (var l in layout.landmarks)
            {
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(map[l.prefab], root.transform);
                inst.transform.SetPositionAndRotation(new Vector3(l.p[0], l.p[1], l.p[2]), Quaternion.Euler(0f, l.yaw, 0f));
                // land pieces (stalls, pos ronda) slide to the nearest free flat ground if Ivan's houses moved in
                // a stall with no free ground means Ivan's kampung already has a warung there: skip the duplicate
                if (l.p[1] > 0.5f && !NudgeToFreeGround(inst, 7f)) UnityEngine.Object.DestroyImmediate(inst);
            }
            return Save(root, "PF_Env_QuestLandmarks");
        }

        // ---------------- PF_Env_TandaLayanan (service-point marks) ----------------

        private static GameObject BuildServicePointMarks(out int snapped)
        {
            var root = new GameObject("PF_Env_TandaLayanan");
            var marks = root.AddComponent<EnvServicePointMarks>();
            var list = new List<EnvServicePointMarks.Mark>();
            for (int i = 0; i < Layanan.Length; i++)
            {
                var l = Layanan[i];
                var mark = new GameObject("Tanda_" + l.key);
                mark.transform.SetParent(root.transform, false);
                mark.transform.localPosition = new Vector3(i * 6f, 1.4f, 0f);        // parked in a row until snapped
                var decal = Child(mark, LayananFbx, "SM_Env_TandaLantai");
                var dr = decal.GetComponent<MeshRenderer>();
                dr.sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>(Mats + "M_Env_TandaLantai_" + l.key + ".mat");
                dr.shadowCastingMode = ShadowCastingMode.Off;
                var sign = Child(mark, LayananFbx, "SM_Env_PapanLayanan_" + l.key);
                Box(sign, "Papan_Collider", new Vector3(0.03f, 0.6f, 2.65f), new Vector3(0.14f, 1.3f, 1.6f));
                list.Add(new EnvServicePointMarks.Mark { keyword = l.keyword, root = mark.transform });
            }
            marks.marks = list.ToArray();
            snapped = marks.Snap();                                                   // bake positions when Main.unity is open
            return Save(root, "PF_Env_TandaLayanan");
        }

        private static bool IgnoredForPlacement(Collider c) =>
            c is TerrainCollider || c.name.Contains("Terrain") || c.name.Contains("Ground") || c.name.Contains("Water")
            || c.transform.root.name.StartsWith("NPC_") || c.name.StartsWith("NPC_") || c.name.Contains("Player");

        private static bool FlatGround(Vector3 p, float groundY)
        {
            foreach (var h in Physics.RaycastAll(p + Vector3.up * 6f, Vector3.down, 12f, ~0, QueryTriggerInteraction.Ignore))
                if (h.collider is TerrainCollider || h.collider.name.Contains("Terrain") || h.collider.name.Contains("Ground"))
                    return Mathf.Abs(h.point.y - groundY) < 0.3f;
            return false;
        }

        /// <summary>Moves a land landmark to the closest spot (rings up to maxRadius) where its footprint hits no
        /// scene collider and all four corners stand on bank-top ground (not the talud or the river).</summary>
        private static bool NudgeToFreeGround(GameObject inst, float maxRadius)
        {
            var cols = inst.GetComponentsInChildren<Collider>();
            var b = new Bounds(inst.transform.position, Vector3.zero);
            foreach (var r in inst.GetComponentsInChildren<Renderer>()) b.Encapsulate(r.bounds);
            Vector3 offset = b.center - inst.transform.position, ext = b.extents;
            Vector3 start = inst.transform.position;
            for (float r = 0f; r <= maxRadius; r += 0.75f)
            {
                int steps = r < 0.01f ? 1 : 16;
                for (int i = 0; i < steps; i++)
                {
                    float a = i * Mathf.PI * 2f / steps;
                    Vector3 p = start + new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)) * r;
                    Vector3 c = p + offset;
                    bool free = true;
                    foreach (var hit in Physics.OverlapBox(new Vector3(c.x, p.y + 0.3f + ext.y * 0.5f, c.z), new Vector3(ext.x * 0.9f, ext.y * 0.5f, ext.z * 0.9f), Quaternion.identity, ~0, QueryTriggerInteraction.Ignore))
                        if (Array.IndexOf(cols, hit) < 0 && !IgnoredForPlacement(hit)) { free = false; break; }
                    if (free)
                        foreach (var k in new[] { new Vector3(-1, 0, -1), new Vector3(1, 0, -1), new Vector3(1, 0, 1), new Vector3(-1, 0, 1), Vector3.zero })
                            if (!FlatGround(c + Vector3.Scale(k, ext * 0.9f), p.y)) { free = false; break; }
                    if (!free) continue;
                    inst.transform.position = p;
                    Physics.SyncTransforms();
                    if (r > 0f) Debug.Log($"[EnvDressingBuilder] {inst.name} moved {r:0.0} m to free ground {p}");
                    return true;
                }
            }
            Debug.LogWarning($"[EnvDressingBuilder] {inst.name}: no free ground within {maxRadius} m of {start}, not placed");
            return false;
        }

        // ---------------- PF_Env_KampungDressing ----------------

        /// <summary>True when a spot is free in the open scene: no building / house / prop collider
        /// at body height and no ambient NPC or station service point within 2.5 m. Lets the Python layout stay approximate
        /// while Ivan's 61 procedural houses decide the exact free ground.</summary>
        private static bool SceneFree(Vector3 p, float radius, List<Vector3> npcs)
        {
            foreach (var n in npcs)
                if ((new Vector2(n.x - p.x, n.z - p.z)).sqrMagnitude < 6.25f) return false;
            foreach (var c in Physics.OverlapSphere(p + Vector3.up * (radius + 0.25f), radius, ~0, QueryTriggerInteraction.Ignore))
            {
                if (c is TerrainCollider || c.name.Contains("Terrain") || c.name.Contains("Ground") || c.name.Contains("Water")) continue;
                return false;
            }
            return true;
        }

        private static int BuildDressing(Layout layout, GameObject lampuJalan, Dictionary<string, GameObject> plants, GameObject tanda, GameObject quest)
        {
            var questProbe = (GameObject)PrefabUtility.InstantiatePrefab(quest);   // so plants/lamps keep off the landmarks
            Physics.SyncTransforms();
            var npcs = new List<Vector3>();
            foreach (var t in UnityEngine.Object.FindObjectsOfType<Transform>())
                if (t.name.StartsWith("NPC_") || t.name.EndsWith(EnvServicePointMarks.ServicePointSuffix)) npcs.Add(t.position);   // keep the floor rings clear
            int skipped = 0;
            var root = new GameObject("PF_Env_KampungDressing");
            var lampParent = new GameObject("LampuJalan").transform;
            lampParent.SetParent(root.transform, false);
            for (int i = 0; i < layout.lamps.Length; i++)
            {
                var l = layout.lamps[i];
                if (!SceneFree(new Vector3(l.p[0], l.p[1], l.p[2]), 0.45f, npcs)) { skipped++; continue; }
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(lampuJalan, lampParent);
                inst.name = $"LampuJalan_{i + 1:00}";
                inst.transform.SetPositionAndRotation(new Vector3(l.p[0], l.p[1], l.p[2]), Quaternion.Euler(0f, l.yaw, 0f));
            }
            var groups = new Dictionary<string, Transform>();
            foreach (var p in layout.plants)
            {
                float r = p.m is "PohonKetapang" or "Bambu" ? 1.2f : p.m is "PohonKelapa" or "PohonPisang" ? 0.6f : 0.35f;
                if (!SceneFree(new Vector3(p.p[0], p.p[1], p.p[2]), r, npcs)) { skipped++; continue; }
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
            UnityEngine.Object.DestroyImmediate(questProbe);
            PrefabUtility.InstantiatePrefab(tanda, root.transform);                   // service-point marks ride along
            Save(root, "PF_Env_KampungDressing");
            return skipped;
        }

        // ---------------- env_dressing.json ----------------

        [Serializable] private class Lamp { public float[] p; public float yaw; }
        [Serializable] private class PlantItem { public string m; public float[] p; public float yaw; public float s; }
        [Serializable] private class Spot { public float[] p; public float yaw; }
        [Serializable] private class Wall { public string prefab; public Spot[] spots; }
        [Serializable] private class Landmark { public string prefab; public float[] p; public float yaw; }
        [Serializable] private class Arrow { public string prefab; public float yaw; public float y; }
        [Serializable] private class SignPost { public float[] p; public Arrow[] arrows; }
        [Serializable] private class Layout { public Lamp[] lamps; public PlantItem[] plants; public Wall[] wall_lamps; public Landmark[] landmarks; public SignPost[] signposts; }
    }
}
