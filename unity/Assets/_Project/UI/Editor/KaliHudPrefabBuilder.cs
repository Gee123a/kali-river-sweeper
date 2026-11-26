using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace KaliRiverSweeper.UI.Editor
{
    /// <summary>
    /// Builds Assets/_Project/UI/Prefabs/Canvas_HUD.prefab from docs/HUD_SPEC_NIKI.md section 3.
    /// Run from the menu: KALI/UI/Build Canvas_HUD. Solid colors stand in for the hatch and
    /// vellum sprites until the 3 UI sprites exist; fonts use TMP's default until Barlow
    /// Condensed and IBM Plex Mono are in the project.
    /// </summary>
    public static class KaliHudPrefabBuilder
    {
        private const string PrefabFolder = "Assets/_Project/UI/Prefabs";
        private const string PrefabPath = PrefabFolder + "/Canvas_HUD.prefab";

        private static readonly Color Vellum = new Color32(0xF4, 0xF2, 0xEC, 230);
        private static readonly Color VellumSolid = new Color32(0xF4, 0xF2, 0xEC, 255);
        private static readonly Color Ink = new Color32(0x1E, 0x1F, 0x1D, 255);
        private static readonly Color InkSecondary = new Color32(0x54, 0x53, 0x4E, 255);
        private static readonly Color Alert = new Color32(0xB5, 0x0E, 0x6F, 255);
        private static readonly Color Teal = new Color32(0x1B, 0x8A, 0x7A, 255);
        private static readonly Color Track = new Color32(0xDC, 0xDA, 0xD2, 255);

        [MenuItem("KALI/UI/Build Canvas_HUD")]
        public static void Build()
        {
            EnsureFolder("Assets/_Project/UI", "Prefabs");

            GameObject root = new GameObject("Canvas_HUD", typeof(Canvas), typeof(CanvasScaler), typeof(KaliHudController));
            Canvas canvas = root.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 10;

            CanvasScaler scaler = root.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            BuildSurvivalSheet(root.transform);
            BuildToolToast(root.transform);
            BuildHydroRail(root.transform);
            BuildContextualRail(root.transform);
            BuildEconomyLedger(root.transform);
            BuildCrosshair(root.transform);
            BuildDockSheet(root.transform);
            BuildHydroMap(root.transform);

            PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            Object.DestroyImmediate(root);
            AssetDatabase.Refresh();
            Debug.Log("Canvas_HUD prefab written to " + PrefabPath);
        }

        private static void BuildSurvivalSheet(Transform parent)
        {
            GameObject sheet = Panel(parent, "TL_SurvivalFloodSheet", new Vector2(0f, 1f), new Vector2(36f, -32f), new Vector2(342f, 134f), Vellum);
            Text(sheet.transform, "TMP_HPLabel", "HP", 14f, InkSecondary, new Vector2(12f, -10f), new Vector2(60f, 20f), new Vector2(0f, 1f));
            Text(sheet.transform, "Row_HP/TMP_HPValue", "100", 28f, Ink, new Vector2(12f, -32f), new Vector2(120f, 40f), new Vector2(0f, 1f));
            Text(sheet.transform, "Row_SiagaWater/TMP_SiagaLevel", "SIAGA 4", 20f, Ink, new Vector2(12f, -84f), new Vector2(180f, 28f), new Vector2(0f, 1f));
            Text(sheet.transform, "Row_SiagaWater/TMP_WaterMeters", "+0.00m", 18f, InkSecondary, new Vector2(200f, -84f), new Vector2(130f, 28f), new Vector2(0f, 1f));
        }

        private static void BuildToolToast(Transform parent)
        {
            GameObject toast = Panel(parent, "TL_ToolUnlockToast", new Vector2(0f, 1f), new Vector2(36f, -184f), new Vector2(342f, 58f), Vellum);
            Text(toast.transform, "TMP_ToastText", string.Empty, 16f, Ink, new Vector2(12f, -10f), new Vector2(318f, 40f), new Vector2(0f, 1f));
            toast.SetActive(false);
        }

        private static void BuildHydroRail(Transform parent)
        {
            GameObject rail = Panel(parent, "TC_EcologicalHydroRail", new Vector2(0.5f, 1f), new Vector2(0f, -32f), new Vector2(780f, 76f), Vellum);
            GameObject gunung = Panel(rail.transform, "Cell_GunungSampah", new Vector2(0f, 0.5f), new Vector2(12f, 0f), new Vector2(240f, 56f), VellumSolid);
            Text(gunung.transform, "TMP_GunungLabel", "GUNUNG SAMPAH", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(220f, 20f), new Vector2(0f, 1f));
            Text(gunung.transform, "TMP_GunungPct", "100%", 28f, Ink, new Vector2(8f, -26f), new Vector2(220f, 34f), new Vector2(0f, 1f));

            GameObject clarity = Panel(rail.transform, "Cell_Kejernihan", new Vector2(0f, 0.5f), new Vector2(264f, 0f), new Vector2(240f, 56f), VellumSolid);
            Text(clarity.transform, "TMP_KejernihanLabel", "KEJERNIHAN", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(220f, 20f), new Vector2(0f, 1f));
            Text(clarity.transform, "TMP_KejernihanPct", "12%", 28f, Ink, new Vector2(8f, -26f), new Vector2(220f, 34f), new Vector2(0f, 1f));

            GameObject monsun = Panel(rail.transform, "Cell_MonsunTimer", new Vector2(0f, 0.5f), new Vector2(516f, 0f), new Vector2(252f, 56f), VellumSolid);
            Text(monsun.transform, "TMP_MonsunLabel", "MONSUN", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(230f, 20f), new Vector2(0f, 1f));
            Text(monsun.transform, "TMP_MonsunTimer", "05:00", 28f, Ink, new Vector2(8f, -26f), new Vector2(230f, 34f), new Vector2(0f, 1f));
        }

        private static void BuildContextualRail(Transform parent)
        {
            GameObject rail = Panel(parent, "TC_ContextualAlertRail", new Vector2(0.5f, 1f), new Vector2(0f, -118f), new Vector2(780f, 60f), new Color(0f, 0f, 0f, 0f));
            GameObject bio = Panel(rail.transform, "Strip_BiohazardTimer", new Vector2(0f, 1f), new Vector2(0f, 0f), new Vector2(780f, 28f), Alert);
            Text(bio.transform, "TMP_BiohazardCountdown", "10s", 18f, VellumSolid, new Vector2(8f, -4f), new Vector2(764f, 22f), new Vector2(0f, 1f));
            bio.SetActive(false);

            GameObject sell = Panel(rail.transform, "Strip_SellLockDump", new Vector2(0f, 1f), new Vector2(0f, -32f), new Vector2(780f, 28f), Alert);
            Text(sell.transform, "TMP_SellLockText", "JUAL DIKUNCI · AIR >= +1.85m · [Q] BUANG", 18f, VellumSolid, new Vector2(8f, -4f), new Vector2(764f, 22f), new Vector2(0f, 1f));
            sell.SetActive(false);
        }

        private static void BuildEconomyLedger(Transform parent)
        {
            GameObject ledger = Panel(parent, "TR_EconomyCargoLedger", new Vector2(1f, 1f), new Vector2(-36f, -32f), new Vector2(326f, 202f), Vellum);
            Text(ledger.transform, "Row_KasRupiah/TMP_KasLabel", "KAS", 14f, InkSecondary, new Vector2(12f, -10f), new Vector2(120f, 20f), new Vector2(0f, 1f));
            Text(ledger.transform, "Row_KasRupiah/TMP_KasValue", "Rp 0", 24f, Ink, new Vector2(12f, -30f), new Vector2(300f, 34f), new Vector2(0f, 1f));
            Text(ledger.transform, "Row_MuatanHeader/TMP_MuatanLabel", "MUATAN", 14f, InkSecondary, new Vector2(12f, -76f), new Vector2(120f, 20f), new Vector2(0f, 1f));
            Text(ledger.transform, "Row_MuatanHeader/TMP_MuatanValue", "0 / 8", 20f, Ink, new Vector2(12f, -96f), new Vector2(300f, 28f), new Vector2(0f, 1f));
            Text(ledger.transform, "Grid_Cargo3Class/Cell_Normal/TMP_NormalCount", "0", 22f, Ink, new Vector2(12f, -130f), new Vector2(96f, 30f), new Vector2(0f, 1f));
            Text(ledger.transform, "Grid_Cargo3Class/Cell_Normal/TMP_NormalLabel", "NORMAL", 12f, InkSecondary, new Vector2(12f, -158f), new Vector2(96f, 18f), new Vector2(0f, 1f));
            Text(ledger.transform, "Grid_Cargo3Class/Cell_MedisB3/TMP_MedisCount", "0", 22f, Ink, new Vector2(115f, -130f), new Vector2(96f, 30f), new Vector2(0f, 1f));
            Text(ledger.transform, "Grid_Cargo3Class/Cell_MedisB3/TMP_MedisLabel", "MEDIS B3", 12f, InkSecondary, new Vector2(115f, -158f), new Vector2(96f, 18f), new Vector2(0f, 1f));
            Text(ledger.transform, "Grid_Cargo3Class/Cell_Biohazard/TMP_BioCount", "0", 22f, Ink, new Vector2(218f, -130f), new Vector2(96f, 30f), new Vector2(0f, 1f));
            Text(ledger.transform, "Grid_Cargo3Class/Cell_Biohazard/TMP_BioLabel", "BIO", 12f, InkSecondary, new Vector2(218f, -158f), new Vector2(96f, 18f), new Vector2(0f, 1f));
            Text(ledger.transform, "Row_WargaTrust/TMP_WargaLabel", "KEPERCAYAAN WARGA", 14f, InkSecondary, new Vector2(12f, -180f), new Vector2(200f, 20f), new Vector2(0f, 1f));
            Text(ledger.transform, "Row_WargaTrust/TMP_WargaValue", "40", 20f, Ink, new Vector2(230f, -166f), new Vector2(84f, 28f), new Vector2(0f, 1f));
        }

        private static void BuildCrosshair(Transform parent)
        {
            GameObject cross = Panel(parent, "C_CrosshairReticle", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(24f, 24f), new Color(0f, 0f, 0f, 0f));
            Panel(cross.transform, "Tick_H", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(14f, 2f), Ink);
            Panel(cross.transform, "Tick_V", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(2f, 14f), Ink);
        }

        private static void BuildDockSheet(Transform parent)
        {
            GameObject dock = Panel(parent, "BC_StationDockSheet", new Vector2(0.5f, 0f), new Vector2(0f, 34f), new Vector2(660f, 104f), Vellum);
            Text(dock.transform, "Header_StationName", "STASIUN", 16f, Ink, new Vector2(12f, -8f), new Vector2(636f, 24f), new Vector2(0f, 1f));
            CanvasGroup group = dock.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;
            group.interactable = false;
        }

        private static void BuildHydroMap(Transform parent)
        {
            Panel(parent, "BR_VellumHydroMap", new Vector2(1f, 0f), new Vector2(-44f, 38f), new Vector2(372f, 276f), Vellum);
        }

        private static GameObject Panel(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, Color color)
        {
            GameObject go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = anchor;
            rt.anchorMax = anchor;
            rt.pivot = anchor;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            go.GetComponent<Image>().color = color;
            return go;
        }

        private static void Text(Transform parent, string path, string value, float fontSize, Color color, Vector2 pos, Vector2 size, Vector2 anchor)
        {
            Transform current = parent;
            string[] parts = path.Split('/');
            for (int i = 0; i < parts.Length - 1; i++)
            {
                Transform child = current.Find(parts[i]);
                if (child == null)
                {
                    GameObject holder = new GameObject(parts[i], typeof(RectTransform));
                    holder.transform.SetParent(current, false);
                    child = holder.transform;
                }
                current = child;
            }

            GameObject go = new GameObject(parts[parts.Length - 1], typeof(RectTransform), typeof(TextMeshProUGUI));
            go.transform.SetParent(current, false);
            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = anchor;
            rt.anchorMax = anchor;
            rt.pivot = anchor;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;

            TextMeshProUGUI tmp = go.GetComponent<TextMeshProUGUI>();
            TMP_FontAsset barlow = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(KaliHudFontAssets.BarlowBoldPath);
            TMP_FontAsset mono = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(KaliHudFontAssets.PlexMonoSemiBoldPath);
            // Values with digits use the tabular mono face so counters do not jitter; labels use Barlow.
            if (barlow != null)
            {
                tmp.font = (HasDigit(value) && mono != null) ? mono : barlow;
            }
            tmp.text = value;
            tmp.fontSize = fontSize;
            tmp.color = color;
            tmp.enableWordWrapping = false;
        }

        private static bool HasDigit(string value)
        {
            foreach (char c in value)
            {
                if (char.IsDigit(c)) return true;
            }
            return false;
        }

        private static void EnsureFolder(string parent, string name)
        {
            if (!AssetDatabase.IsValidFolder(parent + "/" + name))
            {
                AssetDatabase.CreateFolder(parent, name);
            }
        }
    }
}
