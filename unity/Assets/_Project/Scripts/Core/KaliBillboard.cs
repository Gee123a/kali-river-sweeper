using UnityEngine;

namespace KaliRiverSweeper.Core
{
    /// <summary>Yaw-only billboard: the front (-Z side) of the transform faces Camera.main. Used by QuestMarker.</summary>
    public sealed class KaliBillboard : MonoBehaviour
    {
        private void LateUpdate()
        {
            Camera cam = Camera.main;
            if (cam == null) return;

            Vector3 away = transform.position - cam.transform.position;
            away.y = 0f;
            if (away.sqrMagnitude < 0.0001f) return;
            transform.rotation = Quaternion.LookRotation(away.normalized, Vector3.up);
        }
    }
}
