using UnityEngine;

namespace KaliRiverSweeper.Core
{
    /// <summary>
    /// Scales/anchors Gunung Sampah nodes from their base without mid-air levitation.
    /// </summary>
    public class GunungNodeController : MonoBehaviour
    {
        public float baseY = 0.0f;
        public float initialScaleY = 1.0f;
        public float nodeHealth = 1.0f;
        public bool scaleFromCenterPrimitive = true;

        private void Awake()
        {
            initialScaleY = Mathf.Max(0.1f, transform.localScale.y);
            baseY = scaleFromCenterPrimitive ? transform.position.y - initialScaleY * 0.5f : transform.position.y;
        }

        public void ApplyDamage(float damageFraction)
        {
            if (nodeHealth <= 0f) return;
            nodeHealth = Mathf.Clamp01(nodeHealth - damageFraction);
            float scaleRatio = Mathf.Max(0.08f, nodeHealth);

            Vector3 sc = transform.localScale;
            sc.y = initialScaleY * scaleRatio;
            transform.localScale = sc;

            if (scaleFromCenterPrimitive)
            {
                Vector3 pos = transform.position;
                pos.y = baseY + sc.y * 0.5f;
                transform.position = pos;
            }

            if (nodeHealth <= 0.01f)
            {
                nodeHealth = 0f;
                gameObject.SetActive(false);
            }
        }

        public void Restore()
        {
            nodeHealth = 1f;
            Vector3 sc = transform.localScale;
            sc.y = initialScaleY;
            transform.localScale = sc;
            if (scaleFromCenterPrimitive)
            {
                Vector3 pos = transform.position;
                pos.y = baseY + sc.y * 0.5f;
                transform.position = pos;
            }
            gameObject.SetActive(true);
        }
    }
}
