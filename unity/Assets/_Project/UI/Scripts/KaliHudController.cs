using System.Globalization;
using KaliRiverSweeper.Core;
using KaliRiverSweeper.Player;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace KaliRiverSweeper.UI
{
    /// <summary>
    /// Drives Canvas_HUD from RiverGameManager events (OnStateChanged, OnToolUnlocked, OnWeatherChanged,
    /// OnHazardOrAlert) and from KaliPlayerController.OnNearbyHubChanged for the station dock.
    /// Gameplay values are read inside handlers. The only timed work is the toast timer, the map refresh
    /// at 15 Hz, and the subscription retry (2 Hz) while the manager or player is not yet present.
    /// Child elements are found by name at Awake, so Canvas_HUD.prefab must keep the names from
    /// docs/HUD_SPEC_NIKI.md section 3. Map coordinates come from HudMapLayout.
    /// </summary>
    public sealed class KaliHudController : MonoBehaviour
    {
        private static readonly CultureInfo Invariant = CultureInfo.InvariantCulture;
        private const float MapRefreshHz = 15f;

        private static readonly Color Ink = new Color32(0x1E, 0x1F, 0x1D, 255);
        private static readonly Color Vellum = new Color32(0xF4, 0xF2, 0xEC, 255);
        private static readonly Color Zone0 = new Color32(0x11, 0x12, 0x11, 255);
        private static readonly Color Track = new Color32(0xDC, 0xDA, 0xD2, 255);
        private static readonly Color Alert = new Color32(0xB5, 0x0E, 0x6F, 255);
        private static readonly Color SiagaGreen = new Color32(0x15, 0x80, 0x3D, 255);
        private static readonly Color SiagaAmber = new Color32(0xC9, 0x7A, 0x0A, 255);
        private static readonly Color SiagaOrange = new Color32(0xEA, 0x58, 0x0C, 255);
        private static readonly Color SiagaRed = new Color32(0xE1, 0x1D, 0x8F, 255);
        private static readonly string[] KeyBaseLabels = { "[1] Normal", "[2] Medis B3", "[3] Biohazard", "[E] Setor Aman" };

        private RiverGameManager manager;
        private KaliPlayerController player;
        private float mapTimer;
        private float toastTimer;
        private float subscribeRetryTimer;

        private Image[] rampCells;
        private Image filtrationDot;
        private RectTransform ruler;
        private RectTransform clarityFill;
        private RectTransform contour;
        private RectTransform chevron;
        private RectTransform damMarker;
        private RectTransform damLabelRect;
        private RectTransform pinB;
        private RectTransform pinM;
        private RectTransform pinK;
        private RectTransform pinP;
        private RectTransform pinS;
        private RectTransform pinT;
        private TMP_Text damLabel;
        private TMP_Text hpValue;
        private TMP_Text siagaLevel;
        private TMP_Text waterMeters;
        private TMP_Text gunungPercent;
        private TMP_Text clarityPercent;
        private TMP_Text monsunTimer;
        private TMP_Text monsunLabel;
        private GameObject biohazardStrip;
        private Image biohazardHatchImage;
        private TMP_Text biohazardCountdown;
        private GameObject sellLockStrip;
        private TMP_Text normalCount;
        private TMP_Text medisCount;
        private TMP_Text bioCount;
        private TMP_Text kas;
        private TMP_Text muatan;
        private TMP_Text warga;
        private GameObject toast;
        private TMP_Text toastText;
        private CanvasGroup dock;
        private TMP_Text dockHeader;
        private TMP_Text dockAccepted;
        private Image[] keyBg;
        private GameObject[] keyCrossHatch;
        private TMP_Text[] keyLabel;

        private void Awake()
        {
            rampCells = new Image[10];
            for (int i = 0; i < rampCells.Length; i++)
            {
                rampCells[i] = Find<Image>("TL_SurvivalFloodSheet/Row_HP/Cell_Ramp_" + i);
            }

            filtrationDot = Find<Image>("TL_SurvivalFloodSheet/Row_SiagaWater/Img_FiltrationDot");
            ruler = Find<RectTransform>("TL_SurvivalFloodSheet/Row_SiagaWater/RulerNeedle");
            clarityFill = Find<RectTransform>("TC_EcologicalHydroRail/Cell_Kejernihan/Img_ClarityFill");
            contour = Find<RectTransform>("BR_VellumHydroMap/Img_ContourCanalBase");
            chevron = Find<RectTransform>("BR_VellumHydroMap/Icon_PlayerSampan");
            damMarker = Find<RectTransform>("BR_VellumHydroMap/Img_DamChokeCrossHatch");
            damLabelRect = Find<RectTransform>("BR_VellumHydroMap/TMP_DamLabel");
            damLabel = Find<TMP_Text>("BR_VellumHydroMap/TMP_DamLabel");
            pinB = Find<RectTransform>("BR_VellumHydroMap/Pin_B");
            pinM = Find<RectTransform>("BR_VellumHydroMap/Pin_M");
            pinK = Find<RectTransform>("BR_VellumHydroMap/Pin_K");
            pinP = Find<RectTransform>("BR_VellumHydroMap/Pin_P");
            pinS = Find<RectTransform>("BR_VellumHydroMap/Pin_S");
            pinT = Find<RectTransform>("BR_VellumHydroMap/Pin_T");

            hpValue = Find<TMP_Text>("TL_SurvivalFloodSheet/Row_HP/TMP_HPValue");
            siagaLevel = Find<TMP_Text>("TL_SurvivalFloodSheet/Row_SiagaWater/TMP_SiagaLevel");
            waterMeters = Find<TMP_Text>("TL_SurvivalFloodSheet/Row_SiagaWater/TMP_WaterMeters");
            gunungPercent = Find<TMP_Text>("TC_EcologicalHydroRail/Cell_GunungSampah/TMP_GunungPct");
            clarityPercent = Find<TMP_Text>("TC_EcologicalHydroRail/Cell_Kejernihan/TMP_KejernihanPct");
            monsunTimer = Find<TMP_Text>("TC_EcologicalHydroRail/Cell_MonsunTimer/TMP_MonsunTimer");
            monsunLabel = Find<TMP_Text>("TC_EcologicalHydroRail/Cell_MonsunTimer/TMP_MonsunLabel");
            biohazardStrip = FindGo("TC_ContextualAlertRail/Strip_BiohazardTimer");
            biohazardHatchImage = Find<Image>("TC_ContextualAlertRail/Strip_BiohazardTimer/Img_CrossHatch90");
            biohazardCountdown = Find<TMP_Text>("TC_ContextualAlertRail/Strip_BiohazardTimer/TMP_BiohazardCountdown");
            sellLockStrip = FindGo("TC_ContextualAlertRail/Strip_SellLockDump");
            normalCount = Find<TMP_Text>("TR_EconomyCargoLedger/Grid_Cargo3Class/Cell_Normal/TMP_NormalCount");
            medisCount = Find<TMP_Text>("TR_EconomyCargoLedger/Grid_Cargo3Class/Cell_MedisB3/TMP_MedisCount");
            bioCount = Find<TMP_Text>("TR_EconomyCargoLedger/Grid_Cargo3Class/Cell_Biohazard/TMP_BioCount");
            kas = Find<TMP_Text>("TR_EconomyCargoLedger/Row_KasRupiah/TMP_KasValue");
            muatan = Find<TMP_Text>("TR_EconomyCargoLedger/Row_MuatanHeader/TMP_MuatanValue");
            warga = Find<TMP_Text>("TR_EconomyCargoLedger/Row_WargaTrust/TMP_WargaValue");
            toast = FindGo("TL_ToolUnlockToast");
            toastText = Find<TMP_Text>("TL_ToolUnlockToast/TMP_ToastText");

            dock = Find<CanvasGroup>("BC_StationDockSheet");
            dockHeader = Find<TMP_Text>("BC_StationDockSheet/Header_StationName");
            dockAccepted = Find<TMP_Text>("BC_StationDockSheet/Header_AcceptedClass");
            keyBg = new Image[4];
            keyCrossHatch = new GameObject[4];
            keyLabel = new TMP_Text[4];
            for (int i = 0; i < 4; i++)
            {
                string slot = "BC_StationDockSheet/Row_ActionKeys/Key_" + i;
                keyBg[i] = Find<Image>(slot);
                keyCrossHatch[i] = FindGo(slot + "/Img_CrossHatch90");
                keyLabel[i] = Find<TMP_Text>(slot + "/TMP_KeyLabel");
            }

            if (toast != null) toast.SetActive(false);
            SetDockVisible(false);
            PlaceMarkers();
        }

        private void OnEnable()
        {
            TrySubscribeManager();
            TrySubscribePlayer();
        }

        // Start runs after every Awake, so RiverGameManager.Instance is set by now.
        private void Start()
        {
            TrySubscribeManager();
            TrySubscribePlayer();
        }

        private void OnDisable()
        {
            if (manager != null)
            {
                manager.OnStateChanged -= Refresh;
                manager.OnToolUnlocked -= HandleToolUnlocked;
                manager.OnWeatherChanged -= HandleWeatherChanged;
                manager.OnHazardOrAlert -= HandleHazardOrAlert;
                manager = null;
            }

            if (player != null)
            {
                player.OnNearbyHubChanged -= HandleNearbyHubChanged;
                player = null;
            }
        }

        private void Update()
        {
            // Subscription retry covers a manager or player spawned after the HUD. Throttled to 2 Hz so the
            // player lookup does not run every frame. Not a gameplay poll.
            subscribeRetryTimer -= Time.unscaledDeltaTime;
            if (subscribeRetryTimer <= 0f)
            {
                subscribeRetryTimer = 0.5f;
                TrySubscribeManager();
                TrySubscribePlayer();
            }

            UpdateToast();
            UpdateMap();
        }

        private void TrySubscribeManager()
        {
            if (manager != null || RiverGameManager.Instance == null) return;

            manager = RiverGameManager.Instance;
            manager.OnStateChanged += Refresh;
            manager.OnToolUnlocked += HandleToolUnlocked;
            manager.OnWeatherChanged += HandleWeatherChanged;
            manager.OnHazardOrAlert += HandleHazardOrAlert;
            Refresh();
        }

        private void TrySubscribePlayer()
        {
            if (player != null) return;

            player = FindObjectOfType<KaliPlayerController>();
            if (player == null) return;

            player.OnNearbyHubChanged += HandleNearbyHubChanged;
        }

        private void HandleWeatherChanged(bool isMonsoonStorm)
        {
            Refresh();
        }

        private void HandleHazardOrAlert(string message, bool isAlert)
        {
            Refresh();
        }

        // Shows the dock sheet only while the player is inside a hub trigger.
        private void HandleNearbyHubChanged(bool near, DiscardStationType station, bool isPosSortir, bool isTokoAlat, string hubName)
        {
            SetDockVisible(near);
            if (!near) return;

            bool isGudang = station == DiscardStationType.GudangPengepul;
            // Toko Alat is a shop, not a discard hub, so it shows no discard keys.
            bool isShop = isTokoAlat;
            if (isShop)
            {
                SetText(dockHeader, "TOKO: " + (hubName ?? string.Empty).ToUpper(Invariant));
                SetText(dockAccepted, "Belanja alat, bukan setor sampah");
            }
            else
            {
                SetText(dockHeader, "STASIUN: " + (hubName ?? string.Empty).ToUpper(Invariant) + " (" + StationLetter(station) + ")");
                SetText(dockAccepted, AcceptedLabel(station));
            }

            for (int i = 0; i < 4; i++)
            {
                bool legal = !isShop && IsLegalKey(station, i);
                bool neutral = i == 3 || isGudang || isShop;
                bool denda = !neutral && !legal;

                if (keyBg[i] != null) keyBg[i].color = legal ? Zone0 : Color.clear;
                if (keyCrossHatch[i] != null) keyCrossHatch[i].SetActive(denda);
                if (keyLabel[i] != null)
                {
                    keyLabel[i].color = legal ? Vellum : Ink;
                    string label = KeyBaseLabels[i];
                    if (i == 3 && isGudang) label = "[E] JUAL SEMUA\n<size=70%>(MURAH \u00B7 TURUN WARGA)</size>";
                    keyLabel[i].text = denda ? label + "\n<size=70%><color=#F43F5E>DENDA</color></size>" : label;
                }
            }
        }

        // Key 0 is Normal at Bank Sampah, key 1 is Medis B3 at Pos Medis B3, key 2 is Biohazard at Karantina.
        private static bool IsLegalKey(DiscardStationType station, int keyIndex)
        {
            switch (station)
            {
                case DiscardStationType.BankSampah: return keyIndex == 0;
                case DiscardStationType.PosMedisB3: return keyIndex == 1;
                case DiscardStationType.KarantinaBiohazard: return keyIndex == 2;
                default: return false;
            }
        }

        private static string StationLetter(DiscardStationType station)
        {
            switch (station)
            {
                case DiscardStationType.BankSampah: return "B";
                case DiscardStationType.PosMedisB3: return "M";
                case DiscardStationType.KarantinaBiohazard: return "K";
                default: return "P";
            }
        }

        private static string AcceptedLabel(DiscardStationType station)
        {
            switch (station)
            {
                case DiscardStationType.BankSampah: return "Terima: Normal";
                case DiscardStationType.PosMedisB3: return "Terima: Medis B3";
                case DiscardStationType.KarantinaBiohazard: return "Terima: Biohazard";
                default: return "Terima: semua kelas (murah · turun warga)";
            }
        }

        private void SetDockVisible(bool visible)
        {
            if (dock == null) return;
            dock.alpha = visible ? 1f : 0f;
            dock.blocksRaycasts = visible;
            dock.interactable = visible;
        }

        private void UpdateToast()
        {
            if (toast == null || !toast.activeSelf) return;

            toastTimer -= Time.unscaledDeltaTime;
            if (toastTimer <= 0f) toast.SetActive(false);
        }

        // Throttled to MapRefreshHz. The chevron tip points along the player's heading; forward is world +Z,
        // which points down the map at yaw 0.
        private void UpdateMap()
        {
            if (chevron == null || contour == null || player == null) return;

            mapTimer -= Time.unscaledDeltaTime;
            if (mapTimer > 0f) return;
            mapTimer = 1f / Mathf.Max(1f, MapRefreshHz);

            Vector2 playerMap = HudMapLayout.WorldToMap(player.transform.position);
            chevron.anchoredPosition = MapToUi(playerMap);

            // Heading in UI space is (sin yaw, -cos yaw). The chevron's tip is up, so the angle is atan2(-x, y).
            float yaw = player.transform.eulerAngles.y * Mathf.Deg2Rad;
            float headingX = Mathf.Sin(yaw);
            float headingY = -Mathf.Cos(yaw);
            float angle = Mathf.Atan2(-headingX, headingY) * Mathf.Rad2Deg;
            chevron.localRotation = Quaternion.Euler(0f, 0f, angle);
        }

        private void PlaceMarkers()
        {
            if (contour == null) return;

            HudMapLayout.PlaceAt(pinB, MapToUi(HudMapLayout.BankSampahPin));
            HudMapLayout.PlaceAt(pinM, MapToUi(HudMapLayout.MedisB3Pin));
            HudMapLayout.PlaceAt(pinK, MapToUi(HudMapLayout.KarantinaPin));
            HudMapLayout.PlaceAt(pinP, MapToUi(HudMapLayout.PengepulPin));
            HudMapLayout.PlaceAt(pinS, MapToUi(HudMapLayout.PosSortirPin));
            HudMapLayout.PlaceAt(pinT, MapToUi(HudMapLayout.TokoAlatPin));

            Vector2 dam = MapToUi(HudMapLayout.DamPoint());
            HudMapLayout.PlaceAt(damMarker, dam);
            if (damLabelRect != null) damLabelRect.anchoredPosition = dam + new Vector2(-32f, -26f);
        }

        private Vector2 MapToUi(Vector2 mapPoint)
        {
            return HudMapLayout.MapToUi(mapPoint, contour.anchoredPosition, contour.sizeDelta);
        }

        private void Refresh()
        {
            if (manager == null) return;

            float hpRatio = manager.maxPlayerHealth > 0f ? Mathf.Clamp01(manager.playerHealth / manager.maxPlayerHealth) : 0f;
            int filled = Mathf.RoundToInt(hpRatio * rampCells.Length);
            Color filledColor = manager.playerHealth <= 40f ? Alert : Ink;
            for (int i = 0; i < rampCells.Length; i++)
            {
                if (rampCells[i] != null) rampCells[i].color = i < filled ? filledColor : Track;
            }

            SetText(hpValue, Mathf.RoundToInt(manager.playerHealth).ToString(Invariant));
            SetText(siagaLevel, "SIAGA " + manager.SiagaLevel.ToString(Invariant));
            SetText(waterMeters, FormatMeters(manager.currentWaterLevelY));
            if (filtrationDot != null) filtrationDot.color = SiagaDotColor(manager.SiagaLevel);
            if (ruler != null)
            {
                float t = Mathf.Clamp01(Mathf.InverseLerp(-0.25f, 2.45f, manager.currentWaterLevelY));
                ruler.anchoredPosition = new Vector2(200f + t * 120f, ruler.anchoredPosition.y);
            }

            SetText(gunungPercent, Mathf.RoundToInt(manager.gunungSampahHealth * 100f).ToString(Invariant) + "%");
            SetText(clarityPercent, Mathf.RoundToInt(manager.waterClarity * 100f).ToString(Invariant) + "%");
            if (clarityFill != null)
            {
                clarityFill.sizeDelta = new Vector2(240f * Mathf.Clamp01(manager.waterClarity), clarityFill.sizeDelta.y);
            }

            SetText(monsunTimer, FormatClock(manager.monsoonCountdownRemaining));
            SetText(monsunLabel, manager.isMonsoonStorm ? "BADAI" : "MONSUN");
            SetText(damLabel, "DAM " + Mathf.RoundToInt(manager.gunungSampahHealth * 100f).ToString(Invariant) + "%");

            bool hasBiohazard = manager.biohazardCargo > 0;
            SetActive(biohazardStrip, hasBiohazard);
            if (hasBiohazard)
            {
                SetText(biohazardCountdown, Mathf.CeilToInt(manager.BiohazardGraceRemaining).ToString(Invariant) + "s");
                if (biohazardHatchImage != null)
                {
                    float graceRatio = manager.biohazardGraceSeconds > 0f
                        ? Mathf.Clamp01(manager.BiohazardGraceRemaining / manager.biohazardGraceSeconds)
                        : 0f;
                    biohazardHatchImage.fillAmount = graceRatio;
                }
            }

            SetActive(sellLockStrip, manager.IsSellLocked);

            SetText(normalCount, manager.normalCargo.ToString(Invariant));
            SetText(medisCount, manager.medicalCargo.ToString(Invariant));
            SetText(bioCount, manager.biohazardCargo.ToString(Invariant));
            SetText(kas, "Rp " + FormatRupiah(manager.rupiah));
            SetText(muatan, manager.cargoCount.ToString(Invariant) + " / " + manager.cargoCapacity.ToString(Invariant));
            SetText(warga, manager.communityTrust.ToString(Invariant));
        }

        private void HandleToolUnlocked(ToolDefinition tool)
        {
            if (tool == null || toast == null || toastText == null) return;

            string badge = tool.GunungDamagePerSwing > 0f ? "  · BISA KERUK" : string.Empty;
            SetText(toastText, "Alat Baru: #" + tool.Index.ToString("00", Invariant) + " " + tool.DisplayName + badge);
            toast.SetActive(true);
            toastTimer = 3.5f;
        }

        private static Color SiagaDotColor(int siagaLevel)
        {
            switch (siagaLevel)
            {
                case 1: return SiagaRed;
                case 2: return SiagaOrange;
                case 3: return SiagaAmber;
                default: return SiagaGreen;
            }
        }

        private static string FormatMeters(float levelY)
        {
            string sign = levelY >= 0f ? "+" : string.Empty;
            return sign + levelY.ToString("0.00", Invariant) + "m";
        }

        private static string FormatClock(float seconds)
        {
            int total = Mathf.Max(0, Mathf.CeilToInt(seconds));
            return (total / 60).ToString("00", Invariant) + ":" + (total % 60).ToString("00", Invariant);
        }

        // Indonesian thousand separator is "." (Rp 1.250.000).
        private static string FormatRupiah(int amount)
        {
            return amount.ToString("#,0", Invariant).Replace(',', '.');
        }

        private T Find<T>(string path) where T : Component
        {
            Transform t = transform.Find(path);
            return t != null ? t.GetComponent<T>() : null;
        }

        private GameObject FindGo(string path)
        {
            Transform t = transform.Find(path);
            return t != null ? t.gameObject : null;
        }

        private static void SetText(TMP_Text target, string value)
        {
            if (target != null) target.text = value;
        }

        private static void SetActive(GameObject target, bool active)
        {
            if (target != null && target.activeSelf != active) target.SetActive(active);
        }
    }
}
