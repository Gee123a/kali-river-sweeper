using UnityEngine;

namespace KaliRiverSweeper.Lighting
{
    /// <summary>
    /// Slight sine-wave flicker for the warung hanging incandescent bulb (PF_Lantern_Warung).
    /// Two stacked sine waves (slow sway + fast shimmer) with a random phase per lantern
    /// so a row of lanterns never pulses in sync.
    /// </summary>
    [RequireComponent(typeof(Light))]
    public class LanternFlicker : MonoBehaviour
    {
        [Header("Flicker")]
        public float baseIntensity = 1.6f;
        [Range(0f, 0.5f)] public float slowAmplitude = 0.12f;
        public float slowSpeed = 2.6f;
        [Range(0f, 0.3f)] public float fastAmplitude = 0.04f;
        public float fastSpeed = 11f;

        [Header("Optional glowing bulb")]
        public Renderer bulbRenderer;
        public float emissionMultiplier = 3f;

        private Light _light;
        private float _phase;
        private MaterialPropertyBlock _block;
        private Color _emissionBase = new Color(1f, 0.69f, 0.30f);
        private static readonly int EmissionColorId = Shader.PropertyToID("_EmissionColor");

        private void Awake()
        {
            _light = GetComponent<Light>();
            _phase = Random.value * 100f;
            _block = new MaterialPropertyBlock();
        }

        private void Update()
        {
            float t = Time.time + _phase;
            float k = 1f + Mathf.Sin(t * slowSpeed) * slowAmplitude + Mathf.Sin(t * fastSpeed) * fastAmplitude;
            _light.intensity = baseIntensity * k;

            if (bulbRenderer != null)
            {
                bulbRenderer.GetPropertyBlock(_block);
                _block.SetColor(EmissionColorId, _emissionBase * (emissionMultiplier * k));
                bulbRenderer.SetPropertyBlock(_block);
            }
        }
    }
}
