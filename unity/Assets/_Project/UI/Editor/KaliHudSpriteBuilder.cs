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

            Texture2D contour = Contour(256);
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

        // Contour lines from a smooth field: a pixel is a line where the field sits near an integer level.
        private static Texture2D Contour(int size)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float u = x / (float)size * Mathf.PI * 2f;
                    float v = y / (float)size * Mathf.PI * 2f;
                    float field = Mathf.Sin(u * 1.3f + v * 0.4f) + Mathf.Cos(v * 1.1f - u * 0.3f) * 0.8f;
                    float scaled = field * 3f;
                    float distance = Mathf.Abs(scaled - Mathf.Round(scaled));
                    bool line = distance < 0.035f;
                    tex.SetPixel(x, y, line ? new Color32(0x1E, 0x1F, 0x1D, 200) : Clear);
                }
            }
            tex.Apply();
            return tex;
        }

        // Upward-pointing triangle (tip at the top row) in solid inverted Zone 0.
        private static Texture2D Chevron(int size)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            float center = (size - 1) * 0.5f;
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float halfWidth = (size - 1 - y) * 0.5f;
                    bool inside = Mathf.Abs(x - center) <= halfWidth;
                    tex.SetPixel(x, y, inside ? SolidInk : Clear);
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
