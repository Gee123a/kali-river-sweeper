using UnityEngine;

namespace KaliRiverSweeper.Core
{
    public static class RiverMath
    {
        public const float MapScale = 0.125f;
        public const float WorldW = 1040f;
        public const float WorldH = 1440f;
        public const float MinWorldX = -WorldW * MapScale * 0.5f;
        public const float MaxWorldX = WorldW * MapScale * 0.5f;
        public const float MinWorldZ = -WorldH * MapScale * 0.5f;
        public const float MaxWorldZ = WorldH * MapScale * 0.5f;

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

    /// <summary>
    /// Simulates sinusoidal bobbing on dynamic linear waterLevelY and +Z downstream drift
    /// from Gunung Sampah (-Z upstream) toward Pintu Air (+Z downstream barrier).
    /// </summary>
    public class RiverFlowBuoyancy : MonoBehaviour
    {
        [Header("Buoyancy & +Z Downstream Current")]
        public float waterLevelY = 0.0f;
        public float floatOffsetY = 0.06f; // spec D: sits on top of the surface, never hidden by turbid water
        public float bobAmplitude = 0.08f;
        public float bobSpeed = 2.0f;
        public float currentDriftSpeed = 0.75f;
        public bool driftDownstream = true;
        public float downstreamBarrierZ = 76.0f;
        public float trashBoomZ = -18.125f;

        private float phaseOffset;
        private RiverTrashItem trashItem;
        private bool settledAtBarrier;

        private void Awake()
        {
            phaseOffset = Random.Range(0f, Mathf.PI * 2f);
            trashItem = GetComponent<RiverTrashItem>();
        }

        private void Update()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm != null)
            {
                waterLevelY = gm.currentWaterLevelY;
            }

            Vector3 pos = transform.position;
            pos.y = waterLevelY + floatOffsetY + Mathf.Sin(Time.time * bobSpeed + phaseOffset) * bobAmplitude;

            if (driftDownstream)
            {
                if (!settledAtBarrier && pos.z < downstreamBarrierZ)
                {
                    // Storm current x1.5 (was x2.2, which flushed the whole pre-storm backlog into Pintu Air in ~60 s).
                    float stormMult = gm != null && gm.isMonsoonStorm ? 1.5f : 1f;
                    float boomSlow = (gm != null && gm.trashBoomActive && Mathf.Abs(pos.z - trashBoomZ) < 4.5f) ? 0.35f : 1f;
                    pos.z += currentDriftSpeed * stormMult * boomSlow * Time.deltaTime;

                    float mapY = pos.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
                    float targetCenterX = (RiverMath.RiverCenterMapX(mapY) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
                    if (gm != null && gm.trashBoomActive && Mathf.Abs(pos.z - trashBoomZ) < 6f)
                    {
                        // Boom gathers mid-river debris along east channel edge.
                        targetCenterX += 5.5f;
                    }
                    pos.x = Mathf.Lerp(pos.x, targetCenterX, 0.35f * Time.deltaTime);
                }
                else
                {
                    settledAtBarrier = true;
                    pos.z = downstreamBarrierZ + Mathf.Sin(phaseOffset) * 1.4f;
                    if (trashItem != null && !trashItem.isPiledAtBarrier)
                    {
                        trashItem.MarkPiledAtBarrier();
                        if (gm != null && gm.ShouldAbsorbVisualBarrierProp())
                        {
                            trashItem.AbsorbIntoNumericPile();
                            return;
                        }
                    }
                }
            }

            transform.position = pos;
        }
    }
}
