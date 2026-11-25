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
    /// Turns JC's FBX meshes (Props/Trash/Meshes, Props/Tools/Meshes) into prefabs and builds the
    /// shared 2048 atlas URP Lit materials. Editor-only (lives in an Editor folder).
    /// </summary>
    public static class KaliPropPrefabBuilder
    {
        private const string LogPrefix = "[KALI JC] ";

        private const string PropsRoot = "Assets/_Project/Props";

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

        private const string TrashMeshPattern = @"^SM_Trash_(.+)\.fbx$";
        private const string ToolMeshPattern = @"^SM_Tool_(.+)\.fbx$";

        private const string UrpLitShader = "Universal Render Pipeline/Lit";
        private const string BuoyancyTypeName = "RiverFlowBuoyancy";

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

        [MenuItem("KALI/JC/Build All JC Prefabs")]
        public static void BuildAllJcPrefabs()
        {
            int atlasCount = 0;
            int trashBuilt = 0;
            int trashFailed = 0;
            int toolBuilt = 0;
            int toolFailed = 0;

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
            }
            finally
            {
                AssetDatabase.SaveAssets();
                Debug.Log(LogPrefix + "Build All JC Prefabs summary: atlas materials ok=" + atlasCount
                          + " | trash prefabs built=" + trashBuilt + " failed=" + trashFailed
                          + " | tool prefabs built=" + toolBuilt + " failed=" + toolFailed);
            }
        }

        // ------------------------------------------------------------------
        // 3. Atlas materials
        // ------------------------------------------------------------------

        /// <summary>Configures the atlas textures and creates/updates both URP Lit atlas materials. Returns materials ok.</summary>
        private static int BuildAtlasMaterials()
        {
            EnsureFolder(TrashTextureFolder);
            EnsureFolder(TrashMaterialFolder);
            EnsureFolder(ToolTextureFolder);
            EnsureFolder(ToolMaterialFolder);

            AssetDatabase.StartAssetEditing();
            try
            {
                ConfigureAtlasTextures(TrashTextureFolder, TrashAtlasBaseName);
                ConfigureAtlasTextures(ToolTextureFolder, ToolAtlasBaseName);
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
            }

            int ok = 0;
            if (CreateOrUpdateAtlasMaterial(TrashMaterialPath, TrashTextureFolder, TrashAtlasBaseName)) ok++;
            if (CreateOrUpdateAtlasMaterial(ToolMaterialPath, ToolTextureFolder, ToolAtlasBaseName)) ok++;

            AssetDatabase.SaveAssets();
            Debug.Log(LogPrefix + "Atlas materials ready: " + ok + "/2 (" + TrashMaterialPath + ", " + ToolMaterialPath + ")");
            return ok;
        }

        private static void ConfigureAtlasTextures(string textureFolder, string baseName)
        {
            // Albedo: sRGB colour, point filter (flat colour swatches).
            ConfigureTextureImporter(textureFolder + "/" + baseName + "_Albedo.png",
                TextureImporterType.Default, true, true);
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
            Type buoyancyType = FindBuoyancyType();

            GameObject root = InstantiateUnpacked(entry);
            if (root == null)
            {
                return false;
            }

            try
            {
                MeshFilter mf = root.GetComponentInChildren<MeshFilter>(true);
                if (mf == null || mf.sharedMesh == null)
                {
                    Debug.LogError(LogPrefix + "No MeshFilter/mesh found in " + entry.AssetPath);
                    return false;
                }

                if (mf.gameObject != root)
                {
                    Debug.LogWarning(LogPrefix + entry.AssetPath + ": mesh is on child '" + mf.gameObject.name
                                     + "', the MeshCollider is put on the root and uses its mesh.");
                }

                ApplyMaterial(root, mat);

                MeshCollider mc = root.AddComponent<MeshCollider>();
                mc.convex = true;
                mc.sharedMesh = mf.sharedMesh;

                Rigidbody rb = root.AddComponent<Rigidbody>();
                rb.mass = TrashMass;
                rb.drag = TrashDrag;
                rb.angularDrag = TrashAngularDrag;

                if (buoyancyType != null)
                {
                    root.AddComponent(buoyancyType);
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
            instance.name = (entry.AssetPath.Contains("SM_Tool_") ? "PF_Tool_" : "PF_Trash_") + entry.Variant;
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

        private static Type FindBuoyancyType()
        {
            foreach (Type t in TypeCache.GetTypesDerivedFrom<MonoBehaviour>())
            {
                if (t.Name == BuoyancyTypeName && !t.IsAbstract)
                {
                    return t;
                }
            }

            Debug.LogWarning(LogPrefix + "Component '" + BuoyancyTypeName
                             + "' not found; trash prefabs are built without buoyancy.");
            return null;
        }

        private static bool TryGetLocalBounds(GameObject root, out Bounds localBounds)
        {
            localBounds = new Bounds();
            bool any = false;

            foreach (MeshFilter mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                if (mf.sharedMesh == null)
                {
                    continue;
                }

                Bounds mb = mf.sharedMesh.bounds;
                Vector3 min = mb.min;
                Vector3 max = mb.max;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = new Vector3(
                        (i & 1) == 0 ? min.x : max.x,
                        (i & 2) == 0 ? min.y : max.y,
                        (i & 4) == 0 ? min.z : max.z);
                    Vector3 local = root.transform.InverseTransformPoint(mf.transform.TransformPoint(corner));

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

            return any;
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
