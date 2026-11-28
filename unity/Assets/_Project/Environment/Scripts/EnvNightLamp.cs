using KaliRiverSweeper.Core;
using UnityEngine;

namespace KaliRiverSweeper.Env
{
    /// <summary>
    /// Wesley (Environment): switches a building or street lamp on when the kampung gets dark.
    /// Darkness is read from Ivan's KaliDayNightCycle (sun elevation + monsoon storm) and never
    /// written back. Each lamp switches at a slightly different moment and fades in like a real
    /// bulb warming up, so a row of lamps does not pop on in the same frame.
    /// Also publishes the global shader float _KaliEnvNight (0 day .. 1 night) for KaliLightPool.
    /// </summary>
    [ExecuteAlways]
    [DisallowMultipleComponent]
    public class EnvNightLamp : MonoBehaviour
    {
        [Header("Lamp")]
        public Light lamp;
        [Min(0f)] public float onIntensity = 2.2f;

        [Header("Glow (bulb emission + ground light pool)")]
        public Renderer[] glowRenderers;
        public Color glowColor = new Color(1f, 0.78f, 0.22f);   // yellow kampung bulb (Wesley)
        [Min(0f)] public float glowEmission = 4f;

        [Header("Switching")]
        [Tooltip("Darkness (0..1) at which this lamp switches on; a random offset is added per lamp.")]
        [Range(0.1f, 0.9f)] public float switchAt = 0.45f;
        [Range(0f, 0.25f)] public float switchJitter = 0.12f;
        [Min(0.01f)] public float warmUpSeconds = 0.8f;

        private static readonly int EmissionColorId = Shader.PropertyToID("_EmissionColor");
        private static readonly int GlowId = Shader.PropertyToID("_Glow");
        private static readonly int EnvNightId = Shader.PropertyToID("_KaliEnvNight");

        private static int s_frame = -1;
        private static float s_darkness;

        private MaterialPropertyBlock _block;
        private float _offset;
        private float _level = -1f;
        private bool _on;

        /// <summary>0 = full daylight, 1 = night (or a heavy monsoon sky). Computed once per frame.</summary>
        public static float Darkness
        {
            get
            {
                if (s_frame == Time.frameCount) return s_darkness;
                s_frame = Time.frameCount;
                var cycle = KaliDayNightCycle.Instance;
                if (cycle == null)
                {
                    s_darkness = 0f;
                }
                else
                {
                    float sunUp = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(-0.05f, 0.14f, cycle.SunDirection.y));
                    s_darkness = Mathf.Max(1f - sunUp, cycle.StormBlend * 0.85f);
                }
                Shader.SetGlobalFloat(EnvNightId, s_darkness);
                return s_darkness;
            }
        }

        private void OnEnable()
        {
            _block ??= new MaterialPropertyBlock();
            // Stable per-lamp offset from its position: the same lamp always switches at the same moment.
            Vector3 p = transform.position;
            _offset = Mathf.Repeat(Mathf.Sin(p.x * 12.9898f + p.z * 78.233f) * 43758.547f, 1f) * switchJitter;
            _level = -1f;
        }

        private void Update()
        {
            float dark = Darkness;
            float threshold = switchAt + _offset;
            if (_on && dark < threshold - 0.06f) _on = false;        // hysteresis: no flicker at dusk
            else if (!_on && dark > threshold) _on = true;

            float target = _on ? 1f : 0f;
            if (_level < 0f || !Application.isPlaying) _level = target;
            else _level = Mathf.MoveTowards(_level, target, Time.deltaTime / warmUpSeconds);
            Apply(_level * _level * (3f - 2f * _level));
        }

        private void Apply(float k)
        {
            if (lamp != null)
            {
                lamp.enabled = k > 0.01f;
                lamp.intensity = onIntensity * k;
            }
            if (glowRenderers == null) return;
            Color emission = glowColor * (glowEmission * k);
            foreach (var r in glowRenderers)
            {
                if (r == null) continue;
                r.GetPropertyBlock(_block);
                _block.SetColor(EmissionColorId, emission);
                _block.SetFloat(GlowId, k);
                r.SetPropertyBlock(_block);
            }
        }
    }
}
