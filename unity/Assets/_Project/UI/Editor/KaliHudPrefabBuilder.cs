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
            Text(gunung.transform, "TMP_GunungLabel", "GUNUNG SAMPAH", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(220f, 20f), new Vector2(0f, 1f));
            Text(gunung.transform, "TMP_GunungPct", "100%", 28f, Ink, new Vector2(8f, -26f), new Vector2(220f, 34f), new Vector2(0f, 1f));

            GameObject clarity = Panel(rail.transform, "Cell_Kejernihan", new Vector2(0f, 0.5f), new Vector2(264f, 0f), new Vector2(240f, 56f), VellumSolid);
            Panel(clarity.transform, "Img_ClarityFill", new Vector2(0f, 0f), Vector2.zero, new Vector2(240f, 6f), Teal);
            Text(clarity.transform, "TMP_KejernihanLabel", "KEJERNIHAN", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(220f, 20f), new Vector2(0f, 1f));
            Text(clarity.transform, "TMP_KejernihanPct", "12%", 28f, Ink, new Vector2(8f, -26f), new Vector2(220f, 34f), new Vector2(0f, 1f));

            GameObject monsun = Panel(rail.transform, "Cell_MonsunTimer", new Vector2(0f, 0.5f), new Vector2(516f, 0f), new Vector2(252f, 56f), VellumSolid);
            Text(monsun.transform, "TMP_MonsunLabel", "MONSUN", 14f, InkSecondary, new Vector2(8f, -6f), new Vector2(230f, 20f), new Vector2(0f, 1f));
            Text(monsun.transform, "TMP_MonsunTimer", "05:00", 28f, Ink, new Vector2(8f, -26f), new Vector2(230f, 34f), new Vector2(0f, 1f));
        }

        private static void BuildContextualRail(Transform parent)
        {
            GameObject rail = Panel(parent, "TC_ContextualAlertRail", new Vector2(0.5f, 1f), new Vector2(0f, -118f), new Vector2(780f, 60f), Clear);

            GameObject bio = Panel(rail.transform, "Strip_BiohazardTimer", new Vector2(0f, 1f), new Vector2(0f, 0f), new Vector2(780f, 28f), Clear);
            Texture(bio.transform, "Img_CrossHatch90", "UI_CrossHatch90_Magenta.png", new Vector2(780f, 28f), Vector2.zero, new Vector2(0f, 1f), 1f);
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
            GameObject dock = Panel(parent, "BC_StationDockSheet", new Vector2(0.5f, 0f), new Vector2(0f, 34f), new Vector2(660f, 104f), Vellum);
            Text(dock.transform, "Header_StationName", "STASIUN", 16f, Ink, new Vector2(12f, -8f), new Vector2(636f, 24f), new Vector2(0f, 1f));
            Text(dock.transform, "Header_AcceptedClass", "Terima: -", 13f, InkSecondary, new Vector2(12f, -32f), new Vector2(636f, 20f), new Vector2(0f, 1f));

            Transform row = Holder(dock.transform, "Row_ActionKeys");
            string[] keys = { "[1] Normal", "[2] Medis B3", "[3] Biohazard", "[E] Setor Aman" };
            for (int i = 0; i < keys.Length; i++)
            {
                Text(row, "Key_" + i, keys[i], 14f, Ink, new Vector2(12f + i * 160f, -62f), new Vector2(150f, 22f), new Vector2(0f, 1f));
            }

            CanvasGroup group = dock.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;
            group.interactable = false;
        }

        private static void BuildHydroMap(Transform parent)
        {
            GameObject map = Panel(parent, "BR_VellumHydroMap", new Vector2(1f, 0f), new Vector2(-44f, 38f), new Vector2(372f, 276f), Vellum);
            map.transform.localRotation = Quaternion.Euler(0f, 0f, 2.5f);

            Texture(map.transform, "Img_ContourCanalBase", "UI_Contour.png", new Vector2(340f, 220f), new Vector2(16f, -16f), new Vector2(0f, 1f), 1f);
            Texture(map.transform, "Img_DamChokeCrossHatch", "UI_CrossHatch90_Magenta.png", new Vector2(84f, 56f), new Vector2(150f, -110f), new Vector2(0f, 1f), 1f);
            Text(map.transform, "TMP_DamLabel", "DAM 0%", 14f, Ink, new Vector2(156f, -122f), new Vector2(80f, 20f), new Vector2(0f, 1f));

            // Chevron centered on its own position, so it rotates around its middle.
            GameObject chevron = Texture(map.transform, "Icon_PlayerSampan", "UI_Chevron.png", new Vector2(20f, 20f), new Vector2(170f, -130f), new Vector2(0f, 1f), 1f);
            RectTransform chevronRect = (RectTransform)chevron.transform;
            chevronRect.pivot = new Vector2(0.5f, 0.5f);

            Panel(map.transform, "TapePin_TL", new Vector2(0f, 1f), new Vector2(8f, -6f), new Vector2(50f, 14f), TapeTint).transform.localRotation = Quaternion.Euler(0f, 0f, 38f);
            Panel(map.transform, "TapePin_BR", new Vector2(0f, 1f), new Vector2(314f, -252f), new Vector2(50f, 14f), TapeTint).transform.localRotation = Quaternion.Euler(0f, 0f, 38f);

            string[] pins = { "B", "M", "K", "P" };
            for (int i = 0; i < pins.Length; i++)
            {
                GameObject pin = Panel(map.transform, "Pin_" + pins[i], new Vector2(0f, 1f), new Vector2(24f + i * 40f, -226f), new Vector2(28f, 28f), Ink);
                Text(pin.transform, "TMP_PinLetter", pins[i], 16f, VellumSolid, new Vector2(8f, -4f), new Vector2(12f, 20f), new Vector2(0f, 1f));
            }
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

        private static void Text(Transform parent, string path, string value, float fontSize, Color color, Vector2 pos, Vector2 size, Vector2 anchor)
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
