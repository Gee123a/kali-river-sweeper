using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace KaliRiverSweeper.Core
{
    /// <summary>
    /// Procedural 12-minute day/night controller driving KALI/Sky globals, directional sun/moon lighting,
    /// trilight ambient, exponential fog, SG_KaliWater sun glint, and URP post-processing overrides.
    /// Independent of the 300s Monsoon run timer (RestartRun does not reset the time-of-day clock).
    /// </summary>
    [ExecuteAlways]
    public class KaliDayNightCycle : MonoBehaviour
    {
        public static KaliDayNightCycle Instance { get; private set; }

        [Serializable]
        public struct TimeKeyframe
        {
            public float hour;
            public Color skyZenith;
            public Color skyHorizon;
            public Color skyHaze;
            public Color hillColor;
            public Color sunColor;
            public float sunHdrIntensity;
            public float sunSize;
            public float sunGlow;
            public Color moonColor;
            public float moonHdrIntensity;
            public float stars;
            public Color lightColor;
            public float lightIntensity;
            public Color ambientSky;
            public Color ambientEquator;
            public Color ambientGround;
            public Color fogColor;
            public float fogDensity;
            public float bloomIntensity;
            public float postExposure;
            public float saturation;
            public Color colorFilter;
        }

        private struct PhaseTarget
        {
            public string name;
            public float hour;
        }

        [Header("Clock (Independent of 300s Run)")]
        [Min(1f)] public float dayLengthSeconds = 720f;
        [Range(0f, 24f)] public float startHour = 17.50f;
        [Range(0f, 24f)] public float currentHour = 17.50f;

        [Header("Scene References")]
        public Light sunLight;
        public Volume globalVolume;

        [Header("Time-of-Day Keyframes")]
        public TimeKeyframe[] keyframes;

        public float CurrentHour => currentHour;
        public int ClockMinuteOfDay { get; private set; } = -1;
        public string ClockText { get; private set; } = "17:36";
        public string CurrentPhaseName { get; private set; } = "GOLDEN HOUR";
        public Vector3 SunDirection { get; private set; } = new Vector3(0.026f, 0.099f, -0.995f);
        public Vector3 MoonDirection { get; private set; } = new Vector3(-0.026f, -0.099f, 0.995f);
        public float CurrentStars { get; private set; }
        public float StormBlend { get; private set; }
        public float SmogFactor { get; private set; }

        private static readonly float SinTilt = Mathf.Sin(72f * Mathf.Deg2Rad);

        private static readonly int SkyZenithId = Shader.PropertyToID("_KaliSkyZenith");
        private static readonly int SkyHorizonId = Shader.PropertyToID("_KaliSkyHorizon");
        private static readonly int SkyHazeId = Shader.PropertyToID("_KaliSkyHaze");
        private static readonly int SunDirId = Shader.PropertyToID("_KaliSunDir");
        private static readonly int SunColorId = Shader.PropertyToID("_KaliSunColor");
        private static readonly int SunSizeId = Shader.PropertyToID("_KaliSunSize");
        private static readonly int SunGlowId = Shader.PropertyToID("_KaliSunGlow");
        private static readonly int MoonDirId = Shader.PropertyToID("_KaliMoonDir");
        private static readonly int MoonColorId = Shader.PropertyToID("_KaliMoonColor");
        private static readonly int StarsId = Shader.PropertyToID("_KaliStars");
        private static readonly int HillColorId = Shader.PropertyToID("_KaliHillColor");
        private static readonly int StormId = Shader.PropertyToID("_KaliStorm");
        private static readonly int SmogId = Shader.PropertyToID("_KaliSmog");
        private static readonly int SkyTintId = Shader.PropertyToID("_KaliSkyTint");

        private static readonly Color StormZenith = Hex(0x4C5B6E);
        private static readonly Color StormHorizon = Hex(0x6D7D8F);
        private static readonly Color StormHaze = Hex(0x748290);
        private static readonly Color StormLight = Hex(0x8899AB);
        private static readonly Color StormAmbientSky = Hex(0x5E6F82);
        private static readonly Color StormAmbientEq = Hex(0x546373);
        private static readonly Color StormAmbientGnd = Hex(0x2D343D);
        private static readonly Color StormFog = Hex(0x6C7987);
        private static readonly Color SmogHazeTint = Hex(0x8F7252);
        private static readonly Color SmogFogTint = Hex(0x866A4B);

        private VolumeProfile runtimeProfile;
        private Bloom cachedBloom;
        private ColorAdjustments cachedColorAdj;
        private Tonemapping cachedTonemapping;
        private readonly PhaseTarget[] phaseCycle = new PhaseTarget[5];

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                if (Application.isPlaying)
                {
                    Destroy(gameObject);
                    return;
                }
            }
            Instance = this;
            EnsureInitialized();
            if (Application.isPlaying)
            {
                currentHour = NormalizeHour(startHour);
            }
            ApplyState(0f);
        }

        private void OnEnable()
        {
            if (Instance == null) Instance = this;
            EnsureInitialized();
            ApplyState(0f);
        }

        private void OnValidate()
        {
            EnsureInitialized();
            currentHour = NormalizeHour(currentHour);
            ApplyState(0f);
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
            if (runtimeProfile != null)
            {
                if (Application.isPlaying) Destroy(runtimeProfile);
                else DestroyImmediate(runtimeProfile);
                runtimeProfile = null;
            }
        }

        private void Update()
        {
            if (!Application.isPlaying) return;
            Step(Time.deltaTime);
        }

        public void SetHour(float hour)
        {
            EnsureInitialized();
            currentHour = NormalizeHour(hour);
            ApplyState(0f);
        }

        public void SkipToNextPhase()
        {
            EnsureInitialized();
            RefreshPhaseCycleTable();

            float h = NormalizeHour(currentHour);
            int nextIdx = 0;
            for (int i = 0; i < phaseCycle.Length; i++)
            {
                if (phaseCycle[i].hour > h + 0.05f)
                {
                    nextIdx = i;
                    break;
                }
            }

            currentHour = NormalizeHour(phaseCycle[nextIdx].hour);
            CurrentPhaseName = phaseCycle[nextIdx].name;
            ApplyState(0f);
        }

        public void Step(float dt)
        {
            EnsureInitialized();
            if (dt > 0f)
            {
                float dayHours = (dt / Mathf.Max(1f, dayLengthSeconds)) * 24f;
                currentHour = NormalizeHour(currentHour + dayHours);
            }
            ApplyState(dt);
        }

        private void ApplyState(float dt)
        {
            UpdateClockTextAndPhase();

            RiverGameManager gm = RiverGameManager.Instance;
            float targetStorm = gm != null && gm.isMonsoonStorm ? 1f : 0f;
            if (dt > 0f)
            {
                StormBlend = Mathf.MoveTowards(StormBlend, targetStorm, dt / 6f);
            }
            else if (Application.isPlaying && gm != null)
            {
                // Keep current StormBlend on instantaneous jumps unless initialized
            }

            float clarity = gm != null ? gm.waterClarity : 0.65f;
            SmogFactor = Mathf.Clamp01((0.60f - clarity) / 0.50f);

            // Sun & moon vectors: toward-sun = normalize(0.25*sin(theta), sin(theta)*sin(72deg), cos(theta))
            float theta = (currentHour - 6f) / 12f * Mathf.PI;
            float sinT = Mathf.Sin(theta);
            float cosT = Mathf.Cos(theta);
            Vector3 sunDir = new Vector3(0.25f * sinT, sinT * SinTilt, cosT).normalized;
            SunDirection = sunDir;
            MoonDirection = -sunDir;

            TimeKeyframe k = EvaluateKeyframes(currentHour);

            // Apply storm and smog onto atmosphere and lighting
            float storm = Mathf.Clamp01(StormBlend);
            float smog = Mathf.Clamp01(SmogFactor);

            Color zenith = Color.Lerp(k.skyZenith, StormZenith, storm * 0.85f);
            Color horizon = Color.Lerp(k.skyHorizon, StormHorizon, storm * 0.82f);
            Color haze = Color.Lerp(k.skyHaze, StormHaze, storm * 0.88f);
            haze = Color.Lerp(haze, SmogHazeTint, smog * 0.55f);

            Color sunCol = k.sunColor * k.sunHdrIntensity;
            sunCol *= (1f - storm * 0.85f) * (1f - smog * 0.45f);

            Color moonCol = k.moonColor * k.moonHdrIntensity;
            moonCol *= (1f - storm * 0.90f);

            CurrentStars = k.stars * (1f - storm) * (1f - smog * 0.70f);

            // Directional light crossfade between sun (day) and moon (night)
            bool useSun = sunDir.y >= -0.02f;
            Vector3 activeDir = useSun ? sunDir : MoonDirection;
            if (activeDir.y < 0.06f)
            {
                activeDir = new Vector3(activeDir.x, 0.06f, activeDir.z).normalized;
            }

            float dayFade = SmoothStep(-0.02f, 0.08f, sunDir.y);
            float nightFade = SmoothStep(0.02f, 0.12f, MoonDirection.y);
            float elevFade = useSun ? dayFade : nightFade;

            Color lightCol = Color.Lerp(k.lightColor, StormLight, storm * 0.75f);
            lightCol = Color.Lerp(lightCol, SmogHazeTint, smog * 0.25f);
            float lightInt = k.lightIntensity * elevFade * (1f - storm * 0.55f) * (1f - smog * 0.22f);

            if (sunLight != null)
            {
                sunLight.transform.rotation = Quaternion.LookRotation(-activeDir, Vector3.up);
                sunLight.color = lightCol;
                sunLight.intensity = lightInt;
                sunLight.shadowStrength = Mathf.Lerp(0.85f, 0.35f, storm);
            }

            // Trilight ambient & exponential fog
            Color ambSky = Color.Lerp(k.ambientSky, StormAmbientSky, storm * 0.80f);
            Color ambEq = Color.Lerp(k.ambientEquator, StormAmbientEq, storm * 0.80f);
            Color ambGnd = Color.Lerp(k.ambientGround, StormAmbientGnd, storm * 0.80f);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = ambSky;
            RenderSettings.ambientEquatorColor = ambEq;
            RenderSettings.ambientGroundColor = ambGnd;

            Color fogCol = Color.Lerp(k.fogColor, StormFog, storm * 0.88f);
            fogCol = Color.Lerp(fogCol, SmogFogTint, smog * 0.50f);
            float fogDens = k.fogDensity + storm * 0.0085f + smog * 0.0065f;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = fogCol;
            RenderSettings.fogDensity = fogDens;

            // Shader globals (KALI/Sky + SG_KaliWater)
            Shader.SetGlobalColor(SkyZenithId, zenith);
            Shader.SetGlobalColor(SkyHorizonId, horizon);
            Shader.SetGlobalColor(SkyHazeId, haze);
            Shader.SetGlobalVector(SunDirId, new Vector4(sunDir.x, sunDir.y, sunDir.z, 0f));
            Shader.SetGlobalColor(SunColorId, sunCol);
            Shader.SetGlobalFloat(SunSizeId, k.sunSize);
            Shader.SetGlobalFloat(SunGlowId, k.sunGlow * (1f - storm * 0.85f));
            Shader.SetGlobalVector(MoonDirId, new Vector4(MoonDirection.x, MoonDirection.y, MoonDirection.z, 0f));
            Shader.SetGlobalColor(MoonColorId, moonCol);
            Shader.SetGlobalFloat(StarsId, CurrentStars);
            Shader.SetGlobalColor(HillColorId, k.hillColor);
            Shader.SetGlobalFloat(StormId, storm);
            Shader.SetGlobalFloat(SmogId, smog);
            Shader.SetGlobalColor(SkyTintId, horizon);

            // URP Volume overrides (runtime clone only; never mutate shared asset)
            if (Application.isPlaying)
            {
                EnsureRuntimeVolume();
                if (cachedBloom != null)
                {
                    cachedBloom.intensity.Override(k.bloomIntensity * (1f - storm * 0.55f));
                }
                if (cachedColorAdj != null)
                {
                    cachedColorAdj.postExposure.Override(k.postExposure - storm * 0.25f - smog * 0.12f);
                    cachedColorAdj.saturation.Override(k.saturation - storm * 22f - smog * 18f);
                    cachedColorAdj.colorFilter.Override(Color.Lerp(k.colorFilter, Color.white, storm * 0.5f));
                }
                if (cachedTonemapping != null)
                {
                    cachedTonemapping.mode.Override(TonemappingMode.Neutral);
                }
            }
        }

        private void EnsureInitialized()
        {
            if (keyframes == null || keyframes.Length == 0)
            {
                keyframes = BuildDefaultKeyframes();
            }
            if (sunLight == null)
            {
                sunLight = GetComponentInChildren<Light>(true);
            }
            if (globalVolume == null)
            {
                globalVolume = GetComponentInChildren<Volume>(true);
            }
            RefreshPhaseCycleTable();
        }

        private void RefreshPhaseCycleTable()
        {
            phaseCycle[0] = new PhaseTarget { name = "FAJAR", hour = 5f + 50f / 60f };
            phaseCycle[1] = new PhaseTarget { name = "SIANG", hour = 12f };
            phaseCycle[2] = new PhaseTarget { name = "GOLDEN HOUR", hour = Mathf.Clamp(startHour, 15.6f, 18.4f) };
            phaseCycle[3] = new PhaseTarget { name = "SENJA", hour = 18f + 40f / 60f };
            phaseCycle[4] = new PhaseTarget { name = "MALAM", hour = 22f };
        }

        private void EnsureRuntimeVolume()
        {
            if (globalVolume == null) return;
            if (runtimeProfile == null && globalVolume.sharedProfile != null)
            {
                runtimeProfile = Instantiate(globalVolume.sharedProfile);
                runtimeProfile.name = globalVolume.sharedProfile.name + " (Runtime)";
                globalVolume.profile = runtimeProfile;
                runtimeProfile.TryGet(out cachedBloom);
                runtimeProfile.TryGet(out cachedColorAdj);
                runtimeProfile.TryGet(out cachedTonemapping);
            }
        }

        private void UpdateClockTextAndPhase()
        {
            float h = NormalizeHour(currentHour);
            int totalMinutes = Mathf.FloorToInt(h * 60f + 0.0001f) % 1440;
            if (totalMinutes != ClockMinuteOfDay)
            {
                ClockMinuteOfDay = totalMinutes;
                int hh = totalMinutes / 60;
                int mm = totalMinutes % 60;
                ClockText = string.Concat(
                    (char)('0' + hh / 10),
                    (char)('0' + hh % 10),
                    ':',
                    (char)('0' + mm / 10),
                    (char)('0' + mm % 10));
            }

            if (h >= 5.2f && h < 7.0f) CurrentPhaseName = "FAJAR";
            else if (h >= 7.0f && h < 16.5f) CurrentPhaseName = "SIANG";
            else if (h >= 16.5f && h < 18.2f) CurrentPhaseName = "GOLDEN HOUR";
            else if (h >= 18.2f && h < 19.8f) CurrentPhaseName = "SENJA";
            else CurrentPhaseName = "MALAM";
        }

        private TimeKeyframe EvaluateKeyframes(float hour)
        {
            int count = keyframes.Length;
            if (count == 1) return keyframes[0];

            int aIdx = count - 1;
            int bIdx = 0;
            for (int i = 0; i < count; i++)
            {
                if (keyframes[i].hour <= hour)
                {
                    aIdx = i;
                    bIdx = (i + 1) % count;
                }
            }

            TimeKeyframe a = keyframes[aIdx];
            TimeKeyframe b = keyframes[bIdx];
            float span = b.hour - a.hour;
            if (span <= 0f) span += 24f;
            float delta = hour - a.hour;
            if (delta < 0f) delta += 24f;
            float t = span > 0.0001f ? Mathf.Clamp01(delta / span) : 0f;

            return new TimeKeyframe
            {
                hour = hour,
                skyZenith = Color.Lerp(a.skyZenith, b.skyZenith, t),
                skyHorizon = Color.Lerp(a.skyHorizon, b.skyHorizon, t),
                skyHaze = Color.Lerp(a.skyHaze, b.skyHaze, t),
                hillColor = Color.Lerp(a.hillColor, b.hillColor, t),
                sunColor = Color.Lerp(a.sunColor, b.sunColor, t),
                sunHdrIntensity = Mathf.Lerp(a.sunHdrIntensity, b.sunHdrIntensity, t),
                sunSize = Mathf.Lerp(a.sunSize, b.sunSize, t),
                sunGlow = Mathf.Lerp(a.sunGlow, b.sunGlow, t),
                moonColor = Color.Lerp(a.moonColor, b.moonColor, t),
                moonHdrIntensity = Mathf.Lerp(a.moonHdrIntensity, b.moonHdrIntensity, t),
                stars = Mathf.Lerp(a.stars, b.stars, t),
                lightColor = Color.Lerp(a.lightColor, b.lightColor, t),
                lightIntensity = Mathf.Lerp(a.lightIntensity, b.lightIntensity, t),
                ambientSky = Color.Lerp(a.ambientSky, b.ambientSky, t),
                ambientEquator = Color.Lerp(a.ambientEquator, b.ambientEquator, t),
                ambientGround = Color.Lerp(a.ambientGround, b.ambientGround, t),
                fogColor = Color.Lerp(a.fogColor, b.fogColor, t),
                fogDensity = Mathf.Lerp(a.fogDensity, b.fogDensity, t),
                bloomIntensity = Mathf.Lerp(a.bloomIntensity, b.bloomIntensity, t),
                postExposure = Mathf.Lerp(a.postExposure, b.postExposure, t),
                saturation = Mathf.Lerp(a.saturation, b.saturation, t),
                colorFilter = Color.Lerp(a.colorFilter, b.colorFilter, t)
            };
        }

        public static TimeKeyframe[] BuildDefaultKeyframes()
        {
            return new[]
            {
                new TimeKeyframe // 03:00 Deep Night
                {
                    hour = 3.0f,
                    skyZenith = Hex(0x091224),
                    skyHorizon = Hex(0x213A63),
                    skyHaze = Hex(0x1B2D45),
                    hillColor = Hex(0x0F1A2B),
                    sunColor = Color.black,
                    sunHdrIntensity = 0f,
                    sunSize = 0.036f,
                    sunGlow = 0f,
                    moonColor = Hex(0xDCEBFF),
                    moonHdrIntensity = 2.2f,
                    stars = 1.0f,
                    lightColor = Hex(0x88B2EE),
                    lightIntensity = 0.82f,
                    ambientSky = Hex(0x315282),
                    ambientEquator = Hex(0x26436B),
                    ambientGround = Hex(0x18283F),
                    fogColor = Hex(0x19293F),
                    fogDensity = 0.0062f,
                    bloomIntensity = 0.35f,
                    postExposure = 0.15f,
                    saturation = -8f,
                    colorFilter = Hex(0xE8F1FF)
                },
                new TimeKeyframe // 05:50 Dawn
                {
                    hour = 5f + 50f / 60f,
                    skyZenith = Hex(0x52678A),
                    skyHorizon = Hex(0xF0A67E),
                    skyHaze = Hex(0xD9A98D),
                    hillColor = Hex(0x5B4A4A),
                    sunColor = Hex(0xFFE0B2),
                    sunHdrIntensity = 2.2f,
                    sunSize = 0.045f,
                    sunGlow = 0.85f,
                    moonColor = Hex(0xC9DDF8),
                    moonHdrIntensity = 0.35f,
                    stars = 0.15f,
                    lightColor = Hex(0xFFB884),
                    lightIntensity = 1.15f,
                    ambientSky = Hex(0x82889E),
                    ambientEquator = Hex(0xCF9E82),
                    ambientGround = Hex(0x514338),
                    fogColor = Hex(0xCFA38B),
                    fogDensity = 0.0068f,
                    bloomIntensity = 0.45f,
                    postExposure = 0.05f,
                    saturation = 4f,
                    colorFilter = Hex(0xFFF3E6)
                },
                new TimeKeyframe // 07:00 Morning
                {
                    hour = 7.0f,
                    skyZenith = Hex(0x4E8CC4),
                    skyHorizon = Hex(0xCBE2F0),
                    skyHaze = Hex(0xD8E3E3),
                    hillColor = Hex(0x5D6F66),
                    sunColor = Hex(0xFFF4D6),
                    sunHdrIntensity = 2.6f,
                    sunSize = 0.038f,
                    sunGlow = 0.45f,
                    moonColor = Color.black,
                    moonHdrIntensity = 0f,
                    stars = 0f,
                    lightColor = Hex(0xFFE9C7),
                    lightIntensity = 1.75f,
                    ambientSky = Hex(0x8BB6DA),
                    ambientEquator = Hex(0xC4D9E2),
                    ambientGround = Hex(0x5C5A4C),
                    fogColor = Hex(0xCEDCE0),
                    fogDensity = 0.0038f,
                    bloomIntensity = 0.35f,
                    postExposure = 0.05f,
                    saturation = 5f,
                    colorFilter = Color.white
                },
                new TimeKeyframe // 12:00 Noon
                {
                    hour = 12.0f,
                    skyZenith = Hex(0x367EC4),
                    skyHorizon = Hex(0xA8D4EC),
                    skyHaze = Hex(0xC8DCE5),
                    hillColor = Hex(0x58716B),
                    sunColor = Hex(0xFFFCEB),
                    sunHdrIntensity = 3.0f,
                    sunSize = 0.034f,
                    sunGlow = 0.22f,
                    moonColor = Color.black,
                    moonHdrIntensity = 0f,
                    stars = 0f,
                    lightColor = Hex(0xFFF7E6),
                    lightIntensity = 2.15f,
                    ambientSky = Hex(0x8DC0E6),
                    ambientEquator = Hex(0xBCD8E4),
                    ambientGround = Hex(0x635E4E),
                    fogColor = Hex(0xC5D8E2),
                    fogDensity = 0.0028f,
                    bloomIntensity = 0.30f,
                    postExposure = 0.0f,
                    saturation = 4f,
                    colorFilter = Color.white
                },
                new TimeKeyframe // 15:30 Afternoon
                {
                    hour = 15.5f,
                    skyZenith = Hex(0x6590BA),
                    skyHorizon = Hex(0xE3D5BC),
                    skyHaze = Hex(0xDFCEB6),
                    hillColor = Hex(0x6F695B),
                    sunColor = Hex(0xFFF4D2),
                    sunHdrIntensity = 2.8f,
                    sunSize = 0.040f,
                    sunGlow = 0.52f,
                    moonColor = Color.black,
                    moonHdrIntensity = 0f,
                    stars = 0f,
                    lightColor = Hex(0xFFE5B4),
                    lightIntensity = 1.95f,
                    ambientSky = Hex(0x9BB7CC),
                    ambientEquator = Hex(0xDECDB2),
                    ambientGround = Hex(0x6B5D4A),
                    fogColor = Hex(0xDCC9AF),
                    fogDensity = 0.0038f,
                    bloomIntensity = 0.40f,
                    postExposure = 0.05f,
                    saturation = 5f,
                    colorFilter = Hex(0xFFFBF2)
                },
                new TimeKeyframe // 17:24 Golden Hour Start (Reference Palette)
                {
                    hour = 17.4f,
                    skyZenith = Hex(0xF7BC84),
                    skyHorizon = Hex(0xFDDAA8),
                    skyHaze = Hex(0xE6C39E),
                    hillColor = Hex(0x8D7059),
                    sunColor = Hex(0xFFFBCC),
                    sunHdrIntensity = 4.4f,
                    sunSize = 0.062f,
                    sunGlow = 1.40f,
                    moonColor = Color.black,
                    moonHdrIntensity = 0f,
                    stars = 0f,
                    lightColor = Hex(0xFFD699),
                    lightIntensity = 1.95f,
                    ambientSky = Hex(0xF9CEA4),
                    ambientEquator = Hex(0xFEE5C5),
                    ambientGround = Hex(0x7E664E),
                    fogColor = Hex(0xE6C39E),
                    fogDensity = 0.0046f,
                    bloomIntensity = 0.70f,
                    postExposure = 0.12f,
                    saturation = 12f,
                    colorFilter = Hex(0xFFF8EE)
                },
                new TimeKeyframe // 17:36 Golden Hour Peak (Reference Elevation ~5.7-7.1 deg)
                {
                    hour = 17.6f,
                    skyZenith = Hex(0xF7BC84),
                    skyHorizon = Hex(0xFDDAA8),
                    skyHaze = Hex(0xE6C39E),
                    hillColor = Hex(0x8D7059),
                    sunColor = Hex(0xFFFBCC),
                    sunHdrIntensity = 4.4f,
                    sunSize = 0.062f,
                    sunGlow = 1.40f,
                    moonColor = Color.black,
                    moonHdrIntensity = 0f,
                    stars = 0f,
                    lightColor = Hex(0xFFD596),
                    lightIntensity = 1.90f,
                    ambientSky = Hex(0xF9CEA4),
                    ambientEquator = Hex(0xFEE5C5),
                    ambientGround = Hex(0x7C634C),
                    fogColor = Hex(0xE6C39E),
                    fogDensity = 0.0048f,
                    bloomIntensity = 0.70f,
                    postExposure = 0.12f,
                    saturation = 12f,
                    colorFilter = Hex(0xFFF8EE)
                },
                new TimeKeyframe // 18:40 Dusk
                {
                    hour = 18f + 40f / 60f,
                    skyZenith = Hex(0x2F3559),
                    skyHorizon = Hex(0xD87659),
                    skyHaze = Hex(0xA66758),
                    hillColor = Hex(0x45353B),
                    sunColor = Hex(0xFF8B52),
                    sunHdrIntensity = 1.0f,
                    sunSize = 0.048f,
                    sunGlow = 0.65f,
                    moonColor = Hex(0xDCEBFF),
                    moonHdrIntensity = 0.7f,
                    stars = 0.35f,
                    lightColor = Hex(0xF08B64),
                    lightIntensity = 0.65f,
                    ambientSky = Hex(0x524F70),
                    ambientEquator = Hex(0xB86E5C),
                    ambientGround = Hex(0x362C30),
                    fogColor = Hex(0x9C655B),
                    fogDensity = 0.0068f,
                    bloomIntensity = 0.45f,
                    postExposure = 0.08f,
                    saturation = 4f,
                    colorFilter = Hex(0xFFEBE3)
                },
                new TimeKeyframe // 19:30 Blue Hour
                {
                    hour = 19.5f,
                    skyZenith = Hex(0x16223D),
                    skyHorizon = Hex(0x364E75),
                    skyHaze = Hex(0x2D4160),
                    hillColor = Hex(0x1C283C),
                    sunColor = Color.black,
                    sunHdrIntensity = 0f,
                    sunSize = 0.036f,
                    sunGlow = 0f,
                    moonColor = Hex(0xDCEBFF),
                    moonHdrIntensity = 1.6f,
                    stars = 0.80f,
                    lightColor = Hex(0x88ACE0),
                    lightIntensity = 0.55f,
                    ambientSky = Hex(0x324B72),
                    ambientEquator = Hex(0x2C4363),
                    ambientGround = Hex(0x182334),
                    fogColor = Hex(0x2A3D58),
                    fogDensity = 0.0062f,
                    bloomIntensity = 0.38f,
                    postExposure = 0.12f,
                    saturation = -4f,
                    colorFilter = Hex(0xE8F0FF)
                },
                new TimeKeyframe // 22:00 Playable Moonlit Night
                {
                    hour = 22.0f,
                    skyZenith = Hex(0x0B1528),
                    skyHorizon = Hex(0x213A63),
                    skyHaze = Hex(0x1D3048),
                    hillColor = Hex(0x111D30),
                    sunColor = Color.black,
                    sunHdrIntensity = 0f,
                    sunSize = 0.036f,
                    sunGlow = 0f,
                    moonColor = Hex(0xDCEBFF),
                    moonHdrIntensity = 2.2f,
                    stars = 1.0f,
                    lightColor = Hex(0x8AB4F0),
                    lightIntensity = 0.82f,
                    ambientSky = Hex(0x315282),
                    ambientEquator = Hex(0x26436B),
                    ambientGround = Hex(0x18283F),
                    fogColor = Hex(0x1A2B42),
                    fogDensity = 0.0060f,
                    bloomIntensity = 0.35f,
                    postExposure = 0.15f,
                    saturation = -6f,
                    colorFilter = Hex(0xE6F0FF)
                }
            };
        }

        private static float NormalizeHour(float h)
        {
            float mod = h % 24f;
            return mod < 0f ? mod + 24f : mod;
        }

        private static float SmoothStep(float edge0, float edge1, float x)
        {
            float t = Mathf.Clamp01((x - edge0) / Mathf.Max(0.0001f, edge1 - edge0));
            return t * t * (3f - 2f * t);
        }

        private static Color Hex(int rgb)
        {
            return new Color(
                ((rgb >> 16) & 0xFF) / 255f,
                ((rgb >> 8) & 0xFF) / 255f,
                (rgb & 0xFF) / 255f,
                1f);
        }
    }
}
