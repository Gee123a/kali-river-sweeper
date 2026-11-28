using UnityEngine;

namespace KaliRiverSweeper.Env
{
    /// <summary>
    /// Wesley (Environment): "clean water payoff" hook for washing steps and jetty snags.
    /// Reads the global _WaterClarity that RiverGameManager already broadcasts (0 = brown sludge,
    /// 1 = clear teal) - no gameplay code needed. While the river is dirty the stone is stained
    /// brown and slimy and the litter layer is shown; as the water clears the stain fades back to
    /// clean wet stone and the litter disappears. Ivan can force a state with SetClarity().
    /// </summary>
    [ExecuteAlways]
    [DisallowMultipleComponent]
    public class EnvClarityStain : MonoBehaviour
    {
        [Tooltip("Shown only while the river is dirty (litter, scum, snagged plastic).")]
        public GameObject[] dirtyOnly;
        [Tooltip("Renderers whose SG_EnvWeathered colour gets the trash stain.")]
        public Renderer[] stainRenderers;
        [Range(0f, 1f)] public float cleanAt = 0.45f;
        public Color stainTint = new Color(0.62f, 0.50f, 0.36f);
        [Range(0f, 1f)] public float slimeMoss = 0.45f;

        private static readonly int ClarityId = Shader.PropertyToID("_WaterClarity");
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int MossId = Shader.PropertyToID("_MossAmount");

        private float _override = -1f;
        private float _applied = -1f;
        private MaterialPropertyBlock _block;

        /// <summary>Force a clarity (0..1); pass a negative value to follow _WaterClarity again.</summary>
        public void SetClarity(float clarity)
        {
            _override = clarity;
            _applied = -1f;
        }

        private void OnEnable()
        {
            _block ??= new MaterialPropertyBlock();
            _applied = -1f;
        }

        private void Update()
        {
            float clarity = _override >= 0f ? _override : Shader.GetGlobalFloat(ClarityId);
            if (Mathf.Abs(clarity - _applied) < 0.01f) return;
            _applied = clarity;
            Apply(clarity);
        }

        private void Apply(float clarity)
        {
            bool dirty = clarity < cleanAt;
            if (dirtyOnly != null)
                foreach (var go in dirtyOnly)
                    if (go != null && go.activeSelf != dirty) go.SetActive(dirty);

            // stain is full below 0.15 clarity and gone 0.2 above the clean threshold
            float stain = 1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.15f, cleanAt + 0.2f, clarity));
            if (stainRenderers == null) return;
            foreach (var r in stainRenderers)
            {
                if (r == null) continue;
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++)
                {
                    var m = mats[i];
                    if (m == null || !m.HasProperty(BaseColorId)) continue;
                    r.GetPropertyBlock(_block, i);
                    Color c = m.GetColor(BaseColorId);
                    _block.SetColor(BaseColorId, Color.Lerp(c, c * stainTint, stain));
                    if (m.HasProperty(MossId)) _block.SetFloat(MossId, Mathf.Lerp(m.GetFloat(MossId), Mathf.Max(m.GetFloat(MossId), slimeMoss), stain));
                    r.SetPropertyBlock(_block, i);
                }
            }
        }
    }
}
