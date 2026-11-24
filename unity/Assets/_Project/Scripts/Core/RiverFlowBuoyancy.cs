using UnityEngine;

namespace KaliRiverSweeper.Core
{
    public static class RiverMath
    {
        public const float MapScale = 0.125f;
        public const float WorldW = 1040f;
        public const float WorldH = 1440f;

        public static Vector3 ToWorld3D(float mapX, float mapY, float elevation = 0f)
        {
            return new Vector3((mapX - WorldW * 0.5f) * MapScale, elevation, (mapY - WorldH * 0.5f) * MapScale);
        }

        public static float RiverCenterMapX(float mapY)
        {
            return 520f + Mathf.Sin((mapY / WorldH) * Mathf.PI * 1.6f) * 58f;
        }

        public static float RiverHalfWidthMap(float mapY, float baseWidth = 180f)
        {
            float w = baseWidth;
            if (mapY < 320f)
            {
                float t = Mathf.Clamp01((320f - mapY) / 200f);
                w += t * 130f;
            }
            float choke = Mathf.Exp(-Mathf.Pow((mapY - 740f) / 150f, 2f)) * 28f;
            float southBay = Mathf.Exp(-Mathf.Pow((mapY - 1220f) / 180f, 2f)) * 22f;
            return (w - choke + southBay) * 0.5f;
        }

        public static bool IsInRiver(Vector3 worldPos, float baseWidth = 180f)
        {
            float mapX = worldPos.x / MapScale + WorldW * 0.5f;
            float mapY = worldPos.z / MapScale + WorldH * 0.5f;
            if (mapY < 110f || mapY > WorldH) return false;
            return Mathf.Abs(mapX - RiverCenterMapX(mapY)) <= RiverHalfWidthMap(mapY, baseWidth);
        }
    }

    public class RiverFlowBuoyancy : MonoBehaviour
    {
        [Header("Buoyancy & Current")]
        public float waterLevelY = 0.0f;
        public float bobAmplitude = 0.08f;
        public float bobSpeed = 2.0f;
        public float currentDriftSpeed = 0.45f;
        public bool driftTowardGunungSampah = true;

        private float phaseOffset;

        private void Awake()
        {
            phaseOffset = Random.Range(0f, Mathf.PI * 2f);
        }

        private void Update()
        {
            Vector3 pos = transform.position;
            pos.y = waterLevelY + Mathf.Sin(Time.time * bobSpeed + phaseOffset) * bobAmplitude;

            if (driftTowardGunungSampah && pos.z > -44f)
            {
                float stormMult = RiverGameManager.Instance != null && RiverGameManager.Instance.isMonsoonStorm ? 2.2f : 1f;
                pos.z -= currentDriftSpeed * stormMult * Time.deltaTime;
                float targetCenterX = (RiverMath.RiverCenterMapX(pos.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
                pos.x = Mathf.Lerp(pos.x, targetCenterX, 0.25f * Time.deltaTime);
            }

            transform.position = pos;
        }
    }
}
