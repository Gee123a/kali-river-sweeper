using UnityEngine;

namespace KaliRiverSweeper.Core
{
    /// <summary>
    /// Syncs the water surface mesh Y position with RiverGameManager.currentWaterLevelY.
    /// </summary>
    public class RiverWaterSurfaceFollower : MonoBehaviour
    {
        public float verticalOffset = 0.0f;

        private void LateUpdate()
        {
            if (RiverGameManager.Instance == null) return;
            Vector3 p = transform.position;
            p.y = RiverGameManager.Instance.currentWaterLevelY + verticalOffset;
            transform.position = p;
        }
    }
}
