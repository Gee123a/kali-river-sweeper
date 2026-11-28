using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Kali.Props.EditorTools
{
    /// <summary>
    /// Turns JC's FBX meshes (Props/Trash/Meshes, Props/Tools/Meshes, Props/Products/Meshes, Props/Equipment/Meshes,
    /// Rigging) into prefabs and builds the shared 2048 atlas & URP Lit materials. Editor-only (lives in an Editor folder).
    /// </summary>
    public static class KaliPropPrefabBuilder
    {
        private const string LogPrefix = "[KALI JC] ";

        private const string PropsRoot = "Assets/_Project/Props";
        private const string RiggingRoot = "Assets/_Project/Rigging";

        private const string TrashMeshFolder = PropsRoot + "/Trash/Meshes";
        private const string TrashPrefabFolder = PropsRoot + "/Trash/Prefabs";
        private const string TrashMaterialFolder = PropsRoot + "/Trash/Materials";
        private const string TrashTextureFolder = PropsRoot + "/Trash/Textures";
        private const string TrashMaterialPath = TrashMaterialFolder + "/M_Trash_Atlas.mat";
        private const string TrashAtlasBaseName = "T_Trash_Atlas";

        private const string ToolMeshFolder = PropsRoot + "/Tools/Meshes";
        private const string ToolPrefabFolder = PropsRoot + "/Tools/Prefabs";
        private const string ToolMaterialFolder = PropsRoot + "/Tools/Materials";
        private const string ToolTextureFolder = PropsRoot + "/Tools/Textures";
        private const string ToolMaterialPath = ToolMaterialFolder + "/M_Tools_Atlas.mat";
        private const string ToolAtlasBaseName = "T_Tools_Atlas";

        private const string ProductMeshFolder = PropsRoot + "/Products/Meshes";
        private const string ProductPrefabFolder = PropsRoot + "/Products/Prefabs";
        private const string ProductMaterialFolder = PropsRoot + "/Products/Materials";
        private const string ProductTextureFolder = PropsRoot + "/Products/Textures";
        private const string ProductMaterialPath = ProductMaterialFolder + "/M_Products_Atlas.mat";
        private const string ProductAtlasBaseName = "T_Products_Atlas";

        // Equipment (boom, boats, kampung bin). Same material path as KaliLightingPropsBuilder, which builds the lantern /
        // beacon / rotor prefabs from this atlas, so both builders share ONE M_Equipment_Atlas.
        private const string EquipmentMeshFolder = PropsRoot + "/Equipment/Meshes";
        private const string EquipmentPrefabFolder = PropsRoot + "/Equipment/Prefabs";
        private const string EquipmentMaterialFolder = PropsRoot + "/Equipment/Materials";
        private const string EquipmentTextureFolder = PropsRoot + "/Equipment/Textures";
        private const string EquipmentMaterialPath = EquipmentMaterialFolder + "/M_Equipment_Atlas.mat";
        private const string EquipmentAtlasBaseName = "T_Equipment_Atlas";

        private const string RiggingMeshFolder = RiggingRoot;
        private const string RiggingPrefabFolder = RiggingRoot;
        private const string RiggingMaterialFolder = RiggingRoot + "/Materials";

        private const string ExcavatorBodyMatPath = RiggingMaterialFolder + "/M_Excavator_Body.mat";
        private const string ExcavatorSteelMatPath = RiggingMaterialFolder + "/M_Hydraulic_Steel.mat";
        private const string ExcavatorRubberMatPath = RiggingMaterialFolder + "/M_Pontoon_Rubber.mat";
        private const string ExcavatorPrefabPath = RiggingRoot + "/PF_ExcavatorAmfibi.prefab";
        private const string ExcavatorModelPath = RiggingRoot + "/SK_ExcavatorAmfibi.fbx";

        private const string TrashMeshPattern = @"^SM_Trash_(.+)\.fbx$";
        private const string ToolMeshPattern = @"^SM_Tool_(.+)\.fbx$";
        private const string ProductMeshPattern = @"^SM_Product_(.+)\.fbx$";
        // The lighting meshes are wrapped by KaliLightingPropsBuilder (KALI > Lighting > Build Lantern & Beacon Prefabs), not here.
        private const string EquipmentMeshPattern = @"^SM_Prop_(?!LanternWarung\.|WarningBeacon\.|BeaconRotor\.)(.+)\.fbx$";

        private const string UrpLitShader = "Universal Render Pipeline/Lit";
        private const string BuoyancyTypeName = "RiverFlowBuoyancy";
        private const string TrashItemTypeName = "RiverTrashItem";

        private const float TrashMass = 0.5f;
        private const float TrashDrag = 1f;
        private const float TrashAngularDrag = 1f;
        private const int AtlasMaxTextureSize = 2048;

        private sealed class MeshEntry
        {
            public string Variant;
            public string AssetPath;
        }

        // ------------------------------------------------------------------
        // Menu items
        // ------------------------------------------------------------------

        [MenuItem("KALI/JC/Build Trash Prefabs")]
        public static void BuildTrashPrefabsMenu()
        {
            try
            {
                BuildAtlasMaterials();
                BuildTrashPrefabs();
            }
            finally
            {
                AssetDatabase.SaveAssets();
            }
        }

        [MenuItem("KALI/JC/Build Tool Prefabs")]
        public static void BuildToolPrefabsMenu()
        {
            try
            {
                BuildAtlasMaterials();
                BuildToolPrefabs();
            }
            finally
            {
                AssetDatabase.SaveAssets();
            }
        }

        [MenuItem("KALI/JC/Build Product Prefabs")]
        public static void BuildProductPrefabsMenu()
        {
            try
            {
                BuildAtlasMaterials();
                BuildProductPrefabs();
            }
            finally
            {
                AssetDatabase.SaveAssets();
            }
        }

        [MenuItem("KALI/JC/Build Equipment Prefabs")]
        public static void BuildEquipmentPrefabsMenu()
        {
            try
            {
                BuildAtlasMaterials();
                BuildEquipmentPrefabs();
            }
            finally
            {
                AssetDatabase.SaveAssets();
            }
        }

        [MenuItem("KALI/JC/Build Atlas Materials")]
        public static void BuildAtlasMaterialsMenu()
        {
            try
            {
                BuildAtlasMaterials();
            }
            finally
            {
                AssetDatabase.SaveAssets();
            }
        }

        [MenuItem("KALI/JC/Build Excavator Prefab")]
        public static void BuildExcavatorPrefabMenu()
        {
            try
            {
                bool ok = BuildExcavatorPrefab();
                Debug.Log(LogPrefix + "Build Excavator Prefab result: " + (ok ? "SUCCESS" : "FAILED"));
            }
            finally
            {
                AssetDatabase.SaveAssets();
            }
        }

        [MenuItem("KALI/JC/Build All JC Prefabs")]
        public static void BuildAllJcPrefabs()
        {
            int atlasCount = 0;
            int trashBuilt = 0;
            int trashFailed = 0;
            int toolBuilt = 0;
            int toolFailed = 0;
            int productBuilt = 0;
            int productFailed = 0;
            int equipmentBuilt = 0;
            int equipmentFailed = 0;
            bool excavatorBuilt = false;

            try
            {
                // 3. Atlas materials first, so the prefab steps can assign them.
                atlasCount = BuildAtlasMaterials();

                // 1. Trash prefabs.
                BuildPrefabsFromFolder(TrashMeshFolder, TrashMeshPattern, TrashPrefabFolder, "PF_Trash_",
                    LoadTrashMaterial(), BuildTrashPrefab, out trashBuilt, out trashFailed);

                // 2. Tool prefabs.
                BuildPrefabsFromFolder(ToolMeshFolder, ToolMeshPattern, ToolPrefabFolder, "PF_Tool_",
                    LoadToolMaterial(), BuildToolPrefab, out toolBuilt, out toolFailed);

                // 2b. Product prefabs (clean shop / world items).
                BuildPrefabsFromFolder(ProductMeshFolder, ProductMeshPattern, ProductPrefabFolder, "PF_Product_",
                    LoadProductMaterial(), BuildProductPrefab, out productBuilt, out productFailed);

                // 2c. Equipment prefabs (trash boom, boats, kampung bin).
                BuildPrefabsFromFolder(EquipmentMeshFolder, EquipmentMeshPattern, EquipmentPrefabFolder, "PF_Prop_",
                    LoadEquipmentMaterial(), BuildEquipmentPrefab, out equipmentBuilt, out equipmentFailed);

                // 4. Excavator prefab & materials.
                excavatorBuilt = BuildExcavatorPrefab();
            }
            finally
            {
                AssetDatabase.SaveAssets();
                Debug.Log(LogPrefix + "Build All JC Prefabs summary: atlas materials ok=" + atlasCount
                          + " | trash prefabs built=" + trashBuilt + " failed=" + trashFailed
                          + " | tool prefabs built=" + toolBuilt + " failed=" + toolFailed
                          + " | product prefabs built=" + productBuilt + " failed=" + productFailed
                          + " | equipment prefabs built=" + equipmentBuilt + " failed=" + equipmentFailed
                          + " | excavator built=" + excavatorBuilt);
            }
        }

        // ------------------------------------------------------------------
        // 3. Atlas materials
        // ------------------------------------------------------------------

        /// <summary>Configures the atlas textures and creates/updates the URP Lit atlas materials. Returns materials ok.</summary>
        private static int BuildAtlasMaterials()
        {
            EnsureFolder(TrashTextureFolder);
            EnsureFolder(TrashMaterialFolder);
            EnsureFolder(ToolTextureFolder);
            EnsureFolder(ToolMaterialFolder);
            EnsureFolder(ProductTextureFolder);
            EnsureFolder(ProductMaterialFolder);
            EnsureFolder(EquipmentTextureFolder);
            EnsureFolder(EquipmentMaterialFolder);

            AssetDatabase.StartAssetEditing();
            try
            {
                // Trash atlas carries painted brand labels: smooth filtering + mipmaps so they read at distance.
                ConfigureAtlasTextures(TrashTextureFolder, TrashAtlasBaseName, smoothAlbedo: true);
                ConfigureAtlasTextures(ToolTextureFolder, ToolAtlasBaseName, smoothAlbedo: false);
                ConfigureAtlasTextures(ProductTextureFolder, ProductAtlasBaseName, smoothAlbedo: true);
                ConfigureAtlasTextures(EquipmentTextureFolder, EquipmentAtlasBaseName, smoothAlbedo: true);
                // Equipment only: emission mask (white on bulb / lens), sRGB, bilinear + mipmaps.
                ConfigureTextureImporter(EquipmentTextureFolder + "/" + EquipmentAtlasBaseName + "_Emission.png",
                    TextureImporterType.Default, true, false);
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
            }

            int ok = 0;
            if (CreateOrUpdateAtlasMaterial(TrashMaterialPath, TrashTextureFolder, TrashAtlasBaseName)) ok++;
            if (CreateOrUpdateAtlasMaterial(ToolMaterialPath, ToolTextureFolder, ToolAtlasBaseName)) ok++;
            if (CreateOrUpdateAtlasMaterial(ProductMaterialPath, ProductTextureFolder, ProductAtlasBaseName)) ok++;
            if (CreateOrUpdateAtlasMaterial(EquipmentMaterialPath, EquipmentTextureFolder, EquipmentAtlasBaseName)) ok++;

            AssetDatabase.SaveAssets();
            Debug.Log(LogPrefix + "Atlas materials ready: " + ok + "/4 (" + TrashMaterialPath + ", " + ToolMaterialPath
                      + ", " + ProductMaterialPath + ", " + EquipmentMaterialPath + ")");
            return ok;
        }

        private static void ConfigureAtlasTextures(string textureFolder, string baseName, bool smoothAlbedo)
        {
            // Albedo: sRGB colour, point filter for flat colour swatches, bilinear + mipmaps for painted labels.
            ConfigureTextureImporter(textureFolder + "/" + baseName + "_Albedo.png",
                TextureImporterType.Default, true, !smoothAlbedo);
            // Normal: NormalMap import type (linear).
            ConfigureTextureImporter(textureFolder + "/" + baseName + "_Normal.png",
                TextureImporterType.NormalMap, false, false);
            // Mask: linear data (metallic R, smoothness A), point filter.
            ConfigureTextureImporter(textureFolder + "/" + baseName + "_Mask.png",
                TextureImporterType.Default, false, true);
        }

        private static void ConfigureTextureImporter(string assetPath, TextureImporterType type, bool sRGB, bool pointFilter)
        {
            TextureImporter importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
            if (importer == null)
            {
                Debug.LogWarning(LogPrefix + "Atlas texture missing, skipped import settings: " + assetPath);
                return;
            }

            importer.textureType = type;
            importer.sRGBTexture = sRGB;
            importer.maxTextureSize = AtlasMaxTextureSize;
            if (pointFilter)
            {
                importer.filterMode = FilterMode.Point;
                // Atlas swatch colours must not bleed into far mip levels.
                importer.mipmapEnabled = false;
            }
            else if (type == TextureImporterType.Default)
            {
                // Reset in case an earlier run imported this texture with point filter / no mipmaps.
                importer.filterMode = FilterMode.Bilinear;
                importer.mipmapEnabled = true;
            }

            importer.SaveAndReimport();
        }

        private static bool CreateOrUpdateAtlasMaterial(string materialPath, string textureFolder, string baseName)
        {
            Shader shader = Shader.Find(UrpLitShader);
            if (shader == null)
            {
                Debug.LogError(LogPrefix + "Shader '" + UrpLitShader + "' not found. Is URP installed? Skipping " + materialPath);
                return false;
            }

            Material mat = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            if (mat == null)
            {
                mat = new Material(shader);
                AssetDatabase.CreateAsset(mat, materialPath);
            }
            else if (mat.shader != shader)
            {
                mat.shader = shader;
            }

            Texture2D albedo = LoadTexture(textureFolder + "/" + baseName + "_Albedo.png");
            Texture2D normal = LoadTexture(textureFolder + "/" + baseName + "_Normal.png");
            Texture2D mask = LoadTexture(textureFolder + "/" + baseName + "_Mask.png");

            if (albedo != null)
            {
                mat.SetTexture("_BaseMap", albedo);
            }

            if (normal != null)
            {
                mat.SetTexture("_BumpMap", normal);
                mat.SetFloat("_BumpScale", 1f);
                mat.EnableKeyword("_NORMALMAP");
            }

            if (mask != null)
            {
                mat.SetTexture("_MetallicGlossMap", mask);
                mat.EnableKeyword("_METALLICSPECGLOSSMAP");
                // Smoothness comes from the mask alpha (SmoothnessTextureChannel 0 = Metallic Alpha).
                mat.SetFloat("_SmoothnessTextureChannel", 0f);
                mat.SetFloat("_Smoothness", 1f);
                mat.SetFloat("_Metallic", 1f);
            }

            // Optional emission mask (only the equipment atlas has one): emission = map x _EmissionColor, so only the
            // white parts (lantern bulb, beacon lens) glow. Same values as KaliLightingPropsBuilder.LoadOrCreateEquipmentMaterial.
            Texture2D emission = AssetDatabase.LoadAssetAtPath<Texture2D>(textureFolder + "/" + baseName + "_Emission.png");
            if (emission != null)
            {
                mat.SetTexture("_EmissionMap", emission);
                mat.EnableKeyword("_EMISSION");
                mat.SetColor("_EmissionColor", new Color(1f, 0.69f, 0.30f) * 2f);
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }

            EditorUtility.SetDirty(mat);
            return true;
        }

        private static Texture2D LoadTexture(string assetPath)
        {
            Texture2D tex = AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
            if (tex == null)
            {
                Debug.LogWarning(LogPrefix + "Atlas texture not found (drop the PNG in and rerun): " + assetPath);
            }

            return tex;
        }

        // ------------------------------------------------------------------
        // 1. Trash prefabs
        // ------------------------------------------------------------------

        private static Material LoadTrashMaterial()
        {
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(TrashMaterialPath);
            if (mat == null)
            {
                Debug.LogWarning(LogPrefix + "Material not found: " + TrashMaterialPath + " (run Build Atlas Materials)");
            }

            return mat;
        }

        private static void BuildTrashPrefabs()
        {
            Material mat = LoadTrashMaterial();
            int built;
            int failed;
            BuildPrefabsFromFolder(TrashMeshFolder, TrashMeshPattern, TrashPrefabFolder, "PF_Trash_",
                mat, BuildTrashPrefab, out built, out failed);
        }

        private static bool BuildTrashPrefab(MeshEntry entry, string prefabPath, Material mat)
        {
            Type buoyancyType = FindComponentType(BuoyancyTypeName);
            Type trashItemType = FindComponentType(TrashItemTypeName);

            GameObject root = InstantiateUnpacked(entry);
            if (root == null)
            {
                return false;
            }

            try
            {
                ApplyMaterial(root, mat);

                Bounds localBounds;
                if (!TryGetLocalBounds(root, out localBounds))
                {
                    Debug.LogError(LogPrefix + "No mesh bounds found in " + entry.AssetPath);
                    return false;
                }

                // Convex MeshCollider would exceed PhysX's 255-polygon convex limit for these props.
                BoxCollider box = root.AddComponent<BoxCollider>();
                box.isTrigger = false;
                box.center = localBounds.center;
                box.size = localBounds.size;

                // Kinematic: RiverFlowBuoyancy drives transform.position in Update().
                Rigidbody rb = root.AddComponent<Rigidbody>();
                rb.mass = TrashMass;
                rb.drag = TrashDrag;
                rb.angularDrag = TrashAngularDrag;
                rb.isKinematic = true;

                if (buoyancyType != null)
                {
                    root.AddComponent(buoyancyType);
                }

                if (trashItemType != null)
                {
                    Component trashComp = root.AddComponent(trashItemType);
                    // Infer WasteClass: Medical=1 if entry.Variant contains "Medical" or "Syringe",
                    // Biohazard=2 if entry.Variant contains "Biohazard" or "Radioactive" or "Drum", else Normal=0.
                    int wasteClassVal = 0;
                    string vUpper = entry.Variant != null ? entry.Variant.ToUpperInvariant() : string.Empty;
                    if (vUpper.Contains("BIOHAZARD") || vUpper.Contains("RADIOACTIVE") || vUpper.Contains("DRUM"))
                    {
                        wasteClassVal = 2; // WasteClass.Biohazard
                    }
                    else if (vUpper.Contains("MEDICAL") || vUpper.Contains("SYRINGE"))
                    {
                        wasteClassVal = 1; // WasteClass.Medical
                    }

                    var wasteClassField = trashItemType.GetField("wasteClass");
                    if (wasteClassField != null)
                    {
                        wasteClassField.SetValue(trashComp, Enum.ToObject(wasteClassField.FieldType, wasteClassVal));
                    }
                }

                return SavePrefab(root, prefabPath);
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        // ------------------------------------------------------------------
        // 2. Tool prefabs
        // ------------------------------------------------------------------

        private static Material LoadToolMaterial()
        {
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(ToolMaterialPath);
            if (mat == null)
            {
                Debug.LogWarning(LogPrefix + "Material not found: " + ToolMaterialPath + " (run Build Atlas Materials)");
            }

            return mat;
        }

        private static void BuildToolPrefabs()
        {
            Material mat = LoadToolMaterial();
            int built;
            int failed;
            BuildPrefabsFromFolder(ToolMeshFolder, ToolMeshPattern, ToolPrefabFolder, "PF_Tool_",
                mat, BuildToolPrefab, out built, out failed);
        }

        private static bool BuildToolPrefab(MeshEntry entry, string prefabPath, Material mat)
        {
            GameObject root = InstantiateUnpacked(entry);
            if (root == null)
            {
                return false;
            }

            try
            {
                if (!IsIdentity(root.transform))
                {
                    // Root is left as imported so the grip pivot (Blender origin) is preserved.
                    Debug.LogWarning(LogPrefix + entry.AssetPath + ": root transform is not identity (pos "
                                     + root.transform.localPosition + ", rot " + root.transform.localEulerAngles
                                     + ", scale " + root.transform.localScale + "). Check FBX export/import scale.");
                }

                ApplyMaterial(root, mat);

                Bounds localBounds;
                if (!TryGetLocalBounds(root, out localBounds))
                {
                    Debug.LogError(LogPrefix + "No mesh bounds found in " + entry.AssetPath);
                    return false;
                }

                BoxCollider box = root.AddComponent<BoxCollider>();
                // Equipped tools must never block CharacterController or scoop raycasts
                box.isTrigger = true;
                box.center = localBounds.center;
                box.size = localBounds.size;

                return SavePrefab(root, prefabPath);
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        // ------------------------------------------------------------------
        // 2b. Product prefabs (clean shop / world items: no Rigidbody, no RiverTrashItem)
        // ------------------------------------------------------------------

        private static Material LoadProductMaterial()
        {
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(ProductMaterialPath);
            if (mat == null)
            {
                Debug.LogWarning(LogPrefix + "Material not found: " + ProductMaterialPath + " (run Build Atlas Materials)");
            }

            return mat;
        }

        private static void BuildProductPrefabs()
        {
            Material mat = LoadProductMaterial();
            int built;
            int failed;
            BuildPrefabsFromFolder(ProductMeshFolder, ProductMeshPattern, ProductPrefabFolder, "PF_Product_",
                mat, BuildProductPrefab, out built, out failed);
        }

        private static bool BuildProductPrefab(MeshEntry entry, string prefabPath, Material mat)
        {
            GameObject root = InstantiateUnpacked(entry);
            if (root == null)
            {
                return false;
            }

            try
            {
                ApplyMaterial(root, mat);

                Bounds localBounds;
                if (!TryGetLocalBounds(root, out localBounds))
                {
                    Debug.LogError(LogPrefix + "No mesh bounds found in " + entry.AssetPath);
                    return false;
                }

                // Solid, static shop / world item: the mesh origin is its base, so the prefab sits on whatever it is placed on.
                BoxCollider box = root.AddComponent<BoxCollider>();
                box.isTrigger = false;
                box.center = localBounds.center;
                box.size = localBounds.size;

                return SavePrefab(root, prefabPath);
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        // ------------------------------------------------------------------
        // 2c. Equipment prefabs (trash boom, rakit, sampan, kampung bin: collider only, no Rigidbody / RiverTrashItem)
        // ------------------------------------------------------------------

        private static Material LoadEquipmentMaterial()
        {
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(EquipmentMaterialPath);
            if (mat == null)
            {
                Debug.LogWarning(LogPrefix + "Material not found: " + EquipmentMaterialPath + " (run Build Atlas Materials)");
            }

            return mat;
        }

        private static void BuildEquipmentPrefabs()
        {
            Material mat = LoadEquipmentMaterial();
            int built;
            int failed;
            BuildPrefabsFromFolder(EquipmentMeshFolder, EquipmentMeshPattern, EquipmentPrefabFolder, "PF_Prop_",
                mat, BuildEquipmentPrefab, out built, out failed);
        }

        // Boom and boats keep their Blender waterline origin (importer places "trash_boom" at y = 0); the bin keeps its
        // base origin. Same body as BuildProductPrefab: material + solid fitted BoxCollider.
        private static bool BuildEquipmentPrefab(MeshEntry entry, string prefabPath, Material mat)
        {
            return BuildProductPrefab(entry, prefabPath, mat);
        }

        // ------------------------------------------------------------------
        // 5. Excavator Prefab & URP Material Support
        // ------------------------------------------------------------------

        private static bool BuildExcavatorPrefab()
        {
            EnsureFolder(RiggingMaterialFolder);

            Shader shader = Shader.Find(UrpLitShader);
            if (shader == null)
            {
                Debug.LogError(LogPrefix + "Shader '" + UrpLitShader + "' not found. Cannot build Excavator materials.");
                return false;
            }

            Material bodyMat = GetOrCreateExcavatorMaterial(ExcavatorBodyMatPath, shader, new Color(0.9176f, 0.6902f, 0.0314f), 0.15f, 0.45f); // #eab308
            Material steelMat = GetOrCreateExcavatorMaterial(ExcavatorSteelMatPath, shader, new Color(0.8863f, 0.9098f, 0.9412f), 0.95f, 0.90f); // #e2e8f0
            Material rubberMat = GetOrCreateExcavatorMaterial(ExcavatorRubberMatPath, shader, new Color(0.1176f, 0.1608f, 0.2314f), 0.0f, 0.20f);  // #1e293b

            GameObject model = AssetDatabase.LoadAssetAtPath<GameObject>(ExcavatorModelPath);
            if (model == null)
            {
                Debug.LogWarning(LogPrefix + "Excavator model not found at " + ExcavatorModelPath + ". Skipping excavator prefab.");
                return false;
            }

            GameObject instance = PrefabUtility.InstantiatePrefab(model) as GameObject;
            if (instance == null)
            {
                Debug.LogError(LogPrefix + "Could not instantiate excavator model " + ExcavatorModelPath);
                return false;
            }

            PrefabUtility.UnpackPrefabInstance(instance, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            instance.name = "PF_ExcavatorAmfibi";

            try
            {
                // Remap Renderer slots by existing material name substring
                foreach (Renderer r in instance.GetComponentsInChildren<Renderer>(true))
                {
                    Material[] oldMats = r.sharedMaterials;
                    Material[] newMats = new Material[oldMats.Length];
                    for (int i = 0; i < oldMats.Length; i++)
                    {
                        string mName = oldMats[i] != null ? oldMats[i].name.ToLowerInvariant() : string.Empty;
                        if (mName.Contains("steel") || mName.Contains("hydraulic") || mName.Contains("metal"))
                        {
                            newMats[i] = steelMat;
                        }
                        else if (mName.Contains("rubber") || mName.Contains("pontoon") || mName.Contains("track"))
                        {
                            newMats[i] = rubberMat;
                        }
                        else
                        {
                            // Default / Body
                            newMats[i] = bodyMat;
                        }
                    }
                    r.sharedMaterials = newMats;
                }

                Bounds localBounds;
                if (TryGetLocalBounds(instance, out localBounds))
                {
                    BoxCollider box = instance.AddComponent<BoxCollider>();
                    box.isTrigger = false;
                    box.center = localBounds.center;
                    box.size = localBounds.size;
                }
                else
                {
                    Debug.LogWarning(LogPrefix + "Excavator model has no mesh bounds; skipping BoxCollider generation.");
                }

                bool success = SavePrefab(instance, ExcavatorPrefabPath);
                Debug.Log(LogPrefix + (success ? "Successfully built excavator prefab at " + ExcavatorPrefabPath : "Failed to save excavator prefab."));
                return success;
            }
            finally
            {
                Object.DestroyImmediate(instance);
            }
        }

        private static Material GetOrCreateExcavatorMaterial(string matPath, Shader shader, Color baseColor, float metallic, float smoothness)
        {
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
            if (mat == null)
            {
                mat = new Material(shader);
                AssetDatabase.CreateAsset(mat, matPath);
            }
            else if (mat.shader != shader)
            {
                mat.shader = shader;
            }

            mat.SetColor("_BaseColor", baseColor);
            mat.SetFloat("_Metallic", metallic);
            mat.SetFloat("_Smoothness", smoothness);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        // ------------------------------------------------------------------
        // Shared helpers
        // ------------------------------------------------------------------

        private delegate bool PrefabBuilder(MeshEntry entry, string prefabPath, Material mat);

        private static void BuildPrefabsFromFolder(string meshFolder, string meshPattern, string prefabFolder,
            string prefabPrefix, Material mat, PrefabBuilder builder, out int built, out int failed)
        {
            built = 0;
            failed = 0;

            EnsureFolder(meshFolder);
            EnsureFolder(prefabFolder);

            List<MeshEntry> entries = FindMeshEntries(meshFolder, meshPattern);
            if (entries.Count == 0)
            {
                Debug.LogWarning(LogPrefix + "No FBX matching '" + meshPattern + "' in " + meshFolder);
                return;
            }

            foreach (MeshEntry entry in entries)
            {
                string prefabPath = prefabFolder + "/" + prefabPrefix + entry.Variant + ".prefab";
                try
                {
                    if (builder(entry, prefabPath, mat))
                    {
                        built++;
                        Debug.Log(LogPrefix + "Saved " + prefabPath);
                    }
                    else
                    {
                        failed++;
                        Debug.LogError(LogPrefix + "Failed to save " + prefabPath);
                    }
                }
                catch (Exception e)
                {
                    failed++;
                    Debug.LogError(LogPrefix + "Exception building " + prefabPath + ": " + e);
                }
            }
        }

        private static List<MeshEntry> FindMeshEntries(string folder, string pattern)
        {
            var result = new List<MeshEntry>();
            if (!AssetDatabase.IsValidFolder(folder))
            {
                return result;
            }

            var regex = new Regex(pattern);
            string[] guids = AssetDatabase.FindAssets("t:Model", new[] { folder });
            foreach (string guid in guids)
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                Match m = regex.Match(Path.GetFileName(path));
                if (m.Success)
                {
                    result.Add(new MeshEntry { Variant = m.Groups[1].Value, AssetPath = path });
                }
            }

            result.Sort((a, b) => string.CompareOrdinal(a.Variant, b.Variant));
            return result;
        }

        private static GameObject InstantiateUnpacked(MeshEntry entry)
        {
            GameObject model = AssetDatabase.LoadAssetAtPath<GameObject>(entry.AssetPath);
            if (model == null)
            {
                Debug.LogError(LogPrefix + "Could not load model " + entry.AssetPath);
                return null;
            }

            GameObject instance = PrefabUtility.InstantiatePrefab(model) as GameObject;
            if (instance == null)
            {
                Debug.LogError(LogPrefix + "Could not instantiate " + entry.AssetPath);
                return null;
            }

            PrefabUtility.UnpackPrefabInstance(instance, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            string prefix = entry.AssetPath.Contains("SM_Tool_") ? "PF_Tool_"
                : entry.AssetPath.Contains("SM_Product_") ? "PF_Product_"
                : entry.AssetPath.Contains("SM_Prop_") ? "PF_Prop_" : "PF_Trash_";
            instance.name = prefix + entry.Variant;
            return instance;
        }

        private static bool SavePrefab(GameObject root, string prefabPath)
        {
            bool success;
            PrefabUtility.SaveAsPrefabAsset(root, prefabPath, out success);
            return success;
        }

        private static void ApplyMaterial(GameObject root, Material mat)
        {
            if (mat == null)
            {
                return;
            }

            foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
            {
                Material[] mats = new Material[Mathf.Max(1, r.sharedMaterials.Length)];
                for (int i = 0; i < mats.Length; i++)
                {
                    mats[i] = mat;
                }

                r.sharedMaterials = mats;
            }
        }

        private static Type FindComponentType(string typeName)
        {
            foreach (Type t in TypeCache.GetTypesDerivedFrom<MonoBehaviour>())
            {
                if (t.Name == typeName && !t.IsAbstract)
                {
                    return t;
                }
            }

            Debug.LogWarning(LogPrefix + "Component '" + typeName + "' not found.");
            return null;
        }

        private static bool TryGetLocalBounds(GameObject root, out Bounds localBounds)
        {
            localBounds = new Bounds();
            bool any = false;

            // Handle BOTH MeshFilter.sharedMesh AND SkinnedMeshRenderer.sharedMesh via clean shared helper loop
            foreach (MeshFilter mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                if (mf.sharedMesh != null)
                {
                    AddMeshBoundsToRoot(root, mf.transform, mf.sharedMesh, ref localBounds, ref any);
                }
            }

            foreach (SkinnedMeshRenderer smr in root.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                if (smr.sharedMesh != null)
                {
                    AddMeshBoundsToRoot(root, smr.transform, smr.sharedMesh, ref localBounds, ref any);
                }
            }

            return any;
        }

        private static void AddMeshBoundsToRoot(GameObject root, Transform meshTransform, Mesh mesh, ref Bounds localBounds, ref bool any)
        {
            Bounds mb = mesh.bounds;
            Vector3 min = mb.min;
            Vector3 max = mb.max;
            for (int i = 0; i < 8; i++)
            {
                Vector3 corner = new Vector3(
                    (i & 1) == 0 ? min.x : max.x,
                    (i & 2) == 0 ? min.y : max.y,
                    (i & 4) == 0 ? min.z : max.z);
                Vector3 local = root.transform.InverseTransformPoint(meshTransform.TransformPoint(corner));

                if (!any)
                {
                    localBounds = new Bounds(local, Vector3.zero);
                    any = true;
                }
                else
                {
                    localBounds.Encapsulate(local);
                }
            }
        }

        private static bool IsIdentity(Transform t)
        {
            return t.localPosition == Vector3.zero
                   && t.localRotation == Quaternion.identity
                   && t.localScale == Vector3.one;
        }

        /// <summary>Creates each folder segment under Assets/ with AssetDatabase.CreateFolder when missing.</summary>
        private static void EnsureFolder(string assetFolder)
        {
            string[] parts = assetFolder.Split('/');
            string current = parts[0];
            for (int i = 1; i < parts.Length; i++)
            {
                string next = current + "/" + parts[i];
                if (!AssetDatabase.IsValidFolder(next))
                {
                    AssetDatabase.CreateFolder(current, parts[i]);
                }

                current = next;
            }
        }
    }
}
