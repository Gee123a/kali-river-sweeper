#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using KaliRiverSweeper.Lighting;

namespace KaliRiverSweeper.LightingEditor
{
    /// <summary>
    /// Builds JC's two lighting props from the Blender meshes (blender/build_all.py --only equipment):
    ///   Prefabs/PF_Lantern_Warung.prefab        (MapJsonImporter puts one on each warung roof)
    ///   Prefabs/PF_WarningBeacon_PintuAir.prefab (MapJsonImporter puts it on the sluice gate)
    /// Menu: KALI > Lighting > Build Lantern &amp; Beacon Prefabs. The sun, sky, volume and PF_LightingRig are built by
    /// Ivan's KaliLightingBuilder (KALI > Lighting > Build Sky &amp; Lighting Rig); this file does not touch them.
    /// </summary>
    public static class KaliLightingPropsBuilder
    {
        private const string Root = "Assets/_Project/Lighting";
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

        [MenuItem("KALI/Lighting/Build Lantern & Beacon Prefabs")]
        public static void BuildAll()
        {
            EnsureFolder(Root, "Prefabs");
            BuildLanternPrefab();
            BuildBeaconPrefab();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[KALI] PF_Lantern_Warung and PF_WarningBeacon_PintuAir built in " + PrefabsDir);
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
