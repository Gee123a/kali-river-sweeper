using UnityEngine;
using UnityEngine.Rendering;
using KaliRiverSweeper.Core;

namespace KaliRiverSweeper.Lighting
{
    public enum LightingPreset
    {
        GoldenHour = 0,   // Act 1 & Clean River ending
        MonsoonStorm = 1  // Act 3 Siaga 1 climax
    }

    [System.Serializable]
    public class PresetSettings
    {
        public Color sunColor = Color.white;
        public float sunKelvin = 6500f;
        public float sunIntensity = 1f;
        public Vector3 sunEuler = new Vector3(50f, -30f, 0f);
        public Color fogColor = Color.grey;
        public float fogDensity = 0.01f;
        public float ambientIntensity = 1f;
    }

    /// <summary>
    /// Switches between the two story lighting scenarios with a smooth blend.
    /// Reads RiverGameManager.isMonsoonStorm (read-only) so Ivan's state machine drives it
    /// without any change to his scripts. Can also be called directly: SetPreset(...).
    /// </summary>
    public class LightingPresetSwitcher : MonoBehaviour
    {
        [Header("Scene references")]
        public Light sun;
        public Volume goldenHourVolume;
        public Volume monsoonVolume;
        public Material goldenHourSkybox;
        public Material monsoonSkybox;

        [Header("Behaviour")]
        public LightingPreset startPreset = LightingPreset.GoldenHour;
        public float transitionSeconds = 6f;
        [Tooltip("Follow RiverGameManager.isMonsoonStorm automatically.")]
        public bool followGameManager = true;

        [Header("Tropical Golden Hour (#FFE2A3, 3400K, intensity 2.2)")]
        public PresetSettings golden = new PresetSettings
        {
            sunColor = new Color(1f, 0.886f, 0.639f),
            sunKelvin = 3400f,
            sunIntensity = 2.2f,
            sunEuler = new Vector3(18f, -35f, 0f),
            fogColor = new Color(1f, 0.82f, 0.62f),
            fogDensity = 0.004f,
            ambientIntensity = 1f
        };

        [Header("Monsoon Storm (#7A8B99, intensity 0.6, fog 0.04)")]
        public PresetSettings monsoon = new PresetSettings
        {
            sunColor = new Color(0.478f, 0.545f, 0.600f),
            sunKelvin = 6500f,
            sunIntensity = 0.6f,
            sunEuler = new Vector3(55f, -35f, 0f),
            fogColor = new Color(0.55f, 0.60f, 0.64f),
            fogDensity = 0.04f,
            ambientIntensity = 0.55f
        };

        /// <summary>0 = Golden Hour, 1 = Monsoon.</summary>
        public float Blend { get; private set; }
        private float _target;
        private bool _skyIsMonsoon;

        private void Start()
        {
            _target = startPreset == LightingPreset.MonsoonStorm ? 1f : 0f;
            Blend = _target;
            ApplyBlend(Blend, forceSky: true);
        }

        private void Update()
        {
            if (followGameManager && RiverGameManager.Instance != null)
                _target = RiverGameManager.Instance.isMonsoonStorm ? 1f : 0f;

            if (!Mathf.Approximately(Blend, _target))
            {
                float step = transitionSeconds <= 0.01f ? 1f : Time.deltaTime / transitionSeconds;
                Blend = Mathf.MoveTowards(Blend, _target, step);
                ApplyBlend(Blend, forceSky: false);
            }
        }

        public void SetPreset(LightingPreset preset, bool instant = false)
        {
            _target = preset == LightingPreset.MonsoonStorm ? 1f : 0f;
            if (instant)
            {
                Blend = _target;
                ApplyBlend(Blend, forceSky: true);
            }
        }

        [ContextMenu("Preview Golden Hour")]
        public void SetGoldenHour() { SetPreset(LightingPreset.GoldenHour, true); }

        [ContextMenu("Preview Monsoon Storm")]
        public void SetMonsoon() { SetPreset(LightingPreset.MonsoonStorm, true); }

        private void ApplyBlend(float b, bool forceSky)
        {
            if (sun != null)
            {
                sun.useColorTemperature = true;
                sun.color = Color.Lerp(golden.sunColor, monsoon.sunColor, b);
                sun.colorTemperature = Mathf.Lerp(golden.sunKelvin, monsoon.sunKelvin, b);
                sun.intensity = Mathf.Lerp(golden.sunIntensity, monsoon.sunIntensity, b);
                sun.transform.rotation = Quaternion.Slerp(
                    Quaternion.Euler(golden.sunEuler), Quaternion.Euler(monsoon.sunEuler), b);
            }

            if (goldenHourVolume != null) goldenHourVolume.weight = 1f - b;
            if (monsoonVolume != null) monsoonVolume.weight = b;

            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = Color.Lerp(golden.fogColor, monsoon.fogColor, b);
            RenderSettings.fogDensity = Mathf.Lerp(golden.fogDensity, monsoon.fogDensity, b);
            RenderSettings.ambientIntensity = Mathf.Lerp(golden.ambientIntensity, monsoon.ambientIntensity, b);

            bool wantMonsoonSky = b >= 0.5f;
            if (forceSky || wantMonsoonSky != _skyIsMonsoon)
            {
                _skyIsMonsoon = wantMonsoonSky;
                Material sky = wantMonsoonSky ? monsoonSkybox : goldenHourSkybox;
                if (sky != null)
                {
                    RenderSettings.skybox = sky;
                    DynamicGI.UpdateEnvironment();
                }
            }
        }
    }
}
