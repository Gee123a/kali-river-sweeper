#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using KaliRiverSweeper.Lighting;

namespace KaliRiverSweeper.LightingEditor
{
    /// <summary>
    /// One-click builder for everything in Assets/_Project/Lighting/.
    /// Menu: KALI > Lighting > Build All Lighting Assets
    /// Creates (idempotent - re-running overwrites our own assets only):
    ///   Profiles/VolumeProfile_GoldenHour.asset
    ///   Profiles/VolumeProfile_MonsoonStorm.asset
    ///   Profiles/Skybox_GoldenHour.mat, Skybox_Monsoon.mat
    ///   Prefabs/PF_Lantern_Warung.prefab
    ///   Prefabs/PF_WarningBeacon_PintuAir.prefab
    ///   Prefabs/PF_LightingRig.prefab  (sun + both volumes + LightingPresetSwitcher, pre-wired)
    /// Keeping this as code (not hand-clicked) lets us explain every number in the Sidang.
    /// </summary>
    public static class KaliLightingBuilder
    {
        private const string Root = "Assets/_Project/Lighting";
        private const string ProfilesDir = Root + "/Profiles";
        private const string PrefabsDir = Root + "/Prefabs";

        // Blender meshes + shared atlas (blender/build_all.py --only equipment). Missing meshes fall back to primitives.
        private const string PropEquipDir = "Assets/_Project/Props/Equipment";
        private const string LanternMeshPath = PropEquipDir + "/Meshes/SM_Prop_LanternWarung.fbx";
        private const string BeaconMeshPath = PropEquipDir + "/Meshes/SM_Prop_WarningBeacon.fbx";
        private const string RotorMeshPath = PropEquipDir + "/Meshes/SM_Prop_BeaconRotor.fbx";
        private const string EquipTextureDir = PropEquipDir + "/Textures";
        private const string EquipAtlasBaseName = "T_Equipment_Atlas";
        private const string EquipMaterialPath = PropEquipDir + "/Materials/M_Equipment_Atlas.mat";

        // Prefab layout (Unity metres). The importer puts each prefab ORIGIN on the building's roof top
        // (MapJsonImporter.AttachOnTopIfPresent: bbox max.y + 0.05), so both props stand up from their origin.
        // Values mirror blender/kali_blender/equipment/*.py (Blender -Y = Unity +Z, Blender +Z = Unity +Y).
        private static readonly Vector3 LanternBulbPos = new Vector3(0f, 0.315f, 0.28f);   // equip_01 BULB
        private const float BeaconRotorY = 0.085f;                                          // equip_02 HOUSING_TOP
        private const float BeaconBeamY = 0.055f;                                           // equip_03 DISH_Z (rotor local)
        private static readonly Color WarmGlow = new Color(1f, 0.69f, 0.30f);

        [MenuItem("KALI/Lighting/Build All Lighting Assets")]
        public static void BuildAll()
        {
            EnsureFolder(Root, "Profiles");
            EnsureFolder(Root, "Prefabs");

            // 'Lights Use Color Temperature' must be on for the 3400K sun to take effect.
            GraphicsSettings.lightsUseColorTemperature = true;

            VolumeProfile golden = BuildGoldenHourProfile();
            VolumeProfile monsoon = BuildMonsoonProfile();
            Material skyGolden = BuildSkybox("Skybox_GoldenHour",
                tint: new Color(1f, 0.72f, 0.45f), ground: new Color(0.42f, 0.33f, 0.24f),
                thickness: 1.4f, exposure: 1.1f, sunSize: 0.06f);
            Material skyMonsoon = BuildSkybox("Skybox_Monsoon",
                tint: new Color(0.45f, 0.52f, 0.58f), ground: new Color(0.26f, 0.29f, 0.32f),
                thickness: 0.6f, exposure: 0.7f, sunSize: 0f);

            BuildLanternPrefab();
            BuildBeaconPrefab();
            BuildRigPrefab(golden, monsoon, skyGolden, skyMonsoon);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[KALI] Lighting assets built in " + Root);
        }

        // ------------------------------------------------------------------ profiles

        private static VolumeProfile BuildGoldenHourProfile()
        {
            VolumeProfile p = CreateProfile("VolumeProfile_GoldenHour");

            var tone = AddComponent<Tonemapping>(p);
            tone.mode.Override(TonemappingMode.ACES);

            var bloom = AddComponent<Bloom>(p);
            bloom.threshold.Override(0.9f);
            bloom.intensity.Override(0.4f);
            bloom.scatter.Override(0.75f);                       // soft scatter
            bloom.tint.Override(new Color(1f, 0.92f, 0.8f));

            // Brief says "Color Adjustments: Temperature +12". In URP, Temperature lives in
            // White Balance, Saturation in Color Adjustments - so we set both.
            var wb = AddComponent<WhiteBalance>(p);
            wb.temperature.Override(12f);

            var ca = AddComponent<ColorAdjustments>(p);
            ca.saturation.Override(10f);

            SaveProfile(p);
            return p;
        }

        private static VolumeProfile BuildMonsoonProfile()
        {
            VolumeProfile p = CreateProfile("VolumeProfile_MonsoonStorm");

            var tone = AddComponent<Tonemapping>(p);
            tone.mode.Override(TonemappingMode.ACES);

            var vignette = AddComponent<Vignette>(p);
            vignette.intensity.Override(0.35f);                  // heavy atmospheric vignette
            vignette.smoothness.Override(0.45f);
            vignette.color.Override(new Color(0.05f, 0.07f, 0.09f));

            // Desaturated, contrast-heavy grade with a cold filter.
            var ca = AddComponent<ColorAdjustments>(p);
            ca.saturation.Override(-35f);
            ca.contrast.Override(25f);
            ca.postExposure.Override(-0.2f);
            ca.colorFilter.Override(new Color(0.82f, 0.9f, 1f));

            var wb = AddComponent<WhiteBalance>(p);
            wb.temperature.Override(-18f);

            // Storm disorientation.
            var chroma = AddComponent<ChromaticAberration>(p);
            chroma.intensity.Override(0.15f);

            SaveProfile(p);
            return p;
        }

        private static VolumeProfile CreateProfile(string name)
        {
            // Update in place (never delete) so the asset keeps its GUID and scene/prefab
            // references survive a re-run - important with 4 people sharing the repo.
            string path = ProfilesDir + "/" + name + ".asset";
            VolumeProfile p = AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
            if (p == null)
            {
                p = ScriptableObject.CreateInstance<VolumeProfile>();
                AssetDatabase.CreateAsset(p, path);
                return p;
            }

            foreach (Object sub in AssetDatabase.LoadAllAssetsAtPath(path))
            {
                if (sub is VolumeComponent) Object.DestroyImmediate(sub, true);
            }
            p.components.Clear();
            return p;
        }

        private static T AddComponent<T>(VolumeProfile p) where T : VolumeComponent
        {
            T c = p.Add<T>(true);                                // all overrides on; we then set values
            c.name = typeof(T).Name;
            AssetDatabase.AddObjectToAsset(c, p);
            return c;
        }

        private static void SaveProfile(VolumeProfile p)
        {
            EditorUtility.SetDirty(p);
            AssetDatabase.SaveAssets();
        }

        // ------------------------------------------------------------------ skybox

        private static Material BuildSkybox(string name, Color tint, Color ground,
            float thickness, float exposure, float sunSize)
        {
            string path = ProfilesDir + "/" + name + ".mat";
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            bool isNew = mat == null;
            if (isNew) mat = new Material(Shader.Find("Skybox/Procedural"));
            mat.SetColor("_SkyTint", tint);
            mat.SetColor("_GroundColor", ground);
            mat.SetFloat("_AtmosphereThickness", thickness);
            mat.SetFloat("_Exposure", exposure);
            mat.SetFloat("_SunSize", sunSize);
            if (isNew) AssetDatabase.CreateAsset(mat, path);
            else EditorUtility.SetDirty(mat);
            return mat;
        }

        // ------------------------------------------------------------------ prefabs

        private static void BuildLanternPrefab()
        {
            var root = new GameObject("PF_Lantern_Warung");

            // Blender lantern (foot block + bamboo post + arm + shade + bulb), origin = post base, so it stands
            // on the roof top where the importer drops the origin. The atlas Emission map is white only on the
            // bulb, so LanternFlicker can glow the bulb through _EmissionColor without lighting up the wood.
            Renderer bulbR = null;
            GameObject lanternMesh = InstantiateMesh(LanternMeshPath, "LanternMesh", root.transform, Vector3.zero);
            if (lanternMesh != null)
            {
                Material lanternMat = LoadOrCreateEquipmentMaterial();
                if (lanternMat == null) lanternMat = MakeLit("M_Lantern_Shade", new Color(0.18f, 0.43f, 0.32f), false);
                ApplyMaterial(lanternMesh, lanternMat);
                bulbR = lanternMesh.GetComponentInChildren<Renderer>();
            }
            else
            {
                Debug.LogWarning("[KALI] " + LanternMeshPath + " not found; using primitive lantern. Run blender/build_all.py --only equipment first.");

                // Post standing on the origin, arm forward (+Z), bulb hanging under it (same layout as the mesh).
                var post = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                post.name = "Post";
                post.transform.SetParent(root.transform, false);
                post.transform.localScale = new Vector3(0.045f, 0.28f, 0.045f);
                post.transform.localPosition = new Vector3(0f, 0.28f, 0f);
                Object.DestroyImmediate(post.GetComponent<Collider>());
                post.GetComponent<Renderer>().sharedMaterial = MakeLit("M_Lantern_Post", new Color(0.79f, 0.64f, 0.39f), false);

                var arm = GameObject.CreatePrimitive(PrimitiveType.Cube);
                arm.name = "Arm";
                arm.transform.SetParent(root.transform, false);
                arm.transform.localScale = new Vector3(0.03f, 0.03f, 0.32f);
                arm.transform.localPosition = new Vector3(0f, 0.515f, 0.13f);
                Object.DestroyImmediate(arm.GetComponent<Collider>());
                arm.GetComponent<Renderer>().sharedMaterial = MakeLit("M_Lantern_Cord", new Color(0.08f, 0.08f, 0.08f), false);

                var bulb = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                bulb.name = "Bulb";
                bulb.transform.SetParent(root.transform, false);
                bulb.transform.localScale = Vector3.one * 0.05f;
                bulb.transform.localPosition = LanternBulbPos;
                Object.DestroyImmediate(bulb.GetComponent<Collider>());
                bulbR = bulb.GetComponent<Renderer>();
                bulbR.sharedMaterial = MakeLit("M_Lantern_Bulb", WarmGlow, true);
            }

            // Light: #FFB04D, ~15W incandescent equivalent, soft falloff, no shadows (many lanterns).
            var lightGo = new GameObject("PointLight");
            lightGo.transform.SetParent(root.transform, false);
            lightGo.transform.localPosition = LanternBulbPos;
            var l = lightGo.AddComponent<Light>();
            l.type = LightType.Point;
            l.color = new Color(1f, 0.690f, 0.302f);
            l.intensity = 1.6f;
            l.range = 7f;
            l.shadows = LightShadows.None;

            var flicker = lightGo.AddComponent<LanternFlicker>();
            flicker.baseIntensity = 1.6f;
            flicker.bulbRenderer = bulbR;

            Save(root, PrefabsDir + "/PF_Lantern_Warung.prefab");
        }

        private static void BuildBeaconPrefab()
        {
            var root = new GameObject("PF_WarningBeacon_PintuAir");

            // Blender beacon (mount plate + housing + amber dome lens + guard bars), origin = plate bottom, so it
            // stands on the sluice-gate top. Only the lens is white in the Emission map, so the rotator's
            // _EmissionColor pulse lights the lens and leaves the dark housing alone.
            Renderer lensR;
            GameObject beaconMesh = InstantiateMesh(BeaconMeshPath, "BeaconMesh", root.transform, Vector3.zero);
            if (beaconMesh != null)
            {
                Material beaconMat = LoadOrCreateEquipmentMaterial();
                if (beaconMat == null) beaconMat = MakeLit("M_Beacon_Lens", new Color(1f, 0.64f, 0.12f), true);
                ApplyMaterial(beaconMesh, beaconMat);
                lensR = beaconMesh.GetComponentInChildren<Renderer>();
            }
            else
            {
                Debug.LogWarning("[KALI] " + BeaconMeshPath + " not found; using primitive beacon. Run blender/build_all.py --only equipment first.");

                var baseGo = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                baseGo.name = "Base";
                baseGo.transform.SetParent(root.transform, false);
                baseGo.transform.localScale = new Vector3(0.16f, BeaconRotorY * 0.5f, 0.16f);
                baseGo.transform.localPosition = new Vector3(0f, BeaconRotorY * 0.5f, 0f);
                Object.DestroyImmediate(baseGo.GetComponent<Collider>());
                baseGo.GetComponent<Renderer>().sharedMaterial = MakeLit("M_Beacon_Base", new Color(0.18f, 0.18f, 0.2f), false);

                var lens = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                lens.name = "Lens";
                lens.transform.SetParent(root.transform, false);
                lens.transform.localScale = new Vector3(0.15f, 0.13f, 0.15f);
                lens.transform.localPosition = new Vector3(0f, BeaconRotorY + BeaconBeamY, 0f);
                Object.DestroyImmediate(lens.GetComponent<Collider>());
                lensR = lens.GetComponent<Renderer>();
                lensR.sharedMaterial = MakeLit("M_Beacon_Lens", new Color(1f, 0.64f, 0.12f), true);
            }

            // Rotor carries the spot light and the mirror pair so rotation is visible.
            var rotor = new GameObject("Rotor");
            rotor.transform.SetParent(root.transform, false);
            rotor.transform.localPosition = new Vector3(0f, BeaconRotorY, 0f);

            GameObject rotorMesh = InstantiateMesh(RotorMeshPath, "RotorMesh", rotor.transform, Vector3.zero);
            if (rotorMesh != null)
            {
                Material rotorMat = LoadOrCreateEquipmentMaterial();
                if (rotorMat == null) rotorMat = MakeLit("M_Beacon_Reflector", new Color(0.8f, 0.8f, 0.8f), false);
                ApplyMaterial(rotorMesh, rotorMat);
            }
            else
            {
                Debug.LogWarning("[KALI] " + RotorMeshPath + " not found; using primitive reflector. Run blender/build_all.py --only equipment first.");

                var reflector = GameObject.CreatePrimitive(PrimitiveType.Cube);
                reflector.name = "Reflector";
                reflector.transform.SetParent(rotor.transform, false);
                reflector.transform.localScale = new Vector3(0.07f, 0.07f, 0.01f);
                reflector.transform.localPosition = new Vector3(0f, BeaconBeamY, -0.02f);
                Object.DestroyImmediate(reflector.GetComponent<Collider>());
                reflector.GetComponent<Renderer>().sharedMaterial = MakeLit("M_Beacon_Reflector", new Color(0.8f, 0.8f, 0.8f), false);
            }

            var beamGo = new GameObject("BeamLight");
            beamGo.transform.SetParent(rotor.transform, false);
            beamGo.transform.localPosition = new Vector3(0f, BeaconBeamY, 0f);   // reflector-dish centre, inside the lens
            beamGo.transform.localRotation = Quaternion.Euler(8f, 0f, 0f);
            var beam = beamGo.AddComponent<Light>();
            beam.type = LightType.Spot;
            beam.spotAngle = 45f;
            beam.innerSpotAngle = 20f;
            beam.range = 25f;
            beam.intensity = 8f;
            beam.color = new Color(1f, 0.64f, 0.12f);
            beam.shadows = LightShadows.None;

            var rot = root.AddComponent<WarningBeaconRotator>();
            rot.rotor = rotor.transform;
            rot.beamLight = beam;
            rot.lensRenderer = lensR;

            Save(root, PrefabsDir + "/PF_WarningBeacon_PintuAir.prefab");
        }

        private static void BuildRigPrefab(VolumeProfile golden, VolumeProfile monsoon,
            Material skyGolden, Material skyMonsoon)
        {
            var root = new GameObject("PF_LightingRig");

            var sunGo = new GameObject("Sun");
            sunGo.transform.SetParent(root.transform, false);
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.shadows = LightShadows.Soft;                     // soft shadows
            sun.shadowStrength = 0.85f;
            sun.useColorTemperature = true;
            sun.color = new Color(1f, 0.886f, 0.639f);           // #FFE2A3
            sun.colorTemperature = 3400f;
            sun.intensity = 2.2f;
            sunGo.transform.rotation = Quaternion.Euler(18f, -35f, 0f);

            Volume vGolden = MakeVolume(root.transform, "Vol_GoldenHour", golden, priority: 0f, weight: 1f);
            Volume vMonsoon = MakeVolume(root.transform, "Vol_MonsoonStorm", monsoon, priority: 1f, weight: 0f);

            var sw = root.AddComponent<LightingPresetSwitcher>();
            sw.sun = sun;
            sw.goldenHourVolume = vGolden;
            sw.monsoonVolume = vMonsoon;
            sw.goldenHourSkybox = skyGolden;
            sw.monsoonSkybox = skyMonsoon;

            Save(root, PrefabsDir + "/PF_LightingRig.prefab");
        }

        private static Volume MakeVolume(Transform parent, string name, VolumeProfile profile, float priority, float weight)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var v = go.AddComponent<Volume>();
            v.isGlobal = true;
            v.sharedProfile = profile;
            v.priority = priority;
            v.weight = weight;
            return v;
        }

        // ------------------------------------------------------------------ helpers

        private static Material MakeLit(string name, Color color, bool emissive)
        {
            string path = PrefabsDir + "/" + name + ".mat";
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            bool isNew = mat == null;
            if (isNew) mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            mat.SetColor("_BaseColor", color);
            if (emissive)
            {
                mat.EnableKeyword("_EMISSION");
                mat.SetColor("_EmissionColor", color * 3f);
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }
            if (isNew) AssetDatabase.CreateAsset(mat, path);
            else EditorUtility.SetDirty(mat);
            return mat;
        }

        // Instantiates a Blender FBX as an unpacked child. Returns null when the FBX does not exist.
        private static GameObject InstantiateMesh(string fbxPath, string name, Transform parent, Vector3 localPos)
        {
            var src = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
            if (src == null) return null;

            var go = (GameObject)PrefabUtility.InstantiatePrefab(src);
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            foreach (Collider c in go.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(c);
            return go;
        }

        private static void ApplyMaterial(GameObject go, Material mat)
        {
            foreach (Renderer r in go.GetComponentsInChildren<Renderer>(true)) r.sharedMaterial = mat;
        }

        // URP Lit material for the equipment atlas (albedo / normal / mask / emission from Blender), created or
        // updated in place. Returns null when the atlas textures have not been exported yet.
        private static Material LoadOrCreateEquipmentMaterial()
        {
            string tex = EquipTextureDir + "/" + EquipAtlasBaseName;
            Texture2D albedo = ConfigureTexture(tex + "_Albedo.png", TextureImporterType.Default, true, false);
            if (albedo == null)
            {
                Debug.LogWarning("[KALI] " + tex + "_Albedo.png not found; lighting props use flat fallback materials.");
                return null;
            }
            Texture2D normal = ConfigureTexture(tex + "_Normal.png", TextureImporterType.NormalMap, false, false);
            Texture2D mask = ConfigureTexture(tex + "_Mask.png", TextureImporterType.Default, false, true);
            Texture2D emission = ConfigureTexture(tex + "_Emission.png", TextureImporterType.Default, true, false);

            EnsureFolder(PropEquipDir, "Materials");
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(EquipMaterialPath);
            bool isNew = mat == null;
            if (isNew) mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            mat.SetTexture("_BaseMap", albedo);
            mat.SetColor("_BaseColor", Color.white);
            if (normal != null)
            {
                mat.SetTexture("_BumpMap", normal);
                mat.EnableKeyword("_NORMALMAP");
            }
            if (mask != null)
            {
                // Same convention as KaliPropPrefabBuilder: metallic R, smoothness A.
                mat.SetTexture("_MetallicGlossMap", mask);
                mat.EnableKeyword("_METALLICSPECGLOSSMAP");
                mat.SetFloat("_SmoothnessTextureChannel", 0f);
                mat.SetFloat("_Smoothness", 1f);
                mat.SetFloat("_Metallic", 1f);
            }
            if (emission != null)
            {
                // Emission = map (white on bulb + lens only) x _EmissionColor; the scripts animate the colour.
                mat.SetTexture("_EmissionMap", emission);
                mat.EnableKeyword("_EMISSION");
                mat.SetColor("_EmissionColor", WarmGlow * 2f);
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }
            if (isNew) AssetDatabase.CreateAsset(mat, EquipMaterialPath);
            else EditorUtility.SetDirty(mat);
            return mat;
        }

        private static Texture2D ConfigureTexture(string path, TextureImporterType type, bool sRGB, bool pointFilter)
        {
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null) return null;
            importer.textureType = type;
            importer.sRGBTexture = sRGB;
            importer.maxTextureSize = 2048;
            importer.filterMode = pointFilter ? FilterMode.Point : FilterMode.Bilinear;   // mask: no swatch bleed
            importer.mipmapEnabled = !pointFilter;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        private static void Save(GameObject go, string path)
        {
            PrefabUtility.SaveAsPrefabAsset(go, path);
            Object.DestroyImmediate(go);
        }

        private static void EnsureFolder(string parent, string child)
        {
            if (!AssetDatabase.IsValidFolder(parent + "/" + child))
                AssetDatabase.CreateFolder(parent, child);
        }
    }
}
#endif
