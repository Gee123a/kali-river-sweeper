using System.IO;
using UnityEditor;
using UnityEngine;

namespace KaliRiverSweeper.UI.Editor
{
    /// <summary>
    /// Generates the HUD textures from docs/HUD_SPEC_NIKI.md section 5 and imports them as sprites:
    /// UI_Vellum9Slice (9-slice vellum), UI_Hatch45_Tile and UI_CrossHatch90_Magenta (seamless tiles),
    /// UI_Contour (river contour lines for the map), UI_Chevron (player marker).
    /// Run from the menu: KALI/UI/Build HUD Sprites. Re-running overwrites the PNGs.
    /// </summary>
    public static class KaliHudSpriteBuilder
    {
        private const string Folder = "Assets/_Project/UI/Sprites";

        private static readonly Color32 Vellum = new Color32(0xF4, 0xF2, 0xEC, 230);
        private static readonly Color32 Ink = new Color32(0x1E, 0x1F, 0x1D, 255);
        private static readonly Color32 Magenta = new Color32(0xE1, 0x1D, 0x8F, 255);
        private static readonly Color32 SolidInk = new Color32(0x11, 0x12, 0x11, 255);
        private static readonly Color32 Clear = new Color32(0, 0, 0, 0);

        [MenuItem("KALI/UI/Build HUD Sprites")]
        public static void Build()
        {
            if (!AssetDatabase.IsValidFolder("Assets/_Project/UI/Sprites"))
            {
                AssetDatabase.CreateFolder("Assets/_Project/UI", "Sprites");
            }

            Texture2D vellum = Vellum9Slice();
            WritePng("UI_Vellum9Slice.png", vellum, sliced: true);

            Texture2D hatch = Hatch45();
            WritePng("UI_Hatch45_Tile.png", hatch, sliced: false, wrapRepeat: true);

            Texture2D cross = CrossHatch90();
            WritePng("UI_CrossHatch90_Magenta.png", cross, sliced: false, wrapRepeat: true);

            Texture2D contour = Contour(256, 354);
            WritePng("UI_Contour.png", contour, sliced: false, wrapRepeat: false);

            Texture2D chevron = Chevron(32);
            WritePng("UI_Chevron.png", chevron, sliced: false, wrapRepeat: false);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("HUD sprites written to " + Folder);
        }

        // 64x64, 1px charcoal border, vellum fill. Sliced with 4px borders.
        private static Texture2D Vellum9Slice()
        {
            var tex = new Texture2D(64, 64, TextureFormat.RGBA32, false);
            for (int y = 0; y < 64; y++)
            {
                for (int x = 0; x < 64; x++)
                {
                    bool edge = x == 0 || y == 0 || x == 63 || y == 63;
                    tex.SetPixel(x, y, edge ? Ink : Vellum);
                }
            }
            tex.Apply();
            return tex;
        }

        // 32x32 seamless 45-degree lines. Period 8 divides 32, so the tile wraps cleanly.
        private static Texture2D Hatch45()
        {
            var tex = new Texture2D(32, 32, TextureFormat.RGBA32, false);
            for (int y = 0; y < 32; y++)
            {
                for (int x = 0; x < 32; x++)
                {
                    tex.SetPixel(x, y, (x + y) % 8 == 0 ? Ink : Clear);
                }
            }
            tex.Apply();
            return tex;
        }

        // 32x32 seamless 90-degree magenta cross-hatch.
        private static Texture2D CrossHatch90()
        {
            var tex = new Texture2D(32, 32, TextureFormat.RGBA32, false);
            for (int y = 0; y < 32; y++)
            {
                for (int x = 0; x < 32; x++)
                {
                    bool line = x % 8 == 0 || y % 8 == 0;
                    tex.SetPixel(x, y, line ? Magenta : Clear);
                }
            }
            tex.Apply();
            return tex;
        }

        // Anchors the minimap to the actual RiverMath S-curve, Jembatan Utama (y=740), and Pintu Air (y=1390).
        // Texture y=0 is bottom (mapY = WorldH), y=height-1 is top (mapY = 0).
        private static Texture2D Contour(int width, int height)
        {
            var tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
            Color32 riverFill = new Color32(0x1B, 0x8A, 0x7A, 72);
            Color32 bankLine = new Color32(0x1E, 0x1F, 0x1D, 210);
            Color32 landContour = new Color32(0x1E, 0x1F, 0x1D, 64);
            Color32 bridgeColor = new Color32(0x54, 0x53, 0x4E, 235);
            Color32 sluiceColor = new Color32(0xE1, 0x1D, 0x8F, 220);

            for (int py = 0; py < height; py++)
            {
                float ny = 1f - (py / (float)(height - 1));
                float mapY = ny * KaliRiverSweeper.Core.RiverMath.WorldH;
                float centerX = KaliRiverSweeper.Core.RiverMath.RiverCenterMapX(mapY);
                float halfW = KaliRiverSweeper.Core.RiverMath.RiverHalfWidthMap(mapY);
                bool isBridge = Mathf.Abs(mapY - 740f) <= 20f;
                bool isSluice = Mathf.Abs(mapY - 1390f) <= 16f;

                for (int px = 0; px < width; px++)
                {
                    float nx = px / (float)(width - 1);
                    float mapX = nx * KaliRiverSweeper.Core.RiverMath.WorldW;
                    float dist = Mathf.Abs(mapX - centerX);

                    if (isSluice && dist <= halfW + 25f)
                    {
                        tex.SetPixel(px, py, sluiceColor);
                        continue;
                    }

                    if (isBridge && dist <= halfW + 45f)
                    {
                        tex.SetPixel(px, py, bridgeColor);
                        continue;
                    }

                    if (dist <= halfW && mapY >= 110f)
                    {
                        bool bankEdge = Mathf.Abs(dist - halfW) <= 10f;
                        tex.SetPixel(px, py, bankEdge ? bankLine : riverFill);
                    }
                    else
                    {
                        float u = nx * Mathf.PI * 2f;
                        float v = ny * Mathf.PI * 2f;
                        float field = Mathf.Sin(u * 1.3f + v * 0.4f) + Mathf.Cos(v * 1.1f - u * 0.3f) * 0.8f;
                        float scaled = field * 3f;
                        bool contourLine = Mathf.Abs(scaled - Mathf.Round(scaled)) < 0.032f;
                        tex.SetPixel(px, py, contourLine ? landContour : Clear);
                    }
                }
            }
            tex.Apply();
            return tex;
        }

        // High-contrast cyan directional arrow with dark outline so it reads over river, contours, and DAM hatch.
        private static Texture2D Chevron(int size)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            Color32 cyan = new Color32(0x06, 0xB6, 0xD4, 255);
            float center = (size - 1) * 0.5f;
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float halfWidth = (size - 1 - y) * 0.45f;
                    float dx = Mathf.Abs(x - center);
                    bool inOuter = y >= 2 && y <= size - 2 && dx <= halfWidth + 2.2f;
                    bool inInner = y >= 4 && y <= size - 4 && dx <= Mathf.Max(0f, halfWidth - 0.5f);
                    if (inInner) tex.SetPixel(x, y, cyan);
                    else if (inOuter) tex.SetPixel(x, y, SolidInk);
                    else tex.SetPixel(x, y, Clear);
                }
            }
            tex.Apply();
            return tex;
        }

        private static void WritePng(string fileName, Texture2D tex, bool sliced, bool wrapRepeat = false)
        {
            string assetPath = Folder + "/" + fileName;
            string fullPath = Path.Combine(Application.dataPath, "_Project/UI/Sprites", fileName);
            File.WriteAllBytes(fullPath, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);

            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
            var importer = (TextureImporter)AssetImporter.GetAtPath(assetPath);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.filterMode = FilterMode.Point;
            importer.wrapMode = wrapRepeat ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
            importer.alphaIsTransparency = true;
            importer.mipmapEnabled = false;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.spritePixelsPerUnit = 32f;
            importer.spriteBorder = sliced ? new Vector4(4f, 4f, 4f, 4f) : Vector4.zero;
            importer.SaveAndReimport();
        }
    }
}
