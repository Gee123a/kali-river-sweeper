using KaliRiverSweeper.Core;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace KaliRiverSweeper.UI.Editor
{
    /// <summary>
    /// Builds Assets/_Project/UI/Prefabs/Canvas_HUD.prefab from docs/HUD_SPEC_NIKI.md section 3.
    /// Run KALI/UI/Build HUD Sprites and KALI/UI/Create HUD Font Assets first, then KALI/UI/Build Canvas_HUD.
    /// Holder objects are stretched to their parent, so child positions are relative to the visible panel.
    /// </summary>
    public static class KaliHudPrefabBuilder
    {
        private const string PrefabFolder = "Assets/_Project/UI/Prefabs";
        private const string PrefabPath = PrefabFolder + "/Canvas_HUD.prefab";
        private const string SpriteFolder = "Assets/_Project/UI/Sprites/";

        private static readonly Color Vellum = new Color32(0xF4, 0xF2, 0xEC, 230);
        private static readonly Color VellumSolid = new Color32(0xF4, 0xF2, 0xEC, 255);
        private static readonly Color Ink = new Color32(0x1E, 0x1F, 0x1D, 255);
        private static readonly Color InkSecondary = new Color32(0x54, 0x53, 0x4E, 255);
        private static readonly Color Track = new Color32(0xDC, 0xDA, 0xD2, 255);
        private static readonly Color Teal = new Color32(0x1B, 0x8A, 0x7A, 255);
        private static readonly Color TapeTint = new Color(1f, 0.99f, 0.96f, 0.62f);
        private static readonly Color Clear = new Color(0f, 0f, 0f, 0f);
        private static readonly Color Zone0 = new Color32(0x11, 0x12, 0x11, 255);

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

        /// <summary>
        /// Builds Canvas_SDGImpactReport.prefab: the end-of-run modal for RiverGameManager.OnEndingTriggered.
        /// Hidden at rest; SdgImpactReportController fills the copy and stats when an ending fires.
        /// </summary>
        [MenuItem("KALI/UI/Build Canvas_SDGImpactReport")]
        public static void BuildSdgReport()
        {
            EnsureFolder("Assets/_Project/UI", "Prefabs");

            GameObject root = new GameObject("Canvas_SDGImpactReport", typeof(Canvas), typeof(CanvasScaler), typeof(CanvasGroup), typeof(SdgImpactReportController));
            Canvas canvas = root.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 30;

            CanvasScaler scaler = root.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            CanvasGroup group = root.GetComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;
            group.interactable = false;

            GameObject dim = Panel(root.transform, "Dim", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1920f, 1080f), new Color(0.07f, 0.07f, 0.06f, 0.66f));
            RectTransform dimRect = (RectTransform)dim.transform;
            dimRect.anchorMin = Vector2.zero;
            dimRect.anchorMax = Vector2.one;
            dimRect.offsetMin = Vector2.zero;
            dimRect.offsetMax = Vector2.zero;

            GameObject card = Panel(root.transform, "Card", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(880f, 600f), Vellum);
            Text(card.transform, "TMP_Title", "LAPORAN DAMPAK SDG", 30f, Ink, new Vector2(40f, -30f), new Vector2(800f, 40f), new Vector2(0f, 1f));
            Text(card.transform, "TMP_EndingHeadline", string.Empty, 26f, Ink, new Vector2(40f, -84f), new Vector2(800f, 36f), new Vector2(0f, 1f));
            Text(card.transform, "TMP_EndingBody", string.Empty, 18f, InkSecondary, new Vector2(40f, -124f), new Vector2(800f, 60f), new Vector2(0f, 1f));

            string[] labels = {
                "Sampah didaur ulang",
                "Sampah dibuang ke sungai",
                "Medis B3 diamankan",
                "Biohazard diamankan",
                "Denda salah stasiun",
                "Limbah berbahaya dibuang di Pengepul",
                "Kepercayaan warga",
            };
            for (int i = 0; i < labels.Length; i++)
            {
                float y = -200f - i * 36f;
                Text(card.transform, "Stats/Row_" + i + "/TMP_Label", labels[i], 18f, InkSecondary, new Vector2(40f, y), new Vector2(420f, 28f), new Vector2(0f, 1f));
                Text(card.transform, "Stats/Row_" + i + "/TMP_Value", "0", 20f, Ink, new Vector2(460f, y), new Vector2(380f, 28f), new Vector2(0f, 1f));
            }

            Text(card.transform, "TMP_Sdg63", string.Empty, 16f, Ink, new Vector2(40f, -446f), new Vector2(800f, 24f), new Vector2(0f, 1f));
            Text(card.transform, "TMP_Sdg115", string.Empty, 16f, Ink, new Vector2(40f, -474f), new Vector2(800f, 24f), new Vector2(0f, 1f));
            Text(card.transform, "TMP_Sdg141", string.Empty, 16f, Ink, new Vector2(40f, -502f), new Vector2(800f, 24f), new Vector2(0f, 1f));
            Text(card.transform, "TMP_Footer", "Permainan selesai. Terima kasih sudah menjaga sungai.", 16f, InkSecondary, new Vector2(40f, -548f), new Vector2(800f, 24f), new Vector2(0f, 1f));

            PrefabUtility.SaveAsPrefabAsset(root, PrefabFolder + "/Canvas_SDGImpactReport.prefab");
            Object.DestroyImmediate(root);
            AssetDatabase.Refresh();
            Debug.Log("Canvas_SDGImpactReport prefab written to " + PrefabFolder + "/Canvas_SDGImpactReport.prefab");
        }

        /// <summary>
        /// Builds Canvas_ShopBankSampah.prefab: the Toko Alat shop, shown by KaliShopController while the
        /// player is inside the Toko Alat trigger. Sort order 20, below the SDG report (30) and above the HUD (10).
        /// Layout is a 1240 x 840 vellum card on a dim layer. Names match KaliShopController's Find paths.
        /// </summary>
        [MenuItem("KALI/UI/Build Canvas_ShopBankSampah")]
        public static void BuildShop()
        {
            EnsureFolder("Assets/_Project/UI", "Prefabs");

            GameObject root = new GameObject("Canvas_ShopBankSampah", typeof(Canvas), typeof(CanvasScaler), typeof(CanvasGroup), typeof(KaliShopController));
            Canvas canvas = root.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 20;

            CanvasScaler scaler = root.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            CanvasGroup group = root.GetComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;
            group.interactable = false;

            GameObject dim = Panel(root.transform, "Dim", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1920f, 1080f), new Color(0.07f, 0.07f, 0.06f, 0.66f));
            RectTransform dimRect = (RectTransform)dim.transform;
            dimRect.anchorMin = Vector2.zero;
            dimRect.anchorMax = Vector2.one;
            dimRect.offsetMin = Vector2.zero;
            dimRect.offsetMax = Vector2.zero;

            GameObject card = Panel(root.transform, "Card", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1240f, 840f), Vellum);
            Transform c = card.transform;

            // Header: title, subtitle, and the Rupiah and trust box on the right.
            Text(c, "Header/TMP_Title", "TOKO ALAT", 32f, Ink, new Vector2(40f, -28f), new Vector2(600f, 40f), new Vector2(0f, 1f));
            Text(c, "Header/TMP_Subtitle", "Kampung Hulu · belanja alat dan armada", 16f, InkSecondary, new Vector2(40f, -68f), new Vector2(600f, 24f), new Vector2(0f, 1f));
            Panel(c, "RupiahBox", new Vector2(1f, 1f), new Vector2(-40f, -24f), new Vector2(300f, 76f), VellumSolid);
            Text(c, "Header/TMP_RupiahValue", "Rp 0", 30f, Ink, new Vector2(-340f, -32f), new Vector2(284f, 40f), new Vector2(1f, 1f));
            Text(c, "Header/TMP_TrustValue", "Kepercayaan warga 0", 14f, InkSecondary, new Vector2(-340f, -70f), new Vector2(284f, 22f), new Vector2(1f, 1f));

            // Bins: a one-time install, bought with a button.
            GameObject bins = Panel(c, "Bins", new Vector2(0f, 1f), new Vector2(40f, -130f), new Vector2(360f, 306f), Vellum);
            Text(bins.transform, "TMP_BinsTitle", "Tempat Sampah Kampung", 20f, Ink, new Vector2(16f, -16f), new Vector2(330f, 28f), new Vector2(0f, 1f));
            Text(bins.transform, "TMP_BinsDesc", "Sampah desa turun 60%.", 15f, InkSecondary, new Vector2(16f, -52f), new Vector2(330f, 22f), new Vector2(0f, 1f));
            Text(bins.transform, "TMP_BinsDesc2", "Kepercayaan warga +25.", 15f, InkSecondary, new Vector2(16f, -76f), new Vector2(330f, 22f), new Vector2(0f, 1f));
            ButtonPanel(bins.transform, "Btn_BuyBins", new Vector2(16f, -120f), new Vector2(328f, 56f), Zone0);
            ShopLabel(bins.transform, "TMP_BinsStatus", "BELI  Rp 30.000", 18f, Vellum, new Vector2(28f, -136f), new Vector2(304f, 26f), TextAlignmentOptions.Center);

            // Armada: four upgrade tiers in a 2 x 2 grid.
            GameObject armada = Holder(c, "Armada").gameObject;
            string[] tierNames = { "Galah 4 m", "Perahu Sampan Kayu", "Trash Boom & Pos Sortir", "Amphibious Excavator" };
            string[] tierDesc = { "Alat dasar untuk sungai.", "Kapasitas 22, dari 8.", "Passive +Rp 2.500 tiap 4 detik.", "Kapasitas 60, keruk Gunung Sampah." };
            string[] tierPrice = { "Rp 20.000", "Rp 40.000", "Rp 75.000", "Rp 120.000" };
            for (int i = 0; i < 4; i++)
            {
                float x = 420f + (i % 2) * 390f;
                float y = -120f - (i / 2) * 166f;
                GameObject tier = Panel(armada.transform, "Tier_" + i, new Vector2(0f, 1f), new Vector2(x, y), new Vector2(375f, 150f), Vellum);
                Text(tier.transform, "TMP_TierName", tierNames[i], 19f, Ink, new Vector2(16f, -14f), new Vector2(343f, 28f), new Vector2(0f, 1f));
                Text(tier.transform, "TMP_TierDesc", tierDesc[i], 14f, InkSecondary, new Vector2(16f, -44f), new Vector2(343f, 22f), new Vector2(0f, 1f));
                ButtonPanel(tier.transform, "Btn_Buy", new Vector2(16f, -80f), new Vector2(343f, 52f), Zone0);
                ShopLabel(tier.transform, "TMP_Status", tierPrice[i], 17f, Vellum, new Vector2(28f, -93f), new Vector2(319f, 26f), TextAlignmentOptions.Center);
            }

            // Tools: one row per role (slot 1-4 = Serok, Capit, Ganco, Garuk), cells in ladder order. Names stay Tool_XX.
            // TODO(Niki): restyle role rows (icons, DESIGN.md tokens).
            Text(c, "Tools/TMP_ToolsTitle", "ALAT · SATU SLOT = SATU PERAN", 16f, InkSecondary, new Vector2(40f, -456f), new Vector2(600f, 24f), new Vector2(0f, 1f));
            Transform tools = Holder(c, "Tools");
            Transform grid = Holder(tools, "Grid");
            int[] perRow = new int[4];
            for (int t = 1; t <= 20; t++)
            {
                ToolDefinition def = ToolCatalog.GetTool(t);
                int row = (int)def.Role;
                if (perRow[row] == 0)
                {
                    Text(c, "Tools/Role_" + row, (row + 1) + " " + ToolCatalog.RoleName(def.Role), 14f, Ink, new Vector2(40f, -492f - row * 72f), new Vector2(100f, 40f), new Vector2(0f, 1f));
                }
                int col = perRow[row]++;
                string label = t.ToString("00") + " " + def.DisplayName;

                GameObject cell = Panel(grid, "Tool_" + t.ToString("00"), new Vector2(0f, 1f), new Vector2(140f + col * 132f, -486f - row * 72f), new Vector2(126f, 64f), Track);
                ButtonPanel(cell.transform, "Btn_Select", Vector2.zero, new Vector2(126f, 64f), Clear);
                ShopLabel(cell.transform, "TMP_Name", label, 11f, Ink, new Vector2(6f, -4f), new Vector2(116f, 30f), TextAlignmentOptions.TopLeft);
                cell.transform.Find("TMP_Name").GetComponent<TMP_Text>().enableWordWrapping = true;
                ShopLabel(cell.transform, "TMP_Status", "TERKUNCI", 10f, InkSecondary, new Vector2(6f, -40f), new Vector2(116f, 20f), TextAlignmentOptions.Left);
            }

            Text(c, "Footer/TMP_Hint", string.Empty, 15f, InkSecondary, new Vector2(40f, -800f), new Vector2(1160f, 22f), new Vector2(0f, 1f));

            PrefabUtility.SaveAsPrefabAsset(root, PrefabFolder + "/Canvas_ShopBankSampah.prefab");
            Object.DestroyImmediate(root);
            AssetDatabase.Refresh();
            Debug.Log("Canvas_ShopBankSampah prefab written to " + PrefabFolder + "/Canvas_ShopBankSampah.prefab");
        }

        // Button backed by a panel. The label sits on top and does not block clicks.
        private static GameObject ButtonPanel(Transform parent, string name, Vector2 pos, Vector2 size, Color color)
        {
            GameObject go = Panel(parent, name, new Vector2(0f, 1f), pos, size, color);
            Button button = go.AddComponent<Button>();
            button.targetGraphic = go.GetComponent<Image>();
            return go;
        }

        // Shop label: no raycast, so it never blocks the button under it.
        private static void ShopLabel(Transform parent, string name, string value, float fontSize, Color color, Vector2 pos, Vector2 size, TextAlignmentOptions alignment)
        {
            Text(parent, name, value, fontSize, color, pos, size, new Vector2(0f, 1f));
            Transform label = parent.Find(name);
            if (label == null) return;
            TMP_Text tmp = label.GetComponent<TMP_Text>();
            if (tmp == null) return;
            tmp.raycastTarget = false;
            tmp.alignment = alignment;
        }

        private static void BuildSurvivalSheet(Transform parent)
        {
            GameObject sheet = Panel(parent, "TL_SurvivalFloodSheet", new Vector2(0f, 1f), new Vector2(36f, -32f), new Vector2(342f, 134f), Vellum);
            Panel(sheet.transform, "TapePin_Top", new Vector2(0f, 1f), new Vector2(120f, 8f), new Vector2(60f, 14f), TapeTint).transform.localRotation = Quaternion.Euler(0f, 0f, 1.5f);

            Text(sheet.transform, "TMP_HPLabel", "HP", 14f, InkSecondary, new Vector2(12f, -10f), new Vector2(60f, 20f), new Vector2(0f, 1f));
            Text(sheet.transform, "Row_HP/TMP_HPValue", "100", 28f, Ink, new Vector2(12f, -32f), new Vector2(110f, 40f), new Vector2(0f, 1f));

            // 10-cell HP ramp; the controller fills cells from playerHealth / maxPlayerHealth.
            Transform rowHp = Holder(sheet.transform, "Row_HP");
            for (int i = 0; i < 10; i++)
            {
                Panel(rowHp, "Cell_Ramp_" + i, new Vector2(0f, 1f), new Vector2(128f + i * 20f, -40f), new Vector2(18f, 22f), Track);
            }

            Transform rowSiaga = Holder(sheet.transform, "Row_SiagaWater");
            Panel(rowSiaga, "Img_FiltrationDot", new Vector2(0f, 1f), new Vector2(12f, -89f), new Vector2(12f, 12f), Teal);
            Text(rowSiaga, "TMP_SiagaLevel", "SIAGA 4", 20f, Ink, new Vector2(30f, -84f), new Vector2(160f, 28f), new Vector2(0f, 1f));
            Text(rowSiaga, "TMP_WaterMeters", "+0.00m", 18f, InkSecondary, new Vector2(200f, -84f), new Vector2(130f, 28f), new Vector2(0f, 1f));
            Panel(rowSiaga, "RulerTrack", new Vector2(0f, 1f), new Vector2(200f, -114f), new Vector2(120f, 2f), Track);
            Panel(rowSiaga, "RulerNeedle", new Vector2(0f, 1f), new Vector2(200f, -108f), new Vector2(3f, 14f), Ink);
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
            Texture(gunung.transform, "Img_Hatch45Fill", "UI_Hatch45_Tile.png", new Vector2(240f, 56f), Vector2.zero, new Vector2(0f, 0f), 1f);
            // Solid cleared box so the labels stay sharp over the hatch (spec section 1, rule 3).
            Panel(gunung.transform, "Box_Cleared", new Vector2(0f, 1f), new Vector2(4f, -3f), new Vector2(132f, 50f), VellumSolid);
            Text(gunung.transform, "TMP_GunungLabel", "GUNUNG SAMPAH", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(220f, 20f), new Vector2(0f, 1f));
            Text(gunung.transform, "TMP_GunungPct", "100%", 28f, Ink, new Vector2(8f, -26f), new Vector2(220f, 34f), new Vector2(0f, 1f));

            GameObject clarity = Panel(rail.transform, "Cell_Kejernihan", new Vector2(0f, 0.5f), new Vector2(264f, 0f), new Vector2(240f, 56f), VellumSolid);
            Panel(clarity.transform, "Img_ClarityFill", new Vector2(0f, 0f), Vector2.zero, new Vector2(240f, 6f), Teal);
            Text(clarity.transform, "TMP_KejernihanLabel", "KEJERNIHAN", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(220f, 20f), new Vector2(0f, 1f));
            Text(clarity.transform, "TMP_KejernihanPct", "12%", 28f, Ink, new Vector2(8f, -26f), new Vector2(220f, 34f), new Vector2(0f, 1f));

            GameObject monsun = Panel(rail.transform, "Cell_MonsunTimer", new Vector2(0f, 0.5f), new Vector2(516f, 0f), new Vector2(252f, 56f), VellumSolid);
            Text(monsun.transform, "TMP_MonsunLabel", "MONSUN", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(115f, 20f), new Vector2(0f, 1f));
            GameObject clockGo = Text(monsun.transform, "TMP_ClockTime", "17:24", 14f, InkSecondary, new Vector2(130f, -6f), new Vector2(114f, 20f), new Vector2(0f, 1f));
            clockGo.GetComponent<TextMeshProUGUI>().alignment = TextAlignmentOptions.Right;
            Text(monsun.transform, "TMP_MonsunTimer", "05:00", 28f, Ink, new Vector2(8f, -26f), new Vector2(230f, 34f), new Vector2(0f, 1f));
        }

        private static void BuildContextualRail(Transform parent)
        {
            GameObject rail = Panel(parent, "TC_ContextualAlertRail", new Vector2(0.5f, 1f), new Vector2(0f, -118f), new Vector2(780f, 60f), Clear);

            GameObject bio = Panel(rail.transform, "Strip_BiohazardTimer", new Vector2(0f, 1f), new Vector2(0f, 0f), new Vector2(780f, 28f), Clear);
            GameObject bioHatchGo = new GameObject("Img_CrossHatch90", typeof(RectTransform), typeof(Image));
            bioHatchGo.transform.SetParent(bio.transform, false);
            RectTransform bioHatchRt = (RectTransform)bioHatchGo.transform;
            bioHatchRt.anchorMin = new Vector2(0f, 1f);
            bioHatchRt.anchorMax = new Vector2(0f, 1f);
            bioHatchRt.pivot = new Vector2(0f, 1f);
            bioHatchRt.anchoredPosition = Vector2.zero;
            bioHatchRt.sizeDelta = new Vector2(780f, 28f);
            Image hatchImage = bioHatchGo.GetComponent<Image>();
            hatchImage.sprite = LoadSprite("UI_CrossHatch90_Magenta.png");
            hatchImage.type = Image.Type.Filled;
            hatchImage.fillMethod = Image.FillMethod.Horizontal;
            hatchImage.fillOrigin = (int)Image.OriginHorizontal.Left;
            hatchImage.fillAmount = 1f;
            Panel(bio.transform, "Box_Cleared", new Vector2(0f, 1f), new Vector2(8f, -4f), new Vector2(180f, 20f), VellumSolid);
            Text(bio.transform, "TMP_BiohazardCountdown", "10s", 18f, Ink, new Vector2(12f, -4f), new Vector2(170f, 22f), new Vector2(0f, 1f));
            bio.SetActive(false);

            GameObject sell = Panel(rail.transform, "Strip_SellLockDump", new Vector2(0f, 1f), new Vector2(0f, -32f), new Vector2(780f, 28f), Clear);
            Texture(sell.transform, "Img_CrossHatch90", "UI_CrossHatch90_Magenta.png", new Vector2(780f, 28f), Vector2.zero, new Vector2(0f, 1f), 1f);
            Panel(sell.transform, "Box_Cleared", new Vector2(0f, 1f), new Vector2(8f, -4f), new Vector2(500f, 20f), VellumSolid);
            Text(sell.transform, "TMP_SellLockText", "JUAL DIKUNCI · AIR >= +1.85m · [Q] BUANG", 18f, Ink, new Vector2(12f, -4f), new Vector2(490f, 22f), new Vector2(0f, 1f));
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
            Text(ledger.transform, "Row_WargaTrust/TMP_WargaValue", "40", 20f, Ink, new Vector2(230f, -176f), new Vector2(84f, 28f), new Vector2(0f, 1f));
        }

        // Four 7x2 ticks around a 4 px center dot, per spec section 3.
        private static void BuildCrosshair(Transform parent)
        {
            GameObject cross = Panel(parent, "C_CrosshairReticle", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(24f, 24f), Clear);
            Panel(cross.transform, "Tick_Top", new Vector2(0.5f, 0.5f), new Vector2(0f, 9f), new Vector2(2f, 7f), Ink);
            Panel(cross.transform, "Tick_Bottom", new Vector2(0.5f, 0.5f), new Vector2(0f, -9f), new Vector2(2f, 7f), Ink);
            Panel(cross.transform, "Tick_Left", new Vector2(0.5f, 0.5f), new Vector2(-9f, 0f), new Vector2(7f, 2f), Ink);
            Panel(cross.transform, "Tick_Right", new Vector2(0.5f, 0.5f), new Vector2(9f, 0f), new Vector2(7f, 2f), Ink);
            Panel(cross.transform, "CenterDot", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(4f, 4f), Ink);
        }

        // Hidden at rest. Station data is not wired yet; the controller shows it only once a station event exists.
        private static void BuildDockSheet(Transform parent)
        {
            GameObject dock = Panel(parent, "BC_StationDockSheet", new Vector2(0.5f, 0f), new Vector2(0f, 34f), new Vector2(660f, 112f), Vellum);
            Text(dock.transform, "Header_StationName", "STASIUN", 16f, Ink, new Vector2(12f, -8f), new Vector2(636f, 24f), new Vector2(0f, 1f));
            Text(dock.transform, "Header_AcceptedClass", "Terima: -", 13f, InkSecondary, new Vector2(12f, -32f), new Vector2(636f, 20f), new Vector2(0f, 1f));

            Transform row = Holder(dock.transform, "Row_ActionKeys");
            string[] keys = { "[1] Normal", "[2] Medis B3", "[3] Biohazard", "[E] Setor Aman" };
            for (int i = 0; i < keys.Length; i++)
            {
                // Each slot: a background the controller can invert, a hidden magenta cross-hatch for DENDA, and the label.
                GameObject slot = Panel(row, "Key_" + i, new Vector2(0f, 1f), new Vector2(12f + i * 160f, -60f), new Vector2(150f, 42f), Clear);
                GameObject hatch = Texture(slot.transform, "Img_CrossHatch90", "UI_CrossHatch90_Magenta.png", new Vector2(150f, 42f), Vector2.zero, new Vector2(0f, 1f), 1f);
                hatch.SetActive(false);
                GameObject labelGo = Text(slot.transform, "TMP_KeyLabel", keys[i], 14f, Ink, new Vector2(27f, -1f), new Vector2(96f, 40f), new Vector2(0f, 1f));
                TextMeshProUGUI keyLabelText = labelGo.GetComponent<TextMeshProUGUI>();
                keyLabelText.enableWordWrapping = true;
                keyLabelText.enableAutoSizing = true;
                keyLabelText.fontSizeMin = 12f;
                keyLabelText.fontSizeMax = 20f;
                keyLabelText.alignment = TextAlignmentOptions.Center;
            }

            CanvasGroup group = dock.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;
            group.interactable = false;
        }

        private static void BuildHydroMap(Transform parent)
        {
            GameObject map = Panel(parent, "BR_VellumHydroMap", new Vector2(1f, 0f), new Vector2(-36f, 32f), new Vector2(360f, 298f), Vellum);
            map.transform.localRotation = Quaternion.Euler(0f, 0f, 2.5f);

            Texture(map.transform, "Img_ContourCanalBase", "UI_Contour.png", HudMapLayout.ContourArea, HudMapLayout.ContourOrigin, new Vector2(0f, 1f), 1f);
            // Dam marker is centered on Gunung Sampah upstream basin; the controller updates DAM %.
            GameObject dam = Texture(map.transform, "Img_DamChokeCrossHatch", "UI_CrossHatch90_Magenta.png", new Vector2(64f, 32f), new Vector2(96f, -44f), new Vector2(0f, 1f), 1f);
            ((RectTransform)dam.transform).pivot = new Vector2(0.5f, 0.5f);
            Text(map.transform, "TMP_DamLabel", "DAM 0%", 12f, Ink, new Vector2(64f, -68f), new Vector2(72f, 16f), new Vector2(0f, 1f));

            // Chevron centered on its own position, so it rotates around its middle.
            GameObject chevron = Texture(map.transform, "Icon_PlayerSampan", "UI_Chevron.png", new Vector2(20f, 20f), new Vector2(96f, -150f), new Vector2(0f, 1f), 1f);
            RectTransform chevronRect = (RectTransform)chevron.transform;
            chevronRect.pivot = new Vector2(0.5f, 0.5f);

            Panel(map.transform, "TapePin_TL", new Vector2(0f, 1f), new Vector2(8f, -6f), new Vector2(50f, 14f), TapeTint).transform.localRotation = Quaternion.Euler(0f, 0f, 38f);
            Panel(map.transform, "TapePin_BR", new Vector2(0f, 1f), new Vector2(302f, -274f), new Vector2(50f, 14f), TapeTint).transform.localRotation = Quaternion.Euler(0f, 0f, 38f);

            // 4 discard hubs: solid colored badges; 1 utility hub (KD = Kopdes): outline badge.
            CreateMapPin(map.transform, "Pin_B", "B", new Color32(0x22, 0xC5, 0x5E, 255), VellumSolid, solid: true);
            CreateMapPin(map.transform, "Pin_M", "M", new Color32(0xEA, 0xB3, 0x08, 255), Ink, solid: true);
            CreateMapPin(map.transform, "Pin_K", "K", new Color32(0xA8, 0x55, 0xF7, 255), VellumSolid, solid: true);
            CreateMapPin(map.transform, "Pin_P", "P", new Color32(0xA8, 0x70, 0x18, 255), VellumSolid, solid: true);
            CreateMapPin(map.transform, "Pin_KD", "KD", new Color32(0xF5, 0x9E, 0x0B, 255), new Color32(0xB4, 0x53, 0x09, 255), solid: false);

            // Place pins and the dam from kali-river-map.json now, so the prefab is right without Play mode.
            Vector2 origin = HudMapLayout.ContourOrigin;
            Vector2 area = HudMapLayout.ContourArea;
            HudMapLayout.PlaceAt((RectTransform)map.transform.Find("Pin_B"), HudMapLayout.MapToUi(HudMapLayout.BankSampahPin, origin, area));
            HudMapLayout.PlaceAt((RectTransform)map.transform.Find("Pin_M"), HudMapLayout.MapToUi(HudMapLayout.MedisB3Pin, origin, area));
            HudMapLayout.PlaceAt((RectTransform)map.transform.Find("Pin_K"), HudMapLayout.MapToUi(HudMapLayout.KarantinaPin, origin, area));
            HudMapLayout.PlaceAt((RectTransform)map.transform.Find("Pin_P"), HudMapLayout.MapToUi(HudMapLayout.PengepulPin, origin, area));
            HudMapLayout.PlaceAt((RectTransform)map.transform.Find("Pin_KD"), HudMapLayout.MapToUi(HudMapLayout.KopdesPin, origin, area));

            Vector2 damCenter = HudMapLayout.MapToUi(HudMapLayout.DamPoint(), origin, area);
            HudMapLayout.PlaceAt((RectTransform)dam.transform, damCenter);
            ((RectTransform)map.transform.Find("TMP_DamLabel")).anchoredPosition = damCenter + new Vector2(-32f, -26f);

            // Compact legend on the right side of the portrait river map.
            BuildMapLegend(map.transform);
        }

        private static void CreateMapPin(Transform parent, string name, string letter, Color badgeColor, Color textColor, bool solid)
        {
            GameObject pin = Panel(parent, name, new Vector2(0f, 1f), Vector2.zero, new Vector2(22f, 22f), badgeColor);
            ((RectTransform)pin.transform).pivot = new Vector2(0.5f, 0.5f);
            if (!solid)
            {
                Panel(pin.transform, "InnerFill", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(16f, 16f), VellumSolid);
            }
            GameObject letterGo = Text(pin.transform, "TMP_PinLetter", letter, letter.Length > 1 ? 10.5f : 13f, textColor, Vector2.zero, new Vector2(22f, 22f), new Vector2(0.5f, 0.5f));
            letterGo.GetComponent<TextMeshProUGUI>().alignment = TextAlignmentOptions.Center;
        }

        private static void BuildMapLegend(Transform parent)
        {
            float lx = 220f;
            Text(parent, "Legend/TMP_Title", "PETA SUNGAI", 13f, Ink, new Vector2(lx, -16f), new Vector2(128f, 18f), new Vector2(0f, 1f));
            (string code, string label, Color color, bool solid)[] rows = {
                ("B", "Bank Sampah", new Color32(0x22, 0xC5, 0x5E, 255), true),
                ("M", "Medis B3", new Color32(0xEA, 0xB3, 0x08, 255), true),
                ("K", "Karantina", new Color32(0xA8, 0x55, 0xF7, 255), true),
                ("P", "Pengepul", new Color32(0xA8, 0x70, 0x18, 255), true),
                ("KD", "Kopdes", new Color32(0xF5, 0x9E, 0x0B, 255), false),
            };
            for (int i = 0; i < rows.Length; i++)
            {
                float y = -44f - i * 26f;
                GameObject swatch = Panel(parent, "Legend/Swatch_" + rows[i].code, new Vector2(0f, 1f), new Vector2(lx, y - 2f), new Vector2(14f, 14f), rows[i].color);
                if (!rows[i].solid)
                {
                    Panel(swatch.transform, "Inner", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(8f, 8f), VellumSolid);
                }
                Text(parent, "Legend/Label_" + rows[i].code, rows[i].code + " · " + rows[i].label, 12f, InkSecondary, new Vector2(lx + 20f, y), new Vector2(110f, 18f), new Vector2(0f, 1f));
            }
            Text(parent, "Legend/Label_Bridge", "— Jembatan", 11f, InkSecondary, new Vector2(lx, -212f), new Vector2(128f, 16f), new Vector2(0f, 1f));
            Text(parent, "Legend/Label_Sluice", "— Pintu Air", 11f, new Color32(0xE1, 0x1D, 0x8F, 255), new Vector2(lx, -230f), new Vector2(128f, 16f), new Vector2(0f, 1f));
            Text(parent, "Legend/Label_Dam", "# Gunung Sampah", 11f, new Color32(0xE1, 0x1D, 0x8F, 255), new Vector2(lx, -248f), new Vector2(128f, 16f), new Vector2(0f, 1f));
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

            Image image = go.GetComponent<Image>();
            image.color = color;
            if (IsTranslucentVellum(color))
            {
                // 9-slice vellum sprite carries its own 230 alpha, so the tint stays white.
                Sprite vellum = LoadSprite("UI_Vellum9Slice.png");
                if (vellum != null)
                {
                    image.sprite = vellum;
                    image.type = Image.Type.Sliced;
                    image.color = Color.white;
                }
            }
            return go;
        }

        // Stretched holder, so its children use the parent panel's top-left as their origin.
        private static Transform Holder(Transform parent, string name)
        {
            Transform existing = parent.Find(name);
            if (existing != null) return existing;

            GameObject holder = new GameObject(name, typeof(RectTransform));
            holder.transform.SetParent(parent, false);
            RectTransform rt = (RectTransform)holder.transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            return holder.transform;
        }

        // Sprite fill or textured child. tile is repeats per 32 px for seamless tiles; 1 is one tile per 32 px.
        private static GameObject Texture(Transform parent, string name, string spriteFile, Vector2 size, Vector2 pos, Vector2 anchor, float tile)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = anchor;
            rt.anchorMax = anchor;
            rt.pivot = anchor;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;

            Sprite sprite = LoadSprite(spriteFile);
            if (sprite == null)
            {
                Image fallback = go.AddComponent<Image>();
                fallback.color = Ink;
                return go;
            }

            if (spriteFile.Contains("Chevron"))
            {
                Image image = go.AddComponent<Image>();
                image.sprite = sprite;
                image.preserveAspect = true;
                return go;
            }

            RawImage raw = go.AddComponent<RawImage>();
            raw.texture = sprite.texture;
            raw.color = Color.white;
            if (spriteFile.Contains("Contour"))
            {
                raw.uvRect = new Rect(0f, 0f, 1f, 1f);
            }
            else
            {
                raw.uvRect = new Rect(0f, 0f, size.x / 32f * tile, size.y / 32f * tile);
            }
            return go;
        }

        private static GameObject Text(Transform parent, string path, string value, float fontSize, Color color, Vector2 pos, Vector2 size, Vector2 anchor)
        {
            Transform current = parent;
            string[] parts = path.Split('/');
            for (int i = 0; i < parts.Length - 1; i++)
            {
                current = Holder(current, parts[i]);
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
            return go;
        }

        private static bool IsTranslucentVellum(Color color)
        {
            return Mathf.Approximately(color.r, Vellum.r)
                && Mathf.Approximately(color.g, Vellum.g)
                && Mathf.Approximately(color.b, Vellum.b)
                && Mathf.Abs(color.a - Vellum.a) < 0.01f;
        }

        private static Sprite LoadSprite(string fileName)
        {
            return AssetDatabase.LoadAssetAtPath<Sprite>(SpriteFolder + fileName);
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
