using TMPro;
using UnityEditor;
using UnityEngine;

namespace KaliRiverSweeper.UI.Editor
{
    /// <summary>
    /// Creates TMP SDF font assets from the OFL fonts in Assets/_Project/UI/Fonts.
    /// Run from the menu: KALI/UI/Create HUD Font Assets. Re-running overwrites the assets.
    /// </summary>
    public static class KaliHudFontAssets
    {
        public const string BarlowBoldPath = "Assets/_Project/UI/Fonts/BarlowCondensed-Bold SDF.asset";
        public const string PlexMonoSemiBoldPath = "Assets/_Project/UI/Fonts/IBMPlexMono-SemiBold SDF.asset";

        [MenuItem("KALI/UI/Create HUD Font Assets")]
        public static void Create()
        {
            CreateFromTtf("Assets/_Project/UI/Fonts/BarlowCondensed-Bold.ttf", BarlowBoldPath);
            CreateFromTtf("Assets/_Project/UI/Fonts/IBMPlexMono-SemiBold.ttf", PlexMonoSemiBoldPath);
            AssetDatabase.SaveAssets();
            Debug.Log("HUD TMP font assets created.");
        }

        private static void CreateFromTtf(string ttfPath, string assetPath)
        {
            Font font = AssetDatabase.LoadAssetAtPath<Font>(ttfPath);
            if (font == null)
            {
                Debug.LogError("Font not found, import it first: " + ttfPath);
                return;
            }

            TMP_FontAsset fontAsset = TMP_FontAsset.CreateFontAsset(font, 90, 9, UnityEngine.TextCore.LowLevel.GlyphRenderMode.SDFAA, 2048, 2048);
            fontAsset.name = System.IO.Path.GetFileNameWithoutExtension(assetPath);
            AssetDatabase.CreateAsset(fontAsset, assetPath);
            Debug.Log("Created " + assetPath);
        }
    }
}
