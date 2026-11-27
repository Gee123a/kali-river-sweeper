using UnityEngine;

namespace KaliRiverSweeper.Lighting
{
    /// <summary>
    /// Rotating amber/red emergency beacon for Pintu Air (PF_WarningBeacon_PintuAir).
    /// The rotor (which carries the spot light) spins; the light colour pulses amber -> red.
    /// </summary>
    public class WarningBeaconRotator : MonoBehaviour
    {
        [Header("References")]
        public Transform rotor;
        public Light beamLight;
        public Renderer lensRenderer;

        [Header("Behaviour")]
        public float degreesPerSecond = 220f;
        public float colorPulseHz = 0.8f;
        public Color amber = new Color(1f, 0.64f, 0.12f);
        public Color red = new Color(0.92f, 0.10f, 0.05f);
        public float beamIntensity = 8f;
        public float lensEmission = 3f;

        private MaterialPropertyBlock _block;
        private static readonly int EmissionColorId = Shader.PropertyToID("_EmissionColor");

        private void Awake()
        {
            _block = new MaterialPropertyBlock();
        }

        private void Update()
        {
            if (rotor != null)
                rotor.Rotate(0f, degreesPerSecond * Time.deltaTime, 0f, Space.Self);

            float k = 0.5f + 0.5f * Mathf.Sin(Time.time * colorPulseHz * Mathf.PI * 2f);
            Color c = Color.Lerp(amber, red, k);

            if (beamLight != null)
            {
                beamLight.color = c;
                beamLight.intensity = beamIntensity;
            }

            if (lensRenderer != null)
            {
                lensRenderer.GetPropertyBlock(_block);
                _block.SetColor(EmissionColorId, c * lensEmission);
                lensRenderer.SetPropertyBlock(_block);
            }
        }
    }
}
