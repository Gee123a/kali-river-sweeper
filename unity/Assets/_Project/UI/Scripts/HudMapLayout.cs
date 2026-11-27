using KaliRiverSweeper.Core;
using UnityEngine;

namespace KaliRiverSweeper.UI
{
    /// <summary>
    /// Map math shared by the HUD controller and the prefab builder. Coordinates are river-map pixels
    /// (x in [0, 1040], y in [0, 1440], +Z down the map), matching RiverMath.ToWorld3D.
    /// Station points come from Assets/_Project/Data/kali-river-map.json (item x + w/2, y + h/2).
    /// </summary>
    public static class HudMapLayout
    {
        public static readonly Vector2 BankSampahPin = new Vector2(237f, 1215f);
        public static readonly Vector2 MedisB3Pin = new Vector2(261f, 749f);
        public static readonly Vector2 KarantinaPin = new Vector2(803f, 505f);
        public static readonly Vector2 PengepulPin = new Vector2(319f, 1307f);
        public static readonly Vector2 PosSortirPin = new Vector2(783f, 649f);
        public static readonly Vector2 TokoAlatPin = new Vector2(234f, 1113f);

        // Upstream Gunung Sampah basin (Puncak Gunung Sampah at y = 150..325).
        public const float DamChokeY = 237.5f;

        // Contour art position and size inside the vellum map panel (top-left anchored, 1040:1440 portrait ratio).
        public static readonly Vector2 ContourOrigin = new Vector2(16f, -16f);
        public static readonly Vector2 ContourArea = new Vector2(192f, 266f);

        public static Vector2 DamPoint()
        {
            return new Vector2(RiverMath.RiverCenterMapX(DamChokeY), DamChokeY);
        }

        public static Vector2 WorldToMap(Vector3 world)
        {
            float mapX = world.x / RiverMath.MapScale + RiverMath.WorldW * 0.5f;
            float mapY = world.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            return new Vector2(mapX, mapY);
        }

        // Map point to the contour's top-left space (y goes down).
        public static Vector2 MapToUi(Vector2 mapPoint, Vector2 origin, Vector2 area)
        {
            float nx = Mathf.Clamp01(mapPoint.x / RiverMath.WorldW);
            float ny = Mathf.Clamp01(mapPoint.y / RiverMath.WorldH);
            return new Vector2(origin.x + nx * area.x, origin.y - ny * area.y);
        }

        // Centers a marker on its map point, whatever its pivot is.
        // anchoredPosition is the pivot's position, so the rect center lands on `center` when the pivot is (0.5, 0.5).
        public static void PlaceAt(RectTransform marker, Vector2 center)
        {
            if (marker == null) return;
            marker.anchoredPosition = center + (marker.pivot - new Vector2(0.5f, 0.5f)) * marker.sizeDelta;
        }
    }
}
