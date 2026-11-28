#if UNITY_EDITOR
using KaliRiverSweeper.Core;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace KaliRiverSweeper.Lighting.Editor
{
    /// <summary>
    /// Idempotent builder for KALI's procedural skybox material, URP VolumeProfile,
    /// and PF_LightingRig prefab (Sun + Global Volume + KaliDayNightCycle).
    /// </summary>
    public static class KaliLightingBuilder
    {
        public const string SkyMaterialPath = "Assets/_Project/Lighting/Materials/M_KaliSky.mat";
        public const string VolumeProfilePath = "Assets/_Project/Lighting/VolumeProfiles/VP_KaliSky.asset";
        public const string RigPrefabPath = "Assets/_Project/Lighting/Prefabs/PF_LightingRig.prefab";

        [MenuItem("KALI/Lighting/Build Sky & Lighting Rig")]
        public static void BuildSkyAndLightingRig()
        {
            Shader skyShader = Shader.Find("KALI/Sky");
            if (skyShader == null)
            {
                Debug.LogError("[KALI] Shader 'KALI/Sky' not found. Build aborted.");
                return;
            }

            EnsureFolder("Assets/_Project", "Lighting");
            EnsureFolder("Assets/_Project/Lighting", "Materials");
            EnsureFolder("Assets/_Project/Lighting", "VolumeProfiles");
            EnsureFolder("Assets/_Project/Lighting", "Prefabs");

            Material skyMat = CreateOrUpdateSkyMaterial(skyShader);
            VolumeProfile profile = CreateOrUpdateVolumeProfile();
            CreateOrUpdateLightingRigPrefab(profile);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"[KALI] Built Sky & Lighting Rig: {skyMat.name}, {profile.name}, PF_LightingRig.");
        }

        private static Material CreateOrUpdateSkyMaterial(Shader skyShader)
        {
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(SkyMaterialPath);
            if (mat == null)
            {
                mat = new Material(skyShader);
                AssetDatabase.CreateAsset(mat, SkyMaterialPath);
            }
            else if (mat.shader != skyShader)
            {
                mat.shader = skyShader;
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }

        private static VolumeProfile CreateOrUpdateVolumeProfile()
        {
            VolumeProfile profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(VolumeProfilePath);
            if (profile == null)
            {
                profile = ScriptableObject.CreateInstance<VolumeProfile>();
                AssetDatabase.CreateAsset(profile, VolumeProfilePath);
            }

            Bloom bloom = GetOrAddOverride<Bloom>(profile);
            bloom.threshold.Override(0.9f);
            bloom.intensity.Override(0.55f);
            bloom.scatter.Override(0.7f);

            Tonemapping tonemapping = GetOrAddOverride<Tonemapping>(profile);
            tonemapping.mode.Override(TonemappingMode.Neutral);

            ColorAdjustments colorAdj = GetOrAddOverride<ColorAdjustments>(profile);
            colorAdj.postExposure.Override(0.10f);
            colorAdj.contrast.Override(6f);
            colorAdj.saturation.Override(6f);
            colorAdj.colorFilter.Override(Color.white);

            Vignette vignette = GetOrAddOverride<Vignette>(profile);
            vignette.intensity.Override(0.20f);
            vignette.smoothness.Override(0.40f);

            EditorUtility.SetDirty(profile);
            return profile;
        }

        private static T GetOrAddOverride<T>(VolumeProfile profile) where T : VolumeComponent
        {
            if (!profile.TryGet(out T component))
            {
                component = profile.Add<T>(true);
                AssetDatabase.AddObjectToAsset(component, profile);
            }
            component.active = true;
            return component;
        }

        private static void CreateOrUpdateLightingRigPrefab(VolumeProfile profile)
        {
            GameObject root = new GameObject("PF_LightingRig");
            try
            {
                KaliDayNightCycle cycle = root.AddComponent<KaliDayNightCycle>();

                GameObject sunGo = new GameObject("Sun");
                sunGo.transform.SetParent(root.transform, false);
                Light sun = sunGo.AddComponent<Light>();
                sun.type = LightType.Directional;
                sun.shadows = LightShadows.Soft;
                sun.shadowStrength = 0.85f;
                sun.color = new Color(1f, 0.84f, 0.60f);
                sun.intensity = 1.75f;

                GameObject volGo = new GameObject("Global Volume");
                volGo.transform.SetParent(root.transform, false);
                Volume vol = volGo.AddComponent<Volume>();
                vol.isGlobal = true;
                vol.priority = 1f;
                vol.sharedProfile = profile;

                cycle.enabled = true;
                cycle.sunLight = sun;
                cycle.globalVolume = vol;
                cycle.SetHour(cycle.startHour);

                PrefabUtility.SaveAsPrefabAsset(root, RigPrefabPath);
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        private static void EnsureFolder(string parent, string name)
        {
            if (!AssetDatabase.IsValidFolder(parent + "/" + name))
            {
                AssetDatabase.CreateFolder(parent, name);
            }
        }
    }
}
#endif
